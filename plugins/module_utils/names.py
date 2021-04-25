# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from ansible.module_utils._text import to_text


_ONLY_ALABELS_MATCHER = re.compile(r'^[a-zA-Z0-9.-]*$')


def only_alabels(domain):
    '''
    Check whether domain name has only alabels.
    '''
    return _ONLY_ALABELS_MATCHER.match(domain) is not None


class InvalidDomainName(Exception):
    '''
    The provided domain name is not valid.
    '''
    pass


def split_into_labels(domain):
    '''
    Split domain name to a list of labels. Start with the top-most label.

    Returns a list of labels and a tail, which is either ``''`` or ``'.'``.
    Raises ``InvalidDomainName`` if the domain name is not valid.
    '''
    result = []
    index = len(domain)
    tail = ''
    if domain.endswith('.'):
        index -= 1
        tail = '.'
    if index > 0:
        while index >= 0:
            next_index = domain.rfind('.', 0, index)
            label = domain[next_index + 1:index]
            if label == '' or label[0] == '-' or label[-1] == '-' or len(label) > 63:
                raise InvalidDomainName(domain)
            result.append(label)
            index = next_index
    return result, tail


def join_labels(labels, tail=''):
    '''
    Combines the result of split_into_labels() back into a domain name.
    '''
    return '.'.join(reversed(labels)) + tail


def normalize_label(label):
    '''
    Normalize a domain label. Returns a lower-case alabel.
    '''
    if label not in ('', '*') and not only_alabels(label):
        # Convert ulabel to alabel
        label = to_text(b'xn--' + to_text(label).encode('punycode'))
    # Always convert to lower-case
    return label.lower()
