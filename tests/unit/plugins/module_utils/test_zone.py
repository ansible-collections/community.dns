# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.record import DNSRecord
from ansible_collections.community.dns.plugins.module_utils.record_set import (
    DNSRecordSet,
)
from ansible_collections.community.dns.plugins.module_utils.zone import (
    DNSZone,
    DNSZoneWithRecords,
    DNSZoneWithRecordSets,
)


def test_zone_str_repr():
    Z1 = DNSZone('foo')
    assert str(Z1) == 'DNSZone(name: foo, info: {})'
    assert repr(Z1) == 'DNSZone(name: foo, info: {})'
    Z2 = DNSZone('foo')
    Z2.id = 42
    Z2.info['foo'] = 'bar'
    assert str(Z2) == "DNSZone(id: 42, name: foo, info: {'foo': 'bar'})"
    assert repr(Z2) == "DNSZone(id: 42, name: foo, info: {'foo': 'bar'})"


def test_zone_with_records_str_repr():
    Z1 = DNSZone('foo')
    Z2 = DNSZone('foo')
    Z2.id = 42
    A1 = DNSRecord()
    A1.prefix = None
    A1.type = 'A'
    A1.ttl = 300
    A1.target = '1.2.3.4'
    A2 = DNSRecord()
    A2.id = 23
    A2.prefix = 'bar'
    A2.type = 'A'
    A2.ttl = 1
    A2.target = ''
    A2.extra['foo'] = 23
    ZZ1 = DNSZoneWithRecords(Z1, [A1])
    ZZ2 = DNSZoneWithRecords(Z2, [A1, A2])
    assert str(ZZ1) == '(DNSZone(name: foo, info: {}), [DNSRecord(type: A, prefix: (none), target: "1.2.3.4", ttl: 5m)])'
    assert repr(ZZ1) == 'DNSZoneWithRecords(DNSZone(name: foo, info: {}), [DNSRecord(type: A, prefix: (none), target: "1.2.3.4", ttl: 5m)])'
    assert str(ZZ2) == (
        '(DNSZone(id: 42, name: foo, info: {}), [DNSRecord(type: A, prefix: (none), target: "1.2.3.4", ttl: 5m),'
        ' DNSRecord(id: 23, type: A, prefix: "bar", target: "", ttl: 1s, extra: {\'foo\': 23})])'
    )
    assert repr(ZZ2) == (
        'DNSZoneWithRecords(DNSZone(id: 42, name: foo, info: {}), [DNSRecord(type: A, prefix: (none), target: "1.2.3.4", ttl: 5m),'
        ' DNSRecord(id: 23, type: A, prefix: "bar", target: "", ttl: 1s, extra: {\'foo\': 23})])'
    )


def test_zone_with_record_sets_str_repr():
    Z1 = DNSZone('foo')
    Z2 = DNSZone('foo')
    Z2.id = 42
    A1 = DNSRecord()
    A1.prefix = None
    A1.type = 'A'
    A1.ttl = 300
    A1.target = '1.2.3.4'
    A2 = DNSRecord()
    A2.id = 23
    A2.prefix = 'bar'
    A2.type = 'A'
    A2.ttl = 1
    A2.target = ''
    A2.extra['foo'] = 23
    a1 = DNSRecordSet()
    a1.prefix = None
    a1.type = 'A'
    a1.ttl = 300
    a1.records = [A1]
    a2 = DNSRecordSet()
    a2.prefix = 'bar'
    a2.type = 'A'
    a2.ttl = 1
    a2.records = [A2]
    a2.extra = {'baz': 'bam'}
    ZZ1 = DNSZoneWithRecordSets(Z1, [a1])
    ZZ2 = DNSZoneWithRecordSets(Z2, [a1, a2])
    print(repr(ZZ1))
    print(str(ZZ2))
    print(repr(ZZ2))
    assert str(ZZ1) == (
        '(DNSZone(name: foo, info: {}), [DNSRecordSet(type: A, prefix: (none), ttl: 5m, records:'
        ' [DNSRecord(type: A, prefix: (none), target: "1.2.3.4", ttl: 5m)])])'
    )
    assert repr(ZZ1) == (
        'DNSZoneWithRecordSets(DNSZone(name: foo, info: {}), [DNSRecordSet(type: A, prefix: (none),'
        ' ttl: 5m, records: [DNSRecord(type: A, prefix: (none), target: "1.2.3.4", ttl: 5m)])])'
    )
    assert str(ZZ2) == (
        '(DNSZone(id: 42, name: foo, info: {}), [DNSRecordSet(type: A, prefix: (none), ttl: 5m, records:'
        ' [DNSRecord(type: A, prefix: (none), target: "1.2.3.4", ttl: 5m)]), DNSRecordSet(type: A, prefix: "bar", ttl: 1s,'
        ' records: [DNSRecord(id: 23, type: A, prefix: "bar", target: "", ttl: 1s, extra: {\'foo\': 23})], extra: {\'baz\': \'bam\'})])'
    )
    assert repr(ZZ2) == (
        'DNSZoneWithRecordSets(DNSZone(id: 42, name: foo, info: {}), [DNSRecordSet(type: A, prefix: (none),'
        ' ttl: 5m, records: [DNSRecord(type: A, prefix: (none), target: "1.2.3.4", ttl: 5m)]), DNSRecordSet(type: A, prefix:'
        ' "bar", ttl: 1s, records: [DNSRecord(id: 23, type: A, prefix: "bar", target: "", ttl: 1s, extra: {\'foo\': 23})], extra: {\'baz\': \'bam\'})])'
    )
