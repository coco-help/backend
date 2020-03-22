# CoronaConnect backend

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

# development deployment

make sure you have `npm` installed at a recent version.
```bash
npx serverless deploy --stage dev/<your_name>`
```


# migrating database
look at the sql scripts in migrations/
