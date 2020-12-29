from .queryBuilders.qb import QueryBuilder
import threading
import time
import hashlib
import random
import json
from .api.competitions import start_competition_internal

now = lambda: time.time_ns() // 1000000


def end_competitions():
    comps = (
        QueryBuilder()
        .Select("competitions", "c", ["id", "end", "is_done"])
        .AndWhere('c."end" < {n} and c.is_done is null', {"n": now()})
        .Execute()
    )
    for comp in comps:
        # clear logs
        QueryBuilder().Delete("event_log").AndWhere(
            "competition_id = {id}", {"id": comp["id"]}
        ).Execute()
        # Get leaderboard, Give upper half +10 elo, lower half -10 elo
        entries = (
            QueryBuilder()
            .Select("user_entries", "u", ["user_id", "competition_id", "score"])
            .AndWhere("u.competition_id = {id}", {"id": comp["id"]})
            .Execute()
        )
        entries.sort(key=lambda e: e["score"], reverse=True)
        for k in range(0, len(entries)):
            if k < (len(entries) // 2) + 1:
                QueryBuilder().Update("users", ["elo = elo + 10"]).AndWhere(
                    "id = {id}", {"id": entries[k]["user_id"]}
                ).Execute()
            else:
                QueryBuilder().Update("users", ["elo = elo - 10"]).AndWhere(
                    "id = {id}", {"id": entries[k]["user_id"]}
                ).Execute()

        QueryBuilder().Update("competitions", ["is_done = 1"]).AndWhere(
            "id = {id}", {"id": comp["id"]}
        ).Execute()


def create_periodic_comp():
    start_competition_internal(
        {
            "title": "Periodic Competition " + str(random.randint(0, 999999)),
            "start": now(),
            "end": now() + 1800000,
            "password": None,
        },
        1,
    )


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()

    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


end_competitions()
create_periodic_comp()
set_interval(end_competitions, 60)
set_interval(create_periodic_comp, 60 * 30)
