#!/bin/bash

set -e

lrelease=$1
locales=$2

for locale in $locales
do
    echo "Processing: $locale.ts"
    $lrelease "i18n/$locale.ts"
done
