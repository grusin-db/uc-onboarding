#!/bin/sh
sh scripts/plan_changes.sh $1 && terraform apply
