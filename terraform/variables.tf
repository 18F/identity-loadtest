variable "region" {
  description = "region where it all happens"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "name of cluster"
  type        = string
  default     = "agnesloadtest"
}

variable "dnszone" {
  description = "zone that we create certs and lb names in"
  type        = string
  default     = "agnesloadtest.identitysandbox.gov"
}
