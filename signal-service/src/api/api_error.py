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

"""Error-related classes and utilities for the API."""

import http


class ApiError(Exception):
    """Exception raised for errors in API calls."""

    http_status = None

    def __init__(self, http_status=http.HTTPStatus.INTERNAL_SERVER_ERROR, message=None):
        message = message or http_status.description
        super().__init__(message)
        self.message = message
        self.http_status = http_status

    def __str__(self):
        return self.message

    def to_dict(self):
        return {
            "error": {
                "code": self.http_status.value,
                "message": self.message,
                "status": self.http_status.phrase,
            }
        }
