variable "region" {
  description = "AWS region to deploy resources"
  default     = "eu-west-1" 
}

variable "s3_bucket_name" {
  description = "S3 Bucket name for seismic data"
  default     = "seismicity-app-bucket"
}