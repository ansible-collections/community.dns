# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This module_utils is PRIVATE and should only be used by this collection. Breaking changes can occur any time.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
)


def normalize_dns_name(name):
    # Get zone and record.
    name = name.lower()
    if name[-1:] == '.':
        name = name[:-1]
    return name


def get_prefix(normalized_record, normalized_zone):
    # Convert record to prefix
    if not normalized_record.endswith('.' + normalized_zone) and normalized_record != normalized_zone:
        raise DNSAPIError('Record must be in zone')
    if normalized_record == normalized_zone:
        return None, normalized_record
    else:
        return normalized_record[:len(normalized_record) - len(normalized_zone) - 1], normalized_record
