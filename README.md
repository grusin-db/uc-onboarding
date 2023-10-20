# Team onboarding script to UC

This application should be ran by UC admin team. It allows UC Admins to easily onboard/offboard a team. The setup in `metadata/` folder can and should be updated by respective teams. This can be accomplished safely by usage of PRs with right quality gates.

## Metadata Folder Structure

- `dev` [name of environment]
  - `team01` [name of team]
    - `catalogs.json` [team's catalogs]
    - `storage-locations.json` [team's storage locations]
    - `storage-credentials.json` [team's storage credentials using azure MI]
    - `workspaces.json` [team's workspaces]
  - `team02` [name of other team]
    - `catalogs.json`
    - `storage-locations.json`
    - `storage-credentials.json`
    - `workspaces.json`
  - `<folder per each team>`
    - `catalogs.json`
    - `storage-locations.json`
    - `storage-credentials.json`
    - `workspaces.json`
  - `ucadmin` [name of admin team]
    - `metastores` [global metastore definitions]
    - `workspace-group-master.json` [global list of aad groups federated to all workspaces]
- `dev` [name of enviroment]
- `acc` [name of enviroment]
- `<folder per each enviroment>`

## JSON configuration files for each resource type

- [x] easy to follow environment setup:
  - [x] single place defintion of global environment options:
    - [x] metastores (see `metadata/<env>/ucadmin/metastores.json)`
​    - [x] account level groups (see `metadata/<env>/ucadmin/workspace-group-master.json`)
    - [x] other options (see `metadata/environments.json`)
  - [x] team specific configuration of:
    - [x] catalogs (see `metadata/<env>/<team>/catalogs.json`)​
    - [x] storage credentials (managed identity only) (see `metadata/<env>/<team>/storage-credentials.json`)​
    - [x] external locations (both managed, and real external storages) (see `metadata/<env>/<team>/storage-locations.json`)​
    - [x] workspaces and their metastore bindings (see `metadata/<env>/<team>/workspaces.json`)
      - [x] account groups to add to workspace
    - [ ] workspace catalog binding (soon, just GA'ed, not TF support yet!)
- [x] reusable blueprints for:
  - [x] object acls: (see. see baseline at repo `uc-team-starterpack` )
    - [x] catalogs​
    - [x] schemas​
    - [x] tables / views​
    - [ ] row level?​ (not yet, feature in private priview)
  - [ ] clusters, dbsql warehouses
- [x] custom plan validators
  - only allow onboarding/deleting catalog if it's empty (see `scripts/validate.py`)
- [x] azure devops pipeline
  - pipeline for terraform plan, approve, apply workflow (with visuals!)
  - see `.azuredevops/tf_plan_approve_apply_workflow.yaml` for end to end workflow
  - workflow can be cut into just to run plan stage for quality gates purpose.


See [scripts/README.md](./scripts/README.md) for details

## How to run

```sh
# init terraform and use metadata to dev environment
make init env_name=dev

# runs above + terraform plan
make plan env_name=dev

# runs above + terraform apply
make apply env_name=dev
```

## Terraform cheat sheet / usefull links

### State in azure storage

- https://learn.microsoft.com/en-us/azure/developer/terraform/store-state-in-azure-storage?tabs=azure-cli

## Local Development Setup

### Install Azure CLI

MacOS

- install brew: [official page with instructions](https://brew.sh/)
- make sure you add brew installation path to your path (you will be promoted to do that!)
- `brew install azure-cli`

Windows

- install from MS Software Center, or from [official ms page](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows?tabs=azure-cli)

## Install Terraform

MacOS

- `brew install terraform`

Windows

- download terraform.exe from official terraform page: https://developer.hashicorp.com/terraform/downloads
  - place file in your **windows home/bin** folder, so that `ls -l ~/bin/terraform.exe` shows the file
- make sure that `terraform` command is running from vs code bash/git bash terminal:
  - run to add alias for the command: `echo "alias terraform=~/bin/terraform.exe" > ~/.profile`
  - restart your terminal (or vscode)
  - running `terraform` in bash should not work now :)

## Install Python

MacOS

- `brew install python`
- or follow https://opensource.com/article/19/5/python-3-default-mac

Windows

- install python from MS Software Center, or from official python website

Other

- set python3 to be default python (in case you have python2): `echo "alias python=/usr/bin/python3" >> ~/.profile`
- and restart your shell, now `python` should be point to `python3`
- in case you dont have `/usr/bin/python3` you can locate your python3 installation by running `whereis python3`

## Usefull terraform commands

these can be ran after `make init env_name=dev`

- save plan to a file: `terraform plan -out=tfplan.tfplan`
- apply saved plan without questions asked: `terraform apply tfplan.tfplan`
- display saved plan in:
  - human readable and colored form: `terraform show tfplan.tfplan`
  - human readable: `terraform show -no-color tfplan.tfpla`
  - as json: `terraform show -json tfplan.tfplan`
  - as human readable json: `terraform show -json tfplan.tfplan | jq '.'` (needs jq installed, jq can also query plan in sqllike way)
