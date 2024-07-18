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

"""Taskqueue worker entrypoint."""

import logging

from celery import current_app as current_celery_app
from celery.signals import worker_ready
from celery_singleton import clear_locks
from flask_celeryext import AppContextTask, FlaskCeleryExt

from flask_app import application
from mongodb import connection
from taskqueue import config


def create_celery_app(app):
    celery_app = current_celery_app
    celery_app.config_from_object(config)
    celery_app.flask_app = app
    celery_app.Task = AppContextTask
    return celery_app


@worker_ready.connect
def clear_all_locks(**unused_kwargs):
    """If Celery has unexpectedly crashed, there may be orphaned locks.

    This can cause a deadlock because there is no running task that can release the
    lock. So we clear all existing locks on worker startup.

    See https://github.com/steinitzu/celery-singleton?tab=readme-ov-file#handling-deadlocks.
    """
    logging.info("Clearing all locks.")
    clear_locks(current_celery_app)


connection.init_app(application)
celery_ext = FlaskCeleryExt(create_celery_app=create_celery_app)
celery_ext.init_app(application)
celery = celery_ext.celery
