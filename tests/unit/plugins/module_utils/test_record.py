# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible_collections.community.dns.plugins.module_utils.record import (
    format_ttl,
    DNSRecord,
    format_records_for_output,
)


def test_format_ttl():
    assert format_ttl(None) == 'default'
    assert format_ttl(1) == '1s'
    assert format_ttl(59) == '59s'
    assert format_ttl(60) == '1m'
    assert format_ttl(61) == '1m 1s'
    assert format_ttl(3539) == '58m 59s'
    assert format_ttl(3540) == '59m'
    assert format_ttl(3541) == '59m 1s'
    assert format_ttl(3599) == '59m 59s'
    assert format_ttl(3600) == '1h'
    assert format_ttl(3601) == '1h 1s'
    assert format_ttl(3661) == '1h 1m 1s'


def test_format_records_for_output():
    A1 = DNSRecord()
    A1.type = 'A'
    A1.ttl = 300
    A1.target = '1.2.3.4'
    A1.extra['foo'] = 'bar'
    A2 = DNSRecord()
    A2.type = 'A'
    A2.ttl = 300
    A2.target = '1.2.3.5'
    A3 = DNSRecord()
    A3.type = 'A'
    A3.ttl = 3600
    A3.target = '1.2.3.6'
    AAAA = DNSRecord()
    AAAA.type = 'AAAA'
    AAAA.ttl = 600
    AAAA.target = '::1'
    AAAA2 = DNSRecord()
    AAAA2.type = 'AAAA'
    AAAA2.ttl = None
    AAAA2.target = '::2'
    assert format_records_for_output([], 'foo', '') == {
        'record': 'foo',
        'prefix': '',
        'type': None,
        'ttl': None,
        'value': [],
    }
    assert format_records_for_output([A1, A2], 'foo', 'bar') == {
        'record': 'foo',
        'prefix': 'bar',
        'type': 'A',
        'ttl': 300,
        'value': ['1.2.3.4', '1.2.3.5'],
    }
    assert format_records_for_output([A3, A1], 'foo', None) == {
        'record': 'foo',
        'prefix': '',
        'type': 'A',
        'ttl': 300,
        'ttls': [300, 3600],
        'value': ['1.2.3.6', '1.2.3.4'],
    }
    assert format_records_for_output([A3], 'foo', None) == {
        'record': 'foo',
        'prefix': '',
        'type': 'A',
        'ttl': 3600,
        'value': ['1.2.3.6'],
    }
    assert format_records_for_output([AAAA], 'foo', None) == {
        'record': 'foo',
        'prefix': '',
        'type': 'AAAA',
        'ttl': 600,
        'value': ['::1'],
    }
    assert format_records_for_output([A3, AAAA], 'foo', None) == {
        'record': 'foo',
        'prefix': '',
        'type': 'A',
        'ttl': 600,
        'ttls': [600, 3600],
        'value': ['1.2.3.6', '::1'],
    }
    assert format_records_for_output([AAAA, A3], 'foo', None) == {
        'record': 'foo',
        'prefix': '',
        'type': 'A',
        'ttl': 600,
        'ttls': [600, 3600],
        'value': ['::1', '1.2.3.6'],
    }
    assert format_records_for_output([AAAA2], 'foo', None) == {
        'record': 'foo',
        'prefix': '',
        'type': 'AAAA',
        'ttl': None,
        'value': ['::2'],
    }
    print(format_records_for_output([AAAA2, AAAA], 'foo', None))
    assert format_records_for_output([AAAA2, AAAA], 'foo', None) == {
        'record': 'foo',
        'prefix': '',
        'type': 'AAAA',
        'ttl': None,
        'ttls': [None, 600],
        'value': ['::2', '::1'],
    }


def test_record_str_repr():
    A1 = DNSRecord()
    A1.prefix = None
    A1.type = 'A'
    A1.ttl = 300
    A1.target = '1.2.3.4'
    assert str(A1) == 'DNSRecord(type: A, prefix: (none), target: "1.2.3.4", ttl: 5m)'
    assert repr(A1) == 'DNSRecord(type: A, prefix: (none), target: "1.2.3.4", ttl: 5m)'
    A2 = DNSRecord()
    A2.id = 23
    A2.prefix = 'bar'
    A2.type = 'A'
    A2.ttl = 1
    A2.target = ''
    A2.extra['foo'] = 'bar'
    assert str(A2) == 'DNSRecord(id: 23, type: A, prefix: "bar", target: "", ttl: 1s, extra: {\'foo\': \'bar\'})'
    assert repr(A2) == 'DNSRecord(id: 23, type: A, prefix: "bar", target: "", ttl: 1s, extra: {\'foo\': \'bar\'})'
