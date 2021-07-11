# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.argspec import (
    ArgumentSpec,
)

from ansible_collections.community.dns.plugins.module_utils.provider import (
    ProviderInformation,
)

from ansible_collections.community.dns.plugins.module_utils.wsdl import (
    HAS_LXML_ETREE,
)

from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.wsdl_api import (
    HostTechWSDLAPI,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.json_api import (
    HostTechJSONAPI,
)


class HosttechProviderInformation(ProviderInformation):
    def get_supported_record_types(self):
        """
        Return a list of supported record types.
        """
        return ['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA']

    def normalize_prefix(self, prefix):
        """
        Given a prefix (string or None), return its normalized form.

        The result should always be None for the trivial prefix, and a non-zero length DNS name
        for a non-trivial prefix.

        If a provider supports other identifiers for the trivial prefix, such as '@', this
        function needs to convert them to None as well.
        """
        return prefix or None


def create_hosttech_provider_information():
    return HosttechProviderInformation()


def create_hosttech_argument_spec():
    return ArgumentSpec(
        argument_spec=dict(
            hosttech_username=dict(type='str'),
            hosttech_password=dict(type='str', no_log=True),
            hosttech_token=dict(type='str', no_log=True, aliases=['api_token']),
        ),
        required_together=[('hosttech_username', 'hosttech_password')],
        mutually_exclusive=[('hosttech_username', 'hosttech_token')],
    )


def create_hosttech_api(module):
    if module.params['hosttech_username'] is not None:
        if not HAS_LXML_ETREE:
            module.fail_json(msg='Needs lxml Python module (pip install lxml)')

        return HostTechWSDLAPI(module.params['hosttech_username'], module.params['hosttech_password'], debug=False)

    if module.params['hosttech_token'] is not None:
        return HostTechJSONAPI(module, module.params['hosttech_token'])

    raise DNSAPIError('Internal error!')
