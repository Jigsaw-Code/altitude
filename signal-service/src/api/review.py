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

"""API view for the Review resource."""

import http
import json
import logging
from typing import Any

from flask import Blueprint, request
from mongoengine import ValidationError

from api.api_error import ApiError
from api.validation import Validator
from models.case import Case, Review
from taskqueue import tasks

_REVIEW_SCHEMA = {
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
}

bp = Blueprint("Review", __name__)


DRAFT_TO_PUBLISH_DELAY_SEC = 60


@bp.post("/cases/<case_id>/reviews/")
@Validator(
    input_schema={
        "title": "Reviews Create API input schema",
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": [x.name for x in Review.Decision],
            },
        },
        "required": ["decision"],
        "additionalProperties": False,
    },
    output_schema={
        "title": "Reviews Create API output schema",
    }
    | _REVIEW_SCHEMA,
)
def _create(case_id: str):
    try:
        case = Case.objects.get(id=case_id)
    except (ValidationError, Case.DoesNotExist) as e:
        raise ApiError(
            http.HTTPStatus.NOT_FOUND, message=f"Case {case_id} not found."
        ) from e

    decision = Review.Decision[request.json.get("decision")]
    review = Review(state=Review.State.DRAFT, decision=decision)
    case.review_history.append(review)
    case.save()
    logging.info("Created %s review for %s", decision.value, case_id)

    tasks.publish_review.apply_async(
        kwargs={"case_id": str(case.id), "review_id": str(review.id)},
        countdown=DRAFT_TO_PUBLISH_DELAY_SEC,
    )
    return to_dict(review), http.HTTPStatus.CREATED


@bp.delete("/reviews/<review_id>")
@bp.delete("/cases/<case_id>/reviews/<review_id>")
@Validator(
    input_schema={
        "title": "Reviews Delete API input schema",
        "type": "null",
    },
    output_schema={
        "title": "Reviews Delete API output schema",
        "type": "null",
    },
)
def _delete(review_id: str, case_id: str | None = None):
    if case_id:
        try:
            case = Case.objects.get(id=case_id)
        except (ValidationError, Case.DoesNotExist) as e:
            raise ApiError(
                http.HTTPStatus.NOT_FOUND, message=f"Case {case_id} not found."
            ) from e
    else:
        try:
            case = Case.objects.get(review_history__id=review_id)
        except ValidationError as e:
            raise ApiError(
                http.HTTPStatus.NOT_FOUND, message=f"Review {review_id} not found."
            ) from e

    filtered_reviews = []
    for review in case.review_history:
        if str(review.id) != review_id:
            filtered_reviews.append(review)
            continue
        if review.state != Review.State.DRAFT:
            raise ApiError(
                http.HTTPStatus.METHOD_NOT_ALLOWED,
                message=f"Review {review_id} on case {case.id} cannot be deleted.",
            )
        break
    else:
        raise ApiError(
            http.HTTPStatus.NOT_FOUND,
            message=f"Review {review_id} not found on case {case_id}.",
        )

    case.review_history = filtered_reviews
    case.save()
    return json.dumps(None), http.HTTPStatus.NO_CONTENT


def to_dict(review: Review) -> dict[str, Any]:
    result = {"id": str(review.id), "create_time": review.create_time}
    if review.decision:
        result["decision"] = review.decision
    if review.user:
        result["user"] = review.user
    return result
