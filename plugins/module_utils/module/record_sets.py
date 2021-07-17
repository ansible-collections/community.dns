# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This module_utils is PRIVATE and should only be used by this collection. Breaking changes can occur any time.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import traceback

from ansible_collections.community.dns.plugins.module_utils.argspec import (
    ArgumentSpec,
)

from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
    format_records_for_output,
)

from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
    DNSAPIAuthenticationError,
    NOT_PROVIDED,
    filter_records,
)

from ansible_collections.community.dns.plugins.module_utils.zone_record_helpers import (
    bulk_apply_changes,
)

from ._utils import (
    normalize_dns_name,
    get_prefix,
)


def create_module_argument_spec(zone_id_type, provider_information):
    return ArgumentSpec(
        argument_spec=dict(
            zone_name=dict(type='str', aliases=['zone']),
            zone_id=dict(type=zone_id_type),
            prune=dict(type='bool', default=False),
            record_sets=dict(
                type='list',
                elements='dict',
                required=True,
                aliases=['records'],
                options=dict(
                    record=dict(type='str'),
                    prefix=dict(type='str'),
                    ttl=dict(type='int', default=3600),
                    type=dict(choices=provider_information.get_supported_record_types(), required=True),
                    value=dict(type='list', elements='str'),
                    ignore=dict(type='bool', default=False),
                ),
                required_if=[('ignore', False, ['value'])],
                required_one_of=[('record', 'prefix')],
                mutually_exclusive=[('record', 'prefix')],
            ),
        ),
        required_one_of=[
            ('zone_name', 'zone_id'),
        ],
        mutually_exclusive=[
            ('zone_name', 'zone_id'),
        ],
    )


def run_module(module, create_api, provider_information):
    try:
        # Create API
        api = create_api()

        # Get zone information
        if module.params['zone_name'] is not None:
            zone_in = normalize_dns_name(module.params['zone_name'])
            zone = api.get_zone_with_records_by_name(zone_in)
            if zone is None:
                module.fail_json(msg='Zone not found')
            zone_id = zone.zone.id
            zone_records = zone.records
        else:
            zone = api.get_zone_with_records_by_id(module.params['zone_id'])
            if zone is None:
                module.fail_json(msg='Zone not found')
            zone_in = normalize_dns_name(zone.zone.name)
            zone_id = zone.zone.id
            zone_records = zone.records

        # Process parameters
        prune = module.params['prune']
        record_sets = module.params['record_sets']
        record_sets_dict = dict()
        for index, record_set in enumerate(record_sets):
            record_set = record_set.copy()
            record_name = record_set['record']
            prefix = record_set['prefix']
            record_name, prefix = get_prefix(
                normalized_zone=zone_in, normalized_record=record_name, prefix=prefix, provider_information=provider_information)
            record_set['record'] = record_name
            record_set['prefix'] = prefix
            key = (prefix, record_set['type'])
            if key in record_sets_dict:
                module.fail_json(msg='Found multiple sets for record {record} and type {type}: index #{i1} and #{i2}'.format(
                    record=record_name,
                    type=record_set['type'],
                    i1=record_sets_dict[key][0],
                    i2=index,
                ))
            record_sets_dict[key] = (index, record_set)

        # Group existing record sets
        existing_record_sets = dict()
        for record in zone_records:
            key = (record.prefix, record.type)
            if key not in existing_record_sets:
                existing_record_sets[key] = []
            existing_record_sets[key].append(record)

        # Data required for diff
        old_record_sets = dict([(k, [r.clone() for r in v]) for k, v in existing_record_sets.items()])
        new_record_sets = dict([(k, list(v)) for k, v in existing_record_sets.items()])

        # Create action lists
        to_create = []
        to_delete = []
        to_change = []
        for (prefix, record_type), (dummy, record_set) in record_sets_dict.items():
            key = (prefix, record_type)
            if key not in new_record_sets:
                new_record_sets[key] = []
            existing_recs = existing_record_sets.get(key, [])
            existing_record_sets[key] = []
            new_recs = new_record_sets[key]

            if record_set['ignore']:
                continue

            mismatch_recs = []
            keep_record_sets = []
            values = list(record_set['value'])
            for record in existing_recs:
                if record.ttl != record_set['ttl']:
                    mismatch_recs.append(record)
                    new_recs.remove(record)
                    continue
                if record.target in values:
                    values.remove(record.target)
                    keep_record_sets.append(record)
                else:
                    mismatch_recs.append(record)
                    new_recs.remove(record)

            for target in values:
                if mismatch_recs:
                    record = mismatch_recs.pop()
                    to_change.append(record)
                else:
                    # Otherwise create new record
                    record = DNSRecord()
                    to_create.append(record)
                record.prefix = prefix
                record.type = record_type
                record.ttl = record_set['ttl']
                record.target = target
                new_recs.append(record)

            to_delete.extend(mismatch_recs)

        # If pruning, remove superfluous record sets
        if prune:
            for key, record_set in existing_record_sets.items():
                to_delete.extend(record_set)
                for record in record_set:
                    new_record_sets[key].remove(record)

        # Apply changes
        result = dict(
            changed=False,
            zone_id=zone_id,
        )
        if to_create or to_delete or to_change:
            result['changed'] = True
            if not module.check_mode:
                actually_changed, errors = bulk_apply_changes(
                    api,
                    zone_id,
                    records_to_delete=to_delete,
                    records_to_change=to_change,
                    records_to_create=to_create,
                )
                if not actually_changed:
                    result['changed'] = False
                if errors:
                    if len(errors) == 1:
                        raise errors[0]
                    module.fail_json(
                        msg='Errors: {0}'.format('; '.join([str(e) for e in errors])),
                        errors=[str(e) for e in errors],
                    )

        # Include diff information
        if module._diff:
            def sort_items(dictionary):
                items = [
                    (zone_in if prefix is None else (prefix + '.' + zone_in), type, prefix, record_set)
                    for (prefix, type), record_set in dictionary.items() if len(record_set) > 0
                ]
                return sorted(items)

            result['diff'] = dict(
                before=dict(
                    record_sets=[
                        format_records_for_output(record_set, record_name, prefix)
                        for record_name, type, prefix, record_set in sort_items(old_record_sets)
                    ],
                ),
                after=dict(
                    record_sets=[
                        format_records_for_output(record_set, record_name, prefix)
                        for record_name, type, prefix, record_set in sort_items(new_record_sets)
                    ],
                ),
            )

        module.exit_json(**result)
    except DNSAPIAuthenticationError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=str(e), exception=traceback.format_exc())
    except DNSAPIError as e:
        module.fail_json(msg='Error: {0}'.format(e), error=str(e), exception=traceback.format_exc())
