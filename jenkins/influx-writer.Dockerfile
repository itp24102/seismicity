FROM python:3.9-slim

# Εγκατάσταση εργαλείων και βιβλιοθηκών
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    zip \
    gnupg \
    ca-certificates \
    && pip install --no-cache-dir awscli \
    && curl -LO https://github.com/opentofu/opentofu/releases/download/v1.9.1/tofu_1.9.1_linux_amd64.zip \
    && unzip tofu_1.9.1_linux_amd64.zip \
    && install -o root -g root -m 0755 tofu /usr/local/bin/tofu \
    && rm -rf tofu tofu_1.9.1_linux_amd64.zip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Ορισμός default command
CMD ["bash"]
