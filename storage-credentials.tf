locals {
  storage_credentials_json = jsondecode(file("${path.module}/.metadata.tmp/storage-credentials.json"))
  storage_credentials = {
    for x in local.storage_credentials_json :
    x.name => x if x.enabled
  }
}

# https://registry.terraform.io/providers/databricks/databricks/latest/docs/resources/storage_credential
resource "databricks_storage_credential" "storage_credential" {
  provider = databricks.account
  for_each = local.storage_credentials
  name     = each.key
  azure_managed_identity {
    access_connector_id = each.value.access_connector_id
  }
  comment = "Managed identity credential by TF"
  owner   = each.value.role_owner
  depends_on = [
    databricks_metastore.this
  ]
}