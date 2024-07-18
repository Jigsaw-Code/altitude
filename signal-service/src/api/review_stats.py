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

"""API view for the ReviewStats resource.

The ReviewStats resource is a read-only singleton resource (see http://aip.dev/156)
with a single `Users` resource parent.
"""

import collections

from flask import Blueprint

from api.validation import Validator
from models.case import Case, Review

bp = Blueprint("ReviewStats", __name__, url_prefix="/cases/review_stats")


@bp.get("/")
@Validator(
    input_schema={
        "title": "ReviewStats API input schema",
        "type": "null",
    },
    output_schema={
        "title": "ReviewStats API output schema",
        "type": "object",
        "properties": {
            "count_approved": {"type": "number"},
            "count_removed": {"type": "number"},
            "count_active": {"type": "number"},
        },
        "required": [
            "count_approved",
            "count_removed",
            "count_active",
        ],
        "additionalProperties": False,
    },
)
def _get():
    """Get the summary statistics for reviews."""
    all_cases = Case.objects(review_history__exists=True)
    counter = collections.Counter(
        (case.latest_review.decision for case in all_cases if case.latest_review)
    )

    return {
        "count_approved": counter[Review.Decision.APPROVE],
        "count_removed": counter[Review.Decision.BLOCK],
        # TODO - even Cases that have a Review are considered
        # "ACTIVE", not sure if that's a bug, but it makes this number
        # unintuitive (ie something can be approved and active at the same
        # time).
        "count_active": Case.objects(state=Case.State.ACTIVE).count(),
    }
