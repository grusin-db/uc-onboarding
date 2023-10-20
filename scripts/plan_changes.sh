#!/bin/sh
sh scripts/pre_tf.sh $1 && 
  terraform plan -out tfplan $2 $3 $4 &&
  terraform show -json tfplan > tfplan.json &&
  python scripts/validate_plan.py $1 tfplan.json