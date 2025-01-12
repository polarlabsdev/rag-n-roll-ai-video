variable "snowflake_organization_name" {
  description = "The name of the Snowflake organization"
  type        = string
}

variable "snowflake_account_name" {
  description = "The name of the Snowflake account"
  type        = string
}

variable "snowflake_user" {
  description = "The Snowflake user"
  type        = string
}

variable "snowflake_password" {
  description = "The password for the Snowflake user"
  type        = string
  sensitive   = true
}

variable "snowflake_warehouse" {
  description = "The Snowflake warehouse to use"
  type        = string
}

variable "snowflake_user_rsa_public_key" {
  description = "The RSA public key for the Snowflake user"
  type        = string
  sensitive   = true
}

variable "build_knowledge_base_command" {
  description = "The command to build the knowledge base"
  type        = string
}

variable "knowledge_base_file_name" {
  description = "The name of the knowledge base file"
  type        = string
}

variable "knowledge_base_directory_path" {
  description = "The directory where the knowledge base file is located"
  type        = string
}
