# Copyright (c), Felix Fontein <felix@fontein.de>, 2021
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import textwrap
import typing as t
from collections.abc import Callable

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

from ..modules.infomaniak import (
    INFOMANIAK_ZONE_JSON,
    with_records,
)

INFOMANIAK_JSON_ZONE_RECORDS_GET_RESULT = [
    {
        "id": 1,
        "type": "A",
        "source": ".",
        "target": "1.2.3.4",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 2,
        "type": "A",
        "source": "*",
        "target": "1.2.3.5",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 3,
        "type": "AAAA",
        "source": ".",
        "target": "2001:1:2::3",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 4,
        "type": "AAAA",
        "source": "foo",
        "target": "2001:1:2::4",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 5,
        "type": "MX",
        "source": ".",
        "target": "10 example.com",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 6,
        "type": "CNAME",
        "source": "bar",
        "target": "example.org.",
        "ttl": 86400,
        "updated_at": 12345678,
    },
]

INFOMANIAK_JSON_ZONE_RECORDS_GET_RESULT_UNSAFE = [
    {
        "id": 7,
        "type": "A",
        "source": ".",
        "target": "1.2.{3.4",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 8,
        "type": "A",
        "source": "*",
        "target": "1.2.{3.5",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 9,
        "type": "AAAA",
        "source": ".",
        "target": "2001:1:2::{3",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 10,
        "type": "AAAA",
        "source": "foo",
        "target": "2001:1:2::{4",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 11,
        "type": "MX",
        "source": ".",
        "target": "10 example.com",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 12,
        "type": "CNAME",
        "source": "bar",
        "target": "example.org.",
        "ttl": 86400,
        "updated_at": 12345678,
    },
]

INFOMANIAK_JSON_ZONE_RECORDS_GET_RESULT_2 = [
    {
        "id": 1,
        "type": "TXT",
        "source": ".",
        "target": '"this is wrongly quoted',
        "ttl": 3600,
        "updated_at": 12345678,
    },
]


original_exists = os.path.exists
original_access = os.access


def exists_mock(
    path: os.PathLike | str, exists: bool = True
) -> Callable[[os.PathLike | str], bool]:
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


def test_inventory_wrong_file(mocker) -> None:
    inventory_filename = "test.infomaniakdns.yml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.infomaniak_dns_records
    infomaniak_token: foo
    """)}

    open_url = OpenUrlProxy([])
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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
    inventory_filename = "test.infomaniak_dns.yml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore

    open_url = OpenUrlProxy([])
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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


def test_inventory_file_simple(mocker) -> None:
    inventory_filename = "test.infomaniak_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.infomaniak_dns_records
    infomaniak_token: foo
    zone_name: example.com
    simple_filters:
      type: A
    """)}

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("Authorization", "Bearer foo")
            .expect_url("https://api.infomaniak.com/2/zones/example.com?with=records")
            .return_header("Content-Type", "application/json")
            .result_json(
                with_records(
                    INFOMANIAK_ZONE_JSON, INFOMANIAK_JSON_ZONE_RECORDS_GET_RESULT_UNSAFE
                )
            ),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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
        im._inventory.get_host("example.com").get_vars()["ansible_host"] == "1.2.{3.4"  # type: ignore[union-attr]
    )
    assert (
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"] == "1.2.{3.5"  # type: ignore[union-attr]
    )
    assert not is_trusted(
        im._inventory.get_host("example.com").get_vars()["ansible_host"]  # type: ignore[union-attr]
    )
    assert not is_trusted(
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"]  # type: ignore[union-attr]
    )
    assert len(im._inventory.groups["ungrouped"].hosts) == 2
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_simple_2(mocker) -> None:
    inventory_filename = "test.infomaniak_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.infomaniak_dns_records
    infomaniak_token: foo
    zone_name: example.com
    filters:
      - include: ansible_host == '1.2.{3.4'
      - include: ansible_host == '1.2.{3.5'
      - exclude: true
    """)}

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("Authorization", "Bearer foo")
            .expect_url("https://api.infomaniak.com/2/zones/example.com?with=records")
            .return_header("Content-Type", "application/json")
            .result_json(
                with_records(
                    INFOMANIAK_ZONE_JSON, INFOMANIAK_JSON_ZONE_RECORDS_GET_RESULT_UNSAFE
                )
            ),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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
        im._inventory.get_host("example.com").get_vars()["ansible_host"] == "1.2.{3.4"  # type: ignore[union-attr]
    )
    assert (
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"] == "1.2.{3.5"  # type: ignore[union-attr]
    )
    assert not is_trusted(
        im._inventory.get_host("example.com").get_vars()["ansible_host"]  # type: ignore[union-attr]
    )
    assert not is_trusted(
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"]  # type: ignore[union-attr]
    )
    assert len(im._inventory.groups["ungrouped"].hosts) == 2
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_collision(mocker) -> None:
    inventory_filename = "test.infomaniak_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.infomaniak_dns_records
    infomaniak_token: '{{ "foo" }}'
    zone_name: '{{ "example." ~ "com" }}'
    simple_filters:
      type:
        - A
        - AAAA
    """)}

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("Authorization", "Bearer foo")
            .expect_url("https://api.infomaniak.com/2/zones/example.com?with=records")
            .return_header("Content-Type", "application/json")
            .result_json(
                with_records(
                    INFOMANIAK_ZONE_JSON, INFOMANIAK_JSON_ZONE_RECORDS_GET_RESULT
                )
            ),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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
        im._inventory.get_host("example.com").get_vars()["ansible_host"]  # type: ignore[union-attr]
        == "2001:1:2::3"
    )
    assert (
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"] == "1.2.3.5"  # type: ignore[union-attr]
    )
    assert (
        im._inventory.get_host("foo.example.com").get_vars()["ansible_host"]  # type: ignore[union-attr]
        == "2001:1:2::4"
    )
    assert len(im._inventory.groups["ungrouped"].hosts) == 3
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_no_filter(mocker) -> None:
    inventory_filename = "test.infomaniak_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.infomaniak_dns_records
    infomaniak_token: foo
    zone_name: example.com
    """)}

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("Authorization", "Bearer foo")
            .expect_url("https://api.infomaniak.com/2/zones/example.com?with=records")
            .return_header("Content-Type", "application/json")
            .result_json(
                with_records(
                    INFOMANIAK_ZONE_JSON, INFOMANIAK_JSON_ZONE_RECORDS_GET_RESULT
                )
            ),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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
        im._inventory.get_host("example.com").get_vars()["ansible_host"]  # type: ignore[union-attr]
        == "2001:1:2::3"
    )
    assert (
        im._inventory.get_host("*.example.com").get_vars()["ansible_host"] == "1.2.3.5"  # type: ignore[union-attr]
    )
    assert (
        im._inventory.get_host("foo.example.com").get_vars()["ansible_host"]  # type: ignore[union-attr]
        == "2001:1:2::4"
    )
    assert (
        im._inventory.get_host("bar.example.com").get_vars()["ansible_host"]  # type: ignore[union-attr]
        == "example.org."
    )
    assert len(im._inventory.groups["ungrouped"].hosts) == 4
    assert len(im._inventory.groups["all"].hosts) == 0


def test_inventory_file_record_conversion_error(mocker) -> None:
    inventory_filename = "test.infomaniak_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.infomaniak_dns_records
    infomaniak_token: foo
    zone_name: "{{ 'example_com' }}"
    """)}

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 200)
            .expect_header("accept", "application/json")
            .expect_header("Authorization", "Bearer foo")
            .expect_url("https://api.infomaniak.com/2/zones/example.com?with=records")
            .return_header("Content-Type", "application/json")
            .result_json(
                with_records(
                    INFOMANIAK_ZONE_JSON, INFOMANIAK_JSON_ZONE_RECORDS_GET_RESULT_2
                )
            ),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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
    inventory_filename = "test.infomaniak_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.infomaniak_dns_records
    infomaniak_token: foo
    """)}

    open_url = OpenUrlProxy([])
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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
    inventory_filename = "test.infomaniak_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.infomaniak_dns_records
    infomaniak_token: foo
    zone_name: 'example.com'
    """)}

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 404)
            .expect_header("accept", "application/json")
            .expect_header("Authorization", "Bearer foo")
            .expect_url("https://api.infomaniak.com/2/zones/example.com?with=records")
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
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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
    inventory_filename = "test.infomaniak_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.infomaniak_dns_records
    infomaniak_token: foo
    zone_name: example.com
    """)}

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 401)
            .expect_header("accept", "application/json")
            .expect_header("Authorization", "Bearer foo")
            .expect_url("https://api.infomaniak.com/2/zones/example.org")
            .result_json(
                {
                    "result": "error",
                    "error": {
                        "code": "not_authorized",
                        "description": "Not authorized.",
                    },
                }
            ),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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
    inventory_filename = "test.infomaniak_dns.yaml"
    C.INVENTORY_ENABLED = ["community.dns.infomaniak_dns_records"]  # type: ignore
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.infomaniak_dns_records
    infomaniak_token: foo
    zone_id: example.com
    """)}

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 500)
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
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils._http.open_url",
        open_url,
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
