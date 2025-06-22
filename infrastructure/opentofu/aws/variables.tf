variable "region" {
  description = "The AWS region to deploy resources to"
  type        = string
  default     = "eu-west-1"
}

variable "s3_bucket_name" {
  description = "The name of the S3 bucket for Lambda function code"
  type        = string
  default     = "seismicity-app-bucket"
}

variable "influx_url" {
  description = "The URL of the InfluxDB instance"
  type        = string
  default     = "http://dummy"
}

variable "influx_token" {
  description = "The token for authenticating with InfluxDB"
  type        = string
  default     = "dummy"
}
