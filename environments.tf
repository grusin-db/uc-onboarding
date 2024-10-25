locals {
  current_environment = jsondecode(file("${path.module}/.metadata.tmp/current_environment.json"))
  environments_json   = jsondecode(file("${path.module}/.metadata.tmp/environments.json"))
  environments = {
    for x in local.environments_json :
    x.name => x if x.enabled
  }
  environment = local.environments[terraform.workspace]
}

terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "1.24.0"
    }
  }
}

provider "databricks" {
  alias      = "account"
  host       = "https://accounts.azuredatabricks.net"
  account_id = local.current_environment["databricks_account_id"]
}

provider "databricks" {
  alias = "admin"
  host  = local.current_environment["admin_databricks_worskapce_url"]
}