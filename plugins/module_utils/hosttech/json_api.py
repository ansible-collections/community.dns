# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# The API documentation can be found here: https://api.ns1.hosttech.eu/api/documentation/

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import json

from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url

from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
)

from ansible_collections.community.dns.plugins.module_utils.zone import (
    DNSZone,
    DNSZoneWithRecords,
)

from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
    DNSAPIAuthenticationError,
    ZoneRecordAPI,
)


def _create_record_from_json(source, type=None):
    result = DNSRecord()
    result.id = source['id']
    result.type = source.get('type', type)
    result.ttl = int(source['ttl']) if source['ttl'] is not None else None
    result.comment = source['comment']

    name = source.get('name')
    target = None
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
        target = '{0} {1}'.format(source['pref'], source['name'])
    elif result.type == 'NS':
        name = source['ownername']
        target = source['targetname']
    elif result.type == 'PTR':
        name = ''
        target = '{0} {1}'.format(source['origin'], source['name'])
    elif result.type == 'SRV':
        name = source['service']
        target = '{0} {1} {2} {3}'.format(source['priority'], source['weight'], source['port'], source['target'])
    elif result.type == 'TXT':
        target = source['text']
    elif result.type == 'TLSA':
        target = source['text']
    else:
        raise DNSAPIError('Cannot parse unknown record type: {0}'.format(result.type))

    result.prefix = name or None  # API returns '', we want None
    result.target = target
    return result


def _create_zone_from_json(source):
    zone = DNSZone(source['name'])
    zone.id = source['id']
    # zone.email = source.get('email')
    # zone.ttl = int(source['ttl'])
    # zone.nameserver = source['nameserver']
    return zone


def _create_zone_with_records_from_json(source):
    return DNSZoneWithRecords(
        _create_zone_from_json(source),
        [_create_record_from_json(record) for record in source['records']])


def _record_to_json(record, include_id=False, include_type=True):
    result = {
        'ttl': record.ttl,
        'comment': record.comment or '',
    }
    if include_type:
        result['type'] = record.type
    if include_id:
        result['id'] = record.id

    if record.type == 'A':
        result['name'] = record.prefix or ''
        result['ipv4'] = record.target
    elif record.type == 'AAAA':
        result['name'] = record.prefix or ''
        result['ipv6'] = record.target
    elif record.type == 'CAA':
        result['name'] = record.prefix or ''
        try:
            flag, tag, value = record.target.split(' ', 2)
            result['flag'] = flag
            result['tag'] = tag
            result['value'] = value
        except Exception as e:
            raise DNSAPIError(
                'Cannot split {0} record "{1}" into flag, tag and value: {2}'.format(
                    record.type, record.target, e))
    elif record.type == 'CNAME':
        result['name'] = record.prefix or ''
        result['cname'] = record.target
    elif record.type == 'MX':
        result['ownername'] = record.prefix or ''
        try:
            pref, name = record.target.split(' ', 1)
            result['pref'] = int(pref)
            result['name'] = name
        except Exception as e:
            raise DNSAPIError(
                'Cannot split {0} record "{1}" into integer preference and name: {2}'.format(
                    record.type, record.target, e))
    elif record.type == 'NS':
        result['ownername'] = record.prefix or ''
        result['targetname'] = record.target
    elif record.type == 'PTR':
        try:
            origin, name = record.target.split(' ', 1)
            result['origin'] = origin
            result['name'] = name
        except Exception as e:
            raise DNSAPIError(
                'Cannot split {0} record "{1}" into origin and name: {2}'.format(
                    record.type, record.target, e))
    elif record.type == 'SRV':
        result['service'] = record.prefix or ''
        try:
            priority, weight, port, target = record.target.split(' ', 3)
            result['priority'] = int(priority)
            result['weight'] = int(weight)
            result['port'] = int(port)
            result['target'] = target
        except Exception as e:
            raise DNSAPIError(
                'Cannot split {0} record "{1}" into integer priority, integer weight, integer port and target: {2}'.format(
                    record.type, record.target, e))
    elif record.type == 'TXT':
        result['name'] = record.prefix or ''
        result['text'] = record.target
    elif record.type == 'TLSA':
        result['name'] = record.prefix or ''
        result['text'] = record.target
    else:
        raise DNSAPIError('Cannot serialize unknown record type: {0}'.format(record.type))

    return result


class HostTechJSONAPI(ZoneRecordAPI):
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

    def _extract_error_message(self, result):
        if result is None:
            return ''
        if isinstance(result, dict):
            res = ''
            if result.get('message'):
                res = '{0} with message "{1}"'.format(res, result['message'])
            if 'errors' in result:
                if isinstance(result['errors'], dict):
                    for k, v in sorted(result['errors'].items()):
                        if isinstance(v, list):
                            v = '; '.join(v)
                        res = '{0} (field "{1}": {2})'.format(res, k, v)
            if res:
                return res
        return ' with data: {0}'.format(result)

    def _validate(self, response=None, result=None, info=None, expected=None, method='GET'):
        if info is None:
            raise DNSAPIError('Internal error: info needs to be provided')
        status = info['status']
        url = info['url']
        # Check expected status
        if expected is not None:
            if status not in expected:
                more = self._extract_error_message(result)
                raise DNSAPIError(
                    'Expected HTTP status {0} for {1} {2}, but got HTTP status {3}{4}'.format(
                        ', '.join(['{0}'.format(e) for e in expected]), method, url, status, more))
        else:
            if status < 200 or status >= 300:
                more = self._extract_error_message(result)
                raise DNSAPIError(
                    'Expected successful HTTP status for {0} {1}, but got HTTP status {2}{3}'.format(
                        method, url, status, more))

    def _process_json_result(self, response, info, must_have_content=True, method='GET', expected=None):
        if isinstance(must_have_content, (list, tuple)):
            must_have_content = info['status'] in must_have_content
        # Read content
        try:
            content = response.read()
        except AttributeError:
            content = info.pop('body', None)
        # Check for unauthenticated
        if info['status'] == 401:
            message = 'Unauthorized: the authentication parameters are incorrect (HTTP status 401)'
            try:
                body = self._module.from_json(content.decode('utf8'))
                if body['message']:
                    message = '{0}: {1}'.format(message, body['message'])
            except Exception:
                pass
            raise DNSAPIAuthenticationError(message)
        if info['status'] == 403:
            message = 'Forbidden: you do not have access to this resource (HTTP status 403)'
            try:
                body = self._module.from_json(content.decode('utf8'))
                if body['message']:
                    message = '{0}: {1}'.format(message, body['message'])
            except Exception:
                pass
            raise DNSAPIAuthenticationError(message)
        # Check Content-Type header
        content_type = info.get('content-type')
        for k, v in info.items():
            if k.lower() == 'content-type':
                content_type = v
        if content_type != 'application/json':
            if must_have_content:
                raise DNSAPIError(
                    '{0} {1} did not yield JSON data, but HTTP status code {2} with Content-Type "{3}" and data: {4}'.format(
                        method, info['url'], info['status'], content_type, to_native(content)))
            self._validate(result=content, info=info, expected=expected, method=method)
            return None, info
        # Decode content as JSON
        try:
            result = self._module.from_json(content.decode('utf8'))
        except Exception:
            if must_have_content:
                raise DNSAPIError(
                    '{0} {1} did not yield JSON data, but HTTP status code {2} with data: {3}'.format(
                        method, info['url'], info['status'], to_native(content)))
            self._validate(result=content, info=info, expected=expected, method=method)
            return None, info
        self._validate(result=result, info=info, expected=expected, method=method)
        return result, info

    def _get(self, url, query=None, must_have_content=True, expected=None):
        full_url = self._build_url(url, query)
        if self._debug:
            pass
            # q.q('Request: GET {0}'.format(full_url))
        headers = dict(
            accept='application/json',
            authorization='Bearer {token}'.format(token=self._token),
        )
        response, info = fetch_url(self._module, full_url, headers=headers, method='GET')
        return self._process_json_result(response, info, must_have_content=must_have_content, method='GET', expected=expected)

    def _post(self, url, data=None, query=None, must_have_content=True, expected=None):
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
        return self._process_json_result(response, info, must_have_content=must_have_content, method='POST', expected=expected)

    def _put(self, url, data=None, query=None, must_have_content=True, expected=None):
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
        return self._process_json_result(response, info, must_have_content=must_have_content, method='PUT', expected=expected)

    def _delete(self, url, query=None, must_have_content=True, expected=None):
        full_url = self._build_url(url, query)
        if self._debug:
            pass
            # q.q('Request: DELETE {0}'.format(full_url))
        headers = dict(
            accept='application/json',
            authorization='Bearer {token}'.format(token=self._token),
        )
        response, info = fetch_url(self._module, full_url, headers=headers, method='DELETE')
        return self._process_json_result(response, info, must_have_content=must_have_content, method='DELETE', expected=expected)

    def _list_pagination(self, url, query=None, block_size=100):
        result = []
        offset = 0
        while True:
            query_ = query.copy() if query else dict()
            query_['limit'] = block_size
            query_['offset'] = offset
            res, info = self._get(url, query_, must_have_content=True, expected=[200])
            result.extend(res['data'])
            if len(res['data']) < block_size:
                return result
            offset += block_size

    def get_zone_with_records_by_id(self, id):
        """
        Given a zone ID, return the zone contents with records if found.

        @param id: The zone ID
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """
        result, info = self._get('user/v1/zones/{0}'.format(id), expected=[200, 404], must_have_content=[200])
        if info['status'] == 404:
            return None
        return _create_zone_with_records_from_json(result['data'])

    def get_zone_with_records_by_name(self, name):
        """
        Given a zone name, return the zone contents with records if found.

        @param name: The zone name (string)
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """
        result = self._list_pagination('user/v1/zones', query=dict(query=name))
        for zone in result:
            if zone['name'] == name:
                result, info = self._get('user/v1/zones/{0}'.format(zone['id']), expected=[200])
                return _create_zone_with_records_from_json(result['data'])
        return None

    def get_zone_by_name(self, name):
        """
        Given a zone name, return the zone contents if found.

        @param name: The zone name (string)
        @return The zone information (DNSZone), or None if not found
        """
        result = self._list_pagination('user/v1/zones', query=dict(query=name))
        for zone in result:
            if zone['name'] == name:
                return _create_zone_from_json(zone)
        return None

    def get_zone_by_id(self, id):
        """
        Given a zone ID, return the zone contents if found.

        @param id: The zone ID
        @return The zone information (DNSZone), or None if not found
        """
        result, info = self._get('user/v1/zones/{0}'.format(id), expected=[200, 404], must_have_content=[200])
        if info['status'] == 404:
            return None
        return _create_zone_from_json(result['data'])

    def add_record(self, zone_id, record):
        """
        Adds a new record to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        data = _record_to_json(record, include_id=False, include_type=True)
        result, dummy = self._post('user/v1/zones/{0}/records'.format(zone_id), data=data, expected=[201])
        return _create_record_from_json(result['data'])

    def update_record(self, zone_id, record):
        """
        Update a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        if record.id is None:
            raise DNSAPIError('Need record ID to update record!')
        data = _record_to_json(record, include_id=False, include_type=False)
        result, dummy = self._put('user/v1/zones/{0}/records/{1}'.format(zone_id, record.id), data=data, expected=[200])
        return _create_record_from_json(result['data'])

    def delete_record(self, zone_id, record):
        """
        Delete a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        if record.id is None:
            raise DNSAPIError('Need record ID to delete record!')
        dummy, info = self._delete('user/v1/zones/{0}/records/{1}'.format(zone_id, record.id), must_have_content=False, expected=[204, 404])
        return info['status'] == 204
