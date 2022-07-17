# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.provider import (
    ProviderInformation,
)


class CustomProviderInformation(ProviderInformation):
    def __init__(self, txt_record_handling='decoded'):
        super(CustomProviderInformation, self).__init__()
        self._txt_record_handling = txt_record_handling

    def get_supported_record_types(self):
        return ['A']

    def get_zone_id_type(self):
        return 'str'

    def get_record_id_type(self):
        return 'str'

    def get_record_default_ttl(self):
        return 300

    def txt_record_handling(self):
        return self._txt_record_handling


class CustomProvideOptions(object):
    def __init__(self, option_dict):
        self._option_dict = option_dict

    def get_option(self, name):
        return self._option_dict.get(name)
