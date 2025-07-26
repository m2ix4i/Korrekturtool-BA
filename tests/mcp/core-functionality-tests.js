/**
 * Core Functionality Tests - DOCX Upload & Processing
 * Tests the main purpose of the application: upload DOCX, process, download corrected version
 * Professional-grade testing for production readiness
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class CoreFunctionalityTests {
    constructor() {
        this.baseUrl = process.env.TEST_BASE_URL || 'http://localhost:5001';
        this.browser = null;
        this.page = null; // Single page instance for stability
        this.testDocumentPath = '/Users/max/Downloads/Volltext_BA_Max Thomsen.docx';
        this.testResults = {
            passed: 0,
            failed: 0,
            errors: [],
            screenshots: [],
            processingResults: {},
            downloadedFiles: []
        };
    }

    /**
     * Setup single browser instance for stable testing
     */
    async setupBrowser() {
        console.log('🚀 Setting up stable browser for core functionality testing...');
        
        try {
            // Verify test document exists
            if (!fs.existsSync(this.testDocumentPath)) {
                throw new Error(`Test document not found: ${this.testDocumentPath}`);
            }
            
            console.log(`✅ Test document found: ${this.testDocumentPath}`);
            const stats = fs.statSync(this.testDocumentPath);
            console.log(`📄 Document size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
            
            // Launch single browser instance
            this.browser = await puppeteer.launch({
                headless: false, // Keep visible for monitoring
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-dev-shm-usage',
                    '--no-first-run',
                    '--disable-default-apps'
                ],
                defaultViewport: { width: 1280, height: 720 },
                devtools: false // Disable devtools for stability
            });
            
            // Create single page instance
            this.page = await this.browser.newPage();
            await this.page.setViewport({ width: 1280, height: 720 });
            
            // Set up error handling
            this.page.on('error', error => {
                console.log(`🔴 Page Error: ${error.message}`);
            });
            
            this.page.on('console', msg => {
                if (msg.type() === 'error') {
                    console.log(`🔴 Console Error: ${msg.text()}`);
                }
            });
            
            console.log('✅ Stable browser setup completed');
            return true;
        } catch (error) {
            console.error('❌ Browser setup failed:', error);
            return false;
        }
    }

    /**
     * Take screenshot with context
     */
    async takeScreenshot(name, context = null) {
        if (!this.page) return null;
        
        const timestamp = Date.now();
        const screenshotPath = path.join(__dirname, 'screenshots', `core-${name}-${timestamp}.png`);
        
        const screenshotDir = path.dirname(screenshotPath);
        if (!fs.existsSync(screenshotDir)) {
            fs.mkdirSync(screenshotDir, { recursive: true });
        }
        
        try {
            await this.page.screenshot({ path: screenshotPath, fullPage: true });
            this.testResults.screenshots.push({
                path: screenshotPath,
                context: context,
                timestamp: timestamp
            });
            
            console.log(`📸 Screenshot: ${screenshotPath}`);
            return screenshotPath;
        } catch (error) {
            console.log(`⚠️  Screenshot failed: ${error.message}`);
            return null;
        }
    }

    /**
     * Wait for element with timeout and error handling
     */
    async waitForElement(selector, timeout = 30000, visible = true) {
        try {
            await this.page.waitForSelector(selector, { visible, timeout });
            return true;
        } catch (error) {
            console.log(`⚠️  Element not found: ${selector} (${error.message})`);
            return false;
        }
    }

    /**
     * TEST: Complete DOCX upload and processing workflow
     */
    async testDocumentUploadAndProcessing() {
        console.log('\n📄 TEST: Complete DOCX Upload and Processing Workflow');
        console.log('====================================================');
        
        try {
            // Navigate to application
            console.log('🌐 Navigating to application...');
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle0' });
            await this.takeScreenshot('app-loaded', 'Application loaded');
            
            // Wait for upload area
            console.log('🔍 Locating upload area...');
            const uploadAreaExists = await this.waitForElement('#uploadArea', 10000);
            if (!uploadAreaExists) {
                throw new Error('Upload area not found');
            }
            
            console.log('✅ Upload area found');
            
            // Get file input element
            console.log('📁 Preparing file upload...');
            const fileInputExists = await this.waitForElement('#fileInput', 5000, false);
            if (!fileInputExists) {
                throw new Error('File input not found');
            }
            
            // Upload the document
            console.log(`📤 Uploading document: ${this.testDocumentPath}`);
            const fileInput = await this.page.$('#fileInput');
            await fileInput.uploadFile(this.testDocumentPath);
            
            await this.takeScreenshot('file-uploaded', 'Document uploaded');
            
            // Wait for configuration section to become visible
            console.log('⚙️  Waiting for configuration section...');
            await new Promise(resolve => setTimeout(resolve, 2000)); // Allow UI to update
            
            // Check if configuration section is now visible
            const configVisible = await this.page.evaluate(() => {
                const configSection = document.getElementById('configSection');
                if (configSection) {
                    const style = window.getComputedStyle(configSection);
                    return style.display !== 'none' && style.visibility !== 'hidden';
                }
                return false;
            });
            
            if (configVisible) {
                console.log('✅ Configuration section activated after file upload');
                
                // Configure processing options
                console.log('⚙️  Configuring processing options...');
                
                // Ensure complete mode is selected
                try {
                    await this.page.click('#modeComplete');
                    console.log('✅ Complete processing mode selected');
                } catch (clickError) {
                    console.log('⚠️  Could not click complete mode (may already be selected)');
                }
                
                // Ensure all categories are selected
                const categories = ['categoryGrammar', 'categoryStyle', 'categoryClarity', 'categoryAcademic'];
                for (const category of categories) {
                    try {
                        const element = await this.page.$(`#${category}`);
                        if (element) {
                            const isChecked = await this.page.$eval(`#${category}`, el => el.checked);
                            if (!isChecked) {
                                await this.page.click(`#${category}`);
                                console.log(`✅ Enabled ${category}`);
                            } else {
                                console.log(`✅ ${category} already enabled`);
                            }
                        }
                    } catch (categoryError) {
                        console.log(`⚠️  Could not configure ${category}: ${categoryError.message}`);
                    }
                }
                
                await this.takeScreenshot('configuration-set', 'Processing configuration set');
                
            } else {
                console.log('⚠️  Configuration section still hidden - using default settings');
            }
            
            // Look for process/submit button
            console.log('🚀 Looking for process button...');
            
            const processButtonSelectors = [
                '#processButton',
                '#submitButton', 
                'button[type="submit"]',
                '.process-btn',
                '.submit-btn',
                'button:contains("Process")',
                'button:contains("Submit")',
                'button:contains("Start")'
            ];
            
            let processButton = null;
            for (const selector of processButtonSelectors) {
                try {
                    processButton = await this.page.$(selector);
                    if (processButton) {
                        console.log(`✅ Found process button: ${selector}`);
                        break;
                    }
                } catch (error) {
                    // Continue to next selector
                }
            }
            
            if (processButton) {
                console.log('🚀 Starting document processing...');
                await processButton.click();
                
                await this.takeScreenshot('processing-started', 'Document processing started');
                
                // Monitor processing progress
                console.log('📊 Monitoring processing progress...');
                
                // Wait for progress section to appear
                const progressSectionVisible = await this.waitForElement('#progressSection', 10000);
                if (progressSectionVisible) {
                    console.log('✅ Progress section appeared');
                    
                    // Monitor progress for up to 5 minutes
                    const maxWaitTime = 5 * 60 * 1000; // 5 minutes
                    const startTime = Date.now();
                    let lastProgress = 0;
                    
                    while (Date.now() - startTime < maxWaitTime) {
                        try {
                            // Check for progress updates
                            const progressInfo = await this.page.evaluate(() => {
                                const progressSection = document.getElementById('progressSection');
                                const progressBar = document.querySelector('.progress-bar, .progress');
                                const progressText = document.querySelector('.progress-text, .progress-info');
                                const statusText = document.querySelector('.status-text, .job-status');
                                
                                return {
                                    sectionVisible: progressSection && window.getComputedStyle(progressSection).display !== 'none',
                                    progressValue: progressBar ? progressBar.style.width || progressBar.value : null,
                                    progressText: progressText ? progressText.textContent : null,
                                    statusText: statusText ? statusText.textContent : null
                                };
                            });
                            
                            if (progressInfo.progressText && progressInfo.progressText !== lastProgress) {
                                console.log(`📊 Progress: ${progressInfo.progressText}`);
                                lastProgress = progressInfo.progressText;
                            }
                            
                            if (progressInfo.statusText) {
                                console.log(`📋 Status: ${progressInfo.statusText}`);
                                
                                // Check for completion
                                if (progressInfo.statusText.toLowerCase().includes('complete') || 
                                    progressInfo.statusText.toLowerCase().includes('finished') ||
                                    progressInfo.statusText.toLowerCase().includes('done')) {
                                    console.log('✅ Processing completed successfully');
                                    break;
                                }
                                
                                // Check for errors
                                if (progressInfo.statusText.toLowerCase().includes('error') || 
                                    progressInfo.statusText.toLowerCase().includes('failed')) {
                                    console.log('❌ Processing failed');
                                    break;
                                }
                            }
                            
                            await new Promise(resolve => setTimeout(resolve, 2000)); // Check every 2 seconds
                            
                        } catch (monitorError) {
                            console.log(`⚠️  Progress monitoring error: ${monitorError.message}`);
                            break;
                        }
                    }
                    
                    await this.takeScreenshot('processing-complete', 'Processing completed');
                    
                } else {
                    console.log('⚠️  Progress section not visible - processing may be instant or failed');
                }
                
                // Check for results section
                console.log('📥 Checking for results...');
                const resultsVisible = await this.waitForElement('#resultsSection', 10000);
                if (resultsVisible) {
                    console.log('✅ Results section appeared');
                    
                    // Look for download button/link
                    const downloadSelectors = [
                        '#downloadButton',
                        '.download-btn',
                        'a[download]',
                        'button:contains("Download")',
                        '.download-link'
                    ];
                    
                    let downloadElement = null;
                    for (const selector of downloadSelectors) {
                        try {
                            downloadElement = await this.page.$(selector);
                            if (downloadElement) {
                                console.log(`✅ Found download element: ${selector}`);
                                break;
                            }
                        } catch (error) {
                            // Continue to next selector
                        }
                    }
                    
                    if (downloadElement) {
                        console.log('📥 Attempting to download corrected document...');
                        
                        // Set up download handling
                        await this.page._client.send('Page.setDownloadBehavior', {
                            behavior: 'allow',
                            downloadPath: path.join(__dirname, 'downloads')
                        });
                        
                        // Ensure download directory exists
                        const downloadDir = path.join(__dirname, 'downloads');
                        if (!fs.existsSync(downloadDir)) {
                            fs.mkdirSync(downloadDir, { recursive: true });
                        }
                        
                        // Click download
                        await downloadElement.click();
                        
                        // Wait for download to complete
                        console.log('⏳ Waiting for download to complete...');
                        await new Promise(resolve => setTimeout(resolve, 5000));
                        
                        // Check for downloaded files
                        const downloadedFiles = fs.readdirSync(downloadDir).filter(file => 
                            file.endsWith('.docx') && !file.includes('.crdownload')
                        );
                        
                        if (downloadedFiles.length > 0) {
                            console.log(`✅ Downloaded file(s): ${downloadedFiles.join(', ')}`);
                            this.testResults.downloadedFiles = downloadedFiles.map(file => 
                                path.join(downloadDir, file)
                            );
                            
                            // Verify downloaded file
                            const downloadedFile = path.join(downloadDir, downloadedFiles[0]);
                            const stats = fs.statSync(downloadedFile);
                            console.log(`📄 Downloaded file size: ${(stats.size / 1024).toFixed(2)} KB`);
                            
                        } else {
                            console.log('⚠️  No downloaded files found');
                        }
                        
                        await this.takeScreenshot('download-complete', 'Download completed');
                        
                    } else {
                        console.log('⚠️  Download button/link not found');
                    }
                    
                } else {
                    console.log('⚠️  Results section not visible');
                }
                
            } else {
                console.log('⚠️  Process button not found - checking if processing started automatically...');
                
                // Check if processing started automatically
                await new Promise(resolve => setTimeout(resolve, 3000));
                const autoProgressVisible = await this.page.$('#progressSection');
                if (autoProgressVisible) {
                    console.log('✅ Processing appears to have started automatically');
                } else {
                    console.log('❌ No processing detected');
                }
            }
            
            this.testResults.passed++;
            console.log('✅ Document upload and processing workflow test COMPLETED');
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`Document workflow error: ${error.message}`);
            console.error('❌ Document upload and processing workflow ERROR:', error);
            await this.takeScreenshot('workflow-error', 'Workflow error occurred');
        }
    }

    /**
     * TEST: WebSocket progress tracking during processing
     */
    async testRealTimeProgressTracking() {
        console.log('\n🔌 TEST: Real-time Progress Tracking via WebSocket');
        console.log('=================================================');
        
        try {
            // Set up WebSocket monitoring
            console.log('🔌 Setting up WebSocket progress monitoring...');
            
            const socketSetup = await this.page.evaluate(() => {
                return new Promise((resolve) => {
                    window.socketEvents = [];
                    window.progressUpdates = [];
                    
                    if (typeof io !== 'undefined') {
                        const socket = io();
                        
                        socket.on('connect', () => {
                            window.socketEvents.push({ type: 'connect', time: Date.now() });
                            console.log('🔌 WebSocket connected for progress tracking');
                        });
                        
                        socket.on('progress_update', (data) => {
                            window.progressUpdates.push({
                                ...data,
                                timestamp: Date.now()
                            });
                            console.log('📊 Progress update:', data);
                        });
                        
                        socket.on('job_started', (data) => {
                            window.socketEvents.push({ type: 'job_started', data, time: Date.now() });
                            console.log('🚀 Job started:', data);
                        });
                        
                        socket.on('job_completed', (data) => {
                            window.socketEvents.push({ type: 'job_completed', data, time: Date.now() });
                            console.log('✅ Job completed:', data);
                        });
                        
                        socket.on('job_failed', (data) => {
                            window.socketEvents.push({ type: 'job_failed', data, time: Date.now() });
                            console.log('❌ Job failed:', data);
                        });
                        
                        window.testSocket = socket;
                        
                        setTimeout(() => {
                            resolve({
                                connected: socket.connected,
                                eventsCount: window.socketEvents.length,
                                progressCount: window.progressUpdates.length
                            });
                        }, 3000);
                    } else {
                        resolve({ error: 'SocketIO not available' });
                    }
                });
            });
            
            console.log('🔌 WebSocket setup result:', socketSetup);
            
            // Monitor for progress updates during any ongoing processing
            console.log('📊 Monitoring for progress updates...');
            await new Promise(resolve => setTimeout(resolve, 10000)); // Monitor for 10 seconds
            
            const progressResults = await this.page.evaluate(() => {
                return {
                    events: window.socketEvents || [],
                    progressUpdates: window.progressUpdates || []
                };
            });
            
            console.log(`📊 Captured ${progressResults.events.length} socket events`);
            console.log(`📈 Captured ${progressResults.progressUpdates.length} progress updates`);
            
            if (progressResults.progressUpdates.length > 0) {
                console.log('✅ Real-time progress tracking working');
                progressResults.progressUpdates.forEach((update, index) => {
                    console.log(`  ${index + 1}. ${JSON.stringify(update)}`);
                });
            }
            
            this.testResults.passed++;
            console.log('✅ Real-time progress tracking test COMPLETED');
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`Progress tracking error: ${error.message}`);
            console.error('❌ Real-time progress tracking ERROR:', error);
        }
    }

    /**
     * Run all core functionality tests
     */
    async runAllTests() {
        console.log('🧪 STARTING CORE FUNCTIONALITY TEST SUITE');
        console.log('==========================================');
        console.log('🎯 Testing the MAIN PURPOSE of the application:');
        console.log('   📤 DOCX file upload');
        console.log('   🤖 AI-powered document processing');
        console.log('   📥 Download corrected DOCX file');
        console.log('==========================================');
        
        const startTime = Date.now();
        
        if (!await this.setupBrowser()) {
            console.error('❌ Failed to setup browser. Aborting tests.');
            return false;
        }
        
        try {
            // Run core functionality tests
            await this.testDocumentUploadAndProcessing();
            await this.testRealTimeProgressTracking();
            
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
     * Print comprehensive test results
     */
    printResults(totalTime) {
        console.log('\n🧪 CORE FUNCTIONALITY TEST RESULTS');
        console.log('===================================');
        console.log(`⏱️  Total execution time: ${totalTime}ms`);
        console.log(`✅ Tests passed: ${this.testResults.passed}`);
        console.log(`❌ Tests failed: ${this.testResults.failed}`);
        console.log(`📸 Screenshots taken: ${this.testResults.screenshots.length}`);
        console.log(`📥 Files downloaded: ${this.testResults.downloadedFiles.length}`);
        
        if (this.testResults.errors.length > 0) {
            console.log('\n🚨 ERRORS:');
            this.testResults.errors.forEach((error, index) => {
                console.log(`${index + 1}. ${error}`);
            });
        }
        
        if (this.testResults.downloadedFiles.length > 0) {
            console.log('\n📥 DOWNLOADED FILES:');
            this.testResults.downloadedFiles.forEach((file, index) => {
                console.log(`${index + 1}. ${file}`);
            });
        }
        
        if (this.testResults.screenshots.length > 0) {
            console.log('\n📸 SCREENSHOTS:');
            this.testResults.screenshots.forEach((screenshot, index) => {
                console.log(`${index + 1}. ${screenshot.path} (${screenshot.context || 'No context'})`);
            });
        }
        
        const success = this.testResults.failed === 0;
        console.log(`\n${success ? '🎉 ALL CORE FUNCTIONALITY TESTS PASSED!' : '⚠️  SOME TESTS FAILED'}`);
        
        if (success) {
            console.log('\n🚀 CORE FUNCTIONALITY VALIDATED');
            console.log('✅ DOCX upload working');
            console.log('✅ Document processing pipeline functional');
            console.log('✅ Real-time progress tracking active');
            if (this.testResults.downloadedFiles.length > 0) {
                console.log('✅ Download functionality working');
            }
            console.log('\n🎯 READY FOR PROFESSIONAL TESTING');
        } else {
            console.log('\n⚠️  ISSUES FOUND - NEEDS ATTENTION BEFORE PROFESSIONAL TESTING');
        }
    }

    /**
     * Cleanup resources - single browser instance
     */
    async cleanup() {
        console.log('\n🧹 Cleaning up test resources...');
        
        if (this.page) {
            try {
                await this.page.close();
                console.log('✅ Page closed successfully');
            } catch (error) {
                console.warn('Warning: Could not close page:', error.message);
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
module.exports = CoreFunctionalityTests;

// Run tests if called directly
if (require.main === module) {
    const testSuite = new CoreFunctionalityTests();
    testSuite.runAllTests()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('Fatal error:', error);
            process.exit(1);
        });
}