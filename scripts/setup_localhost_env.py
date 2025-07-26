#!/usr/bin/env python3
"""
Localhost Environment Setup and Validation Script
Korrekturtool für Wissenschaftliche Arbeiten

This script validates and sets up the complete localhost development environment
for the German Bachelor Thesis Correction Tool web application.

Usage:
    python scripts/setup_localhost_env.py [--fix] [--verbose]
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import importlib.util
from dataclasses import dataclass
from enum import Enum


class ValidationStatus(Enum):
    """Status levels for validation results"""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARNING = "⚠️ WARNING"
    INFO = "ℹ️ INFO"


@dataclass
class ValidationResult:
    """Result of a validation check"""
    component: str
    status: ValidationStatus
    message: str
    details: Optional[str] = None
    fix_command: Optional[str] = None


class LocalhostEnvironmentValidator:
    """Comprehensive localhost environment validator for Korrekturtool"""
    
    def __init__(self, fix_issues: bool = False, verbose: bool = False):
        self.fix_issues = fix_issues
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.results: List[ValidationResult] = []
        
        # Required directories
        self.required_dirs = ['uploads', 'temp', 'outputs', 'web/static', 'web/templates']
        
        # Required Python packages
        self.required_python_packages = [
            'flask', 'flask_cors', 'flask_socketio', 'python_dotenv',
            'google.generativeai', 'docx', 'celery', 'redis', 'sqlalchemy'
        ]
        
        # Required Node.js packages
        self.required_node_packages = ['@modelcontextprotocol/server-puppeteer']
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            print(f"[{level}] {message}")
    
    def add_result(self, result: ValidationResult):
        """Add validation result and log it"""
        self.results.append(result)
        status_symbol = result.status.value.split()[0]
        self.log(f"{status_symbol} {result.component}: {result.message}")
        
        if result.details and self.verbose:
            self.log(f"    Details: {result.details}")
            
        if result.fix_command and result.status == ValidationStatus.FAIL:
            self.log(f"    Fix: {result.fix_command}")
    
    def validate_python_environment(self) -> bool:
        """Validate Python version and virtual environment"""
        self.log("🐍 Validating Python environment...", "INFO")
        
        # Check Python version
        py_version = sys.version_info
        if py_version.major == 3 and py_version.minor >= 9:
            self.add_result(ValidationResult(
                "Python Version",
                ValidationStatus.PASS,
                f"Python {py_version.major}.{py_version.minor}.{py_version.micro}",
                "Meets minimum requirement of Python 3.9+"
            ))
        else:
            self.add_result(ValidationResult(
                "Python Version",
                ValidationStatus.FAIL,
                f"Python {py_version.major}.{py_version.minor}.{py_version.micro} is too old",
                "Requires Python 3.9 or newer",
                "Install Python 3.9+ from https://python.org"
            ))
            return False
        
        # Check virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.add_result(ValidationResult(
                "Virtual Environment",
                ValidationStatus.PASS,
                "Active virtual environment detected",
                f"Virtual env: {sys.prefix}"
            ))
        else:
            self.add_result(ValidationResult(
                "Virtual Environment",
                ValidationStatus.WARNING,
                "No virtual environment detected",
                "Running without virtual environment may cause dependency conflicts",
                "Run: python -m venv venv && source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
            ))
        
        return True
    
    def validate_python_dependencies(self) -> bool:
        """Validate Python package dependencies"""
        self.log("📦 Validating Python dependencies...", "INFO")
        
        # Check if requirements.txt exists
        req_file = self.project_root / "requirements.txt"
        if not req_file.exists():
            self.add_result(ValidationResult(
                "Requirements File",
                ValidationStatus.FAIL,
                "requirements.txt not found",
                f"Expected at: {req_file}",
                "Create requirements.txt with necessary dependencies"
            ))
            return False
        
        self.add_result(ValidationResult(
            "Requirements File",
            ValidationStatus.PASS,
            "requirements.txt found",
            f"Location: {req_file}"
        ))
        
        # Check installed packages
        missing_packages = []
        installed_packages = []
        
        for package in self.required_python_packages:
            try:
                # Handle package name mapping
                import_name = package
                if package == 'google.generativeai':
                    import_name = 'google.generativeai'
                elif package == 'python_dotenv':
                    import_name = 'dotenv'
                elif package == 'docx':
                    import_name = 'docx'
                elif package == 'flask_cors':
                    import_name = 'flask_cors'
                elif package == 'flask_socketio':
                    import_name = 'flask_socketio'
                
                spec = importlib.util.find_spec(import_name)
                if spec is not None:
                    installed_packages.append(package)
                else:
                    missing_packages.append(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.add_result(ValidationResult(
                "Python Dependencies",
                ValidationStatus.FAIL,
                f"Missing {len(missing_packages)} required packages",
                f"Missing: {', '.join(missing_packages)}",
                "pip install -r requirements.txt"
            ))
            return False
        else:
            self.add_result(ValidationResult(
                "Python Dependencies",
                ValidationStatus.PASS,
                f"All {len(installed_packages)} required packages installed",
                f"Installed: {', '.join(installed_packages)}"
            ))
        
        return True
    
    def validate_node_dependencies(self) -> bool:
        """Validate Node.js and package dependencies"""
        self.log("📦 Validating Node.js dependencies...", "INFO")
        
        # Check if Node.js is installed
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                self.add_result(ValidationResult(
                    "Node.js",
                    ValidationStatus.PASS,
                    f"Node.js {node_version} installed",
                    "Node.js available for MCP server dependencies"
                ))
            else:
                raise subprocess.CalledProcessError(result.returncode, 'node')
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            self.add_result(ValidationResult(
                "Node.js",
                ValidationStatus.WARNING,
                "Node.js not found or not accessible",
                "Node.js required for Puppeteer MCP server",
                "Install Node.js from https://nodejs.org"
            ))
            return False
        
        # Check package.json
        package_json = self.project_root / "package.json"
        if not package_json.exists():
            self.add_result(ValidationResult(
                "Package.json",
                ValidationStatus.WARNING,
                "package.json not found",
                "Node.js dependencies may not be properly configured",
                "Run: npm init -y"
            ))
            return False
        
        # Check node_modules
        node_modules = self.project_root / "node_modules"
        if not node_modules.exists():
            self.add_result(ValidationResult(
                "Node Dependencies",
                ValidationStatus.FAIL,
                "node_modules directory not found",
                "Node.js packages not installed",
                "Run: npm install"
            ))
            return False
        
        # Check specific Puppeteer MCP package
        puppeteer_mcp = node_modules / "@modelcontextprotocol" / "server-puppeteer"
        if puppeteer_mcp.exists():
            self.add_result(ValidationResult(
                "Puppeteer MCP Server",
                ValidationStatus.PASS,
                "Puppeteer MCP server package installed",
                f"Location: {puppeteer_mcp}"
            ))
        else:
            self.add_result(ValidationResult(
                "Puppeteer MCP Server",
                ValidationStatus.FAIL,
                "Puppeteer MCP server package not found",
                "Required for browser automation testing",
                "Run: npm install @modelcontextprotocol/server-puppeteer"
            ))
            return False
        
        return True
    
    def validate_configuration(self) -> bool:
        """Validate environment configuration"""
        self.log("⚙️ Validating configuration...", "INFO")
        
        # Check .env file
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if not env_file.exists():
            if env_example.exists():
                self.add_result(ValidationResult(
                    "Environment File",
                    ValidationStatus.FAIL,
                    ".env file not found",
                    ".env.example exists but .env is missing",
                    f"Copy .env.example to .env and configure: cp {env_example} {env_file}"
                ))
            else:
                self.add_result(ValidationResult(
                    "Environment File",
                    ValidationStatus.FAIL,
                    "Neither .env nor .env.example found",
                    "Environment configuration missing",
                    "Create .env file with required configuration"
                ))
            return False
        
        self.add_result(ValidationResult(
            "Environment File",
            ValidationStatus.PASS,
            ".env file found",
            f"Location: {env_file}"
        ))
        
        # Check required environment variables
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        required_vars = [
            'GOOGLE_API_KEY', 'SECRET_KEY', 'FLASK_ENV', 
            'MAX_FILE_SIZE', 'UPLOAD_FOLDER', 'TEMP_FOLDER', 'OUTPUT_FOLDER'
        ]
        
        missing_vars = []
        configured_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if value and value != f"your_{var.lower()}_here":
                configured_vars.append(var)
            else:
                missing_vars.append(var)
        
        if missing_vars:
            self.add_result(ValidationResult(
                "Environment Variables",
                ValidationStatus.FAIL,
                f"Missing or unconfigured variables: {', '.join(missing_vars)}",
                "Required environment variables not properly set",
                f"Configure missing variables in {env_file}"
            ))
            return False
        else:
            self.add_result(ValidationResult(
                "Environment Variables",
                ValidationStatus.PASS,
                f"All {len(configured_vars)} required variables configured",
                f"Configured: {', '.join(configured_vars)}"
            ))
        
        return True
    
    def validate_api_configuration(self) -> bool:
        """Validate Google Gemini API key"""
        self.log("🔑 Validating API configuration...", "INFO")
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key or api_key == 'your_google_api_key_here':
            self.add_result(ValidationResult(
                "Google API Key",
                ValidationStatus.FAIL,
                "Google API key not configured",
                "GOOGLE_API_KEY is missing or using placeholder value",
                "Set GOOGLE_API_KEY in .env file with your actual API key"
            ))
            return False
        
        # Basic validation - check if it looks like a valid API key
        if len(api_key) < 20 or not api_key.startswith(('AIza', 'google')):
            self.add_result(ValidationResult(
                "Google API Key",
                ValidationStatus.WARNING,
                "API key format may be invalid",
                f"Key length: {len(api_key)}, starts with: {api_key[:4]}...",
                "Verify API key format and permissions in Google AI Studio"
            ))
        else:
            self.add_result(ValidationResult(
                "Google API Key",
                ValidationStatus.PASS,
                "API key appears to be properly formatted",
                f"Key length: {len(api_key)}, starts with: {api_key[:4]}..."
            ))
        
        return True
    
    def validate_directory_structure(self) -> bool:
        """Validate required directory structure"""
        self.log("📁 Validating directory structure...", "INFO")
        
        all_exist = True
        for dir_name in self.required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                # Check permissions
                if os.access(dir_path, os.R_OK | os.W_OK):
                    self.add_result(ValidationResult(
                        f"Directory: {dir_name}",
                        ValidationStatus.PASS,
                        "Exists with proper permissions",
                        f"Path: {dir_path}"
                    ))
                else:
                    self.add_result(ValidationResult(
                        f"Directory: {dir_name}",
                        ValidationStatus.WARNING,
                        "Exists but permissions may be insufficient",
                        f"Path: {dir_path}",
                        f"Fix permissions: chmod 755 {dir_path}"
                    ))
            else:
                all_exist = False
                self.add_result(ValidationResult(
                    f"Directory: {dir_name}",
                    ValidationStatus.FAIL,
                    "Directory missing",
                    f"Expected path: {dir_path}",
                    f"Create directory: mkdir -p {dir_path}"
                ))
                
                if self.fix_issues:
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        self.log(f"✅ Created directory: {dir_path}")
                    except OSError as e:
                        self.log(f"❌ Failed to create directory {dir_path}: {e}")
        
        return all_exist
    
    def validate_service_connectivity(self) -> bool:
        """Validate service connectivity and requirements"""
        self.log("🔌 Validating service connectivity...", "INFO")
        
        # Check if Flask can import properly
        try:
            import flask
            self.add_result(ValidationResult(
                "Flask Import",
                ValidationStatus.PASS,
                f"Flask {flask.__version__} imports successfully",
                "Web server framework ready"
            ))
        except ImportError as e:
            self.add_result(ValidationResult(
                "Flask Import",
                ValidationStatus.FAIL,
                "Flask import failed",
                str(e),
                "pip install flask"
            ))
            return False
        
        # Check SocketIO
        try:
            import flask_socketio
            version = getattr(flask_socketio, '__version__', 'unknown')
            self.add_result(ValidationResult(
                "SocketIO Import",
                ValidationStatus.PASS,
                f"Flask-SocketIO {version} imports successfully",
                "WebSocket support ready"
            ))
        except ImportError as e:
            self.add_result(ValidationResult(
                "SocketIO Import",
                ValidationStatus.FAIL,
                "Flask-SocketIO import failed",
                str(e),
                "pip install flask-socketio"
            ))
            return False
        
        # Check if port 5000 is available
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', 5000))
                self.add_result(ValidationResult(
                    "Port Availability",
                    ValidationStatus.PASS,
                    "Port 5000 is available",
                    "Default Flask port ready for use"
                ))
        except OSError:
            self.add_result(ValidationResult(
                "Port Availability",
                ValidationStatus.WARNING,
                "Port 5000 is in use",
                "Another service may be using the default port",
                "Use PORT environment variable to specify different port"
            ))
        
        return True
    
    def generate_setup_report(self) -> Dict:
        """Generate comprehensive setup report"""
        self.log("📊 Generating setup report...", "INFO")
        
        # Count results by status
        status_counts = {}
        for status in ValidationStatus:
            status_counts[status.name] = len([r for r in self.results if r.status == status])
        
        # Determine overall status
        if status_counts['FAIL'] > 0:
            overall_status = "FAILED"
            overall_message = f"Environment setup failed with {status_counts['FAIL']} critical issues"
        elif status_counts['WARNING'] > 0:
            overall_status = "WARNING" 
            overall_message = f"Environment setup completed with {status_counts['WARNING']} warnings"
        else:
            overall_status = "SUCCESS"
            overall_message = "Environment setup completed successfully"
        
        report = {
            "overall_status": overall_status,
            "overall_message": overall_message,
            "timestamp": str(os.popen('date').read().strip()),
            "platform": platform.platform(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "project_root": str(self.project_root),
            "status_summary": status_counts,
            "total_checks": len(self.results),
            "results": [
                {
                    "component": r.component,
                    "status": r.status.name,
                    "message": r.message,
                    "details": r.details,
                    "fix_command": r.fix_command
                }
                for r in self.results
            ]
        }
        
        return report
    
    def run_validation(self) -> bool:
        """Run complete validation suite"""
        print("🚀 Starting Localhost Environment Validation")
        print(f"Project Root: {self.project_root}")
        print(f"Fix Issues: {self.fix_issues}")
        print(f"Verbose: {self.verbose}")
        print("-" * 60)
        
        # Run all validation checks
        checks = [
            self.validate_python_environment,
            self.validate_python_dependencies,
            self.validate_node_dependencies,
            self.validate_configuration,
            self.validate_api_configuration,
            self.validate_directory_structure,
            self.validate_service_connectivity
        ]
        
        success = True
        for check in checks:
            try:
                if not check():
                    success = False
            except Exception as e:
                self.add_result(ValidationResult(
                    f"Check: {check.__name__}",
                    ValidationStatus.FAIL,
                    f"Validation check failed: {str(e)}",
                    f"Exception during {check.__name__}",
                    "Review error and fix underlying issue"
                ))
                success = False
        
        # Generate and display report
        report = self.generate_setup_report()
        
        print("-" * 60)
        print("📊 VALIDATION SUMMARY")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Overall Message: {report['overall_message']}")
        print(f"Total Checks: {report['total_checks']}")
        
        for status, count in report['status_summary'].items():
            if count > 0:
                status_obj = ValidationStatus[status]
                print(f"{status_obj.value}: {count}")
        
        if not success:
            print("\n❌ SETUP FAILED - Please fix the issues above")
            print("💡 Run with --fix flag to automatically fix some issues")
            print("💡 Run with --verbose flag for detailed information")
        else:
            print("\n✅ SETUP SUCCESSFUL - Environment ready for development!")
        
        # Save report to file
        report_file = self.project_root / "localhost_setup_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return success


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate and setup localhost development environment"
    )
    parser.add_argument(
        "--fix", 
        action="store_true", 
        help="Automatically fix issues where possible"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    validator = LocalhostEnvironmentValidator(
        fix_issues=args.fix,
        verbose=args.verbose
    )
    
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()