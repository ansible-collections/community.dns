# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence  # pragma: no cover

    from ansible.module_utils.basic import AnsibleModule  # pragma: no cover

    class OptionProvider(t.Protocol):  # pragma: no cover
        def get_option(self, option: str) -> t.Any: ...  # pragma: no cover


class ArgumentSpec:
    def __init__(
        self,
        argument_spec: Mapping[str, t.Any] | None = None,
        *,
        required_together: Sequence[Sequence[str]] | None = None,
        required_if: (
            Sequence[
                tuple[str, t.Any, Sequence[str]]
                | tuple[str, t.Any, Sequence[str], bool]
            ]
            | None
        ) = None,
        required_one_of: Sequence[Sequence[str]] | None = None,
        mutually_exclusive: Sequence[Sequence[str]] | None = None,
    ):
        self.argument_spec: dict[str, t.Any] = {}
        self.required_together: list[Sequence[str]] = []
        self.required_if: list[
            tuple[str, t.Any, Sequence[str]] | tuple[str, t.Any, Sequence[str], bool]
        ] = []
        self.required_one_of: list[Sequence[str]] = []
        self.mutually_exclusive: list[Sequence[str]] = []
        if argument_spec:
            self.argument_spec.update(argument_spec)
        if required_together:
            self.required_together.extend(required_together)
        if required_if:
            self.required_if.extend(required_if)
        if required_one_of:
            self.required_one_of.extend(required_one_of)
        if mutually_exclusive:
            self.mutually_exclusive.extend(mutually_exclusive)

    def merge(self, other: ArgumentSpec) -> t.Self:
        self.argument_spec.update(other.argument_spec)
        self.required_together.extend(other.required_together)
        self.required_if.extend(other.required_if)
        self.required_one_of.extend(other.required_one_of)
        self.mutually_exclusive.extend(other.mutually_exclusive)
        return self

    def to_kwargs(self) -> dict[str, t.Any]:
        return {
            "argument_spec": self.argument_spec,
            "required_together": self.required_together,
            "required_if": self.required_if,
            "required_one_of": self.required_one_of,
            "mutually_exclusive": self.mutually_exclusive,
        }


class ModuleOptionProvider:
    def __init__(self, module: AnsibleModule) -> None:
        self.module = module

    def get_option(self, option: str) -> t.Any:
        return self.module.params[option]
