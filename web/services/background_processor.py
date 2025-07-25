"""
Background Processor service for async job processing
"""

import threading
import time
import logging
from queue import Queue, Empty
from typing import Optional

from web.services.job_manager import JobManager
from web.services.processor_integration import ProcessorIntegration
from web.models.job import JobStatus

logger = logging.getLogger(__name__)


class BackgroundProcessor:
    """Background processor for handling processing jobs asynchronously"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for background processor"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self.job_manager = JobManager()
        self.processor_integration = ProcessorIntegration()
        
        # Job queue and worker thread
        self.job_queue = Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        self.is_running = False
        
        # Cleanup thread
        self.cleanup_thread: Optional[threading.Thread] = None
        
        self._initialized = True
        logger.info("BackgroundProcessor initialized")
    
    def start(self):
        """Start the background processor"""
        if self.is_running:
            logger.warning("Background processor already running")
            return
        
        self.is_running = True
        self.shutdown_event.clear()
        
        # Start worker thread
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            name="ProcessingWorker",
            daemon=True
        )
        self.worker_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            name="CleanupWorker", 
            daemon=True
        )
        self.cleanup_thread.start()
        
        # Queue any pending jobs
        self._queue_pending_jobs()
        
        logger.info("Background processor started")
    
    def stop(self):
        """Stop the background processor"""
        if not self.is_running:
            return
        
        logger.info("Stopping background processor...")
        
        self.is_running = False
        self.shutdown_event.set()
        
        # Wait for threads to complete
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=2.0)
        
        logger.info("Background processor stopped")
    
    def submit_job(self, job_id: str):
        """Submit a job for background processing"""
        if not self.is_running:
            logger.error("Cannot submit job - background processor not running")
            return False
        
        try:
            self.job_queue.put(job_id, timeout=1.0)
            logger.info(f"Submitted job {job_id} for processing")
            return True
        except Exception as e:
            logger.error(f"Error submitting job {job_id}: {str(e)}")
            return False
    
    def _worker_loop(self):
        """Main worker loop for processing jobs"""
        logger.info("Worker loop started")
        
        while not self.shutdown_event.is_set():
            try:
                # Get job from queue with timeout
                job_id = self.job_queue.get(timeout=1.0)
                
                if job_id:
                    self._process_job(job_id)
                    
            except Empty:
                # No job available, continue
                continue
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}")
                time.sleep(1.0)
        
        logger.info("Worker loop stopped")
    
    def _process_job(self, job_id: str):
        """Process a single job"""
        try:
            # Get job from manager
            job = self.job_manager.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            logger.info(f"Processing job {job_id}")
            
            # Start job
            self.job_manager.start_job(job_id)
            
            # Set up progress callback
            self.processor_integration.set_progress_callback(
                self.job_manager.update_job_progress,
                job_id
            )
            
            # Process document
            result = self.processor_integration.process_document(
                input_file_path=job.file_path,
                processing_mode=job.processing_mode,
                categories=job.options.categories,
                output_filename=job.options.output_filename
            )
            
            # Complete job
            self.job_manager.complete_job(job_id, result)
            
            logger.info(f"Successfully completed job {job_id}")
            
        except Exception as e:
            error_message = f"Processing failed: {str(e)}"
            logger.error(f"Error processing job {job_id}: {error_message}")
            
            # Mark job as failed
            self.job_manager.fail_job(job_id, error_message)
    
    def _queue_pending_jobs(self):
        """Queue any pending jobs on startup"""
        try:
            pending_jobs = self.job_manager.get_pending_jobs()
            
            for job in pending_jobs:
                self.job_queue.put(job.job_id)
                logger.info(f"Queued pending job {job.job_id}")
            
            if pending_jobs:
                logger.info(f"Queued {len(pending_jobs)} pending jobs")
                
        except Exception as e:
            logger.error(f"Error queuing pending jobs: {str(e)}")
    
    def _cleanup_loop(self):
        """Background cleanup loop for expired jobs"""
        logger.info("Cleanup loop started")
        
        cleanup_interval = 3600  # 1 hour
        
        while not self.shutdown_event.is_set():
            try:
                # Wait for shutdown event with timeout
                if self.shutdown_event.wait(cleanup_interval):
                    break
                
                # Perform cleanup
                removed_count = self.job_manager.cleanup_expired_jobs()
                
                if removed_count > 0:
                    logger.info(f"Cleanup: removed {removed_count} expired jobs")
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                time.sleep(60)  # Wait before retrying
        
        logger.info("Cleanup loop stopped")
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.job_queue.qsize()
    
    def get_status(self) -> dict:
        """Get processor status"""
        return {
            'is_running': self.is_running,
            'queue_size': self.get_queue_size(),
            'worker_alive': self.worker_thread.is_alive() if self.worker_thread else False,
            'cleanup_alive': self.cleanup_thread.is_alive() if self.cleanup_thread else False,
            'job_stats': self.job_manager.get_job_stats()
        }