/**
 * Results Manager Module
 * Manages results display and document download after processing completion
 * Handles results visualization, download functionality, and error recovery
 */

/**
 * Results Manager Class
 * Handles displaying processing results, download functionality, and result state management
 */
export class ResultsManager {
    constructor(eventBus) {
        this.eventBus = eventBus;
        this.isVisible = false;
        this.currentResultData = null;
        this.downloadRetryCount = 0;
        this.maxDownloadRetries = 3;
        
        // Cache DOM elements
        this.elements = {};
        
        console.log('📊 ResultsManager initialized');
    }
    
    /**
     * Initialize the results manager and cache DOM elements
     */
    init() {
        this.cacheDOMElements();
        this.setupEventListeners();
        console.log('📊 ResultsManager DOM elements cached and events setup');
    }
    
    /**
     * Cache DOM elements for performance
     * @private
     */
    cacheDOMElements() {
        // Results section elements
        this.elements.resultsSection = document.getElementById('resultsSection');
        this.elements.resultsList = document.getElementById('resultsList');
        
        console.log('📦 ResultsManager DOM elements cached');
    }
    
    /**
     * Setup event listeners for processing completion and app events
     * @private
     */
    setupEventListeners() {
        // Listen for processing completion
        this.eventBus.on('progress:completed', (data) => {
            this.handleProcessingCompleted(data);
        });
        
        // Listen for processing failure
        this.eventBus.on('progress:failed', (data) => {
            this.handleProcessingFailed(data);
        });
        
        // Listen for app reset (new upload)
        this.eventBus.on('app:reset', () => {
            this.clearResults();
        });
        
        // Listen for upload events to clear previous results
        this.eventBus.on('upload:file-selected', () => {
            this.clearResults();
        });
        
        console.log('👂 ResultsManager event listeners setup complete');
    }
    
    /**
     * Handle processing completion event and display results
     * @param {Object} data - Processing completion data
     */
    handleProcessingCompleted(data) {
        console.log('🎉 Handling processing completed:', data);
        
        this.currentResultData = data;
        this.downloadRetryCount = 0;
        
        // Generate and display results
        this.generateResultsHTML(data);
        this.showResults();
        
        // Emit results displayed event
        this.eventBus.emit('results:displayed', {
            jobId: data.jobId,
            success: true,
            timestamp: Date.now()
        });
        
        console.log('✅ Results displayed successfully');
    }
    
    /**
     * Handle processing failure and display error results
     * @param {Object} data - Processing failure data
     */
    handleProcessingFailed(data) {
        console.error('💥 Handling processing failed:', data);
        
        this.currentResultData = data;
        
        // Generate error results HTML
        this.generateErrorResultsHTML(data);
        this.showResults();
        
        // Emit results displayed event
        this.eventBus.emit('results:displayed', {
            jobId: data.jobId,
            success: false,
            error: data.error,
            timestamp: Date.now()
        });
        
        console.log('❌ Error results displayed');
    }
    
    /**
     * Generate and insert success results HTML
     * @param {Object} data - Processing completion data
     * @private
     */
    generateResultsHTML(data) {
        if (!this.elements.resultsList) {
            console.error('❌ ResultsList element not found');
            return;
        }
        
        // Extract data with defaults
        const {
            jobId,
            processingTime = 'Unbekannt',
            success = true,
            resultData = {}
        } = data;
        
        const {
            total_suggestions = 0,
            categories_processed = [],
            file_size_mb = 0,
            download_url = null
        } = resultData;
        
        // Format categories for display
        const categoryMap = {
            'grammar': 'Grammatik',
            'style': 'Stil', 
            'clarity': 'Klarheit',
            'academic': 'Wissenschaftlichkeit'
        };
        
        const categoriesText = categories_processed
            .map(cat => categoryMap[cat] || cat)
            .join(', ') || 'Alle Kategorien';
        
        // Generate download button (only if download URL available)
        const downloadButtonHTML = download_url ? `
            <button class=\"btn btn-primary\" 
                    id=\"downloadButton\" 
                    data-download-url=\"${download_url}\"
                    aria-describedby=\"download-help\">
                📥 Dokument herunterladen
            </button>
        ` : `
            <button class=\"btn btn-primary\" disabled>
                📥 Download nicht verfügbar
            </button>
        `;
        
        // Generate complete results HTML
        const resultsHTML = `
            <div class=\"result-item\" role=\"region\" aria-labelledby=\"result-heading\">
                <h4 id=\"result-heading\">📄 Ihr korrigiertes Dokument ist bereit</h4>
                <p>Die KI-Analyse wurde erfolgreich abgeschlossen. Sie können Ihr verbessertes Dokument jetzt herunterladen.</p>
                
                <div class=\"result-stats\">
                    <div class=\"stat\">
                        <span class=\"stat-label\">Verbesserungen:</span>
                        <span class=\"stat-value\">${total_suggestions} Kommentare</span>
                    </div>
                    <div class=\"stat\">
                        <span class=\"stat-label\">Kategorien:</span>
                        <span class=\"stat-value\">${categoriesText}</span>
                    </div>
                    <div class=\"stat\">
                        <span class=\"stat-label\">Verarbeitungszeit:</span>
                        <span class=\"stat-value\">${processingTime}</span>
                    </div>
                    <div class=\"stat\">
                        <span class=\"stat-label\">Dateigröße:</span>
                        <span class=\"stat-value\">${file_size_mb} MB</span>
                    </div>
                </div>
                
                <div class=\"result-actions\">
                    ${downloadButtonHTML}
                    <button class=\"btn btn-secondary\" id=\"newUploadButton\">
                        🔄 Neues Dokument
                    </button>
                    <div id=\"download-help\" class=\"visually-hidden\">
                        Lädt die korrigierte Version Ihres Dokuments mit KI-generierten Kommentaren herunter
                    </div>
                </div>
            </div>
        `;
        
        // Insert HTML and setup event listeners
        this.elements.resultsList.innerHTML = resultsHTML;
        this.setupResultsEventListeners();
        
        console.log('📊 Results HTML generated and inserted');
    }
    
    /**
     * Generate and insert error results HTML
     * @param {Object} data - Processing failure data
     * @private
     */
    generateErrorResultsHTML(data) {
        if (!this.elements.resultsList) {
            console.error('❌ ResultsList element not found');
            return;
        }
        
        const {
            error = 'Ein unbekannter Fehler ist aufgetreten',
            stage = 'processing',
            processingTime = 'Unbekannt'
        } = data;
        
        const errorHTML = `
            <div class=\"result-item result-error\" role=\"region\" aria-labelledby=\"error-heading\">
                <h4 id=\"error-heading\">❌ Verarbeitung fehlgeschlagen</h4>
                <p>Leider konnte Ihr Dokument nicht erfolgreich verarbeitet werden.</p>
                
                <div class=\"error-details\">
                    <div class=\"error-stat\">
                        <span class=\"stat-label\">Fehler:</span>
                        <span class=\"stat-value error-message\">${error}</span>
                    </div>
                    <div class=\"error-stat\">
                        <span class=\"stat-label\">Phase:</span>
                        <span class=\"stat-value\">${this.getPhaseDisplayName(stage)}</span>
                    </div>
                    <div class=\"error-stat\">
                        <span class=\"stat-label\">Zeit bis Fehler:</span>
                        <span class=\"stat-value\">${processingTime}</span>
                    </div>
                </div>
                
                <div class=\"result-actions\">
                    <button class=\"btn btn-primary\" id=\"retryProcessingButton\">
                        🔄 Erneut versuchen
                    </button>
                    <button class=\"btn btn-secondary\" id=\"newUploadButton\">
                        📄 Neues Dokument
                    </button>
                </div>
            </div>
        `;
        
        // Insert HTML and setup event listeners
        this.elements.resultsList.innerHTML = errorHTML;
        this.setupErrorResultsEventListeners();
        
        console.log('❌ Error results HTML generated and inserted');
    }
    
    /**
     * Setup event listeners for results section buttons
     * @private
     */
    setupResultsEventListeners() {
        // Download button
        const downloadBtn = document.getElementById('downloadButton');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', (e) => {
                const downloadUrl = e.target.dataset.downloadUrl;
                if (downloadUrl) {
                    this.handleDownload(downloadUrl);
                }
            });
        }
        
        // New upload button
        const newUploadBtn = document.getElementById('newUploadButton');
        if (newUploadBtn) {
            newUploadBtn.addEventListener('click', () => {
                this.handleNewUpload();
            });
        }
    }
    
    /**
     * Setup event listeners for error results section buttons
     * @private
     */
    setupErrorResultsEventListeners() {
        // Retry processing button
        const retryBtn = document.getElementById('retryProcessingButton');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                this.handleRetryProcessing();
            });
        }
        
        // New upload button
        const newUploadBtn = document.getElementById('newUploadButton');
        if (newUploadBtn) {
            newUploadBtn.addEventListener('click', () => {
                this.handleNewUpload();
            });
        }
    }
    
    /**
     * Handle document download
     * @param {string} downloadUrl - URL to download the file
     */
    async handleDownload(downloadUrl) {
        try {
            console.log(`📥 Starting download from: ${downloadUrl}`);
            
            // Show loading state
            this.setDownloadButtonState('loading');
            
            // Create temporary download link
            const downloadLink = document.createElement('a');
            downloadLink.href = downloadUrl;
            downloadLink.download = ''; // Let server set filename via Content-Disposition
            downloadLink.style.display = 'none';
            
            // Add to DOM and trigger download
            document.body.appendChild(downloadLink);
            downloadLink.click();
            
            // Clean up
            setTimeout(() => {
                document.body.removeChild(downloadLink);
            }, 100);
            
            // Reset download button state
            setTimeout(() => {
                this.setDownloadButtonState('success');
            }, 1000);
            
            // Reset to normal state after success message
            setTimeout(() => {
                this.setDownloadButtonState('normal');
            }, 3000);
            
            // Emit download event
            this.eventBus.emit('results:download-attempted', {
                downloadUrl,
                success: true,
                timestamp: Date.now()
            });
            
            // Show success message
            this.showMessage('Download gestartet! Die Datei wird heruntergeladen.', 'success');
            
            console.log('✅ Download triggered successfully');
            
        } catch (error) {
            console.error('❌ Download failed:', error);
            this.handleDownloadError(error);
        }
    }
    
    /**
     * Handle download errors with retry mechanism
     * @param {Error} error - Download error
     */
    handleDownloadError(error) {
        this.downloadRetryCount++;
        
        console.error(`❌ Download attempt ${this.downloadRetryCount} failed:`, error);
        
        // Reset button state
        this.setDownloadButtonState('error');
        
        // Show error message with retry option
        if (this.downloadRetryCount < this.maxDownloadRetries) {
            this.showMessage(
                `Download fehlgeschlagen. Versuche es automatisch erneut... (${this.downloadRetryCount}/${this.maxDownloadRetries})`,
                'error'
            );
            
            // Retry after delay
            setTimeout(() => {
                if (this.currentResultData && this.currentResultData.resultData.download_url) {
                    this.handleDownload(this.currentResultData.resultData.download_url);
                }
            }, 2000);
        } else {
            this.showMessage(
                'Download fehlgeschlagen. Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support.',
                'error'
            );
            
            // Reset retry count for next attempt
            this.downloadRetryCount = 0;
        }
        
        // Emit download error event
        this.eventBus.emit('results:download-error', {
            error: error.message,
            retryCount: this.downloadRetryCount,
            timestamp: Date.now()
        });
    }
    
    /**
     * Set download button visual state
     * @param {string} state - Button state (normal, loading, success, error)
     * @private
     */
    setDownloadButtonState(state) {
        const downloadBtn = document.getElementById('downloadButton');
        if (!downloadBtn) return;
        
        // Remove existing state classes
        downloadBtn.classList.remove('loading', 'success', 'error');
        
        switch (state) {
            case 'loading':
                downloadBtn.classList.add('loading');
                downloadBtn.innerHTML = '⏳ Wird heruntergeladen...';
                downloadBtn.disabled = true;
                break;
            case 'success':
                downloadBtn.classList.add('success');
                downloadBtn.innerHTML = '✅ Download gestartet!';
                downloadBtn.disabled = false;
                break;
            case 'error':
                downloadBtn.classList.add('error');
                downloadBtn.innerHTML = '❌ Fehler beim Download';
                downloadBtn.disabled = false;
                break;
            case 'normal':
            default:
                downloadBtn.innerHTML = '📥 Dokument herunterladen';
                downloadBtn.disabled = false;
                break;
        }
    }
    
    /**
     * Handle retry processing request
     */
    handleRetryProcessing() {
        console.log('🔄 Retry processing requested');
        
        // Clear current results
        this.clearResults();
        
        // Emit retry event for app to handle
        this.eventBus.emit('results:retry-processing', {
            previousJobId: this.currentResultData?.jobId,
            timestamp: Date.now()
        });
        
        this.showMessage('Verarbeitung wird wiederholt...', 'info');
    }
    
    /**
     * Handle new upload request
     */
    handleNewUpload() {
        console.log('📄 New upload requested');
        
        // Clear results and reset app
        this.clearResults();
        
        // Emit new upload event
        this.eventBus.emit('results:new-upload-requested', {
            timestamp: Date.now()
        });
    }
    
    /**
     * Show results section
     */
    showResults() {
        if (this.elements.resultsSection) {
            this.elements.resultsSection.classList.add('active');
            this.isVisible = true;
            console.log('📊 Results section shown');
        }
    }
    
    /**
     * Hide results section
     */
    hideResults() {
        if (this.elements.resultsSection) {
            this.elements.resultsSection.classList.remove('active');
            this.isVisible = false;
            console.log('📊 Results section hidden');
        }
    }
    
    /**
     * Clear results and reset state
     */
    clearResults() {
        if (this.elements.resultsList) {
            this.elements.resultsList.innerHTML = '';
        }
        
        this.hideResults();
        this.currentResultData = null;
        this.downloadRetryCount = 0;
        
        console.log('🧹 Results cleared');
    }
    
    /**
     * Get display name for processing phase
     * @param {string} stage - Processing stage
     * @returns {string} Display name in German
     * @private
     */
    getPhaseDisplayName(stage) {
        const phaseMap = {
            'parsing': 'Upload und Parsing',
            'analyzing': 'KI-Analyse',
            'commenting': 'Kommentar-Generierung',
            'integrating': 'Integration',
            'processing': 'Verarbeitung'
        };
        
        return phaseMap[stage] || stage;
    }
    
    /**
     * Show a message to the user
     * @param {string} message - Message text
     * @param {string} type - Message type (success, error, info)
     */
    showMessage(message, type = 'info') {
        // Use the existing message system from the app
        this.eventBus.emit('ui:show-message', {
            message,
            type,
            duration: type === 'error' ? 8000 : 4000
        });
    }
    
    /**
     * Get current results information
     * @returns {Object} Current results state
     */
    getResultsInfo() {
        return {
            isVisible: this.isVisible,
            currentResultData: this.currentResultData,
            downloadRetryCount: this.downloadRetryCount
        };
    }
    
    /**
     * Cleanup and destroy the results manager
     */
    destroy() {
        console.log('🧹 Destroying ResultsManager...');
        
        // Clear results
        this.clearResults();
        
        // Clear event listeners
        this.eventBus.off('progress:completed');
        this.eventBus.off('progress:failed');
        this.eventBus.off('app:reset');
        this.eventBus.off('upload:file-selected');
        
        // Clear cached elements
        this.elements = {};
        
        console.log('💀 ResultsManager destroyed');
    }
}

export default ResultsManager;