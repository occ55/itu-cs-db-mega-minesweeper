from functools import wraps
from flask import g, request, redirect, url_for
from .queryBuilders.qb import QueryBuilder


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
