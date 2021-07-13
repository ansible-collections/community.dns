# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# Copyright (c) 2020 Markus Bergholz <markuman+spambelongstogoogle@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import abc

from ansible.errors import AnsibleError
from ansible.module_utils import six
from ansible.module_utils.common._collections_compat import Sequence
from ansible.plugins.inventory import BaseInventoryPlugin

from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
    DNSAPIAuthenticationError,
)


@six.add_metaclass(abc.ABCMeta)
class RecordsInventoryModule(BaseInventoryPlugin):
    VALID_ENDINGS = ('dns.yaml', 'dns.yml')

    def __init__(self):
        super(RecordsInventoryModule, self).__init__()

    @abc.abstractmethod
    def setup_api(self):
        pass

    def verify_file(self, path):
        if super(RecordsInventoryModule, self).verify_file(path):
            if path.endswith(self.VALID_ENDINGS):
                return True
        return False

    def parse(self, inventory, loader, path, cache=False):
        super(RecordsInventoryModule, self).parse(inventory, loader, path, cache)

        config = self._read_config_data(path)

        try:
            self.setup_api()

            zone_name = self.get_option('zone_name')
            zone_id = self.get_option('zone_id')

            if zone_name is not None:
                zone_with_records = self.api.get_zone_with_records_by_name(zone_name)
            elif zone_id is not None:
                zone_with_records = self.api.get_zone_with_records_by_id(zone_id)
            else:
                raise AnsibleError('One of zone_name and zone_id must be specified!')

            if zone_with_records is None:
                raise AnsibleError('Zone does not exist')

        except DNSAPIAuthenticationError as e:
            raise AnsibleError('Cannot authenticate: %s' % e)
        except DNSAPIError as e:
            raise AnsibleError('Error: %s' % e)

        filters = self.get_option('filters')

        filter_types = filters.get('type') or ['A', 'AAAA', 'CNAME']
        if not isinstance(filter_types, Sequence) or isinstance(filter_types, six.string_types):
            filter_types = [filter_types]

        for record in zone_with_records.records:
            if record.type in filter_types:
                name = zone_with_records.zone.name
                if record.prefix:
                    name = '%s.%s' % (record.prefix, name)
                self.inventory.add_host(name)
                self.inventory.set_variable(name, 'ansible_host', record.target)
