from ..init import app
from flask import render_template
from ..queryBuilders.qb import QueryBuilder
from ..utils import *


@app.route("/")
@login_optional
def home_page(user):
    return render_template("competitions.html", data={"user": user})


@app.route("/competition_page")
@login_required
def competition_page(user_id):
    user = (
        QueryBuilder()
        .Select("users", "u", ["id", "username", "elo"])
        .AndWhere("u.id = {id}", {"id": user_id})
        .ExecuteOne()
    )
    return render_template(
        "game.html", data={"competition_id": request.args.get("cid"), "user": user}
    )


@app.route("/login_page")
@login_optional
def login_page(user):
    return render_template("login.html", data={"user": user})


@app.route("/leaderboards_page")
@login_optional
def leaderboards_page(user):
    return render_template("leaderboards.html", data={"user": user})


@app.route("/profile_page")
@login_required
def profile_page(user_id):
    user = (
        QueryBuilder()
        .Select("users", "u", ["id", "username", "elo"])
        .AndWhere("u.id = {id}", {"id": user_id})
        .ExecuteOne()
    )
    return render_template("profile.html", data={"user": user})
