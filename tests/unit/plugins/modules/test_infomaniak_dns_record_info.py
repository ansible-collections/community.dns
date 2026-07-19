# Copyright (c) 2026 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    patch,
)
from ansible_collections.community.internal_test_tools.tests.unit.utils.fetch_url_module_framework import (
    BaseTestModule,
    FetchUrlCall,
)

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils._http  # noqa: F401, pylint: disable=unused-import
from ansible_collections.community.dns.plugins.modules import infomaniak_dns_record_info

from .infomaniak import (
    get_infomaniak_json_pagination_meta,
    get_infomaniak_json_records,
)


def mock_sleep(delay):
    pass


class TestInfomaniakDNSRecordInfoJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = "ansible_collections.community.dns.plugins.modules.infomaniak_dns_record_info.AnsibleModule"
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = (
        "ansible_collections.community.dns.plugins.module_utils._http.fetch_url"
    )

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_info,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.org",
                "record": "example.org",
                "type": "A",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 404)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.org/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
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
            infomaniak_dns_record_info,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.org",
                "record": "example.org",
                "type": "A",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 401)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.org/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
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
            infomaniak_dns_record_info,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.org",
                "record": "example.org",
                "type": "A",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 500)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.org/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
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
            "https://api.infomaniak.com/2/zones/example.org/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1,"
            " but got HTTP status 500 (Internal Server Error)[something_went_wrong] Something went wrong."
        )

    def test_too_many_retries(self, mocker):
        sleep_values = [5, 10, 1, 1, 1, 60, 10, 1, 10, 3.1415]

        def sleep_check(delay):
            expected = sleep_values.pop(0)
            assert delay == expected

        with patch("time.sleep", sleep_check):
            result = self.run_module_failed(
                mocker,
                infomaniak_dns_record_info,
                {
                    "infomaniak_token": "foo",
                    "zone_name": "example.com",
                    "record": "example.com",
                    "type": "A",
                    "_ansible_remote_tmp": "/tmp/tmp",
                    "_ansible_keep_remote_files": True,
                },
                [
                    FetchUrlCall("GET", 429)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .return_header("Retry-After", "5")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .return_header("Retry-After", "10")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .return_header("Retry-After", "1")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .return_header("Retry-After", "0")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .return_header("Retry-After", "-1")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .return_header("Retry-After", "61")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .return_header("Retry-After", "foo")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .return_header("Retry-After", "0.9")
                    .result_str(""),
                    FetchUrlCall("GET", 429).result_str(""),
                    FetchUrlCall("GET", 429)
                    .return_header("Retry-After", "3.1415")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .return_header("Retry-After", "42")
                    .result_str(""),
                ],
            )
        print(sleep_values)
        assert (
            result["msg"]
            == "Error: Stopping after 10 failed retries with 429 Too Many Attempts"
        )
        assert len(sleep_values) == 0

    def test_conversion_error(self, mocker):
        with patch("time.sleep", mock_sleep):
            result = self.run_module_failed(
                mocker,
                infomaniak_dns_record_info,
                {
                    "infomaniak_token": "foo",
                    "zone_name": "example.com",
                    "record": "example.com",
                    "type": "TXT",
                    "txt_transformation": "unquoted",
                    "_ansible_remote_tmp": "/tmp/tmp",
                    "_ansible_keep_remote_files": True,
                },
                [
                    FetchUrlCall("GET", 200)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .result_json(
                        {
                            "result": "success",
                            "data": [
                                {
                                    "id": 201,
                                    "type": "TXT",
                                    "source": ".",
                                    "target": '"hellö\\',
                                    "ttl": 86400,
                                },
                            ],
                            **get_infomaniak_json_pagination_meta(1),
                        }
                    ),
                ],
            )

        assert result["msg"] == (
            "Error while converting DNS values: While processing record from API: Unexpected backslash at end of string"
        )

    def test_get_single(self, mocker):
        with patch("time.sleep", mock_sleep):
            result = self.run_module_success(
                mocker,
                infomaniak_dns_record_info,
                {
                    "infomaniak_token": "foo",
                    "zone_name": "example.com",
                    "record": "example.com",
                    "type": "A",
                    "_ansible_remote_tmp": "/tmp/tmp",
                    "_ansible_keep_remote_files": True,
                },
                [
                    FetchUrlCall("GET", 429)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .return_header("Retry-After", "5")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .return_header("Retry-After", "10")
                    .result_str(""),
                    FetchUrlCall("GET", 200)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .result_json(get_infomaniak_json_records(".", "A")),
                ],
            )
        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert len(result["records"]) == 1
        assert result["records"][0] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 3600,
            "type": "A",
            "value": "1.2.3.4",
            "extra": {},
        }

    def test_get_single_prefix(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_info,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "prefix": "*",
                "type": "A",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=%2A&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records("*", "A")),
            ],
        )
        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert len(result["records"]) == 1
        assert result["records"][0] == {
            "record": "*.example.com",
            "prefix": "*",
            "ttl": 3600,
            "type": "A",
            "value": "1.2.3.5",
            "extra": {},
        }

    def test_get_all_for_one_record(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_info,
            {
                "infomaniak_token": "foo",
                "what": "all_types_for_record",
                "zone_name": "example.com",
                "record": "*.example.com",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=%2A&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records("*")),
            ],
        )
        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert len(result["records"]) == 2
        assert result["records"][0] == {
            "record": "*.example.com",
            "prefix": "*",
            "ttl": 3600,
            "type": "A",
            "value": "1.2.3.5",
            "extra": {},
        }
        assert result["records"][1] == {
            "record": "*.example.com",
            "prefix": "*",
            "ttl": 3600,
            "type": "AAAA",
            "value": "2001:1:2::4",
            "extra": {},
        }

    def test_get_all_for_one_record_prefix(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_info,
            {
                "infomaniak_token": "foo",
                "what": "all_types_for_record",
                "zone_name": "example.com.",
                "prefix": ".",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".")),
            ],
        )
        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert len(result["records"]) == 6
        assert result["records"][0] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 3600,
            "type": "A",
            "value": "1.2.3.4",
            "extra": {},
        }
        assert result["records"][1] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 3600,
            "type": "AAAA",
            "value": "2001:1:2::3",
            "extra": {},
        }
        assert result["records"][2] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 3600,
            "type": "MX",
            "value": "10 example.com",
            "extra": {},
        }
        assert result["records"][3] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 86400,
            "type": "NS",
            "value": "ns1.infomaniak.ch",
            "extra": {},
        }
        assert result["records"][4] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 86400,
            "type": "NS",
            "value": "ns2.infomaniak.ch",
            "extra": {},
        }
        assert result["records"][5] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 86400,
            "type": "SOA",
            "value": "ns1.infomaniak.ch. hostmaster.infomaniak.ch. 2021070900 86400 10800 3600000 3600",
            "extra": {},
        }

    def test_get_all(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_info,
            {
                "infomaniak_token": "foobar",
                "what": "all_records",
                "zone_name": "example.com",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foobar")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records()),
            ],
        )
        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert len(result["records"]) == 9
        assert result["records"][0] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 3600,
            "type": "A",
            "value": "1.2.3.4",
            "extra": {},
        }
        assert result["records"][1] == {
            "record": "*.example.com",
            "prefix": "*",
            "ttl": 3600,
            "type": "A",
            "value": "1.2.3.5",
            "extra": {},
        }
        assert result["records"][2] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 3600,
            "type": "AAAA",
            "value": "2001:1:2::3",
            "extra": {},
        }
        assert result["records"][3] == {
            "record": "*.example.com",
            "prefix": "*",
            "ttl": 3600,
            "type": "AAAA",
            "value": "2001:1:2::4",
            "extra": {},
        }
        assert result["records"][4] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 3600,
            "type": "MX",
            "value": "10 example.com",
            "extra": {},
        }
        assert result["records"][5] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 86400,
            "type": "NS",
            "value": "ns1.infomaniak.ch",
            "extra": {},
        }
        assert result["records"][6] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 86400,
            "type": "NS",
            "value": "ns2.infomaniak.ch",
            "extra": {},
        }
        assert result["records"][7] == {
            "record": "example.com",
            "prefix": "",
            "ttl": 86400,
            "type": "SOA",
            "value": "ns1.infomaniak.ch. hostmaster.infomaniak.ch. 2021070900 86400 10800 3600000 3600",
            "extra": {},
        }
        assert result["records"][8] == {
            "record": "foo.example.com",
            "prefix": "foo",
            "type": "TXT",
            "ttl": 86400,
            "value": 'bär "with quotes" (use \\ to escape)',
            "extra": {},
        }

    def test_get_single_txt_api(self, mocker):
        with patch("time.sleep", mock_sleep):
            result = self.run_module_success(
                mocker,
                infomaniak_dns_record_info,
                {
                    "infomaniak_token": "foo",
                    "zone_name": "example.com",
                    "prefix": "foo",
                    "type": "TXT",
                    "txt_transformation": "api",
                    "_ansible_remote_tmp": "/tmp/tmp",
                    "_ansible_keep_remote_files": True,
                },
                [
                    FetchUrlCall("GET", 429)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .return_header("Retry-After", "5")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .return_header("Retry-After", "10")
                    .result_str(""),
                    FetchUrlCall("GET", 200)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .result_json(get_infomaniak_json_records("foo", "TXT")),
                ],
            )
        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert result["records"] == [
            {
                "record": "foo.example.com",
                "prefix": "foo",
                "ttl": 86400,
                "type": "TXT",
                "value": '"bär" " \\"with quotes\\"" " " "(use \\\\ to escape)"',
                "extra": {},
            }
        ]

    def test_get_single_txt_quoted(self, mocker):
        with patch("time.sleep", mock_sleep):
            result = self.run_module_success(
                mocker,
                infomaniak_dns_record_info,
                {
                    "infomaniak_token": "foo",
                    "zone_name": "example.com",
                    "prefix": "foo",
                    "type": "TXT",
                    "txt_transformation": "quoted",
                    "txt_character_encoding": "decimal",
                    "_ansible_remote_tmp": "/tmp/tmp",
                    "_ansible_keep_remote_files": True,
                },
                [
                    FetchUrlCall("GET", 429)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .return_header("Retry-After", "5")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .return_header("Retry-After", "10")
                    .result_str(""),
                    FetchUrlCall("GET", 200)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .result_json(get_infomaniak_json_records("foo", "TXT")),
                ],
            )
        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert result["records"] == [
            {
                "record": "foo.example.com",
                "prefix": "foo",
                "ttl": 86400,
                "type": "TXT",
                "value": '"b\\195\\164r \\"with quotes\\" (use \\\\ to escape)"',
                "extra": {},
            }
        ]

    def test_get_single_txt_quoted_octal(self, mocker):
        with patch("time.sleep", mock_sleep):
            result = self.run_module_success(
                mocker,
                infomaniak_dns_record_info,
                {
                    "infomaniak_token": "foo",
                    "zone_name": "example.com",
                    "prefix": "foo",
                    "type": "TXT",
                    "txt_transformation": "quoted",
                    "txt_character_encoding": "octal",
                    "_ansible_remote_tmp": "/tmp/tmp",
                    "_ansible_keep_remote_files": True,
                },
                [
                    FetchUrlCall("GET", 429)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .return_header("Retry-After", "5")
                    .result_str(""),
                    FetchUrlCall("GET", 429)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .return_header("Retry-After", "10")
                    .result_str(""),
                    FetchUrlCall("GET", 200)
                    .expect_header("accept", "application/json")
                    .expect_header("Authorization", "Bearer foo")
                    .expect_url(
                        "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                    )
                    .return_header("Content-Type", "application/json")
                    .result_json(get_infomaniak_json_records("foo", "TXT")),
                ],
            )
        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert result["records"] == [
            {
                "record": "foo.example.com",
                "prefix": "foo",
                "ttl": 86400,
                "type": "TXT",
                "value": '"b\\303\\244r \\"with quotes\\" (use \\\\ to escape)"',
                "extra": {},
            }
        ]
