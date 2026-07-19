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
from ansible_collections.community.dns.plugins.modules import infomaniak_dns_zone_info

from .infomaniak import INFOMANIAK_ZONE_JSON


class TestInfomaniakDNSZoneInfoJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = "ansible_collections.community.dns.plugins.modules.infomaniak_dns_zone_info.AnsibleModule"
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = (
        "ansible_collections.community.dns.plugins.module_utils._http.fetch_url"
    )

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(
            mocker,
            infomaniak_dns_zone_info,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.org",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 404)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.org")
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
            infomaniak_dns_zone_info,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.org",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 401)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.org")
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
            infomaniak_dns_zone_info,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.org",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 500)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.org")
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
            "Error: Expected HTTP status 200, 404 for GET https://api.infomaniak.com/2/zones/example.org,"
            " but got HTTP status 500 (Internal Server Error)[something_went_wrong] Something went wrong."
        )

    def test_get(self, mocker):
        result = self.run_module_success(
            mocker,
            infomaniak_dns_zone_info,
            {
                "infomaniak_token": "foo",
                "zone_name": "example.com",
                "_ansible_remote_tmp": "/tmp/tmp",
                "_ansible_keep_remote_files": True,
            },
            [
                FetchUrlCall("GET", 200)
                .expect_header("accept", "application/json")
                .expect_header("Authorization", "Bearer foo")
                .expect_url("https://api.infomaniak.com/2/zones/example.com")
                .return_header("Content-Type", "application/json")
                .result_json(INFOMANIAK_ZONE_JSON),
            ],
        )
        assert result["changed"] is False
        assert result["zone_id"] == "example.com"
        assert result["zone_name"] == "example.com"
        assert result["zone_info"] == {
            "dnssec": {
                "is_enabled": True,
            },
            "id": 42,
            "nameservers": [
                "ns1.infomaniak.ch",
                "ns2.infomaniak.ch",
            ],
        }
