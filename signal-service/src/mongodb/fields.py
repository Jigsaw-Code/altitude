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

"""Custom MongoEngine fields to use in our application models."""

import datetime
from typing import Callable

from mongoengine import fields


class ListField(fields.ListField):
    """A list field with added functionality.

    In particular, it is able to filter out `None` values.
    """

    def __init__(
        self,
        *args,
        filter_predicate: Callable | None = None,
        **kwargs,
    ):
        """Constructor.

        Args:
            filter_predicate: A predicate to filter the list on. This callable will be
                passed to `filter(..., value)` to filter items from the list. A common
                use case is to filter out None values, by passing `None.__ne__` as the
                predicate.
        """
        super().__init__(*args, **kwargs)
        self._filter_predicate = filter_predicate

    def __get__(self, instance, owner):
        data = super().__get__(instance, owner)
        if isinstance(data, list) and self._filter_predicate is not None:
            data[:] = list(filter(self._filter_predicate, data))
        return data

    def __set__(self, instance, value):
        if isinstance(value, list) and self._filter_predicate is not None:
            value[:] = filter(self._filter_predicate, value)
        return super().__set__(instance, value)  # pytype: disable=attribute-error


class ExpireDateTimeField(fields.DateTimeField):
    """A datetime field that auto-expires.

    In particular, it amends the standard `DateTimeField` to remove expired datetime
    fields based on the specified expiration time, if provided.
    """

    def __init__(self, *args, expiration: datetime.timedelta | None = None, **kwargs):
        """Constructor.

        Args:
            expiration: A timedelta representing how long before the field expires.
                Expired dates are returned as `None`.
        """
        super().__init__(*args, **kwargs)
        self._expiration = expiration

    def _has_expired(self, value: datetime.datetime) -> bool:
        if self._expiration is None:
            return False
        return datetime.datetime.now(datetime.timezone.utc) - value > self._expiration

    def to_python(self, value):
        value = super().to_python(value)
        if value is None or self._has_expired(value):
            return None
        return value

    def validate(self, value):
        super().validate(value)

        if self._has_expired(value):
            self.error("`DateTimeField()` only accepts values that have not expired")
