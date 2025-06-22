variable "region" {
  description = "AWS Region"
  type        = string
}

variable "s3_bucket" {
  description = "S3 bucket where Lambda code is uploaded"
  type        = string
}
