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
