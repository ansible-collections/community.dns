# Copyright (c) 2025 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

try:
    from ansible.module_utils.datatag import deprecate_value as _deprecate_value

    HAS_DEPRECATE_VALUE = True
except ImportError:
    HAS_DEPRECATE_VALUE = False

if t.TYPE_CHECKING:  # pragma: no cover
    _T = t.TypeVar("_T")


def deprecate_value(
    value: _T, *, msg: str, version: str, help_text: str | None = None
) -> _T:
    """
    Given a value, tag it as deprecated (with message, removal version, and optional help text).

    For ansible-core versions that do not support data tagging, simply returns the value as-is.
    """
    if not HAS_DEPRECATE_VALUE:
        return value
    # Assign this to a variable to work around a bug in ansible-test's pylint check (https://github.com/ansible/ansible/issues/85614)
    collection_name = "community.dns"
    return _deprecate_value(
        value,
        msg,
        collection_name=collection_name,
        version=version,
        help_text=help_text,
    )
