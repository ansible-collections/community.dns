# Copyright (c) 2026 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.community.internal_test_tools.tests.unit.utils.fetch_url_module_framework import (
    BaseTestModule,
    FetchUrlCall,
)

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils._http  # noqa: F401, pylint: disable=unused-import
from ansible_collections.community.dns.plugins.modules import infomaniak_dns_record_sets

from .infomaniak import get_infomaniak_json_records


class TestInfomaniakDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = "ansible_collections.community.dns.plugins.modules.infomaniak_dns_record_sets.AnsibleModule"
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = (
        "ansible_collections.community.dns.plugins.module_utils._http.fetch_url"
    )

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.org",
                "record_sets": [],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 404)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.org/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "error",
                        "error": {
                            "code": "zone_does_not_exists",
                            "description": "Zone does not exists: example.com",
                        },
                    }
                ),
            ],
        )

        assert result["msg"] == "Zone not found"

    def test_auth_error(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.org",
                "record_sets": [],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 401)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.org/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "error",
                        "error": {
                            "code": "not_authorized",
                            "description": "Not authorized.",
                        },
                    }
                ),
            ],
        )

        assert (
            result["msg"]
            == "Cannot authenticate: Unauthorized: the authentication parameters are incorrect (HTTP status 401)"
        )

    def test_other_error(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.org",
                "record_sets": [],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 500)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.org/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "error",
                        "error": {
                            "code": "something_went_wrong",
                            "description": "Something went wrong.",
                        },
                    }
                ),
            ],
        )

        assert result["msg"] == (
            "Error: Expected HTTP status 200, 404 for GET "
            "https://api.infomaniak.com/2/zones/example.org/records?per_page=100&page=1,"
            " but got HTTP status 500 (Internal Server Error)[something_went_wrong] Something went wrong."
        )

    def test_key_collision_error(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "record": "test.example.com",
                        "type": "A",
                        "ignore": True,
                    },
                    {
                        "prefix": "test",
                        "type": "A",
                        "value": ["1.2.3.4"],
                    },
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
            ],
        )

        assert (
            result["msg"]
            == "Found multiple sets for record test.example.com and type A: index #0 and #1"
        )

    def test_conversion_error(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "record": "example.com",
                        "type": "TXT",
                        "ttl": 3600,
                        "value": [
                            '"hellö',
                        ],
                    },
                ],
                "txt_transformation": "quoted",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
            ],
        )

        assert result["msg"] == (
            "Error while converting DNS values: While processing record from the user: Missing double quotation mark at the end of value"
        )

    def test_idempotency_empty(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
            ],
        )

        assert result["changed"] is False
        assert result["zone_id"] == "example.com"

    def test_idempotency_present(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "record": "example.com",
                        "type": "MX",
                        "ttl": 3600,
                        "value": [
                            "10 example.com",
                        ],
                    },
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
            ],
        )

        assert result["changed"] is False
        assert result["zone_id"] == "example.com"

    def test_removal_prune(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "prune": "true",
                "record_sets": [
                    {
                        "prefix": "*",
                        "ttl": 3600,
                        "type": "A",
                        "value": ["1.2.3.5"],
                    },
                    {
                        "prefix": "",
                        "ttl": 3600,
                        "type": "A",
                        "value": ["1.2.3.4"],
                    },
                    {
                        "prefix": ".",
                        "ttl": 3600,
                        "type": "AAAA",
                        "value": [],
                    },
                    {
                        "record": "example.com",
                        "type": "MX",
                        "ignore": True,
                    },
                    {
                        "record": "example.com",
                        "type": "NS",
                        "ignore": True,
                    },
                    {
                        "record": "example.com",
                        "type": "SOA",
                        "ignore": True,
                    },
                    {
                        "record": "foo.example.com",
                        "type": "TXT",
                        "ttl": 86400,
                        "value": ['bär "with quotes" (use \\ to escape)'],
                    },
                ],
                "_ansible_diff": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
                FetchUrlCall("DELETE", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/3")
                .return_header("Content-Type", "application/json")
                .result_json({"result": "success", "data": True}),
                FetchUrlCall("DELETE", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/4")
                .return_header("Content-Type", "application/json")
                .result_json({"result": "success", "data": True}),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"
        assert result["diff"]["before"] == {
            "record_sets": [
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.5"],
                },
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "AAAA",
                    "value": ["2001:1:2::4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "AAAA",
                    "value": ["2001:1:2::3"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "MX",
                    "value": ["10 example.com"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 86400,
                    "type": "NS",
                    "value": [
                        "ns1.infomaniak.ch",
                        "ns2.infomaniak.ch",
                    ],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 86400,
                    "type": "SOA",
                    "value": [
                        "ns1.infomaniak.ch. hostmaster.infomaniak.ch. 2021070900 86400 10800 3600000 3600"
                    ],
                },
                {
                    "record": "foo.example.com",
                    "prefix": "foo",
                    "ttl": 86400,
                    "type": "TXT",
                    "value": ['bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result["diff"]["after"] == {
            "record_sets": [
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.5"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "MX",
                    "value": ["10 example.com"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "type": "NS",
                    "ttl": 86400,
                    "value": [
                        "ns1.infomaniak.ch",
                        "ns2.infomaniak.ch",
                    ],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 86400,
                    "type": "SOA",
                    "value": [
                        "ns1.infomaniak.ch. hostmaster.infomaniak.ch. 2021070900 86400 10800 3600000 3600"
                    ],
                },
                {
                    "record": "foo.example.com",
                    "prefix": "foo",
                    "ttl": 86400,
                    "type": "TXT",
                    "value": ['bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "record": "example.com",
                        "type": "CAA",
                        "ttl": 3600,
                        "value": [
                            '0 issue "letsencrypt.org"',
                        ],
                    },
                ],
                "_ansible_check_mode": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_change_add_one_check_mode_prefix(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "prefix": "",
                        "type": "CAA",
                        "ttl": 3600,
                        "value": [
                            '0 issue "letsencrypt.org"',
                        ],
                    },
                ],
                "_ansible_check_mode": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_change_add_one(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "record": "example.com",
                        "type": "CAA",
                        "ttl": 3600,
                        "value": [
                            '128 issue "letsencrypt.org xxx"',
                        ],
                    },
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
                FetchUrlCall("POST", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records")
                .expect_json_value_absent(["id"])
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["source"], ".")
                .expect_json_value(["target"], '128 issue "letsencrypt.org xxx"')
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "success",
                        "data": {
                            "id": "133",
                            "type": "CAA",
                            "source": "@",
                            "target": '128 issue "letsencrypt.org xxx"',
                            "ttl": 3600,
                            "updated_at": 123456789,
                        },
                    }
                ),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_change_add_one_prefix(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "prefix": "",
                        "type": "CAA",
                        "ttl": 3600,
                        "value": [
                            '128 issue "letsencrypt.org"',
                        ],
                    },
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
                FetchUrlCall("POST", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records")
                .expect_json_value_absent(["id"])
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["source"], ".")
                .expect_json_value(["target"], '128 issue "letsencrypt.org"')
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "success",
                        "data": {
                            "id": "133",
                            "type": "CAA",
                            "source": "@",
                            "target": '128 issue "letsencrypt.org"',
                            "ttl": 3600,
                            "updated_at": 123456789,
                        },
                    }
                ),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_change_add_one_idn_prefix(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "prefix": "☺",
                        "type": "CAA",
                        "ttl": 3600,
                        "value": [
                            '128 issue "letsencrypt.org"',
                        ],
                    },
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
                FetchUrlCall("POST", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records")
                .expect_json_value_absent(["id"])
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["source"], "xn--74h")
                .expect_json_value(["target"], '128 issue "letsencrypt.org"')
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "success",
                        "data": {
                            "id": "133",
                            "type": "CAA",
                            "source": "xn--74h",
                            "target": '128 issue "letsencrypt.org"',
                            "ttl": 3600,
                            "updated_at": 123456789,
                        },
                    }
                ),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_change_add_one_failed(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "record": "example.com",
                        "type": "CAA",
                        "ttl": 3600,
                        "value": [
                            '128 issue "letsencrypt.org xxx"',
                        ],
                    },
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
                FetchUrlCall("POST", 500)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records")
                .expect_json_value_absent(["id"])
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["source"], ".")
                .expect_json_value(["target"], '128 issue "letsencrypt.org xxx"')
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "error": {
                            "code": "something",
                            "description": "Internal Server Error",
                        },
                    }
                ),
            ],
        )

        assert result["msg"] == (
            "Error: Expected HTTP status 200, 201 for POST https://api.infomaniak.com/2/zones/example.com/records,"
            " but got HTTP status 500 (Internal Server Error)[something] Internal Server Error"
        )

    def test_change_modify_list(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "record": "example.com",
                        "type": "NS",
                        "ttl": 86400,
                        "value": [
                            "ns3.infomaniak.ch",
                        ],
                    },
                ],
                "_ansible_diff": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
                FetchUrlCall("DELETE", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/6")
                .return_header("Content-Type", "application/json")
                .result_json({"result": "success", "data": True}),
                FetchUrlCall("PUT", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/7")
                .expect_json_value_absent(["id"])
                .expect_json_value_absent(["type"])
                .expect_json_value(["ttl"], 86400)
                .expect_json_value_absent(["source"])
                .expect_json_value(["target"], "ns3.infomaniak.ch")
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "success",
                        "data": {
                            "id": 131,
                            "type": "NS",
                            "source": ".",
                            "ttl": 86400,
                            "target": "ns3.infomaniak.ch",
                            "updated_at": 123456789,
                        },
                    }
                ),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"
        assert "diff" in result
        assert "before" in result["diff"]
        assert "after" in result["diff"]
        assert result["diff"]["before"] == {
            "record_sets": [
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.5"],
                },
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "AAAA",
                    "value": ["2001:1:2::4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "AAAA",
                    "value": ["2001:1:2::3"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "MX",
                    "value": ["10 example.com"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 86400,
                    "type": "NS",
                    "value": [
                        "ns1.infomaniak.ch",
                        "ns2.infomaniak.ch",
                    ],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 86400,
                    "type": "SOA",
                    "value": [
                        "ns1.infomaniak.ch. hostmaster.infomaniak.ch. 2021070900 86400 10800 3600000 3600"
                    ],
                },
                {
                    "record": "foo.example.com",
                    "prefix": "foo",
                    "ttl": 86400,
                    "type": "TXT",
                    "value": ['bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result["diff"]["after"] == {
            "record_sets": [
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.5"],
                },
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "AAAA",
                    "value": ["2001:1:2::4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "AAAA",
                    "value": ["2001:1:2::3"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "MX",
                    "value": ["10 example.com"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "type": "NS",
                    "ttl": 86400,
                    "value": ["ns3.infomaniak.ch"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 86400,
                    "type": "SOA",
                    "value": [
                        "ns1.infomaniak.ch. hostmaster.infomaniak.ch. 2021070900 86400 10800 3600000 3600"
                    ],
                },
                {
                    "record": "foo.example.com",
                    "prefix": "foo",
                    "ttl": 86400,
                    "type": "TXT",
                    "value": ['bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_change_modify_list_ttl(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_sets,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "record_sets": [
                    {
                        "record": "example.com",
                        "type": "NS",
                        "ttl": 3600,
                        "value": [
                            "ns3.infomaniak.ch",
                        ],
                    },
                ],
                "_ansible_diff": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
                FetchUrlCall("DELETE", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/6")
                .return_header("Content-Type", "application/json")
                .result_json({"result": "success", "data": True}),
                FetchUrlCall("PUT", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/7")
                .expect_json_value_absent(["id"])
                .expect_json_value_absent(["type"])
                .expect_json_value(["ttl"], 3600)
                .expect_json_value_absent(["source"])
                .expect_json_value(["target"], "ns3.infomaniak.ch")
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "success",
                        "data": {
                            "id": 130,
                            "type": "NS",
                            "source": "@",
                            "target": "ns3.infomaniak.ch",
                            "ttl": 3600,
                            "updated_at": 123456789,
                        },
                    }
                ),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"
        assert "diff" in result
        assert "before" in result["diff"]
        assert "after" in result["diff"]
        assert result["diff"]["before"] == {
            "record_sets": [
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.5"],
                },
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "AAAA",
                    "value": ["2001:1:2::4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "AAAA",
                    "value": ["2001:1:2::3"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "MX",
                    "value": ["10 example.com"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 86400,
                    "type": "NS",
                    "value": [
                        "ns1.infomaniak.ch",
                        "ns2.infomaniak.ch",
                    ],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 86400,
                    "type": "SOA",
                    "value": [
                        "ns1.infomaniak.ch. hostmaster.infomaniak.ch. 2021070900 86400 10800 3600000 3600"
                    ],
                },
                {
                    "record": "foo.example.com",
                    "prefix": "foo",
                    "ttl": 86400,
                    "type": "TXT",
                    "value": ['bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result["diff"]["after"] == {
            "record_sets": [
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.5"],
                },
                {
                    "record": "*.example.com",
                    "prefix": "*",
                    "ttl": 3600,
                    "type": "AAAA",
                    "value": ["2001:1:2::4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "A",
                    "value": ["1.2.3.4"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "AAAA",
                    "value": ["2001:1:2::3"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 3600,
                    "type": "MX",
                    "value": ["10 example.com"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "type": "NS",
                    "ttl": 3600,
                    "value": ["ns3.infomaniak.ch"],
                },
                {
                    "record": "example.com",
                    "prefix": "",
                    "ttl": 86400,
                    "type": "SOA",
                    "value": [
                        "ns1.infomaniak.ch. hostmaster.infomaniak.ch. 2021070900 86400 10800 3600000 3600"
                    ],
                },
                {
                    "record": "foo.example.com",
                    "prefix": "foo",
                    "ttl": 86400,
                    "type": "TXT",
                    "value": ['bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
