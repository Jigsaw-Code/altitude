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

"""Utility functions dealing with MongoDB connections."""

import contextlib
import logging
import os

import mongoengine
from flask import Flask
from flask_mongoengine import MongoEngine

from mongodb import update


def _get_secret(path):
    try:
        with open(path, "r", encoding="utf-8") as secret_file:
            return secret_file.readline().rstrip("\n")
    except FileNotFoundError as e:
        logging.exception(e)
    return None


DATABASE = os.environ.get("MONGO_DATABASE")
HOST = os.environ.get("MONGO_SERVER", "localhost")
PORT = 27017
_USERNAME_FILE = os.environ.get("MONGO_USERNAME_FILE")
_PASSWORD_FILE = os.environ.get("MONGO_PASSWORD_FILE")
USERNAME = _get_secret(_USERNAME_FILE) if _USERNAME_FILE else None
PASSWORD = _get_secret(_PASSWORD_FILE) if _PASSWORD_FILE else None
TZ_AWARE = True

CONFIG = {
    "db": DATABASE,
    "host": HOST,
    "port": PORT,
    "username": USERNAME,
    "password": PASSWORD,
    "authentication_source": DATABASE,
    "tz_aware": TZ_AWARE,
}


@contextlib.contextmanager
def connect(*args, **kwargs):
    """A context manager to connect to MongoDB using the MongoEngine.

    This is useful for non-Flask scripts that want to connect directly to MongoDB using
    MongoEngine.

    Args:
        *args: Positional arguments to pass on to the MongoEngine connection.
        **kwargs: Keyword arguments to pass on to the MongoEngine connection.

    Example usage:

        def main():
            with connection.connect(**connection.CONFIG):
                update_my_entities()
    """
    connection = mongoengine.connect(*args, **kwargs)
    try:
        update.update()
        yield connection
    finally:
        mongoengine.disconnect()


def init_app(app: Flask):
    """Initializes a MongoDB connection on a Flask application."""
    MongoEngine().init_app(app)
    update.update()
