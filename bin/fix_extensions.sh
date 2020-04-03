#!/bin/bash

# Tiny helper to rename files based on their detect mimetype.
#
# Call with no trailing slash like:
#
#   ./bin/fix_extensions.sh some_dir

for file in $1/*; do
    TYPE=$(file --mime-type -b "$file" | cut -f2 -d/);
    if [[ ! $file =~ \.$TYPE ]]; then
        mv -v "$file" "$file.$TYPE";
    fi
done
