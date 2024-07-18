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

"""Task implementations that will be executed by the taskqueue workers.

The easiest way to run a task from this module is using its `delay()` method. For
example, to run the task defined by `generate_hashes()` below, you would run:

    tasks.generate_hashes.delay(target_id="target123")

See https://docs.celeryq.dev/en/stable/userguide/calling.html for further documentation
on how to call tasks.

TODO: Consider wrapping tasks in an easier interface to abstract more of Celery away.
"""

import datetime
import enum
import itertools
import json
import logging
import os
from typing import Iterable

import requests
from bson.objectid import ObjectId
from celery import chain, chord, group, shared_task
from celery.exceptions import SoftTimeLimitExceeded
from celery_singleton import Singleton as SingletonTask
from mongoengine import DoesNotExist
from threatexchange.signal_type.pdq import PdqSignal

import config
from analyzers import ocr, perspective, safe_search, translation
from importers import importer, tcap_csv
from indexing.index import Index, IndexMatch, IndexNotFoundError, SerializedIndexMatch
from models import features
from models.case import Case, Review
from models.features.image import Likelihood
from models.importer import ImporterConfig, ImporterLoadError
from models.signal import Content, Signal, Source, Sources
from models.target import FeatureSet, Target
from taskqueue.config import EXPORT_DIAGNOSTICS_FREQUENCY_DAYS
from utils import hashing

# The expiration time for importer task locks.
SIGNAL_IMPORTER_LOCK_EXPIRATION_SEC = 60 * 60 * 1  # 1 hour
# How many signals to yield in a chunk when an importer is run.
SIGNAL_IMPORTER_CHUNK_SIZE = 200
# TODO: Configure CSV filepath in the UI using the `ImporterConfig` class.
SIGNAL_IMPORTER_CSV_FILEPATH = os.environ.get("CSV_FILEPATH")

# The local filepath where to write logs for tasks, if any.
LOG_FILEPATH = "/logs/tasks"

ACTION_RECEIVER_URL = os.environ.get("ACTION_RECEIVER_URL")
DEFAULT_MAX_RETRIES = 5

DEFAULT_SAFE_SEARCH_THRESHOLD = Likelihood.POSSIBLE
SAFE_SEARCH_THRESHOLD = Likelihood(
    int(os.environ.get("SAFE_SEARCH_THRESHOLD", DEFAULT_SAFE_SEARCH_THRESHOLD))
)
# Whether to enable the Safe Search API. If enabled, it will send content from targets to
# the Safe Search API and create cases when the API returns a score that exceeds the threshold
# for the violence attribute.
ENABLE_SAFE_SEARCH_API = os.environ.get("ENABLE_SAFE_SEARCH_API", "").lower() == "true"
# Scores from perspective API above threshold will cause a case to be created.
# TODO: Make the threshold user-adjustable.
PERSPECTIVE_THRESHOLD = 0.7

# Whether to enable the Perspective API. If enabled, it will send text from targets to
# the Perspective API and create cases when the API returns high scores for any of the
# attributes.
ENABLE_PERSPECTIVE_API = os.environ.get("ENABLE_PERSPECTIVE_API", "").lower() == "true"

# Whether to enable the Translation API. If enabled, it will translate the text provided
# to the desired language. The text can be from a Text Target or from the text found
# within an Image target using OCR processing.
ENABLE_TRANSLATION_API = os.environ.get("ENABLE_TRANSLATION_API", "").lower() == "true"


@shared_task()
def generate_hashes(target_id: str):
    """Generates required hashes for the given Target entity.

    Args:
        target_id: The Target entity ObjectId identifier.

    Returns:
        A PDQ hash of the target entity's image, if the quality is high enough.
    """
    logging.info("Running hashing task for target %s", target_id)

    target = Target.objects.get(id=target_id)
    pdq_digest = PdqSignal.hash_from_bytes(target.feature_set.image.data)

    if not pdq_digest:
        logging.info(
            "PDQ hash for target %s is unusable because the quality is too low. The "
            "provided image is probably too small.",
            target_id,
        )
        return None

    target.feature_set.image.pdq_digest = pdq_digest
    target.save()

    return pdq_digest


@shared_task(
    autoretry_for=(IndexNotFoundError,),
    retry_backoff=5 * 60,  # 5 minutes
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def query_indices(pdq_digest: str | None, target_id: str) -> list[SerializedIndexMatch]:
    """Queries the existing indices using a PDQ hash digest to find a match.

    Args:
        pdq_digest: The hash digest to match against PDQ index.
        target_id: The Target entity ObjectId identifier that generated the PDQ digest.

    Returns:
       A list of matches.
    """
    logging.info("Running PDQ query index task for target %s", target_id)

    if not pdq_digest:
        logging.info("No PDQ hash for target %s", target_id)
        return []

    try:
        index = Index.load(index_type=PdqSignal)
    except IndexNotFoundError as e:
        logging.error("Unable to query index: %s", e)
        # TODO: Do we want to manually kick off a task to rebuild indices?
        raise

    return [match.serialize() for match in index.query(pdq_digest)]


@shared_task()
def process_matches(
    matches: list[SerializedIndexMatch], target_id: str
) -> list[str] | None:
    """Processes potential index matches by creating a list of signal ids.

    Args:
        matches: The index matches found, as dictionaries of type IndexMatch.
        target_id: The Target entity identifier for which we queried the index.

    Returns:
        signals: A list containing signals ids for each match that was found.
    """
    logging.info(
        "Running processing task for %d index matches for target %s",
        len(matches),
        target_id,
    )

    if not matches:
        logging.info("No index matches found for target %s", target_id)
        return None

    signal_ids = []
    for serialized_match in matches:
        match = IndexMatch.deserialize(serialized_match)
        signal_ids.append(match.metadata.signal_id)
    return signal_ids


@shared_task()
def process_safe_search(target_id: str) -> list[str] | None:
    """Processes Target entity throught Safe Search Detection API.

    Args:
        target_id: The Target entity identifier.
    Returns:
        If the 'Violence' attribute is higher than the threshold, the Safe Search
        signal id is returned.
    """
    if not ENABLE_SAFE_SEARCH_API:
        logging.info(
            "Safe Search API disabled. Skipping safe search processing for target %s.",
            target_id,
        )
        return None
    logging.info("Running safe search processing on target %s", target_id)

    target = Target.objects.get(id=target_id)
    safe = safe_search.SafeSearch().analyze(data=target.feature_set.image.data)

    target.feature_set.image.adult_likelihood = safe["adult"]
    target.feature_set.image.spoof_likelihood = safe["spoof"]
    target.feature_set.image.medical_likelihood = safe["medical"]
    target.feature_set.image.violence_likelihood = safe["violence"]
    target.feature_set.image.racy_likelihood = safe["racy"]
    target.save()
    if (
        target.feature_set.image.violence_likelihood < SAFE_SEARCH_THRESHOLD
    ):  # TODO Allow users to choose which likelihood value is checked
        logging.info(
            "Results were less than '%s' for Target %s",
            SAFE_SEARCH_THRESHOLD.name,
            target_id,
        )
        return None

    try:
        signal = (
            Signal.objects(sources__sources__0__name=Source.Name.SAFE_SEARCH)
            .only("id")
            .get()
        )
    except Signal.DoesNotExist:
        signal = Signal(
            content=[
                Content(
                    value="https://vision.googleapis.com/v1/images:annotate",
                    content_type=Content.ContentType.API,
                )
            ],
            sources=Sources(sources=[Source(name=Source.Name.SAFE_SEARCH)]),
        )
        signal.save()

    return [str(signal.id)]


@shared_task()
def process_new_image_target(target_id: str):
    """Processes a new Target entity by sending it through Safe Search,
       OCR, and Hash & Query processing.

    Args:
        target_id: The Target entity ObjectId identifier.
    """
    logging.info("Running processing task for new target %s", target_id)

    kwargs = {"target_id": target_id}
    # Workflow order is specific to avoid errors. Chains cannot be the first in Groups.
    workflow = chord(
        group(
            process_safe_search.s(**kwargs),
            process_ocr.s(**kwargs),
            chain(
                generate_hashes.s(**kwargs),
                query_indices.s(**kwargs),
                process_matches.s(**kwargs),
            ),
        ),
        generate_cases.s(**kwargs),
    )
    workflow()


@shared_task()
def generate_cases(results: Iterable[Iterable[str] | None], target_id: str):
    """Creates cases based on the results from various evaluation sub-processes.

    This is the final step of various evaluation processes, where a target is evaluated
    to determine whether it needs to be reviewed by a human. Some examples are targets
    matched against a hash index or targets that meet a threshold against some API.

    Targets go through any number of those steps in parallel, and all results from
    these steps are concatenated into this final step, where they get merged into a
    single case if one needs to be created.

    Args:
        results: An iterable of results from the processes completed on the content.
            Each result is either an iterable of signal IDs or None.
        target_id: The Target entity ObjectId identifier.
    """
    signal_ids = list(
        itertools.chain.from_iterable(x for x in results if x is not None)
    )
    if not signal_ids:
        logging.info("No case will be created for target %s.", target_id)
        return
    # If an active case already exists for the target, let's update that one instead of
    # creating a new one.
    if target_id is None:
        case = None
    else:
        case = (
            Case.objects()
            .filter(target_id=ObjectId(target_id))
            .filter(state=Case.State.ACTIVE)
            .first()
        )
    if case:
        logging.info("Found existing active case %s for target %s", case.id, target_id)
    else:
        logging.info("Creating new case for target %s", target_id)
        case = Case(target_id=ObjectId(target_id) if target_id else None)
    existing_signal_ids = set(case.signal_ids)
    existing_signal_ids.update(ObjectId(signal_id) for signal_id in signal_ids)
    case.signal_ids = list(existing_signal_ids)
    case.save()


@shared_task()
def process_ocr(target_id: str) -> list[str] | None:
    """Extracts text from a given Target entity using Optical Character Recognition (OCR).

    If text was found, then it will be translated and processed utilizing Perspective.

    Args:
        target_id: The Target entity ObjectId identifier.

    Returns:
        If the perspective scores pass the set threshold, then the Perspective Signal ID
        is returned. Otherwise, None is returned.
    """
    logging.info("Running OCR processing task for target %s", target_id)

    target = Target.objects.get(id=target_id)
    ocr_text = ocr.OCR().analyze(target.feature_set.image.data).strip()
    if not ocr_text:
        logging.info(
            "OCR text for target %s is empty. The "
            "provided image did not have text that OCR could identify.",
            target_id,
        )
        return None
    target.feature_set.image.ocr_text = features.text.Text(data=ocr_text)
    if ENABLE_TRANSLATION_API:
        translate_response = translation.Translate().analyze(data=ocr_text)
        if translate_response:
            target.feature_set.image.ocr_text.translated_data = translate_response[0]
            target.feature_set.image.ocr_text.detected_language_code = (
                translate_response[1]
            )
    if not ENABLE_PERSPECTIVE_API:
        logging.info(
            "Perspective API disabled. Skipping scoring for target %s.", target_id
        )
        target.save()
        return None

    # When running Perspective, we use the original text instead of the translated text
    # to avoid the loss of meaning that can occur during translation.
    try:
        scores = perspective.Perspective().analyze(ocr_text)
    except perspective.Error as e:
        logging.error("Perspective analysis failed: %s", e)
        target.save()
        return None

    target.feature_set.image.ocr_text.perspective_scores = scores
    target.save()
    if scores.get("THREAT", 0) < PERSPECTIVE_THRESHOLD:
        return None

    try:
        signal = (
            Signal.objects(sources__sources__0__name=Source.Name.PERSPECTIVE)
            .only("id")
            .get()
        )
    except Signal.DoesNotExist:
        signal = Signal(
            content=[
                Content(
                    value="https://perspectiveapi.com",
                    content_type=Content.ContentType.API,
                )
            ],
            sources=Sources(sources=[Source(name=Source.Name.PERSPECTIVE)]),
        )
        signal.save()
    return [str(signal.id)]


@shared_task()
def process_new_signals(signal_ids: Iterable[str]):
    """Processes new Signal entities after they are first imported.

    Args:
        signal_ids: The Signal entity ObjectId identifiers.
    """
    signal_ids = [ObjectId(i) for i in signal_ids]
    logging.info("Running processing task for %d new signals", len(signal_ids))

    signals = Signal.objects.in_bulk(signal_ids)

    for signal in signals.values():
        if signal.is_url_only:
            url = signal.content[0].value
            pdq_digest = hashing.generate_pdq_hash_from_url(url)

            if pdq_digest:
                signal.content.append(
                    Content(value=pdq_digest, content_type=Content.ContentType.HASH_PDQ)
                )
                signal.save()

    # URL-based signals are currently processed and converted to hash and passed through the
    # same pipeline as hash-based signals. If the URL was unable to be processed to a hash,
    # then it will create a case.
    # TODO: Create cases for these signals without a target.
    for signal in signals.values():
        if signal.is_url_only:
            context = signal.content[0].value
            target = Target(client_context=context, feature_set=FeatureSet())
            target.save()
            generate_cases.s(
                results=[[str(signal.id)]], target_id=str(target.id)
            ).delay()


@shared_task()
def generate_perspective_scores(target_id: str):
    """Populates a text target's score if there is a match by making a call to Perspective API.

    Args:
        target_id: The target object identifier.

    Returns:
        scores: Text Target's perspective scores as a dictionary.
    """
    if not ENABLE_PERSPECTIVE_API:
        logging.info(
            "Perspective API disabled. Skipping scoring for target %s.", target_id
        )
        return {}

    target = Target.objects.get(id=target_id)

    try:
        scores = perspective.Perspective().analyze(data=target.feature_set.text.data)
    except perspective.Error as e:
        logging.error("Perspective analysis failed: %s", e)
        return {}

    target.feature_set.text.perspective_scores = scores
    target.save()
    return scores


@shared_task()
def process_perspective_scores(scores: dict[str, float], target_id: str):
    """Uses Perspective API scores of a text Target to create a case if
    a score is any score is above the threshold.

    Args:
        target_id: The target object identifier.
        scores: Dictionary of Perspective API attributes and scores.
    """

    if scores.get("THREAT", 0) < PERSPECTIVE_THRESHOLD:
        return

    perspective_signal_id = (
        Signal.objects(sources__sources__0__name=Source.Name.PERSPECTIVE)
        .only("id")
        .get()
        .id
    )

    case = Case(
        signal_ids=[perspective_signal_id],
        target_id=ObjectId(target_id),
    )

    logging.info(
        "Creating a new case for text target %s",
        target_id,
    )
    Case.objects.insert(case)


@shared_task()
def process_new_text_target(target_id: str):
    """Processes a new Text Target entity by sending it through the scoring
    and case creation workflow.

    Args:
        target_id: The Target entity ObjectId identifier.
    """
    logging.info("Running processing task for new target %s", target_id)

    if ENABLE_TRANSLATION_API:
        target = Target.objects.get(id=target_id)
        translate_response = translation.Translate().analyze(
            data=target.feature_set.text.data
        )
        if translate_response:
            target.feature_set.text.translated_data = translate_response[0]
            target.feature_set.text.detected_language_code = translate_response[1]
            target.save()

    workflow = chain(
        generate_perspective_scores.s(target_id),
        process_perspective_scores.s(target_id),
    )
    workflow()


@shared_task()
def rebuild_indices():
    """Rebuilds indices for all imported signals."""
    logging.info("Running index rebuild task.")

    # Create an index for PDQ signals and save it.
    index = Index(index_type=PdqSignal).build(Signal.pdq)
    index.save()


def _send_review(decision_json):
    "Sends review to action receiver and raises exception on error."
    if not ACTION_RECEIVER_URL:
        log_dir = os.path.join(LOG_FILEPATH, "verdict-notifier")
        try:
            os.mkdir(log_dir)
        except OSError:
            logging.info("Directory `%s` already exists.", log_dir)
        verdict_path = os.path.join(
            log_dir,
            f"{datetime.date.today().strftime('%Y%m%d')}.txt",
        )
        with open(verdict_path, "a+", encoding="utf-8") as verdict_file:
            verdict_file.write(json.dumps(decision_json, sort_keys=True))
            verdict_file.write("\n")
        return

    try:
        response = requests.post(ACTION_RECEIVER_URL, json=decision_json, timeout=30)
    except requests.exceptions.RequestException as e:
        logging.error("%s POST Request failed: %s", ACTION_RECEIVER_URL, e)
        raise

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error("HTTP Error occured: %s", e)
        raise


@shared_task(
    autoretry_for=(requests.exceptions.RequestException, requests.exceptions.HTTPError),
    retry_backoff=5 * 60,  # 5 minutes
    retry_jitter=True,
    retry_kwargs={"max_retries": DEFAULT_MAX_RETRIES},
)
def deliver_review(case_id: str, review_id: str):
    "Sends a case review decision to the client via a preconfigured endpoint."
    logging.info(
        "Running deliver review task for case %s and review %s", case_id, review_id
    )

    case = Case.objects.get(id=case_id)
    target = Target.objects.get(id=case.target_id)
    review = case.review_history.get(id=review_id)
    decision_json = {
        "client_context": target.client_context,
        "decision": review.decision.value,
        "decision_time": review.create_time.isoformat(),
    }
    try:
        _send_review(decision_json)
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
        logging.error("%s POST Request failed: %s", ACTION_RECEIVER_URL, e)
        if deliver_review.request.retries < DEFAULT_MAX_RETRIES:
            raise
        review.delivery_status = Review.DeliveryStatus.FAILED
        logging.info("Seting `delivery_status` to failed: %s", review.delivery_status)
    else:
        review.delivery_status = Review.DeliveryStatus.ACCEPTED
    case.save()


@shared_task()
def publish_review(case_id: str, review_id: str):
    """Publishes a draft review and delivers it to clients."""
    logging.info(
        "Running publish review task for case %s and review %s",
        case_id,
        review_id,
    )

    case = Case.objects.get(id=case_id)
    try:
        review = case.review_history.get(id=review_id, state=Review.State.DRAFT)
    except DoesNotExist:
        logging.info("No review found for case %s and review %s", case_id, review_id)
        # The draft review may have been deleted or already published. Nothing to do here.
        return

    review.state = Review.State.PUBLISHED
    case.save()
    deliver_review.delay(case_id=case_id, review_id=review_id)


@enum.unique
class ImporterType(str, enum.Enum):
    """Valid importer types."""

    TCAP_API = "TCAP_API"
    TCAP_CSV = "TCAP_CSV"
    THREAT_EXCHANGE_API = "THREAT_EXCHANGE_API"


def get_importer_config(importer_type: ImporterType) -> ImporterConfig:
    """Returns the correct ImporterConfig based on the given type.

    Args:
        importer_type: The type of importer to run.

    Returns:
        The requested importer config.

    Raises:
        ImporterLoadError: If the requested importer is not configured
            properly (e.g. the credentials are missing) or has been disabled.
    """
    try:
        importer_config = ImporterConfig.objects.get(type=importer_type)
    except ImporterConfig.DoesNotExist as e:
        raise ImporterLoadError(
            f"No configuration found for importer {importer_type}"
        ) from e

    return importer_config


def get_importer(importer_type: ImporterType) -> importer.Importer:
    """Returns the correct Importer based on the given type and stored configuration.

    Args:
        importer_type: The type of importer to run.

    Returns:
        The requested importer.

    Raises:
        ImporterLoadError: If the requested importer is not configured
            properly (e.g. the credentials are missing) or has been disabled.
    """
    if importer_type == ImporterType.TCAP_CSV:
        return tcap_csv.TcapCsvImporter(filepath=SIGNAL_IMPORTER_CSV_FILEPATH)

    importer_config = get_importer_config(importer_type)
    return importer_config.to_importer()


@shared_task(
    base=SingletonTask,
    lock_expiry=SIGNAL_IMPORTER_LOCK_EXPIRATION_SEC,
    time_limit=SIGNAL_IMPORTER_LOCK_EXPIRATION_SEC,
    soft_time_limit=SIGNAL_IMPORTER_LOCK_EXPIRATION_SEC - 60 * 5,
)
def run_signal_importer(importer_type: ImporterType):
    """Runs a single signal importer for a given type.

    This is a potentially long running task, especially the first time it's run and does
    a backfill. It requires a pretty high `time_limit` and `soft_time_limit`.
    """
    try:
        signal_importer = get_importer(importer_type)
    except ImporterLoadError as e:
        logging.warning("Skipping import: %s", e)
        return
    try:
        for signal_ids in signal_importer.run(SIGNAL_IMPORTER_CHUNK_SIZE):
            logging.info("Enqueueing %d new signals", len(signal_ids))
            process_new_signals.delay(signal_ids=tuple(str(id) for id in signal_ids))
    except importer.Error as e:
        logging.error("Unexpected importer error: %s", e)
    except SoftTimeLimitExceeded:
        logging.info("Maximum running time exceeded for import")


@shared_task()
def import_signals():
    """Imports all signals by kicking off individual importers, one for each type."""
    tasks = [
        run_signal_importer.s(importer_type=ImporterType.TCAP_API),
        run_signal_importer.s(importer_type=ImporterType.THREAT_EXCHANGE_API),
    ]

    if config.DEVELOPMENT_APP_VERSION:
        tasks.append(run_signal_importer.s(importer_type=ImporterType.TCAP_CSV))

    workflow = group(*tasks)
    workflow()


@shared_task(
    base=SingletonTask,
    autoretry_for=(requests.exceptions.RequestException, requests.exceptions.HTTPError),
    retry_backoff=5 * 60,  # 5 minutes
    retry_jitter=True,
    retry_kwargs={"max_retries": DEFAULT_MAX_RETRIES},
)
def export_signal_diagnostic(importer_type: ImporterType):
    """Runs a single task to export diagnostics for a given type."""
    try:
        importer_config = get_importer_config(importer_type)
    except ImporterLoadError as e:
        logging.warning("Skipping sending diagnostics: %s", e)
        return

    if importer_config.diagnostics_state != importer_config.State.ACTIVE:
        return

    today_with_tz = datetime.datetime.now(datetime.timezone.utc)
    importer_config.to_importer().send_diagnostics(
        today_with_tz - datetime.timedelta(days=EXPORT_DIAGNOSTICS_FREQUENCY_DAYS),
        today_with_tz,
    )


@shared_task()
def export_signal_diagnostics():
    """Kicks off an individual jobs for each source to send diagnostics."""
    tasks = [
        export_signal_diagnostic.s(importer_type=ImporterType.TCAP_API),
        export_signal_diagnostic.s(importer_type=ImporterType.THREAT_EXCHANGE_API),
    ]

    if config.DEVELOPMENT_APP_VERSION:
        tasks.append(export_signal_diagnostic.s(importer_type=ImporterType.TCAP_CSV))

    workflow = group(*tasks)
    workflow()
