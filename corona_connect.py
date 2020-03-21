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


def lookup_zip(zip_code):
    zip_response = requests.get(
        f"https://public.opendatasoft.com/api/records/1.0/search/",
        params=dict(dataset="postleitzahlen-deutschland", facet="plz", q=zip_code,),
    )
    zip_json = zip_response.json()

    return glom.glom(
        zip_json,
        (
            "records",
            [
                (
                    "fields",
                    {
                        "lat": glom.T["geo_point_2d"][0],
                        "lon": glom.T["geo_point_2d"][1],
                        "location_name": "note",
                    },
                )
            ],
            glom.T[0],
        ),
    )


def make_response(body, status_code=200, headers=None):
    headers = headers or {}
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {"Access-Control-Allow-Origin": "*", **headers},
    }


@db_session
def register(event, context):
    user = json.loads(event["body"])

    first_name, _, last_name = user.pop("name").partition(" ")

    user = dict(**user, first_name=first_name, last_name=last_name)

    user["zip_code"] = str(user.pop("zip"))

    try:
        user.update(lookup_zip(user["zip_code"]))
    except glom.PathAccessError:
        return make_response(
            {"error": "invalid_zip_code", "value": user["zip_code"]}, status_code=400
        )

    print("Creating user with", user)
    new_user = Helper(**user, is_active=user.get("is_active", True))
    print("Created user", new_user)

    body = {
        "message": new_user.first_name,
    }

    return make_response(body)


def verify(event, context):
    if (
        event["queryStringParameters"] is None
        or "code" not in event["queryStringParameters"]
        or "phone" not in event["queryStringParameters"]
    ):
        body = {"error": "'code' and 'phone' query paramters are needed."}
        return make_response(body, status_code=400)

    body = {
        "message": event["queryStringParameters"]["phone"],
    }

    return make_response(body)


@db_session
def get_helper(event, context):
    if event["pathParameters"] is None or "phone" not in event["pathParameters"]:
        body = {"error": "'phone' path paramter is needed"}
        return {"statusCode": 400, "body": json.dumps(body)}

    requested_phone = event["pathParameters"]["phone"]
    helper = Helper.get(phone=requested_phone)
    if helper is None:
        body = {"error": "No helper for this number"}
        return {"statusCode": 404, "body": json.dumps(body)}
    else:
        return {"statusCode": 200, "body": json.dumps(helper.to_dict())}


@db_session
def update_helper(event, context):
    if event["pathParameters"] is None or "phone" not in event["pathParameters"]:
        body = {"error": "'phone' path paramter is needed"}
        return {"statusCode": 400, "body": json.dumps(body)}

    requested_phone = event["pathParameters"]["phone"]
    helper_update = json.loads(event["body"])

    helper = Helper.get(phone=requested_phone)
    if helper is None:
        body = {"error": "No helper for this number"}
        return {"statusCode": 404, "body": json.dumps(body)}
    else:
        helper.set(**helper_update)
        return {"statusCode": 200, "body": json.dumps(helper.to_dict())}


@db_session
def delete_helper(event, context):
    if event["pathParameters"] is None or "phone" not in event["pathParameters"]:
        body = {"error": "'phone' path paramter is needed"}
        return {"statusCode": 400, "body": json.dumps(body)}

    requested_phone = event["pathParameters"]["phone"]
    helper = Helper.get(phone=requested_phone)
    if helper is None:
        body = {"error": "No helper for this number"}
        return {"statusCode": 404, "body": json.dumps(body)}
    else:
        helper.delete()
        body = {"message": "deleted"}
        return {"statusCode": 200, "body": json.dumps(body)}


@db_session
def phone(event, context):
    if (
        event["queryStringParameters"] is None
        or "zip" not in event["queryStringParameters"]
    ):
        body = {"error": "'zip' query paramter is needed"}
        return make_response(body, status_code=400)

    zip_code = event["queryStringParameters"]["zip"]
    try:
        zip_point = lookup_zip(zip_code)
    except glom.PathAccessError:
        return make_response(
            {"error": "invalid_zip_code", "value": zip_code}, status_code=400
        )
    requester_lat = zip_point["lat"]
    requester_lon = zip_point["lon"]

    helper = (
        select(h for h in Helper if h.is_active)
        .order_by(lambda h: (h.lon - requester_lon) ** 2 + (h.lat - requester_lat) ** 2)
        .first()
    )
    if helper is None:
        body = {"error": "No helpers available"}
        return make_response(body, status_code=500)
    else:
        body = {
            "phone": helper.phone,
            "name": f"{helper.first_name} {helper.last_name}",
            "location": helper.location_name,
        }

        return make_response(body)
