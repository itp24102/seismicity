variable "location" {
  default = "West Europe"
}

variable "resource_group_name" {
  default = "seismicity-rg"
}

variable "vm_name" {
  default = "seismicity-vm"
}

variable "admin_username" {
  default = "azureadmin"
}

variable "public_key_path" {
  default = "~/.ssh/mySSHKey.pub"
}

variable "public_ip_name" {
  default = "seismicity-pip"
}