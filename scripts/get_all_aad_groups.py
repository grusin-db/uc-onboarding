import json
import argparse
import build_metadata_tmp as BMT

if __name__ == "__main__":
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument("output", help="output.json file name to write groups to")
  args = arg_parser.parse_args()

  groups = set()

  for env_name in BMT.get_all_enviroments():
    groups.update(BMT.get_env_aad_groups(env_name))
    
  with open(args.output, "w") as f:
    f.write(json.dumps(list(groups), indent=2))
