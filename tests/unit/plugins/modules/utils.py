# Copyright (c) 2025 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function


__metaclass__ = type


try:
    from ansible.module_utils.common.messages import WarningSummary as _WarningSummary
except ImportError:
    _WarningSummary = None


def extract_warnings_texts(result):
    warnings = []
    if result.get('warnings'):
        for warning in result['warnings']:
            if _WarningSummary and isinstance(warning, _WarningSummary):
                if warning.details:
                    warnings.append(warning.details[0].msg)
                continue
            warnings.append(warning)
    return warnings
