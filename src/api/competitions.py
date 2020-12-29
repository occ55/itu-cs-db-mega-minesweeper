from ..init import app
from flask import Flask, request, jsonify, make_response
from ..queryBuilders.qb import QueryBuilder
import os
from ..utils import *
import time
import hashlib
import random

now = lambda: time.time_ns() // 1000000

chunk_size = 16
map_size = 128
map_chunk_ct = map_size // chunk_size
mine_chance = 0.3


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
@login_required  # TODO: entry required
def get_field(user_id):
    chunks = (
        QueryBuilder()
        .Select("chunks", "c", ["competition_id", "x", "y", "cdata"])
        .AndWhere("c.competition_id = {competition_id}", request.json)
        .Execute()
    )
    return jsonify(chunks)


@app.route("/api/open_tile", methods=["POST"])
@login_required  # TODO: entry required
def open_tile(user_id):
    x = request.json["x"]
    y = request.json["y"]
    competition_id = request.json["competition_id"]
    game_map = empty_map()
    closed_map = empty_map()
    print(lgetm(game_map, closed_map, x, y, competition_id))
    return jsonify({})


@app.route("/api/debug_tile", methods=["POST"])
@login_required  # TODO: entry required
def debug_tile(user_id):
    x = request.json["x"]
    y = request.json["y"]
    competition_id = request.json["competition_id"]
    game_map = empty_map()
    closed_map = empty_map()
    res = lgetm(game_map, closed_map, x, y, competition_id)
    return jsonify({"data": res[0], "cdata": res[1]})


# chunk data format is "x1234567890-fgc" representing tile, data = "0000000" etc
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
