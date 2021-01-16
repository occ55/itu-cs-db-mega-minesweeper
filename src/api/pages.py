from ..init import app
from flask import render_template
from ..queryBuilders.qb import QueryBuilder
from ..utils import *


@app.route("/")
@EP
@login_optional
def home_page(user, last_error):
    return render_template(
        "competitions.html", data={"user": user}, last_error=last_error
    )


@app.route("/competition_page")
@EP
@login_required
def competition_page(user_id, last_error):
    user = (
        QueryBuilder()
        .Select("users", "u", ["id", "username", "elo"])
        .AndWhere("u.id = {id}", {"id": user_id})
        .ExecuteOne()
    )
    entry = (
        QueryBuilder()
        .Select("user_entries", "u", ["user_id"])
        .AndWhere(
            "u.user_id = {user_id} and u.competition_id = {cid}",
            {"user_id": user_id, "cid": request.args.get("cid")},
        )
        .ExecuteOne()
    )
    if entry is None:
        return redirect("/")
    return render_template(
        "game.html",
        data={"competition_id": request.args.get("cid"), "user": user},
        last_error=last_error,
    )


@app.route("/login_page")
@EP
@login_optional
def login_page(user, last_error):
    return render_template("login.html", data={"user": user}, last_error=last_error)


@app.route("/leaderboards_page")
@EP
@login_optional
def leaderboards_page(user, last_error):
    return render_template(
        "leaderboards.html", data={"user": user}, last_error=last_error
    )


@app.route("/profile_page")
@EP
@login_required
def profile_page(user_id, last_error):
    user = (
        QueryBuilder()
        .Select("users", "u", ["id", "username", "elo"])
        .AndWhere("u.id = {id}", {"id": user_id})
        .ExecuteOne()
    )
    return render_template("profile.html", data={"user": user}, last_error=last_error)
