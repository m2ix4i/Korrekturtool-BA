/**
 * Event Bus Utility
 * Simple event emitter for component communication
 * Provides a centralized event system for modular architecture
 */

export class EventBus {
    constructor() {
        this.events = new Map();
        this.debug = false; // Set to true for debugging
    }
    
    /**
     * Subscribe to an event
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     * @param {Object} options - Options object
     * @param {boolean} options.once - Only fire once
     * @param {number} options.priority - Event priority (higher = first)
     */
    on(event, callback, options = {}) {
        if (typeof callback !== 'function') {
            throw new Error('Event callback must be a function');
        }
        
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }
        
        const listener = {
            callback,
            once: options.once || false,
            priority: options.priority || 0,
            id: this.generateId()
        };
        
        const listeners = this.events.get(event);
        listeners.push(listener);
        
        // Sort by priority (higher priority first)
        listeners.sort((a, b) => b.priority - a.priority);
        
        if (this.debug) {
            console.log(`📡 EventBus: Subscribed to '${event}' (ID: ${listener.id})`);
        }
        
        // Return unsubscribe function
        return () => this.off(event, listener.id);
    }
    
    /**
     * Subscribe to an event only once
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     * @param {Object} options - Options object
     */
    once(event, callback, options = {}) {
        return this.on(event, callback, { ...options, once: true });
    }
    
    /**
     * Unsubscribe from an event
     * @param {string} event - Event name
     * @param {string|Function} callbackOrId - Callback function or listener ID
     */
    off(event, callbackOrId) {
        if (!this.events.has(event)) {
            return false;
        }
        
        const listeners = this.events.get(event);
        const initialLength = listeners.length;
        
        if (typeof callbackOrId === 'string') {
            // Remove by ID
            const index = listeners.findIndex(listener => listener.id === callbackOrId);
            if (index !== -1) {
                listeners.splice(index, 1);
            }
        } else if (typeof callbackOrId === 'function') {
            // Remove by callback function
            const index = listeners.findIndex(listener => listener.callback === callbackOrId);
            if (index !== -1) {
                listeners.splice(index, 1);
            }
        }
        
        // Clean up empty event arrays
        if (listeners.length === 0) {
            this.events.delete(event);
        }
        
        const removed = initialLength > listeners.length;
        
        if (this.debug && removed) {
            console.log(`📡 EventBus: Unsubscribed from '${event}'`);
        }
        
        return removed;
    }
    
    /**
     * Emit an event
     * @param {string} event - Event name
     * @param {*} data - Event data
     * @param {Object} options - Emit options
     * @param {boolean} options.async - Emit asynchronously
     */
    emit(event, data = null, options = {}) {
        if (!this.events.has(event)) {
            if (this.debug) {
                console.log(`📡 EventBus: No listeners for '${event}'`);
            }
            return false;
        }
        
        const listeners = this.events.get(event);
        const listenersToRemove = [];
        
        if (this.debug) {
            console.log(`📡 EventBus: Emitting '${event}' to ${listeners.length} listeners`, data);
        }
        
        const executeListeners = () => {
            for (const listener of listeners) {
                try {
                    listener.callback(data, event);
                    
                    // Mark once listeners for removal
                    if (listener.once) {
                        listenersToRemove.push(listener.id);
                    }
                } catch (error) {
                    console.error(`📡 EventBus: Error in '${event}' listener:`, error);
                }
            }
            
            // Remove once listeners
            listenersToRemove.forEach(id => this.off(event, id));
        };
        
        if (options.async) {
            // Execute asynchronously
            setTimeout(executeListeners, 0);
        } else {
            // Execute synchronously
            executeListeners();
        }
        
        return true;
    }
    
    /**
     * Emit an event asynchronously
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    emitAsync(event, data = null) {
        return this.emit(event, data, { async: true });
    }
    
    /**
     * Get all listeners for an event
     * @param {string} event - Event name
     * @returns {Array} Array of listeners
     */
    getListeners(event) {
        return this.events.get(event) || [];
    }
    
    /**
     * Get all event names
     * @returns {Array} Array of event names
     */
    getEventNames() {
        return Array.from(this.events.keys());
    }
    
    /**
     * Check if event has listeners
     * @param {string} event - Event name
     * @returns {boolean} True if event has listeners
     */
    hasListeners(event) {
        return this.events.has(event) && this.events.get(event).length > 0;
    }
    
    /**
     * Get total listener count
     * @returns {number} Total number of listeners
     */
    getListenerCount() {
        let count = 0;
        for (const listeners of this.events.values()) {
            count += listeners.length;
        }
        return count;
    }
    
    /**
     * Clear all listeners for an event or all events
     * @param {string} event - Optional event name
     */
    clear(event = null) {
        if (event) {
            this.events.delete(event);
            if (this.debug) {
                console.log(`📡 EventBus: Cleared all listeners for '${event}'`);
            }
        } else {
            this.events.clear();
            if (this.debug) {
                console.log('📡 EventBus: Cleared all listeners');
            }
        }
    }
    
    /**
     * Enable or disable debug mode
     * @param {boolean} enabled - Debug enabled
     */
    setDebug(enabled) {
        this.debug = enabled;
        console.log(`📡 EventBus: Debug mode ${enabled ? 'enabled' : 'disabled'}`);
    }
    
    /**
     * Get debug information
     * @returns {Object} Debug information
     */
    getDebugInfo() {
        const eventInfo = {};
        
        for (const [event, listeners] of this.events.entries()) {
            eventInfo[event] = {
                listenerCount: listeners.length,
                listeners: listeners.map(l => ({
                    id: l.id,
                    once: l.once,
                    priority: l.priority
                }))
            };
        }
        
        return {
            totalEvents: this.events.size,
            totalListeners: this.getListenerCount(),
            events: eventInfo
        };
    }
    
    /**
     * Create a namespaced event bus
     * @param {string} namespace - Namespace prefix
     * @returns {Object} Namespaced event bus methods
     */
    namespace(namespace) {
        const prefixEvent = (event) => `${namespace}:${event}`;
        
        return {
            on: (event, callback, options) => this.on(prefixEvent(event), callback, options),
            once: (event, callback, options) => this.once(prefixEvent(event), callback, options),
            off: (event, callbackOrId) => this.off(prefixEvent(event), callbackOrId),
            emit: (event, data, options) => this.emit(prefixEvent(event), data, options),
            emitAsync: (event, data) => this.emitAsync(prefixEvent(event), data),
            hasListeners: (event) => this.hasListeners(prefixEvent(event)),
            clear: (event) => this.clear(event ? prefixEvent(event) : null)
        };
    }
    
    /**
     * Generate unique listener ID
     * @returns {string} Unique ID
     */
    generateId() {
        return `listener_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Destroy the event bus (cleanup)
     */
    destroy() {
        this.clear();
        console.log('📡 EventBus: Destroyed');
    }
}