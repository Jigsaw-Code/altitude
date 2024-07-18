# SignalService

## Setup

Install [Poetry](https://python-poetry.org/docs/#installation) for package
management and then install dependencies:

```shell
poetry install
```

## Running the server locally

This command assumes you're already running a local mongodb instance:

```shell
MONGO_USERNAME_FILE='../secrets/mongodb_username.txt' \
    MONGO_PASSWORD_FILE='../secrets/mongodb_password.txt' \
    MONGO_DATABASE='altitude' \
    poetry run python src/server.py
```

## Making a Request

Some example requests that are supported by the API.

1. Creating a new image target entity:

   ```shell
    echo '{"client_context": "#myref", "content_type": "IMAGE", "content_bytes": "'$(base64 -w 0 src/testing/testdata/logo.png)'"}' | \
        curl -i -H "Content-Type: application/json" --data-binary @- \
            "http://127.0.0.1:8082/targets/"
   ```

1. Creating a new text target entity:

   ```shell
    echo '{"client_context": "#myref", "content_type": "TEXT", "content_bytes": "aGVsbG8="}' | \
        curl -i -H "Content-Type: application/json" --data-binary @- \
            "http://127.0.0.1:8082/targets/"
   ```

1. Fetching a list of signals:

   ```shell
   curl -H "Content-Type: application/json" \
       "http://127.0.0.1:8082/signals/"
   ```

1. Fetching a single signal:

   ```shell
   curl -H "Content-Type: application/json" \
       "http://127.0.0.1:8082/signals/<signal_id>"
   ```

1. Fetching a list of cases:

   ```shell
   curl -H "Content-Type: application/json" \
       "http://127.0.0.1:8082/cases/"
   ```

1. Fetching a single case:

   ```shell
   curl -H "Content-Type: application/json" \
       "http://127.0.0.1:8082/cases/<case_id>"
   ```

1. Adding a review to a case:

   ```shell
   curl -X "POST" -H "Content-Type: application/json" \
       -d '{"decision": "BLOCK"}' \
       "http://127.0.0.1:8082/cases/<case_id>/reviews/"
   ```

### Configuring API Settings

To set the threshold for the Safe Search Detection Api, you will need to update
the docker-compose configuration SAFE_SEARCH_THRESHOLD environment variable
depending on your needs. The numbers range from 1 to 5 with each number
representing how likely the content is to be of that type, with 1 being the least
likely and 5 being the most likely.

#### Updating Signal Prioritization Algorithm

After changing the algorithm in src/prioritization/case_priority.py, you'll
need to update the priority of the existing signals in the database. You can
update these by running:

```shell
docker exec -it signal-service /bin/sh -c \
"poetry run python update_case_priority.py --dry_run=False"
```

You can view the changes without commiting them if you set dry_run = True. Also,
be sure to check the update_case_priority code calls calculate_priority as
intended.

## Docker development server

Build a Docker image of the application:

```shell
docker build -t jigsaw/altitude-signal-service .
```

Run the backend server with Docker:

```shell
docker run -p 8082:8082 jigsaw/altitude-signal-service
```

The backend is now ready to receive requests at `http://localhost:8082`. Logs
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
