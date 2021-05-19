#!/bin/sh
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
