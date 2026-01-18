# -*- coding: utf-8 -*-
# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

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

HETZNER_DEFAULT_ZONE_NO_LEGACY = {
    'id': '42',
    'created': '2021-07-09T11:18:37Z',
    'modified': '2021-07-09T11:18:37Z',
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

HETZNER_JSON_ZONE_LIST_RESULT_NO_LEGACY = {
    'zones': [
        HETZNER_DEFAULT_ZONE_NO_LEGACY,
    ],
}

HETZNER_JSON_ZONE_GET_RESULT_NO_LEGACY = {
    'zone': HETZNER_DEFAULT_ZONE_NO_LEGACY,
}

HETZNER_JSON_ZONE_RECORDS_GET_RESULT = {
    'records': HETZNER_JSON_DEFAULT_ENTRIES,
}

#############################################################################################
# New API

HETZNER_ZONE_NEW_JSON = {
    "zone": {
        "id": 42,
        "name": "example.com",
        "mode": "primary",
        "ttl": 3600,
        "labels": {},
        "primary_nameservers": [],
        "created": "2016-01-30T23:55:00Z",
        "protection": {
            "delete": False,
        },
        "status": "ok",
        "authoritative_nameservers": {
            "assigned": [
                "hydrogen.ns.hetzner.com.",
                "oxygen.ns.hetzner.com.",
                "helium.ns.hetzner.de.",
            ],
            "delegated": [
                "hydrogen.ns.hetzner.com.",
                "oxygen.ns.hetzner.com.",
                "helium.ns.hetzner.de.",
            ],
            "delegation_last_check": "2016-01-30T23:55:00Z",
            "delegation_status": "valid",
        },
        "record_count": 23,
        "registrar": "other",
    },
}

HETZNER_NEW_JSON_DEFAULT_ENTRIES = [
    {
        'id': '@/A',
        'type': 'A',
        'name': '@',
        "labels": {},
        "protection": {
            "change": False,
        },
        "records": [
            {
                'value': '1.2.3.4',
                "comment": "",
            },
        ],
        'ttl': 3600,
        'zone': '42',
    },
    {
        'id': '*/A',
        'type': 'A',
        'name': '*',
        "labels": {},
        "protection": {
            "change": False,
        },
        "records": [
            {
                'value': '1.2.3.5',
                "comment": "",
            },
        ],
        'ttl': 3600,
        'zone': '42',
    },
    {
        'id': '@/AAAA',
        'type': 'AAAA',
        'name': '@',
        "labels": {},
        "protection": {
            "change": False,
        },
        "records": [
            {
                'value': '2001:1:2::3',
                "comment": "",
            },
        ],
        'ttl': 3600,
        'zone': '42',
    },
    {
        'id': '*/AAAA',
        'type': 'AAAA',
        'name': '*',
        "labels": {},
        "protection": {
            "change": False,
        },
        "records": [
            {
                'value': '2001:1:2::4',
                "comment": "",
            },
        ],
        'ttl': 3600,
        'zone': '42',
    },
    {
        'id': '@/MX',
        'type': 'MX',
        'name': '@',
        "labels": {},
        "protection": {
            "change": False,
        },
        "records": [
            {
                'value': '10 example.com',
                "comment": "",
            },
        ],
        'ttl': 3600,
        'zone': '42',
    },
    {
        'id': '@/NS',
        'type': 'NS',
        'name': '@',
        "labels": {},
        "protection": {
            "change": False,
        },
        "records": [
            {
                'value': 'helium.ns.hetzner.de.',
                "comment": "",
            },
            {
                'value': 'hydrogen.ns.hetzner.com.',
                "comment": "",
            },
            {
                'value': 'oxygen.ns.hetzner.com.',
                "comment": "foo",
            },
        ],
        "ttl": None,
        'zone': '42',
    },
    {
        'id': '@/SOA',
        'type': 'SOA',
        'name': '@',
        "labels": {},
        "protection": {
            "change": False,
        },
        "records": [
            {
                'value': 'hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600',
                "comment": "",
            },
        ],
        "ttl": None,
        'zone': '42',
    },
    {
        'id': 'foo/TXT',
        'type': 'TXT',
        'name': 'foo',
        "labels": {},
        "protection": {
            "change": False,
        },
        "records": [
            {
                'value': u'"bär" " \\"with quotes\\"" " " "(use \\\\ to escape)"',
                "comment": "",
            },
        ],
        "ttl": None,
        'zone': '42',
    },
]


def get_hetzner_new_json_pagination_meta(total_entries, page=1, per_page=100, last_page=1):
    return {
        "pagination": {
            "last_page": last_page,
            "next_page": None if page == last_page else page + 1,
            "page": page,
            "per_page": per_page,
            "previous_page": None if page == 1 else page - 1,
            "total_entries": total_entries
        }
    }


def get_hetzner_new_json_records(name=None, record_type=None, update=None):
    rrsets = list(HETZNER_NEW_JSON_DEFAULT_ENTRIES)
    if record_type is not None:
        rrsets = [rrset for rrset in rrsets if rrset["type"] == record_type]
    if name is not None:
        rrsets = [rrset for rrset in rrsets if rrset["name"] == name]
    if update is not None:
        for index, rrset in enumerate(rrsets):
            upd = update.get((rrset['name'], rrset['type']))
            if upd is not None:
                rrsets[index] = upd
    return {
        "meta": get_hetzner_new_json_pagination_meta(len(rrsets)),
        "rrsets": rrsets,
    }
