# Phase 1: Firestore Governance Rules Update

## Overview
This document updates the Firestore Security Rules to enforce the HITL model, specifically implementing a "finalize-once" logic gate.

## Core Change: Immutable Finalization
The intake result (`intake_results` collection) now enforces that once a document is marked as `status: 'finalized'`, it becomes **immutable**.
Only a `clinician` can perform the transition from `pending_review` (or other states) to `finalized`.

## Security Rules (firestore.rules) Diff

The following rules enforce the "Clinical Gate" and immutability:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Intake Results Collection
    match /intake_results/{resultId} {
      
      // Allow AI (service account) or authenticated user to create the initial intake result
      allow create: if request.auth != null;

      // STRICT UPDATE POLICY (The "Clinical Gate"):
      // 1. Current status must NOT be 'finalized' (prevents editing after sign-off).
      // 2. User must have 'clinician' role.
      // 3. The new status must be 'finalized' (closing the record).
      // 4. Must include a valid clinician signature.
      allow update: if resource.data.status != 'finalized'
                    && request.auth.token.role == 'clinician'
                    && request.resource.data.status == 'finalized'
                    && request.resource.data.governance.clinician_signature_id != null;

      // READ POLICY:
      // - Clinicians and Admins can read pending intakes.
      // - Patients (resource owner) can read ONLY if the intake is signed off by a clinician.
      allow read: if request.auth.token.role in ['clinician', 'admin']
                  || (request.auth.uid == resource.data.patient_id && resource.data.governance.clinician_signature_id != null);
    }

    // Default deny for other collections (safety fallback)
    match /{document=**} {
      allow read, write: if false; 
    }
  }
}
```

## Rationale
- **Immutability**: `resource.data.status != 'finalized'` ensures that once the gate is closed, it cannot be reopened or tampered with.
- **Authority**: Only `clinician` role can close the gate.
