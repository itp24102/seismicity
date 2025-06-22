variable "region" {
  description = "AWS Region"
  type        = string
}

variable "s3_bucket_name" {
  description = "The S3 bucket containing the Lambda deployment package"
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
