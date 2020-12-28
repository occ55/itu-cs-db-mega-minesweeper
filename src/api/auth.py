from ..init import app
from flask import Flask, request, jsonify, make_response
from ..queryBuilders.qb import QueryBuilder
import hashlib
import os, binascii
from ..utils import *


@app.route("/api/login", methods=["POST"])
def login():
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
    resp = make_response(jsonify({}))
    if user is not None:
        if old_session is None:
            session_id = binascii.b2a_hex(os.urandom(32)).decode("utf-8")
            resp.set_cookie("session_id", session_id)
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
def register():
    session_id_old = request.cookies.get("session_id")
    if session_id_old is not None:
        return jsonify({"error": "Already logged in"})
    data = request.json
    if "password" in data:
        data["password"] = hashlib.sha256(bytes(data["password"], "utf-8")).hexdigest()
    user_id = (
        QueryBuilder()
        .Insert("users", {"username": data["username"], "password": data["password"]})
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
