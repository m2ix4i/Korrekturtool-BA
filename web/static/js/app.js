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
        
        // Listen for theme changes
        this.themeManager.onThemeChange((event) => {
            this.eventBus.emit('theme:changed', event.detail);
        });
        
        // Listen for upload events
        this.setupUploadEventListeners();
        
        // Listen for configuration events
        this.setupConfigEventListeners();
        
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
            
            // TODO: Implement actual processing logic
            this.showSuccessMessage('Konfiguration validiert! Verarbeitung würde hier starten...');
            
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
     * Reset application to initial state
     */
    resetApplication() {
        console.log('🔄 Resetting application...');
        
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