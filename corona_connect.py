import json

from pony.orm import *

from db import Helper

def register(event, context):
    body = {
        "message": "user created",
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

@db_session
def phone(event, context):
    helper = Helper[1]
    return {
        "phone": helper.phone,
        "name": helper.first_name + " " + helper.last_name,
        "location": "Berlin Mitte",
    }
