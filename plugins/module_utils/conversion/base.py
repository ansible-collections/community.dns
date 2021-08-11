# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class DNSConversionError(Exception):
    def __init__(self, message):
        super(DNSConversionError, self).__init__(message)
        self.error_message = message
