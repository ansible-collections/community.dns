# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


def format_ttl(ttl):
    sec = ttl % 60
    ttl //= 60
    min = ttl % 60
    ttl //= 60
    h = ttl
    result = []
    if h:
        result.append('{0}h'.format(h))
    if min:
        result.append('{0}m'.format(min))
    if sec:
        result.append('{0}s'.format(sec))
    return ' '.join(result)


class DNSRecord(object):
    def __init__(self):
        self.id = None
        self.zone = None
        self.type = None
        self.prefix = None
        self.target = None
        self.ttl = 86400  # 24 * 60 * 60
        self.priority = None

    @staticmethod
    def create_from_encoding(source, type=None):
        result = DNSRecord()
        result.id = source['id']
        result.zone = source['zone']
        result.type = source.get('type', type)
        result.prefix = source.get('prefix')
        result.target = source.get('target')
        result.ttl = int(source['ttl']) if source['ttl'] is not None else None
        result.priority = source.get('priority')
        return result

    @staticmethod
    def create_from_json(source, zone=None, type=None):
        result = DNSRecord()
        result.id = source['id']
        result.zone = zone
        result.type = source.get('type', type)
        result.ttl = int(source['ttl']) if source['ttl'] is not None else None

        name = source.get('name')
        target = None
        priority = None
        if result.type == 'A':
            target = source['ipv4']
        elif result.type == 'AAAA':
            target = source['ipv6']
        elif result.type == 'CAA':
            target = '{0} {1} {2}'.format(source['flag'], source['tag'], source['value'])
        elif result.type == 'CNAME':
            target = source['cname']
        elif result.type == 'MX':
            priority = source['pref']
            target = source['name']
            name = source['ownername']
        elif result.type == 'NS':
            name = source['ownername']
            target = source['targetname']
        elif result.type == 'PTR':
            name = ''
            target = '{0} {1}'.format(source['origin'], source['name'])
        elif result.type == 'SRV':
            name = source['service']
            target = '{0} {1} {2} {3}'.format(source['priority'], source['weight'], source['port'], source['target'])
            # priority = source['priority']
        elif result.type == 'TXT':
            target = source['text']
        elif result.type == 'TLSA':
            target = source['text']

        result.prefix = name
        result.target = target
        result.priority = priority
        return result

    def encode(self, include_ids=False):
        result = {
            'type': self.type,
            'prefix': self.prefix,
            'target': self.target,
            'ttl': self.ttl,
            'priority': self.priority,
        }
        if include_ids:
            result['id'] = self.id
            result['zone'] = self.zone
        return result

    def clone(self):
        return DNSRecord.create_from_encoding(self.encode(include_ids=True))

    def __str__(self):
        data = []
        if self.id:
            data.append('id: {0}'.format(self.id))
        if self.zone:
            data.append('zone: {0}'.format(self.zone))
        data.append('type: {0}'.format(self.type))
        if self.prefix:
            data.append('prefix: "{0}"'.format(self.prefix))
        else:
            data.append('prefix: (none)')
        data.append('target: "{0}"'.format(self.target))
        data.append('ttl: {0}'.format(format_ttl(self.ttl)))
        if self.priority:
            data.append('priority: {0}'.format(self.priority))
        return 'DNSRecord(' + ', '.join(data) + ')'

    def __repr__(self):
        return 'DNSRecord.create_from_encoding({0!r})'.format(self.encode(include_ids=True))


def format_records_for_output(records, record_name):
    ttls = set([record.ttl for record in records]),
    entry = {
        'record': record_name,
        'type': min([record.type for record in records]) if records else None,
        'ttl': min(*list(ttls)) if records else None,
        'value': [record.target for record in records],
    }
    if len(ttls) > 1:
        entry['ttls'] = ttls
    return entry
