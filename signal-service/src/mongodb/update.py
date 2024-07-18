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

"""Functionality to update the database to resolve breaking changes."""

# pylint: disable=protected-access

import logging

import pymongo

import config
from models.settings import Settings
from models.signal import Signal


def update():
    """Updates the database to resolve breaking changes.

    As these changes are to fix MongoEngine backwards incompatible changes, we
    can't use MongoEngine itself to update documents (except for Settings singletone
    used), as the entities stored in the database may not longer be consistent with the
    new schema. As such, we need to use the PyMongo driver directly to make changes.
    """
    if config.UNIT_TEST_VERSION:
        logging.info(
            "Skip updating database in tests; MongoMock does not yet support array "
            "filters."
        )
        return

    settings = Settings.get_singleton()
    print(f"Current database version: {settings.version}")

    if settings.version < "0.0.1":
        print("Updating database to version 0.0.1")

        # Rename source "TCAP API" to "TCAP".
        Signal._get_collection().update_many(
            {"sources.sources.name": "TCAP API"},
            {"$set": {"sources.sources.$[element].name": "TCAP"}},
            array_filters=[{"element.name": "TCAP API"}],
        )

        # Rename source to "GIFCT" and move the sub-name to a new `author` field.
        # We can't reference one field (`name`) to set another (`author`) in a single
        # query, so we need to do it manually.
        updates = []
        for doc in Signal._get_collection().find(
            {
                "$and": [
                    {"sources.sources.name": {"$not": {"$regex": "GIFCT"}}},
                    {"sources.sources.description": {"$regex": "GIFCT"}},
                ]
            }
        ):
            updated_sources = []
            for source in doc["sources"]["sources"]:
                if "GIFCT" in source["description"]:
                    source["author"] = source["name"]
                    source["name"] = "GIFCT"
                updated_sources.append(source)
            updates.append(
                pymongo.UpdateOne(
                    {"_id": doc["_id"]}, {"$set": {"sources.sources": updated_sources}}
                )
            )
        if updates:
            Signal._get_collection().bulk_write(updates, ordered=False)

        settings.version = "0.0.1"

    settings.save()
    print(f"Current database version after updates: {settings.version}")
