# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import warnings

import pytest

from ansible_collections.community.dns.plugins.module_utils._conversion.base import (
    DNSConversionError,
)
from ansible_collections.community.dns.plugins.module_utils._conversion.txt import (
    _get_utf8_length,
    decode_txt_value,
    encode_txt_value,
)

TEST_DECODE = [
    (r"", "decimal", ""),
    (r'"" "" ""', "decimal", ""),
    (r'   ""     ""  ', "decimal", ""),
    (r"\032\033", "decimal", " !"),
    (r'"\032" \033 ""', "decimal", " !"),
    (r"\040\041", "octal", " !"),
    (r'"\040" \041 ""', "octal", " !"),
]


@pytest.mark.parametrize("encoded, character_encoding, decoded", TEST_DECODE)
def test_decode(encoded, character_encoding, decoded):
    decoded_ = decode_txt_value(encoded, character_encoding=character_encoding)
    print(repr(decoded_), repr(decoded))
    assert decoded_ == decoded


TEST_GET_UTF8_LENGTH = [
    # See https://en.wikipedia.org/wiki/UTF-8#Examples
    (0xC2, 2),  # first byte of UTF-8 encoding of U+0024
    (0xC3, 2),  # first byte of UTF-8 encoding of ä
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
    ("", '""', False, True, "decimal"),
    ("", '""', True, True, "decimal"),
    ("Hi", "Hi", False, True, "decimal"),
    ("Hi", '"Hi"', True, True, "decimal"),
    ('"\\', '\\"\\\\', False, True, "decimal"),
    ('"\\', '"\\"\\\\"', True, True, "decimal"),
    ("ä", "ä", False, False, "decimal"),
    ("ä", '"ä"', True, False, "decimal"),
    ("ä", "\\195\\164", False, True, "decimal"),
    ("ä", '"\\195\\164"', True, True, "decimal"),
    ("a b", '"a b"', False, True, "decimal"),
    ("a b", '"a b"', True, True, "decimal"),
    (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuv"
        "wxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg hijklmnopqrstu"
        "vwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        False,
        True,
        "decimal",
    ),
    (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuv"
        "wxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        '"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        "BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012"
        '3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg" "hijklmnopqr'
        'stuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"',
        True,
        True,
        "decimal",
    ),
    (
        "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA"
        "BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012"
        "3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstu"
        "vwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        '"abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01"
        '23456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef" ghijklmnopqr'
        "stuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        False,
        True,
        "decimal",
    ),
    (
        "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA"
        "BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012"
        "3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstu"
        "vwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        '"abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01"
        '23456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef" "ghijklmnopq'
        'rstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"',
        True,
        True,
        "decimal",
    ),
    (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg",
        False,
        True,
        "decimal",
    ),
    (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg",
        '"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        "BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012"
        '3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefg"',
        True,
        True,
        "decimal",
    ),
    (
        # Avoid splitting up an escape into multiple TXT strings
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        '456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef"\\',
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        '456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef \\"\\\\',
        False,
        True,
        "decimal",
    ),
    (
        # Avoid splitting up an decimal sequence into multiple TXT strings
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789aä",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789a\\195 \\164",
        False,
        True,
        "decimal",
    ),
    (
        # Avoid splitting up a UTF-8 character into multiple TXT strings
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefä",
        '"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        "BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012"
        '3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef" "ä"',
        True,
        False,
        "decimal",
    ),
    (
        # Avoid splitting up an octal sequence into multiple TXT strings
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789aä",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789a\\303 \\244",
        False,
        True,
        "octal",
    ),
    (
        # Avoid splitting up a UTF-8 character into multiple TXT strings
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzAB"
        "CDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123"
        "456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefä",
        '"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzA'
        "BCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012"
        '3456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdef" "ä"',
        True,
        False,
        "octal",
    ),
]


@pytest.mark.parametrize(
    "decoded, encoded, always_quote, use_character_encoding, character_encoding",
    TEST_ENCODE_DECODE,
)
def test_encode_decode(
    decoded, encoded, always_quote, use_character_encoding, character_encoding
):
    decoded_ = decode_txt_value(encoded, character_encoding=character_encoding)
    print(repr(decoded_), repr(decoded))
    assert decoded_ == decoded
    encoded_ = encode_txt_value(
        decoded,
        always_quote=always_quote,
        use_character_encoding=use_character_encoding,
        character_encoding=character_encoding,
    )
    print(repr(encoded_), repr(encoded))
    assert encoded_ == encoded


TEST_DECODE_ERROR = [
    ("\\", "decimal", "Unexpected backslash at end of string"),
    ("\\a", "decimal", 'A backslash must not be followed by "a" (index 2)'),
    ("\\0", "decimal", "The decimal sequence at the end requires 2 more digit(s)"),
    ("\\00", "decimal", "The decimal sequence at the end requires 1 more digit(s)"),
    ("\\0a", "decimal", "The decimal sequence at the end requires 1 more digit(s)"),
    (
        "\\0a0",
        "decimal",
        'The second letter of the decimal sequence at index 3 is not a decimal digit, but "a"',
    ),
    (
        "\\00a",
        "decimal",
        'The third letter of the decimal sequence at index 4 is not a decimal digit, but "a"',
    ),
    ("\\0", "octal", "The octal sequence at the end requires 2 more digit(s)"),
    ("\\00", "octal", "The octal sequence at the end requires 1 more digit(s)"),
    ("\\0a", "octal", "The octal sequence at the end requires 1 more digit(s)"),
    (
        "\\0a0",
        "octal",
        'The second letter of the octal sequence at index 3 is not a octal digit, but "a"',
    ),
    (
        "\\00a",
        "octal",
        'The third letter of the octal sequence at index 4 is not a octal digit, but "a"',
    ),
    (
        'a"b',
        "decimal",
        "Unexpected double quotation mark inside an unquoted block at position 2",
    ),
    ('"', "decimal", "Missing double quotation mark at the end of value"),
]


@pytest.mark.parametrize("encoded, character_encoding, error", TEST_DECODE_ERROR)
def test_decode_error(encoded, character_encoding, error):
    with pytest.raises(DNSConversionError) as exc:
        decode_txt_value(encoded, character_encoding=character_encoding)
    print(exc.value.error_message)
    assert exc.value.error_message == error


def test_validation():
    with pytest.raises(ValueError) as exc:
        decode_txt_value("foo", character_encoding="foo")
    print(exc.value.args)
    assert exc.value.args == ('character_encoding must be set to "octal" or "decimal"',)

    with pytest.raises(ValueError) as exc:
        encode_txt_value("foo", character_encoding="foo")
    print(exc.value.args)
    assert exc.value.args == ('character_encoding must be set to "octal" or "decimal"',)


def test_deprecation():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        encode_txt_value("foo")

        print(len(w), w)
        assert len(w) >= 1
        warning = w[0]
        assert issubclass(warning.category, DeprecationWarning)
        msg = (
            "The default value of the encode_txt_value parameter character_encoding is deprecated."
            ' Set explicitly to "octal" for the old behavior, or set to "decimal" for the new and correct behavior.'
        )
        print(str(warning.message))
        assert msg == str(warning.message)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        encode_txt_value("foo", use_octal=True, character_encoding="octal")

        print(len(w), w)
        assert len(w) >= 1
        warning = w[0]
        assert issubclass(warning.category, DeprecationWarning)
        msg = "The encode_txt_value parameter use_octal is deprecated. Use use_character_encoding instead."
        print(str(warning.message))
        assert msg == str(warning.message)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        decode_txt_value("foo")

        print(len(w), w)
        assert len(w) >= 1
        warning = w[0]
        assert issubclass(warning.category, DeprecationWarning)
        msg = (
            "The default value of the decode_txt_value parameter character_encoding is deprecated."
            ' Set explicitly to "octal" for the old behavior, or set to "decimal" for the new and correct behavior.'
        )
        print(str(warning.message))
        assert msg == str(warning.message)

    with pytest.raises(ValueError) as exc:
        encode_txt_value("foo", use_octal=True, use_character_encoding=True)
    print(exc.value.args)
    assert exc.value.args == (
        "Cannot use both use_character_encoding and use_octal. Use only use_character_encoding!",
    )
