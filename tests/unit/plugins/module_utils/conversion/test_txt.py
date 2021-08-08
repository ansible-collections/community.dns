# -*- coding: utf-8 -*-
# (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible_collections.community.dns.plugins.module_utils.conversion.base import (
    DNSConversionError,
)

from ansible_collections.community.dns.plugins.module_utils.conversion.txt import (
    _parse_quoted,
    decode_txt_value,
    encode_txt_value,
)


TEST_DECODE = [
    (r'', ''),
    (r'"" "" ""', ''),
    (r'   ""     ""  ', ''),
    (r'\040\041', ' !'),
    (r'"\040" \041 ""', ' !'),
]


@pytest.mark.parametrize("encoded, decoded", TEST_DECODE)
def test_decode(encoded, decoded):
    decoded_ = decode_txt_value(encoded)
    print(decoded_)
    assert decoded_ == decoded


TEST_ENCODE_DECODE = [
    ('', '""', False),
    ('', '""', True),
    ('Hi', 'Hi', False),
    ('Hi', '"Hi"', True),
    ('"\\', '\\\"\\\\', False),
    ('"\\', '"\\"\\\\"', True),
    ('ä', '\\303\\244', False),
    ('ä', '"\\303\\244"', True),
    ('a b', '"a b"', False),
    ('a b', '"a b"', True),
    (
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        '456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuv'
        'wxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        '456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg hijklmnopqrstu'
        'vwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        False
    ),
    (
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        '456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuv'
        'wxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        '"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        'BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012'
        '3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg" "hijklmnopqr'
        'stuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"',
        True
    ),
    (
        'abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        'BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012'
        '3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstu'
        'vwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        '"abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01'
        '23456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef" ghijklmnopqr'
        'stuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        False
    ),
    (
        'abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        'BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012'
        '3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstu'
        'vwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        '"abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01'
        '23456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef" "ghijklmnopq'
        'rstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"',
        True
    ),
    (
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        '456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg',
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        '456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg',
        False
    ),
    (
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB'
        'CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123'
        '456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg',
        '"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        'BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012'
        '3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg"',
        True
    ),
]


@pytest.mark.parametrize("decoded, encoded, always_quote", TEST_ENCODE_DECODE)
def test_encode_decode(decoded, encoded, always_quote):
    decoded_ = decode_txt_value(encoded)
    print(decoded_)
    assert decoded_ == decoded
    encoded_ = encode_txt_value(decoded, always_quote=always_quote)
    print(encoded_)
    assert encoded_ == encoded


TEST_DECODE_ERROR = [
    ('\\', 'Unexpected backslash at end of string'),
    ('\\a', 'A backslash must not be followed by "a" (index 2)'),
    ('\\0', 'The octal sequence at the end requires 2 more digit(s)'),
    ('\\00', 'The octal sequence at the end requires 1 more digit(s)'),
    ('\\0a', 'The octal sequence at the end requires 1 more digit(s)'),
    ('\\0a0', 'The second letter of the octal sequence at index 3 is not an octal digit, but "a"'),
    ('\\00a', 'The third letter of the octal sequence at index 4 is not an octal digit, but "a"'),
    ('a"b', 'Unexpected double quotation mark inside an unquoted block at position 2'),
    ('"', 'Missing double quotation mark at the end of value'),
]


@pytest.mark.parametrize("encoded, error", TEST_DECODE_ERROR)
def test_decode_error(encoded, error):
    with pytest.raises(DNSConversionError) as exc:
        decode_txt_value(encoded)
    print(exc.value.args[0])
    assert exc.value.args[0] == error
