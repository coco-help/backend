import json


def register(event, context):
    body = {
        "message": "user created",
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response


def phone(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "phone": "+4917696585570",
            "name": "Jonas",
            "location": "Berlin Mitte",
        }),
    }
