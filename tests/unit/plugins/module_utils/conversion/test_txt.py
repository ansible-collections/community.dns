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

from ansible_collections.community.dns.plugins.module_utils.conversion.txt import (
    _parse_quoted,
    _get_utf8_length,
    decode_txt_value,
    encode_txt_value,
)


TEST_DECODE = [
    (r'', u''),
    (r'"" "" ""', u''),
    (r'   ""     ""  ', u''),
    (r'\040\041', u' !'),
    (r'"\040" \041 ""', u' !'),
]


@pytest.mark.parametrize("encoded, decoded", TEST_DECODE)
def test_decode(encoded, decoded):
    decoded_ = decode_txt_value(encoded)
    print(repr(decoded_), repr(decoded))
    assert decoded_ == decoded


TEST_GET_UTF8_LENGTH = [
    # See https://en.wikipedia.org/wiki/UTF-8#Examples
    (0xC2, 2),  # first byte of UTF-8 encoding of U+0024
    (0o303, 2),  # first byte of UTF-8 encoding of ä
    (0xE0, 3),  # first byte of UTF-8 encoding of U+0939
    (0xE2, 3),  # first byte of UTF-8 encoding of U+20AC
    (0xED, 3),  # first byte of UTF-8 encoding of U+D55C
    (0xF0, 4),  # first byte of UTF-8 encoding of U+10348
    (0x00, 1),
    (0xFF, 1),
]


@pytest.mark.parametrize("letter_code, length", TEST_GET_UTF8_LENGTH)
def test_get_utf8_length(letter_code, length):
    length_ = _get_utf8_length(letter_code)
    print(length_, length)
    assert length_ == length


TEST_ENCODE_DECODE = [
    (u'', u'""', False, True),
    (u'', u'""', True, True),
    (u'Hi', u'Hi', False, True),
    (u'Hi', u'"Hi"', True, True),
    (u'"\\', u'\\\"\\\\', False, True),
    (u'"\\', u'"\\"\\\\"', True, True),
    (u'ä', u'ä', False, False),
    (u'ä', u'"ä"', True, False),
    (u'ä', u'\\303\\244', False, True),
    (u'ä', u'"\\303\\244"', True, True),
    (u'a b', u'"a b"', False, True),
    (u'a b', u'"a b"', True, True),
    (
        u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        u'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        u'456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuv'
        u'wxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        u'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        u'456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg hijklmnopqrstu'
        u'vwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        False, True
    ),
    (
        u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        u'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        u'456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuv'
        u'wxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        u'"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        u'BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012'
        u'3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg" "hijklmnopqr'
        u'stuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"',
        True, True
    ),
    (
        u'abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        u'BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012'
        u'3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstu'
        u'vwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        u'"abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'
        u'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01'
        u'23456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef" ghijklmnopqr'
        u'stuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        False, True
    ),
    (
        u'abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        u'BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012'
        u'3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstu'
        u'vwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        u'"abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'
        u'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01'
        u'23456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef" "ghijklmnopq'
        u'rstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"',
        True, True
    ),
    (
        u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        u'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        u'456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg',
        u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        u'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        u'456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg',
        False, True
    ),
    (
        u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        u'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        u'456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg',
        u'"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        u'BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012'
        u'3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg"',
        True, True
    ),
    (
        # Avoid splitting up an octal sequence into multiple TXT strings
        u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        u'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        u'456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789aä',
        u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        u'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        u'456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789a\\303 \\244',
        False, True
    ),
    (
        # Avoid splitting up a UTF-8 character into multiple TXT strings
        u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        u'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        u'456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefä',
        u'"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        u'BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012'
        u'3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef" "ä"',
        True, False
    ),
]


@pytest.mark.parametrize("decoded, encoded, always_quote, use_octal", TEST_ENCODE_DECODE)
def test_encode_decode(decoded, encoded, always_quote, use_octal):
    decoded_ = decode_txt_value(encoded)
    print(repr(decoded_), repr(decoded))
    assert decoded_ == decoded
    encoded_ = encode_txt_value(decoded, always_quote=always_quote, use_octal=use_octal)
    print(repr(encoded_), repr(encoded))
    assert encoded_ == encoded


TEST_DECODE_ERROR = [
    (u'\\', 'Unexpected backslash at end of string'),
    (u'\\a', 'A backslash must not be followed by "a" (index 2)'),
    (u'\\0', 'The octal sequence at the end requires 2 more digit(s)'),
    (u'\\00', 'The octal sequence at the end requires 1 more digit(s)'),
    (u'\\0a', 'The octal sequence at the end requires 1 more digit(s)'),
    (u'\\0a0', 'The second letter of the octal sequence at index 3 is not an octal digit, but "a"'),
    (u'\\00a', 'The third letter of the octal sequence at index 4 is not an octal digit, but "a"'),
    (u'a"b', 'Unexpected double quotation mark inside an unquoted block at position 2'),
    (u'"', 'Missing double quotation mark at the end of value'),
]


@pytest.mark.parametrize("encoded, error", TEST_DECODE_ERROR)
def test_decode_error(encoded, error):
    with pytest.raises(DNSConversionError) as exc:
        decode_txt_value(encoded)
    print(exc.value.error_message)
    assert exc.value.error_message == error
