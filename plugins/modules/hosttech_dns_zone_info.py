#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: hosttech_dns_zone_info

short_description: Retrieve zone information in Hosttech DNS service

version_added: 0.2.0

description:
    - "Retrieves zone information in Hosttech DNS service."

extends_documentation_fragment:
    - community.dns.hosttech
    - community.dns.module_zone_info

options:
    zone_id:
        type: int

author:
    - Felix Fontein (@felixfontein)
'''

EXAMPLES = '''
- name: Retrieve details for foo.com zone
  community.dns.hosttech_dns_zone_info:
    zone: foo.com
    hosttech_username: foo
    hosttech_password: bar
  register: rec

- name: Retrieve details for zone 23
  community.dns.hosttech_dns_record:
    state: absent
    zone_id: 23
    hosttech_token: access_token
'''

RETURN = '''
zone_name:
    description: The name of the zone.
    type: int
    returned: success
    sample: example.com

zone_id:
    description: The ID of the zone.
    type: int
    returned: success
    sample: 23
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.dns.plugins.module_utils.hosttech.api import (
    create_hosttech_argument_spec,
    create_hosttech_api,
    create_hosttech_provider_information,
)

from ansible_collections.community.dns.plugins.module_utils.module.zone_info import (
    run_module,
    create_module_argument_spec,
)


def main():
    provider_information = create_hosttech_provider_information()
    argument_spec = create_hosttech_argument_spec()
    argument_spec.merge(create_module_argument_spec(zone_id_type='int', provider_information=provider_information))
    module = AnsibleModule(supports_check_mode=True, **argument_spec.to_kwargs())
    run_module(module, lambda: create_hosttech_api(module), provider_information=provider_information)


if __name__ == '__main__':
    main()
