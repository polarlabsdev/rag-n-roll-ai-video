output "streamlit_role_name" {
  value = snowflake_account_role.streamlit_role.name
}

output "streamlit_user_name" {
  value = snowflake_service_user.streamlit_user.name
}

output "rag_n_roll_db_name" {
  value = snowflake_database.rag_n_roll_db.name
}

output "rag_n_roll_schema_name" {
  value = snowflake_schema.rag_n_roll_schema.name
}

output "rag_n_roll_warehouse_name" {
  value = snowflake_warehouse.rag_n_roll_warehouse.name
}

output "cortex_search_warehouse_name" {
  value = snowflake_warehouse.cortex_search_warehouse.name
}

output "knowledge_base_table_name" {
  value = "${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_table.knowledge_base.name}"
}

output "kb_csv_format_name" {
  value = "${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_file_format.kb_csv_format.name}"
}

output "kb_csv_stage_name" {
  value = "${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_stage.kb_csv_stage.name}"
}

output "kb_search_service_name" {
  value = "${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_cortex_search_service.kb_search_service.name}"
}

output "knowledge_base_file_path" {
  value = "${var.knowledge_base_directory_path}/${var.knowledge_base_file_name}"
}

output "fully_qualified_kb_csv_stage_name" {
  value = snowflake_stage.kb_csv_stage.fully_qualified_name
}

output "list_knowledge_base_command" {
  value = "SELECT * FROM ${snowflake_database.rag_n_roll_db.name}.${snowflake_schema.rag_n_roll_schema.name}.${snowflake_table.knowledge_base.name} LIMIT 5"
}
