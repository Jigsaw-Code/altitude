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

"""API view for the Signal resource."""

import http
import logging
from datetime import datetime
from typing import Any

from flask import Blueprint, request
from mongoengine import ValidationError

from api.api_error import ApiError
from api.validation import Validator
from models.signal import Content, Signal, Source, Sources
from taskqueue import tasks

_CONFIDENCE_ENUM = {"type": ["null", "string"], "enum": [None, "YES", "NO", "UNSURE"]}
_SIGNAL_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "create_time": {
            "type": ["string", "null"],
            "format": "date-time",
        },
        "content": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"},
                    "content_type": {
                        "type": "string",
                        "enum": ["URL", "HASH_PDQ", "HASH_MD5", "API", "UNKNOWN"],
                    },
                },
            },
        },
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {
                        "type": "string",
                        "enum": [
                            "TCAP",
                            "GIFCT",
                            "USER_REPORT",
                            "SAFE_SEARCH",
                            "PERSPECTIVE",
                            "UNKNOWN",
                        ],
                    },
                    "author": {"type": ["string", "null"]},
                    "create_time": {
                        "type": ["string", "null"],
                        "format": "date-time",
                    },
                },
                "additionalProperties": False,
            },
        },
        "content_features": {
            "type": "object",
            "properties": {
                "associated_entities": {
                    "type": ["array"],
                    "items": {"type": ["string"]},
                },
                "contains_pii": _CONFIDENCE_ENUM,
                "is_violent_or_graphic": _CONFIDENCE_ENUM,
                "is_illegal_in_countries": {
                    "type": ["array"],
                    "items": {"type": "string"},
                },
                "tags": {
                    "type": ["array"],
                    "items": {"type": "string"},
                },
            },
        },
        "status": {
            "type": "object",
            "properties": {
                "last_checked_time": {
                    "type": ["string", "null"],
                    "format": "date-time",
                },
                "verifier": {"type": "string"},
                "most_recent_status": {
                    "type": ["string", "null"],
                    "enum": [
                        "UNKNOWN",
                        "ACTIVE",
                        "REMOVED_BY_USER",
                        "REMOVED_BY_MODERATOR",
                        "UNAVAILABLE",
                    ],
                },
            },
        },
    },
    "additionalProperties": False,
}


bp = Blueprint("Signal", __name__, url_prefix="/signals/")


@bp.post("/")
@Validator(
    input_schema={
        "title": "Signal Create API input schema",
        "type": "object",
        "properties": {
            "content": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["HASH_PDQ", "HASH_MD5", "URL"],
                    },
                },
                "required": ["value", "type"],
            },
            "source": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "enum": ["TCAP", "GIFCT", "USER_REPORT"],
                    },
                    "author": {"type": "string"},
                    "create_time": {
                        "type": "string",
                        "format": "date-time",
                    },
                },
                "required": ["name"],
            },
        },
        "required": ["content"],
        "additionalProperties": False,
    },
    output_schema={
        "title": "Signal Create API output schema",
    }
    | _SIGNAL_SCHEMA,
)
def _create():
    content = request.json.get("content")
    signal = Signal(
        content=[
            Content(
                value=content.get("value"),
                content_type=content.get("type"),
            )
        ],
    )
    source = request.json.get("source")
    if source:
        create_time = source.get("create_time")
        report_date = datetime.fromisoformat(create_time) if create_time else None
        signal.sources = Sources(
            sources=[
                Source(
                    name=source.get("name"),
                    author=source.get("author"),
                    report_date=report_date,
                )
            ]
        )
    # TODO: Merge with existing signal if it already exists.
    signal.save()
    logging.info("Created signal %s", str(signal.id))

    logging.info("Enqueueing signal %s", str(signal.id))
    tasks.process_new_signals.delay(signal_ids=[str(signal.id)])

    return _to_dict(signal), http.HTTPStatus.CREATED


@bp.get("/<signal_id>")
@Validator(
    input_schema={
        "title": "Signals Get API input schema",
        "type": "null",
    },
    output_schema={
        "title": "Signals Get API output schema",
    }
    | _SIGNAL_SCHEMA,
)
def _get(signal_id: str):
    """Returns a single Signal by its unique identifier.

    Args:
        signal_id: A unique identifier to fetch a single signal.

    Returns:
        A dictionary containing details about a signal.
    """
    try:
        signal = Signal.objects.get(id=signal_id)
    except (ValidationError, Signal.DoesNotExist) as e:
        raise ApiError(
            http.HTTPStatus.NOT_FOUND, message=f"Signal {signal_id} not found."
        ) from e

    return _to_dict(signal)


@bp.get("/")
@Validator(
    input_schema={
        "title": "Signals List API input schema",
        "type": "null",
    },
    output_schema={
        "title": "Signals List API output schema",
        "type": "array",
        "items": _SIGNAL_SCHEMA,
    },
)
def _list():
    """Returns a list of signals.

    Returns:
        A list of signal dictionaries.
    """
    return [_to_dict(v) for v in Signal.objects]


def _to_dict(signal: Signal) -> dict[str, Any]:
    result = {
        "id": str(signal.id),
        # TODO: Add a new `create_time` to the signal object.
        "create_time": min(source.report_date for source in signal.sources.sources),
        "content": [
            {"value": content["value"], "content_type": content["content_type"]}
            for content in signal.content
        ],
    }

    if signal.content_status:
        result["status"] = {
            "most_recent_status": signal.content_status.most_recent_status,
            "last_checked_time": signal.content_status.last_checked_date,
        }

    if signal.sources:
        result["sources"] = []
        for source in signal.sources.sources:
            source_document = {"name": source.name}
            if source.report_date:
                source_document["create_time"] = source.report_date
            if source.author:
                source_document["author"] = source.author
            result["sources"].append(source_document)

    if signal.content_features:
        result["content_features"] = {
            "associated_entities": signal.content_features.associated_terrorist_organizations,
            "contains_pii": signal.content_features.contains_pii,
            "is_violent_or_graphic": signal.content_features.is_violent_or_graphic,
            "is_illegal_in_countries": signal.content_features.is_illegal_in_countries,
            "tags": signal.content_features.tags,
        }

    return result
