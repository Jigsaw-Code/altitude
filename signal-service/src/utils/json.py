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

"""Utilities for JSON decoding and encoding."""

import datetime
import enum
import json
from typing import Any, Type

from indexing.index import IndexEntryMetadata, IndexMatch


class JSONDecodeError(ValueError):
    """Error raised when input cannot be decoded as JSON."""


class JSONEncoder(json.JSONEncoder):
    """A custom JSON encoder."""

    def default(self, o):
        if isinstance(o, (IndexEntryMetadata, IndexMatch)):
            return o.to_dict()
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()
        if isinstance(o, enum.Enum):
            return o.value
        if isinstance(o, bytes):
            return o.decode(errors="ignore")
        return super().default(o)


def dumps(
    obj: Any, cls: Type[json.JSONEncoder] | None = JSONEncoder, **kwargs: Any
) -> str:
    """Serializes object to a JSON formatted string.

    Args:
        obj: The object to convert to JSON.
        cls: optional JSONEncoder to use instead of the default. Defaults to our
            applicatons custom `JSONEncoder`.
        **kwargs: Keyword arguments to pass to `json.dumps()`.

    Returns:
        The JSON formatted string.
    """
    return json.dumps(obj, cls=cls, **kwargs)


def loads(data: str | bytes, **kwargs: Any) -> Any:
    """Deserializes data as JSON.

    Args:
        data: Text or UTF-8 bytes.
        **kwargs: Keyword arguments to pass to `json.loads()`.

    Returns:
        The deserialized data.

    Raises:
        JSONDecodeError: If there is a problem with string encodings.
    """
    try:
        return json.loads(data, **kwargs)
    except ValueError as e:
        raise JSONDecodeError(str(e)) from e
