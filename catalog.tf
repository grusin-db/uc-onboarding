locals {
  catalogs_json = jsondecode(file("${path.module}/.metadata.tmp/catalogs.json"))
  catalogs = {
    for x in local.catalogs_json :
    x.name => x if x.enabled
  }

  catalog_grants = {
    for name, x in local.catalogs :
    name => x if length(lookup(x, "grants", {})) > 0
  }
}

resource "databricks_catalog" "catalog" {
  provider      = databricks.admin
  for_each      = local.catalogs
  metastore_id  = databricks_metastore.this.id
  name          = each.key
  force_destroy = false
  storage_root  = databricks_external_location.storage_location[each.value.storage_location_name].url
  comment       = each.value.comment
  properties = {
    purpose = "testing"
  }
  owner = each.value.role_owner

  depends_on = [
    databricks_external_location.storage_location
  ]
}

module "catalog_grants" {
  providers = {
    databricks = databricks.admin
  }
  for_each     = local.catalog_grants
  source       = "./modules/catalog_grants"
  catalog_name = each.key
  grants       = each.value.grants
  depends_on   = [databricks_catalog.catalog]
}
