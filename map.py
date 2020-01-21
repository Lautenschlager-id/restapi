import os
import aiomysql

from types import SimpleNamespace

from sanic import Blueprint
from sanic import response

pools = SimpleNamespace()
blueprint = Blueprint("map", url_prefix="/map")

@blueprint.listener("before_server_start")
async def setup_connection(app, loop):
	pools.a801 = await aiomysql.create_pool(
		host=os.getenv("A801_API_HOST_IP"),
		port=int(os.getenv("A801_API_HOST_PORT")),
		user=os.getenv("A801_API_USER"),
		password=os.getenv("A801_API_PASS"),
		db=os.getenv("A801_API_DB"),
		loop=loop,
		cursorclass=aiomysql.SSDictCursor,
		autocommit=True
	)

	pools.cfm = await aiomysql.create_pool(
		host=os.getenv("CFM_API_HOST_IP"),
		port=int(os.getenv("CFM_API_HOST_PORT")),
		user=os.getenv("CFM_API_USER"),
		password=os.getenv("CFM_API_PASS"),
		db=os.getenv("CFM_API_DB"),
		loop=loop,
		cursorclass=aiomysql.SSDictCursor,
		autocommit=True
	)

@blueprint.route("/@<mapcode:\\d+>/image")
async def parse_map_image(request, mapcode):
	return response.redirect(
		"https://cheese.formice.com/maps.php?code={}&nodefault".format(mapcode)
	)

@blueprint.route("/@<mapcode:\\d+>", methods=["POST"])
async def parse_map_update(request, mapcode):
	async with pools.cfm.acquire() as conn:
		async with conn.cursor() as cursor:
			await cursor.execute(
				"SELECT \
					b.completing \
				FROM \
					tfmvai_maps as m \
					LEFT JOIN vai_bots.batches as b ON \
						b.batch_start = m.code AND b.batch_end = m.code \
				WHERE \
					m.code = %s",
				(mapcode,)
			)
			rows = await cursor.fetchall()
			if len(rows) > 0:
				if rows[0]["completing"]:
					return response.json({
						"error": "The map is already in the queue."
					}, 400)
			else:
				return response.json({"error": "Map not found."}, 404)

			await cursor.execute(
				"INSERT INTO \
					vai_bots.batches \
					(batch_start, batch_end, completing, bot) \
				VALUES \
					(%s, %s, 0, 0)",
				(mapcode, mapcode)
			)
			return response.json({
				"message": "The map has been added to the queue."
			})

@blueprint.route("/<prefix:.><data:.+>")
async def parse_request(request, prefix, data):
	data = data.strip("/")

	if prefix == "@": # map
		if not data.isdigit():
			return response.json({
				"error": "Map code must be a valid number. Check the docs for"
						 " further information on how to use this endpoint."
			}, 400)

		async with pools.cfm.acquire() as conn:
			async with conn.cursor() as cursor:
				await cursor.execute(
					"SELECT \
						m.code, \
						p.name as author, \
						m.perm, \
						m.public_map, \
						m.public_xml, \
						m.xml, \
						m.last_update, \
						m.is_loaded as drawn, \
						b.completing, \
						b.bot \
					FROM \
						tfmvai_maps as m \
						INNER JOIN tfmvai_player as p ON p.id = m.author \
						LEFT JOIN vai_bots.batches as b ON \
							b.batch_start = m.code AND b.batch_end = m.code \
					WHERE \
						m.code = %s",
					(data,)
				)
				row = await cursor.fetchone()

				if row is None:
					return response.json({"error": "Map not found."}, 404)

				# TODO: Check if the user has permission to see the xml.
				if not row["public_xml"]:
					row["xml"] = None

				row["public"] = {
					"map": bool(row["public_map"]),
					"xml": bool(row["public_xml"])
				}
				del row["public_map"], row["public_xml"]

				if row["completing"] is not None:
					if row["bot"] > 0:
						if row["completing"]:
							code, status = 2, "SAVING"
						else:
							code, status = 1, "WAITING_BOT"
						assigned = row["bot"]
					else:
						code, status = 0, "ASSIGNING_BOT"
						assigned = None

					row["queue"] = {
						"code": code,
						"status": status,
						"assigned_bot": assigned
					}
				else:
					row["queue"] = None
				del row["completing"], row["bot"]

				row["code"] = "@" + row["code"]
				row["drawn"] = bool(row["drawn"])
				return response.json(row)

	elif prefix.lower() == "p": # category
		if not data.isdigit():
			return response.json({
				"error": "Category must be a valid number. Check the docs for"
						 " further information on how to use this endpoint."
			}, 400)

		async with pools.cfm.acquire() as conn:
			async with conn.cursor() as cursor:
				await cursor.execute(
					"SELECT \
						m.code, \
						p.name as author \
					FROM \
						tfmvai_maps as m \
						INNER JOIN tfmvai_player as p ON p.id = m.author \
					WHERE \
						m.perm = %s \
					LIMIT 50",
					(data,)
				)
				return response.json(await cursor.fetchall())

	elif prefix == ":": # author
		no_tag = data.replace("#0000", "")
		parameters = (no_tag, no_tag + "#0000")
		# Transformice stores some users with the #0000 tag
		# and some without it. We need to search both.

		async with pools.cfm.acquire() as conn:
			async with conn.cursor() as cursor:
				await cursor.execute(
					"SELECT \
						m.code, \
						m.perm \
					FROM \
						tfmvai_maps as m \
						INNER JOIN tfmvai_player as p ON p.id = m.author \
					WHERE \
						p.name IN (%s, %s)",
					parameters
				)
				return response.json(await cursor.fetchall())

	else:
		return response.json({
			"error": "Unknown prefix '{}'. Check the docs for further"
					 " information on how to use this endpoint.".format(prefix)
		}, 400)