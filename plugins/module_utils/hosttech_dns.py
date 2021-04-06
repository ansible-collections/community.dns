# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.wsdl import (
    WSDLError, Composer,
)


def format_ttl(ttl):
    sec = ttl % 60
    ttl //= 60
    min = ttl % 60
    ttl //= 60
    h = ttl
    result = []
    if h:
        result.append('{0}h'.format(h))
    if min:
        result.append('{0}m'.format(min))
    if sec:
        result.append('{0}s'.format(sec))
    return ' '.join(result)


class DNSRecord(object):
    def __init__(self):
        self.id = None
        self.zone = None
        self.type = None
        self.prefix = None
        self.target = None
        self.ttl = 86400  # 24 * 60 * 60
        self.priority = None

    @staticmethod
    def create_from_encoding(source, type=None):
        result = DNSRecord()
        result.id = source['id']
        result.zone = source['zone']
        result.type = source.get('type', type)
        result.prefix = source.get('prefix')
        result.target = source.get('target')
        result.ttl = int(source['ttl']) if source['ttl'] is not None else None
        result.priority = source.get('priority')
        return result

    def encode(self, include_ids=False):
        result = {
            'type': self.type,
            'prefix': self.prefix,
            'target': self.target,
            'ttl': self.ttl,
            'priority': self.priority,
        }
        if include_ids:
            result['id'] = self.id
            result['zone'] = self.zone
        return result

    def clone(self):
        return DNSRecord.create_from_encoding(self.encode(include_ids=True))

    def __str__(self):
        data = []
        if self.id:
            data.append('id: {0}'.format(self.id))
        if self.zone:
            data.append('zone: {0}'.format(self.zone))
        data.append('type: {0}'.format(self.type))
        if self.prefix:
            data.append('prefix: "{0}"'.format(self.prefix))
        else:
            data.append('prefix: (none)')
        data.append('target: "{0}"'.format(self.target))
        data.append('ttl: {0}'.format(format_ttl(self.ttl)))
        if self.priority:
            data.append('priority: {0}'.format(self.priority))
        return 'DNSRecord(' + ', '.join(data) + ')'

    def __repr__(self):
        return 'DNSRecord.create_from_encoding({0!r})'.format(self.encode(include_ids=True))


class DNSZone(object):
    def __init__(self, name):
        self.id = None
        self.name = name
        self.email = None
        self.ttl = 10800  # 3 * 60 * 60
        self.nameserver = None
        self.serial = None
        self.template = None
        self.records = []

    @staticmethod
    def create_from_encoding(source):
        result = DNSZone(source['name'])
        result.id = source['id']
        result.email = source.get('email')
        result.ttl = int(source['ttl'])
        result.nameserver = source['nameserver']
        result.serial = source['serial']
        result.template = source.get('template')
        result.records = [DNSRecord.create_from_encoding(record) for record in source['records']]
        return result

    def encode(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'ttl': self.ttl,
            'nameserver': self.nameserver,
            'serial': self.serial,
            'template': self.template,
            'ns3': self.ns3,
            'records': [record.encode(include_ids=True) for record in self.records],
        }

    def __str__(self):
        data = []
        if self.id:
            data.append('id: {0}'.format(self.id))
        data.append('name: {0}'.format(self.name))
        if self.email:
            data.append('email: {0}'.format(self.email))
        data.append('ttl: {0}'.format(format_ttl(self.ttl)))
        if self.nameserver:
            data.append('nameserver: {0}'.format(self.nameserver))
        if self.serial:
            data.append('serial: {0}'.format(self.serial))
        if self.template:
            data.append('template: {0}'.format(self.template))
        for record in self.records:
            data.append('record: {0}'.format(str(record)))
        return 'DNSZone(\n' + ',\n'.join(['  ' + line for line in data]) + '\n)'

    def __repr__(self):
        return 'DNSZone.create_from_encoding({0!r})'.format(self.encode())


class HostTechAPIError(Exception):
    pass


class HostTechAPIAuthError(Exception):
    pass


class HostTechAPI(object):
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
        if self._debug:
            self._announce('get zone')
        command = self._prepare()
        command.add_simple_command('getZone', sZoneName=search)
        try:
            return DNSZone.create_from_encoding(self._execute(command, 'getZoneResponse', dict))
        except WSDLError as e:
            if e.error_origin == 'server' and e.error_message == 'zone not found':
                return None
            raise

    def add_record(self, search, record):
        """
        Adds a new record to an existing zone.

        @param zone: The search string, i.e. a zone name or ID (string)
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        if self._debug:
            self._announce('add record')
        command = self._prepare()
        command.add_simple_command('addRecord', search=search, recorddata=record.encode(include_ids=False))
        try:
            return DNSRecord.create_from_encoding(self._execute(command, 'addRecordResponse', dict))
        except WSDLError as e:
            # FIXME
            raise

    def update_record(self, record):
        """
        Update a record.

        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        if record.id is None:
            raise HostTechAPIError('Need record ID to update record!')
        if self._debug:
            self._announce('update record')
        command = self._prepare()
        command.add_simple_command('updateRecord', recordId=record.id, recorddata=record.encode(include_ids=False))
        try:
            return DNSRecord.create_from_encoding(self._execute(command, 'updateRecordResponse', dict))
        except WSDLError as e:
            # FIXME
            raise

    def delete_record(self, record):
        """
        Delete a record.

        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        if record.id is None:
            raise HostTechAPIError('Need record ID to delete record!')
        if self._debug:
            self._announce('delete record')
        command = self._prepare()
        command.add_simple_command('deleteRecord', recordId=record.id)
        try:
            return self._execute(command, 'deleteRecordResponse', bool)
        except WSDLError as e:
            # FIXME
            raise


def format_records_for_output(records, record_name):
    ttls = set([record.ttl for record in records]),
    entry = {
        'record': record_name,
        'type': min([record.type for record in records]) if records else None,
        'ttl': min(*list(ttls)) if records else None,
        'value': [record.target for record in records],
    }
    if len(ttls) > 1:
        entry['ttls'] = ttls
    return entry
