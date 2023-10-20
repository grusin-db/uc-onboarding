import json
import re
import sys
from datetime import datetime
import argparse
from databricks.sdk import WorkspaceClient, AccountClient
from typing import Optional

def get_json_dict(file_name:str):
  with open(file_name) as json_file:
    d = json.load(json_file)
    if not isinstance(d, dict):
      raise ValueError("not a dict")
    
    return d
  
def validate_plan(tfplan):  
  for rc in tfplan['resource_changes']:
    yield from validate_resource_change(rc)
      
def validate_resource_change(changed_resource):
  #print("################## changed:", changed_resource)
  r_change = changed_resource['change']
  
  for action in r_change['actions']:
    if action == "delete" and changed_resource['type'] == 'databricks_catalog':
      catalog_name = changed_resource['index']
      catalog_schemas = [ 
        s.name 
        for s in wc.schemas.list(catalog_name)
        if not s.full_name.endswith('.information_schema')
      ]
      
      if catalog_schemas:
        yield ValueError(f"Cannot delete catalog {catalog_name}: catalog is not empty: {catalog_schemas}")
        
def raise_on_validation_error(validation_issues):
  if len(validation_issues):
    print("Validation errors:", file=sys.stderr)
    for idx, v in enumerate(validation_issues):
      print(f"- #{idx+1}: {v}", file=sys.stderr)
    
    raise ValueError(f"{len(validation_issues)} terrafrom plan validation error(s) found. Aborting.")
  else:
    print("Not issues found.")
    return True
        
if __name__ == "__main__":
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument("env_name")
  arg_parser.add_argument("tfplan_json")
  args = arg_parser.parse_args()
    
  env_setup = get_json_dict(".metadata.tmp/current_environment.json")
  if env_setup['name'] != args.env_name:
    raise ValueError("Invalid enviroment name")
  
  print("Running terraform plan validator...")
  
  dbr_host = env_setup['admin_databricks_worskapce_url']
  dbr_account_id = env_setup['databricks_account_id']
  wc = WorkspaceClient(host=dbr_host)
  
  tfplan = get_json_dict(args.tfplan_json)
  validation_issues = list(validate_plan(tfplan))
  raise_on_validation_error(validation_issues)