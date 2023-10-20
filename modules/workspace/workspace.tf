variable "databricks_workspace_id" {}
variable "databricks_metastore_id" {}

terraform {
  required_providers {
    databricks = {
      source                = "databricks/databricks"
      version               = "1.24.0"
      configuration_aliases = [databricks.admin, databricks.account]
    }
  }
}

locals {
  workspace_groups_master_json = jsondecode(file("${path.module}/../../.metadata.tmp/workspace-group-master.json"))
  workspace_groups_master = {
    for x in local.workspace_groups_master_json :
    x.aad_group_name => x if x.enabled
  }

  workspaces_json = jsondecode(file("${path.module}/../../.metadata.tmp/workspaces.json"))
  workspaces = {
    for x in local.workspaces_json :
    x.workspace_id => x if x.enabled
  }
  workspace_cfg = local.workspaces[var.databricks_workspace_id]

  aad_group_names = setunion(keys(local.workspace_groups_master), toset(lookup(local.workspace_cfg, "account_groups", [])))
}

output "test" {
  value = local.workspaces
}

resource "databricks_metastore_assignment" "this" {
  provider             = databricks.account
  metastore_id         = var.databricks_metastore_id
  workspace_id         = var.databricks_workspace_id
  default_catalog_name = lookup(local.workspace_cfg, "default_catalog_name", "hive_metastore")
}

data "databricks_group" "some" {
  for_each                   = local.aad_group_names
  provider                   = databricks.account
  display_name               = each.key
  workspace_access           = false
  allow_cluster_create       = false
  allow_instance_pool_create = false
  databricks_sql_access      = false

  depends_on = [
    databricks_metastore_assignment.this
  ]
}

resource "databricks_mws_permission_assignment" "some" {
  for_each     = local.aad_group_names
  provider     = databricks.account
  workspace_id = databricks_metastore_assignment.this.workspace_id
  principal_id = data.databricks_group.some[each.key].id
  permissions  = each.key == local.workspace_cfg["role_admin"] ? ["ADMIN"] : ["USER"]

  depends_on = [
    databricks_metastore_assignment.this
  ]
}

