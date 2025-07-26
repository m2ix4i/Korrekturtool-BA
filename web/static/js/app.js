/**
 * Main Application Controller
 * Korrekturtool für Wissenschaftliche Arbeiten
 * Modern modular architecture with ES6 modules
 */

// Import core modules
import { ThemeManager } from './modules/theme-manager.js';
import { EventBus } from './utils/event-bus.js';
import { UploadHandler } from './handlers/upload-handler.js';
import { ConfigManager } from './modules/config-manager.js';
import { WebSocketManager } from './modules/websocket-manager.js';
import { ProgressManager } from './modules/progress-manager.js';
import { ResultsManager } from './modules/results-manager.js';
import { APIService } from './services/api-service.js';

/**
 * Main Application Class
 * Orchestrates all application modules and components
 */
class KorrekturtoolApp {
    constructor() {
        this.version = '2.0.0';
        this.initialized = false;
        
        // Core system components
        this.eventBus = new EventBus();
        this.themeManager = null;
        this.uploadHandler = null;
        this.configManager = null;
        this.webSocketManager = null;
        this.progressManager = null;
        this.resultsManager = null;
        this.apiService = new APIService();
        
        // Application state
        this.state = {
            currentFileId: null,
            currentJobId: null,
            isProcessing: false,
            lastError: null
        };
        
        // DOM elements cache
        this.elements = {};
        
        console.log(`🚀 Korrekturtool App v${this.version} initializing...`);
        
        // Initialize when DOM is ready
        this.initializeWhenReady();
    }
    
    /**
     * Initialize application when DOM is ready
     */
    initializeWhenReady() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    /**
     * Initialize performance monitoring
     */
    initializePerformanceMonitoring() {
        this.performanceMetrics = {
            initStart: performance.now(),
            initEnd: null,
            loadTime: null
        };
    }
    
    /**
     * Initialize the application
     */
    async init() {
        try {
            console.log('🔄 Initializing application components...');
            
            // Initialize performance monitoring
            this.initializePerformanceMonitoring();
            
            // Cache DOM elements
            this.initializeDOMCache();
            
            // Initialize core modules
            await this.initializeModules();
            
            // Setup global event listeners
            this.setupGlobalEventListeners();
            
            // Setup error handling
            this.setupErrorHandling();
            
            // Initialize component visibility
            this.initializeComponentVisibility();
            
            // Finalize initialization
            this.finalizeInitialization();
            
        } catch (error) {
            console.error('❌ Application initialization failed:', error);
            this.handleInitializationError(error);
        }
    }
    
    /**
     * Initialize DOM element caching
     */
    initializeDOMCache() {
        this.cacheMainSections();
        this.cacheFormElements();
        this.cacheProgressElements();
        this.cacheMessageContainers();
    }
    
    /**
     * Finalize initialization process
     */
    finalizeInitialization() {
        // Performance monitoring
        this.performanceMetrics.initEnd = performance.now();
        this.performanceMetrics.loadTime = this.performanceMetrics.initEnd - this.performanceMetrics.initStart;
        
        this.initialized = true;
        
        console.log(`✅ Application initialized in ${Math.round(this.performanceMetrics.loadTime)}ms`);
        
        // Emit initialization complete event
        this.eventBus.emit('app:initialized', {
            version: this.version,
            loadTime: this.performanceMetrics.loadTime
        });
        
        // Test API connectivity
        this.testAPIConnectivity();
    }
    
    /**
     * Cache main application sections
     */
    cacheMainSections() {
        this.elements.uploadArea = document.getElementById('uploadArea');
        this.elements.fileInput = document.getElementById('fileInput');
        this.elements.configSection = document.getElementById('configSection');
        this.elements.progressSection = document.getElementById('progressSection');
        this.elements.resultsSection = document.getElementById('resultsSection');
    }
    
    /**
     * Cache form-related elements
     */
    cacheFormElements() {
        this.elements.processingForm = document.getElementById('processingForm');
        this.elements.processingMode = document.getElementById('processingMode');
        this.elements.analysisCategories = document.getElementById('analysisCategories');
        this.elements.outputFilename = document.getElementById('outputFilename');
        this.elements.startProcessing = document.getElementById('startProcessing');
        this.elements.cancelUpload = document.getElementById('cancelUpload');
    }
    
    /**
     * Cache progress tracking elements
     */
    cacheProgressElements() {
        this.elements.progressFill = document.getElementById('progressFill');
        this.elements.progressText = document.getElementById('progressText');
        this.elements.statusBadge = document.getElementById('statusBadge');
        this.elements.resultsList = document.getElementById('resultsList');
    }
    
    /**
     * Cache message and notification containers
     */
    cacheMessageContainers() {
        this.elements.errorContainer = document.getElementById('errorContainer');
        this.elements.successContainer = document.getElementById('successContainer');
        this.elements.ariaLivePolite = document.getElementById('ariaLivePolite');
        this.elements.ariaLiveAssertive = document.getElementById('ariaLiveAssertive');
        
        console.log('📦 DOM elements cached');
    }
    
    /**
     * Initialize core modules
     */
    async initializeModules() {
        // Initialize theme manager
        this.themeManager = new ThemeManager();
        
        // Initialize upload handler
        this.uploadHandler = new UploadHandler(
            this.elements.uploadArea,
            this.elements.fileInput,
            this.eventBus
        );
        
        // Initialize configuration manager
        this.configManager = new ConfigManager(this.eventBus);
        await this.configManager.init();
        
        // Initialize WebSocket manager
        this.webSocketManager = new WebSocketManager(this.eventBus);
        
        // Initialize progress manager
        this.progressManager = new ProgressManager(this.eventBus);
        this.progressManager.init();
        
        // Initialize results manager
        this.resultsManager = new ResultsManager(this.eventBus);
        this.resultsManager.init();
        
        // Listen for theme changes
        this.themeManager.onThemeChange((event) => {
            this.eventBus.emit('theme:changed', event.detail);
        });
        
        // Listen for upload events
        this.setupUploadEventListeners();
        
        // Listen for configuration events
        this.setupConfigEventListeners();
        
        // Listen for results events
        this.setupResultsEventListeners();
        
        console.log('🧩 Core modules initialized');
    }
    
    /**
     * Setup upload-related event listeners
     */
    setupUploadEventListeners() {
        this.eventBus.on('upload:file-selected', (data) => {
            console.log('📁 File selected:', data.name);
            // Show configuration section when file is selected
            if (this.elements.configSection) {
                this.elements.configSection.classList.add('active');
            }
        });
        
        this.eventBus.on('upload:error', (data) => {
            this.showErrorMessage(data.message);
        });
        
        this.eventBus.on('upload:reset', () => {
            this.resetApplication();
        });
    }
    
    /**
     * Setup configuration-related event listeners
     */
    setupConfigEventListeners() {
        this.eventBus.on('config:initialized', (config) => {
            console.log('⚙️ Configuration initialized:', config);
        });
        
        this.eventBus.on('config:processing-mode-changed', (mode) => {
            console.log('🔄 Processing mode changed:', mode);
        });
        
        this.eventBus.on('config:categories-changed', (categories) => {
            console.log('📝 Analysis categories changed:', categories);
        });
        
        this.eventBus.on('config:estimation-updated', (estimation) => {
            console.log('📊 Cost/time estimation updated:', estimation);
        });
        
        this.eventBus.on('config:saved', (config) => {
            console.log('💾 Configuration saved to localStorage');
        });
    }
    
    /**
     * Setup results-related event listeners
     */
    setupResultsEventListeners() {
        this.eventBus.on('results:retry-processing', (data) => {
            console.log('🔄 Retry processing requested:', data);
            // Reset form and restart processing
            this.resetApplicationForRetry();
        });
        
        this.eventBus.on('results:new-upload-requested', (data) => {
            console.log('📄 New upload requested:', data);
            // Reset entire application
            this.resetApplication();
        });
        
        this.eventBus.on('results:displayed', (data) => {
            console.log('📊 Results displayed:', data);
            // Hide progress section when results are shown
            this.hideProgressSection();
        });
        
        this.eventBus.on('results:download-attempted', (data) => {
            console.log('📥 Download attempted:', data);
        });
        
        this.eventBus.on('results:download-error', (data) => {
            console.error('❌ Download error:', data);
        });
    }
    
    /**
     * Setup global event listeners
     */
    setupGlobalEventListeners() {
        // Note: Upload handling is now managed by UploadHandler class
        
        // Form submission with enhanced configuration
        if (this.elements.processingForm) {
            this.elements.processingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmission();
            });
        }
        
        // Cancel button
        if (this.elements.cancelUpload) {
            this.elements.cancelUpload.addEventListener('click', () => {
                this.resetApplication();
            });
        }
        
        // Window events
        window.addEventListener('beforeunload', (e) => {
            if (this.state.isProcessing) {
                e.preventDefault();
                e.returnValue = 'Eine Verarbeitung läuft noch. Möchten Sie wirklich die Seite verlassen?';
                return e.returnValue;
            }
        });
        
        console.log('👂 Global event listeners setup complete');
    }
    
    /**
     * Setup error handling
     */
    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (e) => {
            console.error('🚨 Global error:', e.error);
            this.handleError(e.error, 'Ein unerwarteter Fehler ist aufgetreten');
        });
        
        // Promise rejection handler
        window.addEventListener('unhandledrejection', (e) => {
            console.error('🚨 Unhandled promise rejection:', e.reason);
            this.handleError(e.reason, 'Ein Fehler bei der Verarbeitung ist aufgetreten');
        });
        
        console.log('🛡️ Error handling setup complete');
    }
    
    /**
     * Initialize component visibility
     */
    initializeComponentVisibility() {
        // Hide all sections except upload
        const sections = [
            this.elements.configSection,
            this.elements.progressSection,
            this.elements.resultsSection
        ];
        
        sections.forEach(section => {
            if (section) {
                section.classList.remove('active');
            }
        });
        
        console.log('👁️ Component visibility initialized');
    }
    
    /**
     * Test API connectivity
     */
    async testAPIConnectivity() {
        try {
            console.log('🔍 Testing API connectivity...');
            
            const response = await fetch('/api/v1/info', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ API Connection successful:', data);
                this.eventBus.emit('api:connected', data);
            } else {
                throw new Error(`API responded with status ${response.status}`);
            }
            
        } catch (error) {
            console.error('❌ API Connection failed:', error);
            this.handleError(error, 'Verbindung zum Server fehlgeschlagen. Bitte versuchen Sie es später erneut.');
            this.eventBus.emit('api:connection-failed', error);
        }
    }
    
    /**
     * Handle application errors
     * @param {Error} error - Error object
     * @param {string} userMessage - User-friendly message
     */
    handleError(error, userMessage) {
        this.state.lastError = error;
        
        // Log detailed error for debugging
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
        
        // Show user-friendly error message
        this.showErrorMessage(userMessage);
        
        // Emit error event
        this.eventBus.emit('app:error', {
            error,
            userMessage,
            timestamp: Date.now()
        });
    }
    
    /**
     * Handle initialization errors
     * @param {Error} error - Initialization error
     */
    handleInitializationError(error) {
        // Show critical error message
        const errorHTML = `
            <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif; color: #721c24; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 8px; margin: 20px;">
                <h2>🚨 Initialisierungsfehler</h2>
                <p>Die Anwendung konnte nicht vollständig geladen werden.</p>
                <p><strong>Fehler:</strong> ${error.message}</p>
                <button onclick="window.location.reload()" style="background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-top: 15px;">
                    🔄 Seite neu laden
                </button>
            </div>
        `;
        
        document.body.innerHTML = errorHTML;
    }
    
    /**
     * Show error message to user
     * @param {string} message - Error message
     */
    showErrorMessage(message) {
        if (this.elements.errorContainer) {
            this.elements.errorContainer.textContent = message;
            this.elements.errorContainer.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                this.elements.errorContainer.style.display = 'none';
            }, 5000);
        }
        
        // Also announce to screen readers
        if (this.elements.ariaLiveAssertive) {
            this.elements.ariaLiveAssertive.textContent = `Fehler: ${message}`;
        }
        
        console.log('📢 Error message shown to user');
    }
    
    /**
     * Show success message to user
     * @param {string} message - Success message
     */
    showSuccessMessage(message) {
        if (this.elements.successContainer) {
            this.elements.successContainer.textContent = message;
            this.elements.successContainer.style.display = 'block';
            
            // Auto-hide after 3 seconds
            setTimeout(() => {
                this.elements.successContainer.style.display = 'none';
            }, 3000);
        }
        
        // Also announce to screen readers
        if (this.elements.ariaLivePolite) {
            this.elements.ariaLivePolite.textContent = message;
        }
        
        console.log('📢 Success message shown to user');
    }
    
    /**
     * Handle form submission with configuration validation
     */
    async handleFormSubmission() {
        try {
            console.log('📝 Processing form submission...');
            
            // Validate configuration
            const validation = this.configManager.validateConfig();
            if (!validation.isValid) {
                this.showErrorMessage(validation.errors.join(', '));
                return;
            }
            
            // Get configuration for processing
            const config = this.configManager.exportForProcessing();
            console.log('⚙️ Configuration for processing:', config);
            
            // Start comprehensive processing with API, WebSocket, and Results integration
            await this.processDocumentWithFullIntegration(config);
            
            // Emit form submission event with configuration
            this.eventBus.emit('form:submitted', {
                config,
                timestamp: Date.now()
            });
            
        } catch (error) {
            console.error('❌ Form submission failed:', error);
            this.handleError(error, 'Fehler beim Verarbeiten der Konfiguration');
        }
    }
    
    /**
     * Start WebSocket progress tracking demonstration
     * This method demonstrates the real-time progress tracking functionality
     * In production, this would be triggered after successful API job creation
     * @param {Object} config - Configuration from config manager
     */
    async startWebSocketProgressDemo(config) {
        try {
            console.log('🚀 Starting WebSocket progress tracking demo...');
            
            // Generate a demo job ID
            const demoJobId = 'demo-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            this.state.currentJobId = demoJobId;
            this.state.isProcessing = true;
            
            // Show progress section
            this.showProgressSection();
            
            // Connect to WebSocket if not already connected
            if (!this.webSocketManager.isConnected()) {
                console.log('🔌 Connecting to WebSocket...');
                await this.webSocketManager.connect();
            }
            
            // Join job room for demo
            await this.webSocketManager.joinJob(demoJobId);
            
            // Start progress tracking
            this.progressManager.startTracking(demoJobId);
            
            // Simulate WebSocket progress events for demonstration
            this.simulateProgressEvents(demoJobId, config);
            
            this.showSuccessMessage('WebSocket Verbindung hergestellt! Fortschritt wird live angezeigt.');
            
        } catch (error) {
            console.error('❌ WebSocket demo failed:', error);
            this.handleError(error, 'WebSocket Verbindung fehlgeschlagen. Fallback zu statischen Updates.');
            
            // Fallback to static progress simulation
            this.simulateStaticProgress(config);
        }
    }
    
    /**
     * Process document with comprehensive API, WebSocket, and Results integration
     * Combines real API processing with WebSocket monitoring and Results display
     * @param {Object} config - Configuration from config manager
     */
    async processDocumentWithFullIntegration(config) {
        try {
            console.log('🚀 Starting comprehensive document processing...');
            
            // 1. Validate prerequisites
            const uploadState = this.uploadHandler.getState();
            if (!uploadState.hasFile) {
                throw new Error('Keine Datei ausgewählt. Bitte laden Sie zuerst eine DOCX-Datei hoch.');
            }
            
            // 2. Set processing state and show progress section
            this.state.isProcessing = true;
            this.showProgressSection();
            
            // 3. Initialize WebSocket connection for real-time progress
            try {
                if (!this.webSocketManager.isConnected()) {
                    console.log('🔌 Connecting to WebSocket...');
                    await this.webSocketManager.connect();
                }
            } catch (wsError) {
                console.warn('⚠️ WebSocket connection failed, will use fallback progress:', wsError);
            }
            
            // 4. Upload file to server using API service
            console.log('📤 Uploading file:', uploadState.fileName);
            const uploadResult = await this.apiService.uploadFile(uploadState.selectedFile);
            this.state.currentFileId = uploadResult.file_id;
            console.log('✅ File uploaded successfully, ID:', this.state.currentFileId);
            
            // 5. Prepare processing request
            const processingRequest = {
                file_id: this.state.currentFileId,
                processing_mode: config.processing_mode,
                categories: config.categories,
                output_filename: config.output_filename
            };
            
            // 6. Submit for AI processing
            console.log('🤖 Submitting for AI processing...');
            const processResult = await this.apiService.processDocument(processingRequest);
            this.state.currentJobId = processResult.job_id;
            console.log('✅ Processing started, Job ID:', this.state.currentJobId);
            
            // 7. Start progress tracking with both managers
            this.progressManager.startTracking(this.state.currentJobId);
            
            // 8. Join WebSocket room if connected, otherwise use fallback
            if (this.webSocketManager.isConnected()) {
                await this.webSocketManager.joinJob(this.state.currentJobId);
                this.showSuccessMessage('Verarbeitung gestartet! Live-Updates über WebSocket aktiv.');
            } else {
                // Fallback to demo simulation for results display
                this.simulateProgressEventsForResults(this.state.currentJobId, config);
                this.showSuccessMessage('Verarbeitung gestartet! Fortschritt wird simuliert.');
            }
            
            // 9. Emit events for other components
            this.eventBus.emit('processing:started', {
                jobId: this.state.currentJobId,
                fileId: this.state.currentFileId,
                config: config
            });
            
        } catch (error) {
            console.error('❌ Document processing failed:', error);
            this.state.isProcessing = false;
            this.handleError(error, 'Fehler beim Starten der Verarbeitung');
        }
    }
    
    /**
     * Simulate WebSocket progress events for Results display demo
     * This shows how real progress events would be handled and integrates with Results
     * @param {string} jobId - Demo job ID
     * @param {Object} config - Processing configuration
     */
    simulateProgressEventsForResults(jobId, config) {
        console.log('📊 Simulating WebSocket progress events for Results display...');
        
        // Simulate job started event
        setTimeout(() => {
            this.eventBus.emit('websocket:job-started', {
                job_id: jobId,
                stages: ['parsing', 'analyzing', 'commenting', 'integrating'],
                estimated_duration: 60, // 60 seconds
                timestamp: new Date().toISOString()
            });
        }, 1000);
        
        // Simulate progress updates
        const progressUpdates = [
            { stage: 'parsing', progress: 10, message: 'Dokument wird analysiert...', delay: 3000 },
            { stage: 'parsing', progress: 25, message: 'Textstruktur wird erfasst...', delay: 6000 },
            { stage: 'analyzing', progress: 40, message: 'KI-Analyse läuft...', delay: 12000 },
            { stage: 'analyzing', progress: 60, message: 'Grammatik wird geprüft...', delay: 18000 },
            { stage: 'commenting', progress: 75, message: 'Verbesserungsvorschläge werden generiert...', delay: 24000 },
            { stage: 'integrating', progress: 90, message: 'Kommentare werden eingefügt...', delay: 30000 },
            { stage: 'integrating', progress: 100, message: 'Verarbeitung abgeschlossen!', delay: 35000 }
        ];
        
        progressUpdates.forEach(update => {
            setTimeout(() => {
                this.eventBus.emit('websocket:progress-update', {
                    job_id: jobId,
                    stage: update.stage,
                    progress: update.progress,
                    message: update.message,
                    estimated_remaining: Math.max(0, 60 - (update.delay / 1000)) + ' Sekunden',
                    timestamp: new Date().toISOString()
                });
            }, update.delay);
        });
        
        // Simulate stage completions
        setTimeout(() => {
            this.eventBus.emit('websocket:stage-completed', {
                job_id: jobId,
                completed_stage: 'parsing',
                next_stage: 'analyzing',
                timestamp: new Date().toISOString()
            });
        }, 8000);
        
        setTimeout(() => {
            this.eventBus.emit('websocket:stage-completed', {
                job_id: jobId,
                completed_stage: 'analyzing',
                next_stage: 'commenting',
                timestamp: new Date().toISOString()
            });
        }, 20000);
        
        setTimeout(() => {
            this.eventBus.emit('websocket:stage-completed', {
                job_id: jobId,
                completed_stage: 'commenting',
                next_stage: 'integrating',
                timestamp: new Date().toISOString()
            });
        }, 26000);
        
        // Simulate job completion with Results integration
        setTimeout(() => {
            this.eventBus.emit('websocket:job-completed', {
                job_id: jobId,
                success: true,
                processing_time: '37 Sekunden',
                duration_seconds: 37,
                timestamp: new Date().toISOString(),
                download_url: '/api/v1/download/' + jobId.replace('demo-', ''),
                result_data: {
                    total_suggestions: 23,
                    categories_processed: config.categories || ['grammar', 'style', 'clarity', 'academic'],
                    file_size_mb: 2.4
                }
            });
        }, 37000);
    }
    
    /**
     * Simulate WebSocket progress events for demonstration
     * This shows how real progress events would be handled
     * @param {string} jobId - Demo job ID
     * @param {Object} config - Processing configuration
     */
    simulateProgressEvents(jobId, config) {
        console.log('📊 Simulating WebSocket progress events...');
        
        // Simulate job started event
        setTimeout(() => {
            this.eventBus.emit('websocket:job-started', {
                job_id: jobId,
                stages: ['parsing', 'analyzing', 'commenting', 'integrating'],
                estimated_duration: 60, // 60 seconds
                timestamp: new Date().toISOString()
            });
        }, 1000);
        
        // Simulate progress updates
        const progressUpdates = [
            { stage: 'parsing', progress: 10, message: 'Dokument wird analysiert...', delay: 3000 },
            { stage: 'parsing', progress: 25, message: 'Textstruktur wird erfasst...', delay: 6000 },
            { stage: 'analyzing', progress: 40, message: 'KI-Analyse läuft...', delay: 12000 },
            { stage: 'analyzing', progress: 60, message: 'Grammatik wird geprüft...', delay: 18000 },
            { stage: 'commenting', progress: 75, message: 'Verbesserungsvorschläge werden generiert...', delay: 24000 },
            { stage: 'integrating', progress: 90, message: 'Kommentare werden eingefügt...', delay: 30000 },
            { stage: 'integrating', progress: 100, message: 'Verarbeitung abgeschlossen!', delay: 35000 }
        ];
        
        progressUpdates.forEach(update => {
            setTimeout(() => {
                this.eventBus.emit('websocket:progress-update', {
                    job_id: jobId,
                    stage: update.stage,
                    progress: update.progress,
                    message: update.message,
                    estimated_remaining: Math.max(0, 60 - (update.delay / 1000)) + ' Sekunden',
                    timestamp: new Date().toISOString()
                });
            }, update.delay);
        });
        
        // Simulate stage completions
        setTimeout(() => {
            this.eventBus.emit('websocket:stage-completed', {
                job_id: jobId,
                completed_stage: 'parsing',
                next_stage: 'analyzing',
                timestamp: new Date().toISOString()
            });
        }, 8000);
        
        setTimeout(() => {
            this.eventBus.emit('websocket:stage-completed', {
                job_id: jobId,
                completed_stage: 'analyzing',
                next_stage: 'commenting',
                timestamp: new Date().toISOString()
            });
        }, 20000);
        
        setTimeout(() => {
            this.eventBus.emit('websocket:stage-completed', {
                job_id: jobId,
                completed_stage: 'commenting',
                next_stage: 'integrating',
                timestamp: new Date().toISOString()
            });
        }, 26000);
        
        // Simulate job completion
        setTimeout(() => {
            this.eventBus.emit('websocket:job-completed', {
                job_id: jobId,
                success: true,
                processing_time: '37 Sekunden',
                duration_seconds: 37,
                timestamp: new Date().toISOString(),
                download_url: '/api/v1/download/' + jobId.replace('demo-', ''),
                result_data: {
                    total_suggestions: 23,
                    categories_processed: config.categories || ['grammar', 'style', 'clarity', 'academic'],
                    file_size_mb: 2.4
                }
            });
        }, 37000);
    }
    
    /**
     * Fallback static progress simulation when WebSocket is unavailable
     * @param {Object} config - Processing configuration
     */
    simulateStaticProgress(config) {
        console.log('📊 Starting static progress fallback...');
        
        // Show progress section
        this.showProgressSection();
        
        // Start basic progress tracking without WebSocket
        const demoJobId = 'static-demo-' + Date.now();
        this.progressManager.startTracking(demoJobId);
        
        // Simple progress simulation
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            progress = Math.min(100, progress);
            
            let message = 'Verarbeitung läuft...';
            if (progress < 25) message = 'Dokument wird analysiert...';
            else if (progress < 50) message = 'KI-Analyse läuft...';
            else if (progress < 75) message = 'Kommentare werden generiert...';
            else if (progress < 100) message = 'Integration läuft...';
            else message = 'Verarbeitung abgeschlossen!';
            
            this.progressManager.updateProgress(progress, message);
            
            if (progress >= 100) {
                clearInterval(interval);
                this.progressManager.updateStatus('Demo abgeschlossen', 'completed');
                this.showSuccessMessage('Statische Progress-Demo abgeschlossen!');
                this.state.isProcessing = false;
                
                // Emit completion event to trigger ResultsManager
                this.eventBus.emit('progress:completed', {
                    jobId: demoJobId,
                    processingTime: '58 Sekunden',
                    success: true,
                    resultData: {
                        total_suggestions: 23,
                        categories_processed: ['grammar', 'style', 'clarity', 'academic'],
                        file_size_mb: 2.4,
                        download_url: '/api/v1/download/demo-file'
                    }
                });
            }
        }, 2000);
    }
    
    /**
     * Show progress section and hide configuration section
     */
    showProgressSection() {
        // Hide configuration section
        if (this.elements.configSection) {
            this.elements.configSection.classList.remove('active');
        }
        
        // Show progress section
        if (this.elements.progressSection) {
            this.elements.progressSection.classList.add('active');
        }
        
        console.log('📊 Progress section shown');
    }
    
    /**
     * Hide progress section when results are displayed
     */
    hideProgressSection() {
        if (this.elements.progressSection) {
            this.elements.progressSection.classList.remove('active');
            console.log('📊 Progress section hidden');
        }
    }
    
    /**
     * Reset application for retry processing (keeps file uploaded)
     */
    resetApplicationForRetry() {
        console.log('🔄 Resetting application for retry...');
        
        // Stop progress tracking
        if (this.progressManager && this.progressManager.isTracking) {
            this.progressManager.stopTracking();
            this.progressManager.resetProgress();
        }
        
        // Clear results but keep file uploaded
        if (this.resultsManager) {
            this.resultsManager.clearResults();
        }
        
        // Reset processing state but keep file
        this.state.currentJobId = null;
        this.state.isProcessing = false;
        this.state.lastError = null;
        
        // Show configuration section for retry
        if (this.elements.configSection) {
            this.elements.configSection.classList.add('active');
        }
        
        // Clear messages
        if (this.elements.errorContainer) {
            this.elements.errorContainer.style.display = 'none';
        }
        if (this.elements.successContainer) {
            this.elements.successContainer.style.display = 'none';
        }
        
        console.log('✅ Application reset for retry complete');
    }
    
    /**
     * Reset application to initial state
     */
    resetApplication() {
        console.log('🔄 Resetting application...');
        
        // Stop WebSocket tracking and disconnect if connected
        if (this.webSocketManager && this.webSocketManager.isConnected()) {
            if (this.state.currentJobId) {
                this.webSocketManager.leaveJob(this.state.currentJobId);
            }
            // Note: We don't disconnect WebSocket completely to allow reconnection
        }
        
        // Stop progress tracking
        if (this.progressManager && this.progressManager.isTracking) {
            this.progressManager.stopTracking();
            this.progressManager.resetProgress();
        }
        
        // Clear results
        if (this.resultsManager) {
            this.resultsManager.clearResults();
        }
        
        // Reset state
        this.state.currentFileId = null;
        this.state.currentJobId = null;
        this.state.isProcessing = false;
        this.state.lastError = null;
        
        // Reset form
        if (this.elements.processingForm) {
            this.elements.processingForm.reset();
        }
        
        // Reset upload handler
        if (this.uploadHandler) {
            this.uploadHandler.reset();
        }
        
        // Reset configuration (but keep saved preferences)
        if (this.configManager) {
            this.configManager.applyConfigToForm();
            this.configManager.updateEstimations();
        }
        
        // Hide sections
        this.initializeComponentVisibility();
        
        // Clear messages
        if (this.elements.errorContainer) {
            this.elements.errorContainer.style.display = 'none';
        }
        if (this.elements.successContainer) {
            this.elements.successContainer.style.display = 'none';
        }
        
        // Emit reset event
        this.eventBus.emit('app:reset');
        
        console.log('✅ Application reset complete');
    }
    
    /**
     * Get application state
     * @returns {Object} Current application state
     */
    getState() {
        return {
            ...this.state,
            initialized: this.initialized,
            theme: this.themeManager ? this.themeManager.getThemeInfo() : null,
            version: this.version,
            performanceMetrics: this.performanceMetrics
        };
    }
    
    /**
     * Destroy the application (cleanup)
     */
    destroy() {
        console.log('🧹 Destroying application...');
        
        // Destroy modules
        if (this.themeManager) {
            this.themeManager.destroy();
        }
        
        if (this.uploadHandler) {
            this.uploadHandler.destroy();
        }
        
        if (this.configManager) {
            this.configManager.destroy();
        }
        
        if (this.resultsManager) {
            this.resultsManager.destroy();
        }
        
        if (this.eventBus) {
            this.eventBus.destroy();
        }
        
        // Clear cached elements
        this.elements = {};
        
        console.log('💀 Application destroyed');
    }
}

// Initialize application when this module loads
const app = new KorrekturtoolApp();

// Make app available globally for debugging
if (typeof window !== 'undefined') {
    window.KorrekturtoolApp = app;
}

// Export for potential module use
export default app;