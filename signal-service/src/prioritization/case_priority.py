# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may 1t use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Generate scores used in prioritization based off signal and target features."""

import enum
from typing import Iterable

from bson.objectid import ObjectId

from models.signal import ContentFeatures, Signal, Source

# Map of priority label to the minimum score for each label.
# Low: [1,2], Medium: [3,4], High: [5+]
PRIORITY_SCORE_LOWER_BOUND_MAP = {"HIGH": 5, "MEDIUM": 3, "LOW": 1}
# Priority score map for the individual features: confidence and severity.
PRIORITY_FEATURE_SCORE_MAP = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
# The maximum possible severity score possible used to boost the most severe
# cases to the top.
MAXIMUM_SEVERITY_SCORE = PRIORITY_FEATURE_SCORE_MAP["HIGH"] * 2 + 1
# The maximum possible priority score possible used to boost the most severe
# cases to the top.
MAXIMUM_PRIORITY_SCORE = MAXIMUM_SEVERITY_SCORE + PRIORITY_FEATURE_SCORE_MAP["HIGH"]

TRUSTED_SOURCES = frozenset([Source.Name.TCAP])

MAX_SEVERITY_TAGS = frozenset(["media_priority_s3"])

HIGH_SEVERITY_TAGS = frozenset(
    [
        "cat:am",
        "cat:irf",
        "media_priority_crisis",
    ]
)
MEDIUM_SEVERITY_TAGS = frozenset(
    [
        "media_priority_s0",
        "media_priority_s1",
        "media_priority_s2",
    ]
)


@enum.unique
class Level(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


def calculate_confidence(signal_ids: Iterable[ObjectId]) -> int | None:
    """Calculates confidence based on sources, confidence, and trust.

    Args:
      signal_ids: List of signal IDs associated with Case.

    Returns:
      Integer between 0 and 3 representing how likely the content is to actually
      be TVEC, taking the maximum confidence calculated across all signal ids
      associated with the case.
    """
    if not signal_ids:
        return None

    confidence_scores = []
    # TODO: Consider best way to get the max scores across signals.
    for signal in Signal.objects(id__in=signal_ids):
        confidence = 0
        trust = signal.content_features.trust if signal.content_features else -1
        confidence_score = (
            signal.content_features.confidence if signal.content_features else -1
        )
        source_names = {x.name for x in signal.sources.sources}
        if len(source_names) > 1 or (source_names & TRUSTED_SOURCES) or (trust > 0.7):
            confidence = PRIORITY_FEATURE_SCORE_MAP["HIGH"]
        elif (0.5 < trust < 0.7) or (confidence_score >= 0.5):
            confidence = PRIORITY_FEATURE_SCORE_MAP["MEDIUM"]
        elif confidence_score > 0.1:
            confidence = PRIORITY_FEATURE_SCORE_MAP["LOW"]
        confidence_scores.append(confidence)
    return max(confidence_scores, default=None)


def calculate_severity(signal_ids: Iterable[ObjectId]) -> int | None:
    """Calculates severity based on tags and features on the Signal.

    Args:
      signal: The signal corresponding to the Case.

    Returns:
      Integer between 0 and 7 that represents how quickly action is required,
      taking the maximum severity calculated across all signal ids
      associated with the case.
    """
    if not signal_ids:
        return None

    severity_scores = []
    # TODO: Consider best way to get the max scores across signals.
    for signal in Signal.objects(id__in=signal_ids):
        severity = 0
        features = signal.content_features
        if features:
            if any(tag in MAX_SEVERITY_TAGS for tag in features.tags):
                # Boost to the top by creating the maximum priority score possible.
                severity = MAXIMUM_SEVERITY_SCORE
            elif (
                len(features.associated_terrorist_organizations) > 1
                or features.is_violent_or_graphic == ContentFeatures.Confidence.YES
                or any(tag in HIGH_SEVERITY_TAGS for tag in features.tags)
            ):
                severity = PRIORITY_FEATURE_SCORE_MAP["HIGH"]
            elif features.contains_pii == ContentFeatures.Confidence.YES or any(
                tag in MEDIUM_SEVERITY_TAGS for tag in features.tags
            ):
                severity = PRIORITY_FEATURE_SCORE_MAP["MEDIUM"]
            elif ContentFeatures.Confidence.UNSURE in (
                features.contains_pii,
                features.is_violent_or_graphic,
            ):
                severity = PRIORITY_FEATURE_SCORE_MAP["LOW"]
        severity_scores.append(severity)
    return max(severity_scores, default=None)


def get_confidence_level(confidence: int) -> Level:
    """The confidence level of the case."""
    if confidence == PRIORITY_FEATURE_SCORE_MAP["HIGH"]:
        return Level.HIGH
    if confidence == PRIORITY_FEATURE_SCORE_MAP["MEDIUM"]:
        return Level.MEDIUM
    return Level.LOW


def get_severity_level(severity: int) -> Level:
    """The severity level of the case."""
    if severity >= PRIORITY_FEATURE_SCORE_MAP["HIGH"]:
        return Level.HIGH
    if severity >= PRIORITY_FEATURE_SCORE_MAP["MEDIUM"]:
        return Level.MEDIUM
    return Level.LOW


def get_priority_level(priority: int) -> Level:
    """The priority level of the case."""
    if priority >= PRIORITY_SCORE_LOWER_BOUND_MAP["HIGH"]:
        return Level.HIGH
    if priority >= PRIORITY_SCORE_LOWER_BOUND_MAP["MEDIUM"]:
        return Level.MEDIUM
    return Level.LOW
