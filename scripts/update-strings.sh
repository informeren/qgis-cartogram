#!/bin/bash

set -e

locales=$*

# get newest .py and .ui files so we don't update strings unnecessarily
changed_files=0
python_files=$(find . -regex ".*\(ui\|py\)$" -type f)
for python_file in $python_files; do
  changed=$(stat -c %Y "$python_file")
  if [ "$changed" -gt "$changed_files" ]; then
    changed_files=${changed}
  fi
done

# figure out whether we need to update the .ts files
update=false
for locale in ${locales}; do
  translation_file="i18n/$locale.ts"
  if [ ! -f "$translation_file" ]; then
    # Force translation string collection as we have a new language file
    touch "${translation_file}"
    update=true
    break
  fi

  modification_time=$(stat -c %Y "$translation_file")
  if [ "$changed_files" -gt "$modification_time" ]; then
    # Force translation string collection as a .py file has been updated
    update=true
    break
  fi
done

# create or update .ts files
if [ $update == true ]; then
  echo -e "Updating from source strings from:\n$python_files"

  IFS=$'\n'
  python_files=($python_files)

  echo "Please provide translations by editing the translation files below:"
  for locale in $locales; do
    echo "i18n/$locale.ts"
    # we pass the source files by hand since using the .pro file is flakey
    pylupdate4 -noobsolete "${python_files[@]}" -ts "i18n/$locale.ts"
  done
else
  echo "No need to edit any translation files (.ts) because no python files"
  echo "have been updated since the last translation update."
fi
