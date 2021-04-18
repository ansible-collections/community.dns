# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import abc

from ansible.module_utils import six

from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
)

from ansible_collections.community.dns.plugins.module_utils.wsdl import (
    HAS_LXML_ETREE,
)

from ansible_collections.community.dns.plugins.module_utils.zone import (
    DNSZone,
    DNSZoneWithRecords,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.errors import (
    HostTechAPIError,
    HostTechAPIAuthError,
)


@six.add_metaclass(abc.ABCMeta)
class HostTechAPI(object):
    @abc.abstractmethod
    def get_zone_with_records_by_name(self, name):
        """
        Given a zone name, return the zone contents with records if found.

        @param name: The zone name (string)
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """
        pass

    @abc.abstractmethod
    def get_zone_with_records_by_id(self, id):
        """
        Given a zone ID, return the zone contents with records if found.

        @param id: The zone ID
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """
        pass

    @abc.abstractmethod
    def add_record(self, zone_id, record):
        """
        Adds a new record to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        pass

    @abc.abstractmethod
    def update_record(self, zone_id, record):
        """
        Update a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        pass

    @abc.abstractmethod
    def delete_record(self, zone_id, record):
        """
        Delete a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        pass


def create_argument_spec():
    return dict(
        argument_spec=dict(
            hosttech_username=dict(type='str'),
            hosttech_password=dict(type='str', no_log=True),
            hosttech_token=dict(type='str', no_log=True),
        ),
        required_together=[('hosttech_username', 'hosttech_password')],
        required_if=[],
        mutually_exclusive=[('hosttech_username', 'hosttech_token')],
    )


def create_api(module):
    if module.params['hosttech_username'] is not None:
        if not HAS_LXML_ETREE:
            module.fail_json(msg='Needs lxml Python module (pip install lxml)')

        from ansible_collections.community.dns.plugins.module_utils.hosttech.wsdl_api import HostTechWSDLAPI
        return HostTechWSDLAPI(module.params['hosttech_username'], module.params['hosttech_password'], debug=False)

    if module.params['hosttech_token'] is not None:
        from ansible_collections.community.dns.plugins.module_utils.hosttech.json_api import HostTechJSONAPI
        return HostTechJSONAPI(module, module.params['hosttech_token'])

    raise HostTechAPIError('Internal error!')
