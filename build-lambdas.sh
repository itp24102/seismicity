#!/bin/bash

set -e

echo "📦 Building poller Lambda zip..."
cd services/poller/src
zip -r ../../../infrastructure/opentofu/aws/handler/function.zip .
cd - > /dev/null

echo "📦 Building influx-writer Lambda zip..."
cd services/influx-writer/src
zip -r ../../../infrastructure/opentofu/aws/influx/influx-writer.zip .
cd - > /dev/null

echo "✅ All Lambda zips built successfully."
