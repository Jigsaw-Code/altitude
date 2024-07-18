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

"Update priority of existing Cases in database."
#!/usr/bin/env python

import pymongo
from absl import app, flags

from models.case import Case
from mongodb import connection

_DRY_RUN = flags.DEFINE_bool(
    "dry_run",
    True,
    "If true, skips writing updates to database. It will only log the intended "
    "updates.",
)

# TODO: Consider how this could be optimized. UpdateMany is a potential option
# if we can find a way to set a field based on the value of another field
# in a custom Python function.


def update_priority(dry_run: bool):
    """Updates priority of all Cases that have the required fields.

    Args:
        dry_run: If True, will only print what would have changed, no actual mutations
            occur.
    """
    if dry_run:
        print("This is a dry run!")

    updates = []
    for case in Case.objects:
        # pylint: disable=protected-access
        field_name = case._fields.get("priority").name
        old_priority = case._data.get(field_name)
        # pylint: enable=protected-access
        if case.priority != old_priority:
            if dry_run:
                print(
                    f"The current priority of Signal '{case.id}' "
                    f"is '{old_priority}'. The expected priority "
                    f"update is '{case.priority}'."
                )
                continue

            # NOTE: We could simply `.save() documents one at a time here, but we use
            # the PyMongo driver that's powering MongoEngine directly so we can save
            # them in batches to increase throughput.
            case.validate()
            updates.append(
                pymongo.UpdateOne(
                    {"_id": case.id},
                    {"$set": case.to_mongo(fields=[field_name]).to_dict()},
                )
            )
    if not dry_run and updates:
        collection = Case._get_collection()  # pylint: disable=protected-access
        print(f"Updating priorities in {collection.name} collection...")
        collection.bulk_write(updates, ordered=False)
        print("Completed updating priorities.")


def main(_):  # pylint: disable=missing-docstring
    with connection.connect(**connection.CONFIG):
        update_priority(_DRY_RUN.value)


if __name__ == "__main__":
    app.run(main)
