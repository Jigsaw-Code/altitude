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

"""Server that runs our backend APIs."""

import multiprocessing
import os

import config
import flask_app
import gunicorn_app
from mongodb import connection


def main():
    """Main entrypoint when running the server."""
    connection.init_app(flask_app.application)
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8082))
    if config.DEVELOPMENT_APP_VERSION:
        flask_app.application.run(debug=True, host=host, port=port)
    else:
        options = {
            "bind": f"{host}:{port}",
            "workers": multiprocessing.cpu_count() * 2 + 1,
        }
        gunicorn_app.StandaloneApplication(flask_app.application, options).run()


if __name__ == "__main__":
    main()
