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
