/**
 * Accessibility Utilities
 * WCAG 2.1 AA compliance helpers and accessibility features
 * Provides screen reader support, keyboard navigation, and ARIA management
 */

import { DOMUtils } from './dom-utils.js';

/**
 * Accessibility manager class
 */
export class AccessibilityManager {
    constructor() {
        this.liveRegions = {};
        this.keyboardTrapStack = [];
        this.focusableElements = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]'
        ].join(', ');
        
        this.init();
    }
    
    /**
     * Initialize accessibility features
     */
    init() {
        this.setupLiveRegions();
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        
        console.log('♿ Accessibility Manager initialized');
    }
    
    /**
     * Setup ARIA live regions
     */
    setupLiveRegions() {
        this.liveRegions = {
            polite: DOMUtils.getElementById('ariaLivePolite'),
            assertive: DOMUtils.getElementById('ariaLiveAssertive')
        };
        
        // Create live regions if they don't exist
        if (!this.liveRegions.polite) {
            this.liveRegions.polite = this.createLiveRegion('polite');
        }
        
        if (!this.liveRegions.assertive) {
            this.liveRegions.assertive = this.createLiveRegion('assertive');
        }
    }
    
    /**
     * Create ARIA live region
     * @param {string} politeness - Live region politeness level
     * @returns {HTMLElement} Created live region
     */
    createLiveRegion(politeness) {
        const liveRegion = DOMUtils.createElement('div', {
            'aria-live': politeness,
            'aria-atomic': 'true',
            'className': 'visually-hidden',
            'id': `ariaLive${politeness.charAt(0).toUpperCase() + politeness.slice(1)}`
        });
        
        document.body.appendChild(liveRegion);
        return liveRegion;
    }
    
    /**
     * Announce message to screen readers
     * @param {string} message - Message to announce
     * @param {string} priority - Priority level ('polite' or 'assertive')
     */
    announce(message, priority = 'polite') {
        const liveRegion = this.liveRegions[priority];
        if (liveRegion) {
            // Clear previous message
            liveRegion.textContent = '';
            
            // Set new message with slight delay to ensure screen readers pick it up
            setTimeout(() => {
                liveRegion.textContent = message;
            }, 50);
            
            // Clear message after reasonable time
            setTimeout(() => {
                liveRegion.textContent = '';
            }, priority === 'assertive' ? 3000 : 2000);
        }
    }
    
    /**
     * Setup keyboard navigation
     */
    setupKeyboardNavigation() {
        // Skip link functionality
        const skipLink = DOMUtils.querySelector('.skip-link');
        if (skipLink) {
            DOMUtils.on(skipLink, 'click', (e) => {
                e.preventDefault();
                const target = DOMUtils.querySelector(skipLink.getAttribute('href'));
                if (target) {
                    this.setFocus(target);
                    DOMUtils.scrollIntoView(target);
                }
            });
        }
        
        // Escape key handling for modal-like components
        DOMUtils.on(document, 'keydown', (e) => {
            if (e.key === 'Escape') {
                this.handleEscapeKey(e);
            }
        });
        
        // Tab trapping for modal components
        DOMUtils.on(document, 'keydown', (e) => {
            if (e.key === 'Tab') {
                this.handleTabKey(e);
            }
        });
    }
    
    /**
     * Setup focus management
     */
    setupFocusManagement() {
        // Track focus for keyboard users
        let usingKeyboard = false;
        
        DOMUtils.on(document, 'keydown', (e) => {
            if (e.key === 'Tab') {
                usingKeyboard = true;
                document.body.classList.add('using-keyboard');
                document.body.classList.remove('using-mouse');
            }
        });
        
        DOMUtils.on(document, 'mousedown', () => {
            usingKeyboard = false;
            document.body.classList.add('using-mouse');
            document.body.classList.remove('using-keyboard');
        });
        
        // Focus visible indicator management
        DOMUtils.on(document, 'focusin', (e) => {
            if (usingKeyboard) {
                e.target.classList.add('keyboard-focused');
            }
        });
        
        DOMUtils.on(document, 'focusout', (e) => {
            e.target.classList.remove('keyboard-focused');
        });
    }
    
    /**
     * Handle Escape key press
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleEscapeKey(e) {
        // Close modal-like components
        const activeModal = DOMUtils.querySelector('[role="dialog"][aria-hidden="false"]');
        if (activeModal) {
            this.closeModal(activeModal);
            return;
        }
        
        // Clear error messages
        const errorContainer = DOMUtils.getElementById('errorContainer');
        if (errorContainer && DOMUtils.isVisible(errorContainer)) {
            DOMUtils.hide(errorContainer);
            this.announce('Fehlermeldung geschlossen');
            return;
        }
        
        // Other escape key handling can be added here
    }
    
    /**
     * Handle Tab key press for focus trapping
     * @param {KeyboardEvent} e - Keyboard event
     */
    handleTabKey(e) {
        if (this.keyboardTrapStack.length === 0) return;
        
        const currentTrap = this.keyboardTrapStack[this.keyboardTrapStack.length - 1];
        const focusableElements = this.getFocusableElements(currentTrap);
        
        if (focusableElements.length === 0) return;
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey) {
            // Shift + Tab
            if (document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            // Tab
            if (document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    }
    
    /**
     * Set focus to element with optional announcement
     * @param {HTMLElement} element - Element to focus
     * @param {string} announcement - Optional announcement
     */
    setFocus(element, announcement = null) {
        if (!element) return;
        
        // Ensure element is focusable
        if (element.tabIndex < 0) {
            element.tabIndex = -1;
        }
        
        element.focus();
        
        if (announcement) {
            this.announce(announcement);
        }
    }
    
    /**
     * Get all focusable elements within a container
     * @param {HTMLElement} container - Container element
     * @returns {Array} Array of focusable elements
     */
    getFocusableElements(container = document) {
        const elements = DOMUtils.querySelectorAll(this.focusableElements, container);
        return Array.from(elements).filter(element => {
            return this.isElementVisible(element) && !element.disabled;
        });
    }
    
    /**
     * Check if element is visible (for focus management)
     * @param {HTMLElement} element - Element to check
     * @returns {boolean} True if element is visible
     */
    isElementVisible(element) {
        if (!element) return false;
        
        const style = window.getComputedStyle(element);
        return style.display !== 'none' &&
               style.visibility !== 'hidden' &&
               element.offsetParent !== null;
    }
    
    /**
     * Trap keyboard focus within element
     * @param {HTMLElement} element - Element to trap focus in
     */
    trapFocus(element) {
        if (!element) return;
        
        this.keyboardTrapStack.push(element);
        
        // Focus first focusable element
        const focusableElements = this.getFocusableElements(element);
        if (focusableElements.length > 0) {
            this.setFocus(focusableElements[0]);
        }
    }
    
    /**
     * Release focus trap
     * @param {HTMLElement} element - Element to release trap from
     */
    releaseFocus(element) {
        const index = this.keyboardTrapStack.indexOf(element);
        if (index > -1) {
            this.keyboardTrapStack.splice(index, 1);
        }
    }
    
    /**
     * Update ARIA attributes
     * @param {HTMLElement} element - Target element
     * @param {Object} attributes - ARIA attributes to set
     */
    updateARIA(element, attributes) {
        if (!element) return;
        
        Object.entries(attributes).forEach(([key, value]) => {
            const ariaKey = key.startsWith('aria-') ? key : `aria-${key}`;
            DOMUtils.attr(element, ariaKey, value);
        });
    }
    
    /**
     * Update progress bar accessibility
     * @param {HTMLElement} progressElement - Progress bar element
     * @param {number} value - Current value
     * @param {number} max - Maximum value
     * @param {string} text - Progress text
     */
    updateProgress(progressElement, value, max = 100, text = '') {
        if (!progressElement) return;
        
        this.updateARIA(progressElement, {
            'valuenow': value,
            'valuemax': max,
            'valuetext': text || `${value} von ${max}`
        });
        
        // Update visual progress
        const progressFill = progressElement.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = `${(value / max) * 100}%`;
        }
        
        // Announce significant progress changes
        if (value % 25 === 0 || value === max) {
            this.announce(`Fortschritt: ${text || `${value}%`}`);
        }
    }
    
    /**
     * Make element into accessible button
     * @param {HTMLElement} element - Element to enhance
     * @param {Function} clickHandler - Click handler
     * @param {string} label - Accessible label
     */
    makeAccessibleButton(element, clickHandler, label) {
        if (!element) return;
        
        // Set role and attributes
        element.setAttribute('role', 'button');
        element.setAttribute('tabindex', '0');
        
        if (label) {
            element.setAttribute('aria-label', label);
        }
        
        // Add event listeners
        DOMUtils.on(element, 'click', clickHandler);
        DOMUtils.on(element, 'keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                clickHandler(e);
            }
        });
    }
    
    /**
     * Create accessible modal dialog
     * @param {HTMLElement} modal - Modal element
     * @param {HTMLElement} trigger - Element that triggered modal
     */
    openModal(modal, trigger = null) {
        if (!modal) return;
        
        // Store previous focus
        this.previousFocus = document.activeElement;
        this.modalTrigger = trigger;
        
        // Set ARIA attributes
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-hidden', 'false');
        
        // Show modal
        DOMUtils.show(modal);
        
        // Trap focus
        this.trapFocus(modal);
        
        // Announce modal opened
        const modalTitle = modal.querySelector('h1, h2, h3, [role="heading"]');
        if (modalTitle) {
            this.announce(`Dialog geöffnet: ${modalTitle.textContent}`);
        }
    }
    
    /**
     * Close accessible modal dialog
     * @param {HTMLElement} modal - Modal element
     */
    closeModal(modal) {
        if (!modal) return;
        
        // Set ARIA attributes
        modal.setAttribute('aria-hidden', 'true');
        
        // Hide modal
        DOMUtils.hide(modal);
        
        // Release focus trap
        this.releaseFocus(modal);
        
        // Restore previous focus
        if (this.previousFocus) {
            this.setFocus(this.previousFocus);
        } else if (this.modalTrigger) {
            this.setFocus(this.modalTrigger);
        }
        
        // Clear stored focus
        this.previousFocus = null;
        this.modalTrigger = null;
        
        // Announce modal closed
        this.announce('Dialog geschlossen');
    }
    
    /**
     * Check color contrast ratio
     * @param {string} foreground - Foreground color
     * @param {string} background - Background color
     * @returns {number} Contrast ratio
     */
    getContrastRatio(foreground, background) {
        // Simple implementation - in real app, use proper color contrast library
        // This is a placeholder for the concept
        const getLuminance = (color) => {
            // Simplified luminance calculation
            return 0.5; // Placeholder
        };
        
        const lum1 = getLuminance(foreground);
        const lum2 = getLuminance(background);
        
        const brightest = Math.max(lum1, lum2);
        const darkest = Math.min(lum1, lum2);
        
        return (brightest + 0.05) / (darkest + 0.05);
    }
    
    /**
     * Validate WCAG compliance
     * @param {HTMLElement} container - Container to validate
     * @returns {Object} Validation results
     */
    validateWCAG(container = document) {
        const results = {
            errors: [],
            warnings: [],
            passed: []
        };
        
        // Check for alt text on images
        const images = DOMUtils.querySelectorAll('img', container);
        images.forEach(img => {
            if (!img.alt && img.alt !== '') {
                results.errors.push(`Image missing alt text: ${img.src}`);
            } else {
                results.passed.push('Image has alt text');
            }
        });
        
        // Check for form labels
        const inputs = DOMUtils.querySelectorAll('input, select, textarea', container);
        inputs.forEach(input => {
            const id = input.id;
            const label = id ? DOMUtils.querySelector(`label[for="${id}"]`) : null;
            const ariaLabel = input.getAttribute('aria-label');
            const ariaLabelledby = input.getAttribute('aria-labelledby');
            
            if (!label && !ariaLabel && !ariaLabelledby) {
                results.errors.push(`Form control missing label: ${input.tagName}`);
            } else {
                results.passed.push('Form control has label');
            }
        });
        
        // Check heading hierarchy
        const headings = DOMUtils.querySelectorAll('h1, h2, h3, h4, h5, h6', container);
        let previousLevel = 0;
        headings.forEach(heading => {
            const level = parseInt(heading.tagName.charAt(1));
            if (level > previousLevel + 1) {
                results.warnings.push(`Heading level skip: ${heading.tagName} after h${previousLevel}`);
            }
            previousLevel = level;
        });
        
        return results;
    }
    
    /**
     * Destroy accessibility manager (cleanup)
     */
    destroy() {
        this.keyboardTrapStack = [];
        this.liveRegions = {};
        this.previousFocus = null;
        this.modalTrigger = null;
        
        console.log('♿ Accessibility Manager destroyed');
    }
}

// Export utility functions
export const AccessibilityUtils = {
    /**
     * Quick announce function
     * @param {string} message - Message to announce
     * @param {string} priority - Priority level
     */
    announce(message, priority = 'polite') {
        const liveRegion = DOMUtils.getElementById(`ariaLive${priority.charAt(0).toUpperCase() + priority.slice(1)}`);
        if (liveRegion) {
            liveRegion.textContent = '';
            setTimeout(() => {
                liveRegion.textContent = message;
            }, 50);
        }
    },
    
    /**
     * Check if user prefers reduced motion
     * @returns {boolean} True if user prefers reduced motion
     */
    prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    },
    
    /**
     * Check if user prefers high contrast
     * @returns {boolean} True if user prefers high contrast
     */
    prefersHighContrast() {
        return window.matchMedia('(prefers-contrast: high)').matches;
    }
};