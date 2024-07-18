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

"""API module with all required handlers."""

import http
import logging
from typing import Iterable, Type

from flask import Blueprint, Flask, jsonify
from werkzeug.exceptions import HTTPException

from api import api_error, case, importer, json, review, review_stats, signal, target

_BLUEPRINTS = frozenset(
    [
        case.bp,
        importer.bp,
        review.bp,
        review_stats.bp,
        signal.bp,
        target.bp,
    ]
)


class Api(Flask):
    """Main API application."""

    json_provider_class = json.JSONProvider

    def __init__(
        self, import_name, blueprints: Iterable[Type[Blueprint]] | None = None, **kwargs
    ):
        """Initializes application and binds views.

        Args:
          import_name: The name of the application package.
          blueprints: Iterable of blueprints to register to the application.
        """
        super().__init__(import_name, **kwargs)

        self._blueprints = blueprints or _BLUEPRINTS
        for blueprint in self._blueprints:
            self.register_blueprint(blueprint)

        self.register_error_handler(Exception, self.handle_error)
        self.register_error_handler(HTTPException, self.handle_http_error)
        self.register_error_handler(api_error.ApiError, self.handle_api_error)

    def handle_error(self, error: Exception):
        logging.exception(error)
        return self.handle_api_error(api_error.ApiError())

    def handle_http_error(self, error: HTTPException):
        http_status = http.HTTPStatus(error.code)
        return self.handle_api_error(api_error.ApiError(http_status, error.description))

    def handle_api_error(self, error: api_error.ApiError):
        response = jsonify(error.to_dict())
        response.status_code = error.http_status
        return response
