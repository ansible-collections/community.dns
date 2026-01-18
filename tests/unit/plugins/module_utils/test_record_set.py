# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
)
from ansible_collections.community.dns.plugins.module_utils.record_set import (
    DNSRecordSet,
    format_record_set_for_output,
)


def test_format_record_set_for_output():
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
    A3.prefix = "foo"
    A3.ttl = None
    A3.target = '1.2.3.6'

    a1 = DNSRecordSet()
    a1.type = 'A'
    a1.prefix = None
    a1.ttl = 300
    a1.records = [A1, A2]
    a1.extra = {}

    a2 = DNSRecordSet()
    a2.id = "foo/A"
    a2.type = 'A'
    a2.prefix = "foo"
    a2.ttl = None
    a2.records = [A3]
    a2.extra = {
        "foo": "bar",
    }

    assert format_record_set_for_output(a1, 'example.com', prefix=None) == {
        'prefix': '',
        'record': 'example.com',
        'ttl': 300,
        'type': 'A',
        'value': [
            '1.2.3.4',
            '1.2.3.5',
        ],
    }
    assert format_record_set_for_output(a2, 'foo.example.org', prefix='foo') == {
        'prefix': 'foo',
        'record': 'foo.example.org',
        'ttl': None,
        'type': 'A',
        'value': [
            '1.2.3.6',
        ],
    }


def test_record_str_repr():
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
    A3.prefix = "foo"
    A3.ttl = None
    A3.target = '1.2.3.6'

    a1 = DNSRecordSet()
    a1.type = 'A'
    a1.prefix = None
    a1.ttl = 300
    a1.records = [A1, A2]
    a1.extra = {}

    a2 = DNSRecordSet()
    a2.id = "foo/A"
    a2.type = 'A'
    a2.prefix = "foo"
    a2.ttl = None
    a2.records = [A3]
    a2.extra = {
        "foo": "bar",
    }

    assert str(a1) == repr(a1)
    assert str(a1) == (
        "DNSRecordSet(type: A, prefix: (none), ttl: 5m, records: [DNSRecord(type: A, prefix: (none), target: "
        "\"1.2.3.4\", ttl: 5m, extra: {'foo': 'bar'}), DNSRecord(type: A, prefix: (none), target: \"1.2.3.5\", ttl: 5m)])"
    )
    assert str(a2) == repr(a2)
    assert str(a2) == (
        "DNSRecordSet(id: foo/A, type: A, prefix: \"foo\", ttl: default, records: [DNSRecord(type: A,"
        " prefix: \"foo\", target: \"1.2.3.6\", ttl: default)], extra: {'foo': 'bar'})"
    )
