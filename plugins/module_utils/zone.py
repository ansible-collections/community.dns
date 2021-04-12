# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
    format_ttl,
)


class DNSZone(object):
    def __init__(self, name):
        self.id = None
        self.name = name
        self.records = []

    def __str__(self):
        data = []
        if self.id:
            data.append('id: {0}'.format(self.id))
        data.append('name: {0}'.format(self.name))
        for record in self.records:
            data.append('record: {0}'.format(str(record)))
        return 'DNSZone(\n' + ',\n'.join(['  ' + line for line in data]) + '\n)'
