import json

from pony.orm import db_session

from db import Helper


def register(event, context):
    body = {
        "message": "user created",
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


@db_session
def phone(event, context):
    helper = Helper[1]
    body = {
        "phone": helper.phone,
        "name": helper.first_name + " " + helper.last_name,
        "location": "Berlin Mitte",
    }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "phone": "+4917696585570",
            "name": "Jonas",
            "location": "Berlin Mitte",
        }),
    }
