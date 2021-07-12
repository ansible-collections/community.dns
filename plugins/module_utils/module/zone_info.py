# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This module_utils is PRIVATE and should only be used by this collection. Breaking changes can occur any time.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import traceback

from ansible_collections.community.dns.plugins.module_utils.argspec import (
    ArgumentSpec,
)

from ansible_collections.community.dns.plugins.module_utils.record import (
    format_records_for_output,
)

from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
    DNSAPIAuthenticationError,
)

from ._utils import (
    normalize_dns_name,
)


def create_module_argument_spec(zone_id_type='str', provider_information):
    return ArgumentSpec(
        argument_spec=dict(
            zone=dict(type='str'),
            zone_id=dict(type=zone_id_type),
        ),
        required_one_of=[
            ('zone', 'zone_id'),
        ],
        mutually_exclusive=[
            ('zone', 'zone_id'),
        ],
    )


def run_module(module, create_api, provider_information):
    try:
        # Create API
        api = create_api()

        # Get zone information
        if module.params.get('zone') is not None:
            zone_id = normalize_dns_name(module.params.get('zone'))
            zone = api.get_zone_by_name(zone_id)
            if zone is None:
                module.fail_json(msg='Zone not found')
        else:
            zone = api.get_zone_by_id(module.params.get('zone_id'))
            if zone is None:
                module.fail_json(msg='Zone not found')

        module.exit_json(
            changed=False,
            zone_name=zone.name,
            zone_id=zone.id,
        )
    except DNSAPIAuthenticationError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=str(e), exception=traceback.format_exc())
    except DNSAPIError as e:
        module.fail_json(msg='Error: {0}'.format(e), error=str(e), exception=traceback.format_exc())
