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

"""Flask app object to be used by the web server and Celery taskqueue workers."""

import api
from mongodb.connection import CONFIG as MONGODB_CONFIG

application = api.Api("AltitudeSignalService", static_folder=None)
application.config["PROPAGATE_EXCEPTIONS"] = True
application.config["MONGODB_SETTINGS"] = [MONGODB_CONFIG]
