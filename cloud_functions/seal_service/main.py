import base64
import json
import os
import hashlib
import functions_framework
from google.cloud import firestore
from google.cloud import kms
from cloudevents.http import CloudEvent

# -- Configuration --
# ID of the key to use for signing. 
# Format: projects/{project}/locations/{location}/keyRings/{key_ring}/cryptoKeys/{crypto_key}/cryptoKeyVersions/{version}
# We use an environment variable for flexibility, or fallback to a known location ID pattern if needed.
KMS_KEY_ID = os.environ.get("KMS_KEY_ID") 

db = firestore.Client()
kms_client = kms.KeyManagementServiceClient()

def canonicalize_content(data: dict) -> bytes:
    """
    Creates a deterministic canonical JSON string from specific fields of the intake result.
    This ensures that the signature is verifiable regardless of field ordering in the DB.
    
    Fields included in the seal:
    - asam_scores (dict)
    - suggested_plan (string)
    - level_of_care (string)
    - transcript_summary (string) - optional, if present
    """
    sealable_data = {
        "asam_scores": data.get("asam_scores"),
        "suggested_plan": data.get("suggested_plan"),
        "level_of_care": data.get("level_of_care"),
        # We include the ID to bind the content to this specific document
        "intake_id": data.get("intake_id") 
    }
    
    # Sort keys for determinism. Separators override default (', ', ': ') to no-space (',',':').
    return json.dumps(sealable_data, sort_keys=True, separators=(',', ':')).encode('utf-8')

@functions_framework.cloud_event
def seal_intake_result(cloud_event: CloudEvent):
    """
    Triggered by a Firestore document update.
    Checks if the status is 'finalized' and applies a tamper-evident seal if missing.
    """
    event_data = cloud_event.data
    
    # Defensive check for event format
    if not event_data or "value" not in event_data:
        print("No data found in CloudEvent")
        return

    # Extract the resource name (document path)
    # Format: projects/{project}/databases/(default)/documents/intake_results/{doc_id}
    doc_path = event_data["value"]["name"].split("/documents/")[1]
    
    # Get the raw fields from the event (Firestore protobuf format)
    # However, it's often easier to just fetch the fresh document snapshot to get standard Python types
    # and avoid complex protobuf parsing logic here, ensuring we sign exactly what is currently stored.
    doc_ref = db.document(doc_path)
    doc_snapshot = doc_ref.get()
    
    if not doc_snapshot.exists:
        print(f"Document {doc_path} no longer exists.")
        return

    data = doc_snapshot.to_dict()
    
    # 1. Check Status
    status = data.get("status")
    if status != "finalized":
        print(f"Skipping: Status is '{status}', not 'finalized'.")
        return

    # 2. Check Governance
    governance = data.get("governance", {})
    if not governance.get("clinician_signature_id"):
        print("Skipping: No clinician_signature_id present.")
        return
    
    # 3. Idempotency Check
    if governance.get("seal"):
        print("Skipping: Document already sealed.")
        return

    print(f"Sealing document: {doc_path}")

    # 4. Canonicalize & Hash
    canonical_bytes = canonicalize_content(data)
    # SHA-256 Hash
    digest = hashlib.sha256(canonical_bytes).digest()
    
    # 5. Call KMS to Sign
    if not KMS_KEY_ID:
        print("Error: KMS_KEY_ID environment variable not set.")
        return

    # Build the digest object for KMS
    digest_obj = {"sha256": digest}
    
    try:
        response = kms_client.asymmetric_sign(
            request={
                "name": KMS_KEY_ID,
                "digest": digest_obj,
            }
        )
        
        signature_b64 = base64.b64encode(response.signature).decode('utf-8')
        
        # 6. Update Firestore with Seal
        seal_object = {
            "signature": signature_b64,
            "key_version": KMS_KEY_ID,
            "algorithm": "RSA_SIGN_PKCS1_2048_SHA256",
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        
        doc_ref.update({
            "governance.seal": seal_object
        })
        
        print(f"Successfully sealed {doc_path}")
        
    except Exception as e:
        print(f"Failed to sign document: {e}")
        # We generally do NOT retry blindly on KMS errors to avoid loops, 
        # but in a real system we might output to a DLQ.
