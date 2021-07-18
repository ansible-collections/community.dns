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
    format_record_for_output,
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


def create_module_argument_spec(provider_information):
    return ArgumentSpec(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent'], required=True),
            zone_name=dict(type='str', aliases=['zone']),
            zone_id=dict(type=provider_information.get_zone_id_type()),
            record=dict(type='str'),
            prefix=dict(type='str'),
            ttl=dict(type='int', default=3600),
            type=dict(choices=provider_information.get_supported_record_types(), required=True),
            value=dict(type='str', required=True),
        ),
        required_one_of=[
            ('zone_name', 'zone_id'),
            ('record', 'prefix'),
        ],
        mutually_exclusive=[
            ('zone_name', 'zone_id'),
            ('record', 'prefix'),
        ],
    )


def run_module(module, create_api, provider_information):
    record_in = normalize_dns_name(module.params.get('record'))
    prefix_in = module.params.get('prefix')
    type_in = module.params.get('type')
    try:
        # Create API
        api = create_api()

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

        # Parse records
        value_in = module.params.get('value')

        # Compare records
        existing_record = None
        exact_match = False
        ttl_in = module.params.get('ttl')
        for record in records:
            if record.target == value_in:
                existing_record = record
                exact_match = record.ttl == ttl_in
                break

        before = existing_record.clone() if existing_record else None
        after = before
        changed = False

        if module.params.get('state') == 'present':
            if existing_record is None:
                # Create record
                record = DNSRecord()
                record.prefix = prefix
                record.type = type_in
                record.ttl = ttl_in
                record.target = value_in
                if not module.check_mode:
                    api.add_record(zone_id, record)
                after = record
                changed = True
            elif not exact_match:
                # Update record
                record = existing_record
                record.ttl = ttl_in
                if not module.check_mode:
                    api.update_record(zone_id, record)
                after = record
                changed = True
        else:
            if existing_record is not None:
                # Delete record
                if not module.check_mode:
                    api.delete_record(zone_id, existing_record)
                after = None
                changed = True

        # Compose result
        result = dict(
            changed=changed,
            zone_id=zone_id,
        )
        if module._diff:
            result['diff'] = dict(
                before=format_record_for_output(before, record_in, prefix) if before else {},
                after=format_record_for_output(after, record_in, prefix) if after else {},
            )

        module.exit_json(**result)
    except DNSAPIAuthenticationError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=str(e), exception=traceback.format_exc())
    except DNSAPIError as e:
        module.fail_json(msg='Error: {0}'.format(e), error=str(e), exception=traceback.format_exc())
