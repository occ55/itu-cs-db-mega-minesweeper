import os
import sys

import psycopg2 as dbapi2

INIT_STATEMENTS = [
    "CREATE TABLE IF NOT EXISTS migration_version (version INTEGER)",
]

MIGRATIONS = [
    [open("./src/migrations/initial_db.sql").read()],
    [
        """
ALTER TABLE users
ALTER COLUMN username TYPE character varying(255),
ALTER COLUMN password TYPE character varying(255);

ALTER TABLE sessions
ALTER COLUMN session_id TYPE character varying(255);

ALTER TABLE competitions
ALTER COLUMN title TYPE character varying(255),
ALTER COLUMN password TYPE character varying(255);

ALTER TABLE chunks
ALTER COLUMN data TYPE character varying(255);
"""
    ],
    ["ALTER TABLE users ADD CONSTRAINT usernameunique UNIQUE (username);"],
]


def current_version(cursor):
    cursor.execute("SELECT version FROM migration_version")
    result = cursor.fetchall()
    if len(result) == 0:
        cursor.execute('INSERT INTO "migration_version" VALUES (0)')
        return 0
    return result[0][0]


def inc_version(cursor):
    cursor.execute('UPDATE public."migration_version" SET version = version + 1')


def initialize(url):
    with dbapi2.connect(url) as connection:
        cursor = connection.cursor()
        for statement in INIT_STATEMENTS:
            cursor.execute(statement)
            connection.commit()
        version = current_version(cursor)
        connection.commit()
        for k in range(version, len(MIGRATIONS)):
            for q in MIGRATIONS[k]:
                cursor.execute(q)
                connection.commit()
            inc_version(cursor)
            connection.commit()
        cursor.close()


if __name__ == "__main__":
    url = os.getenv("DATABASE_URL")
    if url is None:
        print("Usage: DATABASE_URL=url python dbinit.py", file=sys.stderr)
        sys.exit(1)
    initialize(url)
