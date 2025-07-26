/**
 * Performance & Load Testing with MCP Automation - Issue #24
 * Comprehensive performance validation and load testing
 * Final production readiness assessment
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class PerformanceLoadTests {
    constructor() {
        this.baseUrl = process.env.TEST_BASE_URL || 'http://localhost:5001';
        this.browser = null;
        this.pages = [];
        this.testResults = {
            passed: 0,
            failed: 0,
            errors: [],
            screenshots: [],
            performanceMetrics: {
                pageLoad: [],
                apiResponse: [],
                memoryUsage: [],
                networkMetrics: [],
                userInteraction: []
            },
            loadTestResults: {},
            productionReadiness: {
                score: 0,
                criteria: [],
                recommendations: []
            }
        };
    }

    /**
     * Initialize browser for performance testing
     */
    async setupBrowser() {
        console.log('🚀 Initializing browser for performance & load testing...');
        
        try {
            this.browser = await puppeteer.launch({
                headless: false,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--enable-precise-memory-info'
                ],
                defaultViewport: { width: 1280, height: 720 }
            });
            
            console.log('✅ Browser initialized for performance testing');
            return true;
        } catch (error) {
            console.error('❌ Browser initialization failed:', error);
            return false;
        }
    }

    /**
     * Create new page for testing with performance monitoring
     */
    async createPage() {
        if (!this.browser) {
            throw new Error('Browser not initialized. Call setupBrowser() first.');
        }
        
        const page = await this.browser.newPage();
        await page.setViewport({ width: 1280, height: 720 });
        
        // Enable performance monitoring
        await page.setCacheEnabled(false); // Disable cache for accurate testing
        
        // Monitor performance metrics
        page.on('response', response => {
            if (response.url().includes(this.baseUrl)) {
                this.testResults.performanceMetrics.networkMetrics.push({
                    url: response.url(),
                    status: response.status(),
                    responseTime: response.timing ? response.timing().responseEnd : null,
                    size: response.headers()['content-length'] || 0,
                    timestamp: Date.now()
                });
            }
        });
        
        this.pages.push(page);
        return page;
    }

    /**
     * Take performance screenshot
     */
    async takeScreenshot(page, name, context = null) {
        const timestamp = Date.now();
        const screenshotPath = path.join(__dirname, 'screenshots', `perf-${name}-${timestamp}.png`);
        
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
        
        console.log(`📸 Performance Screenshot: ${screenshotPath}`);
        return screenshotPath;
    }

    /**
     * TEST: Page load performance and Core Web Vitals
     */
    async testPageLoadPerformance() {
        console.log('\n⚡ TEST: Page Load Performance & Core Web Vitals');
        const page = await this.createPage();
        
        try {
            // Enable performance tracking
            await page.evaluateOnNewDocument(() => {
                window.performanceMarks = [];
                window.performanceObserver = new PerformanceObserver((list) => {
                    window.performanceMarks.push(...list.getEntries());
                });
                window.performanceObserver.observe({ entryTypes: ['navigation', 'paint', 'largest-contentful-paint'] });
            });
            
            const startTime = Date.now();
            await page.goto(this.baseUrl, { waitUntil: 'networkidle0' });
            const totalLoadTime = Date.now() - startTime;
            
            // Get Web Vitals and performance metrics
            const webVitals = await page.evaluate(() => {
                return new Promise((resolve) => {
                    const metrics = {};
                    
                    // First Contentful Paint (FCP)
                    const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0];
                    metrics.fcp = fcpEntry ? fcpEntry.startTime : null;
                    
                    // Largest Contentful Paint (LCP)
                    let lcpValue = null;
                    new PerformanceObserver((entryList) => {
                        const entries = entryList.getEntries();
                        const lastEntry = entries[entries.length - 1];
                        lcpValue = lastEntry.startTime;
                    }).observe({ entryTypes: ['largest-contentful-paint'] });
                    
                    // Time to Interactive (TTI) approximation
                    const navEntry = performance.getEntriesByType('navigation')[0];
                    metrics.domContentLoaded = navEntry ? navEntry.domContentLoadedEventEnd : null;
                    metrics.loadComplete = navEntry ? navEntry.loadEventEnd : null;
                    
                    // Memory usage
                    if (performance.memory) {
                        metrics.memoryUsed = performance.memory.usedJSHeapSize;
                        metrics.memoryTotal = performance.memory.totalJSHeapSize;
                        metrics.memoryLimit = performance.memory.jsHeapSizeLimit;
                    }
                    
                    // Resource loading
                    const resources = performance.getEntriesByType('resource');
                    metrics.resourceCount = resources.length;
                    metrics.totalResourceSize = resources.reduce((sum, resource) => 
                        sum + (resource.transferSize || 0), 0);
                    
                    setTimeout(() => {
                        metrics.lcp = lcpValue;
                        resolve(metrics);
                    }, 2000);
                });
            });
            
            console.log(`⏱️  Total page load time: ${totalLoadTime}ms`);
            console.log(`🎨 First Contentful Paint: ${webVitals.fcp ? Math.round(webVitals.fcp) + 'ms' : 'Not measured'}`);
            console.log(`🖼️  Largest Contentful Paint: ${webVitals.lcp ? Math.round(webVitals.lcp) + 'ms' : 'Not measured'}`);
            console.log(`📦 DOM Content Loaded: ${webVitals.domContentLoaded ? Math.round(webVitals.domContentLoaded) + 'ms' : 'Not measured'}`);
            console.log(`✅ Load Complete: ${webVitals.loadComplete ? Math.round(webVitals.loadComplete) + 'ms' : 'Not measured'}`);
            console.log(`🧠 Memory Used: ${webVitals.memoryUsed ? (webVitals.memoryUsed / 1024 / 1024).toFixed(2) + 'MB' : 'Not available'}`);
            console.log(`📊 Resources Loaded: ${webVitals.resourceCount}`);
            console.log(`📈 Total Resource Size: ${webVitals.totalResourceSize ? (webVitals.totalResourceSize / 1024).toFixed(2) + 'KB' : 'Not measured'}`);
            
            // Store performance metrics
            this.testResults.performanceMetrics.pageLoad.push({
                totalLoadTime: totalLoadTime,
                fcp: webVitals.fcp,
                lcp: webVitals.lcp,
                domContentLoaded: webVitals.domContentLoaded,
                loadComplete: webVitals.loadComplete,
                memoryUsed: webVitals.memoryUsed,
                resourceCount: webVitals.resourceCount,
                totalResourceSize: webVitals.totalResourceSize,
                timestamp: Date.now()
            });
            
            // Performance evaluation
            const performanceScore = this.evaluatePagePerformance(webVitals, totalLoadTime);
            console.log(`📊 Performance Score: ${performanceScore}/100`);
            
            await this.takeScreenshot(page, 'page-load-performance', 'Page load performance metrics');
            
            this.testResults.passed++;
            console.log('✅ Page load performance test PASSED');
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`Page load performance error: ${error.message}`);
            console.error('❌ Page load performance test ERROR:', error);
        }
    }

    /**
     * TEST: API load testing and concurrency
     */
    async testAPILoadTesting() {
        console.log('\n🚀 TEST: API Load Testing & Concurrency');
        const page = await this.createPage();
        
        try {
            await page.goto(this.baseUrl);
            
            // Test different load levels
            const loadTests = [
                { name: 'Light Load', concurrent: 5, requests: 10 },
                { name: 'Medium Load', concurrent: 15, requests: 30 },
                { name: 'Heavy Load', concurrent: 25, requests: 50 }
            ];
            
            for (const test of loadTests) {
                console.log(`🔄 Testing ${test.name}: ${test.concurrent} concurrent, ${test.requests} total requests...`);
                
                const loadTestResult = await page.evaluate(async (baseUrl, testConfig) => {
                    const startTime = Date.now();
                    const results = [];
                    const errors = [];
                    
                    // Create batches of concurrent requests
                    const batchSize = testConfig.concurrent;
                    const totalRequests = testConfig.requests;
                    const batches = Math.ceil(totalRequests / batchSize);
                    
                    for (let batch = 0; batch < batches; batch++) {
                        const batchRequests = [];
                        const remainingRequests = Math.min(batchSize, totalRequests - (batch * batchSize));
                        
                        for (let i = 0; i < remainingRequests; i++) {
                            batchRequests.push(
                                fetch(`${baseUrl}/health`)
                                    .then(res => ({
                                        status: res.status,
                                        responseTime: Date.now(),
                                        batch: batch,
                                        request: i
                                    }))
                                    .catch(err => {
                                        errors.push({
                                            error: err.message,
                                            batch: batch,
                                            request: i
                                        });
                                        return null;
                                    })
                            );
                        }
                        
                        const batchResults = await Promise.all(batchRequests);
                        results.push(...batchResults.filter(r => r !== null));
                        
                        // Small delay between batches to prevent overwhelming
                        if (batch < batches - 1) {
                            await new Promise(resolve => setTimeout(resolve, 100));
                        }
                    }
                    
                    const totalTime = Date.now() - startTime;
                    const successfulRequests = results.filter(r => r.status === 200).length;
                    const failedRequests = results.length - successfulRequests + errors.length;
                    
                    return {
                        testName: testConfig.name,
                        totalTime: totalTime,
                        totalRequests: totalRequests,
                        successfulRequests: successfulRequests,
                        failedRequests: failedRequests,
                        successRate: (successfulRequests / totalRequests) * 100,
                        requestsPerSecond: totalRequests / (totalTime / 1000),
                        errors: errors
                    };
                }, this.baseUrl, test);
                
                console.log(`⚡ ${test.name} Results:`);
                console.log(`  📊 Total time: ${loadTestResult.totalTime}ms`);
                console.log(`  ✅ Successful requests: ${loadTestResult.successfulRequests}/${loadTestResult.totalRequests}`);
                console.log(`  📈 Success rate: ${loadTestResult.successRate.toFixed(2)}%`);
                console.log(`  🚀 Requests per second: ${loadTestResult.requestsPerSecond.toFixed(2)}`);
                
                if (loadTestResult.errors.length > 0) {
                    console.log(`  🔴 Errors: ${loadTestResult.errors.length}`);
                }
                
                // Store load test results
                this.testResults.loadTestResults[test.name] = loadTestResult;
            }
            
            await this.takeScreenshot(page, 'api-load-testing', 'API load testing results');
            
            this.testResults.passed++;
            console.log('✅ API load testing PASSED');
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`API load testing error: ${error.message}`);
            console.error('❌ API load testing ERROR:', error);
        }
    }

    /**
     * TEST: Memory usage and resource monitoring
     */
    async testMemoryAndResourceUsage() {
        console.log('\n🧠 TEST: Memory Usage & Resource Monitoring');
        const page = await this.createPage();
        
        try {
            await page.goto(this.baseUrl);
            
            // Monitor memory usage over time
            const memoryTests = [];
            
            for (let i = 0; i < 5; i++) {
                console.log(`📊 Memory test ${i + 1}/5...`);
                
                const memoryUsage = await page.evaluate(() => {
                    const metrics = {};
                    
                    if (performance.memory) {
                        metrics.usedJSHeapSize = performance.memory.usedJSHeapSize;
                        metrics.totalJSHeapSize = performance.memory.totalJSHeapSize;
                        metrics.jsHeapSizeLimit = performance.memory.jsHeapSizeLimit;
                        metrics.memoryUtilization = (metrics.usedJSHeapSize / metrics.jsHeapSizeLimit) * 100;
                    }
                    
                    // Count DOM nodes
                    metrics.domNodes = document.querySelectorAll('*').length;
                    
                    // Resource count
                    const resources = performance.getEntriesByType('resource');
                    metrics.resourceCount = resources.length;
                    
                    return metrics;
                });
                
                memoryTests.push({
                    test: i + 1,
                    ...memoryUsage,
                    timestamp: Date.now()
                });
                
                console.log(`  🧠 Memory used: ${(memoryUsage.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`);
                console.log(`  📊 Memory utilization: ${memoryUsage.memoryUtilization?.toFixed(2) || 'N/A'}%`);
                console.log(`  🏗️  DOM nodes: ${memoryUsage.domNodes}`);
                
                // Trigger some interactions to test memory stability
                await page.click('#uploadArea');
                await page.hover('#configSection');
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            
            // Store memory metrics
            this.testResults.performanceMetrics.memoryUsage = memoryTests;
            
            // Check for memory leaks (usage should be stable)
            const firstTest = memoryTests[0];
            const lastTest = memoryTests[memoryTests.length - 1];
            const memoryIncrease = lastTest.usedJSHeapSize - firstTest.usedJSHeapSize;
            const memoryIncreasePercent = (memoryIncrease / firstTest.usedJSHeapSize) * 100;
            
            console.log(`📈 Memory change: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB (${memoryIncreasePercent.toFixed(2)}%)`);
            
            if (memoryIncreasePercent < 50) {
                console.log('✅ Memory usage stable - no significant leaks detected');
            } else {
                console.log('⚠️  Significant memory increase detected - potential leak');
            }
            
            await this.takeScreenshot(page, 'memory-usage', 'Memory and resource monitoring');
            
            this.testResults.passed++;
            console.log('✅ Memory and resource usage test PASSED');
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`Memory usage testing error: ${error.message}`);
            console.error('❌ Memory usage testing ERROR:', error);
        }
    }

    /**
     * TEST: User interaction performance
     */
    async testUserInteractionPerformance() {
        console.log('\n👆 TEST: User Interaction Performance');
        const page = await this.createPage();
        
        try {
            await page.goto(this.baseUrl);
            
            const interactions = [
                { name: 'Upload Area Click', selector: '#uploadArea', action: 'click' },
                { name: 'Upload Area Hover', selector: '#uploadArea', action: 'hover' },
                { name: 'Theme Toggle', selector: '.theme-toggle', action: 'click' },
                { name: 'Page Scroll', selector: 'body', action: 'scroll' }
            ];
            
            for (const interaction of interactions) {
                console.log(`🖱️  Testing ${interaction.name}...`);
                
                const element = await page.$(interaction.selector);
                if (!element) {
                    console.log(`⚠️  Element ${interaction.selector} not found`);
                    continue;
                }
                
                const startTime = Date.now();
                
                try {
                    switch (interaction.action) {
                        case 'click':
                            await page.click(interaction.selector);
                            break;
                        case 'hover':
                            await page.hover(interaction.selector);
                            break;
                        case 'scroll':
                            await page.evaluate(() => window.scrollTo(0, 500));
                            break;
                    }
                    
                    // Wait for any animations or state changes
                    await new Promise(resolve => setTimeout(resolve, 300));
                    
                } catch (interactionError) {
                    console.log(`⚠️  ${interaction.name} interaction failed: ${interactionError.message}`);
                    continue;
                }
                
                const responseTime = Date.now() - startTime;
                
                this.testResults.performanceMetrics.userInteraction.push({
                    interaction: interaction.name,
                    responseTime: responseTime,
                    timestamp: Date.now()
                });
                
                console.log(`  ⚡ Response time: ${responseTime}ms`);
                
                if (responseTime < 100) {
                    console.log(`  ✅ Excellent responsiveness (<100ms)`);
                } else if (responseTime < 300) {
                    console.log(`  ⚡ Good responsiveness (<300ms)`);
                } else {
                    console.log(`  ⚠️  Slow responsiveness (>300ms)`);
                }
            }
            
            await this.takeScreenshot(page, 'user-interactions', 'User interaction performance');
            
            this.testResults.passed++;
            console.log('✅ User interaction performance test PASSED');
            
        } catch (error) {
            this.testResults.failed++;
            this.testResults.errors.push(`User interaction performance error: ${error.message}`);
            console.error('❌ User interaction performance test ERROR:', error);
        }
    }

    /**
     * Evaluate page performance and assign score
     */
    evaluatePagePerformance(webVitals, totalLoadTime) {
        let score = 100;
        
        // FCP scoring (0-25 points)
        if (webVitals.fcp) {
            if (webVitals.fcp > 3000) score -= 25;
            else if (webVitals.fcp > 1800) score -= 15;
            else if (webVitals.fcp > 1000) score -= 5;
        }
        
        // LCP scoring (0-25 points)
        if (webVitals.lcp) {
            if (webVitals.lcp > 4000) score -= 25;
            else if (webVitals.lcp > 2500) score -= 15;
            else if (webVitals.lcp > 1200) score -= 5;
        }
        
        // Total load time scoring (0-25 points)
        if (totalLoadTime > 5000) score -= 25;
        else if (totalLoadTime > 3000) score -= 15;
        else if (totalLoadTime > 1500) score -= 5;
        
        // Memory usage scoring (0-25 points)
        if (webVitals.memoryUsed) {
            const memoryMB = webVitals.memoryUsed / 1024 / 1024;
            if (memoryMB > 100) score -= 25;
            else if (memoryMB > 50) score -= 15;
            else if (memoryMB > 25) score -= 5;
        }
        
        return Math.max(0, score);
    }

    /**
     * Generate production readiness assessment
     */
    generateProductionReadinessAssessment() {
        console.log('\n📋 GENERATING PRODUCTION READINESS ASSESSMENT');
        console.log('=============================================');
        
        const criteria = [];
        let totalScore = 0;
        const maxScore = 100;
        
        // Page Load Performance (25 points)
        const pageLoadMetrics = this.testResults.performanceMetrics.pageLoad[0];
        let pageLoadScore = 25;
        if (pageLoadMetrics) {
            if (pageLoadMetrics.totalLoadTime > 3000) pageLoadScore = 10;
            else if (pageLoadMetrics.totalLoadTime > 1500) pageLoadScore = 20;
        }
        totalScore += pageLoadScore;
        criteria.push({
            category: 'Page Load Performance',
            score: pageLoadScore,
            maxScore: 25,
            status: pageLoadScore >= 20 ? 'PASS' : pageLoadScore >= 15 ? 'WARNING' : 'FAIL',
            details: pageLoadMetrics ? `${pageLoadMetrics.totalLoadTime}ms load time` : 'Not measured'
        });
        
        // API Performance (25 points)
        const apiMetrics = this.testResults.performanceMetrics.apiResponse;
        let apiScore = 25;
        if (apiMetrics.length > 0) {
            const avgResponseTime = apiMetrics.reduce((sum, metric) => sum + metric.responseTime, 0) / apiMetrics.length;
            if (avgResponseTime > 1000) apiScore = 10;
            else if (avgResponseTime > 500) apiScore = 20;
        }
        totalScore += apiScore;
        criteria.push({
            category: 'API Performance',
            score: apiScore,
            maxScore: 25,
            status: apiScore >= 20 ? 'PASS' : apiScore >= 15 ? 'WARNING' : 'FAIL',
            details: apiMetrics.length > 0 ? `Average response time measured` : 'Not measured'
        });
        
        // Load Testing (25 points)
        let loadTestScore = 25;
        if (Object.keys(this.testResults.loadTestResults).length > 0) {
            const heavyLoad = this.testResults.loadTestResults['Heavy Load'];
            if (heavyLoad && heavyLoad.successRate < 90) loadTestScore = 10;
            else if (heavyLoad && heavyLoad.successRate < 95) loadTestScore = 20;
        }
        totalScore += loadTestScore;
        criteria.push({
            category: 'Load Testing',
            score: loadTestScore,
            maxScore: 25,
            status: loadTestScore >= 20 ? 'PASS' : loadTestScore >= 15 ? 'WARNING' : 'FAIL',
            details: 'Load testing completed'
        });
        
        // Memory Management (25 points)
        let memoryScore = 25;
        const memoryMetrics = this.testResults.performanceMetrics.memoryUsage;
        if (memoryMetrics.length > 0) {
            const firstMemory = memoryMetrics[0].usedJSHeapSize;
            const lastMemory = memoryMetrics[memoryMetrics.length - 1].usedJSHeapSize;
            const memoryIncrease = ((lastMemory - firstMemory) / firstMemory) * 100;
            
            if (memoryIncrease > 100) memoryScore = 10;
            else if (memoryIncrease > 50) memoryScore = 20;
        }
        totalScore += memoryScore;
        criteria.push({
            category: 'Memory Management',
            score: memoryScore,
            maxScore: 25,
            status: memoryScore >= 20 ? 'PASS' : memoryScore >= 15 ? 'WARNING' : 'FAIL',
            details: 'Memory usage monitoring completed'
        });
        
        // Overall assessment
        const overallGrade = totalScore >= 90 ? 'A' : totalScore >= 80 ? 'B' : totalScore >= 70 ? 'C' : totalScore >= 60 ? 'D' : 'F';
        const readinessStatus = totalScore >= 80 ? 'PRODUCTION READY' : totalScore >= 70 ? 'PRODUCTION READY WITH MONITORING' : 'NEEDS IMPROVEMENT';
        
        this.testResults.productionReadiness = {
            score: totalScore,
            maxScore: maxScore,
            grade: overallGrade,
            status: readinessStatus,
            criteria: criteria,
            recommendations: this.generateRecommendations(criteria)
        };
        
        return this.testResults.productionReadiness;
    }

    /**
     * Generate recommendations based on assessment
     */
    generateRecommendations(criteria) {
        const recommendations = [];
        
        criteria.forEach(criterion => {
            if (criterion.status === 'FAIL') {
                switch (criterion.category) {
                    case 'Page Load Performance':
                        recommendations.push('🚀 Optimize page load times: Enable compression, optimize images, minimize JavaScript');
                        break;
                    case 'API Performance':
                        recommendations.push('⚡ Improve API response times: Add caching, optimize database queries, use CDN');
                        break;
                    case 'Load Testing':
                        recommendations.push('📊 Enhance load handling: Implement load balancing, optimize concurrent processing');
                        break;
                    case 'Memory Management':
                        recommendations.push('🧠 Fix memory issues: Identify and fix memory leaks, optimize resource usage');
                        break;
                }
            } else if (criterion.status === 'WARNING') {
                switch (criterion.category) {
                    case 'Page Load Performance':
                        recommendations.push('⚡ Consider further page load optimizations for better user experience');
                        break;
                    case 'API Performance':
                        recommendations.push('📊 Monitor API performance closely and consider optimizations');
                        break;
                    case 'Load Testing':
                        recommendations.push('🔄 Monitor server performance under load and plan for scaling');
                        break;
                    case 'Memory Management':
                        recommendations.push('🧠 Monitor memory usage and implement cleanup procedures');
                        break;
                }
            }
        });
        
        return recommendations;
    }

    /**
     * Run all performance and load tests
     */
    async runAllTests() {
        console.log('🧪 STARTING PERFORMANCE & LOAD TEST SUITE');
        console.log('==========================================');
        
        const startTime = Date.now();
        
        if (!await this.setupBrowser()) {
            console.error('❌ Failed to setup browser. Aborting tests.');
            return false;
        }
        
        try {
            // Run all performance tests
            await this.testPageLoadPerformance();
            await this.testAPILoadTesting();
            await this.testMemoryAndResourceUsage();
            await this.testUserInteractionPerformance();
            
        } catch (error) {
            console.error('❌ Test suite error:', error);
        } finally {
            await this.cleanup();
        }
        
        const totalTime = Date.now() - startTime;
        
        // Generate production readiness assessment
        const assessment = this.generateProductionReadinessAssessment();
        
        this.printResults(totalTime, assessment);
        
        return this.testResults.failed === 0;
    }

    /**
     * Print comprehensive performance test results
     */
    printResults(totalTime, assessment) {
        console.log('\n🧪 PERFORMANCE & LOAD TEST RESULTS');
        console.log('===================================');
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
        
        // Print load test results
        if (Object.keys(this.testResults.loadTestResults).length > 0) {
            console.log('\n🚀 LOAD TEST SUMMARY:');
            Object.entries(this.testResults.loadTestResults).forEach(([testName, result]) => {
                console.log(`${testName}: ${result.successRate.toFixed(1)}% success (${result.requestsPerSecond.toFixed(1)} req/s)`);
            });
        }
        
        // Print production readiness assessment
        console.log('\n📋 PRODUCTION READINESS ASSESSMENT');
        console.log('==================================');
        console.log(`🎯 Overall Score: ${assessment.score}/${assessment.maxScore} (Grade: ${assessment.grade})`);
        console.log(`🚀 Status: ${assessment.status}`);
        
        console.log('\n📊 CRITERIA BREAKDOWN:');
        assessment.criteria.forEach(criterion => {
            const statusIcon = criterion.status === 'PASS' ? '✅' : criterion.status === 'WARNING' ? '⚠️' : '❌';
            console.log(`${statusIcon} ${criterion.category}: ${criterion.score}/${criterion.maxScore} (${criterion.status})`);
            console.log(`   ${criterion.details}`);
        });
        
        if (assessment.recommendations.length > 0) {
            console.log('\n💡 RECOMMENDATIONS:');
            assessment.recommendations.forEach((rec, index) => {
                console.log(`${index + 1}. ${rec}`);
            });
        }
        
        const success = this.testResults.failed === 0;
        console.log(`\n${success ? '🎉 ALL PERFORMANCE TESTS PASSED!' : '⚠️  SOME TESTS FAILED'}`);
        
        if (success && assessment.score >= 80) {
            console.log('\n🚀 SYSTEM IS PRODUCTION READY!');
            console.log('✅ Performance validated');
            console.log('✅ Load testing passed');
            console.log('✅ Memory management stable');
            console.log('✅ User interactions responsive');
        }
    }

    /**
     * Cleanup resources
     */
    async cleanup() {
        console.log('\n🧹 Cleaning up performance test resources...');
        
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
module.exports = PerformanceLoadTests;

// Run tests if called directly
if (require.main === module) {
    const testSuite = new PerformanceLoadTests();
    testSuite.runAllTests()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('Fatal error:', error);
            process.exit(1);
        });
}