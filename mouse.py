import os
import aiomysql

from types import SimpleNamespace

from sanic import Blueprint
from sanic import response

pools = SimpleNamespace()
blueprint = Blueprint("mouse", url_prefix="/mouse")

ranks = {
	"administrator": 2 ** 0,
	"moderator": 2 ** 1,
	"sentinel": 2 ** 2,
	"mapcrew": 2 ** 3,
	"module_team": 2 ** 4,
	"funcorp": 2 ** 5,
	"fashion_squad": 2 ** 6
}

def normalize_rank(rank):
	rank_list = []

	for filter in ranks.items():
		if rank & filter[1]:
			rank_list.append(filter[0])

	return rank_list

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

@blueprint.route("/<path:.*>")
async def parse_request(request, path):
	path = path.strip("/")

	if path == "search": # /mouse/search?query=Tocu
		if "query" not in request.raw_args:
			return response.json({
				"error": "Missing 'query' parameter. Check the docs for"
						 " further information on how to use this endpoint."
			}, 400)
		query = request.raw_args["query"]

		async with pools.a801.acquire() as conn:
			async with conn.cursor() as cursor:
				await cursor.execute(
					"SELECT name FROM player WHERE name LIKE %s LIMIT 30",
					("{}%".format(query),)
					# Starts with the query. Otherwise, it is too slow.
				)
				result = await cursor.fetchall()

		return response.json(result)

	elif path == "rank": # /mouse/rank?query=1
		if "query" not in request.raw_args:
			return response.json({
				"error": "Missing 'query' parameter. Check the docs for"
						 " further information on how to use this endpoint."
			}, 400)
		elif not request.raw_args["query"].isdigit():
			return response.json({
				"error": "The 'query' parameter must be a number. Check the"
						 " docs for further information on how to use this"
						 " endpoint."
			}, 400)
		query = int(request.raw_args["query"])
		result = []

		async with pools.cfm.acquire() as conn:
			async with conn.cursor() as cursor:
				await cursor.execute("SELECT rank, name FROM ranks_relations")

				async for row in cursor:
					if (row["rank"] & query) == query:# Has all the query ranks
						row["normalized"] = normalize_rank(row["rank"])
						result.append(row)

		return response.json({
			"filter": normalize_rank(query),
			"result": result
		})

	elif path[0] == "@": # /mouse/@Tocutoeltuco
		no_tag = path[1:].replace("#0000", "")
		parameters = (no_tag, no_tag + "#0000")
		# Transformice stores some users with the #0000 tag
		# and some without it. We need to search both.

		async with pools.a801.acquire() as conn:
			async with conn.cursor() as cursor:
				await cursor.execute(
					"SELECT \
						p.*, \
						m.*, \
						t.name as tribe_name \
					FROM \
						player as p \
						LEFT JOIN member as m ON m.id_member = p.id \
						LEFT JOIN tribe as t ON t.id = m.id_tribe \
					WHERE \
						p.name IN (%s, %s)",
					parameters
				)
				result = await cursor.fetchone()

		if result is None:
			return response.json({"error": "Player not found."}, 404)

		del result["id_member"], result["m.name"]

		async with pools.cfm.acquire() as conn:
			async with conn.cursor() as cursor:
				await cursor.execute(
					"SELECT rank FROM ranks_relations WHERE id = %s",
					(result["id"],)
				)
				rank = await cursor.fetchone()

				if rank is not None:
					result["rank"] = rank["rank"]

		return response.json(result)

	else:
		return response.json({
			"error": "Route not found. Check the docs for further information"
					 " on how to use this endpoint."
		}, 404)
