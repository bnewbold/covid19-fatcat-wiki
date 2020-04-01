#!/bin/bash

for file in $1/*; do
    TYPE=$(file --mime-type -b "$file" | cut -f2 -d/);
    if [[ ! $file =~ \.$TYPE ]]; then
        mv -v "$file" "$file.$TYPE";
    fi
done
