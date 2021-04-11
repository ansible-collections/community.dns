# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.hosttech.record import (
    DNSRecord,
    format_ttl,
)


class DNSZone(object):
    def __init__(self, name):
        self.id = None
        self.name = name
        self.email = None
        self.ttl = 10800  # 3 * 60 * 60
        self.nameserver = None
        self.serial = None
        self.template = None
        self.records = []

    @staticmethod
    def create_from_encoding(source):
        result = DNSZone(source['name'])
        result.id = source['id']
        result.email = source.get('email')
        result.ttl = int(source['ttl'])
        result.nameserver = source['nameserver']
        result.serial = source['serial']
        result.template = source.get('template')
        result.records = [DNSRecord.create_from_encoding(record) for record in source['records']]
        return result

    @staticmethod
    def create_from_json(source):
        result = DNSZone(source['name'])
        result.id = source['id']
        result.email = source.get('email')
        result.ttl = int(source['ttl'])
        result.nameserver = source['nameserver']
        result.serial = None
        result.template = None
        result.records = [DNSRecord.create_from_json(record, zone=source['name']) for record in source['records']]
        return result

    def encode(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'ttl': self.ttl,
            'nameserver': self.nameserver,
            'serial': self.serial,
            'template': self.template,
            'records': [record.encode(include_ids=True) for record in self.records],
        }

    def __str__(self):
        data = []
        if self.id:
            data.append('id: {0}'.format(self.id))
        data.append('name: {0}'.format(self.name))
        if self.email:
            data.append('email: {0}'.format(self.email))
        data.append('ttl: {0}'.format(format_ttl(self.ttl)))
        if self.nameserver:
            data.append('nameserver: {0}'.format(self.nameserver))
        if self.serial:
            data.append('serial: {0}'.format(self.serial))
        if self.template:
            data.append('template: {0}'.format(self.template))
        for record in self.records:
            data.append('record: {0}'.format(str(record)))
        return 'DNSZone(\n' + ',\n'.join(['  ' + line for line in data]) + '\n)'

    def __repr__(self):
        return 'DNSZone.create_from_encoding({0!r})'.format(self.encode())
