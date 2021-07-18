# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import abc

from ansible.module_utils import six


@six.add_metaclass(abc.ABCMeta)
class ProviderInformation(object):
    @abc.abstractmethod
    def get_zone_id_type(self):
        """
        Return the (short) type for zone IDs, like ``'int'`` or ``'str'``.
        """

    @abc.abstractmethod
    def get_record_id_type(self):
        """
        Return the (short) type for record IDs, like ``'int'`` or ``'str'``.
        """

    @abc.abstractmethod
    def get_supported_record_types(self):
        """
        Return a list of supported record types.
        """

    def normalize_prefix(self, prefix):
        """
        Given a prefix (string or None), return its normalized form.

        The result should always be None for the trivial prefix, and a non-zero length DNS name
        for a non-trivial prefix.

        If a provider supports other identifiers for the trivial prefix, such as '@', this
        function needs to convert them to None as well.
        """
        return prefix or None

    def supports_bulk_actions(self):
        """
        Return whether the API supports some kind of bulk actions.
        """
        return False
