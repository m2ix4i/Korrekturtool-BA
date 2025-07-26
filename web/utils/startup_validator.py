"""
Startup validation utilities for Flask application
Validates environment and configuration before server startup
"""

import os
import sys
import socket
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class StartupValidationError(Exception):
    """Custom exception for startup validation failures"""
    def __init__(self, message: str, fix_suggestion: str = None):
        self.message = message
        self.fix_suggestion = fix_suggestion
        super().__init__(self.message)


class StartupValidator:
    """Validates Flask application startup requirements"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.errors: List[Tuple[str, str]] = []  # (error, fix_suggestion)
        self.warnings: List[Tuple[str, str]] = []  # (warning, suggestion)
        
        # Load environment variables
        load_dotenv(self.project_root / '.env')
    
    def add_error(self, message: str, fix_suggestion: str = None):
        """Add a critical error that prevents startup"""
        self.errors.append((message, fix_suggestion))
        logger.error(f"Startup Error: {message}")
        if fix_suggestion:
            logger.error(f"Fix: {fix_suggestion}")
    
    def add_warning(self, message: str, suggestion: str = None):
        """Add a warning that doesn't prevent startup"""
        self.warnings.append((message, suggestion))
        logger.warning(f"Startup Warning: {message}")
        if suggestion:
            logger.warning(f"Suggestion: {suggestion}")
    
    def validate_environment_variables(self) -> bool:
        """Validate required environment variables"""
        required_vars = [
            'SECRET_KEY',
            'FLASK_ENV', 
            'MAX_FILE_SIZE',
            'UPLOAD_FOLDER',
            'TEMP_FOLDER',
            'OUTPUT_FOLDER'
        ]
        
        optional_vars = [
            'GOOGLE_API_KEY',
            'REDIS_URL',
            'DATABASE_URL'
        ]
        
        success = True
        
        # Check required variables
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                self.add_error(
                    f"Required environment variable {var} is not set",
                    f"Set {var} in your .env file"
                )
                success = False
            elif value.startswith('your_') and value.endswith('_here'):
                self.add_error(
                    f"Environment variable {var} is using placeholder value: {value}",
                    f"Replace the placeholder with actual value in .env file"
                )
                success = False
        
        # Check optional but important variables
        for var in optional_vars:
            value = os.getenv(var)
            if not value or (value.startswith('your_') and value.endswith('_here')):
                if var == 'GOOGLE_API_KEY':
                    self.add_warning(
                        f"Google API key not configured - AI processing will fail",
                        "Set GOOGLE_API_KEY in .env file for full functionality"
                    )
                elif var == 'REDIS_URL':
                    self.add_warning(
                        f"Redis URL not configured - background jobs disabled",
                        "Set REDIS_URL for background processing support"
                    )
        
        return success
    
    def validate_directories(self) -> bool:
        """Validate required directory structure"""
        required_dirs = [
            os.getenv('UPLOAD_FOLDER', 'uploads'),
            os.getenv('TEMP_FOLDER', 'temp'),
            os.getenv('OUTPUT_FOLDER', 'outputs'),
            'web/static',
            'web/templates'
        ]
        
        success = True
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created missing directory: {dir_path}")
                except OSError as e:
                    self.add_error(
                        f"Cannot create required directory: {dir_path}",
                        f"Create directory manually or fix permissions: {e}"
                    )
                    success = False
            
            # Check write permissions
            if dir_path.exists():
                try:
                    test_file = dir_path / '.test_write'
                    test_file.touch()
                    test_file.unlink()
                except (PermissionError, OSError) as e:
                    self.add_error(
                        f"Directory {dir_path} is not writable",
                        f"Fix directory permissions: chmod 755 {dir_path}"
                    )
                    success = False
        
        return success
    
    def validate_python_dependencies(self) -> bool:
        """Validate critical Python dependencies"""
        critical_imports = [
            ('flask', 'Flask framework'),
            ('flask_cors', 'CORS support'),
            ('flask_socketio', 'WebSocket support'),
            ('dotenv', 'Environment variable loading'),
            ('google.generativeai', 'Google AI integration (optional)'),
        ]
        
        success = True
        
        for module_name, description in critical_imports:
            try:
                __import__(module_name)
                logger.debug(f"✓ {description} available")
            except ImportError as e:
                if module_name == 'google.generativeai':
                    self.add_warning(
                        f"Google AI module not available - {description}",
                        "Install: pip install google-generativeai"
                    )
                else:
                    self.add_error(
                        f"Missing critical dependency: {module_name} - {description}",
                        "Install missing dependencies: pip install -r requirements.txt"
                    )
                    success = False
        
        return success
    
    def validate_port_availability(self, port: int) -> bool:
        """Check if the specified port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                logger.debug(f"✓ Port {port} is available")
                return True
        except OSError as e:
            if e.errno == 98:  # Address already in use
                self.add_warning(
                    f"Port {port} is already in use",
                    f"Use different port: export PORT=5001 or stop service on port {port}"
                )
            else:
                self.add_error(
                    f"Port validation failed: {e}",
                    "Check network configuration"
                )
            return False
    
    def validate_config_files(self) -> bool:
        """Validate configuration files exist and are readable"""
        config_files = [
            ('.env', 'Environment configuration'),
            ('requirements.txt', 'Python dependencies'),
            ('web/config.py', 'Flask configuration')
        ]
        
        success = True
        
        for file_path, description in config_files:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                if file_path == '.env':
                    env_example = self.project_root / '.env.example'
                    if env_example.exists():
                        self.add_error(
                            f"Configuration file {file_path} missing",
                            f"Copy .env.example to .env: cp {env_example} {full_path}"
                        )
                    else:
                        self.add_error(
                            f"Configuration file {file_path} missing",
                            f"Create {file_path} with required environment variables"
                        )
                else:
                    self.add_error(
                        f"Required file {file_path} missing - {description}",
                        f"Ensure {file_path} exists in project root"
                    )
                success = False
            
            elif not os.access(full_path, os.R_OK):
                self.add_error(
                    f"Configuration file {file_path} is not readable",
                    f"Fix file permissions: chmod 644 {full_path}"
                )
                success = False
        
        return success
    
    def run_all_validations(self, port: int = 5000) -> bool:
        """Run all startup validations"""
        logger.info("Running startup validations...")
        
        validations = [
            ("Environment Variables", self.validate_environment_variables),
            ("Directory Structure", self.validate_directories),
            ("Python Dependencies", self.validate_python_dependencies),
            ("Configuration Files", self.validate_config_files),
            ("Port Availability", lambda: self.validate_port_availability(port))
        ]
        
        overall_success = True
        
        for name, validation_func in validations:
            try:
                logger.debug(f"Validating: {name}")
                if not validation_func():
                    overall_success = False
                    logger.error(f"Validation failed: {name}")
                else:
                    logger.debug(f"Validation passed: {name}")
            except Exception as e:
                self.add_error(
                    f"Validation error in {name}: {str(e)}",
                    "Check logs for detailed error information"
                )
                overall_success = False
        
        return overall_success
    
    def get_validation_summary(self) -> Dict:
        """Get summary of all validation results"""
        return {
            "success": len(self.errors) == 0,
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "errors": [{"message": msg, "fix": fix} for msg, fix in self.errors],
            "warnings": [{"message": msg, "suggestion": sug} for msg, sug in self.warnings]
        }
    
    def print_validation_summary(self):
        """Print a formatted validation summary"""
        print("\n" + "=" * 60)
        print("🔍 STARTUP VALIDATION SUMMARY")
        print("=" * 60)
        
        if not self.errors and not self.warnings:
            print("✅ All validations passed! Server ready to start.")
            return
        
        if self.errors:
            print(f"❌ {len(self.errors)} Critical Error(s) Found:")
            for i, (error, fix) in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
                if fix:
                    print(f"     Fix: {fix}")
            print()
        
        if self.warnings:
            print(f"⚠️ {len(self.warnings)} Warning(s):")
            for i, (warning, suggestion) in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
                if suggestion:
                    print(f"     Suggestion: {suggestion}")
            print()
        
        if self.errors:
            print("❌ Server cannot start due to critical errors above.")
            print("💡 Fix the errors and try again.")
        else:
            print("⚠️ Server can start but some features may be limited.")
            print("💡 Address warnings for full functionality.")
        
        print("=" * 60)
    
    def raise_if_critical_errors(self):
        """Raise exception if there are critical errors"""
        if self.errors:
            error_msg = f"Startup validation failed with {len(self.errors)} critical errors"
            raise StartupValidationError(error_msg)


def validate_startup_requirements(port: int = 5000, project_root: Path = None) -> bool:
    """
    Convenience function to run all startup validations
    Returns True if startup should proceed, False otherwise
    """
    validator = StartupValidator(project_root)
    
    try:
        success = validator.run_all_validations(port)
        validator.print_validation_summary()
        
        if not success:
            validator.raise_if_critical_errors()
        
        return success
        
    except StartupValidationError as e:
        logger.error(f"Startup validation failed: {e.message}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during startup validation: {e}")
        return False