/**
 * Processing Validation Test - Click Process Button and Monitor Backend
 * Tests what happens when we actually click "Korrektur starten" button
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class ProcessingValidationTest {
    constructor() {
        this.baseUrl = process.env.TEST_BASE_URL || 'http://localhost:5001';
        this.browser = null;
        this.page = null;
        this.testDocumentPath = '/Users/max/Downloads/Volltext_BA_Max Thomsen.docx';
    }

    async setupBrowser() {
        console.log('🚀 Setting up browser for processing validation...');
        
        if (!fs.existsSync(this.testDocumentPath)) {
            throw new Error(`Test document not found: ${this.testDocumentPath}`);
        }

        this.browser = await puppeteer.launch({
            headless: false,
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
            defaultViewport: { width: 1280, height: 720 }
        });

        this.page = await this.browser.newPage();
        
        // Monitor network requests
        await this.page.setRequestInterception(true);
        this.page.on('request', request => {
            if (request.url().includes('/api/') || request.url().includes('/upload') || request.url().includes('/process')) {
                console.log(`📡 API Request: ${request.method()} ${request.url()}`);
            }
            request.continue();
        });

        this.page.on('response', response => {
            if (response.url().includes('/api/') || response.url().includes('/upload') || response.url().includes('/process')) {
                console.log(`📨 API Response: ${response.status()} ${response.url()}`);
            }
        });

        return true;
    }

    async testProcessingClick() {
        console.log('\n🎯 TESTING: Click Process Button and Monitor Backend Response');
        console.log('===========================================================');

        try {
            // Navigate and upload file (same as before)
            await this.page.goto(this.baseUrl, { waitUntil: 'networkidle0' });
            
            // Upload file
            const fileInput = await this.page.$('#fileInput');
            await fileInput.uploadFile(this.testDocumentPath);
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            console.log('✅ File uploaded, looking for process button...');
            
            // Wait for and click the process button
            const processButton = await this.page.waitForSelector('button:contains("Korrektur starten"), #processButton, button[type="submit"]', {
                visible: true,
                timeout: 10000
            });
            
            if (processButton) {
                console.log('🚀 Found process button, clicking...');
                
                // Set up monitoring for any API calls or redirects
                const responsePromise = new Promise((resolve) => {
                    const responses = [];
                    this.page.on('response', (response) => {
                        if (response.url().includes('/api/') || response.url().includes('/upload') || response.url().includes('/process')) {
                            responses.push({
                                url: response.url(),
                                status: response.status(),
                                timestamp: Date.now()
                            });
                        }
                    });
                    
                    setTimeout(() => resolve(responses), 15000); // Monitor for 15 seconds
                });
                
                // Click the process button
                await processButton.click();
                console.log('✅ Process button clicked!');
                
                // Wait and monitor responses
                console.log('📊 Monitoring backend responses for 15 seconds...');
                const responses = await responsePromise;
                
                if (responses.length > 0) {
                    console.log('📡 API Responses detected:');
                    responses.forEach((resp, index) => {
                        console.log(`  ${index + 1}. ${resp.status} ${resp.url}`);
                    });
                } else {
                    console.log('⚠️  No API responses detected - checking page changes...');
                }
                
                // Check what happened to the page
                const currentUrl = this.page.url();
                console.log(`📍 Current URL: ${currentUrl}`);
                
                // Look for any progress indicators, error messages, or status changes
                const pageStatus = await this.page.evaluate(() => {
                    const progressSection = document.getElementById('progressSection');
                    const resultsSection = document.getElementById('resultsSection');
                    const errorMessage = document.querySelector('.error, .alert-danger, .error-message');
                    const successMessage = document.querySelector('.success, .alert-success, .success-message');
                    
                    return {
                        progressVisible: progressSection && window.getComputedStyle(progressSection).display !== 'none',
                        resultsVisible: resultsSection && window.getComputedStyle(resultsSection).display !== 'none',
                        hasError: errorMessage ? errorMessage.textContent : null,
                        hasSuccess: successMessage ? successMessage.textContent : null,
                        bodyText: document.body.innerText.substring(0, 500) // First 500 chars
                    };
                });
                
                console.log('📋 Page Status:');
                console.log(`  Progress visible: ${pageStatus.progressVisible}`);
                console.log(`  Results visible: ${pageStatus.resultsVisible}`);
                if (pageStatus.hasError) console.log(`  Error: ${pageStatus.hasError}`);
                if (pageStatus.hasSuccess) console.log(`  Success: ${pageStatus.hasSuccess}`);
                
                // Take final screenshot
                await this.page.screenshot({ 
                    path: '/Users/max/Korrekturtool-BA/tests/mcp/screenshots/processing-clicked.png',
                    fullPage: true 
                });
                console.log('📸 Screenshot saved: processing-clicked.png');
                
                // Check server logs by looking at console
                console.log('\n📋 Page Content Analysis:');
                if (pageStatus.bodyText.includes('error') || pageStatus.bodyText.includes('Error')) {
                    console.log('❌ Error detected in page content');
                } else if (pageStatus.bodyText.includes('processing') || pageStatus.bodyText.includes('progress')) {
                    console.log('🔄 Processing detected in page content');
                } else if (pageStatus.bodyText.includes('complete') || pageStatus.bodyText.includes('finished')) {
                    console.log('✅ Completion detected in page content');
                } else {
                    console.log('⚠️  No clear status detected');
                }
                
                return true;
            } else {
                console.log('❌ Process button not found');
                return false;
            }
            
        } catch (error) {
            console.error('❌ Processing validation error:', error);
            return false;
        }
    }

    async cleanup() {
        if (this.page) await this.page.close();
        if (this.browser) await this.browser.close();
    }

    async run() {
        try {
            await this.setupBrowser();
            const success = await this.testProcessingClick();
            console.log(`\n${success ? '✅ Processing validation completed' : '❌ Processing validation failed'}`);
            return success;
        } finally {
            await this.cleanup();
        }
    }
}

// Run if called directly
if (require.main === module) {
    const test = new ProcessingValidationTest();
    test.run().then(success => {
        process.exit(success ? 0 : 1);
    }).catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

module.exports = ProcessingValidationTest;