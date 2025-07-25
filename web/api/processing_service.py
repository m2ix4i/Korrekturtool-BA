"""
Processing service following Single Responsibility Principle
Handles ONLY document processing coordination with dependency injection
"""

import logging
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from flask import current_app

from web.services.job_repository import JobRepository, get_default_job_repository
from web.utils.errors import ValidationError, ProcessingError
from .processor_args_adapter import ProcessorArgsAdapter

logger = logging.getLogger(__name__)


class ProcessingService:
    """
    Processing service following Single Responsibility Principle
    
    ONLY responsible for:
    - Coordinating document processing workflow
    - Managing processing job lifecycle
    - Integrating with processor modules
    """
    
    def __init__(self, job_repository: Optional[JobRepository] = None):
        self.job_repository = job_repository or get_default_job_repository()
        logger.info("ProcessingService initialized with dependency injection")
    
    def start_processing(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start document processing and return job info"""
        job_id = str(uuid.uuid4())
        
        self._create_processing_job(job_id, request_data)
        self._start_async_processing(job_id, request_data)
        
        return {
            'job_id': job_id,
            'status': 'processing',
            'message': 'Document processing started',
            'estimated_time': '30-90 seconds'
        }
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get processing status for job ID"""
        job_data = self.job_repository.get_job(job_id)
        if not job_data:
            return None
        
        return self._prepare_status_response(job_data)
    
    def _create_processing_job(self, job_id: str, request_data: Dict[str, Any]) -> None:
        """Create initial job record"""
        job_data = {
            'status': 'processing',
            'created_at': datetime.now().isoformat(),
            'file_id': request_data.get('file_id'),
            'processing_mode': request_data.get('processing_mode', 'complete'),
            'progress': 0,
            'message': 'Processing started'
        }
        self.job_repository.store_job(job_id, job_data)
    
    def _start_async_processing(self, job_id: str, request_data: Dict[str, Any]) -> None:
        """Start processing in background thread"""
        thread = threading.Thread(
            target=self._process_document_async,
            args=(job_id, request_data)
        )
        thread.start()
    
    def _process_document_async(self, job_id: str, request_data: Dict[str, Any]) -> None:
        """Process document asynchronously"""
        try:
            self._initialize_processing(job_id)
            file_paths = self._prepare_file_paths(request_data)
            processor = self._load_processor_module(request_data)
            result = self._execute_processing(processor, file_paths, request_data)
            self._finalize_processing(job_id, result, file_paths)
        except Exception as e:
            self._handle_processing_error(job_id, e)
    
    def _initialize_processing(self, job_id: str) -> None:
        """Initialize processing job status"""
        self.job_repository.update_job(job_id, {
            'progress': 10,
            'message': 'Initializing processing pipeline'
        })
    
    def _prepare_file_paths(self, request_data: Dict[str, Any]) -> Dict[str, Path]:
        """Prepare input and output file paths"""
        upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'outputs'))
        output_dir.mkdir(exist_ok=True)
        
        input_file = upload_dir / f"{request_data['file_id']}.docx"
        if not input_file.exists():
            raise ProcessingError(f"Input file not found: {input_file}")
        
        output_filename = self._generate_output_filename(request_data)
        output_file = output_dir / output_filename
        
        return {'input': input_file, 'output': output_file}
    
    def _generate_output_filename(self, request_data: Dict[str, Any]) -> str:
        """Generate output filename with proper extension"""
        output_filename = (request_data.get('output_filename') or 
                          f"{request_data['file_id']}_corrected.docx")
        if not output_filename.endswith('.docx'):
            output_filename += '.docx'
        return output_filename
    
    def _load_processor_module(self, request_data: Dict[str, Any]):
        """Load appropriate processor module"""
        self.job_repository.update_job(request_data.get('job_id', ''), {
            'progress': 20,
            'message': 'Loading processing modules'
        })
        
        if request_data['processing_mode'] == 'optimized':
            from main_performance_optimized import main as process_main
        else:
            from main_complete_advanced import main as process_main
        
        return process_main
    
    def _execute_processing(self, processor, file_paths: Dict[str, Path], 
                          request_data: Dict[str, Any]) -> bool:
        """Execute document processing"""
        args = ProcessorArgsAdapter.from_request_data(
            request_data, str(file_paths['input']), str(file_paths['output'])
        )
        
        try:
            result = processor(args)
            return result is not False
        except Exception as e:
            logger.error(f"Error in document processing: {str(e)}")
            return False
    
    def _finalize_processing(self, job_id: str, success: bool, 
                           file_paths: Dict[str, Path]) -> None:
        """Finalize processing with success or failure"""
        if success and file_paths['output'].exists():
            self._handle_processing_success(job_id, file_paths['output'])
        else:
            self._handle_processing_failure(job_id)
    
    def _handle_processing_success(self, job_id: str, output_file: Path) -> None:
        """Handle successful processing completion"""
        self.job_repository.update_job(job_id, {
            'status': 'completed',
            'progress': 100,
            'message': 'Document processing completed successfully',
            'output_file': str(output_file),
            'completed_at': datetime.now().isoformat()
        })
        logger.info(f"Document processing completed successfully for job {job_id}")
    
    def _handle_processing_failure(self, job_id: str) -> None:
        """Handle processing failure"""
        self.job_repository.update_job(job_id, {
            'status': 'failed',
            'progress': 0,
            'message': 'Document processing failed',
            'error': 'Processing did not complete successfully',
            'failed_at': datetime.now().isoformat()
        })
        logger.error(f"Document processing failed for job {job_id}")
    
    def _handle_processing_error(self, job_id: str, error: Exception) -> None:
        """Handle processing error"""
        self.job_repository.update_job(job_id, {
            'status': 'failed',
            'progress': 0,
            'message': f'Processing error: {str(error)}',
            'error': str(error),
            'failed_at': datetime.now().isoformat()
        })
        logger.error(f"Processing error for job {job_id}: {str(error)}")
    
    def _prepare_status_response(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare job status response for API"""
        response_data = job_data.copy()
        
        if 'output_file' in job_data and job_data['status'] == 'completed':
            response_data['download_available'] = True
        
        return response_data