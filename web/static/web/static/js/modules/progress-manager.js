/**
 * Progress Manager Module
 * Manages real-time progress visualization for document processing
 * Handles progress bars, phase indicators, timing information, and status updates
 */

/**
 * Processing phases configuration
 */
const PROCESSING_PHASES = {
    'parsing': { 
        icon: '📄', 
        label: 'Upload', 
        description: 'Dokument wird verarbeitet',
        elementId: 'phaseUpload'
    },
    'analyzing': { 
        icon: '🤖', 
        label: 'KI-Analyse', 
        description: 'Text wird analysiert',
        elementId: 'phaseAnalysis'
    },
    'commenting': { 
        icon: '💬', 
        label: 'Kommentare', 
        description: 'Verbesserungen werden generiert',
        elementId: 'phaseComments'
    },
    'integrating': { 
        icon: '📝', 
        label: 'Integration', 
        description: 'Kommentare werden eingefügt',
        elementId: 'phaseIntegration'
    }
};

/**
 * Progress Manager Class
 * Handles real-time progress visualization including progress bars,
 * processing phases, timing information, and status messages
 */
export class ProgressManager {
    constructor(eventBus) {
        this.eventBus = eventBus;
        this.isTracking = false;
        this.currentJobId = null;
        this.startTime = null;
        this.estimatedDuration = null;
        this.currentPhase = null;
        this.progress = 0;
        
        // Cache DOM elements
        this.elements = {};
        this.timers = {
            elapsed: null,
            estimated: null
        };
        
        console.log('📊 ProgressManager initialized');
    }
    
    /**
     * Initialize the progress manager and cache DOM elements
     */
    init() {
        this.cacheDOMElements();
        this.setupEventListeners();
        console.log('📊 ProgressManager DOM elements cached and events setup');
    }
    
    /**
     * Cache DOM elements for performance
     * @private
     */
    cacheDOMElements() {
        // Progress bar elements
        this.elements.progressBar = document.querySelector('.progress-bar[role="progressbar"]');
        this.elements.progressFill = document.getElementById('progressFill');
        this.elements.progressPercentage = document.getElementById('progressPercentage');
        this.elements.progressText = document.getElementById('progressText');
        
        // Phase elements
        this.elements.progressPhases = document.getElementById('progressPhases');
        this.elements.phases = {
            parsing: document.getElementById('phaseUpload'),
            analyzing: document.getElementById('phaseAnalysis'),
            commenting: document.getElementById('phaseComments'),
            integrating: document.getElementById('phaseIntegration')
        };
        
        // Timing elements
        this.elements.estimatedTime = document.getElementById('estimatedTime');
        this.elements.elapsedTime = document.getElementById('elapsedTime');
        
        // Status elements
        this.elements.statusBadge = document.getElementById('statusBadge');
        
        console.log('📦 ProgressManager DOM elements cached');
    }
    
    /**
     * Setup event listeners for WebSocket events
     * @private
     */
    setupEventListeners() {
        // Job started event
        this.eventBus.on('websocket:job-started', (data) => {
            this.handleJobStarted(data);
        });
        
        // Progress update event
        this.eventBus.on('websocket:progress-update', (data) => {
            this.handleProgressUpdate(data);
        });
        
        // Stage completed event
        this.eventBus.on('websocket:stage-completed', (data) => {
            this.handleStageCompleted(data);
        });
        
        // Job completed event
        this.eventBus.on('websocket:job-completed', (data) => {
            this.handleJobCompleted(data);
        });
        
        // Job failed event
        this.eventBus.on('websocket:job-failed', (data) => {
            this.handleJobFailed(data);
        });
        
        // WebSocket connection events
        this.eventBus.on('websocket:connected', () => {
            this.updateConnectionStatus(true);
        });
        
        this.eventBus.on('websocket:disconnected', () => {
            this.updateConnectionStatus(false);
        });
        
        this.eventBus.on('websocket:reconnected', () => {
            this.updateConnectionStatus(true);
            this.showMessage('Verbindung wiederhergestellt', 'success');
        });
        
        this.eventBus.on('websocket:reconnect-failed', () => {
            this.showMessage('Verbindung fehlgeschlagen. Versuche es erneut...', 'error');
        });
        
        console.log('👂 ProgressManager event listeners setup complete');
    }
    
    /**
     * Start tracking progress for a specific job
     * @param {string} jobId - The job ID to track
     */
    startTracking(jobId) {
        console.log(`📊 Starting progress tracking for job: ${jobId}`);
        
        this.currentJobId = jobId;
        this.isTracking = true;
        this.startTime = Date.now();
        this.progress = 0;
        this.currentPhase = null;
        
        // Reset progress visualization
        this.resetProgress();
        
        // Start elapsed time timer
        this.startElapsedTimer();
        
        // Show initial status
        this.updateStatus('Initialisierung...', 'processing');
        this.updateProgress(0, 'Verarbeitung wird gestartet...');
        
        console.log('✅ Progress tracking started');
    }
    
    /**
     * Stop tracking progress
     */
    stopTracking() {
        console.log('📊 Stopping progress tracking');
        
        this.isTracking = false;
        this.currentJobId = null;
        this.currentPhase = null;
        
        // Stop timers
        this.stopTimers();
        
        console.log('✅ Progress tracking stopped');
    }
    
    /**
     * Handle job started event from WebSocket
     * @param {Object} data - Job started data
     * @private
     */
    handleJobStarted(data) {
        console.log('🚀 Handling job started:', data);
        
        if (data.job_id !== this.currentJobId) {
            console.warn('⚠️ Received job started for different job ID');
            return;
        }
        
        // Set estimated duration if provided
        if (data.estimated_duration) {
            this.estimatedDuration = data.estimated_duration;
            this.updateEstimatedTime(data.estimated_duration);
        }
        
        // Initialize phases if provided
        if (data.stages && Array.isArray(data.stages)) {
            this.initializePhases(data.stages);
        }
        
        this.updateStatus('Verarbeitung gestartet', 'processing');
        this.showMessage('Verarbeitung erfolgreich gestartet!', 'success');
    }
    
    /**
     * Handle progress update event from WebSocket
     * @param {Object} data - Progress update data
     * @private
     */
    handleProgressUpdate(data) {
        console.log('📊 Handling progress update:', data);
        
        if (data.job_id !== this.currentJobId) {
            console.warn('⚠️ Received progress update for different job ID');
            return;
        }
        
        // Update progress bar
        if (typeof data.progress === 'number') {
            this.updateProgress(data.progress, data.message || '');
        }
        
        // Update current phase
        if (data.stage && data.stage !== this.currentPhase) {
            this.updatePhase(data.stage);
        }
        
        // Update estimated remaining time
        if (data.estimated_remaining) {
            this.updateEstimatedTime(data.estimated_remaining);
        }
        
        // Update status message
        if (data.message) {
            this.updateProgressMessage(data.message);
        }
    }
    
    /**
     * Handle stage completed event from WebSocket
     * @param {Object} data - Stage completed data
     * @private
     */
    handleStageCompleted(data) {
        console.log('✅ Handling stage completed:', data);
        
        if (data.job_id !== this.currentJobId) {
            console.warn('⚠️ Received stage completed for different job ID');
            return;
        }
        
        // Mark completed stage
        if (data.completed_stage) {
            this.markPhaseCompleted(data.completed_stage);
        }
        
        // Move to next stage
        if (data.next_stage) {
            this.updatePhase(data.next_stage);
        }
        
        // Show completion message for stage
        const phaseInfo = PROCESSING_PHASES[data.completed_stage];
        if (phaseInfo) {
            this.showMessage(`${phaseInfo.label} abgeschlossen`, 'success');
        }
    }
    
    /**
     * Handle job completed event from WebSocket
     * @param {Object} data - Job completion data
     * @private
     */
    handleJobCompleted(data) {
        console.log('🎉 Handling job completed:', data);
        
        if (data.job_id !== this.currentJobId) {
            console.warn('⚠️ Received job completed for different job ID');
            return;
        }
        
        // Complete progress
        this.updateProgress(100, 'Verarbeitung erfolgreich abgeschlossen!');
        
        // Mark all phases as completed
        this.markAllPhasesCompleted();
        
        // Update status
        this.updateStatus('Abgeschlossen', 'completed');
        
        // Show success message
        this.showMessage('Dokument erfolgreich verarbeitet!', 'success');
        
        // Stop tracking
        this.stopTracking();
        
        // Emit completion event for other components
        this.eventBus.emit('progress:completed', {
            jobId: this.currentJobId,
            processingTime: data.processing_time,
            success: true,
            resultData: data
        });
    }
    
    /**
     * Handle job failed event from WebSocket
     * @param {Object} data - Job failure data
     * @private
     */
    handleJobFailed(data) {
        console.error('💥 Handling job failed:', data);
        
        if (data.job_id !== this.currentJobId) {
            console.warn('⚠️ Received job failed for different job ID');
            return;
        }
        
        // Update status to failed
        this.updateStatus('Fehler aufgetreten', 'error');
        
        // Update progress message with error
        const errorMessage = data.error || 'Ein unbekannter Fehler ist aufgetreten';
        this.updateProgressMessage(`Fehler: ${errorMessage}`);
        
        // Mark current phase as failed
        if (data.stage) {
            this.markPhaseFailed(data.stage);
        }
        
        // Show error message
        this.showMessage(`Verarbeitung fehlgeschlagen: ${errorMessage}`, 'error');
        
        // Stop tracking
        this.stopTracking();
        
        // Emit failure event for other components
        this.eventBus.emit('progress:failed', {
            jobId: this.currentJobId,
            error: errorMessage,
            stage: data.stage,
            processingTime: data.processing_time
        });
    }
    
    /**
     * Update progress bar and percentage
     * @param {number} percentage - Progress percentage (0-100)
     * @param {string} message - Progress message
     */
    updateProgress(percentage, message = '') {
        this.progress = Math.max(0, Math.min(100, percentage));
        
        // Update progress bar
        if (this.elements.progressFill) {
            this.elements.progressFill.style.width = `${this.progress}%`;
        }
        
        // Update percentage display
        if (this.elements.progressPercentage) {
            this.elements.progressPercentage.textContent = `${Math.round(this.progress)}%`;
        }
        
        // Update ARIA attributes
        if (this.elements.progressBar) {
            this.elements.progressBar.setAttribute('aria-valuenow', this.progress);
        }
        
        // Update message if provided
        if (message && this.elements.progressText) {
            this.updateProgressMessage(message);
        }
        
        console.log(`📊 Progress updated: ${this.progress}% - ${message}`);
    }
    
    /**
     * Update progress message
     * @param {string} message - Progress message
     */
    updateProgressMessage(message) {
        if (this.elements.progressText) {
            this.elements.progressText.textContent = message;
        }
    }
    
    /**
     * Update current processing phase
     * @param {string} phase - Phase name
     */
    updatePhase(phase) {
        console.log(`🔄 Updating phase to: ${phase}`);
        
        // Remove active class from all phases
        Object.values(this.elements.phases).forEach(element => {
            if (element) {
                element.classList.remove('active', 'completed', 'failed');
            }
        });
        
        // Set new active phase
        this.currentPhase = phase;
        const phaseElement = this.elements.phases[phase];
        if (phaseElement) {
            phaseElement.classList.add('active');
        }
        
        // Update progress message with phase description
        const phaseInfo = PROCESSING_PHASES[phase];
        if (phaseInfo) {
            this.updateProgressMessage(phaseInfo.description);
        }
    }
    
    /**
     * Mark a phase as completed
     * @param {string} phase - Phase name
     */
    markPhaseCompleted(phase) {
        const phaseElement = this.elements.phases[phase];
        if (phaseElement) {
            phaseElement.classList.remove('active', 'failed');
            phaseElement.classList.add('completed');
            console.log(`✅ Phase ${phase} marked as completed`);
        }
    }
    
    /**
     * Mark a phase as failed
     * @param {string} phase - Phase name
     */
    markPhaseFailed(phase) {
        const phaseElement = this.elements.phases[phase];
        if (phaseElement) {
            phaseElement.classList.remove('active', 'completed');
            phaseElement.classList.add('failed');
            console.log(`❌ Phase ${phase} marked as failed`);
        }
    }
    
    /**
     * Mark all phases as completed
     */
    markAllPhasesCompleted() {
        Object.values(this.elements.phases).forEach(element => {
            if (element) {
                element.classList.remove('active', 'failed');
                element.classList.add('completed');
            }
        });
        console.log('✅ All phases marked as completed');
    }
    
    /**
     * Initialize phases based on provided stages
     * @param {string[]} stages - Array of stage names
     */
    initializePhases(stages) {
        console.log('🔄 Initializing phases:', stages);
        
        // Reset all phases
        Object.values(this.elements.phases).forEach(element => {
            if (element) {
                element.classList.remove('active', 'completed', 'failed');
                element.style.display = 'none';
            }
        });
        
        // Show only phases that are in the stages array
        stages.forEach(stage => {
            const phaseElement = this.elements.phases[stage];
            if (phaseElement) {
                phaseElement.style.display = 'inline-flex';
            }
        });
    }
    
    /**
     * Update status badge
     * @param {string} text - Status text
     * @param {string} type - Status type (processing, completed, error)
     */
    updateStatus(text, type = 'processing') {
        if (this.elements.statusBadge) {
            this.elements.statusBadge.textContent = text;
            this.elements.statusBadge.className = `status-badge ${type}`;
        }
        console.log(`📊 Status updated: ${text} (${type})`);
    }
    
    /**
     * Update connection status indicator
     * @param {boolean} connected - Connection status
     */
    updateConnectionStatus(connected) {
        const statusIndicator = document.querySelector('.connection-status');
        if (statusIndicator) {
            statusIndicator.classList.toggle('connected', connected);
            statusIndicator.classList.toggle('disconnected', !connected);
        }
    }
    
    /**
     * Show a temporary message to the user
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
     * Start elapsed time timer
     * @private
     */
    startElapsedTimer() {
        if (this.timers.elapsed) {
            clearInterval(this.timers.elapsed);
        }
        
        this.timers.elapsed = setInterval(() => {
            if (this.startTime && this.elements.elapsedTime) {
                const elapsed = Date.now() - this.startTime;
                this.elements.elapsedTime.textContent = this.formatDuration(elapsed);
            }
        }, 1000);
    }
    
    /**
     * Update estimated time display
     * @param {string|number} estimatedTime - Estimated time remaining
     */
    updateEstimatedTime(estimatedTime) {
        if (this.elements.estimatedTime) {
            if (typeof estimatedTime === 'number') {
                this.elements.estimatedTime.textContent = this.formatDuration(estimatedTime * 1000);
            } else {
                this.elements.estimatedTime.textContent = estimatedTime;
            }
        }
    }
    
    /**
     * Format duration in milliseconds to human-readable string
     * @param {number} ms - Duration in milliseconds
     * @returns {string} Formatted duration
     * @private
     */
    formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes > 0) {
            return `${minutes}m ${remainingSeconds}s`;
        } else {
            return `${remainingSeconds}s`;
        }
    }
    
    /**
     * Stop all timers
     * @private
     */
    stopTimers() {
        if (this.timers.elapsed) {
            clearInterval(this.timers.elapsed);
            this.timers.elapsed = null;
        }
        if (this.timers.estimated) {
            clearInterval(this.timers.estimated);
            this.timers.estimated = null;
        }
    }
    
    /**
     * Reset progress visualization to initial state
     */
    resetProgress() {
        console.log('🔄 Resetting progress visualization');
        
        // Reset progress bar
        this.updateProgress(0, 'Initialisierung...');
        
        // Reset phases
        Object.values(this.elements.phases).forEach(element => {
            if (element) {
                element.classList.remove('active', 'completed', 'failed');
                element.style.display = 'inline-flex';
            }
        });
        
        // Reset timing
        if (this.elements.estimatedTime) {
            this.elements.estimatedTime.textContent = '--';
        }
        if (this.elements.elapsedTime) {
            this.elements.elapsedTime.textContent = '0s';
        }
        
        // Reset status
        this.updateStatus('Initialisierung...', 'processing');
        
        console.log('✅ Progress visualization reset');
    }
    
    /**
     * Get current progress information
     * @returns {Object} Current progress state
     */
    getProgressInfo() {
        return {
            isTracking: this.isTracking,
            currentJobId: this.currentJobId,
            progress: this.progress,
            currentPhase: this.currentPhase,
            startTime: this.startTime,
            estimatedDuration: this.estimatedDuration,
            elapsedTime: this.startTime ? Date.now() - this.startTime : 0
        };
    }
    
    /**
     * Cleanup and destroy the progress manager
     */
    destroy() {
        console.log('🧹 Destroying ProgressManager...');
        
        // Stop tracking and timers
        this.stopTracking();
        
        // Clear event listeners
        this.eventBus.off('websocket:job-started');
        this.eventBus.off('websocket:progress-update');
        this.eventBus.off('websocket:stage-completed');
        this.eventBus.off('websocket:job-completed');
        this.eventBus.off('websocket:job-failed');
        this.eventBus.off('websocket:connected');
        this.eventBus.off('websocket:disconnected');
        this.eventBus.off('websocket:reconnected');
        this.eventBus.off('websocket:reconnect-failed');
        
        // Clear cached elements
        this.elements = {};
        
        console.log('💀 ProgressManager destroyed');
    }
}

export default ProgressManager;