from os import environ

from pony.orm import Database, Required

db = Database()


class Helper(db.Entity):
    phone = Required(str)
    first_name = Required(str)
    last_name = Required(str)
    email = Required(str)
    lon = Required(float)
    lat = Required(float)
    zip_code = Required(str)
    location_name = Required(str)
    is_active = Required(bool)


db.bind(
    provider="postgres",
    host=environ["DB_HOST"],
    user=environ["DB_USER"],
    password=environ["DB_PASSWORD"],
    database="postgres",
)
db.generate_mapping(create_tables=False)
