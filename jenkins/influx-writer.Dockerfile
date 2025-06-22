FROM python:3.9-slim

# Εγκατάσταση εξαρτήσεων CLI
RUN apt-get update && apt-get install -y \
    unzip \
    zip \
    curl \
    awscli \
    && rm -rf /var/lib/apt/lists/*

# Εγκατάσταση OpenTofu
RUN curl -LO https://github.com/opentofu/opentofu/releases/download/v1.9.1/tofu_1.9.1_linux_amd64.zip && \
    unzip tofu_1.9.1_linux_amd64.zip && \
    install -o root -g root -m 0755 tofu /usr/local/bin/tofu && \
    rm -f tofu tofu_1.9.1_linux_amd64.zip

# Προαιρετικά: Δημιουργία μη-root χρήστη
# RUN useradd -ms /bin/bash jenkins && usermod -aG sudo jenkins
# USER jenkins

WORKDIR /workspace

CMD [ "bash" ]
