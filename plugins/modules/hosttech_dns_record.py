#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: hosttech_dns_record

short_description: Add or delete entries in Hosttech DNS service

version_added: 0.1.0

description:
    - "Creates and deletes DNS records in Hosttech DNS service."

extends_documentation_fragment:
    - community.dns.hosttech
    - community.dns.module_record

options:
    zone_id:
        type: int

author:
    - Felix Fontein (@felixfontein)
'''

EXAMPLES = '''
- name: Add new.foo.com as an A record with 3 IPs
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: new.foo.com
    type: A
    ttl: 7200
    value: 1.1.1.1,2.2.2.2,3.3.3.3
    hosttech_token: access_token

- name: Update new.foo.com as an A record with a list of 3 IPs
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: new.foo.com
    type: A
    ttl: 7200
    value:
      - 1.1.1.1
      - 2.2.2.2
      - 3.3.3.3
    hosttech_token: access_token

- name: Retrieve the details for new.foo.com
  community.dns.hosttech_dns_record_info:
    zone: foo.com
    record: new.foo.com
    type: A
    hosttech_username: foo
    hosttech_password: bar
  register: rec

- name: Delete new.foo.com A record using the results from the facts retrieval command
  community.dns.hosttech_dns_record:
    state: absent
    zone: foo.com
    record: "{{ rec.set.record }}"
    ttl: "{{ rec.set.ttl }}"
    type: "{{ rec.set.type }}"
    value: "{{ rec.set.value }}"
    hosttech_username: foo
    hosttech_password: bar

- name: Add an AAAA record
  # Note that because there are colons in the value that the IPv6 address must be quoted!
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: localhost.foo.com
    type: AAAA
    ttl: 7200
    value: "::1"
    hosttech_token: access_token

- name: Add a TXT record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: localhost.foo.com
    type: TXT
    ttl: 7200
    value: 'bar'
    hosttech_username: foo
    hosttech_password: bar

- name: Remove the TXT record
  community.dns.hosttech_dns_record:
    state: absent
    zone: foo.com
    record: localhost.foo.com
    type: TXT
    ttl: 7200
    value: 'bar'
    hosttech_username: foo
    hosttech_password: bar

- name: Add a CAA record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: foo.com
    type: CAA
    ttl: 3600
    value:
    - "128 issue letsencrypt.org"
    - "128 iodef mailto:webmaster@foo.com"
    hosttech_token: access_token

- name: Add an MX record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: foo.com
    type: MX
    ttl: 3600
    value:
    - "10 mail.foo.com"
    hosttech_token: access_token

- name: Add a CNAME record
  community.dns.hosttech_dns_record:
    state: present
    zone: bla.foo.com
    record: foo.com
    type: CNAME
    ttl: 3600
    value:
    - foo.foo.com
    hosttech_username: foo
    hosttech_password: bar

- name: Add a PTR record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.foo.com
    record: foo.com
    type: PTR
    ttl: 3600
    value:
    - foo.foo.com
    hosttech_token: access_token

- name: Add an SPF record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: foo.com
    type: SPF
    ttl: 3600
    value:
    - "v=spf1 a mx ~all"
    hosttech_username: foo
    hosttech_password: bar

- name: Add a PTR record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: foo.com
    type: PTR
    ttl: 3600
    value:
    - "10 100 3333 service.foo.com"
    hosttech_token: access_token
'''

RETURN = '''
zone_id:
    description: The ID of the zone.
    type: int
    returned: success
    sample: 23
    version_added: 0.2.0
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.dns.plugins.module_utils.hosttech.api import (
    create_hosttech_argument_spec,
    create_hosttech_api,
)

from ansible_collections.community.dns.plugins.module_utils.module.record import (
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
