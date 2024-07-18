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
# pylint: disable=too-many-lines
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-lines
"""Test that the server behaves as expected."""

import http
import json
from unittest import mock

import requests
from absl.testing import absltest, parameterized
from threatexchange.signal_type.pdq import PdqSignal

import server
from testing import test_case


def _make_response(content: str, status: int = http.HTTPStatus.OK) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = content.encode("utf-8")  # pylint: disable=protected-access
    return response


class ServerTest(parameterized.TestCase, test_case.TestCase):
    def setUp(self):
        super().setUp()

        requests_patch = mock.patch.multiple(
            requests,
            get=mock.DEFAULT,
            post=mock.DEFAULT,
            delete=mock.DEFAULT,
            patch=mock.DEFAULT,
            autospec=True,
        )
        self.mock_requests = requests_patch.start()

        self.mock_case_response = {
            "id": "abc",
            "signal_ids": ["def"],
            "target_id": "ghi",
            "create_time": "2000-12-26T00:00:00",
            "state": "ACTIVE",
            "review_history": [],
        }

        self.mock_signal_response = {
            "id": "def",
            "content": [
                {
                    "value": "https://www.google.com/",
                    "content_type": "URL",
                }
            ],
            "sources": [
                {
                    "name": "TCAP",
                    "create_time": "2000-12-25T00:00:00",
                }
            ],
            "content_features": {
                "associated_entities": [],
                "contains_pii": "NO",
                "is_violent_or_graphic": "YES",
                "is_illegal_in_countries": [],
            },
            "status": {
                "last_checked_time": "2010-03-12T00:00:00",
                "most_recent_status": "ACTIVE",
            },
        }
        self.mock_target_response = {
            "title": "Title",
            "description": "Description",
            "creator": {
                "ip_address": "1.2.3.4",
            },
            "views": 10,
            "create_time": "2000-12-25T00:00:00",
            "safe_search_scores": {
                "adult": "POSSIBLE",
                "spoof": "POSSIBLE",
                "medical": "POSSIBLE",
                "violence": "POSSIBLE",
                "racy": "POSSIBLE",
            },
        }
        self.mock_ip_response = {"country_name": "United States"}
        self.mock_similar_cases_response = {
            "data": [
                {
                    "id": "xyz",
                    "signal_ids": ["def"],
                    "target_id": "lmnop",
                    "create_time": "2000-12-26T00:00:00",
                    "state": "ACTIVE",
                    "review_history": [],
                }
            ]
        }

    def test_invalid_path_returns_not_found(self):
        with server.app.test_client() as client:
            response = client.get("/foobar")
        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)

    def test_get_case_sends_correct_requests_to_signals_api(self):
        self.mock_requests["get"].side_effect = [
            _make_response(json.dumps({"signal_ids": ["def"], "target_id": "ghi"})),
            _make_response(json.dumps({})),
            _make_response(json.dumps({})),
            _make_response(json.dumps({"data": []})),
        ]

        with server.app.test_client() as client:
            client.get("/get_case/abc")

        self.mock_requests["get"].assert_has_calls(
            [
                mock.call("http://signal-service:8082/cases/abc", timeout=mock.ANY),
                mock.call("http://signal-service:8082/signals/def", timeout=mock.ANY),
                mock.call("http://signal-service:8082/targets/ghi", timeout=mock.ANY),
                mock.call(
                    "http://signal-service:8082/cases?signal_id=def",
                    timeout=mock.ANY,
                ),
            ]
        )

    def test_get_case_sends_multiple_signal_id_requests_to_signals_api(self):
        self.mock_requests["get"].side_effect = [
            _make_response(
                json.dumps({"signal_ids": ["def", "xyz"], "target_id": "ghi"})
            ),
            _make_response(json.dumps({})),
            _make_response(json.dumps({})),
            _make_response(json.dumps({})),
            _make_response(json.dumps({"data": []})),
        ]

        with server.app.test_client() as client:
            client.get("/get_case/abc")

        self.mock_requests["get"].assert_has_calls(
            [
                mock.call("http://signal-service:8082/cases/abc", timeout=mock.ANY),
                mock.call("http://signal-service:8082/signals/def", timeout=mock.ANY),
                mock.call("http://signal-service:8082/signals/xyz", timeout=mock.ANY),
                mock.call("http://signal-service:8082/targets/ghi", timeout=mock.ANY),
                mock.call(
                    "http://signal-service:8082/cases?signal_id=def&signal_id=xyz",
                    timeout=mock.ANY,
                ),
            ]
        )

    def test_get_cases_sends_correct_requests_to_signals_api(self):
        self.mock_requests["get"].side_effect = [
            _make_response(
                json.dumps(
                    {
                        "data": [
                            {"signal_ids": ["abc"], "target_id": "ghi"},
                            {"signal_ids": ["def"], "target_id": "jkl"},
                        ],
                        "total_count": 1,
                    }
                )
            ),
            _make_response(json.dumps({})),
            _make_response(json.dumps({})),
            _make_response(json.dumps({})),
            _make_response(json.dumps({})),
        ]

        with server.app.test_client() as client:
            client.get("/get_cases")

        self.mock_requests["get"].assert_has_calls(
            [
                mock.call(
                    "http://signal-service:8082/cases?state=active&"
                    "next_cursor_token=None&previous_cursor_token=None"
                    "&page_size=None",
                    timeout=mock.ANY,
                ),
                mock.call("http://signal-service:8082/signals/abc", timeout=mock.ANY),
                mock.call("http://signal-service:8082/targets/ghi", timeout=mock.ANY),
                mock.call("http://signal-service:8082/signals/def", timeout=mock.ANY),
                mock.call("http://signal-service:8082/targets/jkl", timeout=mock.ANY),
            ]
        )

    def test_get_cases_with_pagination_cursor_sends_correct_requests_to_signals_api(
        self,
    ):
        self.mock_requests["get"].side_effect = [
            _make_response(
                json.dumps(
                    {
                        "data": [
                            {"signal_ids": ["abc"], "target_id": "ghi"},
                            {"signal_ids": ["def"], "target_id": "jkl"},
                        ],
                        "previous_cursor_token": "aaaaaaaaaaaaaaaaaaaaaaaa_4",
                        "next_cursor_token": None,
                        "total_count": 11,
                    }
                )
            ),
            _make_response(json.dumps({})),
            _make_response(json.dumps({})),
            _make_response(json.dumps({})),
            _make_response(json.dumps({})),
        ]

        with server.app.test_client() as client:
            client.get("/get_cases?next_cursor_token=aaaaaaaaaaaaaaaaaaaaaaaa_5")

        self.mock_requests["get"].assert_has_calls(
            [
                mock.call(
                    "http://signal-service:8082/cases?state=active&"
                    "next_cursor_token=aaaaaaaaaaaaaaaaaaaaaaaa_5&"
                    "previous_cursor_token=None&page_size=None",
                    timeout=mock.ANY,
                ),
                mock.call("http://signal-service:8082/signals/abc", timeout=mock.ANY),
                mock.call("http://signal-service:8082/targets/ghi", timeout=mock.ANY),
                mock.call("http://signal-service:8082/signals/def", timeout=mock.ANY),
                mock.call("http://signal-service:8082/targets/jkl", timeout=mock.ANY),
            ]
        )

    def test_add_reviews_sends_correct_requests_to_cases_api(self):
        self.mock_requests["post"].return_value = _make_response(
            json.dumps(
                {
                    "id": "abc",
                    "create_time": "2000-12-25T00:00:00+00:00",
                    "decision": "BLOCK",
                }
            )
        )

        with server.app.test_client() as client:
            client.post("/add_reviews", json={"case_ids": ["abc"], "decision": 1})

        self.mock_requests["post"].assert_called_with(
            "http://signal-service:8082/cases/abc/reviews/",
            json={"decision": "BLOCK"},
            timeout=mock.ANY,
        )

    @parameterized.parameters(
        ({"decision": 3}, "'case_ids' is a required property"),
        ({"case_ids": ["abc"]}, "'decision' is a required property"),
        ({"case_ids": [], "decision": 1}, "[] should be non-empty"),
        ({"case_ids": ["abc"], "decision": 3}, "3 is not one of [1, 2]"),
    )
    def test_add_reviews_raises_bad_request_on_invalid_input(
        self, input_json, expected_error_description
    ):
        with server.app.test_client() as client:
            response = client.post("/add_reviews", json=input_json)

        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            {
                "code": 400,
                "description": expected_error_description,
                "name": "Bad Request",
            },
            response.json,
        )

    def test_delete_reviews(self):
        self.mock_requests["delete"].return_value = _make_response(json.dumps({}))

        with server.app.test_client() as client:
            response = client.delete(
                "/remove_reviews",
                json={"review_ids": ["123"]},
            )

        self.mock_requests["delete"].assert_called_with(
            "http://signal-service:8082/reviews/123",
            timeout=mock.ANY,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertIsNone(response.json)

    def test_add_reviews_returns_relevant_data(self):
        self.mock_requests["post"].return_value = _make_response(
            json.dumps(
                {
                    "id": "abc",
                    "create_time": "2000-12-25T00:00:00+00:00",
                    "decision": "BLOCK",
                }
            )
        )

        with server.app.test_client() as client:
            response = client.post(
                "/add_reviews", json={"case_ids": ["abc"], "decision": 1}
            )

        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertEqual(["abc"], response.json)
        self.mock_requests["post"].assert_called_with(
            "http://signal-service:8082/cases/abc/reviews/",
            json={"decision": "BLOCK"},
            timeout=mock.ANY,
        )

    def test_get_tags_confidence_unsure(self):
        self.mock_signal_response["content_features"] = {
            "associated_entities": [],
            "contains_pii": "UNSURE",
            "is_violent_or_graphic": "YES",
            "is_illegal_in_countries": [],
        }
        self.mock_requests["get"].side_effect = [
            _make_response(json.dumps(self.mock_case_response)),
            _make_response(json.dumps(self.mock_signal_response)),
            _make_response(json.dumps(self.mock_target_response)),
            _make_response(json.dumps(self.mock_similar_cases_response)),
            _make_response(json.dumps(self.mock_ip_response)),
        ]

        with server.app.test_client() as client:
            response = client.get("/get_case/abc")

        self.assertCountEqual(
            ["contains_pii", "is_violent_or_graphic"], response.json["flags"][0]["tags"]
        )

    def test_get_tags_illegal_in_country(self):
        self.mock_signal_response["content_features"] = {
            "associated_entities": [],
            "contains_pii": "NO",
            "is_violent_or_graphic": "YES",
            "is_illegal_in_countries": ["United States"],
        }
        self.mock_requests["get"].side_effect = [
            _make_response(json.dumps(self.mock_case_response)),
            _make_response(json.dumps(self.mock_signal_response)),
            _make_response(json.dumps(self.mock_target_response)),
            _make_response(json.dumps(self.mock_similar_cases_response)),
            _make_response(json.dumps(self.mock_ip_response)),
        ]

        with server.app.test_client() as client:
            response = client.get("/get_case/abc")

        self.assertCountEqual(
            ["is_illegal_in_countries", "is_violent_or_graphic"],
            response.json["flags"][0]["tags"],
        )

    def test_get_case_returns_relevant_data(self):
        self.mock_requests["get"].side_effect = [
            _make_response(
                json.dumps(
                    {
                        "id": "abc",
                        "signal_ids": ["def", "ghi"],
                        "target_id": "ghi",
                        "create_time": "2000-12-26T00:00:00",
                        "state": "ACTIVE",
                        "notes": "Hello World",
                        "priority": 2,
                        "priority_level": "LOW",
                        "confidence": "MEDIUM",
                        "severity": None,
                        "review_history": [],
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "id": "def",
                        "content": [
                            {
                                "value": "https://www.google.com/",
                                "content_type": "URL",
                            }
                        ],
                        "sources": [
                            {
                                "name": "TCAP",
                                "create_time": "2000-12-25T00:00:00",
                            }
                        ],
                        "content_features": {
                            "associated_entities": [],
                            "contains_pii": "NO",
                            "is_violent_or_graphic": "YES",
                            "is_illegal_in_countries": [],
                        },
                        "status": {
                            "last_checked_time": "2010-03-12T00:00:00",
                            "most_recent_status": "ACTIVE",
                        },
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "id": "ghi",
                        "content": [
                            {
                                "value": "foobar",
                                "content_type": "HASH_PDQ",
                            }
                        ],
                        "sources": [
                            {
                                "name": "GIFCT",
                                "create_time": "2000-12-26T00:00:00",
                            }
                        ],
                        "content_features": {
                            "associated_entities": [],
                            "contains_pii": "NO",
                            "is_violent_or_graphic": "YES",
                            "is_illegal_in_countries": [],
                        },
                        "status": {
                            "last_checked_time": "2010-03-12T00:00:00",
                            "most_recent_status": "ACTIVE",
                        },
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "title": "Title",
                        "description": "Description",
                        "creator": {
                            "ip_address": "1.2.3.4",
                        },
                        "views": 10,
                        "create_time": "2000-12-25T00:00:00",
                        "safe_search_scores": {
                            "adult": "POSSIBLE",
                            "spoof": "POSSIBLE",
                            "medical": "POSSIBLE",
                            "violence": "POSSIBLE",
                            "racy": "POSSIBLE",
                        },
                    }
                )
            ),
            _make_response(json.dumps(self.mock_similar_cases_response)),
            _make_response(json.dumps(self.mock_ip_response)),
        ]

        with server.app.test_client() as client:
            response = client.get("/get_case/abc")

        self.assertEqual(
            {
                server.ID: "abc",
                server.CREATE_TIME: "2000-12-26T00:00:00",
                server.STATE: "ACTIVE",
                server.NOTES: "Hello World",
                server.PRIORITY: {
                    server.SCORE: 2,
                    server.LEVEL: "LOW",
                    server.CONFIDENCE: "MEDIUM",
                    server.SEVERITY: None,
                },
                server.REVIEW_HISTORY: [],
                server.SIGNAL_CONTENT: [
                    {
                        server.CONTENT_VALUE: "https://www.google.com/",
                        server.CONTENT_TYPE: "URL",
                    },
                    {
                        server.CONTENT_VALUE: "foobar",
                        server.CONTENT_TYPE: "HASH_PDQ",
                    },
                ],
                server.FLAGS: [
                    {
                        "name": "TCAP",
                        "createTime": "2000-12-25T00:00:00",
                        "tags": ["is_violent_or_graphic"],
                        "authors": [],
                    },
                    {
                        "name": "GIFCT",
                        "createTime": "2000-12-26T00:00:00",
                        "tags": ["is_violent_or_graphic"],
                        "authors": [],
                    },
                ],
                server.ASSOCIATED_ENTITIES: [],
                server.IMAGE_BYTES: None,
                server.ANALYSIS: {
                    server.SAFE_SEARCH_SCORES: {
                        "adult": "POSSIBLE",
                        "spoof": "POSSIBLE",
                        "medical": "POSSIBLE",
                        "violence": "POSSIBLE",
                        "racy": "POSSIBLE",
                    }
                },
                server.TITLE: "Title",
                server.DESCRIPTION: "Description",
                server.VIEWS: 10,
                server.UPLOAD_TIME: "2000-12-25T00:00:00",
                server.IP_ADDRESS: "1.2.3.4",
                server.IP_REGION: "United States",
                server.SIMILAR_CASE_IDS: ["xyz"],
            },
            response.json,
        )

    def test_get_case_returns_default_analysis_scores(self):
        self.mock_requests["get"].side_effect = [
            _make_response(
                json.dumps(
                    {
                        "id": "abc",
                        "signal_ids": ["def"],
                        "target_id": "ghi",
                        "create_time": "2000-12-26T00:00:00",
                        "state": "ACTIVE",
                        "priority": None,
                        "priority_level": None,
                        "confidence": None,
                        "severity": None,
                        "review_history": [],
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "id": "def",
                        "content": [
                            {
                                "value": "https://www.google.com/",
                                "content_type": "URL",
                            }
                        ],
                        "sources": [
                            {
                                "name": "TCAP",
                                "create_time": "2000-12-25T00:00:00",
                            }
                        ],
                        "content_features": {
                            "associated_entities": [],
                            "contains_pii": "NO",
                            "is_violent_or_graphic": "YES",
                            "is_illegal_in_countries": [],
                        },
                        "status": {
                            "last_checked_time": "2010-03-12T00:00:00",
                            "most_recent_status": "ACTIVE",
                        },
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "title": "Title",
                        "description": "Description",
                        "creator": {
                            "ip_address": "1.2.3.4",
                        },
                        "views": 10,
                        "create_time": "2000-12-25T00:00:00",
                    }
                )
            ),
            _make_response(json.dumps(self.mock_similar_cases_response)),
            _make_response(json.dumps(self.mock_ip_response)),
        ]

        with server.app.test_client() as client:
            response = client.get("/get_case/abc")

        self.assertEqual(
            {
                server.ID: "abc",
                server.CREATE_TIME: "2000-12-26T00:00:00",
                server.STATE: "ACTIVE",
                server.NOTES: None,
                server.PRIORITY: {
                    server.SCORE: None,
                    server.LEVEL: None,
                    server.CONFIDENCE: None,
                    server.SEVERITY: None,
                },
                server.REVIEW_HISTORY: [],
                server.SIGNAL_CONTENT: [
                    {
                        server.CONTENT_VALUE: "https://www.google.com/",
                        server.CONTENT_TYPE: "URL",
                    }
                ],
                server.FLAGS: [
                    {
                        "name": "TCAP",
                        "createTime": "2000-12-25T00:00:00",
                        "tags": ["is_violent_or_graphic"],
                        "authors": [],
                    }
                ],
                server.ASSOCIATED_ENTITIES: [],
                server.IMAGE_BYTES: None,
                server.ANALYSIS: {
                    server.SAFE_SEARCH_SCORES: {
                        "adult": "UNKNOWN",
                        "spoof": "UNKNOWN",
                        "medical": "UNKNOWN",
                        "violence": "UNKNOWN",
                        "racy": "UNKNOWN",
                    }
                },
                server.TITLE: "Title",
                server.DESCRIPTION: "Description",
                server.IP_ADDRESS: "1.2.3.4",
                server.IP_REGION: "United States",
                server.UPLOAD_TIME: "2000-12-25T00:00:00",
                server.VIEWS: 10,
                server.SIMILAR_CASE_IDS: ["xyz"],
            },
            response.json,
        )

    def test_get_case_handles_api_signals_without_creation_time(self):
        self.mock_signal_response["sources"] = [
            {
                "name": "SAFE_SEARCH",
                "create_time": None,
            }
        ]
        self.mock_requests["get"].side_effect = [
            _make_response(json.dumps(self.mock_case_response)),
            _make_response(json.dumps(self.mock_signal_response)),
            _make_response(json.dumps(self.mock_target_response)),
            _make_response(json.dumps(self.mock_similar_cases_response)),
            _make_response(json.dumps(self.mock_ip_response)),
        ]

        with server.app.test_client() as client:
            response = client.get("/get_case/abc")

        print(response.json)

        self.assertIsNone(response.json["flags"][0]["createTime"])

    def test_get_case_raises_error_on_signal_service_404(self):
        self.mock_requests["get"].return_value = _make_response(
            json.dumps(
                {
                    "error": {
                        "code": http.HTTPStatus.NOT_FOUND,
                        "message": http.HTTPStatus.NOT_FOUND.description,
                        "status": http.HTTPStatus.NOT_FOUND.phrase,
                    }
                }
            ),
            http.HTTPStatus.NOT_FOUND,
        )

        with server.app.test_client() as client:
            response = client.get("/get_case/abc")

        self.assertEqual(http.HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(
            {
                "code": 404,
                "description": (
                    "The requested URL was not found on the server. "
                    "If you entered the URL manually please check your spelling and try again."
                ),
                "name": "Not Found",
            },
            response.json,
        )

    def test_get_case_raises_error_on_unexpected_signal_service_response(
        self,
    ):
        self.mock_requests["get"].return_value = _make_response(
            json.dumps(
                {
                    "error": {
                        "code": http.HTTPStatus.NOT_ACCEPTABLE,
                        "message": http.HTTPStatus.NOT_ACCEPTABLE.description,
                        "status": http.HTTPStatus.NOT_ACCEPTABLE.phrase,
                    }
                }
            ),
            http.HTTPStatus.NOT_ACCEPTABLE,
        )

        with server.app.test_client() as client:
            response = client.get("/get_case/abc")

        self.assertEqual(http.HTTPStatus.INTERNAL_SERVER_ERROR, response.status_code)
        self.assertEqual(
            {
                "code": 500,
                "description": (
                    "The server encountered an internal error and was unable to complete "
                    "your request. Either the server is overloaded or there is an error in "
                    "the application."
                ),
                "name": "Internal Server Error",
            },
            response.json,
        )

    def test_get_cases_returns_relevant_data(self):
        self.mock_requests["get"].side_effect = [
            _make_response(
                json.dumps(
                    {
                        "data": [
                            {
                                "id": "abc",
                                "signal_ids": ["def"],
                                "target_id": "ghi",
                                "create_time": "2000-12-26T00:00:00",
                                "state": "ACTIVE",
                                "priority": 2,
                                "priority_level": "LOW",
                                "confidence": "MEDIUM",
                                "severity": None,
                                "review_history": [],
                            }
                        ]
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "id": "def",
                        "content": [
                            {
                                "value": "https://www.google.com/",
                                "content_type": "URL",
                            }
                        ],
                        "sources": [
                            {
                                "name": "TCAP",
                                "create_time": "2000-12-25T00:00:00",
                            }
                        ],
                        "content_features": {
                            "associated_entities": [],
                            "contains_pii": "NO",
                            "is_violent_or_graphic": "YES",
                            "is_illegal_in_countries": [],
                        },
                        "status": {
                            "last_checked_time": "2010-03-12T00:00:00",
                            "most_recent_status": "ACTIVE",
                        },
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "title": "Title",
                        "description": "Description",
                        "creator": {
                            "ip_address": "1.2.3.4",
                        },
                        "views": 10,
                        "create_time": "2000-12-25T00:00:00",
                        "safe_search_scores": {
                            "adult": "POSSIBLE",
                            "spoof": "POSSIBLE",
                            "medical": "POSSIBLE",
                            "violence": "POSSIBLE",
                            "racy": "POSSIBLE",
                        },
                    }
                )
            ),
            _make_response(json.dumps(self.mock_ip_response)),
        ]

        with server.app.test_client() as client:
            response = client.get("/get_cases")

        self.assertEqual(
            [
                {
                    server.ID: "abc",
                    server.CREATE_TIME: "2000-12-26T00:00:00",
                    server.STATE: "ACTIVE",
                    server.NOTES: None,
                    server.PRIORITY: {
                        server.SCORE: 2,
                        server.LEVEL: "LOW",
                        server.CONFIDENCE: "MEDIUM",
                        server.SEVERITY: None,
                    },
                    server.REVIEW_HISTORY: [],
                    server.SIGNAL_CONTENT: [
                        {
                            server.CONTENT_VALUE: "https://www.google.com/",
                            server.CONTENT_TYPE: "URL",
                        }
                    ],
                    server.FLAGS: [
                        {
                            "name": "TCAP",
                            "createTime": "2000-12-25T00:00:00",
                            "tags": ["is_violent_or_graphic"],
                            "authors": [],
                        },
                    ],
                    server.ASSOCIATED_ENTITIES: [],
                    server.IMAGE_BYTES: None,
                    server.ANALYSIS: {
                        server.SAFE_SEARCH_SCORES: {
                            "adult": "POSSIBLE",
                            "spoof": "POSSIBLE",
                            "medical": "POSSIBLE",
                            "violence": "POSSIBLE",
                            "racy": "POSSIBLE",
                        }
                    },
                    server.TITLE: "Title",
                    server.DESCRIPTION: "Description",
                    server.IP_ADDRESS: "1.2.3.4",
                    server.IP_REGION: "United States",
                    server.UPLOAD_TIME: "2000-12-25T00:00:00",
                    server.VIEWS: 10,
                    server.SIMILAR_CASE_IDS: [],
                }
            ],
            response.json["data"],
        )

    def get_review_stats_returns_stats(self):
        self.mock_requests["get"].side_effect = {
            _make_response(
                json.dumps(
                    {
                        "count_approved": 2,
                        "count_removed": 4,
                        "count_active": 6,
                    }
                )
            )
        }

        with server.app.test_client() as client:
            response = client.get("/get_review_stats")

        self.assertEqual(
            {server.COUNT_APPROVED: 2, server.COUNT_REMOVED: 4, server.COUNT_ACTIVE: 6},
            response.json(),
        )

    def test_get_cases_returns_default_analysis_scores(self):
        self.mock_requests["get"].side_effect = [
            _make_response(
                json.dumps(
                    {
                        "data": [
                            {
                                "id": "abc",
                                "signal_ids": ["def"],
                                "target_id": "ghi",
                                "create_time": "2000-12-26T00:00:00",
                                "state": "ACTIVE",
                                "priority": 2,
                                "priority_level": "LOW",
                                "confidence": "MEDIUM",
                                "severity": None,
                                "review_history": [],
                            }
                        ]
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "id": "def",
                        "content": [
                            {
                                "value": "https://www.google.com/",
                                "content_type": "URL",
                            }
                        ],
                        "sources": [
                            {
                                "name": "TCAP",
                                "create_time": "2000-12-25T00:00:00",
                            }
                        ],
                        "content_features": {
                            "associated_entities": [],
                            "contains_pii": "NO",
                            "is_violent_or_graphic": "YES",
                            "is_illegal_in_countries": [],
                        },
                        "status": {
                            "last_checked_time": "2010-03-12T00:00:00",
                            "most_recent_status": "ACTIVE",
                        },
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "title": "Title",
                        "description": "Description",
                        "creator": {
                            "ip_address": "1.2.3.4",
                        },
                        "views": 10,
                        "create_time": "2000-12-25T00:00:00",
                    }
                )
            ),
            _make_response(json.dumps(self.mock_ip_response)),
        ]

        with server.app.test_client() as client:
            response = client.get("/get_cases")

        self.assertEqual(
            [
                {
                    server.ID: "abc",
                    server.CREATE_TIME: "2000-12-26T00:00:00",
                    server.STATE: "ACTIVE",
                    server.NOTES: None,
                    server.PRIORITY: {
                        server.SCORE: 2,
                        server.LEVEL: "LOW",
                        server.CONFIDENCE: "MEDIUM",
                        server.SEVERITY: None,
                    },
                    server.REVIEW_HISTORY: [],
                    server.SIGNAL_CONTENT: [
                        {
                            server.CONTENT_VALUE: "https://www.google.com/",
                            server.CONTENT_TYPE: "URL",
                        }
                    ],
                    server.FLAGS: [
                        {
                            "name": "TCAP",
                            "createTime": "2000-12-25T00:00:00",
                            "tags": ["is_violent_or_graphic"],
                            "authors": [],
                        },
                    ],
                    server.ASSOCIATED_ENTITIES: [],
                    server.IMAGE_BYTES: None,
                    server.ANALYSIS: {
                        server.SAFE_SEARCH_SCORES: {
                            "adult": "UNKNOWN",
                            "spoof": "UNKNOWN",
                            "medical": "UNKNOWN",
                            "violence": "UNKNOWN",
                            "racy": "UNKNOWN",
                        }
                    },
                    server.TITLE: "Title",
                    server.DESCRIPTION: "Description",
                    server.IP_ADDRESS: "1.2.3.4",
                    server.IP_REGION: "United States",
                    server.UPLOAD_TIME: "2000-12-25T00:00:00",
                    server.VIEWS: 10,
                    server.SIMILAR_CASE_IDS: [],
                }
            ],
            response.json["data"],
        )

    def test_get_cases_returns_empty_on_signal_service_404(self):
        self.mock_requests["get"].return_value = _make_response(
            json.dumps(
                {
                    "error": {
                        "code": http.HTTPStatus.NOT_FOUND,
                        "message": http.HTTPStatus.NOT_FOUND.description,
                        "status": http.HTTPStatus.NOT_FOUND.phrase,
                    }
                }
            ),
            http.HTTPStatus.NOT_FOUND,
        )

        with server.app.test_client() as client:
            response = client.get("/get_cases")

        self.assertEmpty(response.json)

    def test_get_cases_raises_error_on_unexpected_signal_service_response(
        self,
    ):
        self.mock_requests["get"].return_value = _make_response(
            json.dumps(
                {
                    "error": {
                        "code": http.HTTPStatus.NOT_ACCEPTABLE,
                        "message": http.HTTPStatus.NOT_ACCEPTABLE.description,
                        "status": http.HTTPStatus.NOT_ACCEPTABLE.phrase,
                    }
                }
            ),
            http.HTTPStatus.NOT_ACCEPTABLE,
        )

        with server.app.test_client() as client:
            response = client.get("/get_cases")

        self.assertEqual(http.HTTPStatus.INTERNAL_SERVER_ERROR, response.status_code)
        self.assertEqual(
            {
                "code": 500,
                "description": (
                    "The server encountered an internal error and was unable to complete "
                    "your request. Either the server is overloaded or there is an error in "
                    "the application."
                ),
                "name": "Internal Server Error",
            },
            response.json,
        )

    def test_fallback_title_content_type_url(self):
        self.mock_requests["get"].side_effect = [
            _make_response(
                json.dumps(
                    {
                        "data": [
                            {
                                "id": "abc",
                                "signal_ids": ["def"],
                                "target_id": "ghi",
                            }
                        ]
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "id": "def",
                        "content": [
                            {
                                "value": "https://abc/fallback_title",
                                "content_type": "URL",
                            }
                        ],
                    }
                )
            ),
            _make_response(json.dumps({})),
        ]

        with server.app.test_client() as client:
            response = client.get("/get_cases")

        self.assertEqual("fallback_title", response.json["data"][0]["title"])

    def test_fallback_title_content_type_not_url(self):
        self.mock_requests["get"].side_effect = [
            _make_response(
                json.dumps(
                    {
                        "data": [
                            {
                                "id": "abc",
                                "signal_ids": ["def"],
                                "target_id": "ghi",
                            }
                        ]
                    }
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "id": "def",
                        "content": [
                            {
                                "value": "https://abc/fallback_title",
                            }
                        ],
                    }
                )
            ),
            _make_response(json.dumps({})),
        ]

        with server.app.test_client() as client:
            response = client.get("/get_cases")
        self.assertEqual(
            "https://abc/fallback_title", response.json["data"][0]["title"]
        )

    def test_add_notes_returns_relevant_data(self):
        self.mock_requests["patch"].return_value = _make_response(
            json.dumps(
                {
                    "id": "abc",
                    "signal_ids": ["def"],
                    "target_id": "ghi",
                    "create_time": "2000-12-26T00:00:00",
                    "state": "ACTIVE",
                    "confidence": 0.5,
                    "severity": None,
                    "review_history": [],
                    "notes": "Hello World",
                }
            )
        )

        with server.app.test_client() as client:
            response = client.patch(
                "/add_notes", json={"case_id": "abc", "notes": "Hello World"}
            )

        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertIsNone(response.json)

    def test_add_notes_sends_correct_requests_to_cases_api(self):
        self.mock_requests["patch"].return_value = _make_response(
            json.dumps(
                {
                    "id": "abc",
                    "signal_ids": ["def"],
                    "target_id": "ghi",
                    "create_time": "2000-12-26T00:00:00",
                    "state": "ACTIVE",
                    "confidence": 0.5,
                    "severity": None,
                    "review_history": [],
                    "notes": "Hello World",
                }
            )
        )

        with server.app.test_client() as client:
            client.patch("/add_notes", json={"case_id": "abc", "notes": "Hello World"})

        self.mock_requests["patch"].assert_has_calls(
            [
                mock.call(
                    "http://signal-service:8082/cases/abc",
                    json={"notes": "Hello World"},
                    timeout=mock.ANY,
                )
            ]
        )

    @parameterized.parameters(
        ({"notes": "Hello World"}, "'case_id' is a required property"),
        ({"case_id": "abc"}, "'notes' is a required property"),
    )
    def test_add_notes_raises_bad_request_on_invalid_input(
        self, input_json, expected_error_description
    ):
        with server.app.test_client() as client:
            response = client.patch("/add_notes", json=input_json)

        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            {
                "code": 400,
                "description": expected_error_description,
                "name": "Bad Request",
            },
            response.json,
        )

    def test_upload_image(self):
        self.mock_requests["post"].side_effect = [
            _make_response(json.dumps({"id": "test_signal"})),
            _make_response(json.dumps({"id": "test_target"})),
            _make_response(json.dumps({"id": "test_case"})),
        ]

        with server.app.test_client() as client, mock.patch.object(
            PdqSignal, "hash_from_bytes"
        ) as fake_hash:
            fake_hash.return_value = "fake_pdq_digest"
            response = client.post(
                "/upload_image",
                json={
                    "name": "filename.jpg",
                    "image": "data:image;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==",  # pylint: disable=line-too-long
                },
            )

        self.mock_requests["post"].assert_has_calls(
            [
                mock.call(
                    "http://signal-service:8082/signals/",
                    json={
                        "content": {"value": "fake_pdq_digest", "type": "HASH_PDQ"},
                        "source": {"name": "USER_REPORT", "create_time": mock.ANY},
                    },
                    timeout=mock.ANY,
                ),
                mock.call(
                    "http://signal-service:8082/targets/",
                    json={
                        "title": "filename.jpg",
                        "content_bytes": "R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==",
                        "content_type": "IMAGE",
                    },
                    timeout=mock.ANY,
                ),
                mock.call(
                    "http://signal-service:8082/cases/",
                    json={"target_id": "test_target", "signal_ids": ["test_signal"]},
                    timeout=mock.ANY,
                ),
            ],
            any_order=True,
        )
        self.assertEqual(http.HTTPStatus.OK, response.status_code)
        self.assertIsNone(response.json)

    def test_get_importer_configs_converts_credentials_correctly(self):
        self.mock_requests["get"].side_effect = [
            _make_response(
                json.dumps(
                    {
                        "type": "TCAP_API",
                        "state": "ACTIVE",
                        "diagnostics_state": "ACTIVE",
                        "credential": {
                            "identifier": "foo",
                            "token": "bar",
                        },
                        "last_run_time": "2022-12-25T11:59:40.684882+00:00",
                        "total_import_count": 12,
                    },
                )
            ),
            _make_response(
                json.dumps(
                    {
                        "type": "THREAT_EXCHANGE_API",
                        "state": "INACTIVE",
                        "diagnostics_state": "INACTIVE",
                        "credential": {
                            "identifier": "foo1",
                            "token": "bar1",
                        },
                        "total_import_count": 0,
                    },
                )
            ),
        ]

        with server.app.test_client() as client:
            response = client.get("/get_importer_configs")

        self.assertEqual(
            {
                "tcap": {
                    "config": {
                        "enabled": True,
                        "diagnosticsEnabled": True,
                        "username": "foo",
                        "password": "bar",
                    },
                    "lastRunTime": "2022-12-25T11:59:40.684882+00:00",
                    "totalImportCount": 12,
                },
                "gifct": {
                    "config": {
                        "enabled": False,
                        "diagnosticsEnabled": False,
                        "privacyGroupId": "foo1",
                        "accessToken": "bar1",
                    },
                    "lastRunTime": None,
                    "totalImportCount": 0,
                },
            },
            response.json,
        )

    def test_update_importer_configs_sends_correct_requests_to_importers_api(self):
        with server.app.test_client() as client:
            client.post(
                "/update_importer_configs",
                json={
                    "tcap": {
                        "enabled": True,
                        "diagnosticsEnabled": True,
                        "username": "username1",
                        "password": "password1",
                    },
                    "gifct": {
                        "privacyGroupId": "",
                        "accessToken": "",
                    },
                },
            )

        self.mock_requests["post"].assert_called_once_with(
            "http://signal-service:8082/importers/",
            json={
                "type": "TCAP_API",
                "state": "ACTIVE",
                "diagnostics_state": "ACTIVE",
                "credential": {"identifier": "username1", "token": "password1"},
            },
            timeout=mock.ANY,
        )
        self.mock_requests["delete"].assert_called_once_with(
            "http://signal-service:8082/importers/THREAT_EXCHANGE_API", timeout=mock.ANY
        )

    def test_update_importer_configs_reraises_on_failed_credential_check(self):
        self.mock_requests["post"].return_value = _make_response(
            json.dumps(
                {
                    "error": {
                        "code": http.HTTPStatus.BAD_REQUEST,
                        "message": http.HTTPStatus.BAD_REQUEST.description,
                        "status": http.HTTPStatus.BAD_REQUEST.phrase,
                    }
                }
            ),
            http.HTTPStatus.BAD_REQUEST,
        )

        with server.app.test_client() as client:
            response = client.post(
                "/update_importer_configs",
                json={"tcap": {"username": "username1", "password": "password1"}},
            )

        self.assertEqual(http.HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            {
                "code": 400,
                "description": "Please check your tcap credentials.",
                "name": "Bad Request",
            },
            response.json,
        )


if __name__ == "__main__":
    absltest.main()
