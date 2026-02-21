# -*- coding: utf-8 -*-
"""
firestore_field_level_encryption.py

This script provides functions to encrypt and decrypt data fields for use with 
Google Cloud Firestore, leveraging a Hardware Security Module (HSM)-backed key 
in Google Cloud Key Management Service (KMS).

This module is intended to be integrated into the main application backend
(e.g., a Flask app running on Cloud Run) to secure Protected Health Information (PHI)
at the application layer before it is stored in Firestore.

Key Functions:
- encrypt_field: Encrypts a UTF-8 string using the specified Cloud HSM key.
- decrypt_field: Decrypts ciphertext using the same Cloud HSM key.
- add_encrypted_document: Demonstrates writing a document to Firestore with an encrypted field.
- get_decrypted_document: Demonstrates reading a document and decrypting the sensitive field.
"""

import base64
from google.cloud import firestore
from google.cloud import kms_v1

# --- Configuration ---
# These values are based on the established project setup.
PROJECT_ID = "intaker-project-hrllc"
LOCATION_ID = "us-west1"  # Ensure this is the correct location of your keyring
KEY_RING_ID = "intaker-hsm-keyring"
KEY_ID = "intaker-hsm-phi-key"

# --- Initialize Clients ---
# It's recommended to initialize clients once and reuse them.
db = firestore.Client(project=PROJECT_ID)
kms_client = kms_v1.KeyManagementServiceClient()

# Construct the full path for the KMS key.
KEY_PATH = kms_client.crypto_key_path(
    PROJECT_ID, LOCATION_ID, KEY_RING_ID, KEY_ID
)

def encrypt_field(plaintext: str) -> str:
    """
    Encrypts a plaintext string using the configured Cloud HSM key.

    Args:
        plaintext: The data to encrypt (must be a string).

    Returns:
        A base64-encoded string of the encrypted data.
    """
    if not isinstance(plaintext, str):
        raise TypeError("Plaintext must be a string.")

    # Convert the plaintext to bytes for encryption.
    plaintext_bytes = plaintext.encode("utf-8")

    # Call the KMS API to encrypt the data.
    response = kms_client.encrypt(
        request={"name": KEY_PATH, "plaintext": plaintext_bytes}
    )

    # The response's ciphertext is in bytes. We encode it to base64 to
    # ensure it can be safely stored as a string in Firestore.
    return base64.b64encode(response.ciphertext).decode("utf-8")

def decrypt_field(ciphertext_b64: str) -> str:
    """
    Decrypts a base64-encoded ciphertext string using the configured Cloud HSM key.

    Args:
        ciphertext_b64: The base64-encoded ciphertext to decrypt.

    Returns:
        The original plaintext string.
    """
    if not isinstance(ciphertext_b64, str):
        raise TypeError("Ciphertext must be a base64 encoded string.")

    # Decode the base64 string back to bytes.
    ciphertext_bytes = base64.b64decode(ciphertext_b64)

    # Call the KMS API to decrypt the data.
    response = kms_client.decrypt(
        request={"name": KEY_PATH, "ciphertext": ciphertext_bytes}
    )

    # The response's plaintext is in bytes. Decode it back to a UTF-8 string.
    return response.plaintext.decode("utf-8")

def add_encrypted_document(collection_name: str, document_id: str, sensitive_field: str, sensitive_data: str):
    """
    Example function to add a document with an encrypted field to Firestore.
    """
    encrypted_data = encrypt_field(sensitive_data)
    
    doc_ref = db.collection(collection_name).document(document_id)
    doc_ref.set({
        sensitive_field: encrypted_data,
        "patient_id": f"patient_{document_id}",
        "notes": "This is a test document with an encrypted field."
    })
    print(f"Document '{document_id}' added to collection '{collection_name}' with encrypted data.")

def get_decrypted_document(collection_name: str, document_id: str, sensitive_field: str):
    """
    Example function to retrieve a document and decrypt its sensitive field.
    """
    doc_ref = db.collection(collection_name).document(document_id)
    document = doc_ref.get()

    if document.exists:
        encrypted_data = document.get(sensitive_field)
        decrypted_data = decrypt_field(encrypted_data)
        
        print(f"Successfully retrieved and decrypted document '{document_id}':")
        print(f"  Encrypted Value: {encrypted_data}")
        print(f"  Decrypted Value: {decrypted_data}")
        return document.to_dict(), decrypted_data
    else:
        print(f"Document '{document_id}' not found.")
        return None, None

# --- Example Usage ---
# This block demonstrates the end-to-end process.
if __name__ == "__main__":
    # Define a sample document and data
    collection = "patient_records"
    doc_id = "patient12345"
    field_name = "social_security_number"
    secret_value = "987-65-4321"

    print("--- Running Firestore Field-Level Encryption Demo ---")
    
    # 1. Add a new patient record with an encrypted SSN.
    print(f"\nStep 1: Encrypting and writing data for document '{doc_id}'...")
    add_encrypted_document(collection, doc_id, field_name, secret_value)

    # 2. Retrieve the patient record and decrypt the SSN.
    print(f"\nStep 2: Reading and decrypting data for document '{doc_id}'...")
    get_decrypted_document(collection, doc_id, field_name)
    
    print("\n--- Demo Complete ---")
