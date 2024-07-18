# Copyright 2024 Google LLC
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

"""Utilities for encoding and decoding pagination cursor tokens."""
import base64
import json
from typing import Any


def encode_cursor(cursor: dict[str, Any]) -> str:
    return base64.b64encode(json.dumps(cursor).encode()).decode("utf-8")


def decode_cursor(encoded_cursor: str) -> dict[str, Any]:
    return json.loads(base64.b64decode(encoded_cursor).decode())
