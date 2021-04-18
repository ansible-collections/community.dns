# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# The API documentation can be found here: https://api.ns1.hosttech.eu/api/documentation/

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import json

from ansible.module_utils.six import raise_from
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url

from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
)

from ansible_collections.community.dns.plugins.module_utils.zone import (
    DNSZone,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.errors import (
    HostTechError,
    HostTechAPIError,
    HostTechAPIAuthError,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.api import (
    HostTechAPI,
)


def create_record_from_json(source, zone=None, type=None):
    result = DNSRecord()
    result.id = source['id']
    result.zone = zone
    result.type = source.get('type', type)
    result.ttl = int(source['ttl']) if source['ttl'] is not None else None
    result.comment = source['comment']

    name = source.get('name')
    target = None
    priority = None
    if result.type == 'A':
        target = source['ipv4']
    elif result.type == 'AAAA':
        target = source['ipv6']
    elif result.type == 'CAA':
        target = '{0} {1} {2}'.format(source['flag'], source['tag'], source['value'])
    elif result.type == 'CNAME':
        target = source['cname']
    elif result.type == 'MX':
        name = source['ownername']
        priority = source['pref']
        target = source['name']
    elif result.type == 'NS':
        name = source['ownername']
        target = source['targetname']
    elif result.type == 'PTR':
        name = ''
        target = '{0} {1}'.format(source['origin'], source['name'])
    elif result.type == 'SRV':
        name = source['service']
        priority = source['priority']
        target = '{0} {1} {2}'.format(source['weight'], source['port'], source['target'])
    elif result.type == 'TXT':
        target = source['text']
    elif result.type == 'TLSA':
        target = source['text']
    else:
        raise HostTechAPIError('Cannot parse unknown record type: {0}'.format(result.type))

    result.prefix = name
    result.target = target
    result.priority = priority
    return result


def create_zone_from_json(source):
    result = DNSZone(source['name'])
    result.id = source['id']
    # result.email = source.get('email')
    # result.ttl = int(source['ttl'])
    # result.nameserver = source['nameserver']
    result.records = [create_record_from_json(record, zone=source['name']) for record in source['records']]
    return result


def record_to_json(record, include_id=False, include_type=True):
    result = {
        'ttl': record.ttl,
        'comment': record.comment or '',
    }
    if include_type:
        result['type'] = record.type
    if include_id:
        result['id'] = record.id

    if record.type == 'A':
        result['name'] = record.prefix
        result['ipv4'] = record.target
    elif record.type == 'AAAA':
        result['name'] = record.prefix
        result['ipv6'] = record.target
    elif record.type == 'CAA':
        result['name'] = record.prefix
        flag, tag, value = record.target.split(' ', 2)
        result['flag'] = flag
        result['tag'] = tag
        result['value'] = value
    elif record.type == 'CNAME':
        result['name'] = record.prefix
        result['cname'] = record.target
    elif record.type == 'MX':
        result['ownername'] = record.prefix
        result['pref'] = record.priority
        result['name'] = record.target
    elif record.type == 'NS':
        result['ownername'] = record.prefix
        result['targetname'] = record.target
    elif record.type == 'PTR':
        origin, name = record.target.split(' ', 1)
        result['origin'] = origin
        result['name'] = name
    elif record.type == 'SRV':
        result['service'] = record.prefix
        result['priority'] = record.priority
        weight, port, target = record.target.split(' ', 2)
        result['weight'] = int(weight)
        result['port'] = int(port)
        result['target'] = target
    elif record.type == 'TXT':
        result['name'] = record.prefix
        result['text'] = record.target
    elif record.type == 'TLSA':
        result['name'] = record.prefix
        result['text'] = record.target
    else:
        raise HostTechAPIError('Cannot serialize unknown record type: {0}'.format(record.type))

    return result


class HostTechJSONAPI(HostTechAPI):
    def __init__(self, module, token, api='https://api.ns1.hosttech.eu/api/', debug=False):
        """
        Create a new HostTech API instance with given username and password.
        """
        self._api = api
        self._module = module
        self._token = token
        self._debug = debug

    def _build_url(self, url, query=None):
        return '{0}{1}{2}'.format(self._api, url, ('?' + urlencode(query)) if query else '')

    def _process_json_result(self, response, info, must_have_content=True, method='GET'):
        # Read content
        try:
            content = response.read()
        except AttributeError:
            content = info.pop('body', None)
        # Check Content-Type header
        content_type = info.get('content-type')
        for k, v in info.items():
            if k.lower() == 'content-type':
                content_type = v
        if content_type != 'application/json':
            if must_have_content:
                raise HostTechAPIError(
                    '{0} {1} did not yield JSON data, but HTTP status code {2} with Content-Type "{2}" and data: {3}'.format(
                        method, info['url'], info['status'], content_type, to_native(content)))
            return None, info
        # Decode content as JSON
        try:
            return self._module.from_json(content.decode('utf8')), info
        except Exception:
            if must_have_content:
                raise HostTechAPIError(
                    '{0} {1} did not yield JSON data, but HTTP status code {2} with data: {3}'.format(
                        method, info['url'], info['status'], to_native(content)))
            return None, info

    def _extract_message(self, result):
        if result is None:
            return ''
        if isinstance(result, dict):
            res = ''
            if 'message' in result:
                res = '{0} with message "{1}"'.format(res, result['message'])
            if 'errors' in result:
                if isinstance(result['errors'], dict):
                    for k, v in result['errors'].items():
                        res = '{0} (field "{1}": {2})'.format(res, k, v)
        return ' with data: {0}'.format(result)

    def _validate(self, response=None, result=None, info=None, expected=None, method='GET'):
        if info is None:
            raise HostTechError('Internal error: info needs to be provided')
        status = info['status']
        url = info['url']
        # Check expected status
        if expected is not None:
            if status not in expected:
                more = self._extract_error_message(result)
                if result is not None:
                    more = ' with data: {0}'.format(result)
                raise HostTechAPIError(
                    'Expected HTTP status {0} for {1} {2}, but got HTTP status {3}{4}'.format(
                        ', '.join(['{0}'.format(e) for e in expected]), method, url, status, more))
        else:
            if status < 200 or status >= 300:
                more = self._extract_error_message(result)
                raise HostTechAPIError(
                    'Expected successful HTTP status for {1} {2}, but got HTTP status {3}{4}'.format(
                        ', '.join(['{0}'.format(e) for e in expected]), method, url, status, more))

    def _get(self, url, query=None, must_have_content=True):
        full_url = self._build_url(url, query)
        if self._debug:
            pass
            # q.q('Request: GET {0}'.format(full_url))
        headers = dict(
            accept='application/json',
            authorization='Bearer {token}'.format(token=self._token),
        )
        response, info = fetch_url(self._module, full_url, headers=headers)
        return self._process_json_result(response, info, must_have_content=must_have_content, method='GET')

    def _post(self, url, data=None, query=None, must_have_content=True):
        full_url = self._build_url(url, query)
        if self._debug:
            pass
            # q.q('Request: POST {0}'.format(full_url))
        headers = dict(
            accept='application/json',
            authorization='Bearer {token}'.format(token=self._token),
        )
        encoded_data = None
        if data is not None:
            headers['content-type'] = 'application/json'
            encoded_data = json.dumps(data).encode('utf-8')
        response, info = fetch_url(self._module, full_url, headers=headers, method='POST', data=encoded_data)
        return self._process_json_result(response, info, must_have_content=must_have_content, method='POST')

    def _put(self, url, data=None, query=None, must_have_content=True):
        full_url = self._build_url(url, query)
        if self._debug:
            pass
            # q.q('Request: PUT {0}'.format(full_url))
        headers = dict(
            accept='application/json',
            authorization='Bearer {token}'.format(token=self._token),
        )
        encoded_data = None
        if data is not None:
            headers['content-type'] = 'application/json'
            encoded_data = json.dumps(data).encode('utf-8')
        response, info = fetch_url(self._module, full_url, headers=headers, method='PUT', data=encoded_data)
        return self._process_json_result(response, info, must_have_content=must_have_content, method='PUT')

    def _delete(self, url, query=None, must_have_content=True):
        full_url = self._build_url(url, query)
        if self._debug:
            pass
            # q.q('Request: DELETE {0}'.format(full_url))
        headers = dict(
            accept='application/json',
            authorization='Bearer {token}'.format(token=self._token),
        )
        response, info = fetch_url(self._module, full_url, headers=headers, method='DELETE')
        self._validate(response=response, info=info, expected=[204], method='DELETE')

    def _list_pagination(self, url, query=None):
        result = []
        block_size = 100
        offset = 0
        while True:
            query_ = query.copy() if query else dict()
            query_['limit'] = block_size
            query_['offset'] = offset
            res, info = self._get(url, query_, must_have_content=True)
            self._validate(result=res, info=info, expected=[200], method='GET')
            result.extend(res['data'])
            if len(res) < block_size:
                return result
            offset += block_size

    def _get_zone_by_id(self, zone_id):
        result, info = self._get('user/v1/zones/{0}'.format(zone_id))
        self._validate(result=result, info=info, expected=[200], method='GET')
        return create_zone_from_json(result['data'])

    def get_zone(self, search):
        """
        Search a zone by name or id.

        @param search: The search string, i.e. a zone name or ID (string)
        @return The zone information (DNSZone)
        """
        result = self._list_pagination('user/v1/zones', query=dict(query=search))
        for zone in result:
            if zone['name'] == search or str(zone['id']) == search:
                return self._get_zone_by_id(zone['id'])
        return None

    def add_record(self, zone_id, record):
        """
        Adds a new record to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        data = record_to_json(record, include_id=False, include_type=True)
        result, info = self._post('user/v1/zones/{0}/records'.format(zone_id, record.id), data=data)
        self._validate(result=result, info=info, expected=[201], method='POST')

    def update_record(self, zone_id, record):
        """
        Update a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        if record.id is None:
            raise HostTechAPIError('Need record ID to update record!')
        data = record_to_json(record, include_id=False, include_type=False)
        result, info = self._put('user/v1/zones/{0}/records/{1}'.format(zone_id, record.id), data=data)
        self._validate(result=result, info=info, expected=[200], method='PUT')

    def delete_record(self, zone_id, record):
        """
        Delete a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        if record.id is None:
            raise HostTechAPIError('Need record ID to delete record!')
        self._delete('user/v1/zones/{0}/records/{1}'.format(zone_id, record.id))
