import datetime
from os import environ

from pony.orm import Database, Optional, PrimaryKey, Required

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

    def to_dict(self):
        return super(Helper, self).to_dict(exclude=["last_called", "verify_code"])


def setup():
    db.bind(
        provider="postgres",
        host=environ["DB_HOST"],
        user=environ["DB_USER"],
        password=environ["DB_PASSWORD"],
        database="postgres",
    )
    db.generate_mapping(create_tables=False)
