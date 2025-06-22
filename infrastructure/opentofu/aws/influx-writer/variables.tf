variable "region" {
  description = "AWS region"
  type        = string
}

variable "influx_url" {
  description = "The URL of the InfluxDB instance"
  type        = string
}

variable "influx_token" {
  description = "The token for authenticating with InfluxDB"
  type        = string
}

variable "influx_org" {
  description = "The InfluxDB organization"
  type        = string
}

variable "influx_bucket" {
  description = "The InfluxDB bucket"
  type        = string
}
