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

"""Application settings."""

from __future__ import annotations

from mongoengine import Document, fields


class Settings(Document):
    """A central singleton settings model."""

    version = fields.StringField(default="0.0.0")

    @classmethod
    def get_singleton(cls) -> Settings:
        try:
            return next(cls.objects)
        except StopIteration:
            return cls()
