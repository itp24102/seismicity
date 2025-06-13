output "s3_bucket_name" {
  description = "The name of the S3 Bucket"
  value       = aws_s3_bucket.seismicity_bucket.bucket
}

output "lambda_function_name" {
  description = "The name of the AWS Lamda Function"
  value       = aws_lambda_function.seismicity.function_name
}