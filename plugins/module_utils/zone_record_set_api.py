# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import abc

from ansible_collections.community.dns.plugins.module_utils._six import (
    add_metaclass,
)
from ansible_collections.community.dns.plugins.module_utils.zone import (
    DNSZoneWithRecordSets,
)
from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (  # pylint: disable=unused-import
    NOT_PROVIDED,
    DNSAPIAuthenticationError,
    DNSAPIError,
    NotProvidedType,
)


@add_metaclass(abc.ABCMeta)
class ZoneRecordSetAPI(object):
    @abc.abstractmethod
    def get_zone_by_name(self, name):
        """
        Given a zone name, return the zone contents if found.

        @param name: The zone name (string)
        @return The zone information (DNSZone), or None if not found
        """

    @abc.abstractmethod
    def get_zone_by_id(self, zone_id):
        """
        Given a zone ID, return the zone contents if found.

        @param zone_id: The zone ID
        @return The zone information (DNSZone), or None if not found
        """

    def get_zone_with_record_sets_by_name(self, name, prefix=NOT_PROVIDED, record_type=NOT_PROVIDED):
        """
        Given a zone name, return the zone contents with records if found.

        @param name: The zone name (string)
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return The zone information with record sets (DNSZoneWithRecordSets), or None if not found
        """
        zone = self.get_zone_by_name(name)
        if zone is None:
            return None
        return DNSZoneWithRecordSets(zone, self.get_zone_record_sets(zone.id, prefix=prefix, record_type=record_type))

    def get_zone_with_record_sets_by_id(self, zone_id, prefix=NOT_PROVIDED, record_type=NOT_PROVIDED):
        """
        Given a zone ID, return the zone contents with records if found.

        @param id: The zone ID
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return The zone information with record sets (DNSZoneWithRecordSets), or None if not found
        """
        zone = self.get_zone_by_id(zone_id)
        if zone is None:
            return None
        return DNSZoneWithRecordSets(zone, self.get_zone_record_sets(zone.id, prefix=prefix, record_type=record_type))

    @abc.abstractmethod
    def get_zone_record_sets(self, zone_id, prefix=NOT_PROVIDED, record_type=NOT_PROVIDED):
        """
        Given a zone ID, return a list of record sets, optionally filtered by the provided criteria.

        @param zone_id: The zone ID
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return A list of DNSrecordSet objects, or None if zone was not found
        """

    @abc.abstractmethod
    def add_record_set(self, zone_id, record_set):
        """
        Adds a new record set to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record set (DNSRecordSet)
        @return The created DNS record set (DNSRecordSet)
        """

    @abc.abstractmethod
    def update_record_set(self, zone_id, record_set, updated_records=True, updated_ttl=True):
        """
        Update a record set.

        @param zone_id: The zone ID
        @param record_set: The DNS record set (DNSRecordSet)
        @param updated_records: Hint whether the values were updated.
        @param updated_ttl: Hint whether the values were updated.
        @return The DNS record set (DNSRecordSet)
        """

    @abc.abstractmethod
    def delete_record_set(self, zone_id, record_set):
        """
        Delete a record set.

        @param zone_id: The zone ID
        @param record_set: The DNS record set (DNSRecordSet)
        @return True in case of success (boolean)
        """

    def add_record_sets(self, record_sets_per_zone_id, stop_early_on_errors=True):
        """
        Add new record sets to an existing zone.

        @param record_sets_per_zone_id: Maps a zone ID to a list of DNS record sets (DNSRecordSet)
        @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                     This might only work on some APIs.
        @return A dictionary mapping zone IDs to lists of tuples ``(record_set, created, failed)``.
                Here ``created`` indicates whether the record set was created (``True``) or not (``False``).
                If it was created, ``record_set`` contains the record set ID and ``failed`` is ``None``.
                If it was not created, ``failed`` should be a ``DNSAPIError`` instance indicating why
                it was not created. It is possible that the API only creates record sets if all succeed,
                in that case ``failed`` can be ``None`` even though ``created`` is ``False``.
        """
        results_per_zone_id = {}
        for zone_id, record_sets in record_sets_per_zone_id.items():
            result = []
            results_per_zone_id[zone_id] = result
            for record_set in record_sets:
                try:
                    result.append((self.add_record_set(zone_id, record_set), True, None))
                except DNSAPIError as e:
                    result.append((record_set, False, e))
                    if stop_early_on_errors:
                        return results_per_zone_id
        return results_per_zone_id

    def update_record_sets(self, record_sets_per_zone_id, stop_early_on_errors=True):
        """
        Update multiple record sets.

        @param record_sets_per_zone_id: Maps a zone ID to a list of tuples
                                        (record_set, updated_records, updated_ttl)
                                        of type (DNSRecordSet, bool, bool).
        @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                     This might only work on some APIs.
        @return A dictionary mapping zone IDs to lists of tuples ``(record_set, updated, failed)``.
                Here ``updated`` indicates whether the record set was updated (``True``) or not (``False``).
                If it was not updated, ``failed`` should be a ``DNSAPIError`` instance. If it was
                updated, ``failed`` should be ``None``.  It is possible that the API only updates
                record sets if all succeed, in that case ``failed`` can be ``None`` even though
                ``updated`` is ``False``.
        """
        results_per_zone_id = {}
        for zone_id, record_sets in record_sets_per_zone_id.items():
            result = []
            results_per_zone_id[zone_id] = result
            for record_set, updated_records, updated_ttl in record_sets:
                try:
                    result.append((self.update_record_set(zone_id, record_set, updated_records=updated_records, updated_ttl=updated_ttl), True, None))
                except DNSAPIError as e:
                    result.append((record_set, False, e))
                    if stop_early_on_errors:
                        return results_per_zone_id
        return results_per_zone_id

    def delete_record_sets(self, record_sets_per_zone_id, stop_early_on_errors=True):
        """
        Delete multiple record_sets.

        @param record_sets_per_zone_id: Maps a zone ID to a list of DNS record sets (DNSRecordSet)
        @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                     This might only work on some APIs.
        @return A dictionary mapping zone IDs to lists of tuples ``(record_set, deleted, failed)``.
                In case ``record_set`` was deleted or not deleted, ``deleted`` is ``True``
                respectively ``False``, and ``failed`` is ``None``. In case an error happened
                while deleting, ``deleted`` is ``False`` and ``failed`` is a ``DNSAPIError``
                instance hopefully providing information on the error.
        """
        results_per_zone_id = {}
        for zone_id, record_sets in record_sets_per_zone_id.items():
            result = []
            results_per_zone_id[zone_id] = result
            for record_set in record_sets:
                try:
                    result.append((record_set, self.delete_record_set(zone_id, record_set), None))
                except DNSAPIError as e:
                    result.append((record_set, False, e))
                    if stop_early_on_errors:
                        return results_per_zone_id
        return results_per_zone_id


def filter_record_sets(record_sets, prefix=NOT_PROVIDED, record_type=NOT_PROVIDED):
    """
    Given a list of record sets, returns a filtered subset.

    @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                   the special constant NOT_PROVIDED indicates that we are not filtering.
    @param record_type: The record type to filter for, if provided
    @return The list of record sets matching the provided filters.
    """
    if prefix is not NOT_PROVIDED:
        record_sets = [record_set for record_set in record_sets if record_set.prefix == prefix]
    if record_type is not NOT_PROVIDED:
        record_sets = [record_set for record_set in record_sets if record_set.type == record_type]
    return record_sets
