# Walkthrough: The Tamper-Evident Seal Process

## Overview
This document describes the flow of the "Tamper-Evident Seal" feature, ensuring the integrity of finalized intake records.

## The Sealing Workflow

1.  **Trigger Event**: A clinician updates a Firestore `intake_results` document.
    *   **Action**: Sets `status` to `'finalized'`.
    *   **Authorization**: Adds `governance.clinician_signature_id`.

2.  **Cloud Function Activation**: The `seal_intake_result` Cloud Function detects the change.
    *   **Inputs**: The update event context and document snapshot.

3.  **Content Canonicalization**:
    *   The function extracts key clinical fields: `asam_scores`, `suggested_plan`, `level_of_care`, and `transcript_summary`.
    *   It serializes these fields into a **canonical JSON string**:
        *   Keys are sorted alphabetically.
        *   No whitespace.
        *   Deterministic ordering ensures the same content *always* produces the same string.

4.  **Cryptographic Signing**:
    *   The function computes a **SHA-256 hash** of the canonical string.
    *   It sends this hash to **Google Cloud KMS** (Key Management Service).
    *   **KMS Action**: Signs the hash using the private key version of `intake-signer-key`.
    *   **Algorithm**: `RSA_SIGN_PKCS1_2048_SHA256`.

5.  **Seal Application**:
    *   The function receives the signature (base64 encoded).
    *   It updates the Firestore document with a new `governance.seal` object:
        ```json
        "seal": {
          "signature": "base64_encoded_signature...",
          "key_version": "projects/.../cryptoKeyVersions/1",
          "algorithm": "RSA_SIGN_PKCS1_2048_SHA256",
          "timestamp": "2026-02-09T14:30:00Z"
        }
        ```

6.  **Verification (Future)**:
    *   Any auditor can retrieve the document and the public key from KMS.
    *   They enable re-computing the canonical string hash and verifying the signature against the public key.
    *   If the document content has changed even by one character, the signature validation will fail.

## Architectural Diagram

```mermaid
sequenceDiagram
    participant Clinician
    participant Firestore
    participant CloudFunction
    participant KMS

    Clinician->>Firestore: Update(status='finalized', sig_id='123')
    Firestore->>CloudFunction: Trigger onUpdate
    CloudFunction->>CloudFunction: Canonicalize Content & Hash
    CloudFunction->>KMS: Sign(Hash)
    KMS-->>CloudFunction: Signature
    CloudFunction->>Firestore: Update(governance.seal = Signature)
61: 
62: ## Deployment & Verification Guide
63: 
64: ### 1. Prerequisites
65: Ensure you have the following Google Cloud permissions:
66: - `cloudfunctions.functions.create`
67: - `cloudkms.cryptoKeyVersions.useToSign` (Service Account)
68: - `datastore.databases.get`
69: 
70: ### 2. Deploy the Service
71: Navigate to the service directory and run the deployment script:
72: 
73: ```bash
74: cd cloud_functions/seal_service
75: chmod +x deploy.sh
76: ./deploy.sh
77: ```
78: 
79: > **Note**: Update the `PROJECT_ID` and `KMS_KEY_ID` variables in `deploy.sh` before running.
80: 
81: ### 3. Verify the Seal
82: Once deployed, perform the following test:
83: 
84: 1.  **Open Firestore Console**.
85: 2.  **Select a Test Document** in the `intake_results` collection.
86: 3.  **Update the Document**:
87:     *   Set `status` to `"finalized"`.
88:     *   Add a test `governance.clinician_signature_id` (e.g., "test-sig-123").
89: 4.  **Wait 5-10 seconds**.
90: 5.  **Refresh**: You should see a new `governance.seal` field appear with a `signature` string.
