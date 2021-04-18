# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class DNSZone(object):
    def __init__(self, name):
        self.id = None
        self.name = name

    def __str__(self):
        data = []
        if self.id is not None:
            data.append('id: {0}'.format(self.id))
        data.append('name: {0}'.format(self.name))
        return 'DNSZone(\n' + ',\n'.join(['  ' + line for line in data]) + '\n)'

    def __repr__(self):
        return self.__str__()


class DNSZoneWithRecords(object):
    def __init__(self, zone, records):
        self.zone = zone
        self.records = records

    def __str__(self):
        return '({0}, {1})'.format(self.zone, self.records)

    def __repr__(self):
        return 'DNSZoneWithRecords({0!r}, {1!r})'.format(self.zone, self.records)
