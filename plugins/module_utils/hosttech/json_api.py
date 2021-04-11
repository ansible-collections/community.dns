# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import json

from ansible.module_utils.six import raise_from
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url

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


class HostTechJSONAPI(HostTechAPI):
    def __init__(self, module, token, api='https://api.ns1.hosttech.eu/api/', debug=False):
        """
        Create a new HostTech API instance with given username and password.
        """
        self._api = api
        self._module = module
        self._token = token
        self._debug = debug

    def _announce(self, msg):
        if self._debug:
            pass
            # q.q('{0} {1} {2}'.format('=' * 4, msg, '=' * 40))

    def _build_url(self, url, query=None):
        return '{0}{1}{2}'.format(self._api, url, ('?' + urlencode(query)) if query else '')

    def _execute(self, command, result_name, acceptable_types):
        if self._debug:
            pass
            # q.q('Request: {0}'.format(command))
        # TODO implement!

    def _process_json_result(self, response, info, must_have_content=True):
        try:
            content = response.read()
        except AttributeError:
            content = info.pop('body', None)
        try:
            return self._module.from_json(content.decode('utf8')), info
        except Exception:
            if must_have_content:
                self._module.fail_json(
                    'GET {0} did not yield JSON data, but HTTP status code {1} with data: {2}'.format(
                        full_url, info['status'], to_native(content)))
            return None, info

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
        return self._process_json_result(response, info, must_have_content=must_have_content)

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
        return self._process_json_result(response, info, must_have_content=must_have_content)

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
        return self._process_json_result(response, info, must_have_content=must_have_content)

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
        # TODO check status 204

    def _list_pagination(self, url, query=None):
        result = []
        block_size = 100
        offset = 0
        while True:
            query_ = query.copy() if query else dict()
            query_['limit'] = block_size
            query_['offset'] = offset
            res, info = self._get(url, query_, must_have_content=True)
            result.extend(res['data'])
            if len(res) < block_size:
                return result
            offset += block_size

    def _get_zone_by_id(self, zone_id):
        self._announce('get zone by id')
        result, info = self._get('user/v1/zones/{0}'.format(zone_id))
        return DNSZone.create_from_json(result['data'])

    def get_zone(self, search):
        """
        Search a zone by name or id.

        @param search: The search string, i.e. a zone name or ID (string)
        @return The zone information (DNSZone)
        """
        self._announce('get zone')
        result = self._list_pagination('user/v1/zones', query=dict(query=search))
        for zone in result:
            if zone['name'] == search or str(zone['id']) == search:
                return self._get_zone_by_id(zone['id'])
        return None

    def add_record(self, search, record):
        """
        Adds a new record to an existing zone.

        @param zone: The search string, i.e. a zone name or ID (string)
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        self._announce('add record')
        # TODO implement!

    def update_record(self, record):
        """
        Update a record.

        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        if record.id is None:
            raise HostTechAPIError('Need record ID to update record!')
        self._announce('update record')
        # TODO implement!

    def delete_record(self, record):
        """
        Delete a record.

        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        if record.id is None:
            raise HostTechAPIError('Need record ID to delete record!')
        self._announce('delete record')
        # TODO implement!
