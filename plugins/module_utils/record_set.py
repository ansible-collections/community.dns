# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from .record import format_ttl as _format_ttl


class DNSRecordSet(object):
    def __init__(self):
        self.id = None
        self.type = None
        self.prefix = None
        self.ttl = None
        self.records = []
        self.extra = {}

    def clone(self):
        result = DNSRecordSet()
        result.id = self.id
        result.type = self.type
        result.prefix = self.prefix
        result.records = [record.clone() for record in self.records]
        result.ttl = self.ttl
        result.extra = dict(self.extra)
        return result

    def __str__(self):
        data = []
        if self.id:
            data.append('id: {0}'.format(self.id))
        data.append('type: {0}'.format(self.type))
        if self.prefix:
            data.append('prefix: "{0}"'.format(self.prefix))
        else:
            data.append('prefix: (none)')
        data.append('ttl: {0}'.format(_format_ttl(self.ttl)))
        data.append('records: [{0}]'.format(', '.join([str(record) for record in self.records])))
        if self.extra:
            data.append('extra: {0}'.format(self.extra))
        return 'DNSRecordSet(' + ', '.join(data) + ')'

    def __repr__(self):
        return self.__str__()


def format_record_set_for_output(record_set, record_name, prefix=None, record_converter=None):
    entry = {
        'prefix': prefix or '',
        'type': record_set.type,
        'ttl': record_set.ttl,
        'value': sorted((record.target for record in record_set.records)),
    }
    if record_converter:
        entry['value'] = record_converter.process_values_to_user(entry['type'], entry['value'])
    if record_name is not None:
        entry['record'] = record_name
    return entry
