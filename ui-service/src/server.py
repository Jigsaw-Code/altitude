# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The server for handling the Angular Client App's requests."""
# pylint: disable=too-many-locals

import base64
import datetime
import enum
import http
import itertools
import logging
import multiprocessing
import os
from typing import Any, Iterable, Mapping, TypedDict
from urllib import parse
from urllib.request import urlopen

import flask
import requests
from flask_expects_json import expects_json
from jsonschema import ValidationError
from threatexchange.signal_type.pdq import PdqSignal
from werkzeug import exceptions

import gunicorn_app

_APP_NAME = "AltitudeUIService"
SIGNAL_SERVICE_URL = "http://signal-service:8082/"
DEFAULT_REQUEST_TIMEOUT_SEC = 5

EPOCH = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)

ID = "id"
CREATE_TIME = "createTime"
SIGNAL_CONTENT = "signalContent"
FLAGS = "flags"
MOST_RECENT_STATUS = "mostRecentStatus"
ASSOCIATED_ENTITIES = "associatedEntities"
IMAGE_BYTES = "imageBytes"
NOTES = "notes"

# For Content
CONTENT_VALUE = "contentValue"
CONTENT_TYPE = "contentType"

# For CASE
SIGNAL_IDS = "signal_ids"
TARGET_ID = "target_id"
STATE = "state"
PRIORITY = "priority"
REVIEW_HISTORY = "reviewHistory"
SIGNAL = "signal"
ANALYSIS = "analysis"

# For ReviewHistory
DECISION = "decision"
USER = "user"

# For Target
TITLE = "title"
DESCRIPTION = "description"
VIEWS = "views"
CREATOR = "creator"
SAFE_SEARCH_SCORES = "safeSearchScores"
UPLOAD_TIME = "uploadTime"
IP_ADDRESS = "ipAddress"
IP_REGION = "ipRegion"

# Review Stats
COUNT_REMOVED = "count_removed"
COUNT_APPROVED = "count_approved"
COUNT_ACTIVE = "count_active"

# For Priority
SCORE = "score"
LEVEL = "level"
CONFIDENCE = "confidence"
SEVERITY = "severity"

# For Similar Cases
SIMILAR_CASE_IDS = "similarCaseIds"


@enum.unique
class ReviewDecisionType(enum.Enum):
    BLOCK = 1
    APPROVE = 2


class MergedSource(TypedDict):
    createTime: str
    name: str
    tags: list[str]
    authors: list[str]


app = flask.Flask(_APP_NAME, static_folder=None)
app.config["PROPAGATE_EXCEPTIONS"] = True


def _to_signal_service_url(relative_path: str):
    return parse.urljoin(SIGNAL_SERVICE_URL, relative_path.lstrip("/"))


def get_ip_region(ip_address: str | None) -> str | None:
    if not ip_address:
        return None

    response = requests.get(
        f"https://ipapi.co/{ip_address}/json/", timeout=DEFAULT_REQUEST_TIMEOUT_SEC
    ).json()
    return response.get("country_name")


def get_fallback_title(signal: Mapping[str, Any]):
    """Returns the fallback title of a signal in case it doesn't have one."""
    contents = signal.get("content")
    if contents:
        for content in contents:
            if content.get("content_type") == "URL":
                return content.get("value").split("/")[-1]
        return contents[0].get("value")
    return None


def _merge_sources(signals: Iterable[dict[str, Any]]) -> list[MergedSource]:
    """Merges sources by name.

    This gives a singular view of multiple reports by different authors but from the
    same source.

    Returns:
        A dictionary of source name to merged source information.
    """
    merged_sources = {}
    for signal in signals:
        # TODO: Refactor tags so they are associated with a specific source.
        content_features = signal.get("content_features", {})
        tags = set(content_features.get("tags", []))
        for feat in {
            "contains_pii",
            "is_violent_or_graphic",
            "is_illegal_in_countries",
        }:
            if content_features.get(feat) and content_features.get(feat) != "NO":
                tags.add(feat)
        for source in signal.get("sources", []):
            name = source.get("name")
            create_time = source.get("create_time")
            if name in merged_sources:
                create_time = min(
                    x for x in (merged_sources[name]["createTime"], create_time) if x
                )
            merged_sources[name] = {
                "createTime": create_time,
                "name": name,
                "tags": sorted(tags),
            }
            authors = merged_sources[name].setdefault("authors", [])
            if "author" in source:
                authors.append(source["author"])
    return list(merged_sources.values())


def case_to_json(
    case: Mapping[str, Any],
    signals: Iterable[dict[str, Any]],
    target: dict[str, Any],
    similar_cases: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Converts a Case from SignalService to a JSON-able dictionary for the client."""
    review_history = case.get("review_history", [])
    creator = target.get(CREATOR, {})
    data = {
        # If there are missing values, return None instead of error.
        ID: case.get("id"),
        CREATE_TIME: case.get("create_time"),
        STATE: case.get("state"),
        PRIORITY: {
            SCORE: case.get("priority"),
            LEVEL: case.get("priority_level"),
            CONFIDENCE: case.get("confidence"),
            SEVERITY: case.get("severity"),
        },
        NOTES: case.get("notes"),
        REVIEW_HISTORY: [
            {
                ID: review.get("id"),
                CREATE_TIME: review.get("create_time"),
                DECISION: review.get("decision"),
                USER: review.get("user"),
            }
            for review in review_history
        ],
        FLAGS: sorted(
            _merge_sources(signals),
            key=(
                lambda x: datetime.datetime.fromisoformat(x["createTime"])
                if x["createTime"]
                else EPOCH
            ),
        ),
        ANALYSIS: {
            SAFE_SEARCH_SCORES: target.get(
                "safe_search_scores",
                {
                    "adult": "UNKNOWN",
                    "spoof": "UNKNOWN",
                    "medical": "UNKNOWN",
                    "violence": "UNKNOWN",
                    "racy": "UNKNOWN",
                },
            ),
        },
        IMAGE_BYTES: target.get("content_bytes"),
        TITLE: (
            target.get("title")
            or next(filter(lambda x: x, (get_fallback_title(x) for x in signals)), None)
        ),
        DESCRIPTION: target.get(DESCRIPTION),
        VIEWS: target.get("views"),
        UPLOAD_TIME: target.get("create_time"),
        IP_ADDRESS: creator.get("ip_address"),
        IP_REGION: get_ip_region(creator.get("ip_address")),
        SIMILAR_CASE_IDS: [
            similar_case.get("id")
            for similar_case in similar_cases
            if similar_case.get("id") != case.get("id")
        ]
        if similar_cases
        else [],
    }

    data[SIGNAL_CONTENT] = []
    for content in itertools.chain.from_iterable(x.get("content", []) for x in signals):
        data[SIGNAL_CONTENT].append(
            {
                CONTENT_VALUE: content.get("value"),
                CONTENT_TYPE: content.get("content_type"),
            }
        )

    entities = set()
    for features in [x.get("content_features", {}) for x in signals]:
        entities.update(features.get("associated_entities", []))
    data[ASSOCIATED_ENTITIES] = list(entities)

    return data


@app.route("/add_reviews", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "case_ids": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            },
            "decision": {
                "type": "number",
                "enum": [x.value for x in ReviewDecisionType],
            },
        },
        "required": [
            "case_ids",
            "decision",
        ],
        "additionalProperties": False,
    }
)
def add_reviews():
    """Adds a review decision for a given set of cases."""
    case_ids = flask.request.json["case_ids"]
    decision = ReviewDecisionType(flask.request.json["decision"])
    logging.info("Received %s review for cases %s", decision, case_ids)

    review_ids = set()
    json = {"decision": decision.name}
    for case_id in case_ids:
        response = requests.post(
            _to_signal_service_url(f"cases/{case_id}/reviews/"),
            json=json,
            timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
        )

        # TODO: Don't error out on the first failing case review.
        if not response.ok:
            return handle_bad_response(response, error_on_not_found=True)

        review_ids.add(response.json().get("id"))

    return (
        flask.jsonify([review_id for review_id in review_ids if review_id is not None]),
        http.HTTPStatus.OK,
    )


@app.route("/remove_reviews", methods=["DELETE"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "review_ids": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            },
        },
        "required": ["review_ids"],
        "additionalProperties": False,
    }
)
def remove_reviews():
    """Removes reviews.

    Note: we can only delete reviews for a limited amount of time after creation. Once
    they move from the `DRAFT` state to the `PUBLISHED` state, they can no longer be
    deleted.
    """
    review_ids = flask.request.json["review_ids"]
    logging.info("Received delete request for reviews %s", review_ids)

    for review_id in review_ids:
        response = requests.delete(
            _to_signal_service_url(f"/reviews/{review_id}"),
            timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
        )

        # TODO: Don't error out on the first failing case review.
        if not response.ok:
            return handle_bad_response(response, error_on_not_found=True)

    return flask.jsonify(), http.HTTPStatus.OK


@app.errorhandler(exceptions.HTTPException)
def handle_exception(error):
    """Returns JSON instead of HTML for HTTP errors."""
    if isinstance(error.description, ValidationError):
        description = error.description.message
    else:
        description = error.description
    return (
        flask.jsonify(
            {
                "code": error.code,
                "name": error.name,
                "description": description,
            }
        ),
        error.code,
    )


@app.route("/get_case/<case_id>", methods=["GET"])
def get_case(case_id: str):
    """Gets single case and formats it for the UI."""
    logging.info("Received request to fetch signal %s", case_id)
    case_response = requests.get(
        _to_signal_service_url(f"cases/{case_id}"),
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )
    case = case_response.json()

    if not case_response.ok:
        return handle_bad_response(case_response, error_on_not_found=True)

    signal_responses = [
        requests.get(
            _to_signal_service_url(f"signals/{signal_id}"),
            timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
        )
        for signal_id in case[SIGNAL_IDS]
    ]
    signals = []
    for signal_response in signal_responses:
        if not signal_response.ok:
            return handle_bad_response(signal_response, error_on_not_found=True)

        signals.append(signal_response.json())

    target_id = case[TARGET_ID]
    target_response = requests.get(
        _to_signal_service_url(f"targets/{target_id}"),
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )
    target = target_response.json()

    if not target_response.ok:
        return handle_bad_response(target_response, error_on_not_found=True)

    signal_id_query_str = parse.urlencode([("signal_id", i) for i in case[SIGNAL_IDS]])
    similar_cases_response = requests.get(
        _to_signal_service_url("cases") + "?" + signal_id_query_str,
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )
    similar_cases = similar_cases_response.json()

    if not similar_cases_response.ok:
        return handle_bad_response(similar_cases_response)

    return (
        flask.jsonify(case_to_json(case, signals, target, similar_cases["data"])),
        http.HTTPStatus.OK,
    )


def handle_bad_response(response: requests.Response, error_on_not_found: bool = False):
    """Creates client responses when there are errors in SignalService

    Args:
        response: the response from Signal Service
        error_on_not_found: whether to propogate a not_found error, when this
            is false a OK Status is returned.
    """
    logging.error("Unexpected error from SignalService: %s", response.json())

    if response.status_code == http.HTTPStatus.NOT_FOUND:
        if error_on_not_found:
            return flask.abort(http.HTTPStatus.NOT_FOUND)
        return flask.jsonify([]), http.HTTPStatus.OK

    # Raise a generic error message if the signal-service server returned an
    # unexpected error.
    return flask.abort(http.HTTPStatus.INTERNAL_SERVER_ERROR)


@app.route("/get_review_stats", methods=["GET"])
def get_review_stats():
    """Gets the review information for the user."""
    logging.info("Received request to fetch review stats.")
    response = requests.get(
        _to_signal_service_url("/cases/review_stats"),
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )
    response_json = response.json()

    if not response.ok:
        return handle_bad_response(response)

    review_stats = {
        COUNT_APPROVED: response_json.get("count_approved"),
        COUNT_REMOVED: response_json.get("count_removed"),
        COUNT_ACTIVE: response_json.get("count_active"),
    }

    return flask.jsonify(review_stats), http.HTTPStatus.OK


# TODO: Consider how to handle pagination for similar cases.
@app.route("/get_cases", methods=["GET"])
def get_cases():
    """Gets all cases that require review and formats them for the UI."""
    logging.info("Received request to fetch all cases for review")
    next_cursor_token = flask.request.args.get("next_cursor_token")
    previous_cursor_token = flask.request.args.get("previous_cursor_token")
    page_size = flask.request.args.get("page_size")
    endpoint = _to_signal_service_url(
        f"cases?state=active&next_cursor_token={next_cursor_token}"
        f"&previous_cursor_token={previous_cursor_token}&page_size={page_size}"
    )
    response = requests.get(
        endpoint,
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )
    response_json = response.json()

    if not response.ok:
        return handle_bad_response(response)
    cases = []
    for case in response_json["data"]:
        signal_responses = [
            requests.get(
                _to_signal_service_url(f"signals/{signal_id}"),
                timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
            )
            for signal_id in case[SIGNAL_IDS]
        ]
        signals = []
        for signal_response in signal_responses:
            if not signal_response.ok:
                return handle_bad_response(signal_response, error_on_not_found=True)

            signals.append(signal_response.json())

        target_id = case[TARGET_ID]
        target_response = requests.get(
            _to_signal_service_url(f"targets/{target_id}"),
            timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
        )
        target = target_response.json()

        if not target_response.ok:
            return handle_bad_response(target_response, error_on_not_found=True)

        case_json = case_to_json(case, signals, target)
        cases.append(case_json)
    result = {
        "data": cases,
        "previous_cursor_token": response_json.get("previous_cursor_token"),
        "next_cursor_token": response_json.get("next_cursor_token"),
        "total_count": response_json.get("total_count"),
    }
    return flask.jsonify(result), http.HTTPStatus.OK


@app.route("/add_notes", methods=["PATCH"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
            },
            "notes": {"type": ["string", "null"], "maxLength": 1000},
        },
        "required": ["case_id", "notes"],
        "additionalProperties": False,
    }
)
def add_notes():
    """Adds a note to a given case."""
    case_id = flask.request.json["case_id"]
    notes = flask.request.json["notes"]
    logging.info("Received %s notes for case %s", notes, case_id)

    json = {"notes": notes}
    response = requests.patch(
        _to_signal_service_url(f"cases/{case_id}"),
        json=json,
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )
    if not response.ok:
        return handle_bad_response(response)

    return flask.jsonify(), http.HTTPStatus.OK


@app.route("/upload_image", methods=["POST"])
@expects_json(
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "image": {
                "type": "string",
                "contentEncoding": "base64",
            },
        },
        "required": ["image"],
        "additionalProperties": False,
    }
)
def upload_image():
    """Handles an image upload."""
    filename = flask.request.json["name"]
    with urlopen(flask.request.json["image"]) as f:
        image_bytes = f.read()

    # We treat UI-uploaded images as "User Reports" for now. This means we first need to
    # create source signals for the image.
    pdq_digest = PdqSignal.hash_from_bytes(image_bytes)
    response = requests.post(
        _to_signal_service_url("signals/"),
        json={
            "content": {"value": pdq_digest, "type": "HASH_PDQ"},
            "source": {
                "name": "USER_REPORT",
                "create_time": datetime.datetime.now().isoformat(),
            },
        },
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )
    if not response.ok:
        return handle_bad_response(response)
    signal_id = response.json()["id"]

    response = requests.post(
        _to_signal_service_url("targets/"),
        json={
            "title": filename,
            "content_bytes": base64.b64encode(image_bytes).decode(),
            "content_type": "IMAGE",
        },
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )
    if not response.ok:
        return handle_bad_response(response)
    target_id = response.json()["id"]

    # This is a hack. Normally, targets are matched against signals, but as indexes only
    # get built every 15 minutes, the above new signal and target will not have matched
    # yet. Instead, we manually create a case.
    response = requests.post(
        _to_signal_service_url("cases/"),
        json={"target_id": target_id, "signal_ids": [signal_id]},
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )

    return flask.jsonify(), http.HTTPStatus.OK


@app.route("/get_importer_configs", methods=["GET"])
def get_importer_configs():
    """Gets the importer configs."""
    importers = {}

    response = requests.get(
        _to_signal_service_url("importers/TCAP_API"),
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )
    if response.ok:
        importers["tcap"] = {
            "config": {
                "enabled": response.json()["state"] == "ACTIVE",
                "diagnosticsEnabled": response.json()["diagnostics_state"] == "ACTIVE",
                "username": response.json()["credential"]["identifier"],
                "password": response.json()["credential"]["token"],
            },
            "lastRunTime": response.json().get("last_run_time"),
            "totalImportCount": response.json()["total_import_count"],
        }

    response = requests.get(
        _to_signal_service_url("importers/THREAT_EXCHANGE_API"),
        timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
    )
    if response.ok:
        importers["gifct"] = {
            "config": {
                "enabled": response.json()["state"] == "ACTIVE",
                "diagnosticsEnabled": response.json()["diagnostics_state"] == "ACTIVE",
                "privacyGroupId": response.json()["credential"]["identifier"],
                "accessToken": response.json()["credential"]["token"],
            },
            "lastRunTime": response.json().get("last_run_time"),
            "totalImportCount": response.json()["total_import_count"],
        }

    return flask.jsonify(importers), http.HTTPStatus.OK


@app.route("/update_importer_configs", methods=["POST"])
def update_importer_configs():
    """Updates the importer configs."""
    importers = {
        "tcap": {
            "type": "TCAP_API",
            "identifier_key": "username",
            "token_key": "password",
        },
        "gifct": {
            "type": "THREAT_EXCHANGE_API",
            "identifier_key": "privacyGroupId",
            "token_key": "accessToken",
        },
    }

    for key, options in importers.items():
        config = flask.request.json[key]
        importer_type = options["type"]
        identifier = config[options["identifier_key"]]
        token = config[options["token_key"]]
        if identifier and token:
            response = requests.post(
                _to_signal_service_url("importers/"),
                json={
                    "type": importer_type,
                    "state": "ACTIVE" if config.get("enabled", False) else "INACTIVE",
                    "diagnostics_state": (
                        "ACTIVE"
                        if config.get("diagnosticsEnabled", False)
                        else "INACTIVE"
                    ),
                    "credential": {
                        "identifier": identifier,
                        "token": token,
                    },
                },
                timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
            )
            if not response.ok:
                if response.status_code == http.HTTPStatus.BAD_REQUEST:
                    return flask.abort(
                        response.status_code, f"Please check your {key} credentials."
                    )
                return handle_bad_response(response)
        else:
            requests.delete(
                _to_signal_service_url(f"importers/{importer_type}"),
                timeout=DEFAULT_REQUEST_TIMEOUT_SEC,
            )

    return flask.jsonify(), http.HTTPStatus.OK


def main():
    """Main entrypoint when running the server."""
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8081))
    if os.environ.get("DEBUG", False):
        app.run(debug=True, host=host, port=port)
    else:
        options = {
            "bind": f"{host}:{port}",
            "workers": multiprocessing.cpu_count() * 2 + 1,
        }
        gunicorn_app.StandaloneApplication(app, options).run()


if __name__ == "__main__":
    main()
