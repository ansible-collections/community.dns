# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# This module_utils is PRIVATE and should only be used by this collection. Breaking changes can occur any time.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import traceback

from ansible.module_utils.common.text.converters import to_text

from ansible_collections.community.dns.plugins.module_utils.argspec import (
    ArgumentSpec,
    ModuleOptionProvider,
)
from ansible_collections.community.dns.plugins.module_utils.conversion.base import (
    DNSConversionError,
)
from ansible_collections.community.dns.plugins.module_utils.conversion.converter import (
    RecordConverter,
)
from ansible_collections.community.dns.plugins.module_utils.options import (
    create_bulk_operations_argspec,
    create_record_transformation_argspec,
)
from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
    format_records_for_output,
)
from ansible_collections.community.dns.plugins.module_utils.record_set import (
    DNSRecordSet,
    format_record_set_for_output,
)
from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    NOT_PROVIDED,
    DNSAPIAuthenticationError,
    DNSAPIError,
    ZoneRecordAPI,
    filter_records,
)
from ansible_collections.community.dns.plugins.module_utils.zone_record_helpers import (
    bulk_apply_changes,
)
from ansible_collections.community.dns.plugins.module_utils.zone_record_set_api import (
    filter_record_sets,
)

from ._utils import get_prefix, normalize_dns_name


def create_module_argument_spec(provider_information):
    return ArgumentSpec(
        argument_spec={
            'state': {'type': 'str', 'choices': ['present', 'absent'], 'required': True},
            'zone_name': {'type': 'str', 'aliases': ['zone']},
            'zone_id': {'type': provider_information.get_zone_id_type()},
            'record': {'type': 'str'},
            'prefix': {'type': 'str'},
            'ttl': {'type': 'int', 'default': provider_information.get_record_default_ttl()},
            'type': {'choices': provider_information.get_supported_record_types(), 'required': True},
            'value': {'type': 'list', 'elements': 'str'},
            'on_existing': {'type': 'str', 'default': 'replace', 'choices': ['replace', 'keep_and_fail', 'keep_and_warn', 'keep']},
        },
        required_one_of=[
            ('zone_name', 'zone_id'),
            ('record', 'prefix'),
        ],
        mutually_exclusive=[
            ('zone_name', 'zone_id'),
            ('record', 'prefix'),
        ],
        required_if=[
            ('state', 'present', ['value']),
            ('on_existing', 'keep_and_fail', ['value']),
            ('on_existing', 'keep_and_warn', ['value']),
            ('on_existing', 'keep', ['value']),
        ],
    ).merge(create_bulk_operations_argspec(provider_information)).merge(create_record_transformation_argspec())


def _run_module_record_api(option_provider, module, provider_information, record_converter, record_in, prefix_in, type_in, api):
    # Get zone information
    if module.params.get('zone_name') is not None:
        zone_in = normalize_dns_name(module.params.get('zone_name'))
        record_in, prefix = get_prefix(
            normalized_zone=zone_in, normalized_record=record_in, prefix=prefix_in, provider_information=provider_information)
        zone = api.get_zone_with_records_by_name(zone_in, prefix=prefix, record_type=type_in)
        if zone is None:
            module.fail_json(msg='Zone not found')
        zone_id = zone.zone.id
        records = zone.records
    elif record_in is not None:
        zone = api.get_zone_with_records_by_id(
            module.params.get('zone_id'),
            record_type=type_in,
            prefix=provider_information.normalize_prefix(prefix_in) if prefix_in is not None else NOT_PROVIDED,
        )
        if zone is None:
            module.fail_json(msg='Zone not found')
        zone_in = normalize_dns_name(zone.zone.name)
        record_in, prefix = get_prefix(
            normalized_zone=zone_in, normalized_record=record_in, prefix=prefix_in, provider_information=provider_information)
        zone_id = zone.zone.id
        records = zone.records
    else:
        zone_id = module.params.get('zone_id')
        prefix = provider_information.normalize_prefix(prefix_in)
        records = api.get_zone_records(
            zone_id,
            record_type=type_in,
            prefix=prefix,
        )
        if records is None:
            module.fail_json(msg='Zone not found')
        zone_in = None
        record_in = None

    # Find matching records
    records = filter_records(records, prefix=prefix)
    record_converter.process_multiple_from_api(records)

    # Parse records
    values = []
    value_in = module.params.get('value') or []
    value_in = record_converter.process_values_from_user(type_in, value_in)
    values = value_in[:]

    # Compare records
    ttl_in = module.params.get('ttl')
    mismatch = False
    mismatch_records = []
    keep_records = []
    for record in records:
        if record.ttl != ttl_in:
            mismatch = True
            mismatch_records.append(record)
            continue
        val = record.target
        if val in values:
            values.remove(val)
            keep_records.append(record)
        else:
            mismatch = True
            mismatch_records.append(record)
            continue
    if values and module.params.get('state') == 'present':
        mismatch = True

    before = [record.clone() for record in records]
    after = keep_records[:]

    # Determine what to do
    to_create = []
    to_delete = []
    to_change = []
    on_existing = module.params.get('on_existing')
    no_mod = False
    if module.params.get('state') == 'present':
        if records and mismatch:
            # Mismatch: user wants to overwrite?
            if on_existing == 'replace':
                to_delete.extend(mismatch_records)
            elif on_existing == 'keep_and_fail':
                module.fail_json(msg="Record already exists with different value. Set on_existing=replace to replace it")
            elif on_existing == 'keep_and_warn':
                module.warn("Record already exists with different value. Set on_existing=replace to replace it")
                no_mod = True
            else:  # on_existing == 'keep'
                no_mod = True
        if no_mod:
            after = before[:]
        else:
            for target in values:
                if to_delete:
                    # If there's a record to delete, change it to new record
                    record = to_delete.pop()
                    to_change.append(record)
                else:
                    # Otherwise create new record
                    record = DNSRecord()
                    to_create.append(record)
                record.prefix = prefix
                record.type = type_in
                record.ttl = ttl_in
                record.target = target
                after.append(record)
    if module.params.get('state') == 'absent':
        if mismatch:
            # Mismatch: user wants to overwrite?
            if on_existing == 'replace':
                no_mod = False
            elif on_existing == 'keep_and_fail':
                module.fail_json(msg="Record already exists with different value. Set on_existing=replace to remove it")
            elif on_existing == 'keep_and_warn':
                module.warn("Record already exists with different value. Set on_existing=replace to remove it")
                no_mod = True
            else:  # on_existing == 'keep'
                no_mod = True
        if no_mod:
            after = before[:]
        else:
            to_delete.extend(records)
            after = []

    # Compose result
    result = {
        'changed': False,
        'zone_id': zone_id,
    }

    # Determine whether there's something to do
    if to_create or to_delete or to_change:
        # Actually do something
        records_to_delete = record_converter.clone_multiple_to_api(to_delete)
        records_to_change = record_converter.clone_multiple_to_api(to_change)
        records_to_create = record_converter.clone_multiple_to_api(to_create)
        result['changed'] = True
        if not module.check_mode:
            dummy, errors, dummy2 = bulk_apply_changes(
                api,
                zone_id=zone_id,
                records_to_delete=records_to_delete,
                records_to_change=records_to_change,
                records_to_create=records_to_create,
                provider_information=provider_information,
                options=option_provider,
            )
            if errors:
                if len(errors) == 1:
                    raise errors[0]
                module.fail_json(
                    msg='Errors: {0}'.format('; '.join([str(e) for e in errors])),
                    errors=[str(e) for e in errors],
                )

    # Include diff information
    if module._diff:
        result['diff'] = {
            'before': (
                format_records_for_output(sorted(before, key=lambda record: record.target), record_in, prefix, record_converter=record_converter)
                if before else {}
            ),
            'after': (
                format_records_for_output(sorted(after, key=lambda record: record.target), record_in, prefix, record_converter=record_converter)
                if after else {}
            ),
        }

    module.exit_json(**result)


def _run_module_record_set_api(option_provider, module, provider_information, record_converter, record_in, prefix_in, type_in, api):
    # Get zone information
    if module.params.get('zone_name') is not None:
        zone_in = normalize_dns_name(module.params.get('zone_name'))
        record_in, prefix = get_prefix(
            normalized_zone=zone_in, normalized_record=record_in, prefix=prefix_in, provider_information=provider_information)
        zone = api.get_zone_with_record_sets_by_name(zone_in, prefix=prefix, record_type=type_in)
        if zone is None:
            module.fail_json(msg='Zone not found')
        zone_id = zone.zone.id
        record_sets = zone.record_sets
    elif record_in is not None:
        zone = api.get_zone_with_record_sets_by_id(
            module.params.get('zone_id'),
            record_type=type_in,
            prefix=provider_information.normalize_prefix(prefix_in) if prefix_in is not None else NOT_PROVIDED,
        )
        if zone is None:
            module.fail_json(msg='Zone not found')
        zone_in = normalize_dns_name(zone.zone.name)
        record_in, prefix = get_prefix(
            normalized_zone=zone_in, normalized_record=record_in, prefix=prefix_in, provider_information=provider_information)
        zone_id = zone.zone.id
        record_sets = zone.record_sets
    else:
        zone_id = module.params.get('zone_id')
        prefix = provider_information.normalize_prefix(prefix_in)
        record_sets = api.get_zone_record_sets(
            zone_id,
            record_type=type_in,
            prefix=prefix,
        )
        if record_sets is None:
            module.fail_json(msg='Zone not found')
        zone_in = None
        record_in = None

    # Find matching records
    record_sets = filter_record_sets(record_sets, prefix=prefix)
    if len(record_sets) > 1:
        module.fail_json(msg='Internal error: should have at most one record set, but got {0}'.format(len(record_sets)))  # pragma: no cover
    record_set = None
    if record_sets:
        record_set = record_sets[0]
        record_converter.process_set_from_api(record_set)

    # Parse records
    values = []
    value_in = module.params.get('value') or []
    value_in = record_converter.process_values_from_user(type_in, value_in)
    values = value_in[:]

    # Compare records
    ttl_in = module.params.get('ttl')
    mismatch_records = []
    keep_records = []
    if record_set:
        mismatch_ttl = record_set.ttl != ttl_in
        for record in record_set.records:
            val = record.target
            if val in values:
                values.remove(val)
                keep_records.append(record)
            else:
                mismatch_records.append(record)
    else:
        mismatch_ttl = False
        mismatch_records = []

    before = record_set.clone() if record_set else None
    after = before

    # Compose result
    result = {
        'changed': False,
        'zone_id': zone_id,
    }

    # Proceed
    on_existing = module.params.get('on_existing')
    no_mod = False
    if module.params.get('state') == 'present':
        mismatch_values = bool(mismatch_records or values)
        if (mismatch_values or mismatch_ttl) and record_set:
            # Mismatch: user wants to overwrite?
            if on_existing == 'replace':
                pass
            elif on_existing == 'keep_and_fail':
                module.fail_json(msg="Record already exists with different value. Set on_existing=replace to replace it")
            elif on_existing == 'keep_and_warn':
                module.warn("Record already exists with different value. Set on_existing=replace to replace it")
                no_mod = True
            else:  # on_existing == 'keep'
                no_mod = True
        if not no_mod:
            after = DNSRecordSet()
            after.type = type_in
            after.ttl = ttl_in
            after.prefix = prefix
            after.records.extend(keep_records)
            if record_set:
                after.id = record_set.id
                after.extra = record_set.extra.copy()
            for value in values:
                rec = DNSRecord()
                rec.type = type_in
                rec.ttl = ttl_in
                rec.prefix = prefix
                rec.target = value
                after.records.append(rec)
            if not after.records:
                after = None
                if record_set:
                    result['changed'] = True
                    if not module.check_mode:
                        api.delete_record_set(zone_id, record_set)
            elif mismatch_ttl or mismatch_values:
                result['changed'] = True
                if not module.check_mode:
                    new_record_set = record_converter.clone_set_to_api(after)
                    if record_set:
                        new_record_set.id = record_set.id
                        after = api.update_record_set(zone_id, new_record_set, updated_records=mismatch_values, updated_ttl=mismatch_ttl)
                    else:
                        after = api.add_record_set(zone_id, new_record_set)
                    after = record_converter.process_set_from_api(after)
    if module.params.get('state') == 'absent':
        mismatch_values = bool(mismatch_records)
        if (mismatch_values or mismatch_ttl) and record_set:
            # Mismatch: user wants to overwrite?
            if on_existing == 'replace':
                no_mod = False
            elif on_existing == 'keep_and_fail':
                module.fail_json(msg="Record already exists with different value. Set on_existing=replace to remove it")
            elif on_existing == 'keep_and_warn':
                module.warn("Record already exists with different value. Set on_existing=replace to remove it")
                no_mod = True
            else:  # on_existing == 'keep'
                no_mod = True
        if not no_mod:
            after = None
            if record_set:
                result['changed'] = True
                if not module.check_mode:
                    api.delete_record_set(zone_id, record_set)

    # Include diff information
    if module._diff:
        result['diff'] = {
            'before': (
                format_record_set_for_output(before, record_in, prefix, record_converter=record_converter)
                if before else {}
            ),
            'after': (
                format_record_set_for_output(after, record_in, prefix, record_converter=record_converter)
                if after else {}
            ),
        }

    module.exit_json(**result)


def run_module(module, create_api, provider_information):
    option_provider = ModuleOptionProvider(module)
    record_converter = RecordConverter(provider_information, option_provider)
    record_converter.emit_deprecations(module.deprecate)

    record_in = normalize_dns_name(module.params.get('record'))
    prefix_in = module.params.get('prefix')
    type_in = module.params.get('type')
    if type_in and type_in not in provider_information.get_supported_record_types():
        module.fail_json(msg='Invalid record type {type}'.format(type=type_in))

    try:
        # Create API
        api = create_api()

        if isinstance(api, ZoneRecordAPI):
            _run_module_record_api(option_provider, module, provider_information, record_converter, record_in, prefix_in, type_in, api)
        else:
            _run_module_record_set_api(option_provider, module, provider_information, record_converter, record_in, prefix_in, type_in, api)

    except DNSConversionError as e:
        module.fail_json(msg='Error while converting DNS values: {0}'.format(e.error_message), error=e.error_message, exception=traceback.format_exc())
    except DNSAPIAuthenticationError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=to_text(e), exception=traceback.format_exc())
    except DNSAPIError as e:
        module.fail_json(msg='Error: {0}'.format(e), error=to_text(e), exception=traceback.format_exc())
