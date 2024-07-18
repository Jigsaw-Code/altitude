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

"""API endpoints for the Target resource."""

import base64
import enum
import http
import logging
from typing import Any

from flask import Blueprint, request
from mongoengine import ValidationError

from api.api_error import ApiError
from api.validation import Validator
from models import features
from models.target import FeatureSet, Target
from taskqueue import tasks
from utils.image import is_image

bp = Blueprint("Target", __name__, url_prefix="/targets/")


@enum.unique
class _ContentType(enum.Enum):
    IMAGE = "IMAGE"
    TEXT = "TEXT"


@enum.unique
class _Likelihood(enum.Enum):
    UNKNOWN = 0
    VERY_UNLIKELY = 1
    UNLIKELY = 2
    POSSIBLE = 3
    LIKELY = 4
    VERY_LIKELY = 5


_TARGET_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "create_time": {"type": "string", "format": "date-time"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "views": {"type": "number"},
        "content_bytes": {"type": "string"},
        "creator": {
            "type": "object",
            "properties": {
                "ip_address": {
                    "type": "string",
                    "anyOf": [
                        {"format": "ipv4"},
                        {"format": "ipv6"},
                        {"format": "hostname"},
                    ],
                }
            },
        },
        "client_context": {
            "description": (
                "An opaque string that will be associated with the entity throughout "
                "the pipeline. This was supplied in the creation endpoint and is "
                "stored and returned without modification."
            ),
            "type": "string",
        },
        "safe_search_scores": {
            "adult": {"type": "string", enum: [x.name for x in _Likelihood]},
            "spoof": {"type": "string", enum: [x.name for x in _Likelihood]},
            "medical": {"type": "string", enum: [x.name for x in _Likelihood]},
            "violence": {"type": "string", enum: [x.name for x in _Likelihood]},
            "racy": {"type": "string", enum: [x.name for x in _Likelihood]},
        },
    },
    "required": ["id", "create_time"],
    "additionalProperties": False,
}


@bp.post("/")
@Validator(
    input_schema={
        "title": "Targets Create API input schema",
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "views": {"type": "number"},
            "creator": {
                "type": "object",
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "anyOf": [
                            {"format": "ipv4"},
                            {"format": "ipv6"},
                            {"format": "hostname"},
                        ],
                    }
                },
            },
            "client_context": {
                "description": (
                    "An opaque string that will be associated with the entity "
                    "throughout the pipeline."
                ),
                "type": "string",
            },
            "content_type": {
                "type": "string",
                "enum": [x.name for x in _ContentType],
            },
            "content_bytes": {
                "description": "The target content, encoded as a base64 string.",
                "type": "string",
                "contentEncoding": "base64",
            },
        },
        "required": ["content_bytes", "content_type"],
        "additionalProperties": False,
    },
    output_schema={
        "title": "Targets Create API output schema",
    }
    | _TARGET_SCHEMA,
)
def _create():
    """Creates a new Target entity reflecting content submitted for scanning."""
    content_type = _ContentType[request.json.get("content_type")]
    logging.info("Received request for type %s", content_type.value)

    target = Target()
    feature_set = FeatureSet()

    views = request.json.get("views")
    creator = request.json.get("creator")
    if creator:
        ip_address = creator.get("ip_address")
        feature_set.creator = features.user.User(ip_address=ip_address)
    if views:
        feature_set.engagement_metrics = features.engagement.Engagement(views=views)

    client_context = request.json.get("client_context")
    if client_context:
        target.client_context = client_context

    title = request.json.get("title")
    description = request.json.get("description")
    if content_type == _ContentType.IMAGE:
        content_bytes = base64.b64decode(request.json.get("content_bytes"))
        if not is_image(content_bytes):
            raise ApiError(
                http.HTTPStatus.BAD_REQUEST, message="Unable to process image data"
            )
        feature_set.image = features.image.Image(
            title=title,
            description=description,
            data=content_bytes,
        )
        target.feature_set = feature_set
        target.save()
        # Kick off heavier processing to be done in a background task so we can return the
        # API call.
        tasks.process_new_image_target.delay(target_id=str(target.id))
    elif content_type == _ContentType.TEXT:
        content_bytes = base64.b64decode(request.json.get("content_bytes"))

        feature_set.text = features.text.Text(
            title=title,
            description=description,
            data=content_bytes,
        )
        target.feature_set = feature_set
        target.save()
        # TODO: Ideally should run after a match is found.
        tasks.process_new_text_target.delay(target_id=str(target.id))

    return _to_dict(target), http.HTTPStatus.CREATED


@bp.get("/<target_id>")
@Validator(
    input_schema={
        "title": "Targets Get API input schema",
        "type": "null",
    },
    output_schema={
        "title": "Targets Get API output schema",
    }
    | _TARGET_SCHEMA,
)
def _get(target_id: str):
    """Returns a single Target by its unique identifier.

    Args:
        target_id: A unique identifier to fetch a single target.

    Returns:
        A dictionary containing details about a target.
    """
    try:
        target = Target.objects.get(id=target_id)
    except (ValidationError, Target.DoesNotExist) as e:
        raise ApiError(
            http.HTTPStatus.NOT_FOUND, message=f"Target {target_id} not found."
        ) from e

    return _to_dict(target)


@bp.patch("/<target_id>")
@Validator(
    input_schema={
        "title": "Targets Update API input schema",
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "views": {"type": "number"},
            "creator": {
                "type": "object",
                "properties": {
                    "ip_address": {
                        "type": "string",
                        "anyOf": [
                            {"format": "ipv4"},
                            {"format": "ipv6"},
                            {"format": "hostname"},
                        ],
                    }
                },
            },
            "client_context": {
                "description": (
                    "An opaque binary blob that will be associated with the entity "
                    "throughout the pipeline, encoded as a base64 string."
                ),
                "type": "string",
            },
        },
        "additionalProperties": False,
    },
    output_schema={
        "title": "Targets Update API output schema",
    }
    | _TARGET_SCHEMA,
)
def _update(target_id: str):
    """Updates and returns a single Target by its unique identifier.

    Args:
        target_id: A unique identifier to fetch a single target.

    Returns:
        A dictionary containing details about a target.
    """
    try:
        target = Target.objects.get(id=target_id)
    except (ValidationError, Target.DoesNotExist) as e:
        raise ApiError(
            http.HTTPStatus.NOT_FOUND, message=f"Target {target_id} not found."
        ) from e
    title = request.json.get("title")
    description = request.json.get("description")
    image = target.feature_set.image
    text = target.feature_set.text
    if image:
        if title:
            target.feature_set.image.title = title
        if description:
            target.feature_set.image.description = description
    elif text:
        if title:
            target.feature_set.text.title = title
        if description:
            target.feature_set.text.description = description

    views = request.json.get("views")
    if views:
        target.feature_set.engagement_metrics.views = views
    creator = request.json.get("creator")
    if creator and creator.get("ip_address"):
        target.feature_set.creator.ip_address = creator.get("ip_address")
    client_context = request.json.get("client_context")
    if client_context:
        target.client_context = client_context
    target.save()

    return _to_dict(target), http.HTTPStatus.OK


def _to_dict(target: Target) -> dict[str, Any]:
    result = {
        "id": str(target.id),
        "create_time": target.create_time,
    }
    if target.client_context:
        result["client_context"] = target.client_context
    image = target.feature_set.image
    text = target.feature_set.text
    if image:
        result["content_bytes"] = base64.b64encode(image.data)
        if image.title:
            result["title"] = image.title
        if image.description:
            result["description"] = image.description
        result["safe_search_scores"] = {
            "adult": target.feature_set.image.adult_likelihood.name,
            "spoof": target.feature_set.image.spoof_likelihood.name,
            "medical": target.feature_set.image.medical_likelihood.name,
            "violence": target.feature_set.image.violence_likelihood.name,
            "racy": target.feature_set.image.racy_likelihood.name,
        }
    elif text:
        if text.title:
            result["title"] = text.title
        if text.description:
            result["description"] = text.description
    if target.feature_set.engagement_metrics:
        result["views"] = target.feature_set.engagement_metrics.views
    if target.feature_set.creator and target.feature_set.creator.ip_address:
        result["creator"] = {"ip_address": target.feature_set.creator.ip_address}
    return result
