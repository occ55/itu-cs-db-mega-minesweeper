from functools import wraps
from flask import g, request, redirect, url_for
from .queryBuilders.qb import QueryBuilder
import threading
import time
import hashlib
import random
import json


now = lambda: time.time_ns() // 1000000


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get("session_id")
        if session_id is not None:
            session_record = (
                QueryBuilder()
                .Select("sessions", "s", ["session_id", "user_id"])
                .AndWhere("s.session_id = {sid}", {"sid": session_id})
                .ExecuteOne()
            )
            if session_record is not None:
                kwargs["user_id"] = session_record["user_id"]
                return f(*args, **kwargs)
        raise RuntimeError("Login Required")

    return decorated_function


last_error = None


def EP(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global last_error
        try:
            kwargs["last_error"] = last_error
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            last_error = str(e)
            if request.url != "/":
                return redirect("/")
            else:
                raise RuntimeError("Main Page Error")

    return decorated_function


def set_last_error(val):
    global last_error
    last_error = val


def login_optional(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get("session_id")
        if session_id is not None:
            session_record = (
                QueryBuilder()
                .Select("sessions", "s", ["session_id", "user_id"])
                .AndWhere("s.session_id = {sid}", {"sid": session_id})
                .ExecuteOne()
            )
            if session_record is not None:
                user = (
                    QueryBuilder()
                    .Select("users", "u", ["id", "username", "elo"])
                    .AndWhere("u.id = {id}", {"id": session_record["user_id"]})
                    .ExecuteOne()
                )
                kwargs["user"] = user
                return f(*args, **kwargs)
        kwargs["user"] = None
        return f(*args, **kwargs)

    return decorated_function


def entry_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.cookies.get("session_id")
        if session_id is not None:
            session_record = (
                QueryBuilder()
                .Select("sessions", "s", ["session_id", "user_id"])
                .AndWhere("s.session_id = {sid}", {"sid": session_id})
                .ExecuteOne()
            )
            if session_record is not None:
                entry_record = (
                    QueryBuilder()
                    .Select("user_entries", "u", ["user_id", "competition_id"])
                    .AndWhere(
                        "u.user_id = {uid} and competition_id = {cid}",
                        {
                            "uid": session_record["user_id"],
                            "cid": request.json["competition_id"],
                        },
                    )
                    .ExecuteOne()
                )
                if entry_record is not None:
                    kwargs["user_id"] = session_record["user_id"]
                    return f(*args, **kwargs)
        raise RuntimeError("Entry Required")

    return decorated_function
