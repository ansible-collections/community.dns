# Copyright (c), Felix Fontein <felix@fontein.de>, 2021
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import json
import os
import textwrap

import pytest

from mock import MagicMock

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.inventory.data import InventoryData
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.internal_test_tools.tests.unit.mock.path import mock_unfrackpath_noop
from ansible_collections.community.internal_test_tools.tests.unit.mock.loader import DictDataLoader
from ansible_collections.community.internal_test_tools.tests.unit.utils.open_url_framework import (
    OpenUrlCall,
    OpenUrlProxy,
)

from ansible_collections.community.dns.plugins.inventory.hosttech_dns_records import InventoryModule


HOSTTECH_WSDL_DEFAULT_ENTRIES = [
    (125, 42, 'A', '', '1.2.3.4', 3600, None, None),
    (126, 42, 'A', '*', '1.2.3.5', 3600, None, None),
    (127, 42, 'AAAA', '', '2001:1:2::3', 3600, None, None),
    (128, 42, 'AAAA', 'foo', '2001:1:2::4', 3600, None, None),
    (129, 42, 'MX', '', 'example.com', 3600, None, '10'),
    (130, 42, 'CNAME', 'bar', 'example.org.', 10800, None, None),
]

HOSTTECH_JSON_DEFAULT_ENTRIES = [
    # (125, 42, 'A', '', '1.2.3.4', 3600, None, None),
    {
        'id': 125,
        'type': 'A',
        'name': '',
        'ipv4': '1.2.3.4',
        'ttl': 3600,
        'comment': '',
    },
    # (126, 42, 'A', '*', '1.2.3.5', 3600, None, None),
    {
        'id': 126,
        'type': 'A',
        'name': '*',
        'ipv4': '1.2.3.5',
        'ttl': 3600,
        'comment': '',
    },
    # (127, 42, 'AAAA', '', '2001:1:2::3', 3600, None, None),
    {
        'id': 127,
        'type': 'AAAA',
        'name': '',
        'ipv6': '2001:1:2::3',
        'ttl': 3600,
        'comment': '',
    },
    # (128, 42, 'AAAA', '*', '2001:1:2::4', 3600, None, None),
    {
        'id': 128,
        'type': 'AAAA',
        'name': 'foo',
        'ipv6': '2001:1:2::4',
        'ttl': 3600,
        'comment': '',
    },
    # (129, 42, 'MX', '', 'example.com', 3600, None, '10'),
    {
        'id': 129,
        'type': 'MX',
        'ownername': '',
        'name': 'example.com',
        'pref': 10,
        'ttl': 3600,
        'comment': '',
    },
    # (130, 42, 'CNAME', 'bar', 'example.org.', 10800, None, None),
    {
        'id': 130,
        'type': 'CNAME',
        'name': 'bar',
        'cname': 'example.org.',
        'ttl': 10800,
        'comment': '',
    },
]


HOSTTECH_JSON_ZONE_LIST_RESULT = {
    "data": [
        {
            "id": 42,
            "name": "example.com",
            "email": "test@example.com",
            "ttl": 10800,
            "nameserver": "ns1.hosttech.ch",
            "dnssec": False,
        },
    ],
}

HOSTTECH_JSON_ZONE_GET_RESULT = {
    "data": {
        "id": 42,
        "name": "example.com",
        "email": "test@example.com",
        "ttl": 10800,
        "nameserver": "ns1.hosttech.ch",
        "dnssec": False,
        "records": HOSTTECH_JSON_DEFAULT_ENTRIES,
    }
}

HOSTTECH_JSON_ZONE_RECORDS_GET_RESULT = {
    "data": HOSTTECH_JSON_DEFAULT_ENTRIES,
}


original_exists = os.path.exists
original_access = os.access


def exists_mock(path, exists=True):
    def exists(f):
        if to_native(f) == path:
            return exists
        return original_exists(f)

    return exists


def access_mock(path, can_access=True):
    def access(f, m, *args, **kwargs):
        if to_native(f) == path:
            return can_access
        return original_access(f, m, *args, **kwargs)

    return access


def test_inventory_file_simple(mocker):
    inventory_filename = "test.hosttech_dns.yaml"
    C.INVENTORY_ENABLED = ['community.dns.hosttech_dns_records']
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.hosttech_dns_records
    hosttech_token: foo
    zone_name: example.com
    filters:
      type: A
    """)}

    open_url = OpenUrlProxy([
        OpenUrlCall('GET', 200)
        .expect_header('accept', 'application/json')
        .expect_header('authorization', 'Bearer foo')
        .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
        .expect_query_values('query', 'example.com')
        .return_header('Content-Type', 'application/json')
        .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
        OpenUrlCall('GET', 200)
        .expect_header('accept', 'application/json')
        .expect_header('authorization', 'Bearer foo')
        .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
        .return_header('Content-Type', 'application/json')
        .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    mocker.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    mocker.patch('os.path.exists', exists_mock(inventory_filename))
    mocker.patch('os.access', access_mock(inventory_filename))
    im = InventoryManager(loader=DictDataLoader(inventory_file), sources=inventory_filename)

    open_url.assert_is_done()

    assert im._inventory.hosts
    assert 'example.com' in im._inventory.hosts
    assert '*.example.com' in im._inventory.hosts
    assert 'foo.example.com' not in im._inventory.hosts
    assert 'bar.example.com' not in im._inventory.hosts
    assert im._inventory.get_host('example.com') in im._inventory.groups['ungrouped'].hosts
    assert im._inventory.get_host('*.example.com') in im._inventory.groups['ungrouped'].hosts
    assert im._inventory.get_host('example.com').get_vars()['ansible_host'] == '1.2.3.4'
    assert im._inventory.get_host('*.example.com').get_vars()['ansible_host'] == '1.2.3.5'
    assert len(im._inventory.groups['ungrouped'].hosts) == 2
    assert len(im._inventory.groups['all'].hosts) == 0


def test_inventory_file_collision(mocker):
    inventory_filename = "test.hosttech_dns.yaml"
    C.INVENTORY_ENABLED = ['community.dns.hosttech_dns_records']
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.hosttech_dns_records
    hosttech_token: "{{ 'foo' }}"
    zone_name: "{{ 'example' ~ '.com' }}"
    filters:
      type:
        - A
        - AAAA
    """)}

    open_url = OpenUrlProxy([
        OpenUrlCall('GET', 200)
        .expect_header('accept', 'application/json')
        .expect_header('authorization', 'Bearer foo')
        .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
        .expect_query_values('query', 'example.com')
        .return_header('Content-Type', 'application/json')
        .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
        OpenUrlCall('GET', 200)
        .expect_header('accept', 'application/json')
        .expect_header('authorization', 'Bearer foo')
        .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
        .return_header('Content-Type', 'application/json')
        .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    mocker.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    mocker.patch('os.path.exists', exists_mock(inventory_filename))
    mocker.patch('os.access', access_mock(inventory_filename))
    im = InventoryManager(loader=DictDataLoader(inventory_file), sources=inventory_filename)

    open_url.assert_is_done()

    assert im._inventory.hosts
    assert 'example.com' in im._inventory.hosts
    assert '*.example.com' in im._inventory.hosts
    assert 'foo.example.com' in im._inventory.hosts
    assert 'bar.example.com' not in im._inventory.hosts
    assert im._inventory.get_host('example.com') in im._inventory.groups['ungrouped'].hosts
    assert im._inventory.get_host('*.example.com') in im._inventory.groups['ungrouped'].hosts
    assert im._inventory.get_host('foo.example.com') in im._inventory.groups['ungrouped'].hosts
    assert im._inventory.get_host('example.com').get_vars()['ansible_host'] == '2001:1:2::3'
    assert im._inventory.get_host('*.example.com').get_vars()['ansible_host'] == '1.2.3.5'
    assert im._inventory.get_host('foo.example.com').get_vars()['ansible_host'] == '2001:1:2::4'
    assert len(im._inventory.groups['ungrouped'].hosts) == 3
    assert len(im._inventory.groups['all'].hosts) == 0


def test_inventory_file_no_filter(mocker):
    inventory_filename = "test.hosttech_dns.yaml"
    C.INVENTORY_ENABLED = ['community.dns.hosttech_dns_records']
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.hosttech_dns_records
    hosttech_token: foo
    zone_id: 42
    """)}

    open_url = OpenUrlProxy([
        OpenUrlCall('GET', 200)
        .expect_header('accept', 'application/json')
        .expect_header('authorization', 'Bearer foo')
        .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
        .return_header('Content-Type', 'application/json')
        .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    mocker.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    mocker.patch('os.path.exists', exists_mock(inventory_filename))
    mocker.patch('os.access', access_mock(inventory_filename))
    im = InventoryManager(loader=DictDataLoader(inventory_file), sources=inventory_filename)

    open_url.assert_is_done()

    assert im._inventory.hosts
    assert 'example.com' in im._inventory.hosts
    assert '*.example.com' in im._inventory.hosts
    assert 'foo.example.com' in im._inventory.hosts
    assert 'bar.example.com' in im._inventory.hosts
    assert im._inventory.get_host('example.com') in im._inventory.groups['ungrouped'].hosts
    assert im._inventory.get_host('*.example.com') in im._inventory.groups['ungrouped'].hosts
    assert im._inventory.get_host('foo.example.com') in im._inventory.groups['ungrouped'].hosts
    assert im._inventory.get_host('bar.example.com') in im._inventory.groups['ungrouped'].hosts
    assert im._inventory.get_host('example.com').get_vars()['ansible_host'] == '2001:1:2::3'
    assert im._inventory.get_host('*.example.com').get_vars()['ansible_host'] == '1.2.3.5'
    assert im._inventory.get_host('foo.example.com').get_vars()['ansible_host'] == '2001:1:2::4'
    assert im._inventory.get_host('bar.example.com').get_vars()['ansible_host'] == 'example.org.'
    assert len(im._inventory.groups['ungrouped'].hosts) == 4
    assert len(im._inventory.groups['all'].hosts) == 0


def test_inventory_file_invalid_zone_id(mocker):
    inventory_filename = "test.hosttech_dns.yaml"
    C.INVENTORY_ENABLED = ['community.dns.hosttech_dns_records']
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.hosttech_dns_records
    hosttech_token: foo
    zone_id: invalid
    """)}

    open_url = OpenUrlProxy([
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    mocker.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    mocker.patch('os.path.exists', exists_mock(inventory_filename))
    mocker.patch('os.access', access_mock(inventory_filename))
    im = InventoryManager(loader=DictDataLoader(inventory_file), sources=inventory_filename)

    open_url.assert_is_done()

    assert not im._inventory.hosts
    assert len(im._inventory.groups['ungrouped'].hosts) == 0
    assert len(im._inventory.groups['all'].hosts) == 0


def test_inventory_file_missing_zone(mocker):
    inventory_filename = "test.hosttech_dns.yaml"
    C.INVENTORY_ENABLED = ['community.dns.hosttech_dns_records']
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.hosttech_dns_records
    hosttech_token: foo
    """)}

    open_url = OpenUrlProxy([
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    mocker.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    mocker.patch('os.path.exists', exists_mock(inventory_filename))
    mocker.patch('os.access', access_mock(inventory_filename))
    im = InventoryManager(loader=DictDataLoader(inventory_file), sources=inventory_filename)

    open_url.assert_is_done()

    assert not im._inventory.hosts
    assert len(im._inventory.groups['ungrouped'].hosts) == 0
    assert len(im._inventory.groups['all'].hosts) == 0


def test_inventory_file_zone_not_found(mocker):
    inventory_filename = "test.hosttech_dns.yaml"
    C.INVENTORY_ENABLED = ['community.dns.hosttech_dns_records']
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.hosttech_dns_records
    hosttech_token: foo
    zone_id: "{{ 11 + 12 }}"
    """)}

    open_url = OpenUrlProxy([
        OpenUrlCall('GET', 404)
        .expect_header('accept', 'application/json')
        .expect_header('authorization', 'Bearer foo')
        .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/23')
        .return_header('Content-Type', 'application/json')
        .result_json(dict(message="")),
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    mocker.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    mocker.patch('os.path.exists', exists_mock(inventory_filename))
    mocker.patch('os.access', access_mock(inventory_filename))
    im = InventoryManager(loader=DictDataLoader(inventory_file), sources=inventory_filename)

    open_url.assert_is_done()

    assert not im._inventory.hosts
    assert len(im._inventory.groups['ungrouped'].hosts) == 0
    assert len(im._inventory.groups['all'].hosts) == 0


def test_inventory_file_unauthorized(mocker):
    inventory_filename = "test.hosttech_dns.yaml"
    C.INVENTORY_ENABLED = ['community.dns.hosttech_dns_records']
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.hosttech_dns_records
    hosttech_token: foo
    zone_id: 23
    """)}

    open_url = OpenUrlProxy([
        OpenUrlCall('GET', 403)
        .expect_header('accept', 'application/json')
        .expect_header('authorization', 'Bearer foo')
        .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/23')
        .result_json(dict(message="")),
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    mocker.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    mocker.patch('os.path.exists', exists_mock(inventory_filename))
    mocker.patch('os.access', access_mock(inventory_filename))
    im = InventoryManager(loader=DictDataLoader(inventory_file), sources=inventory_filename)

    open_url.assert_is_done()

    assert not im._inventory.hosts
    assert len(im._inventory.groups['ungrouped'].hosts) == 0
    assert len(im._inventory.groups['all'].hosts) == 0


def test_inventory_file_error(mocker):
    inventory_filename = "test.hosttech_dns.yaml"
    C.INVENTORY_ENABLED = ['community.dns.hosttech_dns_records']
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.hosttech_dns_records
    hosttech_token: foo
    zone_id: 42
    """)}

    open_url = OpenUrlProxy([
        OpenUrlCall('GET', 500)
        .expect_header('accept', 'application/json')
        .expect_header('authorization', 'Bearer foo')
        .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
        .result_json({}),
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    mocker.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    mocker.patch('os.path.exists', exists_mock(inventory_filename))
    mocker.patch('os.access', access_mock(inventory_filename))
    im = InventoryManager(loader=DictDataLoader(inventory_file), sources=inventory_filename)

    open_url.assert_is_done()

    assert not im._inventory.hosts
    assert len(im._inventory.groups['ungrouped'].hosts) == 0
    assert len(im._inventory.groups['all'].hosts) == 0


def test_inventory_wrong_file(mocker):
    inventory_filename = "test.hetznerdns.yml"
    C.INVENTORY_ENABLED = ['community.dns.hosttech_dns_records']
    inventory_file = {inventory_filename: textwrap.dedent("""\
    ---
    plugin: community.dns.hosttech_dns_records
    hosttech_token: foo
    """)}

    open_url = OpenUrlProxy([])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    mocker.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    mocker.patch('os.path.exists', exists_mock(inventory_filename))
    mocker.patch('os.access', access_mock(inventory_filename))
    im = InventoryManager(loader=DictDataLoader(inventory_file), sources=inventory_filename)

    open_url.assert_is_done()

    assert not im._inventory.hosts
    assert len(im._inventory.groups['ungrouped'].hosts) == 0
    assert len(im._inventory.groups['all'].hosts) == 0


def test_inventory_no_file(mocker):
    inventory_filename = "test.hosttech_dns.yml"
    C.INVENTORY_ENABLED = ['community.dns.hosttech_dns_records']

    open_url = OpenUrlProxy([])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    mocker.patch('ansible.inventory.manager.unfrackpath', mock_unfrackpath_noop)
    mocker.patch('os.path.exists', exists_mock(inventory_filename, False))
    mocker.patch('os.access', access_mock(inventory_filename, False))
    im = InventoryManager(loader=DictDataLoader({}), sources=inventory_filename)

    open_url.assert_is_done()

    assert not im._inventory.hosts
    assert len(im._inventory.groups['ungrouped'].hosts) == 0
    assert len(im._inventory.groups['all'].hosts) == 0
