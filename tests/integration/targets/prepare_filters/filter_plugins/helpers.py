# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations


def endswith(text, *suffixes):
    return any(text.endswith(suffix) for suffix in suffixes)


class FilterModule:
    """Jinja2 helper filters."""

    def filters(self):
        return {
            "endswith": endswith,
        }
