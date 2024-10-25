variable "catalog_name" {
  type = string
}

variable "grants" {
  type = map(list(string))
}


terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "1.24.0"
    }
  }
}

resource "databricks_grants" "this" {
  catalog = var.catalog_name

  dynamic "grant" {
    for_each = var.grants
    content {
      principal  = grant.key
      privileges = grant.value
    }
  }
}