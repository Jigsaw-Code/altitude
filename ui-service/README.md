# UiService

## Setup

Install [Poetry](https://python-poetry.org/docs/#installation) for package
management and then install dependencies:

```shell
poetry install
```

## Running the server locally

```shell
poetry run python src/server.py
```

## Making a Request

1. Fetching a list of cases:

```shell
curl -H "Content-Type: application/json" "http://127.0.0.1:8081/get_cases"
```

1. Fetching a single case:

```shell
curl -H "Content-Type: application/json" "http://127.0.0.1:8081/get_case/<case_id>"
```

1. Creating a review:

```shell
curl -X "POST" -H "Content-Type: application/json" \
       -d '{"case_ids": ["<case_id>"], "decision": 1}' \
       "http://127.0.0.1:8081/add_reviews"
```

## Docker development server

Build a Docker image of the application:

```shell
docker build -t jigsaw/altitude-ui-service .
```

Run the frontend with Docker:

```shell
docker run -p 8081:8081 jigsaw/altitude-ui-service
```

The backend is now ready to receive requests at `http://localhost:8081`. Logs
are written to stdout.

## Running tests

```shell
poetry run coverage run -m unittest discover -s ./src -p '*_test.py'
```

This runs the tests and calculates coverage using
[`Coverage.py`](https://coverage.readthedocs.io/). To generate a HTML report on coverage,
run:

```shell
poetry run coverage html
```

This generates a report under `htmlcov/index.html` which you can view in your browser.

## Running Pylint

```shell
poetry run pylint -rn -sn -v ./src
```

## Running Pytype

```shell
poetry run pytype .
```
