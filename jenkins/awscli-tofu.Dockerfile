FROM amazon/aws-cli:2.15.30

# Εγκατάσταση unzip και curl ανάλογα με το διαθέσιμο package manager
RUN if command -v apt-get > /dev/null; then \
      apt-get update && apt-get install -y unzip curl; \
    elif command -v yum > /dev/null; then \
      yum install -y unzip curl; \
    else \
      echo "Unsupported base image" && exit 1; \
    fi
