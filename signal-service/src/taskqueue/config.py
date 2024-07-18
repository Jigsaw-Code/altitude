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

"""Configuration details for the Celery taskqueue.

See https://docs.celeryq.dev/en/stable/userguide/configuration.html for details on
Celery configuration and defaults.
"""
# pylint: disable=invalid-name

import os
from datetime import timedelta

# Broker settings.
broker_url = os.environ.get("CELERY_BROKER_URL")

# Database to store task state and results.
result_backend = os.environ.get("CELERY_RESULT_BACKEND")

# List of modules to import when the worker starts.
imports = ("taskqueue.tasks",)

# No need to store the task return values. However, we do want to store errors.
task_ignore_result = True
task_store_errors_even_if_ignored = True

# Set a global 15-minute task soft timeout. Individual tasks can override this.
task_soft_time_limit = 60 * 15

# How often to export diagnostics in days.
EXPORT_DIAGNOSTICS_FREQUENCY_DAYS = 7

# Crontab schedules.
beat_schedule = {
    "import-signals": {
        "task": "taskqueue.tasks.import_signals",
        "schedule": timedelta(seconds=60),
    },
    "rebuild-indices": {
        "task": "taskqueue.tasks.rebuild_indices",
        "schedule": timedelta(minutes=15),
    },
    "export-signal-diagnostics": {
        "task": "taskqueue.tasks.export_signal_diagnostics",
        "schedule": timedelta(days=EXPORT_DIAGNOSTICS_FREQUENCY_DAYS),
    },
}
