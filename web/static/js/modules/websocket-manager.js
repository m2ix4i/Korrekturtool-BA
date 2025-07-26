/**
 * WebSocket Manager Module
 * Manages Socket.IO client connections for real-time progress tracking
 * Handles connection management, room joining, and event subscription
 */

/**
 * WebSocket Manager Class
 * Provides centralized WebSocket connection management with automatic reconnection,
 * job room management, and event subscription system for real-time updates
 */
export class WebSocketManager {
    constructor(eventBus) {
        this.eventBus = eventBus;
        this.socket = null;
        this.connected = false;
        this.currentJobId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.connectionTimeout = 10000; // 10 seconds
        
        // Event subscriptions
        this.eventSubscriptions = new Map();
        
        console.log('🔌 WebSocketManager initialized');
    }
    
    /**
     * Establish WebSocket connection to the server
     * @returns {Promise<void>} Resolves when connection is established
     */
    async connect() {
        return new Promise((resolve, reject) => {
            try {
                if (this.connected && this.socket) {
                    console.log('🔌 WebSocket already connected');
                    resolve();
                    return;
                }
                
                console.log('🔌 Establishing WebSocket connection...');
                
                // Initialize Socket.IO connection
                this.socket = io({
                    timeout: this.connectionTimeout,
                    forceNew: true,
                    reconnection: true,
                    reconnectionAttempts: this.maxReconnectAttempts,
                    reconnectionDelay: this.reconnectDelay,
                    reconnectionDelayMax: this.maxReconnectDelay
                });
                
                // Set up connection event handlers
                this.setupConnectionHandlers(resolve, reject);
                
                // Set up message event handlers
                this.setupMessageHandlers();
                
            } catch (error) {
                console.error('❌ Failed to initialize WebSocket connection:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Set up connection-related event handlers
     * @private
     */
    setupConnectionHandlers(resolve, reject) {
        // Connection successful
        this.socket.on('connect', () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            console.log('✅ WebSocket connected successfully');
            
            // Emit connection event
            this.eventBus.emit('websocket:connected', {
                socketId: this.socket.id,
                timestamp: Date.now()
            });
            
            resolve();
        });
        
        // Connection failed
        this.socket.on('connect_error', (error) => {
            console.error('❌ WebSocket connection error:', error);
            this.connected = false;
            
            // Emit connection error event
            this.eventBus.emit('websocket:connection-error', {
                error: error.message,
                attempts: this.reconnectAttempts,
                timestamp: Date.now()
            });
            
            if (this.reconnectAttempts === 0) {
                reject(error);
            }
        });
        
        // Disconnection
        this.socket.on('disconnect', (reason) => {
            this.connected = false;
            console.log('🔌 WebSocket disconnected:', reason);
            
            // Emit disconnection event
            this.eventBus.emit('websocket:disconnected', {
                reason,
                wasConnected: this.connected,
                timestamp: Date.now()
            });
        });
        
        // Reconnection attempt
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            this.reconnectAttempts = attemptNumber;
            console.log(`🔄 WebSocket reconnection attempt ${attemptNumber}/${this.maxReconnectAttempts}`);
            
            // Emit reconnection attempt event
            this.eventBus.emit('websocket:reconnect-attempt', {
                attempt: attemptNumber,
                maxAttempts: this.maxReconnectAttempts,
                timestamp: Date.now()
            });
        });
        
        // Reconnection successful
        this.socket.on('reconnect', (attemptNumber) => {
            this.connected = true;
            this.reconnectAttempts = 0;
            console.log(`✅ WebSocket reconnected after ${attemptNumber} attempts`);
            
            // Rejoin current job room if active
            if (this.currentJobId) {
                console.log(`🔄 Rejoining job room for ${this.currentJobId}`);
                this.joinJob(this.currentJobId);
            }
            
            // Emit reconnection event
            this.eventBus.emit('websocket:reconnected', {
                attempts: attemptNumber,
                timestamp: Date.now()
            });
        });
        
        // Reconnection failed
        this.socket.on('reconnect_failed', () => {
            console.error('❌ WebSocket reconnection failed after maximum attempts');
            this.connected = false;
            
            // Emit reconnection failed event
            this.eventBus.emit('websocket:reconnect-failed', {
                maxAttempts: this.maxReconnectAttempts,
                timestamp: Date.now()
            });
        });
    }
    
    /**
     * Set up message event handlers for progress tracking
     * @private
     */
    setupMessageHandlers() {
        // Connection confirmation
        this.socket.on('connected', (data) => {
            console.log('📨 WebSocket connection confirmed:', data);
            this.eventBus.emit('websocket:confirmed', data);
        });
        
        // Job room joined
        this.socket.on('job_joined', (data) => {
            console.log('🏠 Joined job room:', data);
            this.eventBus.emit('websocket:job-joined', data);
        });
        
        // Job started
        this.socket.on('job_started', (data) => {
            console.log('🚀 Job started:', data);
            this.eventBus.emit('websocket:job-started', data);
        });
        
        // Progress update
        this.socket.on('progress_update', (data) => {
            console.log('📊 Progress update:', data);
            this.eventBus.emit('websocket:progress-update', data);
        });
        
        // Stage completed
        this.socket.on('stage_completed', (data) => {
            console.log('✅ Stage completed:', data);
            this.eventBus.emit('websocket:stage-completed', data);
        });
        
        // Job completed
        this.socket.on('job_completed', (data) => {
            console.log('🎉 Job completed:', data);
            this.eventBus.emit('websocket:job-completed', data);
        });
        
        // Job failed
        this.socket.on('job_failed', (data) => {
            console.error('💥 Job failed:', data);
            this.eventBus.emit('websocket:job-failed', data);
        });
        
        // Job status response
        this.socket.on('job_status_response', (data) => {
            console.log('📋 Job status response:', data);
            this.eventBus.emit('websocket:job-status', data);
        });
        
        // Error events
        this.socket.on('error', (data) => {
            console.error('🚨 WebSocket error:', data);
            this.eventBus.emit('websocket:error', data);
        });
        
        // Ping/pong for connection health
        this.socket.on('pong', (data) => {
            console.log('🏓 Pong received:', data);
            this.eventBus.emit('websocket:pong', data);
        });
    }
    
    /**
     * Join a job-specific room for progress updates
     * @param {string} jobId - The job ID to track
     * @returns {Promise<void>} Resolves when room is joined
     */
    async joinJob(jobId) {
        return new Promise((resolve, reject) => {
            if (!this.connected || !this.socket) {
                const error = new Error('WebSocket not connected');
                console.error('❌ Cannot join job room: WebSocket not connected');
                reject(error);
                return;
            }
            
            console.log(`🏠 Joining job room for: ${jobId}`);
            this.currentJobId = jobId;
            
            // Set up one-time listener for join confirmation
            const joinListener = (data) => {
                if (data.job_id === jobId) {
                    this.socket.off('job_joined', joinListener);
                    console.log(`✅ Successfully joined job room for ${jobId}`);
                    resolve(data);
                }
            };
            
            const errorListener = (error) => {
                if (error.job_id === jobId) {
                    this.socket.off('error', errorListener);
                    this.socket.off('job_joined', joinListener);
                    console.error(`❌ Failed to join job room for ${jobId}:`, error);
                    reject(new Error(error.message || 'Failed to join job room'));
                }
            };
            
            this.socket.on('job_joined', joinListener);
            this.socket.on('error', errorListener);
            
            // Send join request
            this.socket.emit('join_job', { job_id: jobId });
            
            // Timeout handling
            setTimeout(() => {
                this.socket.off('job_joined', joinListener);
                this.socket.off('error', errorListener);
                reject(new Error('Timeout joining job room'));
            }, 5000);
        });
    }
    
    /**
     * Leave the current job room
     * @param {string} jobId - The job ID to leave (optional, defaults to current)
     * @returns {Promise<void>} Resolves when room is left
     */
    async leaveJob(jobId = null) {
        const targetJobId = jobId || this.currentJobId;
        
        if (!targetJobId) {
            console.log('🏠 No job room to leave');
            return;
        }
        
        if (!this.connected || !this.socket) {
            console.warn('⚠️ Cannot leave job room: WebSocket not connected');
            this.currentJobId = null;
            return;
        }
        
        console.log(`🏠 Leaving job room for: ${targetJobId}`);
        
        return new Promise((resolve) => {
            // Set up one-time listener for leave confirmation
            const leaveListener = (data) => {
                if (data.job_id === targetJobId) {
                    this.socket.off('job_left', leaveListener);
                    this.currentJobId = null;
                    console.log(`✅ Successfully left job room for ${targetJobId}`);
                    resolve(data);
                }
            };
            
            this.socket.on('job_left', leaveListener);
            this.socket.emit('leave_job', { job_id: targetJobId });
            
            // Timeout handling
            setTimeout(() => {
                this.socket.off('job_left', leaveListener);
                this.currentJobId = null;
                resolve();
            }, 3000);
        });
    }
    
    /**
     * Get current status of a job
     * @param {string} jobId - The job ID to check
     * @returns {Promise<Object>} Job status data
     */
    async getJobStatus(jobId) {
        return new Promise((resolve, reject) => {
            if (!this.connected || !this.socket) {
                reject(new Error('WebSocket not connected'));
                return;
            }
            
            console.log(`📋 Requesting job status for: ${jobId}`);
            
            // Set up one-time listener for status response
            const statusListener = (data) => {
                if (data.job_id === jobId) {
                    this.socket.off('job_status_response', statusListener);
                    resolve(data);
                }
            };
            
            this.socket.on('job_status_response', statusListener);
            this.socket.emit('get_job_status', { job_id: jobId });
            
            // Timeout handling
            setTimeout(() => {
                this.socket.off('job_status_response', statusListener);
                reject(new Error('Timeout getting job status'));
            }, 5000);
        });
    }
    
    /**
     * Send ping to check connection health
     * @returns {Promise<Object>} Pong response
     */
    async ping() {
        return new Promise((resolve, reject) => {
            if (!this.connected || !this.socket) {
                reject(new Error('WebSocket not connected'));
                return;
            }
            
            const pingData = { timestamp: Date.now() };
            console.log('🏓 Sending ping...');
            
            // Set up one-time listener for pong response
            const pongListener = (data) => {
                if (data.echo && data.echo.timestamp === pingData.timestamp) {
                    this.socket.off('pong', pongListener);
                    const latency = Date.now() - pingData.timestamp;
                    console.log(`🏓 Pong received - latency: ${latency}ms`);
                    resolve({ ...data, latency });
                }
            };
            
            this.socket.on('pong', pongListener);
            this.socket.emit('ping', pingData);
            
            // Timeout handling
            setTimeout(() => {
                this.socket.off('pong', pongListener);
                reject(new Error('Ping timeout'));
            }, 5000);
        });
    }
    
    /**
     * Clean disconnect from WebSocket
     */
    disconnect() {
        if (this.socket) {
            console.log('🔌 Disconnecting WebSocket...');
            
            // Leave current job room if active
            if (this.currentJobId) {
                this.leaveJob();
            }
            
            // Clean disconnect
            this.socket.disconnect();
            this.socket = null;
        }
        
        this.connected = false;
        this.currentJobId = null;
        this.reconnectAttempts = 0;
        
        console.log('✅ WebSocket disconnected cleanly');
    }
    
    /**
     * Check if WebSocket is currently connected
     * @returns {boolean} Connection status
     */
    isConnected() {
        return this.connected && this.socket && this.socket.connected;
    }
    
    /**
     * Get current connection information
     * @returns {Object} Connection info
     */
    getConnectionInfo() {
        return {
            connected: this.connected,
            socketId: this.socket ? this.socket.id : null,
            currentJobId: this.currentJobId,
            reconnectAttempts: this.reconnectAttempts,
            hasSocket: !!this.socket
        };
    }
    
    /**
     * Subscribe to WebSocket events via EventBus
     * @param {string} event - Event name to subscribe to
     * @param {Function} callback - Callback function
     */
    subscribe(event, callback) {
        const eventName = `websocket:${event}`;
        this.eventBus.on(eventName, callback);
        
        // Keep track of subscriptions for cleanup
        if (!this.eventSubscriptions.has(eventName)) {
            this.eventSubscriptions.set(eventName, new Set());
        }
        this.eventSubscriptions.get(eventName).add(callback);
    }
    
    /**
     * Unsubscribe from WebSocket events
     * @param {string} event - Event name to unsubscribe from
     * @param {Function} callback - Callback function to remove
     */
    unsubscribe(event, callback) {
        const eventName = `websocket:${event}`;
        this.eventBus.off(eventName, callback);
        
        // Clean up tracking
        if (this.eventSubscriptions.has(eventName)) {
            this.eventSubscriptions.get(eventName).delete(callback);
        }
    }
    
    /**
     * Cleanup all event subscriptions and disconnect
     */
    destroy() {
        console.log('🧹 Destroying WebSocketManager...');
        
        // Clean up all event subscriptions
        for (const [event, callbacks] of this.eventSubscriptions) {
            for (const callback of callbacks) {
                this.eventBus.off(event, callback);
            }
        }
        this.eventSubscriptions.clear();
        
        // Disconnect WebSocket
        this.disconnect();
        
        console.log('💀 WebSocketManager destroyed');
    }
}

export default WebSocketManager;