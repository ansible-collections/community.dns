# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


import pytest
from ansible_collections.community.dns.plugins.module_utils.hosttech.json_api import (
    HostTechJSONAPI,
    _create_record_from_json,
    _record_to_json,
)
from ansible_collections.community.dns.plugins.module_utils.record import DNSRecord
from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
)
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    MagicMock,
)


# The example JSONs for all record types are taken from https://api.ns1.hosttech.eu/api/documentation/

def test_AAAA():
    data = {
        "id": 11,
        "type": "AAAA",
        "name": "www",
        "ipv6": "2001:db8:1234::1",
        "ttl": 3600,
        "comment": "my first record",
    }
    record = _create_record_from_json(data)
    assert record.id == 11
    assert record.type == 'AAAA'
    assert record.prefix == 'www'
    assert record.target == '2001:db8:1234::1'
    assert record.ttl == 3600
    assert record.extra == {
        'comment': 'my first record',
    }
    assert _record_to_json(record, include_id=True) == data


def test_A():
    data = {
        "id": 10,
        "type": "A",
        "name": "www",
        "ipv4": "1.2.3.4",
        "ttl": 3600,
        "comment": "my first record",
    }
    record = _create_record_from_json(data)
    assert record.id == 10
    assert record.type == 'A'
    assert record.prefix == 'www'
    assert record.target == '1.2.3.4'
    assert record.ttl == 3600
    assert record.extra == {
        'comment': 'my first record',
    }
    assert _record_to_json(record, include_id=True) == data


def test_CAA():
    data = {
        "id": 12,
        "type": "CAA",
        "name": "",
        "flag": "0",
        "tag": "issue",
        "value": "letsencrypt.org",
        "ttl": 3600,
        "comment": "my first record",
    }
    record = _create_record_from_json(data)
    assert record.id == 12
    assert record.type == 'CAA'
    assert record.prefix is None
    assert record.target == '0 issue "letsencrypt.org"'
    assert record.ttl == 3600
    assert record.extra == {
        'comment': 'my first record',
    }
    assert _record_to_json(record, include_id=True) == data

    # We also accept versions without quotes:
    record.target = '0 issue letsencrypt.org'
    assert _record_to_json(record, include_id=True) == data

    record.target = '0\tissue "letsencrypt.org"'
    with pytest.raises(DNSAPIError) as exc:
        _record_to_json(record)
    assert exc.value.args[0].startswith('Cannot split CAA record "0\tissue "letsencrypt.org"" into flag, tag and value: ')


def test_CNAME():
    data = {
        "id": 13,
        "type": "CNAME",
        "name": "www",
        "cname": "site.example.com",
        "ttl": 3600,
        "comment": "my first record",
    }
    record = _create_record_from_json(data)
    assert record.id == 13
    assert record.type == 'CNAME'
    assert record.prefix == 'www'
    assert record.target == 'site.example.com'
    assert record.ttl == 3600
    assert record.extra == {
        'comment': 'my first record',
    }
    assert _record_to_json(record, include_id=True) == data


def test_MX():
    data = {
        "id": 14,
        "type": "MX",
        "ownername": "",
        "name": "mail.example.com",
        "pref": 10,
        "ttl": 3600,
        "comment": "my first record",
    }
    record = _create_record_from_json(data)
    assert record.id == 14
    assert record.type == 'MX'
    assert record.prefix is None
    assert record.target == '10 mail.example.com'
    assert record.ttl == 3600
    assert record.extra == {
        'comment': 'my first record',
    }
    assert _record_to_json(record, include_id=True) == data

    record.target = 'mail.example.com'
    with pytest.raises(DNSAPIError) as exc:
        _record_to_json(record)
    assert exc.value.args[0].startswith('Cannot split MX record "mail.example.com" into integer preference and name: ')

    record.target = 'x mail.example.com'
    with pytest.raises(DNSAPIError) as exc:
        _record_to_json(record)
    assert exc.value.args[0].startswith('Cannot split MX record "x mail.example.com" into integer preference and name: ')


def test_NS():
    # WARNING: as opposed to documented on https://api.ns1.hosttech.eu/api/documentation/,
    #          NS records use 'targetname' and not 'name'!
    data = {
        "id": 14,
        "type": "NS",
        "ownername": "sub",
        "targetname": "ns1.example.com",
        "ttl": 3600,
        "comment": "my first record",
    }
    record = _create_record_from_json(data)
    assert record.id == 14
    assert record.type == 'NS'
    assert record.prefix == 'sub'
    assert record.target == 'ns1.example.com'
    assert record.ttl == 3600
    assert record.extra == {
        'comment': 'my first record',
    }
    assert _record_to_json(record, include_id=True) == data


def test_PTR():
    data = {
        "id": 15,
        "type": "PTR",
        "origin": "4.3.2.1",
        "name": "smtp.example.com",
        "ttl": 3600,
        "comment": "my first record",
    }
    record = _create_record_from_json(data)
    assert record.id == 15
    assert record.type == 'PTR'
    assert record.prefix is None
    assert record.target == '4.3.2.1 smtp.example.com'
    assert record.ttl == 3600
    assert record.extra == {
        'comment': 'my first record',
    }
    assert _record_to_json(record, include_id=True) == data

    record.target = 'smtp.example.com'
    with pytest.raises(DNSAPIError) as exc:
        _record_to_json(record)
    assert exc.value.args[0].startswith('Cannot split PTR record "smtp.example.com" into origin and name: ')


def test_SRV():
    data = {
        "id": 16,
        "type": "SRV",
        "service": "_autodiscover._tcp",
        "priority": 0,
        "weight": 1,
        "port": 443,
        "target": "exchange.example.com",
        "ttl": 3600,
        "comment": "my first record",
    }
    record = _create_record_from_json(data)
    assert record.id == 16
    assert record.type == 'SRV'
    assert record.prefix == '_autodiscover._tcp'
    assert record.target == '0 1 443 exchange.example.com'
    assert record.ttl == 3600
    assert record.extra == {
        'comment': 'my first record',
    }
    assert _record_to_json(record, include_id=True) == data

    record.target = '1 443 exchange.example.com'
    with pytest.raises(DNSAPIError) as exc:
        _record_to_json(record)
    assert exc.value.args[0].startswith(
        'Cannot split SRV record "1 443 exchange.example.com" into integer priority, integer weight, integer port and target: ')

    record.target = 'x 1 443 exchange.example.com'
    with pytest.raises(DNSAPIError) as exc:
        _record_to_json(record)
    assert exc.value.args[0].startswith(
        'Cannot split SRV record "x 1 443 exchange.example.com" into integer priority, integer weight, integer port and target: ')

    record.target = '0 x 443 exchange.example.com'
    with pytest.raises(DNSAPIError) as exc:
        _record_to_json(record)
    assert exc.value.args[0].startswith(
        'Cannot split SRV record "0 x 443 exchange.example.com" into integer priority, integer weight, integer port and target: ')

    record.target = '0 1 x exchange.example.com'
    with pytest.raises(DNSAPIError) as exc:
        _record_to_json(record)
    assert exc.value.args[0].startswith(
        'Cannot split SRV record "0 1 x exchange.example.com" into integer priority, integer weight, integer port and target: ')


def test_TXT():
    data = {
        "id": 17,
        "type": "TXT",
        "name": "",
        "text": "v=spf1 ip4:1.2.3.4/32 -all",
        "ttl": 3600,
        "comment": "my first record",
    }
    record = _create_record_from_json(data)
    assert record.id == 17
    assert record.type == 'TXT'
    assert record.prefix is None
    assert record.target == 'v=spf1 ip4:1.2.3.4/32 -all'
    assert record.ttl == 3600
    assert record.extra == {
        'comment': 'my first record',
    }
    assert _record_to_json(record, include_id=True) == data


def test_TLSA():
    data = {
        "id": 17,
        "type": "TLSA",
        "name": "",
        "text": "0 0 1 d2abde240d7cd3ee6b4b28c54df034b97983a1d16e8a410e4561cb106618e971",
        "ttl": 3600,
        "comment": "my first record",
    }
    record = _create_record_from_json(data)
    assert record.id == 17
    assert record.type == 'TLSA'
    assert record.prefix is None
    assert record.target == '0 0 1 d2abde240d7cd3ee6b4b28c54df034b97983a1d16e8a410e4561cb106618e971'
    assert record.ttl == 3600
    assert record.extra == {
        'comment': 'my first record',
    }
    assert _record_to_json(record, include_id=True) == data


def test_unknown_records():
    data = {
        "id": 17,
        "type": "unknown",
        "name": "",
        "ttl": 3600,
        "comment": "my first record",
    }
    with pytest.raises(DNSAPIError) as exc:
        _create_record_from_json(data)
    assert exc.value.args[0] == 'Cannot parse unknown record type: unknown'

    record = DNSRecord()
    record.type = 'unknown'
    with pytest.raises(DNSAPIError) as exc:
        _record_to_json(record)
    assert exc.value.args[0] == 'Cannot serialize unknown record type: unknown'


def test_list_pagination():
    def get_1(url, query=None, must_have_content=True, expected=None):
        assert url == 'https://example.com'
        assert must_have_content is True
        assert expected == [200]
        assert query is not None
        assert len(query) == 2
        assert query['limit'] == 1
        assert query['offset'] in [0, 1, 2]
        if query['offset'] < 2:
            return {'data': [query['offset']]}, {}
        return {'data': []}, {}

    def get_2(url, query=None, must_have_content=True, expected=None):
        assert url == 'https://example.com'
        assert must_have_content is True
        assert expected == [200]
        assert query is not None
        assert len(query) == 3
        assert query['foo'] == 'bar'
        assert query['limit'] == 2
        assert query['offset'] in [0, 2]
        if query['offset'] < 2:
            return {'data': ['bar', 'baz']}, {}
        return {'data': ['foo']}, {}

    api = HostTechJSONAPI(MagicMock(), '123')

    api._get = MagicMock(side_effect=get_1)
    result = api._list_pagination('https://example.com', block_size=1)
    assert result == [0, 1]

    api._get = MagicMock(side_effect=get_2)
    result = api._list_pagination('https://example.com', query={'foo': 'bar'}, block_size=2)
    assert result == ['bar', 'baz', 'foo']


def test_update_id_missing():
    api = HostTechJSONAPI(MagicMock(), '123')
    with pytest.raises(DNSAPIError) as exc:
        api.update_record(1, DNSRecord())
    assert exc.value.args[0] == 'Need record ID to update record!'


def test_update_id_delete():
    api = HostTechJSONAPI(MagicMock(), '123')
    with pytest.raises(DNSAPIError) as exc:
        api.delete_record(1, DNSRecord())
    assert exc.value.args[0] == 'Need record ID to delete record!'


def test_extract_error_message():
    api = HostTechJSONAPI(MagicMock(), '123')
    assert api._extract_error_message(None) == ''
    assert api._extract_error_message('foo') == ' with data: foo'
    assert api._extract_error_message({}) == ' with data: {}'
    assert api._extract_error_message({'message': ''}) == " with data: {'message': ''}"
    assert api._extract_error_message({'message': 'foo'}) == ' with message "foo"'
    assert api._extract_error_message({'message': 'foo', 'errors': ''}) == ' with message "foo"'
    assert api._extract_error_message({'message': 'foo', 'errors': {}}) == ' with message "foo"'
    assert api._extract_error_message({'message': 'foo', 'errors': {'bar': 'baz'}}) == ' with message "foo" (field "bar": baz)'
    assert api._extract_error_message({'errors': {'bar': ['baz', 'bam'], 'arf': 'fra'}}) == ' (field "arf": fra) (field "bar": baz; bam)'
