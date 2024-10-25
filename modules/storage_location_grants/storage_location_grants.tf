variable "storage_location" {
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
  external_location = var.storage_location

  dynamic "grant" {
    for_each = var.grants
    content {
      principal  = grant.key
      privileges = grant.value
    }
  }
}
