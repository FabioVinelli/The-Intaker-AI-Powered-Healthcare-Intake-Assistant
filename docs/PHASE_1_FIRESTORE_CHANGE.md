# Phase 1: Firestore Governance Rules

## Overview
This document outlines the mandatory clinician sign-off requirement implemented in Firestore Security Rules to enforce the HITL model.

## Core Change: Clinician Authorization
The intake result (`intake_results` collection) now requires a `clinician_signature_id` field for finalization.
The AI can `create` the document, but ONLY a `clinician` role can `update` it with a signature.
The patient CANNOT read final recommendations until this signature is present.

## Schema Diff (Governance Object)

```javascript
// NEW GOVERNANCE OBJECT (Added to intake_result)
{
  "intake_id": "uuid...",
  "status": "pending_reviews", // vs "finalized"
  "governance": {
      "model": "HITL_CLINICIAN_AUTHORIZED",
      "clinician_signature_id": null, // initially null
      "clinician_timestamp": null,
      "ai_generated_scores": {...}
  }
}
```

## Security Rules (firestore.rules) Diff

The following rules enforce the "Clinical Gate":

```javascript
match /intake_results/{resultId} {
  // Allow AI (service account) or authenticated user to create the initial intake result
  allow create: if request.auth != null;

  // STRICT UPDATE POLICY:
  // Only a user with the 'clinician' role can update the document to add a signature.
  // The update must include a valid clinician_signature_id.
  allow update: if request.auth.token.role == 'clinician'
                && request.resource.data.governance.clinician_signature_id != null
                && request.resource.data.status == 'finalized';

  // READ POLICY:
  // - Clinicians and Admins can read pending intakes.
  // - Patients (resource owner) can read ONLY if the intake is signed off by a clinician.
  allow read: if request.auth.token.role in ['clinician', 'admin']
              || (request.auth.uid == resource.data.patient_id && resource.data.governance.clinician_signature_id != null);
}
```

## Rationale
This ensures that no AI-generated medical advice or treatment plan is exposed to the patient without explicit human review and authorization.
The `clinician_signature_id` acts as the immutable "Clinical Gate".
