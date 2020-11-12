import os
import sys

import psycopg2 as dbapi2


INIT_STATEMENTS = [
    "CREATE TABLE IF NOT EXISTS migration_version (version INTEGER)",
]

MIGRATIONS = [
    [
        "CREATE TABLE test (asd INTEGER)"
    ],
    [
        "DROP TABLE test"
    ]
]


def current_version(cursor):
    cursor.execute("SELECT version FROM migration_version")
    result = cursor.fetchall()
    if len(result) == 0:
        cursor.execute("INSERT INTO migration_version VALUES (0)")
        return 0
    return result[0][0]

def inc_version(cursor):
    cursor.execute("UPDATE migration_version SET version = version + 1")

def initialize(url):
    with dbapi2.connect(url) as connection:
        cursor = connection.cursor()
        for statement in INIT_STATEMENTS:
            cursor.execute(statement)
        version = current_version(cursor)
        for k in range(version, len(MIGRATIONS)):
            for q in MIGRATIONS[k]:
                cursor.execute(q)
            inc_version(cursor)
        cursor.close()


if __name__ == "__main__":
    url = os.getenv("DATABASE_URL")
    if url is None:
        print("Usage: DATABASE_URL=url python dbinit.py", file=sys.stderr)
        sys.exit(1)
    initialize(url)
