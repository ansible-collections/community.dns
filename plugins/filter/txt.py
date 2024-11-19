# -*- coding: utf-8 -*-

# Copyright (c) 2020-2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible.errors import AnsibleFilterError
from ansible.module_utils.common.text.converters import to_text

from ansible_collections.community.dns.plugins.module_utils.conversion.txt import (
    decode_txt_value,
    encode_txt_value,
)


def quote_txt(value, always_quote=False, character_encoding='decimal'):
    if not isinstance(value, (str, bytes)):
        raise AnsibleFilterError('Input for community.dns.quote_txt must be a string')
    if not isinstance(always_quote, bool):
        raise AnsibleFilterError(f'always_quote must be a boolean, not {always_quote!r}')
    if character_encoding not in ('decimal', 'octal'):
        raise AnsibleFilterError(f'character_encoding must be "decimal" or "octal", not {character_encoding!r}')
    value = to_text(value)
    return encode_txt_value(value, always_quote=always_quote, character_encoding=character_encoding)


def unquote_txt(value, character_encoding='decimal'):
    if not isinstance(value, (str, bytes)):
        raise AnsibleFilterError('Input for community.dns.unquote_txt must be a string')
    if character_encoding not in ('decimal', 'octal'):
        raise AnsibleFilterError(f'character_encoding must be "decimal" or "octal", not {character_encoding!r}')
    value = to_text(value)
    return decode_txt_value(value, character_encoding=character_encoding)


class FilterModule:
    '''Ansible jinja2 filters'''

    def filters(self):
        return {
            'quote_txt': quote_txt,
            'unquote_txt': unquote_txt,
        }
