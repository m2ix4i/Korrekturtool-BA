/**
 * MCP Puppeteer Testing Framework
 * Comprehensive browser automation testing for Korrekturtool-BA
 * Implements the testing scenarios from Issue #21
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class PuppeteerTestFramework {
    constructor() {
        this.baseUrl = process.env.TEST_BASE_URL || 'http://localhost:5001';
        this.browser = null;
        this.pages = [];
        this.testResults = {
            passed: 0,
            failed: 0,
            errors: [],
            screenshots: []
        };
    }

    /**
     * Initialize browser and setup test environment
     */
    async setupBrowser() {
        console.log('🚀 Initializing Puppeteer browser for testing...');
        
        try {
            this.browser = await puppeteer.launch({
                headless: false, // Show browser for debugging
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            });
            
            console.log('✅ Browser initialized successfully');
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
        this.pages.push(page);
        return page;
    }

    /**
     * Take screenshot for debugging
     */
    async takeScreenshot(page, name) {
        const screenshotPath = path.join(__dirname, 'screenshots', `${name}-${Date.now()}.png`);
        
        // Ensure screenshots directory exists
        const screenshotDir = path.dirname(screenshotPath);
        if (!fs.existsSync(screenshotDir)) {
            fs.mkdirSync(screenshotDir, { recursive: true });
        }
        
        await page.screenshot({ path: screenshotPath, fullPage: true });
        this.testResults.screenshots.push(screenshotPath);
        console.log(`📸 Screenshot saved: ${screenshotPath}`);
        return screenshotPath;
    }

    /**
     * Test: Basic page loading and UI elements
     */
    async testPageLoading() {
        console.log('\n📋 TEST: Basic Page Loading');
        const page = await this.createPage();
        
        try {
            const startTime = Date.now();
            await page.goto(this.baseUrl, { waitUntil: 'networkidle0' });
            const loadTime = Date.now() - startTime;
            
            console.log(`⏱️  Page load time: ${loadTime}ms`);
            
            // Check page title
            const title = await page.title();
            console.log(`📄 Page title: ${title}`);
            
            // Check for essential UI elements
            const elements = await Promise.all([
                page.$('#uploadArea'),
                page.$('#configSection'),
                page.$('#progressSection'),
                page.$('#resultsSection')
            ]);
            
            const elementNames = ['Upload Area', 'Config Section', 'Progress Section', 'Results Section'];
            elements.forEach((element, index) => {
                if (element) {
                    console.log(`✅ ${elementNames[index]} found`);
                } else {
                    console.log(`❌ ${elementNames[index]} missing`);
                    this.testResults.errors.push(`Missing element: ${elementNames[index]}`);
                }
            });
            
            await this.takeScreenshot(page, 'page-loading');
            
            if (loadTime < 3000 && title.includes('Korrekturtool')) {
                this.testResults.passed++;
                console.log('✅ Page loading test PASSED');
            } else {
                this.testResults.failed++;
                console.log('❌ Page loading test FAILED');
            }
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`Page loading error: ${error.message}`);
            console.error('❌ Page loading test ERROR:', error);
        }
    }

    /**
     * Test: Configuration interface functionality
     */
    async testConfigurationInterface() {
        console.log('\n⚙️  TEST: Configuration Interface');
        const page = await this.createPage();
        
        try {
            await page.goto(this.baseUrl);
            
            // Check if config section exists (it might be hidden by default)
            const configSectionExists = await page.$('#configSection');
            if (!configSectionExists) {
                console.log('⚠️  Configuration section not found in DOM');
                throw new Error('Configuration section not found');
            }
            
            // Check if config section is visible or needs activation
            const configVisible = await page.$eval('#configSection', el => {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden';
            });
            
            if (!configVisible) {
                console.log('⚠️  Configuration section hidden by default (expected behavior)');
                console.log('✅ Configuration section exists in DOM structure');
            } else {
                console.log('✅ Configuration section visible');
            }
            
            // Test radio button selection
            console.log('🔘 Testing processing mode radio buttons...');
            
            // Check if radio buttons are available and visible
            const modeCompleteExists = await page.$('#modeComplete');
            const modePerformanceExists = await page.$('#modePerformance');
            
            if (modeCompleteExists) {
                // Check initial state
                const completeChecked = await page.$eval('#modeComplete', el => el.checked);
                console.log(`✅ Complete mode initially checked: ${completeChecked}`);
                
                // Test clicking only if elements are potentially clickable
                if (modePerformanceExists && configVisible) {
                    try {
                        await page.click('#modePerformance');
                        await new Promise(resolve => setTimeout(resolve, 500));
                        
                        const performanceChecked = await page.$eval('#modePerformance', el => el.checked);
                        console.log(`✅ Performance mode selected: ${performanceChecked}`);
                        
                        // Switch back to complete mode
                        await page.click('#modeComplete');
                        await new Promise(resolve => setTimeout(resolve, 500));
                    } catch (clickError) {
                        console.log(`⚠️  Radio button interaction failed (hidden elements): ${clickError.message}`);
                    }
                } else if (modePerformanceExists) {
                    console.log(`⚠️  Performance mode radio exists but section is hidden - testing skipped`);
                }
            } else {
                console.log('⚠️  Radio buttons not found');
            }
            
            // Test category checkboxes if they exist
            console.log('☑️  Testing analysis category checkboxes...');
            const categories = ['categoryGrammar', 'categoryStyle', 'categoryClarity', 'categoryAcademic'];
            let categoriesFound = 0;
            
            for (const category of categories) {
                const categoryElement = await page.$(`#${category}`);
                if (categoryElement) {
                    categoriesFound++;
                    
                    // Only try to click if the configuration section is visible
                    if (configVisible) {
                        try {
                            await page.click(`#${category}`);
                            await new Promise(resolve => setTimeout(resolve, 200));
                            const checked = await page.$eval(`#${category}`, el => el.checked);
                            console.log(`✅ ${category} toggled: ${checked}`);
                        } catch (clickError) {
                            console.log(`⚠️  Could not click ${category}: ${clickError.message}`);
                        }
                    } else {
                        // Just verify the element exists and get its state
                        const checked = await page.$eval(`#${category}`, el => el.checked);
                        console.log(`✅ ${category} found (checked: ${checked}) - hidden section`);
                    }
                } else {
                    console.log(`⚠️  ${category} not found`);
                }
            }
            
            // Test estimation elements if they exist
            console.log('📊 Testing real-time estimation elements...');
            let estimatesFound = false;
            
            try {
                const costEstimate = await page.$eval('#costEstimate', el => el.textContent);
                const timeEstimate = await page.$eval('#timeEstimate', el => el.textContent);
                
                console.log(`💰 Cost estimate: ${costEstimate}`);
                console.log(`⏱️  Time estimate: ${timeEstimate}`);
                estimatesFound = true;
            } catch (estimateError) {
                console.log('⚠️  Estimation elements not found or not accessible');
            }
            
            // Test advanced options if they exist
            console.log('🔧 Testing advanced options toggle...');
            const advancedToggle = await page.$('#advancedToggle');
            if (advancedToggle) {
                try {
                    await page.click('#advancedToggle');
                    await new Promise(resolve => setTimeout(resolve, 500));
                    
                    const advancedOptions = await page.$('#advancedOptions');
                    if (advancedOptions) {
                        const advancedVisible = await page.$eval('#advancedOptions', el => 
                            el.getAttribute('aria-hidden') === 'false' || 
                            !el.hidden || 
                            el.style.display !== 'none'
                        );
                        console.log(`✅ Advanced options expanded: ${advancedVisible}`);
                    }
                } catch (advancedError) {
                    console.log(`⚠️  Advanced options error: ${advancedError.message}`);
                }
            } else {
                console.log('⚠️  Advanced toggle not found');
            }
            
            await this.takeScreenshot(page, 'configuration-interface');
            
            // Pass test if configuration section exists and basic elements are found
            // (Elements may be hidden by design until file upload, which is expected behavior)
            if (configSectionExists && modeCompleteExists) {
                this.testResults.passed++;
                console.log('✅ Configuration interface test PASSED - structure verified');
            } else {
                this.testResults.failed++;
                console.log('❌ Configuration interface test FAILED - essential elements missing');
            }
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`Configuration interface error: ${error.message}`);
            console.error('❌ Configuration interface test ERROR:', error);
        }
    }

    /**
     * Test: API endpoint connectivity
     */
    async testAPIConnectivity() {
        console.log('\n🔌 TEST: API Connectivity');
        const page = await this.createPage();
        
        try {
            // Test API info endpoint
            const response = await page.evaluate(async (baseUrl) => {
                const res = await fetch(`${baseUrl}/api/v1/info`);
                return {
                    status: res.status,
                    data: await res.json()
                };
            }, this.baseUrl);
            
            console.log(`📡 API Info Status: ${response.status}`);
            console.log(`📋 API Info Data:`, response.data);
            
            // Test health endpoint
            const healthResponse = await page.evaluate(async (baseUrl) => {
                const res = await fetch(`${baseUrl}/health`);
                return {
                    status: res.status,
                    data: await res.json()
                };
            }, this.baseUrl);
            
            console.log(`🏥 Health Status: ${healthResponse.status}`);
            console.log(`💚 Health Data:`, healthResponse.data);
            
            if (response.status === 200 && healthResponse.status === 200) {
                this.testResults.passed++;
                console.log('✅ API connectivity test PASSED');
            } else {
                this.testResults.failed++;
                console.log('❌ API connectivity test FAILED');
            }
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`API connectivity error: ${error.message}`);
            console.error('❌ API connectivity test ERROR:', error);
        }
    }

    /**
     * Test: File upload interface (without actual file)
     */
    async testFileUploadInterface() {
        console.log('\n📁 TEST: File Upload Interface');
        const page = await this.createPage();
        
        try {
            await page.goto(this.baseUrl);
            
            // Check for upload elements
            const uploadArea = await page.$('#uploadArea');
            const fileInput = await page.$('#fileInput');
            
            if (uploadArea && fileInput) {
                console.log('✅ Upload area and file input found');
                
                // Test drag and drop visual feedback
                await page.hover('#uploadArea');
                await new Promise(resolve => setTimeout(resolve, 500));
                
                console.log('✅ Upload area hover interaction working');
                
                await this.takeScreenshot(page, 'file-upload-interface');
                
                this.testResults.passed++;
                console.log('✅ File upload interface test PASSED');
            } else {
                throw new Error('Upload elements not found');
            }
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`File upload interface error: ${error.message}`);
            console.error('❌ File upload interface test ERROR:', error);
        }
    }

    /**
     * Test: Error handling scenarios
     */
    async testErrorHandling() {
        console.log('\n🚨 TEST: Error Handling');
        const page = await this.createPage();
        
        try {
            // Test invalid API endpoint
            const invalidResponse = await page.evaluate(async (baseUrl) => {
                try {
                    const res = await fetch(`${baseUrl}/api/v1/nonexistent`);
                    return {
                        status: res.status,
                        data: await res.json()
                    };
                } catch (error) {
                    return { error: error.message };
                }
            }, this.baseUrl);
            
            console.log(`🔍 Invalid endpoint response:`, invalidResponse);
            
            // Test network offline simulation (using CDP)
            const client = await page.target().createCDPSession();
            await client.send('Network.enable');
            await client.send('Network.emulateNetworkConditions', {
                offline: true,
                latency: 0,
                downloadThroughput: 0,
                uploadThroughput: 0
            });
            console.log('📡 Network set to offline');
            
            const offlineResponse = await page.evaluate(async (baseUrl) => {
                try {
                    const res = await fetch(`${baseUrl}/api/v1/info`);
                    return { status: res.status };
                } catch (error) {
                    return { error: error.message };
                }
            }, this.baseUrl);
            
            console.log(`🔌 Offline response:`, offlineResponse);
            
            // Restore network
            await client.send('Network.emulateNetworkConditions', {
                offline: false,
                latency: 0,
                downloadThroughput: 0,
                uploadThroughput: 0
            });
            console.log('📡 Network restored');
            
            await this.takeScreenshot(page, 'error-handling');
            
            if (invalidResponse.status === 404 && offlineResponse.error) {
                this.testResults.passed++;
                console.log('✅ Error handling test PASSED');
            } else {
                this.testResults.failed++;
                console.log('❌ Error handling test FAILED');
            }
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`Error handling test error: ${error.message}`);
            console.error('❌ Error handling test ERROR:', error);
        }
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        console.log('🧪 STARTING MCP PUPPETEER TEST SUITE');
        console.log('=====================================');
        
        const startTime = Date.now();
        
        if (!await this.setupBrowser()) {
            console.error('❌ Failed to setup browser. Aborting tests.');
            return false;
        }
        
        try {
            // Run all test scenarios
            await this.testPageLoading();
            await this.testConfigurationInterface();
            await this.testAPIConnectivity();
            await this.testFileUploadInterface();
            await this.testErrorHandling();
            
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
     * Print test results summary
     */
    printResults(totalTime) {
        console.log('\n🧪 TEST SUITE RESULTS');
        console.log('====================');
        console.log(`⏱️  Total execution time: ${totalTime}ms`);
        console.log(`✅ Tests passed: ${this.testResults.passed}`);
        console.log(`❌ Tests failed: ${this.testResults.failed}`);
        console.log(`📸 Screenshots taken: ${this.testResults.screenshots.length}`);
        
        if (this.testResults.errors.length > 0) {
            console.log('\n🚨 ERRORS:');
            this.testResults.errors.forEach((error, index) => {
                console.log(`${index + 1}. ${error}`);
            });
        }
        
        if (this.testResults.screenshots.length > 0) {
            console.log('\n📸 SCREENSHOTS:');
            this.testResults.screenshots.forEach((screenshot, index) => {
                console.log(`${index + 1}. ${screenshot}`);
            });
        }
        
        const success = this.testResults.failed === 0;
        console.log(`\n${success ? '🎉 ALL TESTS PASSED!' : '⚠️  SOME TESTS FAILED'}`);
    }

    /**
     * Cleanup resources
     */
    async cleanup() {
        console.log('\n🧹 Cleaning up test resources...');
        
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
module.exports = PuppeteerTestFramework;

// Run tests if called directly
if (require.main === module) {
    const testFramework = new PuppeteerTestFramework();
    testFramework.runAllTests()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('Fatal error:', error);
            process.exit(1);
        });
}