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

"""JSON related helpers for the API."""

from typing import Any

from flask.json import provider

from utils import json


class JSONProvider(provider.JSONProvider):
    """A custom Flask JSON provider to be used in the API."""

    def dumps(self, *args: Any, **kwargs: Any) -> str:
        """Serializes object to a JSON formatted string."""
        return json.dumps(*args, **kwargs)

    def loads(self, *args: Any, **kwargs: Any) -> Any:
        """Deserializes data as JSON."""
        return json.loads(*args, **kwargs)
