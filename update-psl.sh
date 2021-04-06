#!/bin/sh
set +eux

curl https://publicsuffix.org/list/public_suffix_list.dat --output plugins/public_suffix_list.dat

git status plugins/public_suffix_list.dat

if [ -n "$(git status --porcelain=v1 plugins/public_suffix_list.dat)" ]; then
    git diff
    exit 1
fi
