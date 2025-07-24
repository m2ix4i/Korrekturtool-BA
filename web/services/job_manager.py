"""
Job Manager service for processing job lifecycle management
"""

import os
import json
import logging
import threading
from typing import Dict, List, Optional, Callable
from pathlib import Path

from web.models.job import Job, JobStatus, ProcessingMode, ProcessingOptions
from web.utils.error_builder import APIErrorBuilder

logger = logging.getLogger(__name__)


class JobManager:
    """Manages processing jobs with in-memory storage and persistence"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for job manager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._jobs: Dict[str, Job] = {}
        self._jobs_lock = threading.RLock()
        self._persistence_file = Path('jobs_state.json')
        self._max_job_age_hours = 24
        self._initialized = True
        
        # Load persisted jobs on startup
        self._load_jobs_from_disk()
        
        logger.info("JobManager initialized")
    
    def create_job(
        self,
        file_id: str,
        file_path: str,
        processing_mode: str,
        options: dict
    ) -> Job:
        """Create a new processing job"""
        try:
            # Validate processing mode
            try:
                mode = ProcessingMode(processing_mode)
            except ValueError:
                raise ValueError(f"Invalid processing mode: {processing_mode}")
            
            # Create processing options
            processing_options = ProcessingOptions.from_dict(options)
            
            # Create job
            job = Job(
                file_id=file_id,
                file_path=file_path,
                processing_mode=mode,
                options=processing_options
            )
            
            # Store job
            with self._jobs_lock:
                self._jobs[job.job_id] = job
                self._persist_jobs_to_disk()
            
            logger.info(f"Created job {job.job_id} for file {file_id}")
            return job
            
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        with self._jobs_lock:
            return self._jobs.get(job_id)
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs"""
        with self._jobs_lock:
            return list(self._jobs.values())
    
    def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """Get jobs by status"""
        with self._jobs_lock:
            return [job for job in self._jobs.values() if job.status == status]
    
    def update_job_progress(
        self,
        job_id: str,
        step: str,
        percent: int,
        estimated_remaining: Optional[int] = None
    ) -> bool:
        """Update job progress"""
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.update_progress(step, percent, estimated_remaining)
            self._persist_jobs_to_disk()
            
            logger.debug(f"Updated job {job_id} progress: {step} ({percent}%)")
            return True
    
    def start_job(self, job_id: str) -> bool:
        """Mark job as started"""
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.start_processing()
            self._persist_jobs_to_disk()
            
            logger.info(f"Started job {job_id}")
            return True
    
    def complete_job(self, job_id: str, result) -> bool:
        """Mark job as completed successfully"""
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.complete_successfully(result)
            self._persist_jobs_to_disk()
            
            logger.info(f"Completed job {job_id}")
            return True
    
    def fail_job(self, job_id: str, error_message: str) -> bool:
        """Mark job as failed"""
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.fail_with_error(error_message)
            self._persist_jobs_to_disk()
            
            logger.error(f"Failed job {job_id}: {error_message}")
            return True
    
    def cleanup_expired_jobs(self) -> int:
        """Clean up expired jobs and return count of removed jobs"""
        removed_count = 0
        
        with self._jobs_lock:
            expired_job_ids = [
                job_id for job_id, job in self._jobs.items()
                if job.is_expired(self._max_job_age_hours)
            ]
            
            for job_id in expired_job_ids:
                job = self._jobs.pop(job_id, None)
                if job:
                    # Clean up associated files if they exist
                    self._cleanup_job_files(job)
                    removed_count += 1
            
            if removed_count > 0:
                self._persist_jobs_to_disk()
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired jobs")
        
        return removed_count
    
    def _cleanup_job_files(self, job: Job):
        """Clean up files associated with a job"""
        try:
            # Clean up input file if it exists
            if job.file_path and os.path.exists(job.file_path):
                os.unlink(job.file_path)
                logger.debug(f"Removed input file: {job.file_path}")
            
            # Clean up output file if it exists
            if job.result and job.result.output_file_path:
                if os.path.exists(job.result.output_file_path):
                    os.unlink(job.result.output_file_path)
                    logger.debug(f"Removed output file: {job.result.output_file_path}")
        
        except Exception as e:
            logger.warning(f"Error cleaning up files for job {job.job_id}: {str(e)}")
    
    def get_pending_jobs(self) -> List[Job]:
        """Get jobs that are pending processing"""
        return self.get_jobs_by_status(JobStatus.PENDING)
    
    def get_processing_jobs(self) -> List[Job]:
        """Get jobs that are currently processing"""
        return self.get_jobs_by_status(JobStatus.PROCESSING)
    
    def _persist_jobs_to_disk(self):
        """Persist jobs to disk for recovery"""
        try:
            jobs_data = {
                job_id: job.to_dict()
                for job_id, job in self._jobs.items()
            }
            
            with open(self._persistence_file, 'w') as f:
                json.dump(jobs_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error persisting jobs to disk: {str(e)}")
    
    def _load_jobs_from_disk(self):
        """Load jobs from disk on startup"""
        try:
            if not self._persistence_file.exists():
                return
            
            with open(self._persistence_file, 'r') as f:
                jobs_data = json.load(f)
            
            for job_id, job_dict in jobs_data.items():
                try:
                    job = Job.from_dict(job_dict)
                    
                    # Reset processing jobs to pending on restart
                    if job.status == JobStatus.PROCESSING:
                        job.status = JobStatus.PENDING
                        job.started_at = None
                        job.progress.current_step = "Restarted"
                        job.progress.progress_percent = 0
                    
                    self._jobs[job_id] = job
                    
                except Exception as e:
                    logger.error(f"Error loading job {job_id}: {str(e)}")
            
            logger.info(f"Loaded {len(self._jobs)} jobs from disk")
            
        except Exception as e:
            logger.error(f"Error loading jobs from disk: {str(e)}")
    
    def get_job_stats(self) -> dict:
        """Get statistics about jobs"""
        with self._jobs_lock:
            stats = {
                'total_jobs': len(self._jobs),
                'pending': len(self.get_jobs_by_status(JobStatus.PENDING)),
                'processing': len(self.get_jobs_by_status(JobStatus.PROCESSING)),
                'completed': len(self.get_jobs_by_status(JobStatus.COMPLETED)),
                'failed': len(self.get_jobs_by_status(JobStatus.FAILED))
            }
        
        return stats