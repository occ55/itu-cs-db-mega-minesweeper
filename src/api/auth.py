from ..init import app
from flask import Flask, request, jsonify, make_response
from ..queryBuilders.qb import QueryBuilder
import hashlib
import os, binascii
from ..utils import *

import time

now = lambda: time.time_ns() // 1000000


@app.route("/api/login", methods=["POST"])
@EP
def login(last_error):
    data = request.json
    if "password" in data:
        data["password"] = hashlib.sha256(bytes(data["password"], "utf-8")).hexdigest()
    user = (
        QueryBuilder()
        .Select("users", "u", ["id"])
        .AndWhere("u.username = {username} and u.password = {password}", data)
        .ExecuteOne()
    )
    old_session = request.cookies.get("session_id")
    print(old_session)
    resp = make_response(jsonify({}))
    if user is not None:
        if old_session is None:
            session_id = binascii.b2a_hex(os.urandom(32)).decode("utf-8")
            resp.set_cookie("session_id", session_id)
            QueryBuilder().Insert(
                "sessions",
                {"session_id": session_id, "user_id": user["id"]},
                False,
            ).Execute()
        else:
            session_record = (
                QueryBuilder()
                .Select("sessions", "s", ["session_id", "user_id"])
                .AndWhere("s.session_id = {sid}", {"sid": old_session})
                .ExecuteOne()
            )
            if session_record is None:
                QueryBuilder().Insert(
                    "sessions",
                    {"session_id": old_session, "user_id": user["id"]},
                    False,
                ).Execute()
            elif session_record["user_id"] != user["id"]:
                raise RuntimeError("Session is logged in with different user")
            else:
                pass
    else:
        raise RuntimeError("Password or username is wrong")
    return resp


@app.route("/api/register", methods=["POST"])
@EP
def register(last_error):
    session_id_old = request.cookies.get("session_id")
    if session_id_old is not None:
        QueryBuilder().Delete("sessions").AndWhere(
            "session_id = {sid}", {"sid": session_id_old}
        ).Execute()
    data = request.json
    if "password" in data:
        if len(data["password"]) < 2:
            raise RuntimeError("Password is too short")
    if "password" in data:
        data["password"] = hashlib.sha256(bytes(data["password"], "utf-8")).hexdigest()
    user_id = (
        QueryBuilder()
        .Insert(
            "users",
            {
                "username": data["username"],
                "password": data["password"],
                "created_at": now(),
            },
        )
        .Execute()
    )
    session_id = binascii.b2a_hex(os.urandom(32)).decode("utf-8")
    (
        QueryBuilder()
        .Insert("sessions", {"session_id": session_id, "user_id": user_id}, False)
        .Execute()
    )
    resp = make_response(jsonify({"id": user_id}))
    resp.set_cookie("session_id", session_id)
    return resp


@app.route("/api/logout", methods=["POST"])
def logout():
    resp = make_response(jsonify({}))
    resp.set_cookie("session_id", "", expires=0)
    return resp


@app.route("/api/me", methods=["GET", "POST"])
@login_required
def me(user_id):
    user = (
        QueryBuilder()
        .Select("users", "u", ["username", "id", "elo"])
        .AndWhere("u.id = {id}", {"id": user_id})
        .ExecuteOne()
    )
    return jsonify(user)


@app.route("/api/clear_error", methods=["GET", "POST"])
def clear_error():
    set_last_error(None)
    return "{}"


@app.route("/api/delete_me", methods=["GET", "POST"])
@EP
@login_required
def delete_me(user_id, last_error):
    QueryBuilder().Delete("sessions").AndWhere(
        "user_id = {uid}", {"uid": user_id}
    ).Execute()
    QueryBuilder().Delete("user_entries").AndWhere(
        "user_id = {uid}", {"uid": user_id}
    ).Execute()
    QueryBuilder().Delete("flags").AndWhere(
        "user_id = {uid}", {"uid": user_id}
    ).Execute()
    QueryBuilder().Delete("guesses").AndWhere(
        "user_id = {uid}", {"uid": user_id}
    ).Execute()
    QueryBuilder().Delete("users").AndWhere("id = {uid}", {"uid": user_id}).Execute()
    return "{}"
