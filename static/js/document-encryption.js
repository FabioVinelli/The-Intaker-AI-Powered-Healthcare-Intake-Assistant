/**
 * Client-Side Document Encryption Module
 * Provides AES-256-GCM encryption for documents before transmission
 * Integrates with server-side encryption infrastructure
 */

class DocumentEncryption {
    constructor() {
        this.algorithm = 'AES-GCM';
        this.keyLength = 256;
        this.ivLength = 12; // 96 bits for GCM
        this.tagLength = 128; // 128 bits for authentication tag
    }

    /**
     * Generate a cryptographically secure random key
     * @returns {Promise<CryptoKey>} Generated AES-256 key
     */
    async generateKey() {
        return await window.crypto.subtle.generateKey(
            {
                name: this.algorithm,
                length: this.keyLength
            },
            true, // extractable
            ['encrypt', 'decrypt']
        );
    }

    /**
     * Derive encryption key from user credentials/session
     * @param {string} userCredential - User credential or session token
     * @param {string} salt - Random salt for key derivation
     * @returns {Promise<CryptoKey>} Derived encryption key
     */
    async deriveKey(userCredential, salt) {
        const encoder = new TextEncoder();
        const keyMaterial = await window.crypto.subtle.importKey(
            'raw',
            encoder.encode(userCredential),
            'PBKDF2',
            false,
            ['deriveBits', 'deriveKey']
        );

        return await window.crypto.subtle.deriveKey(
            {
                name: 'PBKDF2',
                salt: encoder.encode(salt),
                iterations: 100000,
                hash: 'SHA-256'
            },
            keyMaterial,
            {
                name: this.algorithm,
                length: this.keyLength
            },
            true,
            ['encrypt', 'decrypt']
        );
    }

    /**
     * Generate random salt for key derivation
     * @returns {string} Base64 encoded salt
     */
    generateSalt() {
        const salt = new Uint8Array(32);
        window.crypto.getRandomValues(salt);
        return this.arrayBufferToBase64(salt);
    }

    /**
     * Generate random IV for encryption
     * @returns {Uint8Array} Random IV
     */
    generateIV() {
        const iv = new Uint8Array(this.ivLength);
        window.crypto.getRandomValues(iv);
        return iv;
    }

    /**
     * Encrypt file data using AES-256-GCM
     * @param {File} file - File to encrypt
     * @param {CryptoKey} key - Encryption key
     * @returns {Promise<Object>} Encrypted data object
     */
    async encryptFile(file, key) {
        try {
            const fileBuffer = await this.fileToArrayBuffer(file);
            const iv = this.generateIV();

            const encryptedData = await window.crypto.subtle.encrypt(
                {
                    name: this.algorithm,
                    iv: iv,
                    tagLength: this.tagLength
                },
                key,
                fileBuffer
            );

            return {
                encryptedData: this.arrayBufferToBase64(encryptedData),
                iv: this.arrayBufferToBase64(iv),
                originalName: file.name,
                originalSize: file.size,
                mimeType: file.type,
                timestamp: new Date().toISOString(),
                algorithm: this.algorithm,
                keyLength: this.keyLength
            };
        } catch (error) {
            throw new Error(`Encryption failed: ${error.message}`);
        }
    }

    /**
     * Decrypt file data using AES-256-GCM
     * @param {string} encryptedData - Base64 encoded encrypted data
     * @param {string} iv - Base64 encoded IV
     * @param {CryptoKey} key - Decryption key
     * @returns {Promise<ArrayBuffer>} Decrypted file data
     */
    async decryptFile(encryptedData, iv, key) {
        try {
            const encryptedBuffer = this.base64ToArrayBuffer(encryptedData);
            const ivBuffer = this.base64ToArrayBuffer(iv);

            const decryptedData = await window.crypto.subtle.decrypt(
                {
                    name: this.algorithm,
                    iv: ivBuffer,
                    tagLength: this.tagLength
                },
                key,
                encryptedBuffer
            );

            return decryptedData;
        } catch (error) {
            throw new Error(`Decryption failed: ${error.message}`);
        }
    }

    /**
     * Export key to base64 string for transmission
     * @param {CryptoKey} key - Key to export
     * @returns {Promise<string>} Base64 encoded key
     */
    async exportKey(key) {
        const exported = await window.crypto.subtle.exportKey('raw', key);
        return this.arrayBufferToBase64(exported);
    }

    /**
     * Import key from base64 string
     * @param {string} keyData - Base64 encoded key
     * @returns {Promise<CryptoKey>} Imported key
     */
    async importKey(keyData) {
        const keyBuffer = this.base64ToArrayBuffer(keyData);
        return await window.crypto.subtle.importKey(
            'raw',
            keyBuffer,
            {
                name: this.algorithm,
                length: this.keyLength
            },
            true,
            ['encrypt', 'decrypt']
        );
    }

    /**
     * Convert File to ArrayBuffer
     * @param {File} file - File to convert
     * @returns {Promise<ArrayBuffer>} File data as ArrayBuffer
     */
    fileToArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(reader.error);
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Convert ArrayBuffer to base64 string
     * @param {ArrayBuffer} buffer - Buffer to convert
     * @returns {string} Base64 encoded string
     */
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    /**
     * Convert base64 string to ArrayBuffer
     * @param {string} base64 - Base64 string to convert
     * @returns {ArrayBuffer} Converted ArrayBuffer
     */
    base64ToArrayBuffer(base64) {
        const binary = window.atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return bytes.buffer;
    }

    /**
     * Create blob from decrypted data
     * @param {ArrayBuffer} data - Decrypted file data
     * @param {string} mimeType - Original file MIME type
     * @returns {Blob} File blob
     */
    createBlobFromDecrypted(data, mimeType) {
        return new Blob([data], { type: mimeType });
    }

    /**
     * Download decrypted file
     * @param {ArrayBuffer} data - Decrypted file data
     * @param {string} filename - Original filename
     * @param {string} mimeType - Original MIME type
     */
    downloadDecryptedFile(data, filename, mimeType) {
        const blob = this.createBlobFromDecrypted(data, mimeType);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

/**
 * Document Upload Handler with Encryption
 */
class EncryptedDocumentUploader {
    constructor() {
        this.encryption = new DocumentEncryption();
        this.uploadEndpoint = '/api/documents/upload';
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
        this.allowedTypes = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ];
    }

    /**
     * Initialize file upload with encryption
     * @param {HTMLInputElement} fileInput - File input element
     * @param {string} sessionToken - User session token for key derivation
     */
    async initializeUpload(fileInput, sessionToken) {
        try {
            const files = Array.from(fileInput.files);
            const results = [];

            for (const file of files) {
                if (!this.validateFile(file)) {
                    throw new Error(`Invalid file: ${file.name}`);
                }

                const result = await this.encryptAndUpload(file, sessionToken);
                results.push(result);
            }

            return results;
        } catch (error) {
            console.error('Upload failed:', error);
            throw error;
        }
    }

    /**
     * Validate file before encryption/upload
     * @param {File} file - File to validate
     * @returns {boolean} Validation result
     */
    validateFile(file) {
        if (file.size > this.maxFileSize) {
            alert(`File ${file.name} is too large. Maximum size is ${this.maxFileSize / 1024 / 1024}MB`);
            return false;
        }

        if (!this.allowedTypes.includes(file.type)) {
            alert(`File type ${file.type} is not allowed`);
            return false;
        }

        return true;
    }

    /**
     * Encrypt file and upload to server
     * @param {File} file - File to encrypt and upload
     * @param {string} sessionToken - Session token for key derivation
     * @returns {Promise<Object>} Upload result
     */
    async encryptAndUpload(file, sessionToken) {
        try {
            // Generate salt and derive encryption key
            const salt = this.encryption.generateSalt();
            const encryptionKey = await this.encryption.deriveKey(sessionToken, salt);

            // Encrypt the file
            const encryptedFile = await this.encryption.encryptFile(file, encryptionKey);

            // Export key for secure transmission (encrypted by server)
            const exportedKey = await this.encryption.exportKey(encryptionKey);

            // Prepare upload data
            const uploadData = {
                encryptedData: encryptedFile.encryptedData,
                iv: encryptedFile.iv,
                salt: salt,
                clientKey: exportedKey, // Will be re-encrypted by server
                metadata: {
                    originalName: encryptedFile.originalName,
                    originalSize: encryptedFile.originalSize,
                    mimeType: encryptedFile.mimeType,
                    timestamp: encryptedFile.timestamp,
                    algorithm: encryptedFile.algorithm,
                    keyLength: encryptedFile.keyLength
                }
            };

            // Upload to server
            const response = await this.uploadToServer(uploadData);

            return {
                success: true,
                documentId: response.documentId,
                filename: file.name,
                size: file.size,
                encrypted: true
            };
        } catch (error) {
            console.error('Encryption/upload failed:', error);
            return {
                success: false,
                filename: file.name,
                error: error.message
            };
        }
    }

    /**
     * Upload encrypted data to server
     * @param {Object} uploadData - Encrypted file data
     * @returns {Promise<Object>} Server response
     */
    async uploadToServer(uploadData) {
        const response = await fetch(this.uploadEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Encryption-Enabled': 'true'
            },
            body: JSON.stringify(uploadData)
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        return await response.json();
    }
}

/**
 * Document Download Handler with Decryption
 */
class EncryptedDocumentDownloader {
    constructor() {
        this.encryption = new DocumentEncryption();
        this.downloadEndpoint = '/api/documents/download';
    }

    /**
     * Download and decrypt document
     * @param {string} documentId - Document ID to download
     * @param {string} sessionToken - Session token for key derivation
     * @returns {Promise<Object>} Download result
     */
    async downloadAndDecrypt(documentId, sessionToken) {
        try {
            // Download encrypted document from server
            const encryptedDocument = await this.downloadFromServer(documentId);

            // Derive decryption key using original salt
            const decryptionKey = await this.encryption.deriveKey(
                sessionToken, 
                encryptedDocument.salt
            );

            // Decrypt the document
            const decryptedData = await this.encryption.decryptFile(
                encryptedDocument.encryptedData,
                encryptedDocument.iv,
                decryptionKey
            );

            // Create downloadable blob
            const blob = this.encryption.createBlobFromDecrypted(
                decryptedData,
                encryptedDocument.metadata.mimeType
            );

            return {
                success: true,
                blob: blob,
                filename: encryptedDocument.metadata.originalName,
                mimeType: encryptedDocument.metadata.mimeType,
                size: encryptedDocument.metadata.originalSize
            };
        } catch (error) {
            console.error('Download/decryption failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Download encrypted document from server
     * @param {string} documentId - Document ID
     * @returns {Promise<Object>} Encrypted document data
     */
    async downloadFromServer(documentId) {
        const response = await fetch(`${this.downloadEndpoint}/${documentId}`, {
            method: 'GET',
            headers: {
                'X-Encryption-Enabled': 'true'
            }
        });

        if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Trigger file download in browser
     * @param {string} documentId - Document ID
     * @param {string} sessionToken - Session token
     */
    async triggerDownload(documentId, sessionToken) {
        const result = await this.downloadAndDecrypt(documentId, sessionToken);
        
        if (result.success) {
            this.encryption.downloadDecryptedFile(
                await result.blob.arrayBuffer(),
                result.filename,
                result.mimeType
            );
        } else {
            throw new Error(result.error);
        }
    }
}

/**
 * UI Integration Helper Functions
 */
class EncryptionUI {
    constructor() {
        this.uploader = new EncryptedDocumentUploader();
        this.downloader = new EncryptedDocumentDownloader();
    }

    /**
     * Initialize file input with encryption
     * @param {string} inputSelector - CSS selector for file input
     * @param {string} sessionToken - User session token
     */
    initializeFileInput(inputSelector, sessionToken) {
        const fileInput = document.querySelector(inputSelector);
        if (!fileInput) {
            console.error('File input not found:', inputSelector);
            return;
        }

        fileInput.addEventListener('change', async (event) => {
            const files = event.target.files;
            if (files.length === 0) return;

            try {
                this.showUploadProgress(true);
                const results = await this.uploader.initializeUpload(fileInput, sessionToken);
                this.handleUploadResults(results);
            } catch (error) {
                this.showUploadError(error.message);
            } finally {
                this.showUploadProgress(false);
            }
        });
    }

    /**
     * Show/hide upload progress indicator
     * @param {boolean} show - Whether to show progress
     */
    showUploadProgress(show) {
        const progressElement = document.getElementById('upload-progress');
        if (progressElement) {
            progressElement.style.display = show ? 'block' : 'none';
        }
    }

    /**
     * Handle upload results
     * @param {Array} results - Upload results array
     */
    handleUploadResults(results) {
        const successCount = results.filter(r => r.success).length;
        const totalCount = results.length;

        if (successCount === totalCount) {
            this.showUploadSuccess(`Successfully uploaded ${successCount} file(s) with encryption`);
        } else {
            this.showUploadError(`Upload completed: ${successCount}/${totalCount} files successful`);
        }

        // Update UI with uploaded files
        this.updateFileList(results);
    }

    /**
     * Show upload success message
     * @param {string} message - Success message
     */
    showUploadSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success';
        alertDiv.textContent = message;
        this.insertAlert(alertDiv);
    }

    /**
     * Show upload error message
     * @param {string} message - Error message
     */
    showUploadError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger';
        alertDiv.textContent = message;
        this.insertAlert(alertDiv);
    }

    /**
     * Insert alert into DOM
     * @param {HTMLElement} alertElement - Alert element
     */
    insertAlert(alertElement) {
        const container = document.querySelector('.upload-container') || document.body;
        container.insertBefore(alertElement, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertElement.parentNode) {
                alertElement.parentNode.removeChild(alertElement);
            }
        }, 5000);
    }

    /**
     * Update file list in UI
     * @param {Array} results - Upload results
     */
    updateFileList(results) {
        const fileListElement = document.getElementById('uploaded-files');
        if (!fileListElement) return;

        results.forEach(result => {
            const listItem = document.createElement('li');
            listItem.className = result.success ? 'file-success' : 'file-error';
            listItem.innerHTML = `
                <span class="filename">${result.filename}</span>
                <span class="status">${result.success ? '✓ Encrypted' : '✗ Failed'}</span>
                ${result.success ? `<button onclick="downloadFile('${result.documentId}')">Download</button>` : ''}
            `;
            fileListElement.appendChild(listItem);
        });
    }

    /**
     * Initialize download button handlers
     * @param {string} sessionToken - User session token
     */
    initializeDownloadHandlers(sessionToken) {
        // Global function for download buttons
        window.downloadFile = async (documentId) => {
            try {
                await this.downloader.triggerDownload(documentId, sessionToken);
            } catch (error) {
                this.showUploadError(`Download failed: ${error.message}`);
            }
        };
    }
}

// Export classes for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        DocumentEncryption,
        EncryptedDocumentUploader,
        EncryptedDocumentDownloader,
        EncryptionUI
    };
} else {
    // Browser global
    window.DocumentEncryption = DocumentEncryption;
    window.EncryptedDocumentUploader = EncryptedDocumentUploader;
    window.EncryptedDocumentDownloader = EncryptedDocumentDownloader;
    window.EncryptionUI = EncryptionUI;
} 