locals {
  storage_locations_json = jsondecode(file("${path.module}/.metadata.tmp/storage-locations.json"))
  storage_locations = {
    for x in local.storage_locations_json :
    x.name => x if x.enabled
  }

  storage_location_grants = {
    for name, x in local.storage_locations :
    name => x if length(lookup(x, "grants", {})) > 0
  }
}

# https://registry.terraform.io/providers/databricks/databricks/latest/docs/resources/external_location
resource "databricks_external_location" "storage_location" {
  provider        = databricks.admin
  for_each        = local.storage_locations
  name            = each.key
  url             = each.value.adls_gen2_resource_uri
  credential_name = each.value.storage_credential_name
  owner           = each.value.role_owner
  comment         = "Managed by TF"
  skip_validation = true
  depends_on = [
    databricks_storage_credential.storage_credential
  ]
}

module "storage_location_grants" {
  providers = {
    databricks = databricks.admin
  }
  for_each         = local.storage_location_grants
  source           = "./modules/storage_location_grants"
  storage_location = each.key
  grants           = each.value.grants
  depends_on       = [databricks_external_location.storage_location]
}
