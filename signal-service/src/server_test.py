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

# pylint: disable=missing-docstring
"""Test that the server behaves as expected with some end-to-end API calls."""

import http
from unittest import mock

import flask_app
from api import signal
from testing import test_case


class ServerTest(test_case.ApiTestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = flask_app.application

    def test_routes(self):
        routes = []
        with self.app.app_context():
            for rule in self.app.url_map.iter_rules():
                methods = " ".join(sorted(rule.methods))
                routes.append(f"{rule.rule}    {methods}    {rule.endpoint}")
        observed_routes_string = "\n".join(sorted(routes))

        self.assertMultiLineEqual(
            _EXPECTED_ROUTES_GOLDEN_STRING, observed_routes_string
        )

    def test_invalid_path_returns_not_found(self):
        self.get(
            "/foobar",
            expected_status=http.HTTPStatus.NOT_FOUND,
            expected_message=(
                "The requested URL was not found on the server. If you entered "
                "the URL manually please check your spelling and try again."
            ),
        )

    @mock.patch.object(signal.Signal, "objects", new_callable=mock.PropertyMock)
    def test_exceptions_are_caught_and_return_api_errors(self, mock_objects):
        mock_objects.side_effect = TypeError

        self.get(
            "/signals/",
            expected_status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            expected_message="Server got itself in trouble",
        )


_EXPECTED_ROUTES_GOLDEN_STRING = """
/cases/    GET HEAD OPTIONS    Case._list
/cases/    OPTIONS POST    Case._create
/cases/<case_id>    GET HEAD OPTIONS    Case._get
/cases/<case_id>    OPTIONS PATCH    Case._update
/cases/<case_id>/reviews/    OPTIONS POST    Review._create
/cases/<case_id>/reviews/<review_id>    DELETE OPTIONS    Review._delete
/cases/review_stats/    GET HEAD OPTIONS    ReviewStats._get
/importers/    OPTIONS POST    Importer._create
/importers/<importer_type>    DELETE OPTIONS    Importer._delete
/importers/<importer_type>    GET HEAD OPTIONS    Importer._get
/reviews/<review_id>    DELETE OPTIONS    Review._delete
/signals/    GET HEAD OPTIONS    Signal._list
/signals/    OPTIONS POST    Signal._create
/signals/<signal_id>    GET HEAD OPTIONS    Signal._get
/targets/    OPTIONS POST    Target._create
/targets/<target_id>    GET HEAD OPTIONS    Target._get
/targets/<target_id>    OPTIONS PATCH    Target._update
""".strip()
