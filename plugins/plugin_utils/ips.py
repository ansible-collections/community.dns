# -*- coding: utf-8 -*-

# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible.errors import AnsibleError
from ansible.module_utils.basic import missing_required_lib

try:
    import ipaddress  # pylint: disable=unused-import
except ImportError as exc:
    IPADDRESS_IMPORT_EXC = exc
else:
    IPADDRESS_IMPORT_EXC = None


def assert_requirements_present(plugin_name, plugin_type):
    if IPADDRESS_IMPORT_EXC is not None:
        msg = f'The {plugin_name} {plugin_type} plugin is missing requirements: {missing_required_lib("ipaddress")}'
        raise AnsibleError(msg) from IPADDRESS_IMPORT_EXC
