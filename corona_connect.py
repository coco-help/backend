import json

import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(
    dsn="https://c3490788b0fd46d09992667d01bb0352@sentry.io/5169971",
    integrations=[AwsLambdaIntegration()]
)

from pony.orm import db_session

from db import Helper


def register(event, context):
    user = event["body"]

    print(f"Created user {user} in Database")

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
        "name": f"{helper.first_name} {helper.last_name}",
        "location": "Berlin Mitte",
    }

    return {
        "statusCode": 200,
        "body": json.dumps(body)
    }
