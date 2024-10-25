locals {
  metastores_json = jsondecode(file("${path.module}/.metadata.tmp/metastores.json"))
  metastore_setup = one([
    for x in local.metastores_json :
    x if x.enabled
  ])
}

resource "databricks_metastore" "this" {
  provider      = databricks.account
  name          = local.metastore_setup.name
  region        = local.metastore_setup.region
  storage_root  = local.metastore_setup.adls_gen2_path
  owner         = local.metastore_setup.role_owner
  force_destroy = false

  lifecycle {
    precondition {
      condition     = local.current_environment["name"] == terraform.workspace
      error_message = "terraform workspace does not match configuration enviroment"
    }
  }
}