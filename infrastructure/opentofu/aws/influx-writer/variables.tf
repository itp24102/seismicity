variable "region" {
  description = "AWS Region"
  type        = string
  default     = "eu-west-1"
}


variable "influx_url" {
  description = "The URL of the InfluxDB instance"
  type        = string
}

variable "influx_token" {
  description = "The token for authenticating with InfluxDB"
  type        = string
}
