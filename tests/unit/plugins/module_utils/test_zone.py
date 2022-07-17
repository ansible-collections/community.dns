# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
)

from ansible_collections.community.dns.plugins.module_utils.zone import (
    DNSZone,
    DNSZoneWithRecords,
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
