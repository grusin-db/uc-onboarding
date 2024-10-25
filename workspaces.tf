locals {
  workspaces_json = [
    for x in jsondecode(file("${path.module}/.metadata.tmp/workspaces.json")) :
    merge(x, {
      "workspace_name" = reverse(split("/", x["workspace_resource_id"]))[0]
    })
  ]

  workspaces_by_name = {
    for x in local.workspaces_json :
    x.workspace_name => x
    if x.enabled
  }

  workspaces_by_id = {
    for x in local.workspaces_json :
    x.workspace_id => x
    if x.enabled
  }
}

module "dbr_workspace" {
  for_each = local.workspaces_by_name

  source = "./modules/workspace"
  providers = {
    databricks.admin   = databricks.admin
    databricks.account = databricks.account
  }
  databricks_workspace_id = each.value.workspace_id
  databricks_metastore_id = databricks_metastore.this.id

  depends_on = [databricks_metastore.this]
}