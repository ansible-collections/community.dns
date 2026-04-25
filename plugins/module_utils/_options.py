# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

from ansible_collections.community.dns.plugins.module_utils._argspec import ArgumentSpec

if t.TYPE_CHECKING:
    from ._provider import ProviderInformation  # pragma: no cover


def create_bulk_operations_argspec(
    provider_information: ProviderInformation,
) -> ArgumentSpec:
    """
    If the provider supports bulk operations, return an ArgumentSpec object with appropriate
    options. Otherwise return an empty one.
    """
    if not provider_information.supports_bulk_actions():
        return ArgumentSpec()

    return ArgumentSpec(
        argument_spec={
            "bulk_operation_threshold": {"type": "int", "default": 2},
        },
    )


def create_record_transformation_argspec() -> ArgumentSpec:
    return ArgumentSpec(
        argument_spec={
            "txt_transformation": {
                "type": "str",
                "default": "unquoted",
                "choices": ["api", "quoted", "unquoted"],
            },
            "txt_character_encoding": {
                "type": "str",
                "default": "decimal",
                "choices": ["decimal", "octal"],
            },
        },
    )
