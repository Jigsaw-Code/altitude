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

SHELL=/bin/bash

export TAG = prod
export PORT ?= 8080
export SERVE_PATH ?= /
export COMPOSE_PROJECT_NAME = altitude-${TAG}
export COMPOSE_FILE_ARGS = -f infrastructure/docker/compose.yml -f infrastructure/docker/compose.prod.yml

export NGINX_SERVE_PATH := $(SERVE_PATH:/=)
export FLOWER_URL_PREFIX = $(patsubst /%,%/,$(SERVE_PATH:/=))

SECRETS_DIR=$(CURDIR)/secrets

$(SECRETS_DIR):
	@mkdir $(SECRETS_DIR)

MONGODB_CREDENTIAL_FILES = $(SECRETS_DIR)/mongodb_root_username.txt $(SECRETS_DIR)/mongodb_root_password.txt $(SECRETS_DIR)/mongodb_username.txt $(SECRETS_DIR)/mongodb_password.txt

$(MONGODB_CREDENTIAL_FILES): | $(SECRETS_DIR)
	$(eval default=test)
	$(eval name := $(shell sed -e 's/_/ /g' <<< $(basename $(@F))))
	$(eval user := $(shell read -p "$(name) [default=\"$(default)\"]: " username; echo $$username))
	@echo -n $(or $(user), $(default)) > $@

GOOGLE_APP_CREDENTIAL_FILE = $(SECRETS_DIR)/google_app_credentials.json

$(GOOGLE_APP_CREDENTIAL_FILE): | $(SECRETS_DIR)
	@echo -n "{}" > $@

presetup:
	@echo 'Setting up...'

setup: presetup $(MONGODB_CREDENTIAL_FILES) $(GOOGLE_APP_CREDENTIAL_FILE)
	@echo 'Setup done.'

PROD: ## Set up prod mode. Use as `make PROD build start` etc.
	$(eval TAG = prod)
	$(eval COMPOSE_PROJECT_NAME = altitude-${TAG})
	$(eval COMPOSE_FILE_ARGS = -f infrastructure/docker/compose.yml -f infrastructure/docker/compose.prod.yml)

DEV: ## Set up dev mode. Use as `make DEV build start` etc.
	$(eval TAG = dev)
	$(eval COMPOSE_PROJECT_NAME = altitude-${TAG})
	$(eval COMPOSE_FILE_ARGS = -f infrastructure/docker/compose.yml -f infrastructure/docker/compose.dev.yml)

echo-vars:
	@echo TAG=${TAG}
	@echo PORT=${PORT}
	@echo SERVE_PATH=${SERVE_PATH}
	@echo COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}
	@echo ACTION_RECEIVER_URL=${ACTION_RECEIVER_URL}

build: echo-vars ## Build all Docker containers
	docker compose ${COMPOSE_FILE_ARGS} build --parallel

start: setup echo-vars ## Start all Docker containers.
	docker compose ${COMPOSE_FILE_ARGS} up

stop: echo-vars ## Stop all Docker containers.
	docker compose ${COMPOSE_FILE_ARGS} down

rm-containers: echo-vars # Remove Docker containers where (com.google.jigsaw.tag="${TAG}").
	@echo 'Removing filtered containers (com.google.jigsaw.tag="${TAG}").'
	@-docker rm -f $(shell docker container ls -aq --filter "label=com.google.jigsaw.tag=${TAG}")

rm-volumes: echo-vars # Remove Docker volumes where (com.google.jigsaw="${TAG}").
	@echo 'Removing filtered volumes (com.google.jigsaw="${TAG}").'
	@-docker volume rm -f $(shell docker volume ls -q --filter "label=com.google.jigsaw.tag=${TAG}")

rm-networks: echo-vars  # Remove Docker networks where (com.google.jigsaw="${TAG}").
	@echo 'Removing filtered networks (com.google.jigsaw="${TAG}").'
	@-docker network rm -f $(shell docker network ls -q --filter "label=com.google.jigsaw.tag=${TAG}")

rm-images: echo-vars # Remove Docker images where (com.google.jigsaw.tag="${TAG}").
	@echo 'Removing filtered images (com.google.jigsaw.tag="${TAG}").'
	@-docker rmi -f $(shell docker image ls -q --filter "label=com.google.jigsaw.tag=${TAG}")

clean-docker: rm-containers rm-volumes rm-networks rm-images ## Clean all Docker assets (containers, volumes, networks, and images) where (com.google.jigsaw.tag="${TAG}").
	@echo 'Done cleaning Docker assets.'

clean: stop clean-docker ## Clean up everything except persistent database and secrets.

nuke: clean ## Clean plus removes persistent database and secrets.
	@echo 'We have to use sudo to clean out MongoDB data folders. You may be asked for your password.'
	@sudo rm -rf mongodb/data

	@rm -rf $(SECRETS_DIR)

	@echo 'Done cleaning database and secrets.'

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: presetup setup PROD DEV echo-vars build start stop rm-containers rm-volumes rm-networks rm-images clean-docker clean nuke help

.DEFAULT_GOAL := help
