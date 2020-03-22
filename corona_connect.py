import datetime
import json
import logging
import os
import random
import urllib.parse

import db
import glom
import jwt
import phonenumbers
import requests
import sentry_sdk
import yarl
from db import Helper
from pony.orm import ObjectNotFound, db_session
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
from twilio.rest import Client

LOGGER = logging.getLogger(__name__)

EARTH_RADIUS_METERS = 6_371_000

sentry_sdk.init(
    dsn="https://c3490788b0fd46d09992667d01bb0352@sentry.io/5169971",
    integrations=[AwsLambdaIntegration()],
)

FROM_PHONE_NUMBER = os.environ.get("TWILIO_FROM_PHONE_NUMBER", "+1 956 247 4513")
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

USE_TWILIO = "TWILIO_ACCOUNT_SID" in os.environ and "TWILIO_AUTH_TOKEN" in os.environ
if USE_TWILIO:
    twilio = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
else:
    LOGGER.warning(
        "Not using TWILIO because $TWILIO_ACCOUNT_SID or $TWILIO_AUTH_TOKEN not set."
    )
    from unittest.mock import Mock

    twilio = Mock(spec=Client)

db.setup()


def one_time_pin() -> str:
    return str(random.randint(0, 9999)).zfill(4)  # nosec


def send_sms(to, message):
    twilio.messages.create(
        body=message, from_=FROM_PHONE_NUMBER, to=to,
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


def make_response(body, status_code=200, *, headers=None):
    headers = headers or {}
    sentry_sdk.add_breadcrumb(
        category="response",
        message=f"dumping {body} with headers: {headers}",
        level="info",
        type="http",
    )
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {"Access-Control-Allow-Origin": "*", **headers},
    }


def normalize_phone(phone):
    phone_parsed = phonenumbers.parse(phone, region="DE")
    return phonenumbers.format_number(phone_parsed, phonenumbers.PhoneNumberFormat.E164)


def validate_phone(phone):
    phone_parsed = phonenumbers.parse(phone, region="DE")
    if not (
        phonenumbers.is_possible_number(phone_parsed)
        and phonenumbers.is_valid_number(phone_parsed)
    ):
        raise phonenumbers.NumberParseException(
            "NOT_A_NUMBER", "Invalid or impossible number"
        )


def authorize(event, context):
    sentry_sdk.add_breadcrumb(event)
    try:
        token = event["authorizationToken"]
        decoded_token = jwt.decode(token, key=JWT_SECRET, algorithms=[JWT_ALGORITHM])
        sentry_sdk.add_breadcrumb(decoded_token)
        phone_number = decoded_token["phone"]
    except (KeyError, jwt.PyJWTError, glom.PathAccessError):
        effect = "Deny"
    else:
        # only accessing ourselves is allowed
        if (
            normalize_phone(
                urllib.parse.unquote_plus(yarl.URL(event["methodArn"]).parts[-1])
            )
            == phone_number
        ):
            effect = "Allow"
        else:
            effect = "Deny"

    policy = {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": event["methodArn"],
                }
            ],
        },
    }
    return policy


@db_session
def register(event, context):
    LOGGER.info("received", event)
    user = json.loads(event["body"])

    first_name, _, last_name = user.pop("name").partition(" ")

    user = dict(**user, first_name=first_name, last_name=last_name)

    user["zip_code"] = str(user.pop("zip"))

    try:
        user["phone"] = normalize_phone(user["phone"])
        validate_phone(user["phone"])
    except phonenumbers.NumberParseException:
        body = {"error": "invalid_field", "field": "phone"}
        return make_response(body, 422)

    user.setdefault("is_active", True)
    user.setdefault("last_called", datetime.datetime.utcnow())

    try:
        user.update(lookup_zip(user["zip_code"]))
    except glom.PathAccessError:
        return make_response(
            {"error": "invalid_zip_code", "value": user["zip_code"]}, status_code=400
        )

    phone_number = normalize_phone(user["phone"])
    if Helper.get(phone=phone_number) is not None:
        body = {"error": "Phone number already registered"}
        return make_response(body, status_code=409)

    LOGGER.info("Creating user with", user)
    new_user = Helper(**user, verify_code=one_time_pin())
    LOGGER.info("Created user", new_user.to_dict())

    url = yarl.URL.build(
        scheme="https",
        host="coco-frontend.now.sh",
        path=f"/auth/{new_user.phone}",
        query={"code": new_user.verify_code},
    )
    LOGGER.info(f"Send {url} to {new_user.phone}")
    message = (
        f"Hallo {new_user.first_name}, "
        f"Danke das du helfen möchtest.\n"
        f"Dein Code ist {new_user.verify_code}\n"
        f"Oder verifiziere dich indem du den folgenden Link öffnest:\n{url}",
    )
    send_sms(new_user.phone, message)

    body = {
        "message": "User created",
        "phone": new_user.phone,
    }

    return make_response(body)


@db_session
def login(event, context):
    if event["pathParameters"] is None or "phone" not in event["pathParameters"]:
        body = {"error": "missing_parameter", "value": "phone"}
        return make_response(body, 400)
    user_phone = normalize_phone(
        urllib.parse.unquote_plus(event["pathParameters"]["phone"])
    )
    try:
        user = Helper[user_phone]
    except ObjectNotFound:
        body = {"error": "helper_not_found", "value": user_phone}
        return make_response(body, 404)

    user.verify_code = one_time_pin()
    url = yarl.URL.build(
        scheme="https",
        host="coco-frontend.now.sh",
        path=f"/auth/{user.phone}",
        query={"code": user.verify_code},
    )
    message = (
        f"Hier dein Code zum einloggen: {user.verify_code}\n"
        f"Oder verifiziere dich indem du den folgenden Link öffnest:\n{url}"
    )
    send_sms(user.phone, message)
    return make_response({"message": "user_message_sent"})


@db_session
def verify(event, context):
    if (
        event["queryStringParameters"] is None
        or event["pathParameters"] is None
        or "code" not in event["queryStringParameters"]
        or "phone" not in event["pathParameters"]
    ):
        body = {"error": "'code' query parameter is needed."}
        return make_response(body, status_code=400)

    phone_number = normalize_phone(
        urllib.parse.unquote_plus(event["pathParameters"]["phone"])
    )
    verify_code = event["queryStringParameters"]["code"]

    try:
        helper = Helper[phone_number]
    except ObjectNotFound:
        body = {"error": "verification_failed"}
        return make_response(body, status_code=404)

    if helper.verify_code != verify_code:
        body = {"error": "verification_failed"}
        return make_response(body, status_code=404)

    helper.verified = True
    helper.verify_code = None

    issued_at = datetime.datetime.now()
    token = jwt.encode(
        {
            "iat": issued_at,
            "exp": issued_at + datetime.timedelta(minutes=15),
            "phone": helper.phone,
        },
        key=JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    ).decode("utf8")

    body = {
        "message": "user_verified",
        "user": {
            "phone": helper.phone,
            "first_name": helper.first_name,
            "last_name": helper.last_name,
        },
        "token": token,
    }

    if "next" in event["queryStringParameters"]:
        return make_response(
            body,
            status_code=301,
            headers={"Location": event["queryStringParameters"]["next"]},
        )

    return make_response(body)


@db_session
def get_helper(event, context):
    if event["pathParameters"] is None or "phone" not in event["pathParameters"]:
        body = {"error": "'phone' path paramter is needed"}
        return {"statusCode": 400, "body": json.dumps(body)}

    requested_phone = urllib.parse.unquote_plus(event["pathParameters"]["phone"])
    helper = Helper.get(phone=normalize_phone(requested_phone))
    if helper is None:
        body = {"error": "No helper for this number"}
        return make_response(body, 404)
    else:
        return make_response(helper.to_dict(), 200)


@db_session
def update_helper(event, context):
    if event["pathParameters"] is None or "phone" not in event["pathParameters"]:
        body = {"error": "'phone' path paramter is needed"}
        return {"statusCode": 400, "body": json.dumps(body)}

    requested_phone = urllib.parse.unquote_plus(event["pathParameters"]["phone"])
    helper_update = json.loads(event["body"])

    helper = Helper.get(phone=normalize_phone(requested_phone))
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

    requested_phone = urllib.parse.unquote_plus(event["pathParameters"]["phone"])
    helper = Helper.get(phone=normalize_phone(requested_phone))
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

    requester_lat = zip_point["lat"]  # noqa: F841
    requester_lon = zip_point["lon"]  # noqa: F841
    distance_weight = float(  # noqa: F841
        event["queryStringParameters"].get("distance_weight", 1.0)
    )
    time_weight = float(  # noqa: F841
        event["queryStringParameters"].get("time_weight", 40_000.0)
    )

    helper = Helper.get_by_sql(
        """
        SELECT * FROM helper
        WHERE is_active AND verified
        ORDER BY
            $distance_weight * $EARTH_RADIUS_METERS * 2 * asin(
                sqrt(
                    sin(radians($requester_lat - lat)/2)^2
                    + sin(radians($requester_lon - lon)/2)^2
                    * cos(radians($requester_lat))
                    * cos(radians(lat))
                )
            ) + $time_weight / (EXTRACT(epoch FROM (current_timestamp - last_called)) / 60)
        LIMIT 1
        """
    )

    if helper is None:
        body = {"error": "no_helpers_available"}
        return make_response(body, status_code=404)
    else:
        helper.last_called = datetime.datetime.utcnow()
        body = {
            "phone": helper.phone,
            "name": f"{helper.first_name} {helper.last_name}",
            "location": helper.location_name,
        }

        return make_response(body)
