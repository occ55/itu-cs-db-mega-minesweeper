from ..init import app
from flask import Flask, request, jsonify, make_response
from ..queryBuilders.qb import QueryBuilder
import os
from ..utils import *
import time
import hashlib
import random
import json

now = lambda: time.time_ns() // 1000000

chunk_size = 16
map_size = 128
map_chunk_ct = map_size // chunk_size
mine_chance = 0.2


def sanitize_competition(c):
    c["password"] = True if c["password"] is not None else False
    return c


@app.route("/api/get_competitions", methods=["GET", "POST"])
def get_competitions():
    comps = (
        QueryBuilder()
        .Select("competitions", "c", ["id", "start", "end", "title", "password"])
        .AndWhere('c."end" > {now}', {"now": now()})
        .Execute()
    )
    comps = list(map(sanitize_competition, comps))
    return jsonify(comps)


@app.route("/api/start_competition", methods=["POST"])
@login_required
def start_competition(user_id):
    data = request.json
    if "password" in data:
        data["password"] = hashlib.sha256(bytes(data["password"], "utf-8")).hexdigest()
    else:
        data["password"] = None
    if "time" not in data or "title" not in data:
        raise RuntimeError("Essential argument not supplied")
    start = now()
    data["start"] = start
    data["end"] = start + data["time"]
    start_competition_internal(data, user_id)
    return jsonify(data)


@app.route("/api/get_field", methods=["POST"])
@entry_required
def get_field(user_id):
    chunks = (
        QueryBuilder()
        .Select("chunks", "c", ["competition_id", "x", "y", "cdata"])
        .AndWhere("c.competition_id = {competition_id}", request.json)
        .Execute()
    )
    return jsonify(chunks)


@app.route("/api/get_chunk", methods=["POST"])
@entry_required
def get_chunk(user_id):
    chunk = (
        QueryBuilder()
        .Select("chunks", "c", ["competition_id", "x", "y", "cdata"])
        .AndWhere(
            "c.competition_id = {competition_id} and x = {x} and y = {y}", request.json
        )
        .ExecuteOne()
    )
    return jsonify(chunk)


@app.route("/api/open_tile", methods=["POST"])
@entry_required
def open_tile(user_id):
    x = request.json["x"]
    y = request.json["y"]
    competition_id = request.json["competition_id"]
    game_map = empty_map()
    closed_map = empty_map()
    mutation_list = []
    reveal_tile(game_map, closed_map, x, y, competition_id, user_id, mutation_list)
    mutation_list_json = json.dumps(mutation_list, separators=(",", ":"))
    log_id = (
        QueryBuilder()
        .Insert(
            "event_log",
            {
                "competition_id": competition_id,
                "action": json.dumps(
                    {"modified_chunks": mutation_list_json}, separators=(",", ":")
                ),
            },
        )
        .Execute()
    )
    return jsonify({"log_id": log_id})


@app.route("/api/leaderboard", methods=["POST"])
@entry_required
def leaderboard(user_id):
    competition_id = request.json["competition_id"]
    entries = (
        QueryBuilder()
        .Select(
            "user_entries", "ue", ["user_id", "competition_id", "score", "mines_hit"]
        )
        .InnerJoin("users", "u", ["username", "id"], "ue.user_id = u.id")
        .AndWhere("ue.competition_id = {cid}", {"cid": competition_id})
        .Execute()
    )
    return jsonify(entries)


@app.route("/api/global_leaderboard", methods=["POST", "GET"])
@login_required
def global_leaderboard(user_id):
    users = QueryBuilder().Select("users", "u", ["id", "username", "elo"]).Execute()
    return jsonify(users)


@app.route("/api/activate", methods=["POST"])
@entry_required
def activate(user_id):
    competition_id = request.json["competition_id"]
    mutation_list = []
    score = 0
    usere_rec_check = (
        QueryBuilder()
        .Select("user_entries", "u", ["user_id", "competition_id", "last_ability_used"])
        .AndWhere(
            "u.user_id = {user_id} and u.competition_id = {cid} and (u.last_ability_used < {t} or u.last_ability_used is null)",
            {"user_id": user_id, "cid": competition_id, "t": now() - 1000 * 300},
        )
        .ExecuteOne()
    )
    if usere_rec_check is None:
        raise RuntimeError("Not time yet")
    flags = (
        QueryBuilder()
        .Select(
            "flags",
            "f",
            [
                "competition_id",
                "chunk_x",
                "chunk_y",
                "offset_x",
                "offset_y",
                "user_id",
                "state",
            ],
        )
        .AndWhere(
            "f.competition_id = {cid} and f.user_id = {user_id} and f.state = 0",
            {"cid": competition_id, "user_id": user_id},
        )
        .Execute()
    )
    game_map = empty_map()
    closed_map = empty_map()
    for flag in flags:
        cx = flag["chunk_x"]
        cy = flag["chunk_y"]
        ox = flag["offset_x"]
        oy = flag["offset_y"]
        rx = flag["chunk_x"] * 16 + flag["offset_x"]
        ry = flag["chunk_y"] * 16 + flag["offset_y"]
        tile = lgetm(game_map, closed_map, rx, ry, competition_id)
        if tile[0] == "x":
            score = score + 50
            ssetm(closed_map, rx, ry, competition_id, "m", mutation_list)
            (
                QueryBuilder()
                .Update("flags", ["state = 1"])
                .AndWhere(
                    "competition_id = {cid} and chunk_x = {cx} and chunk_y = {cy} and offset_x = {ox} and offset_y = {oy} and user_id = {user_id}",
                    {
                        "cid": competition_id,
                        "cx": cx,
                        "cy": cy,
                        "ox": ox,
                        "oy": oy,
                        "user_id": user_id,
                    },
                )
                .Execute()
            )
        else:
            score = score - 75
            ssetm(closed_map, rx, ry, competition_id, "c", mutation_list)
            (
                QueryBuilder()
                .Update("flags", ["state = 2"])
                .AndWhere(
                    "competition_id = {cid} and chunk_x = {cx} and chunk_y = {cy} and offset_x = {ox} and offset_y = {oy} and user_id = {user_id}",
                    {
                        "cid": competition_id,
                        "cx": cx,
                        "cy": cy,
                        "ox": ox,
                        "oy": oy,
                        "user_id": user_id,
                    },
                )
                .Execute()
            )
    QueryBuilder().Update(
        "user_entries", [f"score = score + {score}", f"last_ability_used = {now()}"]
    ).AndWhere(
        "user_id = {user_id} and competition_id = {cid}",
        {"cid": competition_id, "user_id": user_id},
    ).Execute()
    mutation_list_json = json.dumps(mutation_list, separators=(",", ":"))
    log_id = (
        QueryBuilder()
        .Insert(
            "event_log",
            {
                "competition_id": competition_id,
                "action": json.dumps(
                    {"modified_chunks": mutation_list_json}, separators=(",", ":")
                ),
            },
        )
        .Execute()
    )
    return jsonify({"log_id": log_id})


@app.route("/api/toggle_tile", methods=["POST"])
@entry_required
def toggle_tile(user_id):
    x = request.json["x"]
    y = request.json["y"]
    competition_id = request.json["competition_id"]
    game_map = empty_map()
    closed_map = empty_map()
    mutation_list = []
    tile_content = lgetm(game_map, closed_map, x, y, competition_id)

    cx = x // chunk_size
    cy = y // chunk_size
    ox = x % chunk_size
    oy = y % chunk_size
    if tile_content[1] == "-":
        # put flag
        ssetm(closed_map, x, y, competition_id, "f", mutation_list)
        (
            QueryBuilder()
            .Insert(
                "flags",
                {
                    "competition_id": competition_id,
                    "chunk_x": cx,
                    "chunk_y": cy,
                    "offset_x": ox,
                    "offset_y": oy,
                    "user_id": user_id,
                    "state": 0,
                },
                False,
            )
            .Execute()
        )
    elif tile_content[1] == "f":
        # check ownership
        # remove flag
        # put guess
        flag_rec = (
            QueryBuilder()
            .Select(
                "flags",
                "f",
                [
                    "competition_id",
                    "chunk_x",
                    "chunk_y",
                    "offset_x",
                    "offset_y",
                    "user_id",
                ],
            )
            .AndWhere(
                "f.competition_id = {cid} and f.chunk_x = {cx} and f.chunk_y = {cy} and f.offset_x = {ox} and f.offset_y = {oy} and f.user_id = {user_id}",
                {
                    "cid": competition_id,
                    "cx": cx,
                    "cy": cy,
                    "ox": ox,
                    "oy": oy,
                    "user_id": user_id,
                },
            )
            .ExecuteOne()
        )
        if flag_rec is not None:
            # flag is mine
            (
                QueryBuilder()
                .Delete("flags")
                .AndWhere(
                    "competition_id = {cid} and chunk_x = {cx} and chunk_y = {cy} and offset_x = {ox} and offset_y = {oy} and user_id = {user_id}",
                    {
                        "cid": competition_id,
                        "cx": cx,
                        "cy": cy,
                        "ox": ox,
                        "oy": oy,
                        "user_id": user_id,
                    },
                )
                .Execute()
            )
            (
                QueryBuilder()
                .Insert(
                    "guesses",
                    {
                        "competition_id": competition_id,
                        "chunk_x": cx,
                        "chunk_y": cy,
                        "offset_x": ox,
                        "offset_y": oy,
                        "user_id": user_id,
                    },
                    False,
                )
                .Execute()
            )
            ssetm(closed_map, x, y, competition_id, "g", mutation_list)
    elif tile_content[1] == "g":
        # check ownership
        # remove guess
        # set tile to -
        rec = (
            QueryBuilder()
            .Select(
                "guesses",
                "f",
                [
                    "competition_id",
                    "chunk_x",
                    "chunk_y",
                    "offset_x",
                    "offset_y",
                    "user_id",
                ],
            )
            .AndWhere(
                "f.competition_id = {cid} and f.chunk_x = {cx} and f.chunk_y = {cy} and f.offset_x = {ox} and f.offset_y = {oy} and f.user_id = {user_id}",
                {
                    "cid": competition_id,
                    "cx": cx,
                    "cy": cy,
                    "ox": ox,
                    "oy": oy,
                    "user_id": user_id,
                },
            )
            .ExecuteOne()
        )
        if rec is not None:
            (
                QueryBuilder()
                .Delete("guesses")
                .AndWhere(
                    "competition_id = {cid} and chunk_x = {cx} and chunk_y = {cy} and offset_x = {ox} and offset_y = {oy} and user_id = {user_id}",
                    {
                        "cid": competition_id,
                        "cx": cx,
                        "cy": cy,
                        "ox": ox,
                        "oy": oy,
                        "user_id": user_id,
                    },
                )
                .Execute()
            )
            ssetm(closed_map, x, y, competition_id, "-", mutation_list)
    elif tile_content[1] == "c" or tile_content[1] == "m":
        pass
    else:
        # tile is open
        pass
    mutation_list_json = json.dumps(mutation_list, separators=(",", ":"))
    log_id = (
        QueryBuilder()
        .Insert(
            "event_log",
            {
                "competition_id": competition_id,
                "action": json.dumps(
                    {"modified_chunks": mutation_list_json}, separators=(",", ":")
                ),
            },
        )
        .Execute()
    )
    return jsonify({"log_id": log_id})


@app.route("/api/enter_competition", methods=["POST"])
@login_required
def enter_competition(user_id):
    competition_id = request.json["competition_id"]
    data = request.json
    print(data)
    if "password" in data and data["password"] is not None:
        data["password"] = hashlib.sha256(bytes(data["password"], "utf-8")).hexdigest()
    else:
        data["password"] = None

    cid_holder = "{cid}"
    pass_holder = "{password}"
    comp_record = (
        QueryBuilder()
        .Select("competitions", "c", ["id", "password"])
        .AndWhere(
            f"c.id = {cid_holder} and {'c.password is null' if data['password'] is None else 'c.password = {password_holder}'}",
            {"cid": competition_id, "password": data["password"]},
        )
        .Build()
        .Explain()
        .ExecuteOne()
    )
    if comp_record is None:
        return jsonify({"result": "Wrong Password"})
    QueryBuilder().Insert(
        "user_entries",
        {"competition_id": competition_id, "user_id": user_id, "join_time": now()},
        False,
    ).Execute()
    return jsonify({"result": "Success"})


def reveal_tile(game_map, closed_map, x, y, competition_id, user_id, mutation_list):
    tile = lgetm(game_map, closed_map, x, y, competition_id)
    if tile[1] != "-":
        return
    elif tile[0] == "x":
        # register mine hit
        QueryBuilder().Update(
            "user_entries", ["mines_hit = mines_hit + 1", "score = score - 100"]
        ).AndWhere(
            "user_id = {uid} and competition_id = {cid}",
            {"uid": user_id, "cid": competition_id},
        ).Execute()
        ssetm(closed_map, x, y, competition_id, tile[0], mutation_list)
    elif tile[0] == "0":
        # reveal surroundings
        ssetm(closed_map, x, y, competition_id, tile[0], mutation_list)
        for ny in range(-1, 2):
            for nx in range(-1, 2):
                if abs(nx) == abs(ny):
                    continue
                if nx + x < 0 or ny + y < 0 or nx + x >= map_size or ny + y >= map_size:
                    continue
                c = lgetm(game_map, closed_map, nx + x, ny + y, competition_id)
                if c[0] != "x" and c[1] == "-":
                    reveal_tile(
                        game_map,
                        closed_map,
                        x + nx,
                        y + ny,
                        competition_id,
                        user_id,
                        mutation_list,
                    )
    else:
        ssetm(closed_map, x, y, competition_id, tile[0], mutation_list)
    return


# chunk data format is "x1234567890-fgcm" representing tile, data = "0000000" etc
# every char is chunk_x + k % size , chunk_y + k // size
def gen_chunk_data():
    data = ""
    for k in range(0, chunk_size ** 2):
        rand = random.uniform(0, 1)
        if rand < mine_chance:
            data = data + "x"
        else:
            data = data + "-"
    return data


def empty_map():
    game_map = []
    for y in range(0, map_chunk_ct):
        game_map.append([])
        for x in range(0, map_chunk_ct):
            game_map[y].append(None)
    return game_map


def lgetm(game_map, closed_map, x, y, competition_id):
    cx = x // chunk_size
    cy = y // chunk_size
    if game_map[cy][cx] is None:
        chunk = (
            QueryBuilder()
            .Select("chunks", "c", ["x", "y", "competition_id", "data", "cdata"])
            .AndWhere(
                "c.x = {cx} and c.y = {cy} and c.competition_id = {competition_id}",
                {"cx": cx, "cy": cy, "competition_id": competition_id},
            )
            .ExecuteOne()
        )
        game_map[cy][cx] = chunk["data"]
        closed_map[cy][cx] = chunk["cdata"]
    return (getm(game_map, x, y), getm(closed_map, x, y))


def ssetm(closed_map, x, y, competition_id, v, mutation_list):
    cx = x // chunk_size
    cy = y // chunk_size
    setm(closed_map, x, y, v)
    QueryBuilder().Update("chunks", [f"cdata = '{closed_map[cy][cx]}'"]).AndWhere(
        "competition_id = {cid} and x = {cx} and y = {cy}",
        {"cid": competition_id, "cx": cx, "cy": cy},
    ).Execute()
    matches = list(filter(lambda m: m[0] == cx and m[1] == cy, mutation_list))
    if len(matches) == 0:
        mutation_list.append([cx, cy])


def getm(game_map, x, y):
    cx = x // chunk_size
    cy = y // chunk_size
    offset = (y % chunk_size) * chunk_size + (x % chunk_size)
    return game_map[cy][cx][offset]


def setm(game_map, x, y, v):
    cx = x // chunk_size
    cy = y // chunk_size
    offset = (y % chunk_size) * chunk_size + (x % chunk_size)
    data = replace(game_map[cy][cx], offset, v)
    game_map[cy][cx] = data


def determine_num(game_map, x, y):
    mct = 0
    for ny in range(-1, 2):
        for nx in range(-1, 2):
            if nx == 0 and ny == 0:
                continue
            if nx + x < 0 or ny + y < 0 or nx + x >= map_size or ny + y >= map_size:
                continue
            c = getm(game_map, nx + x, ny + y)
            if c == "x":
                mct = mct + 1
    return mct


def solve_map(game_map):
    for x in range(0, map_size):
        for y in range(0, map_size):
            c = getm(game_map, x, y)
            if c == "-":
                num = determine_num(game_map, x, y)
                setm(game_map, x, y, str(num))


def start_competition_internal(data, user_id):
    cid = (
        QueryBuilder()
        .Insert(
            "competitions",
            {
                "title": data["title"],
                "start": data["start"],
                "end": data["end"],
                "password": data["password"],
            },
        )
        .Execute()
    )
    # generate chunks and build 1.stage map
    game_map = []
    closed_map = []
    for y in range(0, map_chunk_ct):
        game_map.append([])
        closed_map.append([])
        for x in range(0, map_chunk_ct):
            data = gen_chunk_data()
            game_map[y].append(data)
            closed_map[y].append("-" * (chunk_size ** 2))

    solve_map(game_map)
    for y in range(0, map_chunk_ct):
        for x in range(0, map_chunk_ct):
            QueryBuilder().Insert(
                "chunks",
                {
                    "competition_id": cid,
                    "x": x,
                    "y": y,
                    "data": game_map[y][x],
                    "cdata": closed_map[y][x],
                },
                False,
            ).Execute()


def replace(text, index=0, replacement=""):
    return "%s%s%s" % (text[:index], replacement, text[index + 1 :])
