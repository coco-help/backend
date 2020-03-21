import json

import glom
import requests
import sentry_sdk
from db import Helper
from pony.orm import db_session
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(
    dsn="https://c3490788b0fd46d09992667d01bb0352@sentry.io/5169971",
    integrations=[AwsLambdaIntegration()],
)


def register(event, context):
    user = json.loads(event["body"])

    print(f"Created user {user} in Database")

    first_name, _, last_name = user.pop("name").partition(" ")

    user = dict(**user, first_name=first_name, last_name=last_name)

    user["zip_code"] = user.pop("zip")
    zip_response = requests.get(
        f"https://public.opendatasoft.com/api/records/1.0/search/",
        params=dict(
            dataset="postleitzahlen-deutschland", facet="plz", q=user["zip_code"]
        ),
    )
    zip_json = zip_response.json()

    lat, lon = glom.glom(zip_json, ("records", 0, "fields", "geo_point_2d"))
    location = glom.glom(zip_json, ("records", 0, "fields", "note"))

    new_user = Helper(**user, lat=lat, lon=lon, location=location)

    body = {
        "message": new_user.first_name,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


@db_session
def phone(event, context):
    helper = Helper[1]
    body = {
        "phone": helper.phone,
        "name": f"{helper.first_name} {helper.last_name}",
        "location": "Berlin Mitte",
    }

    return {"statusCode": 200, "body": json.dumps(body)}
