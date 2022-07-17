#!/bin/sh
# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

set +eux

curl https://publicsuffix.org/list/public_suffix_list.dat --output plugins/public_suffix_list.dat

git status plugins/public_suffix_list.dat

if [ -n "$(git status --porcelain=v1 plugins/public_suffix_list.dat)" ]; then
    git diff
    if [ ! -e changelogs/fragments/update-psl.yml ]; then
        echo "bugfixes:" > changelogs/fragments/update-psl.yml
        echo '  - "Update Public Suffix List."' >> changelogs/fragments/update-psl.yml
    fi
    exit 1
fi
