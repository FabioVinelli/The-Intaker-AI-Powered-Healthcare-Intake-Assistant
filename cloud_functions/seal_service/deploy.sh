#!/bin/bash

# Configuration
# Replace these with actual project values or set as environment variables
PROJECT_ID="your-project-id"
REGION="us-central1"
KMS_KEY_ID="projects/${PROJECT_ID}/locations/${REGION}/keyRings/intake-key-ring/cryptoKeys/intake-signer-key/cryptoKeyVersions/1"
SERVICE_ACCOUNT="seal-service-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Deploying Cloud Function: seal-intake-result..."

gcloud functions deploy seal-intake-result \
    --gen2 \
    --runtime=python310 \
    --region="${REGION}" \
    --source=. \
    --entry-point=seal_intake_result \
    --trigger-event-filters="type=google.cloud.firestore.document.v1.updated" \
    --trigger-event-filters="database=(default)" \
    --trigger-event-filters="namespace=(default)" \
    --trigger-event-filters="document=intake_results/{resultId}" \
    --set-env-vars KMS_KEY_ID="${KMS_KEY_ID}" \
    --service-account="${SERVICE_ACCOUNT}" \
    --allow-unauthenticated

echo "Deployment command sent."
