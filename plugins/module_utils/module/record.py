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

from ._utils import (
    normalize_dns_name,
    get_prefix,
)


def create_module_argument_spec(zone_id_type='str', record_types=None):
    if record_types is None:
        record_types = ['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA']
    return ArgumentSpec(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent'], required=True),
            zone=dict(type='str'),
            zone_id=dict(type=zone_id_type),
            record=dict(type='str'),
            prefix=dict(type='str'),
            ttl=dict(type='int', default=3600),
            type=dict(choices=record_types, required=True),
            value=dict(required=True, type='list', elements='str'),
            overwrite=dict(default=False, type='bool'),
        ),
        required_one_of=[
            ('zone', 'zone_id'),
            ('record', 'prefix'),
        ],
        mutually_exclusive=[
            ('zone', 'zone_id'),
            ('record', 'prefix'),
        ],
    )


def run_module(module, create_api):
    record_in = normalize_dns_name(module.params.get('record'))
    prefix_in = module.params.get('prefix')
    type_in = module.params.get('type')
    try:
        # Create API
        api = create_api()

        # Get zone information
        if module.params.get('zone') is not None:
            zone_in = normalize_dns_name(module.params.get('zone'))
            record_in, prefix = get_prefix(normalized_zone=zone_in, normalized_record=record_in, prefix=prefix_in)
            zone = api.get_zone_with_records_by_name(zone_in, prefix=prefix, record_type=type_in)
            if zone is None:
                module.fail_json(msg='Zone not found')
            zone_id = zone.zone.id
            records = zone.records
        elif record_in is not None:
            zone = api.get_zone_with_records_by_id(
                module.params.get('zone_id'),
                record_type=type_in,
                prefix=(prefix_in or None) if prefix_in is not None else NOT_PROVIDED,
            )
            if zone is None:
                module.fail_json(msg='Zone not found')
            zone_in = normalize_dns_name(zone.zone.name)
            record_in, prefix = get_prefix(normalized_zone=zone_in, normalized_record=record_in, prefix=prefix_in)
            zone_id = zone.zone.id
            records = zone.records
        else:
            zone_id = module.params.get('zone_id')
            prefix = prefix_in or None
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

        # Parse records
        values = []
        value_in = module.params.get('value')
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
        if values:
            mismatch = True

        before = [record.clone() for record in records]
        after = keep_records[:]

        # Determine what to do
        to_create = []
        to_delete = []
        to_change = []
        if module.params.get('state') == 'present':
            if records and mismatch:
                # Mismatch: user wants to overwrite?
                if module.params.get('overwrite'):
                    to_delete.extend(mismatch_records)
                else:
                    module.fail_json(msg="Record already exists with different value. Set 'overwrite' to replace it")
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
            if not mismatch or module.params.get('overwrite'):
                to_delete.extend(records)
                after = []

        # Is there nothing to change?
        if len(to_create) == 0 and len(to_delete) == 0 and len(to_change) == 0:
            result = dict(
                changed=False,
                zone_id=zone_id,
            )
            if module._diff:
                before_after = (
                    format_records_for_output(sorted(before, key=lambda record: record.target), record_in, prefix)
                    if before else dict()
                )
                result['diff'] = dict(
                    before=before_after,
                    after=before_after,
                )
            module.exit_json(**result)

        # Actually do something
        if not module.check_mode:
            for record in to_delete:
                api.delete_record(zone_id, record)
            for record in to_change:
                api.update_record(zone_id, record)
            for record in to_create:
                api.add_record(zone_id, record)

        result = dict(
            changed=True,
            zone_id=zone_id,
        )
        if module._diff:
            result['diff'] = dict(
                before=(
                    format_records_for_output(sorted(before, key=lambda record: record.target), record_in, prefix)
                    if before else dict()
                ),
                after=(
                    format_records_for_output(sorted(after, key=lambda record: record.target), record_in, prefix)
                    if after else dict()
                ),
            )

        module.exit_json(**result)
    except DNSAPIAuthenticationError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=str(e), exception=traceback.format_exc())
    except DNSAPIError as e:
        module.fail_json(msg='Error: {0}'.format(e), error=str(e), exception=traceback.format_exc())
