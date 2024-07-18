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

# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10-slim AS python

# Set environment variable to dump logs to stdout instead of being buffered.
ENV PYTHONUNBUFFERED 1

# Configure Poetry
# https://python-poetry.org/docs#ci-recommendations
ENV POETRY_VERSION=1.3.0
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Install Poetry
FROM python as poetry

RUN apt-get --fix-missing update \
    && apt-get --fix-broken install \
    # gcc is required for pdqhash dependency.
    && apt-get install gcc g++ -y \
    # Tesseract OCR engine is required for pytesseract dependency.
    # See https://github.com/tesseract-ocr/tesseract.
    && apt-get install tesseract-ocr -y \
    && apt-get install libtesseract-dev -y \
    && apt-get clean

RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

FROM poetry

COPY --from=poetry ${POETRY_VENV} ${POETRY_VENV}
ENV PATH="${PATH}:${POETRY_VENV}/bin"

COPY poetry.lock pyproject.toml ./
WORKDIR /build
RUN poetry check
RUN poetry install --no-interaction --no-cache --no-root --without dev
COPY ./src /build

CMD [ "poetry", "run", "python", "server.py" ]
