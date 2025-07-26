#!/usr/bin/env python3
"""
Service Startup Validation Script
Korrekturtool für Wissenschaftliche Arbeiten

This script validates that all services start correctly and are functioning properly
for the localhost development environment.

Usage:
    python scripts/validate_startup.py [--port PORT] [--timeout TIMEOUT] [--verbose]
"""

import os
import sys
import time
import json
import socket
import requests
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import signal


class ValidationStatus(Enum):
    """Status levels for validation results"""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARNING = "⚠️ WARNING"
    INFO = "ℹ️ INFO"


@dataclass
class ServiceValidationResult:
    """Result of a service validation check"""
    service: str
    status: ValidationStatus
    message: str
    details: Optional[str] = None
    response_time_ms: Optional[float] = None
    fix_suggestion: Optional[str] = None


class FlaskServerProcess:
    """Manages Flask server process for testing"""
    
    def __init__(self, port: int = 5000, timeout: int = 30):
        self.port = port
        self.timeout = timeout
        self.process = None
        self.project_root = Path(__file__).parent.parent
        
    def start_server(self) -> bool:
        """Start Flask server in background process"""
        try:
            # Change to project directory
            env = os.environ.copy()
            env['PORT'] = str(self.port)
            env['FLASK_ENV'] = 'development'
            
            # Start server process
            cmd = [sys.executable, 'web/app.py']
            self.process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self.is_server_running():
                    return True
                time.sleep(0.5)
            
            return False
            
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
    
    def is_server_running(self) -> bool:
        """Check if server is responding"""
        try:
            response = requests.get(
                f'http://localhost:{self.port}/api/v1/info',
                timeout=2
            )
            return response.status_code == 200
        except:
            return False
    
    def stop_server(self):
        """Stop the Flask server process"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            finally:
                self.process = None
    
    def get_server_logs(self) -> Tuple[str, str]:
        """Get stdout and stderr from server process"""
        if self.process:
            stdout, stderr = self.process.communicate(timeout=1)
            return stdout, stderr
        return "", ""


class ServiceStartupValidator:
    """Validates Flask server startup and service functionality"""
    
    def __init__(self, port: int = 5000, timeout: int = 30, verbose: bool = False):
        self.port = port
        self.timeout = timeout
        self.verbose = verbose
        self.base_url = f'http://localhost:{port}'
        self.results: List[ServiceValidationResult] = []
        self.server_process = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with level"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def add_result(self, result: ServiceValidationResult):
        """Add validation result and log it"""
        self.results.append(result)
        status_symbol = result.status.value.split()[0]
        message = f"{status_symbol} {result.service}: {result.message}"
        
        if result.response_time_ms:
            message += f" ({result.response_time_ms:.1f}ms)"
            
        self.log(message)
        
        if result.details and self.verbose:
            self.log(f"    Details: {result.details}")
            
        if result.fix_suggestion and result.status == ValidationStatus.FAIL:
            self.log(f"    Fix: {result.fix_suggestion}")
    
    def validate_port_availability(self) -> bool:
        """Check if the target port is available"""
        self.log(f"🔍 Checking port {self.port} availability...", "INFO")
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', self.port))
                self.add_result(ServiceValidationResult(
                    "Port Availability",
                    ValidationStatus.PASS,
                    f"Port {self.port} is available",
                    f"Ready to start Flask server on localhost:{self.port}"
                ))
                return True
        except OSError as e:
            if e.errno == 98:  # Address already in use
                # Check if it might be our own server
                if self.test_api_endpoint('/api/v1/info'):
                    self.add_result(ServiceValidationResult(
                        "Port Availability",
                        ValidationStatus.WARNING,
                        f"Port {self.port} in use but server appears to be running",
                        "Server may already be started",
                        fix_suggestion="Use different port or stop existing server"
                    ))
                    return True
                else:
                    self.add_result(ServiceValidationResult(
                        "Port Availability",
                        ValidationStatus.FAIL,
                        f"Port {self.port} is occupied by another service",
                        str(e),
                        f"Use different port: export PORT=5001 or stop service on port {self.port}"
                    ))
                    return False
            else:
                self.add_result(ServiceValidationResult(
                    "Port Availability", 
                    ValidationStatus.FAIL,
                    f"Port check failed: {e}",
                    fix_suggestion="Check network configuration"
                ))
                return False
    
    def start_test_server(self) -> bool:
        """Start Flask server for testing"""
        self.log(f"🚀 Starting Flask server on port {self.port}...", "INFO")
        
        self.server_process = FlaskServerProcess(self.port, self.timeout)
        
        start_time = time.time()
        if self.server_process.start_server():
            startup_time = (time.time() - start_time) * 1000
            self.add_result(ServiceValidationResult(
                "Server Startup",
                ValidationStatus.PASS,
                "Flask server started successfully",
                f"Server is responding on localhost:{self.port}",
                startup_time
            ))
            return True
        else:
            self.add_result(ServiceValidationResult(
                "Server Startup",
                ValidationStatus.FAIL,
                f"Flask server failed to start within {self.timeout} seconds",
                "Check server logs for errors",
                fix_suggestion="Run 'python web/app.py' manually to see detailed errors"
            ))
            return False
    
    def test_api_endpoint(self, endpoint: str, expected_status: int = 200) -> bool:
        """Test a specific API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == expected_status:
                self.add_result(ServiceValidationResult(
                    f"API: {endpoint}",
                    ValidationStatus.PASS,
                    f"Endpoint responding correctly (status {response.status_code})",
                    f"Content-Type: {response.headers.get('Content-Type', 'unknown')}",
                    response_time
                ))
                return True
            else:
                self.add_result(ServiceValidationResult(
                    f"API: {endpoint}",
                    ValidationStatus.FAIL,
                    f"Unexpected status code {response.status_code} (expected {expected_status})",
                    f"Response: {response.text[:200]}...",
                    response_time,
                    "Check API endpoint implementation"
                ))
                return False
                
        except requests.exceptions.RequestException as e:
            self.add_result(ServiceValidationResult(
                f"API: {endpoint}",
                ValidationStatus.FAIL,
                f"Request failed: {str(e)[:100]}",
                fix_suggestion="Ensure server is running and endpoint exists"
            ))
            return False
    
    def validate_static_files(self) -> bool:
        """Test static file serving"""
        self.log("📁 Testing static file serving...", "INFO")
        
        static_files = [
            '/static/css/main.css',
            '/static/js/app.js',
            '/static/index.html'
        ]
        
        all_passed = True
        for file_path in static_files:
            url = f"{self.base_url}{file_path}"
            try:
                start_time = time.time()
                response = requests.get(url, timeout=5)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    self.add_result(ServiceValidationResult(
                        f"Static: {file_path}",
                        ValidationStatus.PASS,
                        f"File served correctly ({len(response.content)} bytes)",
                        f"Content-Type: {content_type}",
                        response_time
                    ))
                else:
                    all_passed = False
                    self.add_result(ServiceValidationResult(
                        f"Static: {file_path}",
                        ValidationStatus.FAIL,
                        f"File not found (status {response.status_code})",
                        response_time=response_time,
                        fix_suggestion="Check if static files exist and are properly configured"
                    ))
                    
            except requests.exceptions.RequestException as e:
                all_passed = False
                self.add_result(ServiceValidationResult(
                    f"Static: {file_path}",
                    ValidationStatus.FAIL,
                    f"Request failed: {str(e)[:100]}",
                    fix_suggestion="Check static file configuration"
                ))
        
        return all_passed
    
    def validate_api_endpoints(self) -> bool:
        """Test all critical API endpoints"""
        self.log("🔗 Testing API endpoints...", "INFO")
        
        endpoints = [
            ('/api/v1/info', 200),
            ('/api/v1/health', 200),  # May return 503 if unhealthy, but should respond
            ('/api/v1/upload/info', 200)
        ]
        
        all_passed = True
        for endpoint, expected_status in endpoints:
            # Special handling for health endpoint
            if endpoint == '/api/v1/health':
                # Health endpoint may return 503 but should still respond
                if not self.test_health_endpoint():
                    all_passed = False
            else:
                if not self.test_api_endpoint(endpoint, expected_status):
                    all_passed = False
        
        return all_passed
    
    def test_health_endpoint(self) -> bool:
        """Test health endpoint with special handling"""
        endpoint = '/api/v1/health'
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            # Health endpoint should respond, status code indicates health
            if response.status_code in [200, 503]:
                try:
                    health_data = response.json()
                    overall_status = health_data.get('overall_status', 'unknown')
                    
                    if response.status_code == 200 and overall_status == 'healthy':
                        status = ValidationStatus.PASS
                        message = "Health endpoint reports system healthy"
                    elif response.status_code == 200 and overall_status == 'degraded':
                        status = ValidationStatus.WARNING
                        message = "Health endpoint reports system degraded"
                    else:
                        status = ValidationStatus.WARNING
                        message = f"Health endpoint reports system {overall_status}"
                    
                    self.add_result(ServiceValidationResult(
                        "API: /api/v1/health",
                        status,
                        message,
                        f"Status: {overall_status}, Checks: {health_data.get('summary', {}).get('total_checks', 0)}",
                        response_time
                    ))
                    return True
                    
                except (ValueError, KeyError) as e:
                    self.add_result(ServiceValidationResult(
                        "API: /api/v1/health",
                        ValidationStatus.WARNING,
                        "Health endpoint responded but JSON parsing failed",
                        str(e),
                        response_time
                    ))
                    return True
            else:
                self.add_result(ServiceValidationResult(
                    "API: /api/v1/health",
                    ValidationStatus.FAIL,
                    f"Unexpected status code {response.status_code}",
                    response.text[:200],
                    response_time
                ))
                return False
                
        except requests.exceptions.RequestException as e:
            self.add_result(ServiceValidationResult(
                "API: /api/v1/health",
                ValidationStatus.FAIL,
                f"Health check request failed: {str(e)[:100]}",
                fix_suggestion="Check if server is running and health module is properly configured"
            ))
            return False
    
    def validate_cors_headers(self) -> bool:
        """Test CORS configuration"""
        self.log("🌐 Testing CORS configuration...", "INFO")
        
        url = f"{self.base_url}/api/v1/info"
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET'
        }
        
        try:
            response = requests.options(url, headers=headers, timeout=5)
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if any(cors_headers.values()):
                self.add_result(ServiceValidationResult(
                    "CORS Configuration",
                    ValidationStatus.PASS,
                    "CORS headers present",
                    f"Headers: {cors_headers}"
                ))
                return True
            else:
                self.add_result(ServiceValidationResult(
                    "CORS Configuration",
                    ValidationStatus.WARNING,
                    "No CORS headers found",
                    "May cause issues with frontend connections",
                    fix_suggestion="Check Flask-CORS configuration"
                ))
                return False
                
        except requests.exceptions.RequestException as e:
            self.add_result(ServiceValidationResult(
                "CORS Configuration",
                ValidationStatus.WARNING,
                f"CORS test failed: {str(e)[:100]}",
                fix_suggestion="Manual CORS testing recommended"
            ))
            return False
    
    def cleanup(self):
        """Clean up test server and resources"""
        if self.server_process:
            self.server_process.stop_server()
            self.server_process = None
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        # Count results by status
        status_counts = {}
        for status in ValidationStatus:
            status_counts[status.name] = len([r for r in self.results if r.status == status])
        
        # Calculate performance metrics
        response_times = [r.response_time_ms for r in self.results if r.response_time_ms is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Determine overall status
        if status_counts['FAIL'] > 0:
            overall_status = "FAILED"
            overall_message = f"Service validation failed with {status_counts['FAIL']} critical issues"
        elif status_counts['WARNING'] > 0:
            overall_status = "WARNING"
            overall_message = f"Service validation completed with {status_counts['WARNING']} warnings"
        else:
            overall_status = "SUCCESS"
            overall_message = "All services validated successfully"
        
        report = {
            "overall_status": overall_status,
            "overall_message": overall_message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "server_port": self.port,
            "validation_timeout": self.timeout,
            "status_summary": status_counts,
            "performance": {
                "total_checks": len(self.results),
                "average_response_time_ms": round(avg_response_time, 2),
                "fastest_response_ms": min(response_times) if response_times else None,
                "slowest_response_ms": max(response_times) if response_times else None
            },
            "results": [
                {
                    "service": r.service,
                    "status": r.status.name,
                    "message": r.message,
                    "details": r.details,
                    "response_time_ms": r.response_time_ms,
                    "fix_suggestion": r.fix_suggestion
                }
                for r in self.results
            ]
        }
        
        return report
    
    def run_validation(self) -> bool:
        """Run complete service startup validation"""
        print("🚀 Starting Service Startup Validation")
        print(f"Target URL: {self.base_url}")
        print(f"Timeout: {self.timeout} seconds")
        print(f"Verbose: {self.verbose}")
        print("-" * 60)
        
        success = True
        
        try:
            # Step 1: Check port availability
            if not self.validate_port_availability():
                success = False
                # Try to continue if server might already be running
                if not self.test_api_endpoint('/api/v1/info'):
                    print("❌ Cannot proceed - port unavailable and no server responding")
                    return False
                else:
                    print("⚠️ Continuing with existing server...")
            
            # Step 2: Start server if needed
            if not self.test_api_endpoint('/api/v1/info'):
                if not self.start_test_server():
                    success = False
                    print("❌ Cannot proceed - server startup failed")
                    return False
            
            # Step 3: Validate API endpoints
            if not self.validate_api_endpoints():
                success = False
            
            # Step 4: Validate static files
            if not self.validate_static_files():
                success = False
            
            # Step 5: Test CORS configuration
            if not self.validate_cors_headers():
                # CORS is not critical for basic functionality
                pass
            
        except KeyboardInterrupt:
            print("\n⚠️ Validation interrupted by user")
            success = False
        except Exception as e:
            print(f"❌ Unexpected error during validation: {e}")
            success = False
        finally:
            self.cleanup()
        
        # Generate and display report
        report = self.generate_validation_report()
        
        print("-" * 60)
        print("📊 VALIDATION SUMMARY")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Overall Message: {report['overall_message']}")
        print(f"Total Checks: {report['performance']['total_checks']}")
        print(f"Average Response Time: {report['performance']['average_response_time_ms']:.1f}ms")
        
        for status, count in report['status_summary'].items():
            if count > 0:
                status_obj = ValidationStatus[status]
                print(f"{status_obj.value}: {count}")
        
        if success:
            print("\n✅ SERVICE VALIDATION SUCCESSFUL - All services are operational!")
            print(f"🌐 Server accessible at: {self.base_url}")
            print("💡 Ready for development and testing")
        else:
            print("\n❌ SERVICE VALIDATION FAILED - Issues found")
            print("💡 Review the results above and fix the issues")
            print("💡 Run with --verbose flag for detailed information")
        
        # Save report to file
        project_root = Path(__file__).parent.parent
        report_file = project_root / "service_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return success


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate Flask server startup and service functionality"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv('PORT', 5000)),
        help="Port to test Flask server on (default: from PORT env var or 5000)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout for server startup in seconds (default: 30)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    validator = ServiceStartupValidator(
        port=args.port,
        timeout=args.timeout,
        verbose=args.verbose
    )
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\n🛑 Shutting down validation...")
        validator.cleanup()
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()