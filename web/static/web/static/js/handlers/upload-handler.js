/**
 * Upload Handler Class
 * Manages file upload behavior and state following Tell, Don't Ask principle
 * Encapsulates upload area interactions and file handling logic
 */

import { DOMUtils } from '../utils/dom-utils.js';

export class UploadHandler {
    constructor(uploadArea, fileInput, eventBus) {
        this.uploadArea = uploadArea;
        this.fileInput = fileInput;
        this.eventBus = eventBus;
        
        this.state = {
            isDragover: false,
            isProcessing: false,
            selectedFile: null
        };
        
        this.init();
    }
    
    /**
     * Initialize upload handler
     */
    init() {
        if (!this.uploadArea || !this.fileInput) {
            console.warn('Upload components not found, skipping upload handler initialization');
            return;
        }
        
        this.setupEventListeners();
        this.updateDisplay();
        
        console.log('📁 Upload Handler initialized');
    }
    
    /**
     * Setup all upload-related event listeners
     */
    setupEventListeners() {
        // Click to select file
        DOMUtils.on(this.uploadArea, 'click', () => this.triggerFileSelection());
        
        // Keyboard accessibility
        DOMUtils.on(this.uploadArea, 'keydown', (e) => this.handleKeyboard(e));
        
        // Drag and drop events
        DOMUtils.on(this.uploadArea, 'dragover', (e) => this.handleDragOver(e));
        DOMUtils.on(this.uploadArea, 'dragleave', (e) => this.handleDragLeave(e));
        DOMUtils.on(this.uploadArea, 'drop', (e) => this.handleDrop(e));
        
        // File input change
        DOMUtils.on(this.fileInput, 'change', (e) => this.handleFileSelection(e));
    }
    
    /**
     * Trigger file selection dialog
     */
    triggerFileSelection() {
        if (this.state.isProcessing) return;
        
        this.fileInput.click();
        this.eventBus.emit('upload:selection-triggered');
    }
    
    /**
     * Handle keyboard interactions
     */
    handleKeyboard(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.triggerFileSelection();
        }
    }
    
    /**
     * Handle drag over event
     */
    handleDragOver(e) {
        e.preventDefault();
        
        if (!this.state.isDragover) {
            this.setDragoverState(true);
        }
    }
    
    /**
     * Handle drag leave event
     */
    handleDragLeave(e) {
        e.preventDefault();
        
        // Only remove dragover if leaving the upload area entirely
        if (!this.uploadArea.contains(e.relatedTarget)) {
            this.setDragoverState(false);
        }
    }
    
    /**
     * Handle file drop event
     */
    handleDrop(e) {
        e.preventDefault();
        this.setDragoverState(false);
        
        if (this.state.isProcessing) return;
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.selectFile(files[0]);
        }
    }
    
    /**
     * Handle file input change
     */
    handleFileSelection(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.selectFile(files[0]);
        }
    }
    
    /**
     * Select and validate file
     */
    selectFile(file) {
        // Validate file type
        if (!this.validateFileType(file)) {
            this.showError('Nur DOCX-Dateien werden unterstützt');
            return;
        }
        
        // Validate file size (50MB limit)
        if (!this.validateFileSize(file)) {
            this.showError('Datei ist zu groß. Maximum: 50 MB');
            return;
        }
        
        this.state.selectedFile = file;
        this.updateDisplayForSelectedFile(file);
        
        // Emit file selected event
        this.eventBus.emit('upload:file-selected', {
            file: file,
            name: file.name,
            size: file.size,
            type: file.type
        });
    }
    
    /**
     * Validate file type (DOCX only)
     */
    validateFileType(file) {
        const allowedTypes = [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ];
        const allowedExtensions = ['.docx'];
        
        return allowedTypes.includes(file.type) || 
               allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    }
    
    /**
     * Validate file size (50MB limit)
     */
    validateFileSize(file) {
        const maxSize = 50 * 1024 * 1024; // 50MB in bytes
        return file.size <= maxSize;
    }
    
    /**
     * Set dragover state and update display
     */
    setDragoverState(isDragover) {
        this.state.isDragover = isDragover;
        
        if (isDragover) {
            DOMUtils.addClass(this.uploadArea, 'dragover');
        } else {
            DOMUtils.removeClass(this.uploadArea, 'dragover');
        }
    }
    
    /**
     * Set processing state
     */
    setProcessingState(isProcessing) {
        this.state.isProcessing = isProcessing;
        this.updateDisplay();
        
        if (isProcessing) {
            DOMUtils.addClass(this.uploadArea, 'disabled');
            DOMUtils.attr(this.uploadArea, 'aria-busy', 'true');
        } else {
            DOMUtils.removeClass(this.uploadArea, 'disabled');
            DOMUtils.removeAttr(this.uploadArea, 'aria-busy');
        }
    }
    
    /**
     * Update display for current state
     */
    updateDisplay() {
        const uploadText = this.uploadArea.querySelector('.upload-text');
        const uploadSubtext = this.uploadArea.querySelector('.upload-subtext');
        
        if (!uploadText || !uploadSubtext) return;
        
        if (this.state.isProcessing) {
            uploadText.textContent = 'Verarbeitung läuft...';
            uploadSubtext.textContent = 'Bitte warten Sie, bis die Verarbeitung abgeschlossen ist';
        } else if (this.state.selectedFile) {
            uploadText.textContent = `Datei ausgewählt: ${this.state.selectedFile.name}`;
            uploadSubtext.textContent = 'Klicken Sie auf "Verarbeitung starten" oder wählen Sie eine andere Datei';
        } else {
            uploadText.textContent = 'DOCX-Datei hier ablegen oder klicken zum Auswählen';
            uploadSubtext.textContent = 'Unterstützt werden Word-Dokumente bis 50 MB';
        }
    }
    
    /**
     * Update display when file is selected
     */
    updateDisplayForSelectedFile(file) {
        const fileSize = this.formatFileSize(file.size);
        const uploadText = this.uploadArea.querySelector('.upload-text');
        const uploadSubtext = this.uploadArea.querySelector('.upload-subtext');
        
        if (uploadText && uploadSubtext) {
            uploadText.textContent = `📄 ${file.name}`;
            uploadSubtext.textContent = `Dateigröße: ${fileSize} • Bereit zur Verarbeitung`;
        }
        
        // Add selected state styling
        DOMUtils.addClass(this.uploadArea, 'file-selected');
    }
    
    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }
    
    /**
     * Show error message
     */
    showError(message) {
        this.eventBus.emit('upload:error', { message });
        
        // Visual feedback
        DOMUtils.addClass(this.uploadArea, 'error');
        setTimeout(() => {
            DOMUtils.removeClass(this.uploadArea, 'error');
        }, 3000);
    }
    
    /**
     * Reset upload handler to initial state
     */
    reset() {
        this.state = {
            isDragover: false,
            isProcessing: false,
            selectedFile: null
        };
        
        // Clear file input
        if (this.fileInput) {
            this.fileInput.value = '';
        }
        
        // Reset visual state
        DOMUtils.removeClass(this.uploadArea, 'dragover', 'disabled', 'file-selected', 'error');
        DOMUtils.removeAttr(this.uploadArea, 'aria-busy');
        
        this.updateDisplay();
        
        this.eventBus.emit('upload:reset');
    }
    
    /**
     * Get current upload state
     */
    getState() {
        return {
            ...this.state,
            hasFile: !!this.state.selectedFile,
            fileName: this.state.selectedFile?.name || null,
            fileSize: this.state.selectedFile?.size || null
        };
    }
    
    /**
     * Destroy upload handler (cleanup)
     */
    destroy() {
        // Event listeners are automatically cleaned up when elements are removed
        this.uploadArea = null;
        this.fileInput = null;
        this.eventBus = null;
        this.state = null;
        
        console.log('📁 Upload Handler destroyed');
    }
}