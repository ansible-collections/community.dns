#!/usr/bin/env bash
# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

set -eux

export ANSIBLE_TEST_PREFER_VENV=1  # see https://github.com/ansible/ansible/pull/73000#issuecomment-757012395; can be removed once Ansible 2.9 and ansible-base 2.10 support has been dropped
source virtualenv.sh

# Requirements have to be installed prior to running ansible-playbook
# because plugins and requirements are loaded before the task runs

pip install dnspython

ANSIBLE_ROLES_PATH=../ ansible-playbook runme.yml "$@"
