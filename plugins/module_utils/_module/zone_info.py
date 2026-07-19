# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import traceback
import typing as t

from ansible.module_utils.common.text.converters import to_text

from ansible_collections.community.dns.plugins.module_utils._argspec import ArgumentSpec
from ansible_collections.community.dns.plugins.module_utils._zone_record_api import (
    DNSAPIAuthenticationError,
    DNSAPIError,
)

from ._utils import create_zone_name_id_argspec, get_zone_id_or_name

if t.TYPE_CHECKING:  # pragma: no cover
    from ansible.module_utils.basic import AnsibleModule

    from .._provider import ProviderInformation
    from .._zone_record_api import ZoneRecordAPI
    from .._zone_record_set_api import ZoneRecordSetAPI


def create_module_argument_spec(
    provider_information: ProviderInformation,
) -> ArgumentSpec:
    return create_zone_name_id_argspec(provider_information)


def run_module(
    module: AnsibleModule,
    create_api: t.Callable[[], ZoneRecordAPI | ZoneRecordSetAPI],
    provider_information: ProviderInformation,
) -> t.NoReturn:
    try:
        # Create API
        api = create_api()

        # Get zone information
        zone_name_in, zone_id_in = get_zone_id_or_name(
            module.params, provider_information
        )
        if zone_name_in is not None:
            zone = api.get_zone_by_name(zone_name_in)
        else:
            zone = api.get_zone_by_id(zone_id_in)
        if zone is None:
            module.fail_json(msg="Zone not found")

        module.exit_json(
            changed=False,
            zone_name=zone.name,
            zone_id=zone.id,
            zone_info=zone.info,
        )
    except DNSAPIAuthenticationError as e:
        module.fail_json(
            msg=f"Cannot authenticate: {e}",
            error=to_text(e),
            exception=traceback.format_exc(),
        )
    except DNSAPIError as e:
        module.fail_json(
            msg=f"Error: {e}",
            error=to_text(e),
            exception=traceback.format_exc(),
        )
