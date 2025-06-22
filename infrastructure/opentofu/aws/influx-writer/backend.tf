terraform {
  backend "s3" {
    bucket         = "seismicity-tfstate"
    key            = "influx-writer/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
