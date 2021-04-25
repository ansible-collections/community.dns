# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import abc

from ansible.module_utils import six


class DNSAPIError(Exception):
    pass


class DNSAPIAuthenticationError(DNSAPIError):
    pass


@six.add_metaclass(abc.ABCMeta)
class ZoneRecordAPI(object):
    @abc.abstractmethod
    def get_zone_by_name(self, name):
        """
        Given a zone name, return the zone contents if found.

        @param name: The zone name (string)
        @return The zone information (DNSZone), or None if not found
        """

    @abc.abstractmethod
    def get_zone_with_records_by_name(self, name):
        """
        Given a zone name, return the zone contents with records if found.

        @param name: The zone name (string)
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """

    @abc.abstractmethod
    def get_zone_with_records_by_id(self, id):
        """
        Given a zone ID, return the zone contents with records if found.

        @param id: The zone ID
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """

    @abc.abstractmethod
    def add_record(self, zone_id, record):
        """
        Adds a new record to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """

    @abc.abstractmethod
    def update_record(self, zone_id, record):
        """
        Update a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """

    @abc.abstractmethod
    def delete_record(self, zone_id, record):
        """
        Delete a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
