# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys

from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
)

if sys.version_info >= (3, 6):
    import typing

    if typing.TYPE_CHECKING:
        from .provider import ProviderInformation  # pragma: no cover
        from .record_set import DNSRecordSet  # pragma: no cover
        from .zone_record_set_api import ZoneRecordSetAPI  # pragma: no cover


def bulk_apply_changes(
    api,  # type: ZoneRecordSetAPI
    provider_information,  # type: ProviderInformation
    options,  # TODO type
    zone_id,  # type: str
    record_sets_to_delete=None,  # type: list[DNSRecordSet] | None
    record_sets_to_change=None,  # type: list[tuple[DNSRecordSet, bool, bool]] | None
    record_sets_to_create=None,  # type: list[DNSRecordSet] | None
    stop_early_on_errors=True,  # type: bool
):  # type: (...) -> tuple[bool, list[tuple[typing.Literal["delete", "change", "create"], DNSRecordSet, DNSAPIError]], dict[str, list[DNSRecordSet]]]
    """
    Update multiple records. If an operation failed, raise a DNSAPIException.

    @param api: A ZoneRecordSetAPI instance
    @param provider_information: A ProviderInformation object.
    @param options: A object compatible with ModuleOptionProvider that gives access to the module/plugin
                    options.
    @param zone_id: Zone ID to apply changes to
    @param record_sets_to_delete: Optional list of DNS records to delete (DNSRecordSet)
    @param record_sets_to_change: Optional list of tuples (DNS records, value changed, TTL changed) to change
                                  (tuple[DNSRecordSet, bool, bool])
    @param record_sets_to_create: Optional list of DNS records to create (DNSRecordSet)
    @param bulk_threshold: Minimum number of changes for using the bulk API instead of the regular API
    @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                 This might only work on some APIs.
    @return A tuple (changed, errors, success) where ``changed`` is a boolean which indicates whether a
            change was made, ``errors`` is a list of tuples (what, record_set, err) for the errors occurred,
            and ``success`` is a dictionary with three lists ``success['deleted']``,
            ``success['changed']`` and ``success['created']``, which list all record sets that were deleted,
            changed and created, respectively.
    """
    record_sets_to_delete = record_sets_to_delete or []
    record_sets_to_change = record_sets_to_change or []
    record_sets_to_create = record_sets_to_create or []

    has_change = False
    errors = []  # type: list[tuple[typing.Literal["delete", "change", "create"], DNSRecordSet, DNSAPIError]]

    bulk_threshold = 2
    if provider_information.supports_bulk_actions():
        bulk_threshold = options.get_option('bulk_operation_threshold')

    success = {
        'deleted': [],
        'changed': [],
        'created': [],
    }  # type: dict[str, list[DNSRecordSet]]

    # Delete record sets
    if len(record_sets_to_delete) >= bulk_threshold:
        results = api.delete_record_sets({zone_id: record_sets_to_delete}, stop_early_on_errors=stop_early_on_errors)
        result = results.get(zone_id) or []
        for record_set, deleted, failed in result:
            has_change |= deleted
            if failed is not None:
                errors.append(("delete", record_set, failed))
            if deleted:
                success['deleted'].append(record_set)
        if errors and stop_early_on_errors:
            return has_change, errors, success
    else:
        for record_set in record_sets_to_delete:
            try:
                deleted = api.delete_record_set(zone_id, record_set)
                has_change |= deleted
                if deleted:
                    success['deleted'].append(record_set)
            except DNSAPIError as e:
                errors.append(("delete", record_set, e))
                if stop_early_on_errors:
                    return has_change, errors, success

    # Change record sets
    if len(record_sets_to_change) >= bulk_threshold:
        results = api.update_record_sets({zone_id: record_sets_to_change}, stop_early_on_errors=stop_early_on_errors)
        result = results.get(zone_id) or []
        for record_set, changed, failed in result:
            has_change |= changed
            if failed is not None:
                errors.append(("change", record_set, failed))
            if changed:
                success['changed'].append(record_set)
        if errors and stop_early_on_errors:
            return has_change, errors, success
    else:
        for record_set, updated_value, updated_ttl in record_sets_to_change:
            try:
                record_set = api.update_record_set(zone_id, record_set, updated_records=updated_value, updated_ttl=updated_ttl)
                has_change = True
                success['changed'].append(record_set)
            except DNSAPIError as e:
                errors.append(("change", record_set, e))
                if stop_early_on_errors:
                    return has_change, errors, success

    # Create record sets
    if len(record_sets_to_create) >= bulk_threshold:
        results = api.add_record_sets({zone_id: record_sets_to_create}, stop_early_on_errors=stop_early_on_errors)
        result = results.get(zone_id) or []
        for record_set, created, failed in result:
            has_change |= created
            if failed is not None:
                errors.append(("create", record_set, failed))
            if created:
                success['created'].append(record_set)
        if errors and stop_early_on_errors:
            return has_change, errors, success
    else:
        for record_set in record_sets_to_create:
            try:
                record_set = api.add_record_set(zone_id, record_set)
                has_change = True
                success['created'].append(record_set)
            except DNSAPIError as e:
                errors.append(("create", record_set, e))
                if stop_early_on_errors:
                    return has_change, errors, success

    return has_change, errors, success
