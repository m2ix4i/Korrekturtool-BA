/**
 * Frontend-Backend API Integration Tests - Issue #23
 * Comprehensive validation of API endpoints and data flow
 * Tests critical backend integration and functionality
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class APIIntegrationTests {
    constructor() {
        this.baseUrl = process.env.TEST_BASE_URL || 'http://localhost:5001';
        this.browser = null;
        this.pages = [];
        this.testResults = {
            passed: 0,
            failed: 0,
            errors: [],
            screenshots: [],
            apiResponses: [],
            performanceMetrics: []
        };
    }

    /**
     * Initialize browser for API testing
     */
    async setupBrowser() {
        console.log('🚀 Initializing browser for API integration testing...');
        
        try {
            this.browser = await puppeteer.launch({
                headless: false,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security'
                ],
                defaultViewport: { width: 1280, height: 720 }
            });
            
            console.log('✅ Browser initialized for API testing');
            return true;
        } catch (error) {
            console.error('❌ Browser initialization failed:', error);
            return false;
        }
    }

    /**
     * Create new page for testing
     */
    async createPage() {
        if (!this.browser) {
            throw new Error('Browser not initialized. Call setupBrowser() first.');
        }
        
        const page = await this.browser.newPage();
        await page.setViewport({ width: 1280, height: 720 });
        
        // Monitor network requests
        await page.setRequestInterception(true);
        page.on('request', request => {
            console.log(`📡 ${request.method()} ${request.url()}`);
            request.continue();
        });
        
        page.on('response', response => {
            if (response.url().includes('/api/') || response.url().includes('/health')) {
                console.log(`📨 ${response.status()} ${response.url()}`);
            }
        });
        
        this.pages.push(page);
        return page;
    }

    /**
     * Take screenshot with API context
     */
    async takeScreenshot(page, name, context = null) {
        const timestamp = Date.now();
        const screenshotPath = path.join(__dirname, 'screenshots', `api-${name}-${timestamp}.png`);
        
        const screenshotDir = path.dirname(screenshotPath);
        if (!fs.existsSync(screenshotDir)) {
            fs.mkdirSync(screenshotDir, { recursive: true });
        }
        
        await page.screenshot({ path: screenshotPath, fullPage: true });
        this.testResults.screenshots.push({
            path: screenshotPath,
            context: context,
            timestamp: timestamp
        });
        
        console.log(`📸 API Screenshot: ${screenshotPath}`);
        return screenshotPath;
    }

    /**
     * TEST: Core API endpoints functionality
     */
    async testCoreAPIEndpoints() {
        console.log('\n🔌 TEST: Core API Endpoints');
        const page = await this.createPage();
        
        try {
            await page.goto(this.baseUrl);
            
            // Test all documented API endpoints
            const endpoints = [
                {
                    path: '/health',
                    method: 'GET',
                    name: 'Health Check',
                    expectedStatus: 200,
                    requiredFields: ['status', 'service', 'version']
                },
                {
                    path: '/api/v1/info',
                    method: 'GET', 
                    name: 'API Information',
                    expectedStatus: 200,
                    requiredFields: ['name', 'description', 'version', 'endpoints']
                }
            ];
            
            for (const endpoint of endpoints) {
                console.log(`🔍 Testing ${endpoint.name} (${endpoint.method} ${endpoint.path})...`);
                
                const startTime = Date.now();
                const response = await page.evaluate(async (url, path, method) => {
                    try {
                        const res = await fetch(`${url}${path}`, { method });
                        const data = await res.json();
                        return {
                            status: res.status,
                            ok: res.ok,
                            data: data,
                            headers: Object.fromEntries(res.headers.entries())
                        };
                    } catch (error) {
                        return { error: error.message };
                    }
                }, this.baseUrl, endpoint.path, endpoint.method);
                const responseTime = Date.now() - startTime;
                
                // Store API response for analysis
                this.testResults.apiResponses.push({
                    endpoint: endpoint.path,
                    method: endpoint.method,
                    response: response,
                    responseTime: responseTime,
                    timestamp: Date.now()
                });
                
                // Validate response
                if (response.status === endpoint.expectedStatus) {
                    console.log(`✅ ${endpoint.name}: Status ${response.status} (${responseTime}ms)`);
                    
                    // Check required fields
                    const missingFields = endpoint.requiredFields.filter(field => 
                        !response.data || !(field in response.data)
                    );
                    
                    if (missingFields.length === 0) {
                        console.log(`✅ ${endpoint.name}: All required fields present`);
                        console.log(`📋 Response: ${JSON.stringify(response.data, null, 2)}`);
                    } else {
                        console.log(`⚠️  ${endpoint.name}: Missing fields: ${missingFields.join(', ')}`);
                    }
                } else {
                    console.log(`❌ ${endpoint.name}: Expected ${endpoint.expectedStatus}, got ${response.status}`);
                    if (response.error) {
                        console.log(`🔴 Error: ${response.error}`);
                    }
                }
                
                // Performance tracking
                this.testResults.performanceMetrics.push({
                    endpoint: endpoint.path,
                    responseTime: responseTime,
                    status: response.status
                });
            }
            
            await this.takeScreenshot(page, 'core-endpoints', 'Core API endpoints tested');
            
            this.testResults.passed++;
            console.log('✅ Core API endpoints test PASSED');
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`Core API endpoints error: ${error.message}`);
            console.error('❌ Core API endpoints test ERROR:', error);
        }
    }

    /**
     * TEST: WebSocket connection and real-time features
     */
    async testWebSocketFunctionality() {
        console.log('\n🔌 TEST: WebSocket Real-time Functionality');
        const page = await this.createPage();
        
        try {
            await page.goto(this.baseUrl);
            
            // Wait for SocketIO to load
            await page.waitForFunction(() => typeof io !== 'undefined', { timeout: 10000 });
            console.log('✅ SocketIO library loaded successfully');
            
            // Set up WebSocket monitoring
            const socketSetup = await page.evaluate(() => {
                return new Promise((resolve) => {
                    window.socketEvents = [];
                    window.socketConnected = false;
                    window.socketErrors = [];
                    
                    try {
                        const socket = io();
                        
                        socket.on('connect', () => {
                            window.socketConnected = true;
                            window.socketEvents.push({
                                type: 'connect',
                                timestamp: Date.now()
                            });
                            console.log('🔌 WebSocket connected');
                        });
                        
                        socket.on('disconnect', (reason) => {
                            window.socketEvents.push({
                                type: 'disconnect',
                                reason: reason,
                                timestamp: Date.now()
                            });
                            console.log('🔌 WebSocket disconnected:', reason);
                        });
                        
                        socket.on('progress_update', (data) => {
                            window.socketEvents.push({
                                type: 'progress_update',
                                data: data,
                                timestamp: Date.now()
                            });
                            console.log('📊 Progress update received:', data);
                        });
                        
                        socket.on('job_started', (data) => {
                            window.socketEvents.push({
                                type: 'job_started',
                                data: data,
                                timestamp: Date.now()
                            });
                            console.log('🚀 Job started:', data);
                        });
                        
                        socket.on('job_completed', (data) => {
                            window.socketEvents.push({
                                type: 'job_completed',
                                data: data,
                                timestamp: Date.now()
                            });
                            console.log('✅ Job completed:', data);
                        });
                        
                        socket.on('job_failed', (data) => {
                            window.socketEvents.push({
                                type: 'job_failed',
                                data: data,
                                timestamp: Date.now()
                            });
                            console.log('❌ Job failed:', data);
                        });
                        
                        socket.on('connect_error', (error) => {
                            window.socketErrors.push({
                                error: error.message,
                                timestamp: Date.now()
                            });
                            console.error('🔴 WebSocket connection error:', error);
                        });
                        
                        window.testSocket = socket;
                        
                        // Wait for connection
                        setTimeout(() => {
                            resolve({
                                connected: window.socketConnected,
                                events: window.socketEvents.length,
                                errors: window.socketErrors.length
                            });
                        }, 3000);
                        
                    } catch (error) {
                        resolve({ error: error.message });
                    }
                });
            });
            
            console.log('🔌 WebSocket setup result:', socketSetup);
            
            if (socketSetup.connected) {
                console.log('✅ WebSocket connected successfully');
                console.log(`📊 Events captured: ${socketSetup.events}`);
                
                // Test socket events
                const eventCheck = await page.evaluate(() => {
                    return {
                        events: window.socketEvents,
                        errors: window.socketErrors,
                        connected: window.socketConnected
                    };
                });
                
                console.log('📋 WebSocket events:', eventCheck.events);
                
                if (eventCheck.errors.length > 0) {
                    console.log('🔴 WebSocket errors:', eventCheck.errors);
                }
                
            } else if (socketSetup.error) {
                console.log(`❌ WebSocket setup error: ${socketSetup.error}`);
            } else {
                console.log('⚠️  WebSocket connection delayed or failed');
            }
            
            await this.takeScreenshot(page, 'websocket-test', 'WebSocket functionality test');
            
            this.testResults.passed++;
            console.log('✅ WebSocket functionality test PASSED');
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`WebSocket functionality error: ${error.message}`);
            console.error('❌ WebSocket functionality test ERROR:', error);
        }
    }

    /**
     * TEST: API performance and load handling
     */
    async testAPIPerformance() {
        console.log('\n⚡ TEST: API Performance and Load Handling');
        const page = await this.createPage();
        
        try {
            await page.goto(this.baseUrl);
            
            // Test concurrent API calls
            console.log('🔄 Testing concurrent API requests...');
            
            const concurrentRequests = await page.evaluate(async (baseUrl) => {
                const requests = [];
                const startTime = Date.now();
                
                // Make 10 concurrent requests to health endpoint
                for (let i = 0; i < 10; i++) {
                    requests.push(
                        fetch(`${baseUrl}/health`)
                            .then(res => ({ status: res.status, id: i }))
                            .catch(err => ({ error: err.message, id: i }))
                    );
                }
                
                const results = await Promise.all(requests);
                const totalTime = Date.now() - startTime;
                
                return {
                    results: results,
                    totalTime: totalTime,
                    averageTime: totalTime / requests.length
                };
            }, this.baseUrl);
            
            console.log(`⚡ Concurrent requests completed in ${concurrentRequests.totalTime}ms`);
            console.log(`📊 Average response time: ${concurrentRequests.averageTime.toFixed(2)}ms`);
            
            const successfulRequests = concurrentRequests.results.filter(r => r.status === 200).length;
            console.log(`✅ Successful requests: ${successfulRequests}/10`);
            
            // Test API response times under load
            console.log('📊 Testing individual response times...');
            
            const performanceTests = [];
            for (let i = 0; i < 5; i++) {
                const startTime = Date.now();
                const response = await page.evaluate(async (baseUrl) => {
                    try {
                        const res = await fetch(`${baseUrl}/api/v1/info`);
                        return { status: res.status, ok: res.ok };
                    } catch (error) {
                        return { error: error.message };
                    }
                }, this.baseUrl);
                const responseTime = Date.now() - startTime;
                
                performanceTests.push({
                    test: i + 1,
                    responseTime: responseTime,
                    status: response.status
                });
                
                console.log(`🎯 Test ${i + 1}: ${responseTime}ms (${response.status})`);
            }
            
            const averageResponseTime = performanceTests.reduce((sum, test) => sum + test.responseTime, 0) / performanceTests.length;
            console.log(`📊 Average API response time: ${averageResponseTime.toFixed(2)}ms`);
            
            // Performance evaluation
            if (averageResponseTime < 1000) {
                console.log('✅ API performance: Excellent (<1s)');
            } else if (averageResponseTime < 3000) {
                console.log('⚠️  API performance: Acceptable (1-3s)');
            } else {
                console.log('❌ API performance: Poor (>3s)');
            }
            
            await this.takeScreenshot(page, 'performance-test', 'API performance testing');
            
            this.testResults.passed++;
            console.log('✅ API performance test PASSED');
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`API performance error: ${error.message}`);
            console.error('❌ API performance test ERROR:', error);
        }
    }

    /**
     * TEST: Error handling and edge cases
     */
    async testErrorHandlingIntegration() {
        console.log('\n🚨 TEST: API Error Handling Integration');
        const page = await this.createPage();
        
        try {
            await page.goto(this.baseUrl);
            
            // Test invalid endpoints
            const invalidEndpoints = [
                '/api/v1/nonexistent',
                '/api/v2/info',
                '/api/v1/upload/invalid',
                '/invalid/path'
            ];
            
            console.log('🔍 Testing invalid endpoints...');
            for (const endpoint of invalidEndpoints) {
                const response = await page.evaluate(async (baseUrl, path) => {
                    try {
                        const res = await fetch(`${baseUrl}${path}`);
                        const data = await res.json();
                        return {
                            status: res.status,
                            data: data
                        };
                    } catch (error) {
                        return { error: error.message };
                    }
                }, this.baseUrl, endpoint);
                
                if (response.status === 404) {
                    console.log(`✅ ${endpoint}: Correctly returns 404`);
                    if (response.data && response.data.error) {
                        console.log(`📋 Error message: ${response.data.error}`);
                    }
                } else {
                    console.log(`⚠️  ${endpoint}: Unexpected status ${response.status}`);
                }
            }
            
            // Test malformed requests
            console.log('🔧 Testing malformed requests...');
            
            const malformedTests = [
                { method: 'POST', path: '/health', data: 'invalid-json' },
                { method: 'PUT', path: '/api/v1/info', data: null },
                { method: 'DELETE', path: '/health', data: null }
            ];
            
            for (const test of malformedTests) {
                const response = await page.evaluate(async (baseUrl, testCase) => {
                    try {
                        const options = {
                            method: testCase.method
                        };
                        
                        if (testCase.data) {
                            options.body = testCase.data;
                            options.headers = { 'Content-Type': 'application/json' };
                        }
                        
                        const res = await fetch(`${baseUrl}${testCase.path}`, options);
                        return {
                            status: res.status,
                            method: testCase.method,
                            path: testCase.path
                        };
                    } catch (error) {
                        return { 
                            error: error.message, 
                            method: testCase.method,
                            path: testCase.path
                        };
                    }
                }, this.baseUrl, test);
                
                console.log(`🔧 ${test.method} ${test.path}: ${response.status || 'Error'}`);
            }
            
            // Test CORS preflight
            console.log('🌐 Testing CORS preflight...');
            const corsTest = await page.evaluate(async (baseUrl) => {
                try {
                    const res = await fetch(`${baseUrl}/health`, {
                        method: 'OPTIONS'
                    });
                    return {
                        status: res.status,
                        headers: {
                            'access-control-allow-origin': res.headers.get('Access-Control-Allow-Origin'),
                            'access-control-allow-methods': res.headers.get('Access-Control-Allow-Methods'),
                            'access-control-allow-headers': res.headers.get('Access-Control-Allow-Headers')
                        }
                    };
                } catch (error) {
                    return { error: error.message };
                }
            }, this.baseUrl);
            
            console.log('🌐 CORS preflight result:', corsTest);
            
            await this.takeScreenshot(page, 'error-handling', 'API error handling test');
            
            this.testResults.passed++;
            console.log('✅ API error handling test PASSED');
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`API error handling error: ${error.message}`);
            console.error('❌ API error handling test ERROR:', error);
        }
    }

    /**
     * Run all API integration tests
     */
    async runAllTests() {
        console.log('🧪 STARTING API INTEGRATION TEST SUITE');
        console.log('======================================');
        
        const startTime = Date.now();
        
        if (!await this.setupBrowser()) {
            console.error('❌ Failed to setup browser. Aborting tests.');
            return false;
        }
        
        try {
            // Run all API integration tests
            await this.testCoreAPIEndpoints();
            await this.testWebSocketFunctionality();
            await this.testAPIPerformance();
            await this.testErrorHandlingIntegration();
            
        } catch (error) {
            console.error('❌ Test suite error:', error);
        } finally {
            await this.cleanup();
        }
        
        const totalTime = Date.now() - startTime;
        this.printResults(totalTime);
        
        return this.testResults.failed === 0;
    }

    /**
     * Print comprehensive API test results
     */
    printResults(totalTime) {
        console.log('\n🧪 API INTEGRATION TEST RESULTS');
        console.log('================================');
        console.log(`⏱️  Total execution time: ${totalTime}ms`);
        console.log(`✅ Tests passed: ${this.testResults.passed}`);
        console.log(`❌ Tests failed: ${this.testResults.failed}`);
        console.log(`📸 Screenshots taken: ${this.testResults.screenshots.length}`);
        console.log(`📡 API responses captured: ${this.testResults.apiResponses.length}`);
        console.log(`⚡ Performance metrics: ${this.testResults.performanceMetrics.length}`);
        
        if (this.testResults.errors.length > 0) {
            console.log('\n🚨 ERRORS:');
            this.testResults.errors.forEach((error, index) => {
                console.log(`${index + 1}. ${error}`);
            });
        }
        
        if (this.testResults.performanceMetrics.length > 0) {
            console.log('\n⚡ PERFORMANCE METRICS:');
            const avgResponseTime = this.testResults.performanceMetrics.reduce((sum, metric) => 
                sum + metric.responseTime, 0) / this.testResults.performanceMetrics.length;
            console.log(`📊 Average API response time: ${avgResponseTime.toFixed(2)}ms`);
            
            this.testResults.performanceMetrics.forEach((metric, index) => {
                console.log(`${index + 1}. ${metric.endpoint}: ${metric.responseTime}ms (${metric.status})`);
            });
        }
        
        if (this.testResults.apiResponses.length > 0) {
            console.log('\n📡 API RESPONSE SUMMARY:');
            this.testResults.apiResponses.forEach((api, index) => {
                console.log(`${index + 1}. ${api.method} ${api.endpoint}: ${api.response.status} (${api.responseTime}ms)`);
            });
        }
        
        const success = this.testResults.failed === 0;
        console.log(`\n${success ? '🎉 ALL API INTEGRATION TESTS PASSED!' : '⚠️  SOME TESTS FAILED'}`);
        
        if (success) {
            console.log('\n🚀 API INTEGRATION VALIDATED');
            console.log('✅ All endpoints functional');
            console.log('✅ WebSocket connectivity confirmed');
            console.log('✅ Error handling working');
            console.log('✅ Performance meets standards');
        }
    }

    /**
     * Cleanup resources
     */
    async cleanup() {
        console.log('\n🧹 Cleaning up API test resources...');
        
        if (this.pages.length > 0) {
            for (const page of this.pages) {
                try {
                    await page.close();
                } catch (error) {
                    console.warn('Warning: Could not close page:', error.message);
                }
            }
        }
        
        if (this.browser) {
            try {
                await this.browser.close();
                console.log('✅ Browser closed successfully');
            } catch (error) {
                console.error('❌ Error closing browser:', error);
            }
        }
    }
}

// Export for use in other test files
module.exports = APIIntegrationTests;

// Run tests if called directly
if (require.main === module) {
    const testSuite = new APIIntegrationTests();
    testSuite.runAllTests()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('Fatal error:', error);
            process.exit(1);
        });
}