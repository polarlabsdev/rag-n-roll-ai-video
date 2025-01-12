terraform {
  required_providers {
    snowflake = {
      source = "Snowflake-Labs/snowflake"
    }
  }
}

# You need to put your Snowflake credentials in terraform/terraform.tfvars
provider "snowflake" {
  organization_name = var.snowflake_organization_name
  account_name      = var.snowflake_account_name
  user              = var.snowflake_user
  password          = var.snowflake_password
  warehouse         = var.snowflake_warehouse
  preview_features_enabled = [
    "snowflake_table_resource",
    "snowflake_cortex_search_service_resource",
    "snowflake_file_format_resource",
    "snowflake_stage_resource"
  ]
}

# ------------------------------
# CONFIGURE SNOWFLAKE USER
# ------------------------------
resource "snowflake_account_role" "streamlit_role" {
  name = "RAG_N_ROLE" # hehe
}

# all roles must be owned by SYSADMIN for best practises
resource "snowflake_grant_account_role" "rnr_to_sysadmin" {
  role_name        = snowflake_account_role.streamlit_role.name
  parent_role_name = "SYSADMIN"

  depends_on = [
    snowflake_account_role.streamlit_role
  ]
}

resource "snowflake_warehouse" "rag_n_roll_warehouse" {
  name                = "RAG_N_ROLL"
  comment             = "Warehouse for the RAG-N-ROLL project"
  warehouse_size      = "XSMALL"
  auto_suspend        = 120
  auto_resume         = true
  initially_suspended = true
}

resource "snowflake_warehouse" "cortex_search_warehouse" {
  name                = "CORTEX_SEARCH"
  comment             = "Warehouse for Cortex Search"
  warehouse_size      = "XSMALL"
  auto_suspend        = 120
  auto_resume         = true
  initially_suspended = true
}

# https://docs.snowflake.com/en/user-guide/key-pair-auth
resource "snowflake_service_user" "streamlit_user" {
  login_name        = "STREAMLIT_USER"
  name              = "STREAMLIT_USER"
  display_name      = "Streamlit Service User"
  comment           = "A service user for our streamlit community app."
  default_warehouse = snowflake_warehouse.rag_n_roll_warehouse.name
  default_role      = snowflake_account_role.streamlit_role.name
  rsa_public_key    = var.snowflake_user_rsa_public_key

  depends_on = [
    snowflake_warehouse.rag_n_roll_warehouse,
    snowflake_account_role.streamlit_role
  ]
}

resource "snowflake_grant_account_role" "rnr_to_user" {
  role_name = snowflake_account_role.streamlit_role.name
  user_name = snowflake_service_user.streamlit_user.name

  depends_on = [
    snowflake_service_user.streamlit_user,
    snowflake_account_role.streamlit_role
  ]
}

resource "snowflake_grant_privileges_to_account_role" "rag_warehouse_to_role" {
  privileges        = ["USAGE"]
  account_role_name = snowflake_account_role.streamlit_role.name

  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.rag_n_roll_warehouse.name
  }

  depends_on = [
    snowflake_warehouse.rag_n_roll_warehouse,
    snowflake_account_role.streamlit_role
  ]
}

resource "snowflake_grant_privileges_to_account_role" "search_warehouse_to_role" {
  privileges        = ["USAGE"]
  account_role_name = snowflake_account_role.streamlit_role.name

  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.cortex_search_warehouse.name
  }

  depends_on = [
    snowflake_warehouse.cortex_search_warehouse,
    snowflake_account_role.streamlit_role
  ]
}

# ------------------------------
# CONFIGURE SNOWFLAKE RESOURCES
# ------------------------------
resource "snowflake_database" "rag_n_roll_db" {
  name                        = "RAG_N_ROLL_DB"
  comment                     = "Database for the RAG-N-ROLL project"
  data_retention_time_in_days = 7
}

resource "snowflake_schema" "rag_n_roll_schema" {
  name     = "RAG_N_ROLL_SCHEMA"
  database = snowflake_database.rag_n_roll_db.name
  comment  = "Schema for the RAG-N-ROLL project"

  depends_on = [
    snowflake_database.rag_n_roll_db
  ]
}

resource "snowflake_grant_ownership" "rag_n_roll_ownership" {
  account_role_name   = snowflake_account_role.streamlit_role.name
  outbound_privileges = "COPY"
  on {
    object_type = "DATABASE"
    object_name = snowflake_database.rag_n_roll_db.name
  }

  depends_on = [
    snowflake_database.rag_n_roll_db,
    snowflake_account_role.streamlit_role
  ]
}

resource "snowflake_grant_ownership" "rag_n_roll_schema_ownership" {
  account_role_name   = snowflake_account_role.streamlit_role.name
  outbound_privileges = "COPY"
  on {
    object_type = "SCHEMA"
    object_name = "${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}"
  }

  depends_on = [
    snowflake_schema.rag_n_roll_schema,
    snowflake_account_role.streamlit_role
  ]
}

# ------------------------------
# CONFIGURE KNOWLEDGE BASE
# ------------------------------
resource "snowflake_table" "knowledge_base" {
  database        = snowflake_database.rag_n_roll_db.name
  schema          = snowflake_schema.rag_n_roll_schema.name
  name            = "KNOWLEDGE_BASE"
  change_tracking = true

  column {
    name = "SOURCE"
    type = "VARCHAR"
  }

  column {
    name = "SOURCE_ID"
    type = "VARCHAR"
  }

  column {
    name = "CHUNK_TEXT"
    type = "VARCHAR"
  }

  column {
    name = "TAGS"
    type = "ARRAY"
  }

  column {
    name = "REFERENCE_URL"
    type = "VARCHAR"
  }
}

resource "snowflake_file_format" "kb_csv_format" {
  name                         = "KB_CSV_FORMAT"
  database                     = snowflake_database.rag_n_roll_db.name
  schema                       = snowflake_schema.rag_n_roll_schema.name
  format_type                  = "CSV"
  empty_field_as_null          = true
  parse_header                 = true
  trim_space                   = true
  field_optionally_enclosed_by = "\""

  depends_on = [
    snowflake_database.rag_n_roll_db,
    snowflake_schema.rag_n_roll_schema
  ]
}

resource "snowflake_stage" "kb_csv_stage" {
  name        = "KB_CSV_STAGE"
  database    = snowflake_database.rag_n_roll_db.name
  schema      = snowflake_schema.rag_n_roll_schema.name
  file_format = "FORMAT_NAME = ${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_file_format.kb_csv_format.name}"
  directory   = "ENABLE = true"

  depends_on = [
    snowflake_file_format.kb_csv_format
  ]
}

# This is a "null resource" that will trigger our local command scripts/populate_kb.py
resource "terraform_data" "build_knowledge_base" {
  triggers_replace = [
    snowflake_stage.kb_csv_stage.name
  ]

  provisioner "local-exec" {
    command = var.build_knowledge_base_command
  }

  depends_on = [
    snowflake_table.knowledge_base,
    snowflake_stage.kb_csv_stage
  ]
}

resource "snowflake_execute" "put_csv_on_stage" {
  execute = <<-EOT
    PUT file://${var.knowledge_base_directory_path}/${var.knowledge_base_file_name} @${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_stage.kb_csv_stage.name} AUTO_COMPRESS=TRUE;
  EOT
  revert  = "REMOVE @${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_stage.kb_csv_stage.name}/${var.knowledge_base_file_name}.gz"
  query   = "LIST @${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_stage.kb_csv_stage.name}"

  depends_on = [
    snowflake_table.knowledge_base,
    snowflake_file_format.kb_csv_format,
    terraform_data.build_knowledge_base
  ]
}

resource "snowflake_execute" "load_kb_csv" {
  execute = <<-EOT
    COPY INTO ${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_table.knowledge_base.name}
      FROM @${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_stage.kb_csv_stage.name}/${var.knowledge_base_file_name}.gz
      FILE_FORMAT = (FORMAT_NAME = ${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_file_format.kb_csv_format.name})
      MATCH_BY_COLUMN_NAME='CASE_INSENSITIVE';
  EOT
  revert  = "TRUNCATE TABLE ${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_table.knowledge_base.name}"
  query   = "SELECT * FROM ${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_table.knowledge_base.name} LIMIT 5"

  depends_on = [
    snowflake_table.knowledge_base,
    snowflake_stage.kb_csv_stage,
    snowflake_execute.put_csv_on_stage,
    terraform_data.build_knowledge_base
  ]
}

resource "snowflake_cortex_search_service" "kb_search_service" {
  database   = snowflake_database.rag_n_roll_db.name
  schema     = snowflake_schema.rag_n_roll_schema.name
  name       = "KB_SEARCH_SERVICE"
  on         = "CHUNK_TEXT"
  target_lag = "2 minutes"
  warehouse  = snowflake_warehouse.cortex_search_warehouse.name
  query      = "SELECT SOURCE, SOURCE_ID, CHUNK_TEXT, TAGS, REFERENCE_URL FROM \"${snowflake_database.rag_n_roll_db.name}\".\"${snowflake_schema.rag_n_roll_schema.name}\".\"${snowflake_table.knowledge_base.name}\""
  comment    = "Search service for the knowledge base"

  depends_on = [snowflake_table.knowledge_base]
}

resource "snowflake_grant_ownership" "knowledge_base_ownership" {
  account_role_name   = snowflake_account_role.streamlit_role.name
  outbound_privileges = "COPY"
  on {
    object_type = "TABLE"
    object_name = "${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_table.knowledge_base.name}"
  }

  depends_on = [
    snowflake_table.knowledge_base,
    snowflake_account_role.streamlit_role
  ]
}

resource "snowflake_grant_ownership" "kb_csv_format_ownership" {
  account_role_name   = snowflake_account_role.streamlit_role.name
  outbound_privileges = "COPY"
  on {
    object_type = "FILE FORMAT"
    object_name = "${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_file_format.kb_csv_format.name}"
  }

  depends_on = [
    snowflake_file_format.kb_csv_format,
    snowflake_account_role.streamlit_role
  ]
}

resource "snowflake_grant_privileges_to_account_role" "kb_csv_stage_usage" {
  privileges        = ["READ", "WRITE"]
  account_role_name = snowflake_account_role.streamlit_role.name
  on_schema_object {
    object_type = "STAGE"
    object_name = snowflake_stage.kb_csv_stage.fully_qualified_name
  }

  depends_on = [
    snowflake_stage.kb_csv_stage,
    snowflake_account_role.streamlit_role
  ]
}

resource "snowflake_grant_privileges_to_account_role" "kb_search_service_usage" {
  privileges        = ["USAGE"]
  account_role_name = snowflake_account_role.streamlit_role.name
  on_schema_object {
    object_type = "CORTEX SEARCH SERVICE"
    object_name = snowflake_cortex_search_service.kb_search_service.fully_qualified_name
  }

  depends_on = [
    snowflake_cortex_search_service.kb_search_service,
    snowflake_account_role.streamlit_role
  ]
}
