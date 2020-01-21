import asyncio
import os

from sanic import Sanic

from map import blueprint as map_blueprint
from mouse import blueprint as mouse_blueprint
from tribe import blueprint as tribe_blueprint

# Required environment vars:
# API_HOST_IP
# API_HOST_PORT
# A801_API_HOST_IP
# A801_API_HOST_PORT
# A801_API_USER
# A801_API_PASS
# A801_API_DB
# CFM_API_HOST_IP
# CFM_API_HOST_PORT
# CFM_API_USER
# CFM_API_PASS
# CFM_API_DB

app = Sanic(__name__)

app.blueprint(map_blueprint)
app.blueprint(mouse_blueprint)
app.blueprint(tribe_blueprint)

if __name__ == '__main__':
	app.run(
		host=os.getenv("API_HOST_IP"),
		port=int(os.getenv("API_HOST_PORT"))
	)