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

"""API view for the Case resource."""

import http
import logging
import urllib
from typing import Any

from bson.objectid import ObjectId
from flask import Blueprint, request
from mongoengine import ValidationError
from mongoengine.queryset.visitor import Q

from api import review
from api.api_error import ApiError
from api.validation import Validator
from models.case import Case
from models.signal import Signal
from models.target import Target
from prioritization import case_priority
from utils import cursor

_CASE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "signal_ids": {
            "type": "array",
            "items": {"type": "string"},
        },
        "target_id": {"type": "string"},
        "create_time": {
            "type": ["string"],
            "format": "date-time",
        },
        "state": {"type": ["string"], "enum": ["ACTIVE", "RESOLVED"]},
        "priority": {
            "type": ["number"],
            "minimum": -1,
            "maximum": case_priority.MAXIMUM_PRIORITY_SCORE,
        },
        "priority_level": {
            "anyOf": [
                {"type": "string", "enum": [x.name for x in case_priority.Level]},
                {"type": "null"},
            ]
        },
        "confidence": {
            "anyOf": [
                {"type": "string", "enum": [x.name for x in case_priority.Level]},
                {"type": "null"},
            ]
        },
        "severity": {
            "anyOf": [
                {"type": "string", "enum": [x.name for x in case_priority.Level]},
                {"type": "null"},
            ]
        },
        "review_history": {
            "type": ["array", "null"],
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "create_time": {
                        "type": ["string"],
                        "format": "date-time",
                    },
                    "decision": {"type": "string", "enum": ["BLOCK", "APPROVE"]},
                    "user": {"type": ["string", "null"]},
                },
                "additionalProperties": False,
            },
        },
        "notes": {"type": ["string", "null"], "maxLength": 1000},
    },
    "additionalProperties": False,
}

bp = Blueprint("Case", __name__, url_prefix="/cases/")


@bp.post("/")
@Validator(
    input_schema={
        "title": "Cases Create API input schema",
        "type": "object",
        "properties": {
            "signal_ids": {
                "type": "array",
                "items": {"type": ["string"]},
                "minItems": 1,
            },
            "target_id": {
                "type": ["string", "null"],
            },
        },
        "required": ["signal_ids"],
        "additionalProperties": False,
    },
    output_schema={
        "title": "Cases Create API output schema",
    }
    | _CASE_SCHEMA,
)
def _create():
    signal_ids = set(request.json.get("signal_ids"))
    found_signal_ids = {
        str(x["id"]) for x in Signal.objects(id__in=signal_ids).only("id")
    }
    not_found_signal_ids = signal_ids - found_signal_ids
    if not_found_signal_ids:
        raise ApiError(
            http.HTTPStatus.NOT_FOUND,
            message=f"Signals {sorted(not_found_signal_ids)} not found.",
        )

    target_id = request.json.get("target_id")
    if target_id:
        try:
            Target.objects.get(id=target_id)
        except (ValidationError, Target.DoesNotExist) as e:
            raise ApiError(
                http.HTTPStatus.NOT_FOUND, message=f"Target {target_id} not found."
            ) from e

    case = Case(
        signal_ids=[ObjectId(signal_id) for signal_id in signal_ids],
        target_id=ObjectId(target_id) if target_id else None,
    )
    case.save()

    logging.info("Created case for target %s and signals %s", target_id, signal_ids)

    return _to_dict(case), http.HTTPStatus.CREATED


@bp.get("/<case_id>")
@Validator(
    input_schema={
        "title": "Cases Get API input schema",
        "type": "null",
    },
    output_schema={
        "title": "Cases Get API output schema",
    }
    | _CASE_SCHEMA,
)
def _get(case_id: str):
    """Returns a single Case by its unique identifier.

    Args:
        case_id: A unique identifier to fetch a single case.

    Returns:
        A dictionary containing details about a case.
    """
    try:
        case = Case.objects.get(id=case_id)
    except (ValidationError, Case.DoesNotExist) as e:
        raise ApiError(
            http.HTTPStatus.NOT_FOUND, message=f"Case {case_id} not found."
        ) from e

    return _to_dict(case)


@bp.get("/")
@Validator(
    input_schema={
        "title": "Cases List API input schema",
        "type": "null",
    },
    output_schema={
        "title": "Cases List API output schema",
        "type": "object",
        "properties": {
            "data": {"type": ["array"], "items": _CASE_SCHEMA},
            "next_cursor_token": {
                "type": ["string", "null"],
                "contentEncoding": "base64",
            },
            "previous_cursor_token": {
                "type": ["string", "null"],
                "contentEncoding": "base64",
            },
            "total_count": {"type": ["number"]},
        },
        "additionalProperties": False,
    },
)
def _list():
    """Returns a list of cases.

    Returns:
        A list of case dictionaries.
    """
    query_string = urllib.parse.urlparse(request.url).query
    filters = urllib.parse.parse_qs(query_string)
    page_size = int(filters["page_size"][0]) if "page_size" in filters else None
    cases = Case.objects().order_by("-cached_priority", "id")
    response = {}

    if "state" in filters:
        state_filter = Case.State[filters["state"][0].upper()]
        cases = cases(state=state_filter)
    if "signal_id" in filters:
        signal_ids_to_find = filters["signal_id"]
        cases = cases(signal_ids__in=signal_ids_to_find)

    response["total_count"] = cases.count()

    if "next_cursor_token" in filters and "previous_cursor_token" in filters:
        raise ApiError(
            http.HTTPStatus.BAD_REQUEST,
            message="Only one cursor token should be provided.",
        )
    if "next_cursor_token" in filters:
        next_cursor_token = filters["next_cursor_token"][0]
        try:
            next_cursor = cursor.decode_cursor(next_cursor_token)
        except Exception as e:
            raise ApiError(
                http.HTTPStatus.BAD_REQUEST, message=f"Invalid cursor format: {e}"
            ) from e
        token_id, token_priority = (
            next_cursor["token_id"],
            next_cursor["token_priority"],
        )
        cases = cases(
            Q(cached_priority__lt=token_priority)
            | (Q(cached_priority=token_priority) & Q(id__gt=token_id))
        ).limit(page_size)

    elif "previous_cursor_token" in filters:
        previous_cursor_token = filters["previous_cursor_token"][0]
        try:
            previous_cursor = cursor.decode_cursor(previous_cursor_token)
        except Exception as e:
            raise ApiError(
                http.HTTPStatus.BAD_REQUEST, message=f"Invalid cursor format: {e}"
            ) from e
        token_id, token_priority = (
            previous_cursor["token_id"],
            previous_cursor["token_priority"],
        )

        # Move order by outside of if statements to reduce duplicate code
        cases = cases(
            Q(cached_priority__gt=token_priority)
            | (Q(cached_priority=token_priority) & Q(id__lt=token_id))
        )
        # Get the last page_size cases
        cases = cases[cases.count() - page_size :]

    else:
        cases = cases.limit(page_size)

    if cases:
        count = cases.count(with_limit_and_skip=True)
        last_case = cases[count - 1]
        last_case_id, last_case_priority = (
            last_case.id,
            last_case.priority,
        )

        if Case.objects(
            Q(cached_priority__lt=last_case_priority)
            | (Q(cached_priority=last_case_priority) & Q(id__gt=last_case_id))
        ).first():
            next_cursor = {
                "token_id": str(last_case_id),
                "token_priority": last_case_priority,
            }
            response["next_cursor_token"] = cursor.encode_cursor(next_cursor)
        first_case = cases[0]
        first_case_id, first_case_priority = first_case.id, first_case.priority
        if Case.objects(
            Q(cached_priority__gt=first_case_priority)
            | (Q(cached_priority=first_case_priority) & Q(id__lt=first_case_id))
        ).first():
            previous_cursor = {
                "token_id": str(first_case_id),
                "token_priority": first_case_priority,
            }
            response["previous_cursor_token"] = cursor.encode_cursor(previous_cursor)
    response["data"] = [_to_dict(v) for v in cases]
    return response


@bp.patch("/<case_id>")
@Validator(
    input_schema={
        "title": "Cases Update API input schema",
        "type": "object",
        "properties": {
            "notes": {"type": ["string", "null"], "maxLength": 1000},
        },
        "additionalProperties": False,
    },
    output_schema={
        "title": "Cases Update API output schema",
    }
    | _CASE_SCHEMA,
)
def _update(case_id: str):
    """Updates and returns a single Case by its unique identifier.

    Args:
       case_id: A unique identifier to fetch a single case.

    Returns:
        A dictionary containing details about a case.
    """
    try:
        case = Case.objects.get(id=case_id)
    except (ValidationError, Case.DoesNotExist) as e:
        raise ApiError(
            http.HTTPStatus.NOT_FOUND, message=f"Case {case_id} not found."
        ) from e
    notes = request.json.get("notes")
    case.notes = notes
    case.save()

    return _to_dict(case), http.HTTPStatus.OK


def _to_dict(case: Case) -> dict[str, Any]:
    result = {
        "id": str(case.id),
        "signal_ids": [str(id) for id in case.signal_ids],
        "create_time": case.create_time,
        "state": case.state,
        "priority": case.priority,
        "priority_level": case.priority_level,
        "confidence": case.confidence_level,
        "severity": case.severity_level,
        "notes": case.notes,
    }
    if case.target_id:
        result["target_id"] = str(case.target_id)
    if case.review_history:
        result["review_history"] = []
        for case_review in case.review_history:
            review_document = review.to_dict(case_review)
            result["review_history"].append(review_document)
    return result
