import datetime
import logging
import os
from os import environ

import psycopg2
from pony.orm import Database, Optional, PrimaryKey, Required

LOGGER = logging.getLogger(__name__)

db = Database()


class Helper(db.Entity):
    phone = PrimaryKey(str)
    first_name = Required(str)
    last_name = Required(str)
    email = Required(str)
    lon = Required(float)
    lat = Required(float)
    zip_code = Required(str)
    location_name = Required(str)
    is_active = Required(bool)
    verified = Required(bool, default=False)
    last_called = Required(datetime.datetime, hidden=True)
    verify_code = Optional(str, nullable=True, hidden=True)


def ensure_migration_version_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS _migration_version(
                version INTEGER
            );
            """
        )


def ensure_migration_version_row(conn):
    ensure_migration_version_table(conn)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*) FROM _migration_version;
            """
        )
        count = cur.fetchone()[0]

        if count < 1:
            cur.execute(
                """
                INSERT INTO _migration_version(version)
                VALUES (NULL);
                """
            )


def get_migration_version(conn):
    ensure_migration_version_row(conn)

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM _migration_version")
        return cur.fetchone()[0]


def set_migration_version(conn, version):
    with conn.cursor() as cur:
        cur.execute("UPDATE _migration_version SET version = %s", (version,))


def apply_migrations():
    conn = psycopg2.connect(
        host=environ["DB_HOST"],
        user=environ["DB_USER"],
        password=environ["DB_PASSWORD"],
        dbname="postgres",
    )

    current_version = get_migration_version(conn)
    LOGGER.info(f"Current migration version is {current_version}")

    for migration_dir in os.listdir("migrations"):
        migration_version = int(migration_dir.split(sep="_")[0])

        if current_version is not None and migration_version > current_version:
            LOGGER.info(f"Applying migration version {migration_version}")
            with open(
                f"migrations/{migration_dir}/up.sql", "r"
            ) as migration_sql, conn.cursor() as cur:
                cur.execute(migration_sql.read())

            current_version = migration_version

    set_migration_version(conn, current_version)
    conn.commit()


def setup():
    apply_migrations()

    db.bind(
        provider="postgres",
        host=environ["DB_HOST"],
        user=environ["DB_USER"],
        password=environ["DB_PASSWORD"],
        database="postgres",
    )
    db.generate_mapping(create_tables=False)
