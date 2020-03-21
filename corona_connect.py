import json

import glom
import requests
import sentry_sdk
from db import Helper
from pony.orm import db_session, select
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(
    dsn="https://c3490788b0fd46d09992667d01bb0352@sentry.io/5169971",
    integrations=[AwsLambdaIntegration()],
)


@db_session
def register(event, context):
    user = json.loads(event["body"])

    first_name, _, last_name = user.pop("name").partition(" ")

    user = dict(**user, first_name=first_name, last_name=last_name)

    user["zip_code"] = str(user.pop("zip"))
    zip_response = requests.get(
        f"https://public.opendatasoft.com/api/records/1.0/search/",
        params=dict(
            dataset="postleitzahlen-deutschland", facet="plz", q=user["zip_code"]
        ),
    )
    zip_json = zip_response.json()

    lat, lon = glom.glom(zip_json, ("records", [("fields", "geo_point_2d")]))[0]
    location = glom.glom(zip_json, ("records", [("fields", "note")]))[0]

    user.update(lat=lat, lon=lon, location_name=location)

    print("Creating user with", user)
    new_user = Helper(**user)
    print("Created user", new_user)

    body = {
        "message": new_user.first_name,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


@db_session
def phone(event, context):
    requester_lat = 0.0
    requester_lon = 0.0
    best_helpers = select(h for h in Helper) \
        .order_by(lambda h: (h.lon - requester_lon) ** 2 + (h.lat - requester_lat) ** 2)
    helper = list(best_helpers)[0]
    body = {
        "phone": helper.phone,
        "name": f"{helper.first_name} {helper.last_name}",
        "location": helper.location_name,
    }

    return {"statusCode": 200, "body": json.dumps(body)}
