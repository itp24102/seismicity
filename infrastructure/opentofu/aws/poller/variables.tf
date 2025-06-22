variable "region" {
  description = "The AWS region to deploy into"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket containing the function.zip"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the IAM role for Lambda execution"
  type        = string
}
