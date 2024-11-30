# -*- coding: utf-8 -*-

# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r'''
name: reverse_lookup
author: Felix Fontein (@felixfontein)
short_description: Reverse-look up IP addresses
version_added: 3.1.0
requirements:
    - dnspython >= 1.15.0 (maybe older versions also work)
description:
    - Look up hostnames for IP addresses using DNS reverse lookup.
options:
    _terms:
        description:
            - IP address(es) to look up.
        type: list
        elements: str
        required: true
    query_retry:
        description:
            - Number of retries for DNS query timeouts.
        type: int
        default: 3
    query_timeout:
        description:
            - Timeout per DNS query in seconds.
        type: float
        default: 10
    server:
        description:
            - The DNS server(s) to use to look up the result. Must be a list of one or more IP addresses.
            - By default, the system's standard resolver is used.
        type: list
        elements: str
    servfail_retries:
        description:
            - How often to retry on SERVFAIL errors.
        type: int
        default: 0
notes:
    - Note that when using this lookup plugin with V(lookup(\)), and the result is a one-element list,
      Ansible simply returns the one element not as a list. Since this behavior is surprising and
      can cause problems, it is better to use V(query(\)) instead of V(lookup(\)). See the examples
      and also R(Forcing lookups to return lists, query) in the Ansible documentation.
'''

EXAMPLES = """
- name: Look up hostname of IPv4 address
  ansible.builtin.debug:
    msg: "{{ query('community.dns.reverse_lookup', '192.168.1.1') }}"

- name: Look up hostname of IPv6 address
  ansible.builtin.debug:
    msg: "{{ query('community.dns.reverse_lookup', '1:2:3::4') }}"
"""

RETURN = """
_result:
    description:
        - The hostname(s) returned for the queried IP addresses.
        - If multiple IP addresses are queried in O(_terms), the resulting lists have been concatenated.
    type: list
    elements: str
    sample:
        - example.com
        - example.org
"""

from ansible.errors import AnsibleLookupError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common.text.converters import to_text

from ansible_collections.community.dns.plugins.module_utils.ips import (
    is_ip_address,
)

from ansible_collections.community.dns.plugins.module_utils.resolver import (
    SimpleResolver,
)

from ansible_collections.community.dns.plugins.plugin_utils.ips import (
    assert_requirements_present as assert_requirements_present_ipaddress,
)

from ansible_collections.community.dns.plugins.plugin_utils.resolver import (
    assert_requirements_present as assert_requirements_present_dnspython,
    guarded_run,
)

try:
    import dns.resolver
except ImportError:
    # handled by assert_requirements_present_dnspython
    pass

try:
    import ipaddress
except ImportError:
    # handled by assert_requirements_present
    pass


class LookupModule(LookupBase):
    @staticmethod
    def _resolve(resolver, name, rdtype, server_addresses):
        def callback():
            try:
                rrset = resolver.resolve(
                    name,
                    rdtype=rdtype,
                    server_addresses=server_addresses,
                    nxdomain_is_empty=True,
                    target_can_be_relative=False,
                    search=False,
                )
                if not rrset:
                    return []
                return [to_text(data) for data in rrset]
            except dns.resolver.NXDOMAIN:
                raise AnsibleLookupError(f'Got NXDOMAIN when querying {name}')

        return guarded_run(
            callback,
            error_class=AnsibleLookupError,
            server=name,
        )

    def run(self, terms, variables=None, **kwargs):
        assert_requirements_present_dnspython('community.dns.reverse_lookup', 'lookup')
        assert_requirements_present_ipaddress('community.dns.reverse_lookup', 'lookup')

        self.set_options(var_options=variables, direct=kwargs)

        resolver = SimpleResolver(
            timeout=self.get_option('query_timeout'),
            timeout_retries=self.get_option('query_retry'),
            servfail_retries=self.get_option('servfail_retries'),
        )

        server_addresses = None
        if self.get_option('server'):
            server_addresses = []
            for server in self.get_option('server'):
                if is_ip_address(server):
                    server_addresses.append(server)
                    continue
                else:
                    server_addresses.extend(guarded_run(
                        lambda: resolver.resolve_addresses(server),
                        error_class=AnsibleLookupError,
                        server=server,
                    ))

        ip_adresses = []
        for ip_address in terms:
            try:
                ipaddr = ipaddress.ip_address(to_text(ip_address))
                name = ipaddr.reverse_pointer
                if not name.endswith(u'.'):
                    name += u'.'
                ip_adresses.append(name)
            except Exception as e:
                raise AnsibleLookupError(f'Cannot parse IP address {ip_address!r}: {e}')

        result = []
        for name in ip_adresses:
            result.extend(self._resolve(resolver, name, dns.rdatatype.PTR, server_addresses))
        return result
