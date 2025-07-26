/**
 * API Service Module
 * Centralized API communication for the Korrekturtool application
 * Handles upload, processing, status checking, and download operations
 */

export class APIService {
    constructor() {
        this.baseURL = '/api/v1';
        this.timeout = 30000; // 30 seconds default timeout
    }

    /**
     * Upload a DOCX file to the server
     * @param {File} file - The DOCX file to upload
     * @returns {Promise<Object>} Upload response with file_id
     */
    async uploadFile(file) {
        if (!file) {
            throw new Error('Keine Datei zum Upload bereitgestellt');
        }

        if (!file.name.toLowerCase().endsWith('.docx')) {
            throw new Error('Nur DOCX-Dateien werden unterstützt');
        }

        const maxSize = 50 * 1024 * 1024; // 50MB
        if (file.size > maxSize) {
            throw new Error('Datei ist zu groß. Maximum: 50 MB');
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${this.baseURL}/upload`, {
                method: 'POST',
                body: formData,
                signal: AbortSignal.timeout(this.timeout)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Upload fehlgeschlagen: ${response.status}`);
            }

            const result = await response.json();
            
            if (!result.file_id) {
                throw new Error('Ungültige Server-Antwort: file_id fehlt');
            }

            return result;

        } catch (error) {
            if (error.name === 'TimeoutError') {
                throw new Error('Upload-Timeout: Die Datei konnte nicht rechtzeitig hochgeladen werden');
            }
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Netzwerkfehler: Bitte überprüfen Sie Ihre Internetverbindung');
            }
            throw error;
        }
    }

    /**
     * Submit a document for processing
     * @param {Object} processingRequest - Processing configuration
     * @param {string} processingRequest.file_id - ID of uploaded file
     * @param {string} processingRequest.processing_mode - Processing mode ('complete' or 'performance')
     * @param {Array} processingRequest.categories - Analysis categories
     * @param {string} processingRequest.output_filename - Optional output filename
     * @returns {Promise<Object>} Processing response with job_id
     */
    async processDocument(processingRequest) {
        if (!processingRequest.file_id) {
            throw new Error('file_id ist erforderlich für die Verarbeitung');
        }

        // Format the request according to backend API expectations
        const requestBody = {
            file_id: processingRequest.file_id,
            processing_mode: processingRequest.processing_mode || 'complete',
            options: {
                categories: processingRequest.categories || ['grammar', 'style', 'clarity', 'academic'],
                output_filename: processingRequest.output_filename || null
            }
        };

        try {
            const response = await fetch(`${this.baseURL}/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody),
                signal: AbortSignal.timeout(this.timeout)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Verarbeitung fehlgeschlagen: ${response.status}`);
            }

            const result = await response.json();
            
            if (!result.job_id) {
                throw new Error('Ungültige Server-Antwort: job_id fehlt');
            }

            return result;

        } catch (error) {
            if (error.name === 'TimeoutError') {
                throw new Error('Verarbeitungs-Timeout: Der Server antwortet nicht rechtzeitig');
            }
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Netzwerkfehler: Bitte überprüfen Sie Ihre Internetverbindung');
            }
            throw error;
        }
    }

    /**
     * Check the processing status of a job
     * @param {string} jobId - The job ID to check
     * @returns {Promise<Object>} Status response
     */
    async getProcessingStatus(jobId) {
        if (!jobId) {
            throw new Error('job_id ist erforderlich für Status-Abfrage');
        }

        try {
            const response = await fetch(`${this.baseURL}/status/${jobId}`, {
                method: 'GET',
                signal: AbortSignal.timeout(this.timeout)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Status-Abfrage fehlgeschlagen: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            if (error.name === 'TimeoutError') {
                throw new Error('Status-Abfrage-Timeout: Der Server antwortet nicht rechtzeitig');
            }
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Netzwerkfehler: Bitte überprüfen Sie Ihre Internetverbindung');
            }
            throw error;
        }
    }

    /**
     * Download a processed file
     * @param {string} fileId - The file ID to download
     * @returns {Promise<Blob>} File blob for download
     */
    async downloadFile(fileId) {
        if (!fileId) {
            throw new Error('file_id ist erforderlich für Download');
        }

        try {
            const response = await fetch(`${this.baseURL}/download/${fileId}`, {
                method: 'GET',
                signal: AbortSignal.timeout(60000) // 60 seconds for download
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Download fehlgeschlagen: ${response.status}`);
            }

            return await response.blob();

        } catch (error) {
            if (error.name === 'TimeoutError') {
                throw new Error('Download-Timeout: Die Datei konnte nicht rechtzeitig heruntergeladen werden');
            }
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Netzwerkfehler: Bitte überprüfen Sie Ihre Internetverbindung');
            }
            throw error;
        }
    }

    /**
     * Get API information and health status
     * @returns {Promise<Object>} API info response
     */
    async getAPIInfo() {
        try {
            const response = await fetch(`${this.baseURL}/info`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000) // 5 seconds for health check
            });

            if (!response.ok) {
                throw new Error(`API nicht verfügbar: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            if (error.name === 'TimeoutError') {
                throw new Error('API-Timeout: Der Server antwortet nicht');
            }
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('API nicht erreichbar: Bitte überprüfen Sie Ihre Internetverbindung');
            }
            throw error;
        }
    }

    /**
     * Helper method to trigger file download in browser
     * @param {Blob} blob - File blob to download
     * @param {string} filename - Suggested filename
     */
    triggerDownload(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || 'corrected_document.docx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
}

// Export singleton instance
export const apiService = new APIService();