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
