# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class HostTechError(Exception):
    pass


class HostTechAPIError(HostTechError):
    pass


class HostTechAPIAuthError(HostTechError):
    pass
