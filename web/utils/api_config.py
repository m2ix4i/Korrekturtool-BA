"""
API configuration constants
"""


class APIConfig:
    """Configuration constants for API responses"""
    
    API_NAME = 'German Thesis Correction Tool API'
    API_VERSION = '1.0.0'
    API_DESCRIPTION = 'Web API for automated German thesis correction with AI analysis'
    
    ENDPOINTS = {
        'info': '/api/v1/info',
        'health': '/api/v1/health',
        'upload': '/api/v1/upload',
        'upload_info': '/api/v1/upload/info',
        'upload_cleanup': '/api/v1/upload/{file_id}/cleanup',
        'process': '/api/v1/process',
        'status': '/api/v1/status/{job_id}',
        'download': '/api/v1/download/{file_id}'
    }