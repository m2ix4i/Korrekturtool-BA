"""
Health checking and API validation module
Provides comprehensive system health status for localhost environment
"""

import os
import sys
import json
import time
import socket
from pathlib import Path
from typing import Dict, Any, List
from flask import jsonify
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class HealthChecker:
    """Comprehensive health checking for localhost environment"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.start_time = time.time()
        load_dotenv()
    
    def check_api_key_health(self) -> Dict[str, Any]:
        """Check Google API key configuration and validity"""
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            return {
                "status": "fail",
                "configured": False,
                "valid": False,
                "message": "GOOGLE_API_KEY environment variable not set",
                "fix": "Set GOOGLE_API_KEY in .env file"
            }
        
        if api_key == 'your_google_api_key_here':
            return {
                "status": "fail", 
                "configured": False,
                "valid": False,
                "message": "GOOGLE_API_KEY is using placeholder value",
                "fix": "Replace placeholder with actual Google API key"
            }
        
        # Basic format validation
        if len(api_key) < 20:
            return {
                "status": "warning",
                "configured": True,
                "valid": False,
                "message": "API key appears too short",
                "details": f"Length: {len(api_key)} characters"
            }
        
        # Try to validate with actual API call (optional - can be expensive)
        api_valid = self._validate_gemini_api_key(api_key)
        
        return {
            "status": "pass" if api_valid else "warning",
            "configured": True,
            "valid": api_valid,
            "message": "API key validation completed",
            "details": {
                "key_length": len(api_key),
                "key_prefix": api_key[:4] + "..." if len(api_key) > 4 else "***",
                "validation_attempted": True
            }
        }
    
    def _validate_gemini_api_key(self, api_key: str) -> bool:
        """Attempt to validate API key with actual Gemini API call"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Try to list models - lightweight API call
            models = list(genai.list_models())
            return len(models) > 0
            
        except Exception as e:
            logger.warning(f"API key validation failed: {e}")
            return False
    
    def check_dependencies_health(self) -> Dict[str, Any]:
        """Check critical Python dependencies"""
        critical_packages = [
            'flask', 'flask_cors', 'flask_socketio', 'google.generativeai',
            'python_docx', 'celery', 'redis', 'sqlalchemy'
        ]
        
        installed = []
        missing = []
        versions = {}
        
        for package in critical_packages:
            try:
                # Handle import name mapping
                import_name = package
                if package == 'google.generativeai':
                    import_name = 'google.generativeai'
                elif package == 'python_docx':
                    import_name = 'docx'
                elif package == 'flask_cors':
                    import_name = 'flask_cors'
                elif package == 'flask_socketio':
                    import_name = 'flask_socketio'
                
                module = __import__(import_name)
                installed.append(package)
                
                # Try to get version
                if hasattr(module, '__version__'):
                    versions[package] = module.__version__
                elif hasattr(module, 'VERSION'):
                    versions[package] = str(module.VERSION)
                    
            except ImportError:
                missing.append(package)
        
        status = "pass" if not missing else "fail"
        
        return {
            "status": status,
            "installed_count": len(installed),
            "missing_count": len(missing),
            "installed_packages": installed,
            "missing_packages": missing,
            "versions": versions,
            "message": f"Dependencies check: {len(installed)} installed, {len(missing)} missing"
        }
    
    def check_directories_health(self) -> Dict[str, Any]:
        """Check required directory structure"""
        required_dirs = ['uploads', 'temp', 'outputs', 'web/static', 'web/templates']
        
        status_info = {}
        all_exist = True
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            exists = dir_path.exists()
            writable = False
            
            if exists:
                try:
                    # Test write permissions
                    test_file = dir_path / '.test_write'
                    test_file.touch()
                    test_file.unlink()
                    writable = True
                except (PermissionError, OSError):
                    writable = False
            
            status_info[dir_name] = {
                "exists": exists,
                "writable": writable,
                "path": str(dir_path)
            }
            
            if not exists:
                all_exist = False
        
        return {
            "status": "pass" if all_exist else "fail",
            "directories": status_info,
            "message": f"Directory structure check: {len([d for d in status_info.values() if d['exists']])} of {len(required_dirs)} directories exist"
        }
    
    def check_services_health(self) -> Dict[str, Any]:
        """Check service connectivity and readiness"""
        services = {}
        
        # Check Flask import and basic functionality
        try:
            import flask
            services["flask"] = {
                "status": "pass",
                "version": flask.__version__,
                "message": "Flask framework ready"
            }
        except ImportError as e:
            services["flask"] = {
                "status": "fail",
                "message": f"Flask import failed: {e}"
            }
        
        # Check SocketIO
        try:
            import flask_socketio
            version = getattr(flask_socketio, '__version__', 'unknown')
            services["websocket"] = {
                "status": "pass",
                "version": version,
                "message": "WebSocket support ready"
            }
        except ImportError as e:
            services["websocket"] = {
                "status": "fail",
                "message": f"SocketIO import failed: {e}"
            }
        
        # Check port availability
        port = int(os.getenv('PORT', 5000))
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                services["port"] = {
                    "status": "pass",
                    "port": port,
                    "message": f"Port {port} available"
                }
        except OSError:
            services["port"] = {
                "status": "warning",
                "port": port,
                "message": f"Port {port} in use (may be this server)"
            }
        
        # Overall service status
        failed_services = [name for name, info in services.items() if info["status"] == "fail"]
        overall_status = "fail" if failed_services else "pass"
        
        return {
            "status": overall_status,
            "services": services,
            "failed_services": failed_services,
            "message": f"Services check: {len(failed_services)} failed"
        }
    
    def check_environment_health(self) -> Dict[str, Any]:
        """Check environment configuration"""
        required_vars = [
            'GOOGLE_API_KEY', 'SECRET_KEY', 'FLASK_ENV',
            'MAX_FILE_SIZE', 'UPLOAD_FOLDER', 'TEMP_FOLDER', 'OUTPUT_FOLDER'
        ]
        
        env_status = {}
        missing_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if value and value != f"your_{var.lower()}_here":
                env_status[var] = {
                    "configured": True,
                    "value_length": len(value),
                    "is_placeholder": False
                }
            else:
                env_status[var] = {
                    "configured": False,
                    "is_placeholder": value == f"your_{var.lower()}_here" if value else False
                }
                missing_vars.append(var)
        
        return {
            "status": "pass" if not missing_vars else "fail",
            "environment_variables": env_status,
            "missing_variables": missing_vars,
            "configured_count": len(required_vars) - len(missing_vars),
            "total_required": len(required_vars),
            "message": f"Environment check: {len(required_vars) - len(missing_vars)} of {len(required_vars)} variables configured"
        }
    
    def check_performance_health(self) -> Dict[str, Any]:
        """Check system performance metrics"""
        try:
            import psutil
            
            # CPU and memory info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "status": "pass",
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "memory_percent_used": memory.percent,
                    "disk_total_gb": round(disk.total / (1024**3), 2),
                    "disk_free_gb": round(disk.free / (1024**3), 2),
                    "disk_percent_used": round((disk.used / disk.total) * 100, 1)
                },
                "process": {
                    "memory_mb": round(process_memory.rss / (1024**2), 2),
                    "memory_vms_mb": round(process_memory.vms / (1024**2), 2)
                },
                "uptime_seconds": round(time.time() - self.start_time, 2),
                "message": "System performance metrics collected"
            }
        except ImportError:
            return {
                "status": "warning",
                "message": "psutil not available for performance monitoring"
            }
        except Exception as e:
            return {
                "status": "warning",
                "message": f"Performance monitoring failed: {e}"
            }
    
    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health status for all components"""
        health_checks = {
            "api_key": self.check_api_key_health(),
            "dependencies": self.check_dependencies_health(),
            "directories": self.check_directories_health(),
            "services": self.check_services_health(),
            "environment": self.check_environment_health(),
            "performance": self.check_performance_health()
        }
        
        # Calculate overall status
        failed_checks = [name for name, check in health_checks.items() if check["status"] == "fail"]
        warning_checks = [name for name, check in health_checks.items() if check["status"] == "warning"]
        
        if failed_checks:
            overall_status = "unhealthy"
            overall_message = f"System unhealthy: {len(failed_checks)} critical failures"
        elif warning_checks:
            overall_status = "degraded"
            overall_message = f"System degraded: {len(warning_checks)} warnings"
        else:
            overall_status = "healthy"
            overall_message = "All systems operational"
        
        # System information
        system_info = {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
            "project_root": str(self.project_root),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "check_duration_ms": round((time.time() - self.start_time) * 1000, 2)
        }
        
        return {
            "overall_status": overall_status,
            "overall_message": overall_message,
            "system_info": system_info,
            "health_checks": health_checks,
            "summary": {
                "total_checks": len(health_checks),
                "failed_checks": len(failed_checks),
                "warning_checks": len(warning_checks),
                "passed_checks": len(health_checks) - len(failed_checks) - len(warning_checks)
            },
            "failed_components": failed_checks,
            "warning_components": warning_checks
        }


def get_health_status():
    """Flask route handler for health endpoint"""
    checker = HealthChecker()
    health_data = checker.get_comprehensive_health()
    
    # Set appropriate HTTP status code
    if health_data["overall_status"] == "unhealthy":
        status_code = 503  # Service Unavailable
    elif health_data["overall_status"] == "degraded":
        status_code = 200  # OK but with warnings
    else:
        status_code = 200  # OK
    
    return jsonify(health_data), status_code


def get_basic_info():
    """Enhanced basic API info with health summary"""
    from web.utils.api_config import APIConfig
    
    checker = HealthChecker()
    basic_health = {
        "api_key_configured": checker.check_api_key_health()["configured"],
        "dependencies_ok": checker.check_dependencies_health()["status"] == "pass",
        "directories_ok": checker.check_directories_health()["status"] == "pass",
        "services_ok": checker.check_services_health()["status"] == "pass"
    }
    
    return jsonify({
        'name': APIConfig.API_NAME,
        'version': APIConfig.API_VERSION,
        'description': APIConfig.API_DESCRIPTION,
        'status': 'ready' if all(basic_health.values()) else 'setup_required',
        'health_summary': basic_health,
        'endpoints': APIConfig.ENDPOINTS,
        'health_check_url': '/api/v1/health'
    })