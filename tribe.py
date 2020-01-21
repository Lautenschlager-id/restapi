import os
import aiomysql

from types import SimpleNamespace

from sanic import Blueprint
from sanic import response

pools = SimpleNamespace()
blueprint = Blueprint("tribe", url_prefix="/tribe")

@blueprint.listener("before_server_start")
async def setup_connection(app, loop):
	pools.a801 = await aiomysql.create_pool(
		host=os.getenv("A801_API_HOST_IP"),
		port=int(os.getenv("A801_API_HOST_PORT")),
		user=os.getenv("A801_API_USER"),
		password=os.getenv("A801_API_PASS"),
		db=os.getenv("A801_API_DB"),
		loop=loop,
		cursorclass=aiomysql.SSDictCursor
	)

	pools.cfm = await aiomysql.create_pool(
		host=os.getenv("CFM_API_HOST_IP"),
		port=int(os.getenv("CFM_API_HOST_PORT")),
		user=os.getenv("CFM_API_USER"),
		password=os.getenv("CFM_API_PASS"),
		db=os.getenv("CFM_API_DB"),
		loop=loop,
		cursorclass=aiomysql.SSDictCursor
	)

@blueprint.route("/<path:.*>")
async def parse_request(request, path):
	path = path.strip("/")

	if path == "search": # /tribe/search?query=Runt
		if "query" not in request.raw_args:
			return response.json({
				"error": "Missing 'query' parameter. Check the docs for"
						 " further information on how to use this endpoint."
			}, 400)
		query = request.raw_args["query"]

		async with pools.a801.acquire() as conn:
			async with conn.cursor() as cursor:
				await cursor.execute(
					"SELECT name FROM tribe WHERE name LIKE %s LIMIT 30",
					("{}%".format(query),)
					# Starts with the query. Otherwise, it is too slow.
				)
				result = await cursor.fetchall()

		return response.json(result)

	elif path[0] in ["@", ":"]: # /tribe/@Runtime error /tribe/:Tocutoeltuco
		async with pools.a801.acquire() as conn:
			async with conn.cursor() as cursor:
				if path[0] == "@":
					await cursor.execute(
						"SELECT * FROM tribe WHERE name = %s LIMIT 1",
						(path[1:],)
					)
				else:
					no_tag = path[1:].replace("#0000", "")
					parameters = (no_tag, no_tag + "#0000")
					# Transformice stores some users with the #0000 tag
					# and some without it. We need to search both.

					await cursor.execute(
						"SELECT \
							t.* \
						FROM \
							player as p \
							INNER JOIN member as m ON m.id_member = p.id \
							INNER JOIN tribe as t ON t.id = m.id_tribe \
						WHERE \
							p.name IN (%s, %s) \
						LIMIT 1",
						parameters
					)
				result = await cursor.fetchall()

				if len(result) == 0:
					return response.json({"error": "Tribe not found."}, 404)
				result = result[0]

				await cursor.execute(
					"SELECT \
						p.name \
					FROM \
						member as m \
						INNER JOIN player as p ON p.id = m.id_member \
					WHERE \
						m.id_tribe = %s",
					(result["id"],)
				)
				result["members"] = await cursor.fetchall()

		return response.json(result)

	else:
		return response.json({
			"error": "Route not found. Check the docs for further information"
					 " on how to use this endpoint."
		}, 404)