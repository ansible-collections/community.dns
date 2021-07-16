# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# Copyright (c) 2020 Markus Bergholz <markuman+spambelongstogoogle@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.urls import fetch_url

from ansible_collections.community.dns.plugins.module_utils.argspec import (
    ArgumentSpec,
)

from ansible_collections.community.dns.plugins.module_utils.json_api_helper import (
    JSONAPIHelper,
)

from ansible_collections.community.dns.plugins.module_utils.provider import (
    ProviderInformation,
)

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
    NOT_PROVIDED,
    ZoneRecordAPI,
    filter_records,
)


def _create_zone_from_json(source):
    zone = DNSZone(source['name'])
    zone.id = source['id']
    info = source.copy()
    info.pop('name')
    info.pop('id')
    zone.info = info
    return zone


def _create_record_from_json(source, type=None):
    result = DNSRecord()
    result.id = source['id']
    result.type = source.get('type', type)
    result.ttl = source['ttl'] if source.get('ttl') is not None else None
    name = source.get('name')
    if name == '@':
        name = None
    result.prefix = name
    result.target = source['value']
    return result


def _record_to_json(record, zone_id):
    result = {
        'ttl': record.ttl,
        'name': record.prefix or '@',
        'value': record.target,
        'type': record.type,
        'zone_id': zone_id,
    }
    return result


class HetznerAPI(ZoneRecordAPI, JSONAPIHelper):
    def __init__(self, http_helper, token, api='https://dns.hetzner.com/api/', debug=False):
        JSONAPIHelper.__init__(self, http_helper, token, api=api, debug=debug)

    def _create_headers(self):
        return {
            'Accept': 'application/json',
            'Auth-API-Token': self._token,
        }

    def _list_pagination(self, url, data_key, query=None, block_size=100, accept_404=False):
        result = []
        page = 1
        while True:
            query_ = query.copy() if query else dict()
            query_['per_page'] = block_size
            query_['page'] = page
            res, info = self._get(url, query_, must_have_content=[200], expected=[200, 404] if accept_404 and page == 1 else [200])
            if accept_404 and page == 1 and info['status'] == 404:
                return None
            result.extend(res[data_key])
            if 'meta' not in res and page == 1:
                return result
            if page >= res['meta']['pagination']['last_page']:
                return result
            page += 1

    def get_zone_by_name(self, name):
        """
        Given a zone name, return the zone contents if found.

        @param name: The zone name (string)
        @return The zone information (DNSZone), or None if not found
        """
        result, info = self._get('v1/zones', expected=[200, 404], query=dict(name=name))
        for zone in result['zones']:
            if zone.get('name') == name:
                return _create_zone_from_json(zone)
        return None

    def get_zone_by_id(self, id):
        """
        Given a zone ID, return the zone contents if found.

        @param id: The zone ID
        @return The zone information (DNSZone), or None if not found
        """
        result, info = self._get('v1/zones/{id}'.format(id=id), expected=[200, 404], must_have_content=[200])
        if info['status'] == 404:
            return None
        return _create_zone_from_json(result['zone'])

    def get_zone_records(self, zone_id, prefix=NOT_PROVIDED, record_type=NOT_PROVIDED):
        """
        Given a zone ID, return a list of records, optionally filtered by the provided criteria.

        @param zone_id: The zone ID
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return A list of DNSrecord objects, or None if zone was not found
        """
        result = self._list_pagination('v1/records', data_key='records', query=dict(zone_id=zone_id), accept_404=True)
        if result is None:
            return None
        return filter_records(
            [_create_record_from_json(record) for record in result],
            prefix=prefix,
            record_type=record_type,
        )

    def add_record(self, zone_id, record):
        """
        Adds a new record to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        data = _record_to_json(record, zone_id=zone_id)
        result, dummy = self._post('v1/records', data=data, expected=[200])
        return _create_record_from_json(result['record'])

    def update_record(self, zone_id, record):
        """
        Update a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        if record.id is None:
            raise DNSAPIError('Need record ID to update record!')
        data = _record_to_json(record, zone_id=zone_id)
        result, dummy = self._put('v1/records/{id}'.format(id=record.id), data=data, expected=[200])
        return _create_record_from_json(result['record'])

    def delete_record(self, zone_id, record):
        """
        Delete a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        if record.id is None:
            raise DNSAPIError('Need record ID to delete record!')
        dummy, info = self._delete('v1/records/{id}'.format(id=record.id), must_have_content=False, expected=[200, 404])
        return info['status'] == 200


class HetznerProviderInformation(ProviderInformation):
    def get_supported_record_types(self):
        """
        Return a list of supported record types.
        """
        return ['A', 'AAAA', 'NS', 'MX', 'CNAME', 'RP', 'TXT', 'SOA', 'HINFO', 'SRV', 'DANE', 'TLSA', 'DS', 'CAA']

    def normalize_prefix(self, prefix):
        """
        Given a prefix (string or None), return its normalized form.

        The result should always be None for the trivial prefix, and a non-zero length DNS name
        for a non-trivial prefix.

        If a provider supports other identifiers for the trivial prefix, such as '@', this
        function needs to convert them to None as well.
        """
        return None if prefix in ('@', '') else prefix


def create_hetzner_provider_information():
    return HetznerProviderInformation()


def create_hetzner_argument_spec():
    return ArgumentSpec(
        argument_spec=dict(
            hetzner_token=dict(
                type='str',
                required=True,
                no_log=True,
                aliases=['api_token'],
                fallback=(env_fallback, ['HETZNER_DNS_TOKEN']),
            ),
        ),
    )


def create_hetzner_api(option_provider, http_helper):
    return HetznerAPI(http_helper, option_provider.get_option('hetzner_token'))
