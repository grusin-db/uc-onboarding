#!/bin/sh
python scripts/build_metadata_tmp.py $1 &&
python scripts/build_dynamic_providers.py $1 &&
python scripts/build_dynamic_imports.py &&
(
  if [ "`cat .terraform/environment 2> /dev/null`" == "$1" ]; then 
    echo "Already cached .terraform env is correct!"
  else 
    echo "Change of env detected! Cleaning up cached .terraform folder!" && rm -rf .terraform 2> /dev/null 
  fi
) &&
terraform init -upgrade -migrate-state &&
terraform workspace select -or-create $1 &&
terraform init -upgrade
  