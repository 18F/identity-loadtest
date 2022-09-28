
provider "aws" {
  region = var.region
}

terraform {
  required_version = ">= 1.2.4"
  backend "s3" {
    bucket = "login-gov.tf-state.${data.aws_caller_identity.current.account_id}-${var.region}"
    key    = "terraform-loadtest/terraform-${var.cluster_name}.tfstate"
    region = var.region
    dynamodb_table = "terraform_locks"
  }
}

# Using these data sources allows the configuration to be
# generic for any region.
data "aws_region" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}
