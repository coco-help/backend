# CoronaConnect backend
The backend that powers CoCo's hotline and front-end. It is developed using the [serverless framework](https://serverless.com/) and
is inteded to be deployed on [AWS Lambda](https://aws.amazon.com/lambda/?nc1=h_ls).

# Endpoints

## POST /register
Add a new helper to the database. After a successful request, the helper can be matched.

### Example request
`/register`

#### Request body:
```json
{
    "name": "Mark Test",
    "phone": "+4917612345678",
    "zip": "21037",
    "email": "mark@test.com"
}
```

#### Response body:
```json
{
    "message": "User created",
    "phone": "+4917612345678",
}
```

## POST /login/{phone}
Send a login code to a helper's phone number.

### Example request
`/login/+4917612345678`

#### Request body
None

#### Response body
```json
{
    "message": "user_message_sent"
}
```


## GET /verify/{phone}?code={code}
Verify that a phone number is accessible to a helper with a code sent by SMS.
### Example request
`/verify/+4917612345678?code=1234`

#### Request body
None

#### Response body
```json
{
    "message": "user_verified",
    "user": {
        "phone": "+4917612345678",
        "first_name": "Mark",
        "last_name": "Test"
    },
    "token": "eyJ0eXAiOiJLT1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1ODQ5MTI1NTksImV4cCI6MTU4NDkxMzQ1OSwicGhvbmUiOiIrNDkxNzY0MjA5MDgyMSJ9.ceaqi-SGNhX6AYEsypGty9Y1C3_Jwx46SQO2iGjek3I"
}
```

## GET /helper/{phone}
Get data of a registered helper.

### Example request
`/helper/+4917612345678`

#### Request headers
Key | Value
--- | ---
Authorization |  eyJ0eXAiOiJLT1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1ODQ5MTI1NTksImV4cCI6MTU4NDkxMzQ1OSwicGhvbmUiOiIrNDkxNzY0MjA5MDgyMSJ9.ceaqi-SGNhX6AYEsypGty9Y1C3_Jwx46SQO2iGjek3I

#### Request body
None

#### Response body
```json
{
    "phone": "+4917612345678",
    "first_name": "Mark",
    "last_name": "Test",
    "email": "mark@test.com",
    "lon": 10.1329393,
    "lat": 53.4493502,
    "zip_code": "21037",
    "location_name": "Hamburg",
    "is_active": true,
    "verified": true
}
```


## PUT /helper/{phone}
Update data of a registered helper.

### Example request
`/helper/+4917612345678`

#### Request headers
Key | Value
--- | ---
Authorization |  eyJ0eXAiOiJLT1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1ODQ5MTI1NTksImV4cCI6MTU4NDkxMzQ1OSwicGhvbmUiOiIrNDkxNzY0MjA5MDgyMSJ9.ceaqi-SGNhX6AYEsypGty9Y1C3_Jwx46SQO2iGjek3I

#### Request body
```json
{
    "first_name": "Mark",
    "last_name": "Test",
    "email": "mark@test.com",
    "zip_code": "21037",
    "is_active": false
}
```
#### Response body
```json
{
    "phone": "+4917612345678",
    "first_name": "Mark",
    "last_name": "Test",
    "email": "mark@test.com",
    "lon": 10.1329393,
    "lat": 53.4493502,
    "zip_code": "21037",
    "location_name": "Hamburg",
    "is_active": false,
    "verified": true
}
```

## DELETE /helper/{phone}
Delete a registered helper.

### Example request
`/helper/+4917612345678`

#### Request headers
Key | Value
--- | ---
Authorization |  eyJ0eXAiOiJLT1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1ODQ5MTI1NTksImV4cCI6MTU4NDkxMzQ1OSwicGhvbmUiOiIrNDkxNzY0MjA5MDgyMSJ9.ceaqi-SGNhX6AYEsypGty9Y1C3_Jwx46SQO2iGjek3I

#### Request body
None

#### Response body
```json
{
    "message": "deleted"
}
```

## GET /phone?zip={zip}
Get the best matching helper for a zip code based on their distance to the zip code and the duration since they have last been called.

### Example request
`/phone?zip=21039`

#### Request body
None

#### Response body
```json
{
    "phone": "+4917612345678",
    "name": "Mark Test",
    "location": "Hamburg",
}
```

# Contributing

## Prerequisites

- [Poetry](https://python-poetry.org/docs/#installation)
- Python 3.7

## Setup

### Install poetry

```bash
poetry install
poetry run task setup
```

## Linting

```bash
poetry run task lint
```

## Testing

```bash
poetry run task test
```

## development deployment

make sure you have `npm` installed at a recent version.
```bash
npx serverless deploy --stage dev/<your_name>`
```


## migrating database
look at the sql scripts in migrations/
