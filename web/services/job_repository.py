"""
Job repository following Dependency Inversion Principle
Handles ONLY job data storage and retrieval with thread-safe operations
"""

import logging
import threading
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class JobRepository(ABC):
    """Abstract base class for job storage following Dependency Inversion Principle"""
    
    @abstractmethod
    def store_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Store job data"""
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve job data"""
        pass
    
    @abstractmethod
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job data"""
        pass
    
    @abstractmethod
    def remove_job(self, job_id: str) -> bool:
        """Remove job from storage"""
        pass
    
    @abstractmethod
    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """List all jobs"""
        pass


class InMemoryJobRepository(JobRepository):
    """
    Thread-safe in-memory job repository
    
    ONLY responsible for:
    - Thread-safe job data storage
    - Job data retrieval
    - Job data updates
    """
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        logger.info("InMemoryJobRepository initialized")
    
    def store_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Store job data with thread safety"""
        with self._lock:
            self._jobs[job_id] = job_data.copy()
            logger.debug(f"Job {job_id} stored")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve job data with thread safety"""
        with self._lock:
            job_data = self._jobs.get(job_id)
            return job_data.copy() if job_data else None
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job data with thread safety"""
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._jobs[job_id].update(updates)
            logger.debug(f"Job {job_id} updated")
            return True
    
    def remove_job(self, job_id: str) -> bool:
        """Remove job with thread safety"""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                logger.debug(f"Job {job_id} removed")
                return True
            return False
    
    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """List all jobs with thread safety"""
        with self._lock:
            return {job_id: data.copy() for job_id, data in self._jobs.items()}
    
    def get_job_count(self) -> int:
        """Get number of stored jobs"""
        with self._lock:
            return len(self._jobs)


# Global repository instance for dependency injection
_default_repository = None

def get_default_job_repository() -> JobRepository:
    """Get default job repository instance (singleton pattern)"""
    global _default_repository
    if _default_repository is None:
        _default_repository = InMemoryJobRepository()
    return _default_repository


def set_job_repository(repository: JobRepository) -> None:
    """Set custom job repository for dependency injection"""
    global _default_repository
    _default_repository = repository
    logger.info(f"Job repository set to {repository.__class__.__name__}")