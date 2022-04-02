#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: hetzner_dns_zone_info

short_description: Retrieve zone information in Hetzner DNS service

version_added: 2.0.0

description:
    - "Retrieves zone information in Hetzner DNS service."

extends_documentation_fragment:
    - community.dns.hetzner
    - community.dns.hetzner.zone_id_type
    - community.dns.module_zone_info

author:
    - Markus Bergholz (@markuman) <markuman+spambelongstogoogle@gmail.com>
    - Felix Fontein (@felixfontein)
'''

EXAMPLES = '''
- name: Retrieve details for foo.com zone
  community.dns.hetzner_dns_zone_info:
    zone: foo.com
    hetzner_token: access_token
  register: rec

- name: Retrieve details for zone 23
  community.dns.hetzner_dns_zone_info:
    zone_id: 23
    hetzner_token: access_token
'''

RETURN = '''
zone_name:
    description: The name of the zone.
    type: int
    returned: success
    sample: example.com

zone_id:
    description: The ID of the zone.
    type: str
    returned: success
    sample: 23

zone_info:
    description:
        - Extra information returned by the API.
    type: dict
    returned: success
    contains:
        created:
            description:
                - The time when the zone was created.
            type: str
            sample: "2021-07-15T19:23:58Z"
        modified:
            description:
                - The time the zone was last modified.
            type: str
            sample: "2021-07-15T19:23:58Z"
        legacy_dns_host:
            description:
                # TODO
                - Unknown.
            type: str
        legacy_ns:
            description:
                - List of nameservers during import.
            type: list
            elements: str
        ns:
            description:
                - List of nameservers the zone should have for using Hetzner's DNS.
            type: list
            elements: str
        owner:
            description:
                - Owner of the zone.
            type: str
        paused:
            description:
                # TODO
                - Unknown.
            type: bool
            sample: true
        permission:
            description:
                - Zone's permissions.
            type: str
        project:
            description:
                # TODO
                - Unknown.
            type: str
        registrar:
            description:
                # TODO
                - Unknown.
            type: str
        status:
            description:
                - Status of the zone.
                - Can be one of C(verified), C(failed) and C(pending).
            type: str
            sample: verified
            # choices:
            #     - verified
            #     - failed
            #     - pending
        ttl:
            description:
                - TTL of zone.
            type: int
            sample: 0
        verified:
            description:
                - Time when zone was verified.
            type: str
            sample: "2021-07-15T19:23:58Z"
        records_count:
            description:
                - Number of records associated to this zone.
            type: int
            sample: 0
        is_secondary_dns:
            description:
                - Indicates whether the zone is a secondary DNS zone.
            type: bool
            sample: true
        txt_verification:
            description:
                - Shape of the TXT record that has to be set to verify a zone.
                - If name and token are empty, no TXT record needs to be set.
            type: dict
            sample: {'name': '', 'token': ''}
            contains:
                name:
                    description:
                        - The TXT record's name.
                    type: str
                token:
                    description:
                        - The TXT record's content.
                    type: str
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.dns.plugins.module_utils.argspec import (
    ModuleOptionProvider,
)

from ansible_collections.community.dns.plugins.module_utils.http import (
    ModuleHTTPHelper,
)

from ansible_collections.community.dns.plugins.module_utils.hetzner.api import (
    create_hetzner_argument_spec,
    create_hetzner_api,
    create_hetzner_provider_information,
)

from ansible_collections.community.dns.plugins.module_utils.module.zone_info import (
    run_module,
    create_module_argument_spec,
)


def main():
    provider_information = create_hetzner_provider_information()
    argument_spec = create_hetzner_argument_spec()
    argument_spec.merge(create_module_argument_spec(provider_information=provider_information))
    module = AnsibleModule(supports_check_mode=True, **argument_spec.to_kwargs())
    run_module(module, lambda: create_hetzner_api(ModuleOptionProvider(module), ModuleHTTPHelper(module)), provider_information=provider_information)


if __name__ == '__main__':
    main()
