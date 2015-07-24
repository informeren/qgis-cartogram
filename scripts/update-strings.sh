#!/bin/bash

set -e

locales=$*

# get newest .py and .ui files so we don't update strings unnecessarily

changed_files=0
python_files=$(find . -regex ".*\(ui\|py\)$" -type f)
for python_file in $python_files
do
  changed=$(stat -c %Y "$python_file")
  if [ "${changed}" -gt "${changed_files}" ]
  then
    changed_files=${changed}
  fi
done

# Qt translation stuff
# for .ts file
update=false
for locale in ${locales}
do
  translation_file="i18n/$locale.ts"
  if [ ! -f "${translation_file}" ]
  then
    # Force translation string collection as we have a new language file
    touch "${translation_file}"
    update=true
    break
  fi

  modification_time=$(stat -c %Y "${translation_file}")
  if [ "${changed_files}" -gt "${modification_time}" ]
  then
    # Force translation string collection as a .py file has been updated
    update=true
    break
  fi
done

if [ ${update} == true ]
# retrieve all python files
then
  echo "${python_files}"
  # update .ts
  echo "Please provide translations by editing the translation files below:"
  for locale in ${locales}
  do
    echo "i18n/${locale}.ts"
    # Note we don't use pylupdate with qt .pro file approach as it is flakey
    # about what is made available.
    pylupdate4 -noobsolete ${python_files//\\n/ } -ts "i18n/${locale}.ts"
  done
else
  echo "No need to edit any translation files (.ts) because no python files"
  echo "has been updated since the last update translation."
fi
