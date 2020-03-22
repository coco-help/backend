import datetime

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
    verify_code = Optional(str, nullable=True)
    last_called = Required(datetime.datetime)
