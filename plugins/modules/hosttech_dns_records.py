#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: hosttech_dns_records

short_description: Bulk synchronize DNS records in Hosttech DNS service

version_added: 0.3.0

description:
    - Bulk synchronize DNS records in Hosttech DNS service.

extends_documentation_fragment:
    - community.dns.hosttech
    - community.dns.module_records

options:
    zone_id:
        type: int

author:
    - Felix Fontein (@felixfontein)

'''

EXAMPLES = '''
- name: Make sure some records exist and have the expected values
  community.dns.hosttech_dns_records:
    zone: foo.com
    records:
      - prefix: new
        type: A
        ttl: 7200
        value:
          - 1.1.1.1
          - 2.2.2.2
      - prefix: new
        type: AAAA
        ttl: 7200
        value:
          - "::1"
      - zone: foo.com
        type: TXT
        value:
          - test
    hosttech_token: access_token

- name: Synchronize DNS zone with a fixed set of records
  # If a record exists that is not mentioned here, it will be deleted
  community.dns.hosttech_dns_records:
    zone_id: 23
    purge: true
    records:
      - prefix: ''
        type: A
        value: 127.0.0.1
      - prefix: ''
        type: AAAA
        value: "::1"
      - prefix: ''
        type: NS
        value:
          - ns-1.hoster.com
          - ns-2.hoster.com
          - ns-3.hoster.com
    hosttech_token: access_token
'''

RETURN = '''
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
)

from ansible_collections.community.dns.plugins.module_utils.module.records import (
    create_module_argument_spec,
    run_module,
)


def main():
    argument_spec = create_hosttech_argument_spec()
    argument_spec.merge(create_module_argument_spec(zone_id_type='int'))
    module = AnsibleModule(supports_check_mode=True, **argument_spec.to_kwargs())
    run_module(module, lambda: create_hosttech_api(module))


if __name__ == '__main__':
    main()
