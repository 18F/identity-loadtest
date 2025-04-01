#!/bin/sh

set -euo pipefail

your_loadtest_cluster_name="$1"
yourenv="$2"
yoursp="$3"
yoururn="$4"


cp -rp ENV "$yoursp"
find "$yoursp" -type f -exec sed -i '' "s/CLUSTER_NAME/$your_loadtest_cluster_name/g" '{}' \;
find "$yoursp" -type f -exec sed -i '' "s/ENV/$yourenv/g" '{}' \;
find "$yoursp" -type f -exec sed -i '' "s/SERVICE_PROVIDER/$yoursp/g" '{}' \;
find "$yoursp" -type f -exec sed -i '' "s/URN/$yoururn/g" '{}' \;

cp -rp ENV.yaml "$yoursp.yaml"
find "$yoursp.yaml" -type f -exec sed -i '' "s/CLUSTER_NAME/$your_loadtest_cluster_name/g" '{}' \;
find "$yoursp.yaml" -type f -exec sed -i '' "s/ENV/$yoursp/g" '{}' \;
