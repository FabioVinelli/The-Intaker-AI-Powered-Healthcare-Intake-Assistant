#!/bin/bash

# Deploy GetActiveScript HTTP Cloud Function (Gen2)
#
# Usage:
#   PROJECT_ID="your-project" \
#   REGION="us-central1" \
#   SERVICE_ACCOUNT="intaker-backend-sa@your-project.iam.gserviceaccount.com" \
#   ./deploy.sh
#
# Notes:
# - Ensure ADC / gcloud auth is configured.
# - Keep logs HIPAA-safe; do not log PHI.

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-}"
FUNCTION_NAME="${FUNCTION_NAME:-get-active-script}"
RUNTIME="${RUNTIME:-python311}"
SOURCE_DIR="."
ENTRY_POINT="get_active_script"

DEFAULT_SCRIPT_ID="${DEFAULT_SCRIPT_ID:-full_asam_script_humanized}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "ERROR: PROJECT_ID is required" >&2
  exit 1
fi
if [[ -z "${SERVICE_ACCOUNT}" ]]; then
  echo "ERROR: SERVICE_ACCOUNT is required" >&2
  exit 1
fi

echo "Deploying ${FUNCTION_NAME}..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service Account: ${SERVICE_ACCOUNT}"

gcloud config set project "${PROJECT_ID}" >/dev/null

gcloud functions deploy "${FUNCTION_NAME}" \
  --gen2 \
  --runtime="${RUNTIME}" \
  --region="${REGION}" \
  --source="${SOURCE_DIR}" \
  --entry-point="${ENTRY_POINT}" \
  --trigger-http \
  --service-account="${SERVICE_ACCOUNT}" \
  --set-env-vars="DEFAULT_SCRIPT_ID=${DEFAULT_SCRIPT_ID}" \
  --quiet

echo "✅ Deployed ${FUNCTION_NAME}"


