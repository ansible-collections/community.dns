# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.six import raise_from
from ansible.module_utils._text import to_native

from ansible_collections.community.dns.plugins.module_utils.wsdl import (
    WSDLError,
    WSDLNetworkError,
    Composer,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.errors import (
    HostTechAPIError,
    HostTechAPIAuthError,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.record import (
    DNSRecord,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.zone import (
    DNSZone,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.api import (
    HostTechAPI,
)


class HostTechWSDLAPI(HostTechAPI):
    def __init__(self, username, password, api='https://ns1.hosttech.eu/public/api', debug=False):
        """
        Create a new HostTech API instance with given username and password.
        """
        self._api = api
        self._namespaces = {
            'ns1': 'https://ns1.hosttech.eu/soap',
        }
        self._username = username
        self._password = password
        self._debug = debug

    def _prepare(self):
        command = Composer(self._api, self._namespaces)
        command.add_auth(self._username, self._password)
        return command

    def _announce(self, msg):
        if self._debug:
            pass
            # q.q('{0} {1} {2}'.format('=' * 4, msg, '=' * 40))

    def _execute(self, command, result_name, acceptable_types):
        if self._debug:
            pass
            # q.q('Request: {0}'.format(command))
        try:
            result = command.execute(debug=self._debug)
        except WSDLError as e:
            if e.error_code == '998':
                raise HostTechAPIAuthError('Error on authentication ({0})'.format(e.error_message))
            raise
        res = result.get_result(result_name)
        if isinstance(res, acceptable_types):
            if self._debug:
                pass
                # q.q('Extracted result: {0} (type {1})'.format(res, type(res)))
            return res
        if self._debug:
            pass
            # q.q('Result: {0}; extracted type {1}'.format(result, type(res)))
        raise HostTechAPIError('Result has unexpected type {0} (expecting {1})!'.format(type(res), acceptable_types))

    def get_zone(self, search):
        """
        Search a zone by name or id.

        @param search: The search string, i.e. a zone name or ID (string)
        @return The zone information (DNSZone)
        """
        self._announce('get zone')
        command = self._prepare()
        command.add_simple_command('getZone', sZoneName=search)
        try:
            return DNSZone.create_from_encoding(self._execute(command, 'getZoneResponse', dict))
        except WSDLError as exc:
            if exc.error_origin == 'server' and exc.error_message == 'zone not found':
                return None
            raise_from(HostTechAPIError('Error while getting zone: {0}'.format(to_native(exc))), exc)
        except WSDLNetworkError as exc:
            raise_from(HostTechAPIError('Network error while getting zone: {0}'.format(to_native(exc))), exc)

    def add_record(self, search, record):
        """
        Adds a new record to an existing zone.

        @param zone: The search string, i.e. a zone name or ID (string)
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        self._announce('add record')
        command = self._prepare()
        command.add_simple_command('addRecord', search=search, recorddata=record.encode(include_ids=False))
        try:
            return DNSRecord.create_from_encoding(self._execute(command, 'addRecordResponse', dict))
        except WSDLError as exc:
            raise_from(HostTechAPIError('Error while adding record: {0}'.format(to_native(exc))), exc)
        except WSDLNetworkError as exc:
            raise_from(HostTechAPIError('Network error while adding record: {0}'.format(to_native(exc))), exc)

    def update_record(self, record):
        """
        Update a record.

        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        if record.id is None:
            raise HostTechAPIError('Need record ID to update record!')
        self._announce('update record')
        command = self._prepare()
        command.add_simple_command('updateRecord', recordId=record.id, recorddata=record.encode(include_ids=False))
        try:
            return DNSRecord.create_from_encoding(self._execute(command, 'updateRecordResponse', dict))
        except WSDLError as exc:
            raise_from(HostTechAPIError('Error while updating record: {0}'.format(to_native(exc))), exc)
        except WSDLNetworkError as exc:
            raise_from(HostTechAPIError('Network error while updating record: {0}'.format(to_native(exc))), exc)

    def delete_record(self, record):
        """
        Delete a record.

        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        if record.id is None:
            raise HostTechAPIError('Need record ID to delete record!')
        self._announce('delete record')
        command = self._prepare()
        command.add_simple_command('deleteRecord', recordId=record.id)
        try:
            return self._execute(command, 'deleteRecordResponse', bool)
        except WSDLError as exc:
            raise_from(HostTechAPIError('Error while deleting record: {0}'.format(to_native(exc))), exc)
        except WSDLNetworkError as exc:
            raise_from(HostTechAPIError('Network error while deleting record: {0}'.format(to_native(exc))), exc)
