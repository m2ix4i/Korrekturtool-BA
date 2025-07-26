/**
 * DOM Utilities
 * Helper functions for DOM manipulation and element management
 * Provides consistent, safe DOM operations across the application
 */

/**
 * DOM manipulation utilities
 */
export class DOMUtils {
    
    /**
     * Safely get element by ID
     * @param {string} id - Element ID
     * @returns {HTMLElement|null} Element or null
     */
    static getElementById(id) {
        return document.getElementById(id);
    }
    
    /**
     * Safely query selector
     * @param {string} selector - CSS selector
     * @param {HTMLElement} context - Context element (default: document)
     * @returns {HTMLElement|null} Element or null
     */
    static querySelector(selector, context = document) {
        try {
            return context.querySelector(selector);
        } catch (error) {
            console.warn(`Invalid selector: ${selector}`, error);
            return null;
        }
    }
    
    /**
     * Safely query selector all
     * @param {string} selector - CSS selector
     * @param {HTMLElement} context - Context element (default: document)
     * @returns {NodeList} NodeList (empty if error)
     */
    static querySelectorAll(selector, context = document) {
        try {
            return context.querySelectorAll(selector);
        } catch (error) {
            console.warn(`Invalid selector: ${selector}`, error);
            return document.createDocumentFragment().childNodes;
        }
    }
    
    /**
     * Create element with attributes and content
     * @param {string} tagName - HTML tag name
     * @param {Object} attributes - Attributes object
     * @param {string|HTMLElement|Array} content - Content to append
     * @returns {HTMLElement} Created element
     */
    static createElement(tagName, attributes = {}, content = null) {
        const element = document.createElement(tagName);
        
        // Set attributes
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className' || key === 'class') {
                element.className = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else if (key.startsWith('aria-')) {
                element.setAttribute(key, value);
            } else {
                element[key] = value;
            }
        });
        
        // Add content
        if (content !== null) {
            this.appendContent(element, content);
        }
        
        return element;
    }
    
    /**
     * Append content to element
     * @param {HTMLElement} element - Target element
     * @param {string|HTMLElement|Array} content - Content to append
     */
    static appendContent(element, content) {
        if (typeof content === 'string') {
            element.textContent = content;
        } else if (content instanceof HTMLElement) {
            element.appendChild(content);
        } else if (Array.isArray(content)) {
            content.forEach(item => this.appendContent(element, item));
        }
    }
    
    /**
     * Add CSS classes to element
     * @param {HTMLElement} element - Target element
     * @param {...string} classes - Classes to add
     */
    static addClass(element, ...classes) {
        if (element && element.classList) {
            element.classList.add(...classes);
        }
    }
    
    /**
     * Remove CSS classes from element
     * @param {HTMLElement} element - Target element
     * @param {...string} classes - Classes to remove
     */
    static removeClass(element, ...classes) {
        if (element && element.classList) {
            element.classList.remove(...classes);
        }
    }
    
    /**
     * Toggle CSS class on element
     * @param {HTMLElement} element - Target element
     * @param {string} className - Class to toggle
     * @param {boolean} force - Force state (optional)
     * @returns {boolean} True if class is now present
     */
    static toggleClass(element, className, force = undefined) {
        if (element && element.classList) {
            return element.classList.toggle(className, force);
        }
        return false;
    }
    
    /**
     * Check if element has class
     * @param {HTMLElement} element - Target element
     * @param {string} className - Class to check
     * @returns {boolean} True if class is present
     */
    static hasClass(element, className) {
        return element && element.classList && element.classList.contains(className);
    }
    
    /**
     * Set or get element attribute
     * @param {HTMLElement} element - Target element
     * @param {string} name - Attribute name
     * @param {string} value - Attribute value (optional)
     * @returns {string|null} Attribute value if getting
     */
    static attr(element, name, value = undefined) {
        if (!element) return null;
        
        if (value === undefined) {
            return element.getAttribute(name);
        } else {
            element.setAttribute(name, value);
            return value;
        }
    }
    
    /**
     * Remove attribute from element
     * @param {HTMLElement} element - Target element
     * @param {string} name - Attribute name
     */
    static removeAttr(element, name) {
        if (element) {
            element.removeAttribute(name);
        }
    }
    
    /**
     * Show element (remove display: none)
     * @param {HTMLElement} element - Target element
     * @param {string} display - Display value (default: block)
     */
    static show(element, display = 'block') {
        if (element) {
            element.style.display = display;
        }
    }
    
    /**
     * Hide element (set display: none)
     * @param {HTMLElement} element - Target element
     */
    static hide(element) {
        if (element) {
            element.style.display = 'none';
        }
    }
    
    /**
     * Toggle element visibility
     * @param {HTMLElement} element - Target element
     * @param {string} display - Display value when showing
     * @returns {boolean} True if element is now visible
     */
    static toggle(element, display = 'block') {
        if (!element) return false;
        
        const isVisible = element.style.display !== 'none';
        if (isVisible) {
            this.hide(element);
            return false;
        } else {
            this.show(element, display);
            return true;
        }
    }
    
    /**
     * Check if element is visible
     * @param {HTMLElement} element - Target element
     * @returns {boolean} True if element is visible
     */
    static isVisible(element) {
        if (!element) return false;
        
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && 
               style.visibility !== 'hidden' && 
               style.opacity !== '0';
    }
    
    /**
     * Get element position relative to viewport
     * @param {HTMLElement} element - Target element
     * @returns {Object} Position object with top, left, width, height
     */
    static getPosition(element) {
        if (!element) return null;
        
        const rect = element.getBoundingClientRect();
        return {
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
            right: rect.right,
            bottom: rect.bottom
        };
    }
    
    /**
     * Scroll element into view smoothly
     * @param {HTMLElement} element - Target element
     * @param {Object} options - Scroll options
     */
    static scrollIntoView(element, options = {}) {
        if (!element) return;
        
        const defaultOptions = {
            behavior: 'smooth',
            block: 'nearest',
            inline: 'nearest'
        };
        
        element.scrollIntoView({ ...defaultOptions, ...options });
    }
    
    /**
     * Find closest parent with selector
     * @param {HTMLElement} element - Starting element
     * @param {string} selector - CSS selector
     * @returns {HTMLElement|null} Closest matching parent
     */
    static closest(element, selector) {
        if (!element || !element.closest) return null;
        
        try {
            return element.closest(selector);
        } catch (error) {
            console.warn(`Invalid selector in closest: ${selector}`, error);
            return null;
        }
    }
    
    /**
     * Remove all child elements
     * @param {HTMLElement} element - Parent element
     */
    static empty(element) {
        if (element) {
            while (element.firstChild) {
                element.removeChild(element.firstChild);
            }
        }
    }
    
    /**
     * Safe event listener addition
     * @param {HTMLElement} element - Target element
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     * @param {Object} options - Event options
     */
    static on(element, event, handler, options = {}) {
        if (element && typeof handler === 'function') {
            element.addEventListener(event, handler, options);
        }
    }
    
    /**
     * Safe event listener removal
     * @param {HTMLElement} element - Target element
     * @param {string} event - Event name
     * @param {Function} handler - Event handler
     * @param {Object} options - Event options
     */
    static off(element, event, handler, options = {}) {
        if (element && typeof handler === 'function') {
            element.removeEventListener(event, handler, options);
        }
    }
    
    /**
     * Dispatch custom event
     * @param {HTMLElement} element - Target element
     * @param {string} eventName - Event name
     * @param {*} detail - Event detail data
     */
    static trigger(element, eventName, detail = null) {
        if (!element) return;
        
        const event = new CustomEvent(eventName, {
            detail,
            bubbles: true,
            cancelable: true
        });
        
        element.dispatchEvent(event);
    }
    
    /**
     * Wait for element to appear in DOM
     * @param {string} selector - CSS selector
     * @param {number} timeout - Timeout in milliseconds
     * @returns {Promise<HTMLElement>} Promise that resolves with element
     */
    static waitForElement(selector, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const element = this.querySelector(selector);
            if (element) {
                resolve(element);
                return;
            }
            
            const observer = new MutationObserver(() => {
                const element = this.querySelector(selector);
                if (element) {
                    observer.disconnect();
                    clearTimeout(timeoutId);
                    resolve(element);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            const timeoutId = setTimeout(() => {
                observer.disconnect();
                reject(new Error(`Element with selector "${selector}" not found within ${timeout}ms`));
            }, timeout);
        });
    }
    
    /**
     * Debounce function for DOM events
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Throttle function for DOM events
     * @param {Function} func - Function to throttle
     * @param {number} limit - Limit in milliseconds
     * @returns {Function} Throttled function
     */
    static throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}