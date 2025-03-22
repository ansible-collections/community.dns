# Copyright (c), Felix Fontein <felix@fontein.de>, 2021
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import textwrap
import typing as t

from ansible import constants as C
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.community.internal_test_tools.tests.unit.mock.loader import (
    DictDataLoader,
)
from ansible_collections.community.internal_test_tools.tests.unit.mock.path import (
    mock_unfrackpath_noop,
)
from ansible_collections.community.internal_test_tools.tests.unit.utils.open_url_framework import (
    OpenUrlCall,
    OpenUrlProxy,
)
from ansible_collections.community.internal_test_tools.tests.unit.utils.trust import (
    is_trusted,
)


HETZNER_DEFAULT_ZONE = {
    "id": "42",
    "created": "2021-07-09T11:18:37Z",
    "modified": "2021-07-09T11:18:37Z",
    "legacy_dns_host": "string",
    "legacy_ns": ["string"],
    "name": "example.com",
    "ns": ["string"],
    "owner": "Example",
    "paused": True,
    "permission": "string",
    "project": "string",
    "registrar": "string",
    "status": "verified",
    "ttl": 10800,
    "verified": "2021-07-09T11:18:37Z",
    "records_count": 0,
    "is_secondary_dns": True,
    "txt_verification": {
        "name": "string",
        "token": "string",
    },
}

HETZNER_JSON_DEFAULT_ENTRIES = [
    {
        "id": "125",
        "type": "A",
        "name": "@",
        "value": "1.2.3.4",
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
    {
        "id": "126",
        "type": "A",
        "name": "*",
        "value": "1.2.3.5",
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
    {
        "id": "127",
        "type": "AAAA",
        "name": "@",
        "value": "2001:1:2::3",
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
    {
        "id": "128",
        "type": "AAAA",
        "name": "foo",
        "value": "2001:1:2::4",
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
    {
        "id": "129",
        "type": "MX",
        "name": "@",
        "value": "10 example.com",
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
    {
        "id": "130",
        "type": "CNAME",
        "name": "bar",
        "value": "example.org.",
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
]

HETZNER_JSON_DEFAULT_ENTRIES_UNSAFE = [
    {
        "id": "125",
        "type": "A",
        "name": "@",
        "value": "1.2.{3.4",
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
    {
        "id": "126",
        "type": "A",
        "name": "*",
        "value": "1.2.{3.5",
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
    {
        "id": "127",
        "type": "AAAA",
        "name": "@",
        "value": "2001:1:2::{3",
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
    {
        "id": "128",
        "type": "AAAA",
        "name": "foo",
        "value": "2001:1:2::{4",
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
    {
        "id": "129",
        "type": "MX",
        "name": "@",
        "value": "10 example.com",
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
    {
        "id": "130",
        "type": "CNAME",
        "name": "bar",
        "value": "example.org.",
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
]

HETZNER_JSON_BAD_ENTRIES = [
    {
        "id": "125",
        "type": "TXT",
        "name": "@",
        "value": '"this is wrongly quoted',
        "ttl": 3600,
        "zone_id": "42",
        "created": "2021-07-09T11:18:37Z",
        "modified": "2021-07-09T11:18:37Z",
    },
]

HETZNER_JSON_ZONE_LIST_RESULT = {
    "zones": [
        HETZNER_DEFAULT_ZONE,
    ],
}

HETZNER_JSON_ZONE_GET_RESULT = {
    "zone": HETZNER_DEFAULT_ZONE,
}

HETZNER_JSON_ZONE_RECORDS_GET_RESULT = {
    "records": HETZNER_JSON_DEFAULT_ENTRIES,
}

HETZNER_JSON_ZONE_RECORDS_GET_RESULT_UNSAFE = {
    "records": HETZNER_JSON_DEFAULT_ENTRIES_UNSAFE,
}

HETZNER_JSON_ZONE_RECORDS_GET_RESULT_2 = {
    "records": HETZNER_JSON_BAD_ENTRIES,
}


original_exists = os.path.exists
original_access = os.access


def exists_mock(
    path: os.PathLike | str, exists: bool = True
) -> t.Callable[[os.PathLike | str], bool]:
    def exists_fn(f: os.PathLike | str) -> bool:
        if to_native(f) == path:
            return exists
        return original_exists(f)

    return exists_fn


def access_mock(path: os.PathLike | str, can_access: bool = True):
    def access(f: os.PathLike | str, m: t.Any, *args, **kwargs) -> bool:
        if to_native(f) == path:
            return can_access
        return original_access(f, m, *args, **kwargs)  # pragma: no cover

    return access


def test_inventory_file_simple(mocker) -> None:
    inventory_filename = "test.hetzner_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]
    inventory_file = {
        inventory_filename: textwrap.dedent(
            """\
    ---
    plugin: community.dns.hetzner_dns_records
    hetzner_token: foo
    zone_name: example.com
    simple_filters:
      type: A
    """
        )
    }

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/zones", without_query=True)
            .expect_query_values("name", "example.com")
            .return_header("Content-Type", "application/json")
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/records", without_query=True)
            .expect_query_values("zone_id", "42")
            .expect_query_values("page", "1")
            .expect_query_values("per_page", "100")
            .return_header("Content-Type", "application/json")
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT_UNSAFE),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename))
    mocker.patch("os.access", access_mock(inventory_filename))
    im = InventoryManager(
        loader=DictDataLoader(inventory_file), sources=inventory_filename
    )

    open_url.assert_is_done()

    assert im._inventory.hosts
    assert "example.com" in im._inventory.hosts
    assert "*.example.com" in im._inventory.hosts
    assert "foo.example.com" not in im._inventory.hosts
    assert "bar.example.com" not in im._inventory.hosts
    assert (
        im._inventory.get_host("example.com") in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("*.example.com")
        in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("example.com").get_vars()["ansible_host"] == "1.2.{3.4"
    )
    assert (
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"] == "1.2.{3.5"
    )
    assert not is_trusted(
        im._inventory.get_host("example.com").get_vars()["ansible_host"]
    )
    assert not is_trusted(
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"]
    )
    assert len(im._inventory.groups["ungrouped"].hosts) == 2
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_simple_2(mocker) -> None:
    inventory_filename = "test.hetzner_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]
    inventory_file = {
        inventory_filename: textwrap.dedent(
            """\
    ---
    plugin: community.dns.hetzner_dns_records
    hetzner_token: foo
    zone_name: example.com
    filters:
      - include: ansible_host == '1.2.{3.4'
      - include: ansible_host == '1.2.{3.5'
      - exclude: true
    """
        )
    }

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/zones", without_query=True)
            .expect_query_values("name", "example.com")
            .return_header("Content-Type", "application/json")
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/records", without_query=True)
            .expect_query_values("zone_id", "42")
            .expect_query_values("page", "1")
            .expect_query_values("per_page", "100")
            .return_header("Content-Type", "application/json")
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT_UNSAFE),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename))
    mocker.patch("os.access", access_mock(inventory_filename))
    im = InventoryManager(
        loader=DictDataLoader(inventory_file), sources=inventory_filename
    )

    open_url.assert_is_done()

    assert im._inventory.hosts
    assert "example.com" in im._inventory.hosts
    assert "*.example.com" in im._inventory.hosts
    assert "foo.example.com" not in im._inventory.hosts
    assert "bar.example.com" not in im._inventory.hosts
    assert (
        im._inventory.get_host("example.com") in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("*.example.com")
        in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("example.com").get_vars()["ansible_host"] == "1.2.{3.4"
    )
    assert (
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"] == "1.2.{3.5"
    )
    assert not is_trusted(
        im._inventory.get_host("example.com").get_vars()["ansible_host"]
    )
    assert not is_trusted(
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"]
    )
    assert len(im._inventory.groups["ungrouped"].hosts) == 2
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_collision(mocker) -> None:
    inventory_filename = "test.hetzner_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]
    inventory_file = {
        inventory_filename: textwrap.dedent(
            """\
    ---
    plugin: community.dns.hetzner_dns_records
    hetzner_token: '{{ "foo" }}'
    zone_name: '{{ "example." ~ "com" }}'
    simple_filters:
      type:
        - A
        - AAAA
    """
        )
    }

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/zones", without_query=True)
            .expect_query_values("name", "example.com")
            .return_header("Content-Type", "application/json")
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/records", without_query=True)
            .expect_query_values("zone_id", "42")
            .expect_query_values("page", "1")
            .expect_query_values("per_page", "100")
            .return_header("Content-Type", "application/json")
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename))
    mocker.patch("os.access", access_mock(inventory_filename))
    im = InventoryManager(
        loader=DictDataLoader(inventory_file), sources=inventory_filename
    )

    open_url.assert_is_done()

    assert im._inventory.hosts
    assert "example.com" in im._inventory.hosts
    assert "*.example.com" in im._inventory.hosts
    assert "foo.example.com" in im._inventory.hosts
    assert "bar.example.com" not in im._inventory.hosts
    assert (
        im._inventory.get_host("example.com") in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("*.example.com")
        in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("foo.example.com")
        in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("example.com").get_vars()["ansible_host"]
        == "2001:1:2::3"
    )
    assert (
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"] == "1.2.3.5"
    )
    assert (
        im._inventory.get_host("foo.example.com").get_vars()["ansible_host"]
        == "2001:1:2::4"
    )
    assert len(im._inventory.groups["ungrouped"].hosts) == 3
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_no_filter(mocker) -> None:
    inventory_filename = "test.hetzner_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]
    inventory_file = {
        inventory_filename: textwrap.dedent(
            """\
    ---
    plugin: community.dns.hetzner_dns_records
    hetzner_token: foo
    zone_id: '42'
    """
        )
    }

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/zones/42")
            .return_header("Content-Type", "application/json")
            .result_json(HETZNER_JSON_ZONE_GET_RESULT),
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/records", without_query=True)
            .expect_query_values("zone_id", "42")
            .expect_query_values("page", "1")
            .expect_query_values("per_page", "100")
            .return_header("Content-Type", "application/json")
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename))
    mocker.patch("os.access", access_mock(inventory_filename))
    im = InventoryManager(
        loader=DictDataLoader(inventory_file), sources=inventory_filename
    )

    open_url.assert_is_done()

    assert im._inventory.hosts
    assert "example.com" in im._inventory.hosts
    assert "*.example.com" in im._inventory.hosts
    assert "foo.example.com" in im._inventory.hosts
    assert "bar.example.com" in im._inventory.hosts
    assert (
        im._inventory.get_host("example.com") in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("*.example.com")
        in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("foo.example.com")
        in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("bar.example.com")
        in im._inventory.groups["ungrouped"].hosts
    )
    assert (
        im._inventory.get_host("example.com").get_vars()["ansible_host"]
        == "2001:1:2::3"
    )
    assert (
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"] == "1.2.3.5"
    )
    assert (
        im._inventory.get_host("foo.example.com").get_vars()["ansible_host"]
        == "2001:1:2::4"
    )
    assert (
        im._inventory.get_host("bar.example.com").get_vars()["ansible_host"]
        == "example.org."
    )
    assert len(im._inventory.groups["ungrouped"].hosts) == 4
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_record_conversion_error(mocker) -> None:
    inventory_filename = "test.hetzner_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]
    inventory_file = {
        inventory_filename: textwrap.dedent(
            """\
    ---
    plugin: community.dns.hetzner_dns_records
    hetzner_token: foo
    zone_id: "{{ '42' }}"
    """
        )
    }

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/zones/42")
            .return_header("Content-Type", "application/json")
            .result_json(HETZNER_JSON_ZONE_GET_RESULT),
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/records", without_query=True)
            .expect_query_values("zone_id", "42")
            .expect_query_values("page", "1")
            .expect_query_values("per_page", "100")
            .return_header("Content-Type", "application/json")
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT_2),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename))
    mocker.patch("os.access", access_mock(inventory_filename))
    im = InventoryManager(
        loader=DictDataLoader(inventory_file), sources=inventory_filename
    )

    open_url.assert_is_done()

    # TODO: make sure that the correct error was reported

    assert not im._inventory.hosts
    assert len(im._inventory.groups["ungrouped"].hosts) == 0
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_missing_zone(mocker) -> None:
    inventory_filename = "test.hetzner_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]
    inventory_file = {
        inventory_filename: textwrap.dedent(
            """\
    ---
    plugin: community.dns.hetzner_dns_records
    hetzner_token: foo
    """
        )
    }

    open_url = OpenUrlProxy([])
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename))
    mocker.patch("os.access", access_mock(inventory_filename))
    im = InventoryManager(
        loader=DictDataLoader(inventory_file), sources=inventory_filename
    )

    open_url.assert_is_done()

    # TODO: make sure that the correct error was reported

    assert not im._inventory.hosts
    assert len(im._inventory.groups["ungrouped"].hosts) == 0
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_zone_not_found(mocker) -> None:
    inventory_filename = "test.hetzner_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]
    inventory_file = {
        inventory_filename: textwrap.dedent(
            """\
    ---
    plugin: community.dns.hetzner_dns_records
    hetzner_token: foo
    zone_id: '23'
    """
        )
    }

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 404)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/zones/23")
            .return_header("Content-Type", "application/json")
            .result_json({"message": ""}),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename))
    mocker.patch("os.access", access_mock(inventory_filename))
    im = InventoryManager(
        loader=DictDataLoader(inventory_file), sources=inventory_filename
    )

    open_url.assert_is_done()

    # TODO: make sure that the correct error was reported

    assert not im._inventory.hosts
    assert len(im._inventory.groups["ungrouped"].hosts) == 0
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_unauthorized(mocker) -> None:
    inventory_filename = "test.hetzner_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]
    inventory_file = {
        inventory_filename: textwrap.dedent(
            """\
    ---
    plugin: community.dns.hetzner_dns_records
    hetzner_token: foo
    zone_id: '23'
    """
        )
    }

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 403)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/zones/23")
            .result_json({"message": ""}),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename))
    mocker.patch("os.access", access_mock(inventory_filename))
    im = InventoryManager(
        loader=DictDataLoader(inventory_file), sources=inventory_filename
    )

    open_url.assert_is_done()

    # TODO: make sure that the correct error was reported

    assert not im._inventory.hosts
    assert len(im._inventory.groups["ungrouped"].hosts) == 0
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_error(mocker) -> None:
    inventory_filename = "test.hetzner_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]
    inventory_file = {
        inventory_filename: textwrap.dedent(
            """\
    ---
    plugin: community.dns.hetzner_dns_records
    hetzner_token: foo
    zone_id: '42'
    """
        )
    }

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 500)
            .expect_header("accept", "application/json")
            .expect_header("auth-api-token", "foo")
            .expect_url("https://dns.hetzner.com/api/v1/zones/42")
            .result_json({}),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename))
    mocker.patch("os.access", access_mock(inventory_filename))
    im = InventoryManager(
        loader=DictDataLoader(inventory_file), sources=inventory_filename
    )

    open_url.assert_is_done()

    # TODO: make sure that the correct error was reported

    assert not im._inventory.hosts
    assert len(im._inventory.groups["ungrouped"].hosts) == 0
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_wrong_file(mocker) -> None:
    inventory_filename = "test.hetznerdns.yml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]
    inventory_file = {
        inventory_filename: textwrap.dedent(
            """\
    ---
    plugin: community.dns.hetzner_dns_records
    hetzner_token: foo
    """
        )
    }

    open_url = OpenUrlProxy([])
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename))
    mocker.patch("os.access", access_mock(inventory_filename))
    im = InventoryManager(
        loader=DictDataLoader(inventory_file), sources=inventory_filename
    )

    open_url.assert_is_done()

    # TODO: make sure that the correct error was reported

    assert not im._inventory.hosts
    assert len(im._inventory.groups["ungrouped"].hosts) == 0
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_no_file(mocker) -> None:
    inventory_filename = "test.hetzner_dns.yml"
    C.INVENTORY_ENABLED = ["community.dns.hetzner_dns_records"]

    open_url = OpenUrlProxy([])
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    mocker.patch("ansible.inventory.manager.unfrackpath", mock_unfrackpath_noop)
    mocker.patch("os.path.exists", exists_mock(inventory_filename, False))
    mocker.patch("os.access", access_mock(inventory_filename, False))
    im = InventoryManager(loader=DictDataLoader({}), sources=inventory_filename)

    open_url.assert_is_done()

    # TODO: make sure that the correct error was reported

    assert not im._inventory.hosts
    assert len(im._inventory.groups["ungrouped"].hosts) == 0
    assert len(im._inventory.groups["all"].hosts) == 0
