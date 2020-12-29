from ..init import app
from flask import Flask, request, jsonify, make_response
from ..queryBuilders.qb import QueryBuilder
import os
from ..utils import *
import time
import hashlib
import random
import json


@app.route("/api/get_log", methods=["POST"])
def get_log():
    log = (
        QueryBuilder()
        .Select("event_log", "e", ["id", "competition_id", "action"])
        .AndWhere("e.id = {id}", {"id": request.json["log_id"]})
        .ExecuteOne()
    )
    return jsonify(log)


@app.route("/api/get_logs_after", methods=["POST"])
def get_logs_after():
    logs = (
        QueryBuilder()
        .Select("event_log", "e", ["id", "competition_id", "action"])
        .AndWhere(
            "e.id > {id} and e.competition_id = {cid}",
            {"id": request.json["log_id"], "cid": request.json["competition_id"]},
        )
        .Execute()
    )
    return jsonify(logs)


@app.route("/api/get_past_logs_ids", methods=["POST"])
def get_past_logs_ids():
    logs = (
        QueryBuilder()
        .Select("event_log", "e", ["id", "competition_id"])
        .AndWhere(
            "e.competition_id = {cid}",
            {"cid": request.json["competition_id"]},
        )
        .Execute()
    )
    return jsonify(logs)
