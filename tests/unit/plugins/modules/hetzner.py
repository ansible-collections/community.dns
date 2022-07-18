# -*- coding: utf-8 -*-
# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


HETZNER_DEFAULT_ZONE = {
    'id': '42',
    'created': '2021-07-09T11:18:37Z',
    'modified': '2021-07-09T11:18:37Z',
    'legacy_dns_host': 'string',
    'legacy_ns': ['foo', 'bar'],
    'name': 'example.com',
    'ns': ['string'],
    'owner': 'Example',
    'paused': True,
    'permission': 'string',
    'project': 'string',
    'registrar': 'string',
    'status': 'verified',
    'ttl': 10800,
    'verified': '2021-07-09T11:18:37Z',
    'records_count': 0,
    'is_secondary_dns': True,
    'txt_verification': {
        'name': 'string',
        'token': 'string',
    },
}

HETZNER_JSON_DEFAULT_ENTRIES = [
    {
        'id': '125',
        'type': 'A',
        'name': '@',
        'value': '1.2.3.4',
        'ttl': 3600,
        'zone_id': '42',
        'created': '2021-07-09T11:18:37Z',
        'modified': '2021-07-09T11:18:37Z',
    },
    {
        'id': '126',
        'type': 'A',
        'name': '*',
        'value': '1.2.3.5',
        'ttl': 3600,
        'zone_id': '42',
        'created': '2021-07-09T11:18:37Z',
        'modified': '2021-07-09T11:18:37Z',
    },
    {
        'id': '127',
        'type': 'AAAA',
        'name': '@',
        'value': '2001:1:2::3',
        'ttl': 3600,
        'zone_id': '42',
        'created': '2021-07-09T11:18:37Z',
        'modified': '2021-07-09T11:18:37Z',
    },
    {
        'id': '128',
        'type': 'AAAA',
        'name': '*',
        'value': '2001:1:2::4',
        'ttl': 3600,
        'zone_id': '42',
        'created': '2021-07-09T11:18:37Z',
        'modified': '2021-07-09T11:18:37Z',
    },
    {
        'id': '129',
        'type': 'MX',
        'name': '@',
        'value': '10 example.com',
        'ttl': 3600,
        'zone_id': '42',
        'created': '2021-07-09T11:18:37Z',
        'modified': '2021-07-09T11:18:37Z',
    },
    {
        'id': '130',
        'type': 'NS',
        'name': '@',
        'value': 'helium.ns.hetzner.de.',
        'zone_id': '42',
        'created': '2021-07-09T11:18:37Z',
        'modified': '2021-07-09T11:18:37Z',
    },
    {
        'id': '131',
        'type': 'NS',
        'name': '@',
        'value': 'hydrogen.ns.hetzner.com.',
        'zone_id': '42',
        'created': '2021-07-09T11:18:37Z',
        'modified': '2021-07-09T11:18:37Z',
    },
    {
        'id': '132',
        'type': 'NS',
        'name': '@',
        'value': 'oxygen.ns.hetzner.com.',
        'zone_id': '42',
        'created': '2021-07-09T11:18:37Z',
        'modified': '2021-07-09T11:18:37Z',
    },
    {
        'id': '200',
        'type': 'SOA',
        'name': '@',
        'value': 'hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600',
        'zone_id': '42',
        'created': '2021-07-09T11:18:37Z',
        'modified': '2021-07-09T11:18:37Z',
    },
    {
        'id': '201',
        'type': 'TXT',
        'name': 'foo',
        'value': u'bär " \\"with quotes\\"" " " "(use \\\\ to escape)"',
        'zone_id': '42',
        'created': '2021-07-09T11:18:37Z',
        'modified': '2021-07-09T11:18:37Z',
    },
]

HETZNER_JSON_ZONE_LIST_RESULT = {
    'zones': [
        HETZNER_DEFAULT_ZONE,
    ],
}

HETZNER_JSON_ZONE_GET_RESULT = {
    'zone': HETZNER_DEFAULT_ZONE,
}

HETZNER_JSON_ZONE_RECORDS_GET_RESULT = {
    'records': HETZNER_JSON_DEFAULT_ENTRIES,
}
