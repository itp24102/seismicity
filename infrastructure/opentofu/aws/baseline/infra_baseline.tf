provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "seismicity_bucket" {
  bucket = var.s3_bucket_name

  tags = {
    Name        = "seismicity-app-bucket"
    Environment = "development"
  }

  force_destroy = true
}

resource "aws_iam_role" "lambda_role" {
  name = "seismicity-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "seismicity-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = ["logs:*"],
        Effect   = "Allow",
        Resource = "*"
      },
      {
        Action   = ["s3:*"],
        Effect   = "Allow",
        Resource = [
          aws_s3_bucket.seismicity_bucket.arn,
          "${aws_s3_bucket.seismicity_bucket.arn}/*"
        ]
      }
    ]
  })
}
