"""
Download service following Single Responsibility Principle
Handles ONLY file download operations and cleanup
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from flask import send_file

from web.services.job_repository import JobRepository, get_default_job_repository

logger = logging.getLogger(__name__)


class DownloadService:
    """
    Download service following Single Responsibility Principle
    
    ONLY responsible for:
    - Finding completed jobs by file ID
    - Serving processed files for download
    - Managing file cleanup
    """
    
    def __init__(self, job_repository: Optional[JobRepository] = None):
        self.job_repository = job_repository or get_default_job_repository()
        logger.info("DownloadService initialized with dependency injection")
    
    def download_result(self, file_id: str):
        """Download processed result file"""
        job_data = self._find_completed_job(file_id)
        if not job_data:
            return None
        
        output_file = self._get_output_file(job_data)
        if not output_file.exists():
            return None
        
        return self._serve_file(output_file)
    
    def cleanup_old_jobs(self, hours: int = 24) -> int:
        """Clean up jobs older than specified hours"""
        cutoff_time = datetime.now().timestamp() - (hours * 60 * 60)
        
        jobs_to_remove = []
        all_jobs = self.job_repository.list_jobs()
        
        for job_id, job_data in all_jobs.items():
            if self._is_job_expired(job_data, cutoff_time):
                jobs_to_remove.append(job_id)
        
        return self._remove_expired_jobs(jobs_to_remove)
    
    def _find_completed_job(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Find completed job with matching file ID"""
        all_jobs = self.job_repository.list_jobs()
        
        for job_data in all_jobs.values():
            if self._is_matching_completed_job(job_data, file_id):
                return job_data
        
        return None
    
    def _is_matching_completed_job(self, job_data: Dict[str, Any], file_id: str) -> bool:
        """Check if job matches file ID and is completed"""
        return (job_data.get('file_id') == file_id and 
                job_data.get('status') == 'completed' and 
                'output_file' in job_data)
    
    def _get_output_file(self, job_data: Dict[str, Any]) -> Path:
        """Get output file path from job data"""
        return Path(job_data['output_file'])
    
    def _serve_file(self, output_file: Path):
        """Serve file for download"""
        return send_file(
            str(output_file),
            as_attachment=True,
            download_name=output_file.name,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    
    def _is_job_expired(self, job_data: Dict[str, Any], cutoff_time: float) -> bool:
        """Check if job is expired based on cutoff time"""
        try:
            created_at = datetime.fromisoformat(job_data['created_at']).timestamp()
            return created_at < cutoff_time
        except (KeyError, ValueError):
            return True  # Remove jobs with invalid timestamps
    
    def _remove_expired_jobs(self, job_ids_to_remove: list) -> int:
        """Remove expired jobs and return count"""
        for job_id in job_ids_to_remove:
            self.job_repository.remove_job(job_id)
        
        if job_ids_to_remove:
            logger.info(f"Cleaned up {len(job_ids_to_remove)} expired jobs")
        
        return len(job_ids_to_remove)