provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "seismicity_bucket" {
  bucket = var.s3_bucket_name

  tags = {
    Name = "seismicity-app-bucket"
    Environment = "development"
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "seismicity-lambda-role"

  assume_role_policy = jsonencode({  
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Principal = { Service = "lambda.amazonaws.com" },
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "seismicity-lambda-policy"
  role  = aws_iam_role.lambda_role.id

  policy = jsonencode({  
    Version = "2012-10-17",
    Statement = [{
      Action = [
        "s3:*"
      ],
      Effect = "Allow",
      Resource = aws_s3_bucket.seismicity_bucket.arn
    }]
  })
}

resource "aws_lambda_function" "seismicity" {
  function_name = "seismicity-function"

  role    = aws_iam_role.lambda_role.arn
  handler = "handler.handler"

  runtime = "python3.9"

  filename = "function.zip"  # Θα το ανεβάσεις αφού κάνεις build το handler σου

  environment {
    variables = {
      BUCKET = aws_s3_bucket.seismicity_bucket.bucket
    }
  }
}