# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import sys

from ansible.module_utils.common.text.converters import to_bytes, to_native

from ansible_collections.community.dns.plugins.module_utils.conversion.base import (
    DNSConversionError,
)


_OCTAL_DIGITS = b'0123456789'

_STATE_OUTSIDE = 0
_STATE_QUOTED_STRING = 1
_STATE_UNQUOTED_STRING = 3


if sys.version_info[0] < 3:
    _int_to_byte = chr
else:
    def _int_to_byte(value):
        return bytes((value, ))


def _parse_quoted(value, index):
    if index == len(value):
        raise DNSConversionError('Unexpected backslash at end of string')
    letter = value[index:index + 1]
    index += 1
    if letter in (b'\\', b'"'):
        return letter, index
    # This must be an octal sequence
    v2 = _OCTAL_DIGITS.find(letter)
    if v2 < 0:
        # It is apparently not - error out
        raise DNSConversionError(
            'A backslash must not be followed by "{letter}" (index {index})'.format(letter=to_native(letter), index=index))
    if index + 1 >= len(value):
        # We need more letters for a three-digit octal sequence
        raise DNSConversionError(
            'The octal sequence at the end requires {missing} more digit(s)'.format(missing=index + 2 - len(value)))
    letter = value[index:index + 1]
    index += 1
    v1 = _OCTAL_DIGITS.find(letter)
    if v1 < 0:
        raise DNSConversionError(
            'The second letter of the octal sequence at index {index} is not an octal digit, but "{letter}"'.format(letter=to_native(letter), index=index))
    letter = value[index:index + 1]
    index += 1
    v0 = _OCTAL_DIGITS.find(letter)
    if v0 < 0:
        raise DNSConversionError(
            'The third letter of the octal sequence at index {index} is not an octal digit, but "{letter}"'.format(letter=to_native(letter), index=index))
    return _int_to_byte((v2 << 6) | (v1 << 3) | v0), index


def decode_txt_value(value):
    """
    Given an encoded TXT value, decodes it.

    Raises DNSConversionError in case of errors.
    """
    value = to_bytes(value)
    state = _STATE_OUTSIDE
    index = 0
    length = len(value)
    result = []
    while index < length:
        letter = value[index:index + 1]
        index += 1
        if letter == b' ':
            if state == _STATE_QUOTED_STRING:
                result.append(letter)
            else:
                state = _STATE_OUTSIDE
        elif letter == b'\\':
            if state != _STATE_QUOTED_STRING:
                state = _STATE_UNQUOTED_STRING
            letter, index = _parse_quoted(value, index)
            result.append(letter)
        elif letter == b'"':
            if state == _STATE_QUOTED_STRING:
                state = _STATE_OUTSIDE
            elif state == _STATE_OUTSIDE:
                state = _STATE_QUOTED_STRING
            else:
                raise DNSConversionError(
                    'Unexpected double quotation mark inside an unquoted block at position {index}'.format(index=index))
        else:
            if state != _STATE_QUOTED_STRING:
                state = _STATE_UNQUOTED_STRING
            result.append(letter)

    if state == _STATE_QUOTED_STRING:
        raise DNSConversionError('Missing double quotation mark at the end of value')

    return to_native(b''.join(result))


def encode_txt_value(value, always_quote=False):
    """
    Given a decoded TXT value, encodes it.

    If always_quote is set to True, always use double quotes for all strings.
    """
    value = to_bytes(value)
    buffer = []
    output = []

    def append(buffer):
        value = b''.join(buffer)
        if b' ' in value or not value or always_quote:
            value = b'"%s"' % value
        output.append(value)

    index = 0
    length = len(value)
    while index < length:
        letter = value[index:index + 1]
        index += 1

        # Add letter
        if letter in (b'"', b'\\'):
            buffer.append(b'\\')
            buffer.append(letter)
        elif not (0o40 <= ord(letter) < 0o177):
            letter_value = ord(letter)
            buffer.append(b'\\')
            v2 = (letter_value >> 6) & 7
            v1 = (letter_value >> 3) & 7
            v0 = letter_value & 7
            buffer.append(_OCTAL_DIGITS[v2:v2 + 1])
            buffer.append(_OCTAL_DIGITS[v1:v1 + 1])
            buffer.append(_OCTAL_DIGITS[v0:v0 + 1])
        else:
            buffer.append(letter)

        # Split if too long
        if len(buffer) >= 255:
            append(buffer[:255])
            buffer = buffer[255:]

    if buffer or not output:
        append(buffer)

    return to_native(b' '.join(output))
