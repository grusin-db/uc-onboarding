import os
import glob
import json
import argparse
from typing import Any, List, Dict, Union
from jsonschema import validate

def print_header(text: str) -> None:
  """prints message in green color

  Args:
      text (str): text to print in green color
  """  
  print('\x1b[1;32;40m' + text + '\x1b[0m')
  
def load_json_from_file(file_path:str) -> Any:
  """load json from file path

  Args:
      file_path (str): file path

  Returns:
      Any: python object containing the json document
  """  
  with open(file_path, 'r') as f:
    return json.load(f)

def get_input_files_setup(env_name: str, input_folder:str='metadata', schemas_folder:str='metadata.schemas') -> dict:
  """get input structure document containing as key the name of dataset and as values the schemas, key names and file names used to build the dataset

  Args:
      env_name (str): name of environment, which will be translated to subfolder name in inputs/ folder
      input_folder (str): root folder where enviroment files are stored (defaut: inputs)

  Returns:
      dict: dictionary descring schema, key_name and file_names for each dataset used by terraform scripts
  """
  
  def _get_team_input_file_paths(dataset):
    paths = glob.glob(f'{input_folder}/{env_name}/*/{dataset}.json') \
      + glob.glob(f'{input_folder}/{env_name}/{dataset}.json') \
      + glob.glob(f'{input_folder}/{dataset}.json')
      
    return [
      os.path.normpath(p).replace("\\", "/")
      for p in paths
    ]
  
  return {
    'catalogs': {
      'schema': load_json_from_file(f"{schemas_folder}/catalogs.json")
      ,'key_name': 'name'
      ,'file_names': _get_team_input_file_paths('catalogs')
    }
    ,'storage-credentials': {
      'schema': load_json_from_file(f"{schemas_folder}/storage-credentials.json")
      ,'key_name': 'name'
      ,'file_names': _get_team_input_file_paths('storage-credentials')
    }
    ,'storage-locations': {
      'schema': load_json_from_file(f"{schemas_folder}/storage-locations.json")
      ,'key_name': 'name'
      ,'file_names': _get_team_input_file_paths('storage-locations')
    }
    ,'workspaces': {
      'schema': load_json_from_file(f"{schemas_folder}/workspaces.json")
      ,'key_name': 'workspace_resource_id'
      ,'file_names': _get_team_input_file_paths('workspaces')
    }
    ,'metastores': {
      'schema': load_json_from_file(f"{schemas_folder}/metastores.json")
      ,'key_name': 'name'
      ,'file_names': _get_team_input_file_paths('metastores')
    }
    ,'workspace-group-master': {
      'schema': load_json_from_file(f"{schemas_folder}/workspace-group-master.json")
      ,'key_name': 'aad_group_name'
      ,'file_names': _get_team_input_file_paths('workspace-group-master')
      ,'check_key_duplicates': False
    }
    ,'environments': {
      'schema': load_json_from_file(f"{schemas_folder}/environments.json")
      ,'key_name': 'name'
      ,'file_names': glob.glob(f'{input_folder}/environments.json')
    }
  }

def print_json_debug(doc: Any) -> None:
  """Prints object using JSON formatter in human readable way

  Args:
      doc (Any): any valid json serializable object (dict, list, primitve)
  """  
  print(json.dumps(doc, indent=2))

def validate_document_schema(doc:Any, schema:dict) -> Exception:
  """validates document against provided jsonschema

  Args:
      doc (Any): document 
      schema (dict): jsonschema object

  Returns:
      Exception: when document does not match the file
  """
  if not schema:
    return None

  validate(instance=doc, schema=schema)

def combine_json_files(file_list: List[str], key_column: str, schema:dict, check_key_duplicates:bool=True) -> List[dict]:
  """Combines multiple JSON document into one big document while checking if documents do not have duplicates. Validates the input files to match the schema.

  Args:
      file_list (List[str]): list of file paths for source jsons
      key_column (str): key column in each json document that will be used for validation if documents from various files are not overriding each other
      schema (dict): schema to validate file with. When set to `None` schema validation will be skipped.
      check_key_duplicates (bool): check if duplicateed key_columns are present, and RaiseException
      
  Returns:
      List[Dict]: List of combined JSON documents.
  """  
  data = {}
  key_tracking = {}
  
  for file_name in file_list:
    print(f"- Opening {file_name}...")
    with open(file_name, 'r') as f:
      doc = json.load(f)
      
      schema_validate_exception = validate_document_schema(doc, schema)
      if schema_validate_exception:
        raise ValueError(f'Failed to validate schema of {file_name}') from schema_validate_exception
      
      for idx, entry in enumerate(doc):
        key = entry.get(key_column)
        if not key:
          raise ValueError(f"Undefined key_column={key_column} in file {file_name} record {idx+1}")
        
        prev_file = key_tracking.get(key)
        if prev_file and check_key_duplicates:
          raise ValueError(f"Double defintion of key_column={key_column} in file {file_name} record {idx+1}. Previous definition present in file {prev_file}")
        
        key_tracking[key] = f"{file_name} record {idx+1}"
        data[key] = entry
    
  return [v for k, v in sorted(data.items())]

def get_combined_datasets(input_file_setup: dict) -> dict:
  """Combines datasets defined in multiple file into one object, validates input files if setup contains validation schema for given dataset.

  Args:
      input_file_setup (dict): dict containing input structure obtaied from `get_input_files_setup(...)` function

  Returns:
      dict: dictionary containing as key the name of the dataset, and as value the combined list of all loaded documentes 
  """ 
  print_header("Loading defintion files from input directories...")
  print("")
  data = {}
  for dataset, setup in input_file_setup.items():
    print(f"Processing dataset {dataset}")
    combined = combine_json_files(setup['file_names'], setup['key_name'], setup['schema'], setup.get('check_key_duplicates'))
    data[dataset] = combined
  
  print("")
  return data

def write_input_tmp_files(combined_datasets: dict, env_name:str, destination_folder: str='.metadata.tmp') -> None:
  """Writes combined data into destination folder, each dataset defined (a key in input dictionary) is written to a seperate file in destination folder.

  Args:
      combined_datasets (dict): the dictionary of combined dataset obtained from `get_combined_datasets(...)` function
      env_name (str): name of the current environment
      destination_folder (str): the destination directory that will be used to create json file per each dataset (default: .metadata.tmp)
  """  
  print_header(f"Writing files into {destination_folder}/ directory...")
  print("")
  os.makedirs(destination_folder, exist_ok=True)
  
  current_environment = [
    e
    for e in combined_datasets['environments']
    if e['name'] == env_name
  ][0]
  
  with open(f'{destination_folder}/current_environment.json', 'w') as f:
    f.write(json.dumps(current_environment, indent=2))
      
  for dataset, data in combined_datasets.items():
    output_file_name = f'{destination_folder}/{dataset}.json'
    print(f"- Creating file {output_file_name}")
    with open(output_file_name, 'w') as f:
      f.write(json.dumps(data, indent=2))
      
def validate_environment_name(env_name: str, input_folder:str='metadata') -> Union[bool, Exception]:
  """validates if environment name is defined in environments.json

  Args:
      env_name (str): the name of enviroment that will be validated for existance
      input_folder (str): the name of the folder where environments.json is stored (default: inputs)

  Returns:
      Union[bool, Exception]: True if name of enviroment is present, otherwise exception
  """  
  envs = get_all_enviroments(input_folder)
  
  if env_name in envs:
    return True
  
  raise ValueError(f"Environment {env_name} was not found in {input_folder}/environments.json")

def get_all_enviroments(input_folder:str='metadata') -> dict:
  """gets of all enviroments setup

  Args:
      input_folder (str, optional): the name of the folder where environments.json is stored (default: inputs)
      
  Returns:
      dict: dictionary containing names of enviroments as keys, and value being setup for enviroment
  """  
  data = {}
  
  with open(f'{input_folder}/environments.json', 'r') as f:
    doc = json.load(f)
    for env_cfg in doc:
      env_name = env_cfg.get('name') 
      data[env_name] = env_cfg
      
  return data

def get_env_aad_groups(env_name:str, input_folder:str='metadata') -> list:
  """gets all aad groups for given enviroment setup

  Args:
      env_name (str): name of the enironment
      input_folder (str, optional): the name of the folder where environments.json is stored (default: inputs)

  Returns:
      list: unique list of all aad groups, sortect alphabetically
  """  
  groups = set()
  input_file_setup = get_input_files_setup(env_name, input_folder)
  combined_datasets = get_combined_datasets(input_file_setup)
  
  for w in combined_datasets['workspaces']:
    g = w.get('account_groups', [])
    groups.update(g)
  
  for g in combined_datasets['workspace-group-master']:
    groups.add(g['aad_group_name'])
    
  return sorted(list(groups))
    
if __name__ == "__main__":
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument("env_name")
  args = arg_parser.parse_args()

  validate_environment_name(args.env_name)

  input_file_setup = get_input_files_setup(args.env_name)

  combined_datasets = get_combined_datasets(input_file_setup)

  write_input_tmp_files(combined_datasets, args.env_name)