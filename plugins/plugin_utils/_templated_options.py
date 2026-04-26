# Copyright (c) 2022 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this plugin util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

from ansible.template import Templar


class TemplatedOptionProvider:
    def __init__(self, plugin: t.Any, templar: Templar) -> None:
        self.plugin = plugin
        self.templar = templar

    def get_option(self, option: str) -> t.Any:
        value = self.plugin.get_option(option)
        if self.templar.is_template(value):
            value = self.templar.template(variable=value)
        return value
