import json

from pony.orm import db_session, select

from db import Helper


def register(event, context):
    body = {
        "message": "user created",
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

    return {
        "statusCode": 200,
        "body": json.dumps(body)
    }
