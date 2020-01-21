# CheeseForMice API
 This is the official CFM API. With this, you can access transformice's data easily. Feel free to open an issue for any suggestion or bug.

## Documentation
 The API is distributed along two services: general information and map images.

### General Information Service
 It is located at https://cheese.formice.com/api/ and it has three different endpoints: `mouse`, `tribe` and `map`.

#### Mouse endpoint
 You can access any player's information, search some and filter by ranks. These are the available routes:<br>
 - `GET` /mouse/@Username -> Shows information about a user. Example [here](https://cheese.formice.com/api/mouse/@Tocutoeltuco%230000).
 - `GET` /mouse/search?query=partial -> Searches for a user. Example [here](https://cheese.formice.com/api/mouse/search?query=Tocutoelt).
 - `GET` /mouse/rank?query=rank_filter -> Shows users with the given rank filter. Example [here](https://cheese.formice.com/api/mouse/rank?query=16).

 Regarding `rank_filter`, it is a bitwise filter. If you don't know what it is, don't worry.<br>
 These are the available ranks:<br>
 - `1` -> `administrator`
 - `2` -> `moderator`
 - `4` -> `sentinel`
 - `8` -> `mapcrew`
 - `16` -> `module_team`
 - `32` -> `funcorp`
 - `64` -> `fashion_squad`

 All you need to do is to sum those numbers to add the rank to the filter. Example:<br>
 - To filter users with the `module_team` and `mapcrew` roles, you use `16 + 8` (`24`). [Here is the filter](https://cheese.formice.com/api/mouse/rank?query=24).

#### Tribe endpoint
 You can access any tribe's information and search some. These are the available routes:<br>
 - `GET` /tribe/@Tribename -> Shows information about a tribe. Example [here](https://cheese.formice.com/api/tribe/@Runtime%20error).
 - `GET` /tribe/:Username -> Shows the tribe of the given user. Example [here](https://cheese.formice.com/api/tribe/:Tocutoeltuco%230000).
 - `GET` /tribe/search?query=partial -> Searches for a tribe. Example [here](https://cheese.formice.com/api/tribe/search?query=Runtime%20e).

#### Map endpoint
 You can access any map's information and filter some. These are the available routes:<br>
 - `GET` /map/@code -> Shows information about a map. Example [here](https://cheese.formice.com/api/map/@7642505).
 - `POST` /map/@code -> Adds the map to the update queue.
 - `GET` /map/@code/image -> Shows the thumbnail of a map. Redirects to the **Map Images service**.
 - `GET` /map/Pperm -> Shows some maps in the given category. Example [here](https://cheese.formice.com/api/map/P41).
 - `GET` /map/:Author -> Shows the maps of the given user. Example [here](https://cheese.formice.com/api/map/:Tocutoeltuco).

 Remember that this endpoint does not show xml yet.

### Map Images Service
 It is located at https://cheese.formice.com/maps.php.<br>
 It has a single route, as you can see. It supports GET and POST methods.
 - `GET` /maps.php?code=code -> Shows the image of a map. Example [here](https://cheese.formice.com/maps.php?code=7642505). If it is not drawn yet, shows a default image.
 - `GET` /maps.php?code=code&nodefault -> Shows the image of a map, and if it is not drawn yet, shows a plain text.
 - `POST` /maps.php?code=code -> Adds the map to the drawing queue.