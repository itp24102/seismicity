FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y curl unzip zip awscli && \
    curl -LO https://github.com/opentofu/opentofu/releases/download/v1.9.1/tofu_1.9.1_linux_amd64.zip && \
    unzip -q tofu_1.9.1_linux_amd64.zip && \
    install -o root -g root -m 0755 tofu /usr/local/bin/tofu && \
    rm -rf tofu_1.9.1_linux_amd64.zip tofu

WORKDIR /workspace
