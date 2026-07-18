# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# pylint: disable=use-implicit-booleaness-not-comparison

from __future__ import annotations

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    extract_warnings_texts,
)
from ansible_collections.community.internal_test_tools.tests.unit.utils.fetch_url_module_framework import (
    BaseTestModule,
    FetchUrlCall,
)

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils._http  # noqa: F401, pylint: disable=unused-import
from ansible_collections.community.dns.plugins.modules import infomaniak_dns_record_set

from .infomaniak import (
    INFOMANIAK_JSON_DEFAULT_ENTRIES,
    get_infomaniak_json_records,
)


class TestInfomaniakDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = "ansible_collections.community.dns.plugins.modules.infomaniak_dns_record_set.AnsibleModule"
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = (
        "ansible_collections.community.dns.plugins.module_utils._http.fetch_url"
    )

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.org",
                "record": "example.org",
                "type": "MX",
                "ttl": 3600,
                "value": [
                    "10 example.com",
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 404)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.org/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=MX&per_page=100&page=1"
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
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.org",
                "record": "example.org",
                "type": "MX",
                "ttl": 3600,
                "value": [
                    "10 example.com",
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 401)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.org/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=MX&per_page=100&page=1"
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

        assert result["msg"] == (
            "Cannot authenticate: Unauthorized: the authentication parameters are incorrect (HTTP status 401)"
        )

    def test_other_error(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.org",
                "record": "example.org",
                "type": "MX",
                "ttl": 3600,
                "value": [
                    "10 example.com",
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 500)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.org/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=MX&per_page=100&page=1"
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
            "https://api.infomaniak.com/2/zones/example.org/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=MX&per_page=100&page=1,"
            " but got HTTP status 500 (Internal Server Error)[something_went_wrong] Something went wrong."
        )

    def test_conversion_error(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "TXT",
                "ttl": 3600,
                "value": [
                    '"hellö',
                ],
                "txt_transformation": "quoted",
                "_ansible_diff": True,
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
                .result_json(get_infomaniak_json_records(".", "TXT")),
            ],
        )

        assert result["msg"] == (
            "Error while converting DNS values: While processing record from the user: Missing double quotation mark at the end of value"
        )

    def test_idempotency_present(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "MX",
                "ttl": 3600,
                "value": [
                    "10 example.com",
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
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=MX&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "MX")),
            ],
        )

        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert result["diff"]["before"] == {
            "record": "example.com",
            "prefix": "",
            "type": "MX",
            "ttl": 3600,
            "value": ["10 example.com"],
        }
        assert result["diff"]["before"] == result["diff"]["after"]

    def test_idempotency_absent_value(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "record": "*.example.com",
                "type": "A",
                "ttl": 3600,
                "value": [
                    "1.2.3.6",
                ],
                "on_existing": "keep",
                "_ansible_diff": True,
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
        assert result["diff"]["before"] == {
            "record": "*.example.com",
            "prefix": "*",
            "type": "A",
            "ttl": 3600,
            "value": ["1.2.3.5"],
        }
        assert result["diff"]["before"] == result["diff"]["after"]

    def test_idempotency_absent_value_prefix(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "prefix": "*",
                "type": "A",
                "ttl": 3600,
                "value": [
                    "1.2.3.6",
                ],
                "on_existing": "keep",
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

    def test_idempotency_absent_ttl(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "record": "*.example.com",
                "type": "A",
                "ttl": 1800,
                "value": [
                    "1.2.3.5",
                ],
                "on_existing": "keep",
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

    def test_idempotency_absent_type(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "CAA",
                "ttl": 3600,
                "value": [
                    '0 issue "letsencrypt.org"',
                ],
                "on_existing": "keep",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=CAA&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "CAA")),
            ],
        )

        assert result["changed"] is False
        assert result["zone_id"] == "example.com"

    def test_idempotency_absent_record(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com.",
                "record": "somewhere.example.com.",
                "type": "A",
                "ttl": 3600,
                "value": [
                    "1.2.3.6",
                ],
                "on_existing": "keep",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=somewhere&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records("somewhere", "A")),
            ],
        )

        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert (
            extract_warnings_texts(result) == []
        )  # pylint: disable=use-implicit-booleaness-not-comparison

    def test_idempotency_absent_record_warn(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com.",
                "record": "*.example.com.",
                "type": "A",
                "ttl": 3600,
                "value": [
                    "1.2.3.6",
                ],
                "on_existing": "keep_and_warn",
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
        assert extract_warnings_texts(result) == [
            "Record already exists with different value. Set on_existing=replace to remove it"
        ]

    def test_idempotency_absent_record_fail(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com.",
                "record": "*.example.com.",
                "type": "A",
                "ttl": 3600,
                "value": [
                    "1.2.3.6",
                ],
                "on_existing": "keep_and_fail",
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

        assert (
            result["msg"]
            == "Record already exists with different value. Set on_existing=replace to remove it"
        )

    def test_idempotency_absent_record_warn_bugfix(self, mocker):
        # Fixes a bug that caused the warning to trigger when it shouldn't
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com.",
                "record": "somewhere.example.com.",
                "type": "A",
                "ttl": 3600,
                "value": [
                    "1.2.3.6",
                ],
                "on_existing": "keep_and_warn",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=somewhere&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records("somewhere", "A")),
            ],
        )

        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert extract_warnings_texts(result) == []

    def test_idempotency_absent_record_fail_bugfix(self, mocker):
        # Fixes a bug that caused the failure to trigger when it shouldn't
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com.",
                "record": "somewhere.example.com.",
                "type": "A",
                "ttl": 3600,
                "value": [
                    "1.2.3.6",
                ],
                "on_existing": "keep_and_fail",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=somewhere&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records("somewhere", "A")),
            ],
        )

        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert extract_warnings_texts(result) == []

    def test_absent(self, mocker):
        record = INFOMANIAK_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "record": ((record["source"] + ".") if record["source"] != "." else "")
                + "example.com",
                "type": record["type"],
                "ttl": record["ttl"],
                "value": [
                    record["target"],
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "A")),
                FetchUrlCall("DELETE", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    f"https://api.infomaniak.com/2/zones/example.com/records/{record['id']}"
                )
                .return_header("Content-Type", "application/json")
                .result_json({"result": "success", "data": True}),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_absent_error(self, mocker):
        record = INFOMANIAK_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "record": ((record["source"] + ".") if record["source"] != "." else "")
                + "example.com",
                "type": record["type"],
                "ttl": record["ttl"],
                "value": [
                    record["target"],
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "A")),
                FetchUrlCall("DELETE", 500)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    f"https://api.infomaniak.com/2/zones/example.com/records/{record['id']}"
                )
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "error": {
                            "description": "Internal Server Error",
                            "code": "something",
                        }
                    }
                ),
            ],
        )

        print(result["msg"])
        assert result["msg"] == (
            "Error: Expected HTTP status 200, 404 for DELETE https://api.infomaniak.com/2/zones/example.com/records/1,"
            " but got HTTP status 500 (Internal Server Error)[something] Internal Server Error"
        )

    def test_absent_bulk(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "NS",
                "value": [],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=NS&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "NS")),
                FetchUrlCall("DELETE", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/6")
                .return_header("Content-Type", "application/json")
                .result_json({"result": "success", "data": True}),
                # Record 7 has been deleted between querying and we trying to delete it
                FetchUrlCall("DELETE", 404)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/7")
                .return_header("Content-Type", "application/json")
                # TODO: ???
                .result_json(
                    {
                        "error": {
                            "description": "record does not exist",
                            "code": "does_not_exist",
                        }
                    }
                ),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_absent_bulk_error(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "NS",
                "value": [],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=NS&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "NS")),
                FetchUrlCall("DELETE", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/6")
                .return_header("Content-Type", "application/json")
                .result_json({"result": "success", "data": True}),
                FetchUrlCall("DELETE", 500)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/7")
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "error": {
                            "description": "Internal Server Error",
                            "code": "something",
                        }
                    }
                ),
            ],
        )

        assert result["msg"] == (
            "Error: Expected HTTP status 200, 404 for DELETE https://api.infomaniak.com/2/zones/example.com/records/7,"
            " but got HTTP status 500 (Internal Server Error)[something] Internal Server Error"
        )

    def test_absent_other_value(self, mocker):
        record = INFOMANIAK_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "record": ((record["source"] + ".") if record["source"] != "." else "")
                + "example.com",
                "type": record["type"],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "A")),
                FetchUrlCall("DELETE", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    f"https://api.infomaniak.com/2/zones/example.com/records/{record['id']}"
                )
                .return_header("Content-Type", "application/json")
                .result_json({"result": "success", "data": True}),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "CAA",
                "ttl": 3600,
                "value": [
                    '0 issue "letsencrypt.org"',
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
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=CAA&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "CAA")),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_change_add_one_check_mode_prefix(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "prefix": ".",
                "type": "CAA",
                "ttl": 3600,
                "value": [
                    '0 issue "letsencrypt.org"',
                ],
                "_ansible_diff": True,
                "_ansible_check_mode": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=CAA&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "CAA")),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"
        assert "diff" in result
        assert "before" in result["diff"]
        assert "after" in result["diff"]
        assert result["diff"]["before"] == {}
        assert result["diff"]["after"] == {
            "prefix": "",
            "record": "example.com",
            "type": "CAA",
            "ttl": 3600,
            "value": ['0 issue "letsencrypt.org"'],
        }

    def test_change_add_one(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "CAA",
                "ttl": 3600,
                "value": [
                    '128 issue "letsencrypt.org xxx"',
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=CAA&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "CAA")),
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
                            "id": 133,
                            "type": "CAA",
                            "source": ".",
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
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "prefix": "",
                "type": "CAA",
                "ttl": 3600,
                "value": [
                    '128 issue "letsencrypt.org"',
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=CAA&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "CAA")),
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
                            "id": 133,
                            "type": "CAA",
                            "source": ".",
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
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "prefix": "☺",
                "type": "CAA",
                "ttl": 3600,
                "value": [
                    '128 issue "letsencrypt.org"',
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=xn--74h&filter%5Btypes%5D%5B%5D=CAA&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records("xn--74h", "CAA")),
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
                            "id": 133,
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

    def test_change_modify_list_fail(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "NS",
                "ttl": 86400,
                "value": [
                    "ns1.infomaniak.ch",
                ],
                "on_existing": "keep_and_fail",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=NS&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "NS")),
            ],
        )

        assert (
            result["msg"]
            == "Record already exists with different value. Set on_existing=replace to replace it"
        )

    def test_change_modify_list_warn(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "NS",
                "ttl": 10800,
                "value": [
                    "ns1.infomaniak.ch",
                ],
                "on_existing": "keep_and_warn",
                "_ansible_diff": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=NS&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "NS")),
            ],
        )

        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert "diff" in result
        assert "before" in result["diff"]
        assert "after" in result["diff"]
        assert result["diff"]["before"] == {
            "record": "example.com",
            "prefix": "",
            "type": "NS",
            "ttl": 86400,
            "value": [
                "ns1.infomaniak.ch",
                "ns2.infomaniak.ch",
            ],
        }
        assert result["diff"]["after"] == result["diff"]["before"]
        assert extract_warnings_texts(result) == [
            "Record already exists with different value. Set on_existing=replace to replace it"
        ]

    def test_change_modify_list_keep(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "NS",
                "ttl": 86400,
                "value": [
                    "ns1.infomaniak.ch",
                ],
                "on_existing": "keep",
                "_ansible_diff": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=NS&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "NS")),
            ],
        )

        assert (
            extract_warnings_texts(result) == []
        )  # pylint: disable=use-implicit-booleaness-not-comparison
        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert "diff" in result
        assert "before" in result["diff"]
        assert "after" in result["diff"]
        assert result["diff"]["before"] == {
            "record": "example.com",
            "prefix": "",
            "type": "NS",
            "ttl": 86400,
            "value": [
                "ns1.infomaniak.ch",
                "ns2.infomaniak.ch",
            ],
        }
        assert result["diff"]["after"] == result["diff"]["before"]

    def test_change_modify_list(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "NS",
                "ttl": 86400,
                "value": [
                    "ns3.infomaniak.ch",
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
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=NS&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "NS")),
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
                            "id": "132",
                            "type": "NS",
                            "source": ".",
                            "target": "ns3.infomaniak.ch",
                            "ttl": 86400,
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
            "record": "example.com",
            "prefix": "",
            "type": "NS",
            "ttl": 86400,
            "value": ["ns1.infomaniak.ch", "ns2.infomaniak.ch"],
        }
        assert result["diff"]["after"] == {
            "record": "example.com",
            "prefix": "",
            "type": "NS",
            "ttl": 86400,
            "value": ["ns3.infomaniak.ch"],
        }

    def test_change_modify_txt_unquoted(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "foo.example.com",
                "type": "TXT",
                "ttl": 86400,
                "value": ['bär "with quotes" (use \\ to escape)!'],
                "txt_transformation": "unquoted",
                "_ansible_diff": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records("foo", "TXT")),
                FetchUrlCall("PUT", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/9")
                .expect_json_value_absent(["id"])
                .expect_json_value_absent(["type"])
                .expect_json_value(["ttl"], 86400)
                .expect_json_value_absent(["source"])
                .expect_json_value(
                    ["target"], '"bär \\"with quotes\\" (use \\\\ to escape)!"'
                )
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "success",
                        "data": {
                            "id": 201,
                            "type": "TXT",
                            "source": "foo",
                            "target": '"bär \\"with quotes\\" (use \\\\ to escape)!"',
                            "ttl": 86400,
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
            "record": "foo.example.com",
            "prefix": "foo",
            "type": "TXT",
            "ttl": 86400,
            "value": ['bär "with quotes" (use \\ to escape)'],
        }
        assert result["diff"]["after"] == {
            "record": "foo.example.com",
            "prefix": "foo",
            "type": "TXT",
            "ttl": 86400,
            "value": ['bär "with quotes" (use \\ to escape)!'],
        }

    def test_change_modify_txt_quoted(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "foo.example.com",
                "type": "TXT",
                "ttl": 86400,
                "value": [r'"b\195\164r \"with quotes\" (use \\ to escape)!"'],
                "txt_transformation": "quoted",
                "txt_character_encoding": "decimal",
                "_ansible_diff": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records("foo", "TXT")),
                FetchUrlCall("PUT", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/9")
                .expect_json_value_absent(["id"])
                .expect_json_value_absent(["type"])
                .expect_json_value(["ttl"], 86400)
                .expect_json_value_absent(["source"])
                .expect_json_value(
                    ["target"], '"bär \\"with quotes\\" (use \\\\ to escape)!"'
                )
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "success",
                        "data": {
                            "id": 201,
                            "type": "TXT",
                            "source": "foo",
                            "target": '"bär \\"with quotes\\" (use \\\\ to escape)!"',
                            "ttl": 86400,
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
            "record": "foo.example.com",
            "prefix": "foo",
            "type": "TXT",
            "ttl": 86400,
            "value": [r'"b\195\164r \"with quotes\" (use \\ to escape)"'],
        }
        assert result["diff"]["after"] == {
            "record": "foo.example.com",
            "prefix": "foo",
            "type": "TXT",
            "ttl": 86400,
            "value": [r'"b\195\164r \"with quotes\" (use \\ to escape)!"'],
        }

    def test_change_modify_txt_quoted_octal(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "foo.example.com",
                "type": "TXT",
                "ttl": 86400,
                "value": [r'"b\303\244r \"with quotes\" (use \\ to escape)!"'],
                "txt_transformation": "quoted",
                "txt_character_encoding": "octal",
                "_ansible_diff": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records("foo", "TXT")),
                FetchUrlCall("PUT", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/9")
                .expect_json_value_absent(["id"])
                .expect_json_value_absent(["type"])
                .expect_json_value(["ttl"], 86400)
                .expect_json_value_absent(["source"])
                .expect_json_value(
                    ["target"], '"bär \\"with quotes\\" (use \\\\ to escape)!"'
                )
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "success",
                        "data": {
                            "id": 201,
                            "type": "TXT",
                            "source": "foo",
                            "target": '"bär \\"with quotes\\" (use \\\\ to escape)!"',
                            "ttl": 86400,
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
            "record": "foo.example.com",
            "prefix": "foo",
            "type": "TXT",
            "ttl": 86400,
            "value": [r'"b\303\244r \"with quotes\" (use \\ to escape)"'],
        }
        assert result["diff"]["after"] == {
            "record": "foo.example.com",
            "prefix": "foo",
            "type": "TXT",
            "ttl": 86400,
            "value": [r'"b\303\244r \"with quotes\" (use \\ to escape)!"'],
        }

    def test_change_modify_txt_api(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "foo.example.com",
                "type": "TXT",
                "ttl": 86400,
                "value": ['"bär \\"with quotes\\"" " " "(use \\\\ to escape)"'],
                "txt_transformation": "api",
                "_ansible_diff": True,
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=foo&filter%5Btypes%5D%5B%5D=TXT&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records("foo", "TXT")),
                FetchUrlCall("PUT", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/9")
                .expect_json_value_absent(["id"])
                .expect_json_value_absent(["type"])
                .expect_json_value(["ttl"], 86400)
                .expect_json_value_absent(["source"])
                .expect_json_value(
                    ["target"], '"bär \\"with quotes\\"" " " "(use \\\\ to escape)"'
                )
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "success",
                        "data": {
                            "id": 201,
                            "type": "TXT",
                            "source": "foo",
                            "target": '"bär \\"with quotes\\"" " " "(use \\\\ to escape)"',
                            "ttl": 86400,
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
            "record": "foo.example.com",
            "prefix": "foo",
            "type": "TXT",
            "ttl": 86400,
            "value": ['"bär" " \\"with quotes\\"" " " "(use \\\\ to escape)"'],
        }
        assert result["diff"]["after"] == {
            "record": "foo.example.com",
            "prefix": "foo",
            "type": "TXT",
            "ttl": 86400,
            "value": ['"bär \\"with quotes\\"" " " "(use \\\\ to escape)"'],
        }

    def test_change_modify_bulk_errors(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "NS",
                "ttl": 10800,
                "value": [
                    "a1",
                    "a2",
                    "a3",
                    "a4",
                    "a5",
                    "a6",
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=NS&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "NS")),
                FetchUrlCall("PUT", 500)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/7")
                .expect_json_value_absent(["id"])
                .expect_json_value_absent(["type"])
                .expect_json_value(["ttl"], 10800)
                .expect_json_value_absent(["source"])
                .expect_json_value(["target"], "a1")
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "error": {
                            "description": "Internal Server Error",
                            "code": "foobar",
                        }
                    }
                ),
            ],
        )

        assert result["msg"] == (
            "Error: Expected HTTP status 200 for PUT https://api.infomaniak.com/2/zones/example.com/records/7,"
            " but got HTTP status 500 (Internal Server Error)[foobar] Internal Server Error"
        )

    def test_change_change_bad(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record_set,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "A",
                "ttl": 3600,
                "value": [
                    "1.2.3.4.5",
                ],
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url(
                    "https://api.infomaniak.com/2/zones/example.com/records?filter%5Bsource%5D=.&filter%5Btypes%5D%5B%5D=A&per_page=100&page=1"
                )
                .return_header("Content-Type", "application/json")
                .result_json(get_infomaniak_json_records(".", "A")),
                FetchUrlCall("PUT", 422)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/1")
                .expect_json_value_absent(["id"])
                .expect_json_value_absent(["type"])
                .expect_json_value(["ttl"], 3600)
                .expect_json_value_absent(["source"])
                .expect_json_value(["target"], "1.2.3.4.5")
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "error": {
                            "description": "invalid A record",
                            "code": "meh",  # TODO?
                        },
                    }
                ),
            ],
        )

        assert result["msg"] == (
            "Error: Expected HTTP status 200 for PUT https://api.infomaniak.com/2/zones/example.com/records/1,"
            " but got HTTP status 422 (Unprocessable entity)[meh] invalid A record"
        )
