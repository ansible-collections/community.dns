# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
)


def bulk_apply_changes(api, zone_id,
                       records_to_delete=None,
                       records_to_change=None,
                       records_to_create=None,
                       bulk_threshold=2,
                       stop_early_on_errors=True):
    """
    Update multiple records. If an operation failed, raise a DNSAPIException.

    @param api: A ZoneRecordAPI instance
    @param zone_id: Zone ID to apply changes to
    @param records_to_delete: Optional list of DNS records to delete (DNSRecord)
    @param records_to_change: Optional list of DNS records to change (DNSRecord)
    @param records_to_create: Optional list of DNS records to create (DNSRecord)
    @param bulk_threshold: Minimum number of changes for using the bulk API instead of the regular API
    @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                 This might only work on some APIs.
    @return A tuple (changed, errors) where ``changed`` is a boolean which indicates whether a change
            was made, and ``errors`` is a list of ``DNSAPIError`` instances for the errors occured.
    """
    records_to_delete = records_to_delete or []
    records_to_change = records_to_change or []
    records_to_create = records_to_create or []

    has_change = False
    errors = []

    # Delete records
    if len(records_to_delete) >= bulk_threshold:
        results = api.delete_records({zone_id: records_to_delete}, stop_early_on_errors=stop_early_on_errors)
        result = results.get(zone_id) or []
        for record, deleted, failed in result:
            has_change |= deleted
            if failed is not None:
                errors.append(failed)
        if errors and stop_early_on_errors:
            return has_change, errors
    else:
        for record in records_to_delete:
            try:
                has_change |= api.delete_record(zone_id, record)
            except DNSAPIError as e:
                errors.append(e)
                if stop_early_on_errors:
                    return has_change, errors

    # Change records
    if len(records_to_change) >= bulk_threshold:
        results = api.update_records({zone_id: records_to_change}, stop_early_on_errors=stop_early_on_errors)
        result = results.get(zone_id) or []
        for record, changed, failed in result:
            has_change |= changed
            if failed is not None:
                errors.append(failed)
        if errors and stop_early_on_errors:
            return has_change, errors
    else:
        for record in records_to_change:
            try:
                api.update_record(zone_id, record)
                has_change = True
            except DNSAPIError as e:
                errors.append(e)
                if stop_early_on_errors:
                    return has_change, errors

    # Create records
    if len(records_to_create) >= bulk_threshold:
        results = api.add_records({zone_id: records_to_create}, stop_early_on_errors=stop_early_on_errors)
        result = results.get(zone_id) or []
        for record, created, failed in result:
            has_change |= created
            if failed is not None:
                errors.append(failed)
        if errors and stop_early_on_errors:
            return has_change, errors
    else:
        for record in records_to_create:
            try:
                api.add_record(zone_id, record)
                has_change = True
            except DNSAPIError as e:
                errors.append(e)
                if stop_early_on_errors:
                    return has_change, errors

    return has_change, errors
