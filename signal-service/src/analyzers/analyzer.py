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

"""Define abstract class for all APIs used to analyze content."""

import abc
import functools

import google.auth
from google.auth.credentials import Credentials


class Error(Exception):
    """Base class for exceptions in this module."""


class APIKeyPathError(Error):
    """Error message for Safe Search API response."""


class Analyzer(metaclass=abc.ABCMeta):
    """Interface for APIs used in content analysis."""

    @abc.abstractmethod
    def analyze(self, data):
        """Runs the respective processing method for the Analyzer."""
        raise NotImplementedError()

    @functools.cached_property
    def credentials(self) -> Credentials:
        """Returns the default Google Cloud credentials for the current environment."""
        credentials, _ = google.auth.default()
        return credentials
