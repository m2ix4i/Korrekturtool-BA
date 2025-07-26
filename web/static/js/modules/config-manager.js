/**
 * Configuration Manager Module - Issue #8 Implementation
 * Korrekturtool für Wissenschaftliche Arbeiten
 * Manages user preferences, real-time estimation, tooltips, and advanced options
 */

import { EventBus } from '../utils/event-bus.js';

/**
 * Configuration constants to eliminate magic numbers
 */
const ESTIMATION_CONSTANTS = {
    // Base cost ranges (in USD)
    BASE_COSTS: {
        complete: { min: 0.25, max: 0.75 },
        performance: { min: 0.15, max: 0.45 }
    },
    
    // Base time ranges (in seconds)
    BASE_TIMES: {
        complete: { min: 45, max: 120 },
        performance: { min: 20, max: 60 }
    },
    
    // Category complexity multipliers
    CATEGORY_MULTIPLIERS: {
        grammar: 1.0,
        style: 1.2,
        clarity: 1.1,
        academic: 1.3
    },
    
    // Priority and density modifiers
    PRIORITY_MULTIPLIERS: {
        normal: 1.0,
        high: 1.3
    },
    
    DENSITY_MULTIPLIERS: {
        low: 0.7,
        medium: 1.0,
        high: 1.4
    }
};

/**
 * Configuration Manager Class
 * Handles all configuration-related functionality including localStorage persistence,
 * real-time cost/time estimation, tooltips, and advanced options management
 */
export class ConfigManager {
    constructor(eventBus) {
        this.eventBus = eventBus || new EventBus();
        this.initialized = false;
        
        // Configuration state
        this.config = {
            processingMode: 'complete',
            analysisCategories: {
                grammar: true,
                style: true,
                clarity: true,
                academic: true
            },
            outputFilename: '',
            advancedOptions: {
                processingPriority: 'normal',
                commentDensity: 'medium'
            }
        };
        
        // Use extracted constants for estimation data
        this.estimationData = {
            baseCosts: ESTIMATION_CONSTANTS.BASE_COSTS,
            baseTimes: ESTIMATION_CONSTANTS.BASE_TIMES,
            categoryMultipliers: ESTIMATION_CONSTANTS.CATEGORY_MULTIPLIERS
        };
        
        // DOM elements cache
        this.elements = {};
        
        console.log('🔧 ConfigManager initializing...');
    }
    
    /**
     * Initialize the configuration manager
     */
    async init() {
        try {
            console.log('🔄 ConfigManager: Caching DOM elements...');
            this.cacheDOMElements();
            
            console.log('🔄 ConfigManager: Loading saved preferences...');
            this.loadSavedPreferences();
            
            console.log('🔄 ConfigManager: Setting up event listeners...');
            this.setupEventListeners();
            
            console.log('🔄 ConfigManager: Initializing tooltips...');
            this.initializeTooltips();
            
            console.log('🔄 ConfigManager: Setting up advanced options...');
            this.setupAdvancedOptions();
            
            console.log('🔄 ConfigManager: Updating initial estimations...');
            this.updateEstimations();
            
            this.initialized = true;
            console.log('✅ ConfigManager initialized successfully');
            
            // Emit initialization event
            this.eventBus.emit('config:initialized', this.config);
            
        } catch (error) {
            console.error('❌ ConfigManager initialization failed:', error);
            throw error;
        }
    }
    
    /**
     * Cache DOM elements for performance
     */
    cacheDOMElements() {
        // Processing mode radio buttons
        this.elements.modeComplete = document.getElementById('modeComplete');
        this.elements.modePerformance = document.getElementById('modePerformance');
        
        // Analysis category checkboxes
        this.elements.categoryGrammar = document.getElementById('categoryGrammar');
        this.elements.categoryStyle = document.getElementById('categoryStyle');
        this.elements.categoryClarity = document.getElementById('categoryClarity');
        this.elements.categoryAcademic = document.getElementById('categoryAcademic');
        
        // Output filename
        this.elements.outputFilename = document.getElementById('outputFilename');
        
        // Advanced options
        this.elements.advancedToggle = document.getElementById('advancedToggle');
        this.elements.advancedOptions = document.getElementById('advancedOptions');
        this.elements.processingPriority = document.getElementById('processingPriority');
        this.elements.commentDensity = document.getElementById('commentDensity');
        
        // Estimation displays
        this.elements.costEstimate = document.getElementById('costEstimate');
        this.elements.timeEstimate = document.getElementById('timeEstimate');
        
        // Tooltip triggers
        this.elements.tooltipTriggers = document.querySelectorAll('.tooltip-trigger');
        
        console.log('📦 ConfigManager: DOM elements cached');
    }
    
    /**
     * Load saved preferences from localStorage
     */
    loadSavedPreferences() {
        try {
            const savedConfig = localStorage.getItem('korrekturtool_config');
            if (savedConfig) {
                const parsed = JSON.parse(savedConfig);
                this.config = { ...this.config, ...parsed };
                this.applyConfigToForm();
                console.log('📥 Saved preferences loaded');
            } else {
                console.log('💾 No saved preferences found, using defaults');
            }
        } catch (error) {
            console.warn('⚠️ Failed to load saved preferences:', error);
        }
    }
    
    /**
     * Save current preferences to localStorage
     */
    savePreferences() {
        try {
            localStorage.setItem('korrekturtool_config', JSON.stringify(this.config));
            console.log('💾 Preferences saved');
            this.eventBus.emit('config:saved', this.config);
        } catch (error) {
            console.error('❌ Failed to save preferences:', error);
        }
    }
    
    /**
     * Apply configuration to form elements
     */
    applyConfigToForm() {
        // Set processing mode
        if (this.config.processingMode === 'complete') {
            this.elements.modeComplete.checked = true;
        } else {
            this.elements.modePerformance.checked = true;
        }
        
        // Set analysis categories
        this.elements.categoryGrammar.checked = this.config.analysisCategories.grammar;
        this.elements.categoryStyle.checked = this.config.analysisCategories.style;
        this.elements.categoryClarity.checked = this.config.analysisCategories.clarity;
        this.elements.categoryAcademic.checked = this.config.analysisCategories.academic;
        
        // Set output filename
        this.elements.outputFilename.value = this.config.outputFilename || '';
        
        // Set advanced options
        this.elements.processingPriority.value = this.config.advancedOptions.processingPriority;
        this.elements.commentDensity.value = this.config.advancedOptions.commentDensity;
        
        console.log('📝 Configuration applied to form');
    }
    
    /**
     * Setup event listeners for form elements
     */
    setupEventListeners() {
        // Processing mode change
        [this.elements.modeComplete, this.elements.modePerformance].forEach(radio => {
            radio.addEventListener('change', () => this.handleProcessingModeChange());
        });
        
        // Analysis category changes
        [
            this.elements.categoryGrammar,
            this.elements.categoryStyle,
            this.elements.categoryClarity,
            this.elements.categoryAcademic
        ].forEach(checkbox => {
            checkbox.addEventListener('change', () => this.handleCategoryChange());
        });
        
        // Output filename change
        this.elements.outputFilename.addEventListener('input', () => this.handleOutputFilenameChange());
        
        // Advanced options changes
        this.elements.processingPriority.addEventListener('change', () => this.handleAdvancedOptionChange());
        this.elements.commentDensity.addEventListener('change', () => this.handleAdvancedOptionChange());
        
        console.log('👂 Event listeners setup complete');
    }
    
    /**
     * Handle processing mode change
     */
    handleProcessingModeChange() {
        this.config.processingMode = this.elements.modeComplete.checked ? 'complete' : 'performance';
        this.updateEstimations();
        this.savePreferences();
        this.eventBus.emit('config:processing-mode-changed', this.config.processingMode);
        console.log(`🔄 Processing mode changed to: ${this.config.processingMode}`);
    }
    
    /**
     * Handle analysis category change
     */
    handleCategoryChange() {
        this.config.analysisCategories = {
            grammar: this.elements.categoryGrammar.checked,
            style: this.elements.categoryStyle.checked,
            clarity: this.elements.categoryClarity.checked,
            academic: this.elements.categoryAcademic.checked
        };
        
        this.updateEstimations();
        this.savePreferences();
        this.eventBus.emit('config:categories-changed', this.config.analysisCategories);
        
        const selectedCount = Object.values(this.config.analysisCategories).filter(Boolean).length;
        console.log(`🔄 Analysis categories changed: ${selectedCount} selected`);
    }
    
    /**
     * Handle output filename change
     */
    handleOutputFilenameChange() {
        this.config.outputFilename = this.elements.outputFilename.value.trim();
        this.savePreferences();
        this.eventBus.emit('config:filename-changed', this.config.outputFilename);
    }
    
    /**
     * Handle advanced option changes
     */
    handleAdvancedOptionChange() {
        this.config.advancedOptions = {
            processingPriority: this.elements.processingPriority.value,
            commentDensity: this.elements.commentDensity.value
        };
        
        this.updateEstimations();
        this.savePreferences();
        this.eventBus.emit('config:advanced-options-changed', this.config.advancedOptions);
        console.log('🔄 Advanced options updated');
    }
    
    /**
     * Update cost and time estimations
     */
    updateEstimations() {
        const estimationResults = this.calculateEstimations();
        this.updateEstimationDisplay(estimationResults);
        this.emitEstimationUpdate(estimationResults);
        
        console.log(`📊 Estimations updated: $${estimationResults.cost.min.toFixed(2)}-$${estimationResults.cost.max.toFixed(2)}, ${estimationResults.time.min}-${estimationResults.time.max}s`);
    }
    
    /**
     * Calculate cost and time estimations based on current configuration
     * @returns {Object} Estimation results with cost and time ranges
     */
    calculateEstimations() {
        const baseCost = this.calculateBaseCost();
        const baseTime = this.calculateBaseTime();
        const categoryMultiplier = this.calculateCategoryMultiplier();
        const modifiers = this.calculateModifiers();
        
        return {
            cost: {
                min: baseCost.min * categoryMultiplier * modifiers.density,
                max: baseCost.max * categoryMultiplier * modifiers.density
            },
            time: {
                min: Math.round(baseTime.min * categoryMultiplier / modifiers.priority),
                max: Math.round(baseTime.max * categoryMultiplier / modifiers.priority)
            }
        };
    }
    
    /**
     * Get base cost range for current processing mode
     * @returns {Object} Base cost range {min, max}
     */
    calculateBaseCost() {
        return this.estimationData.baseCosts[this.config.processingMode];
    }
    
    /**
     * Get base time range for current processing mode
     * @returns {Object} Base time range {min, max}
     */
    calculateBaseTime() {
        return this.estimationData.baseTimes[this.config.processingMode];
    }
    
    /**
     * Calculate category complexity multiplier based on selected categories
     * @returns {number} Combined category multiplier
     */
    calculateCategoryMultiplier() {
        const selectedCategories = Object.entries(this.config.analysisCategories)
            .filter(([_, selected]) => selected)
            .map(([category, _]) => category);
        
        if (selectedCategories.length === 0) return 1.0;
        
        const totalMultiplier = selectedCategories.reduce((total, category) => {
            return total + (this.estimationData.categoryMultipliers[category] || 1.0);
        }, 0);
        
        return totalMultiplier / selectedCategories.length;
    }
    
    /**
     * Calculate priority and density modifiers
     * @returns {Object} Modifiers {priority, density}
     */
    calculateModifiers() {
        const priority = this.config.advancedOptions.processingPriority;
        const density = this.config.advancedOptions.commentDensity;
        
        return {
            priority: ESTIMATION_CONSTANTS.PRIORITY_MULTIPLIERS[priority] || 1.0,
            density: ESTIMATION_CONSTANTS.DENSITY_MULTIPLIERS[density] || 1.0
        };
    }
    
    /**
     * Update the estimation display elements
     * @param {Object} estimationResults - Calculated estimation results
     */
    updateEstimationDisplay(estimationResults) {
        const { cost, time } = estimationResults;
        
        this.elements.costEstimate.textContent = `$${cost.min.toFixed(2)} - $${cost.max.toFixed(2)}`;
        this.elements.timeEstimate.textContent = `${time.min} - ${time.max} Sekunden`;
    }
    
    /**
     * Emit estimation update event
     * @param {Object} estimationResults - Calculated estimation results
     */
    emitEstimationUpdate(estimationResults) {
        this.eventBus.emit('config:estimation-updated', estimationResults);
    }
    
    /**
     * Setup advanced options toggle functionality
     */
    setupAdvancedOptions() {
        this.elements.advancedToggle.addEventListener('click', () => {
            const isExpanded = this.elements.advancedToggle.getAttribute('aria-expanded') === 'true';
            const newState = !isExpanded;
            
            // Update ARIA attributes
            this.elements.advancedToggle.setAttribute('aria-expanded', newState);
            this.elements.advancedOptions.setAttribute('aria-hidden', !newState);
            
            // Save expanded state
            this.config.advancedOptionsExpanded = newState;
            this.savePreferences();
            
            console.log(`🔧 Advanced options ${newState ? 'expanded' : 'collapsed'}`);
        });
        
        // Restore expanded state if saved
        if (this.config.advancedOptionsExpanded) {
            this.elements.advancedToggle.setAttribute('aria-expanded', 'true');
            this.elements.advancedOptions.setAttribute('aria-hidden', 'false');
        }
    }
    
    /**
     * Initialize tooltip system
     */
    initializeTooltips() {
        this.elements.tooltipTriggers.forEach(trigger => {
            trigger.addEventListener('mouseenter', (e) => {
                console.log(`💡 Tooltip shown: ${e.target.dataset.tooltip}`);
            });
        });
        
        console.log(`💡 ${this.elements.tooltipTriggers.length} tooltips initialized`);
    }
    
    /**
     * Get current configuration
     * @returns {Object} Current configuration object
     */
    getConfig() {
        return { ...this.config };
    }
    
    /**
     * Validate current configuration
     * @returns {Object} Validation result with isValid and errors
     */
    validateConfig() {
        const errors = [];
        
        // Check if at least one category is selected
        const selectedCategories = Object.values(this.config.analysisCategories).filter(Boolean);
        if (selectedCategories.length === 0) {
            errors.push('Mindestens eine Analysekategorie muss ausgewählt sein');
        }
        
        // Validate output filename if provided
        if (this.config.outputFilename) {
            const filename = this.config.outputFilename.trim();
            if (!/^[^<>:"/\\|?*]+\.docx?$/i.test(filename)) {
                errors.push('Ungültiger Dateiname. Verwenden Sie nur gültige Zeichen und die Endung .docx');
            }
        }
        
        const isValid = errors.length === 0;
        
        if (!isValid) {
            console.warn('⚠️ Configuration validation failed:', errors);
        }
        
        return { isValid, errors };
    }
    
    /**
     * Reset configuration to defaults
     */
    resetToDefaults() {
        this.config = {
            processingMode: 'complete',
            analysisCategories: {
                grammar: true,
                style: true,
                clarity: true,
                academic: true
            },
            outputFilename: '',
            advancedOptions: {
                processingPriority: 'normal',
                commentDensity: 'medium'
            },
            advancedOptionsExpanded: false
        };
        
        this.applyConfigToForm();
        this.updateEstimations();
        this.savePreferences();
        
        console.log('🔄 Configuration reset to defaults');
        this.eventBus.emit('config:reset', this.config);
    }
    
    /**
     * Export configuration for processing
     * @returns {Object} Configuration object formatted for backend
     */
    exportForProcessing() {
        const selectedCategories = Object.entries(this.config.analysisCategories)
            .filter(([_, selected]) => selected)
            .map(([category, _]) => category);
        
        return {
            processing_mode: this.config.processingMode,
            categories: selectedCategories,
            output_filename: this.config.outputFilename || null,
            processing_priority: this.config.advancedOptions.processingPriority,
            comment_density: this.config.advancedOptions.commentDensity
        };
    }
    
    /**
     * Destroy the configuration manager
     */
    destroy() {
        console.log('🧹 Destroying ConfigManager...');
        
        // Save final state
        this.savePreferences();
        
        // Clear cached elements
        this.elements = {};
        
        // Emit destruction event
        this.eventBus.emit('config:destroyed');
        
        console.log('💀 ConfigManager destroyed');
    }
}

export default ConfigManager;