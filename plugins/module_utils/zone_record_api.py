# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import abc

from ansible.module_utils import six

from ansible_collections.community.dns.plugins.module_utils.zone import (
    DNSZoneWithRecords,
)


class DNSAPIError(Exception):
    pass


class DNSAPIAuthenticationError(DNSAPIError):
    pass


class NotProvidedType(object):
    pass


NOT_PROVIDED = NotProvidedType()


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
    def get_zone_by_id(self, id):
        """
        Given a zone ID, return the zone contents if found.

        @param id: The zone ID
        @return The zone information (DNSZone), or None if not found
        """

    def get_zone_with_records_by_name(self, name, prefix=NOT_PROVIDED, record_type=NOT_PROVIDED):
        """
        Given a zone name, return the zone contents with records if found.

        @param name: The zone name (string)
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """
        zone = self.get_zone_by_name(name)
        if zone is None:
            return None
        return DNSZoneWithRecords(zone, self.get_zone_records(zone.id, prefix=prefix, record_type=record_type))

    def get_zone_with_records_by_id(self, id, prefix=NOT_PROVIDED, record_type=NOT_PROVIDED):
        """
        Given a zone ID, return the zone contents with records if found.

        @param id: The zone ID
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """
        zone = self.get_zone_by_id(id)
        if zone is None:
            return None
        return DNSZoneWithRecords(zone, self.get_zone_records(zone.id, prefix=prefix, record_type=record_type))

    @abc.abstractmethod
    def get_zone_records(self, zone_id, prefix=NOT_PROVIDED, record_type=NOT_PROVIDED):
        """
        Given a zone ID, return a list of records, optionally filtered by the provided criteria.

        @param zone_id: The zone ID
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return A list of DNSrecord objects, or None if zone was not found
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


def filter_records(records, prefix=NOT_PROVIDED, record_type=NOT_PROVIDED):
    """
    Given a list of records, returns a filtered subset.

    @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                   the special constant NOT_PROVIDED indicates that we are not filtering.
    @param record_type: The record type to filter for, if provided
    @return The list of records matching the provided filters.
    """
    if prefix is not NOT_PROVIDED:
        records = [record for record in records if record.prefix == prefix]
    if record_type is not NOT_PROVIDED:
        records = [record for record in records if record.type == record_type]
    return records
