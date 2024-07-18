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

"""Utilities for working with iterators."""

import itertools
from typing import Iterator, TypeVar

T = TypeVar("T")


def grouper(
    iterable: Iterator[T], n: int  # pylint: disable=invalid-name
) -> Iterator[tuple[T]]:
    """Yields data into chunks of a given size, without filling the last chunk."""
    # Similar to https://docs.python.org/3/library/itertools.html#itertools-recipes but
    # without fixed-length chunks (i.e. it does not fill up the last chunk).
    while True:
        chunk = tuple(itertools.islice(iterable, n))
        if not chunk:
            return
        yield chunk
