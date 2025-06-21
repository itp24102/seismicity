variable "region" {
  default = "eu-west-1"
}

variable "s3_bucket_name" {
  default = "seismicity-app-bucket"
}
variable "influx_url" {
  description = "The URL of the InfluxDB instance"
  type        = string
}

variable "influx_token" {
  description = "The token for authenticating with InfluxDB"
  type        = string
}
