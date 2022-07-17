# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible_collections.community.dns.plugins.module_utils.conversion.base import (
    DNSConversionError,
)

from ansible_collections.community.dns.plugins.module_utils.conversion.converter import (
    RecordConverter,
)

from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
)

from ..helper import (
    CustomProviderInformation,
    CustomProvideOptions,
)


def test_user_api():
    converter = RecordConverter(
        CustomProviderInformation(txt_record_handling='decoded'),
        CustomProvideOptions({'txt_transformation': 'api'}))
    assert converter.process_value_from_user('TXT', u'"xyz \\') == u'"xyz \\'
    assert converter.process_values_from_user('TXT', [u'"xyz \\']) == [u'"xyz \\']
    assert converter.process_value_to_user('TXT', u'"xyz \\') == u'"xyz \\'
    assert converter.process_values_to_user('TXT', [u'"xyz \\']) == [u'"xyz \\']

    record = DNSRecord()
    record.type = 'TXT'

    record.target = u'"xyz \\'
    converter.process_from_user(record)
    assert record.target == u'"xyz \\'

    record.target = u'"xyz \\'
    converter.process_multiple_from_user([record])
    assert record.target == u'"xyz \\'

    record.target = u'"xyz \\'
    converter.process_to_user(record)
    assert record.target == u'"xyz \\'

    record.target = u'"xyz \\'
    converter.process_multiple_to_user([record])
    assert record.target == u'"xyz \\'


def test_user_quoted():
    converter = RecordConverter(
        CustomProviderInformation(txt_record_handling='decoded'),
        CustomProvideOptions({'txt_transformation': 'quoted'}))
    assert converter.process_value_from_user('TXT', u'hëllo " w\\303\\266rld"') == u'hëllo wörld'
    assert converter.process_values_from_user('TXT', [u'hëllo " w\\303\\266rld"']) == [u'hëllo wörld']
    assert converter.process_value_to_user('TXT', u'hello wörld') == u'"hello w\\303\\266rld"'
    assert converter.process_values_to_user('TXT', [u'hello wörld']) == [u'"hello w\\303\\266rld"']

    record = DNSRecord()
    record.type = 'TXT'

    record.target = u'hëllo " w\\303\\266rld"'
    converter.process_from_user(record)
    assert record.target == u'hëllo wörld'

    record.target = u'hëllo " w\\303\\266rld"'
    converter.process_multiple_from_user([record])
    assert record.target == u'hëllo wörld'

    record.target = u'hello wörld'
    converter.process_to_user(record)
    assert record.target == u'"hello w\\303\\266rld"'

    record.target = u'hello wörld'
    converter.process_multiple_to_user([record])
    assert record.target == u'"hello w\\303\\266rld"'

    record.target = u'"a\\o'
    with pytest.raises(DNSConversionError) as exc:
        converter.process_from_user(record)
    print(exc.value.error_message)
    assert exc.value.error_message == (
        u'While processing record from the user: A backslash must not be followed by "o" (index 4)'
    )


def test_user_unquoted():
    converter = RecordConverter(
        CustomProviderInformation(txt_record_handling='decoded'),
        CustomProvideOptions({'txt_transformation': 'unquoted'}))
    assert converter.process_value_from_user('TXT', u'hello "wörl\\d"') == u'hello "wörl\\d"'
    assert converter.process_values_from_user('TXT', [u'hello "wörl\\d"']) == [u'hello "wörl\\d"']
    assert converter.process_value_to_user('TXT', u'hello "wörl\\d"') == u'hello "wörl\\d"'
    assert converter.process_values_to_user('TXT', [u'hello "wörl\\d"']) == [u'hello "wörl\\d"']

    record = DNSRecord()
    record.type = 'TXT'

    record.target = u'hello "wörl\\d"'
    converter.process_from_user(record)
    assert record.target == u'hello "wörl\\d"'

    record.target = u'hello "wörl\\d"'
    converter.process_multiple_from_user([record])
    assert record.target == u'hello "wörl\\d"'

    record.target = u'hello "wörl\\d"'
    converter.process_to_user(record)
    assert record.target == u'hello "wörl\\d"'

    record.target = u'hello "wörl\\d"'
    converter.process_multiple_to_user([record])
    assert record.target == u'hello "wörl\\d"'


def test_api_decoded():
    converter = RecordConverter(
        CustomProviderInformation(txt_record_handling='decoded'),
        CustomProvideOptions({'txt_transformation': 'unquoted'}))
    record = DNSRecord()
    record.type = 'TXT'

    record.target = u'"xyz \\'
    record_2 = converter.clone_from_api(record)
    assert record is not record_2
    assert record.target == u'"xyz \\'
    assert record_2.target == u'"xyz \\'
    converter.process_from_api(record)
    assert record.target == u'"xyz \\'

    record.target = u'"xyz \\'
    records = converter.clone_multiple_from_api([record])
    assert len(records) == 1
    assert record is not records[0]
    assert record.target == u'"xyz \\'
    assert records[0].target == u'"xyz \\'
    converter.process_multiple_from_api([record])
    assert record.target == u'"xyz \\'

    record.target = u'"xyz \\'
    record_2 = converter.clone_to_api(record)
    assert record is not record_2
    assert record.target == u'"xyz \\'
    assert record_2.target == u'"xyz \\'
    converter.process_to_api(record)
    assert record.target == u'"xyz \\'

    record.target = u'"xyz \\'
    records = converter.clone_multiple_to_api([record])
    assert len(records) == 1
    assert record is not records[0]
    assert record.target == u'"xyz \\'
    assert records[0].target == u'"xyz \\'
    converter.process_multiple_to_api([record])
    assert record.target == u'"xyz \\'


def test_api_encoded():
    converter = RecordConverter(
        CustomProviderInformation(txt_record_handling='encoded'),
        CustomProvideOptions({'txt_transformation': 'unquoted'}))
    record = DNSRecord()
    record.type = 'TXT'

    record.target = u'xyz " " \\\\\\303\\266'
    record_2 = converter.clone_from_api(record)
    assert record is not record_2
    assert record.target == u'xyz " " \\\\\\303\\266'
    print(record_2.target)
    assert record_2.target == u'xyz \\ö'
    converter.process_from_api(record)
    assert record.target == u'xyz \\ö'

    record.target = u'xyz " " \\\\\\303\\266'
    records = converter.clone_multiple_from_api([record])
    assert len(records) == 1
    assert record is not records[0]
    assert record.target == u'xyz " " \\\\\\303\\266'
    assert records[0].target == u'xyz \\ö'
    converter.process_multiple_from_api([record])
    assert record.target == u'xyz \\ö'

    record.target = u'xyz \\ö'
    record_2 = converter.clone_to_api(record)
    assert record is not record_2
    assert record.target == u'xyz \\ö'
    assert record_2.target == u'"xyz \\\\\\303\\266"'
    converter.process_to_api(record)
    assert record.target == u'"xyz \\\\\\303\\266"'

    record.target = u'xyz \\ö'
    records = converter.clone_multiple_to_api([record])
    assert len(records) == 1
    assert record is not records[0]
    assert record.target == u'xyz \\ö'
    assert records[0].target == u'"xyz \\\\\\303\\266"'
    converter.process_multiple_to_api([record])
    assert record.target == u'"xyz \\\\\\303\\266"'

    record.target = u'"a'
    with pytest.raises(DNSConversionError) as exc:
        converter.process_from_api(record)
    print(exc.value.error_message)
    assert exc.value.error_message == (
        u'While processing record from API: Missing double quotation mark at the end of value'
    )


def test_api_encoded_no_octal():
    converter = RecordConverter(
        CustomProviderInformation(txt_record_handling='encoded-no-octal'),
        CustomProvideOptions({'txt_transformation': 'unquoted'}))
    record = DNSRecord()
    record.type = 'TXT'

    record.target = u'xyz " " \\\\\\303\\266'
    record_2 = converter.clone_from_api(record)
    assert record is not record_2
    assert record.target == u'xyz " " \\\\\\303\\266'
    print(record_2.target)
    assert record_2.target == u'xyz \\ö'
    converter.process_from_api(record)
    assert record.target == u'xyz \\ö'

    record.target = u'xyz " " \\\\\\303\\266'
    records = converter.clone_multiple_from_api([record])
    assert len(records) == 1
    assert record is not records[0]
    assert record.target == u'xyz " " \\\\\\303\\266'
    assert records[0].target == u'xyz \\ö'
    converter.process_multiple_from_api([record])
    assert record.target == u'xyz \\ö'

    record.target = u'xyz \\ö"'
    record_2 = converter.clone_to_api(record)
    assert record is not record_2
    assert record.target == u'xyz \\ö"'
    assert record_2.target == u'"xyz \\\\ö\\""'
    converter.process_to_api(record)
    assert record.target == u'"xyz \\\\ö\\""'

    record.target = u'xyz \\ö"'
    records = converter.clone_multiple_to_api([record])
    assert len(records) == 1
    assert record is not records[0]
    assert record.target == u'xyz \\ö"'
    assert records[0].target == u'"xyz \\\\ö\\""'
    converter.process_multiple_to_api([record])
    assert record.target == u'"xyz \\\\ö\\""'
