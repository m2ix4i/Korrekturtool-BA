# Issue #4: Integrate existing processing pipeline with web API

**GitHub Issue**: https://github.com/m2ix4i/Korrekturtool-BA/issues/4

## Problem Analysis

The system currently has two powerful CLI-based processing tools:
1. `CompleteAdvancedKorrekturtool` - Full-featured with multi-pass analysis
2. `PerformanceOptimizedKorrekturtool` - Optimized for large documents with caching

**Challenge**: Integrate these into a web API with async processing, job management, and status tracking.

## Current Processing Interface Analysis

### CompleteAdvancedKorrekturtool
- **Main Method**: `process_document_complete(document_path: str, output_path: str = None) -> bool`
- **Features**: Multi-pass analysis, 4 categories (grammar, style, clarity, academic)
- **Performance Tracking**: Built-in performance stats
- **Processing Flow**: Parse → Chunk → Analyze → Format → Integrate

### PerformanceOptimizedKorrekturtool  
- **Main Method**: `process_document_performance_optimized(document_path: str, output_path: str = None) -> bool`
- **Features**: Batch processing, memory optimization, caching, adaptive configuration
- **System Analysis**: Auto-configures based on available resources
- **Processing Flow**: System Analysis → Parse → Batch Process → Integrate → Dashboard

## Solution Architecture

### 1. Job Management System
```python
Job States: pending → processing → completed | failed
Job Storage: In-memory dict (can be upgraded to database later)
Job Tracking: UUID-based job IDs with metadata
```

### 2. Async Processing
```python
Simple Threading: Using Python threading for background processing
Queue System: Basic FIFO queue for job management
Status Updates: Real-time job status tracking
```

### 3. File Management
```python
Input Files: From upload directory (already implemented)
Output Files: Secure storage in outputs directory
Cleanup: Automatic cleanup after configurable timeout
```

## Implementation Plan

### Phase 1: Core Models and Services
1. **Create Job Model** (`web/models/job.py`)
   - Job data structure with states and metadata
   - Serialization for API responses

2. **Create Job Manager** (`web/services/job_manager.py`)
   - Job lifecycle management
   - Status tracking and updates
   - Queue management

3. **Create Processor Integration** (`web/services/processor_integration.py`)
   - Wrapper for existing processing classes
   - Unified interface for both processing modes
   - Progress callback integration

### Phase 2: Background Processing
4. **Implement Async Processing**
   - Background thread worker
   - Job queue processing
   - Error handling and recovery

### Phase 3: API Endpoints
5. **Create Process API** (`web/api/process.py`)
   - POST /api/v1/process endpoint
   - Request validation and job creation
   - Processing options handling

6. **Create Status API**
   - GET /api/v1/status/{job_id} endpoint
   - Real-time job status and progress

7. **Create Download API**
   - GET /api/v1/download/{file_id} endpoint
   - Secure file download with validation

### Phase 4: Integration and Testing
8. **Add Processing Options**
   - Configuration for processing modes
   - Category selection (grammar, style, clarity, academic)
   - Custom output filenames

9. **Test Complete Pipeline**
   - End-to-end testing
   - Error scenarios
   - Performance validation

## API Specification Implementation

### POST /api/v1/process
```json
Request:
{
  "file_id": "uuid-string",
  "processing_mode": "complete|performance", 
  "options": {
    "categories": ["grammar", "style", "clarity", "academic"],
    "output_filename": "custom_name.docx"
  }
}

Response:
{
  "success": true,
  "job_id": "job-uuid",
  "status": "pending",
  "estimated_time": "60-120 seconds"
}
```

### GET /api/v1/status/{job_id}
```json
Response:
{
  "success": true,
  "job_id": "job-uuid",
  "status": "processing",
  "progress": 45,
  "current_step": "AI Analysis",
  "estimated_remaining": "30 seconds"
}
```

### GET /api/v1/download/{file_id}
```json
Response: Binary file download or
{
  "success": false,
  "error": "file_not_found",
  "message": "File not found or has expired"
}
```

## Technical Decisions

### Background Processing Choice
- **Selected**: Python Threading (simple, sufficient for current needs)  
- **Alternative**: Celery (overkill for initial implementation)
- **Rationale**: Threading provides adequate async processing without external dependencies

### Job Storage Choice
- **Selected**: In-memory dictionary with JSON serialization
- **Alternative**: SQLite database (can be added later)
- **Rationale**: Simple implementation, easy to upgrade later

### File Security
- **Input Files**: Already secured by existing upload system
- **Output Files**: UUID-based naming, configurable cleanup
- **Downloads**: Token-based access validation

## Success Criteria

1. ✅ File upload integration (already implemented)
2. ❓ Async processing job creation
3. ❓ Both processing modes (complete + performance) accessible via API
4. ❓ Real-time status tracking
5. ❓ Secure file download
6. ❓ Proper error handling and logging
7. ❓ Processing options configuration
8. ❓ Performance metrics preservation

## Risks and Mitigations

### Risk: Long-running processing blocks web server
**Mitigation**: Background threading with queue management

### Risk: Memory usage with large files  
**Mitigation**: Use PerformanceOptimizedKorrekturtool for large files

### Risk: File storage security
**Mitigation**: UUID-based filenames, configurable cleanup, access validation

### Risk: Job state persistence across server restarts
**Mitigation**: Job serialization (can be upgraded to database later)

## Files to Create/Modify

### New Files
- `web/models/__init__.py`
- `web/models/job.py`
- `web/services/__init__.py` 
- `web/services/job_manager.py`
- `web/services/processor_integration.py`
- `web/services/background_processor.py`
- `web/api/process.py`

### Modified Files
- `web/api/routes.py` (add new endpoints)
- `web/utils/api_config.py` (update endpoint list)
- `web/config.py` (add processing configuration)

## Estimated Timeline
- **Phase 1**: 2 hours (models and services)
- **Phase 2**: 1 hour (background processing)  
- **Phase 3**: 2 hours (API endpoints)
- **Phase 4**: 1 hour (testing and integration)
- **Total**: 6 hours (matches issue estimate of 4-6 hours)