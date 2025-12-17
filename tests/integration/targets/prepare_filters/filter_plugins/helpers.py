# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible.module_utils.common.collections import is_sequence


def endswith(text, *suffixes):
    for suffix in suffixes:
        if is_sequence(suffix):
            if text.endswith(tuple(suffix)):
                return True
        else:
            if text.endswith(suffix):
                return True
    return False


class FilterModule:
    """Jinja2 helper filters."""

    def filters(self):
        return {
            "endswith": endswith,
        }
