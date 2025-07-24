"""
API configuration constants
"""


class APIConfig:
    """Configuration constants for API responses"""
    
    API_NAME = 'German Thesis Correction Tool API'
    API_VERSION = '1.0.0'
    API_DESCRIPTION = 'Web API for automated German thesis correction with AI analysis'
    
    ENDPOINTS = {
        'health': '/health',
        'info': '/api/v1/info',
        'upload': '/api/v1/upload (coming soon)',
        'process': '/api/v1/process (coming soon)',
        'status': '/api/v1/status/{job_id} (coming soon)',
        'download': '/api/v1/download/{file_id} (coming soon)'
    }