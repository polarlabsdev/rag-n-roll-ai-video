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

resource "snowflake_grant_privileges_to_account_role" "example" {
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
