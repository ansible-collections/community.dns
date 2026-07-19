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
from ansible_collections.community.dns.plugins.modules import infomaniak_dns_record

from .infomaniak import (
    INFOMANIAK_JSON_DEFAULT_ENTRIES,
    get_infomaniak_json_records,
)


class TestInfomaniakDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = "ansible_collections.community.dns.plugins.modules.infomaniak_dns_record.AnsibleModule"
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = (
        "ansible_collections.community.dns.plugins.module_utils._http.fetch_url"
    )

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.org",
                "record": "example.org",
                "type": "MX",
                "ttl": 3600,
                "value": "10 example.com",
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
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.org",
                "record": "example.org",
                "type": "MX",
                "ttl": 3600,
                "value": "10 example.com",
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
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.org",
                "record": "example.org",
                "type": "MX",
                "ttl": 3600,
                "value": "10 example.com",
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
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "TXT",
                "ttl": 3600,
                "value": '"hellö',
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
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "MX",
                "ttl": 3600,
                "value": "10 example.com",
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
            "value": "10 example.com",
            "extra": {},
        }
        assert result["diff"]["before"] == result["diff"]["after"]

    def test_idempotency_absent_value(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "record": "*.example.com",
                "type": "A",
                "ttl": 3600,
                "value": "1.2.3.6",
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
        assert result["diff"]["before"] == {}
        assert result["diff"]["before"] == {}

    def test_idempotency_absent_value_prefix(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "prefix": "*",
                "type": "A",
                "ttl": 3600,
                "value": "1.2.3.6",
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
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "CAA",
                "ttl": 3600,
                "value": '0 issue "letsencrypt.org"',
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
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com.",
                "record": "somewhere.example.com.",
                "type": "A",
                "ttl": 3600,
                "value": "1.2.3.6",
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

    def test_absent_check(self, mocker):
        record = INFOMANIAK_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "record": ((record["source"] + ".") if record["source"] != "." else "")
                + "example.com",
                "type": record["type"],
                "value": record["target"],
                "_ansible_check_mode": True,
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
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_absent(self, mocker):
        record = INFOMANIAK_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "absent",
                "zone_name": "example.com",
                "record": ((record["source"] + ".") if record["source"] != "." else "")
                + "example.com",
                "type": record["type"],
                "value": record["target"],
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
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "CAA",
                "ttl": 3600,
                "value": '0 issue "letsencrypt.org"',
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
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "prefix": ".",
                "type": "CAA",
                "ttl": 3600,
                "value": '0 issue "letsencrypt.org"',
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
            "type": "CAA",
            "ttl": 3600,
            "record": "example.com",
            "value": '0 issue "letsencrypt.org"',
            "extra": {},
        }

    def test_change_add_one(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "example.com",
                "type": "CAA",
                "ttl": 3600,
                "value": '128 issue "letsencrypt.org xxx"',
                "_ansible_diff": True,
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
        assert "diff" in result
        assert "before" in result["diff"]
        assert "after" in result["diff"]
        assert result["diff"]["before"] == {}
        assert result["diff"]["after"] == {
            "prefix": "",
            "record": "example.com",
            "type": "CAA",
            "ttl": 3600,
            "value": '128 issue "letsencrypt.org xxx"',
            "extra": {},
        }

    def test_change_add_one_prefix(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "prefix": "",
                "type": "CAA",
                "ttl": 3600,
                "value": '128 issue "letsencrypt.org"',
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
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "prefix": "☺",
                "type": "CAA",
                "ttl": 3600,
                "value": '128 issue "letsencrypt.org"',
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

    def test_modify_check(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "*.example.com",
                "type": "A",
                "ttl": 300,
                "value": "1.2.3.5",
                "_ansible_check_mode": True,
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

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_modify(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "*.example.com",
                "type": "A",
                "ttl": 300,
                "value": "1.2.3.5",
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
                FetchUrlCall("PUT", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records/2")
                .expect_json_value_absent(["id"])
                .expect_json_value_absent(["type"])
                .expect_json_value(["ttl"], 300)
                .expect_json_value_absent(["source"])
                .expect_json_value(["target"], "1.2.3.5")
                .return_header("Content-Type", "application/json")
                .result_json(
                    {
                        "result": "success",
                        "data": {
                            "id": 126,
                            "type": "A",
                            "source": "*",
                            "target": "1.2.3.5",
                            "ttl": 300,
                            "updated_at": 123456789,
                        },
                    }
                ),
            ],
        )

        assert result["changed"] is True
        assert result["zone_id"] == "example.com"

    def test_create_bad(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_record,
            {
                "infomaniak_token": "foo",
                "state": "present",
                "zone_name": "example.com",
                "record": "*.example.com",
                "type": "A",
                "ttl": 300,
                "value": "1.2.3.5.6",
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
                FetchUrlCall("POST", 422)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com/records")
                .expect_json_value_absent(["id"])
                .expect_json_value(["type"], "A")
                .expect_json_value(["ttl"], 300)
                .expect_json_value(["source"], "*")
                .expect_json_value(["target"], "1.2.3.5.6")
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
            "Error: Expected HTTP status 200, 201 for POST https://api.infomaniak.com/2/zones/example.com/records,"
            " but got HTTP status 422 (Unprocessable entity)[meh] invalid A record"
        )
