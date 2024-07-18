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

"""API view for the Importer resource."""

import http
import json
import logging
from typing import Any

from flask import Blueprint, request

from api.api_error import ApiError
from api.validation import Validator
from importers.importer import PreCheckError
from models.importer import Credential, ImporterConfig
from models.job import Job

_IMPORTER_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": [x.name for x in ImporterConfig.Type],
        },
        "state": {
            "type": "string",
            "enum": [x.name for x in ImporterConfig.State],
        },
        "diagnostics_state": {
            "type": "string",
            "enum": [x.name for x in ImporterConfig.State],
        },
        "last_run_time": {
            "type": ["string", "null"],
            "format": "date-time",
        },
        "total_import_count": {"type": "number"},
        "credential": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string"},
                "token": {"type": "string"},
            },
            "required": ["identifier", "token"],
            "additionalProperties": False,
        },
    },
    "required": [
        "type",
        "state",
        "diagnostics_state",
        "total_import_count",
        "credential",
    ],
    "additionalProperties": False,
}

bp = Blueprint("Importer", __name__, url_prefix="/importers/")


@bp.post("/")
@Validator(
    input_schema={
        "title": "Importer Create API input schema",
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": [x.name for x in ImporterConfig.Type]},
            "state": {
                "type": "string",
                "enum": ["ACTIVE", "INACTIVE"],
            },
            "diagnostics_state": {
                "type": "string",
                "enum": ["ACTIVE", "INACTIVE"],
            },
            "credential": {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string"},
                    "token": {"type": "string"},
                },
                "required": ["identifier", "token"],
                "additionalProperties": False,
            },
        },
        "required": ["type", "credential"],
        "additionalProperties": False,
    },
    output_schema={
        "title": "Importer Create API output schema",
    }
    | _IMPORTER_SCHEMA,
)
def _create():
    state = request.json.get("state", ImporterConfig.State.ACTIVE)
    diagnostics_state = request.json.get(
        "diagnostics_state", ImporterConfig.State.INACTIVE
    )
    config = ImporterConfig(
        type=request.json.get("type"),
        state=state,
        diagnostics_state=diagnostics_state,
        credential=Credential(
            identifier=request.json.get("credential").get("identifier"),
            token=request.json.get("credential").get("token"),
        ),
    )

    # Confirm the provided configuration works with a pre-check. This is most likely to
    # fail on incorrect credentials.
    importer = config.to_importer()
    try:
        importer.pre_check()
    except PreCheckError as e:
        msg = f"Importer {config.type} failed pre-check. Please check your credentials."
        raise ApiError(http.HTTPStatus.BAD_REQUEST, message=msg) from e
    config.save()

    logging.info("Created %s importer", config.type)

    return _to_dict(config), http.HTTPStatus.CREATED


@bp.get("/<importer_type>")
@Validator(
    input_schema={
        "title": "Importer Get API input schema",
        "type": "null",
    },
    output_schema={
        "title": "Importer Get API output schema",
    }
    | _IMPORTER_SCHEMA,
)
def _get(importer_type: str):
    """Returns a single Importer by its type.

    Args:
        importer_type: The type of importer to fetch.

    Returns:
        A dictionary containing details about the importer.
    """
    try:
        importer = ImporterConfig.objects.get(type=importer_type.upper())
    except ImporterConfig.DoesNotExist as e:
        raise ApiError(
            http.HTTPStatus.NOT_FOUND,
            message=f"Importer {importer_type.upper()} not found.",
        ) from e

    return _to_dict(importer)


@bp.delete("/<importer_type>")
@Validator(
    input_schema={
        "title": "Importer Delete API input schema",
        "type": "null",
    },
    output_schema={
        "title": "Importer Delete API output schema",
        "type": "null",
    },
)
def _delete(importer_type: str):
    try:
        importer = ImporterConfig.objects.get(type=importer_type.upper())
    except ImporterConfig.DoesNotExist as e:
        raise ApiError(
            http.HTTPStatus.NOT_FOUND,
            message=f"Importer {importer_type.upper()} not found.",
        ) from e

    importer.delete()
    return json.dumps({}), http.HTTPStatus.NO_CONTENT


def _to_dict(importer: ImporterConfig) -> dict[str, Any]:
    last_job = Job.objects(source=importer.type.value).order_by("-start_time").first()
    aggregation_pipeline = Job.objects(source=importer.type.value).aggregate(
        [
            {
                "$group": {
                    "_id": "null",
                    "totalImportSize": {"$sum": "$import_size"},
                }
            },
        ]
    )
    try:
        import_count = next(aggregation_pipeline)["totalImportSize"]
    except StopIteration:
        import_count = 0
    return {
        "type": importer.type,
        "state": importer.state,
        "diagnostics_state": importer.diagnostics_state,
        "last_run_time": last_job.start_time if last_job else None,
        "total_import_count": import_count,
        "credential": {
            "identifier": importer.credential.identifier,
            # TODO: Consider obfuscating the token here?
            "token": importer.credential.token,
        },
    }
