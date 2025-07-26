# German Thesis Correction Tool - API Documentation

## Overview

This document provides comprehensive documentation for the German Bachelor Thesis Correction Tool Web API (Issue #4 Implementation). The API provides endpoints for uploading documents, processing them with AI-powered correction tools, and downloading the results.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

Currently, the API does not require authentication. This may be added in future versions.

## API Endpoints

### 1. File Upload

#### Upload Document
```http
POST /api/v1/upload
```

Upload a DOCX document for processing.

**Content-Type:** `multipart/form-data`

**Request:**
```
file: (binary) DOCX file to upload
```

**Response:**
```json
{
  "success": true,
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "File uploaded successfully",
  "filename": "original_filename.docx",
  "file_size": 1024000
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "invalid_file_type",
  "message": "Only DOCX files are supported"
}
```

### 2. Document Processing

#### Submit Processing Job
```http
POST /api/v1/process
```

Submit a document for AI-powered correction processing.

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "processing_mode": "complete",
  "options": {
    "categories": ["grammar", "style", "clarity", "academic"],
    "output_filename": "corrected_thesis.docx"
  }
}
```

**Parameters:**
- `file_id` (string, required): UUID of uploaded file
- `processing_mode` (string, required): Processing mode
  - `"complete"`: Full-featured processing with multi-pass analysis
  - `"performance"`: Performance-optimized for large documents
- `options` (object, optional): Processing configuration
  - `categories` (array, optional): Analysis categories to include
    - Valid values: `"grammar"`, `"style"`, `"clarity"`, `"academic"`
    - Default: All categories
  - `output_filename` (string, optional): Custom output filename

**Response:**
```json
{
  "success": true,
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "estimated_time_seconds": 90,
  "message": "Job submitted for processing"
}
```

**Error Responses:**
```json
{
  "success": false,
  "error": "validation_error",
  "message": "file_id is required"
}
```

```json
{
  "success": false,
  "error": "file_not_found",
  "message": "File 550e8400-e29b-41d4-a716-446655440000 not found. Please upload the file first."
}
```

### 3. Job Status

#### Get Job Status
```http
GET /api/v1/status/{job_id}
```

Get the current status and progress of a processing job.

**Parameters:**
- `job_id` (string): UUID of the processing job

**Response:**
```json
{
  "success": true,
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "progress": {
    "overall_progress": 45,
    "current_stage": "analyzing",
    "stage_progress": 60,
    "message": "Analyzing document with AI..."
  },
  "estimated_time_seconds": 90,
  "elapsed_time_seconds": 42,
  "created_at": "2025-01-24T10:30:00Z",
  "started_at": "2025-01-24T10:30:05Z",
  "completed_at": null
}
```

**Completed Job Response:**
```json
{
  "success": true,
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "progress": {
    "overall_progress": 100,
    "current_stage": "completed",
    "stage_progress": 100,
    "message": "Processing completed successfully"
  },
  "estimated_time_seconds": 90,
  "elapsed_time_seconds": 87,
  "created_at": "2025-01-24T10:30:00Z",
  "started_at": "2025-01-24T10:30:05Z",
  "completed_at": "2025-01-24T10:31:32Z",
  "result": {
    "output_file_id": "987fcdeb-51a2-43d5-b789-012345678901",
    "total_suggestions": 42,
    "successful_integrations": 38,
    "processing_time_seconds": 87.5,
    "cost_estimate": 0.0084,
    "download_url": "/api/v1/download/987fcdeb-51a2-43d5-b789-012345678901"
  }
}
```

**Failed Job Response:**
```json
{
  "success": true,
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "failed",
  "progress": {
    "overall_progress": 25,
    "current_stage": "parsing",
    "stage_progress": 100,
    "message": "Processing failed"
  },
  "error_message": "Document could not be parsed. Please check the file format.",
  "created_at": "2025-01-24T10:30:00Z",
  "started_at": "2025-01-24T10:30:05Z",
  "completed_at": "2025-01-24T10:30:15Z"
}
```

### 4. File Download

#### Download Processed File
```http
GET /api/v1/download/{file_id}
```

Download the processed document with corrections.

**Parameters:**
- `file_id` (string): UUID of the output file (from job result)

**Response:**
- **Success**: Binary file download with headers:
  - `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  - `Content-Disposition: attachment; filename="corrected_{file_id}.docx"`

**Error Response:**
```json
{
  "success": false,
  "error": "file_not_found",
  "message": "File not found. It may have been processed too long ago and cleaned up."
}
```

### 5. System Status

#### Get Processor Status
```http
GET /api/v1/processor/status
```

Get the current status of the background processing system (for monitoring).

**Response:**
```json
{
  "success": true,
  "is_running": true,
  "queue_size": 2,
  "worker_thread_alive": true,
  "is_processing": true,
  "jobs_processed_today": 15,
  "average_processing_time": 95.5
}
```

## Job Status Values

| Status | Description |
|--------|-------------|
| `pending` | Job created and waiting to be processed |
| `processing` | Job is currently being processed |
| `completed` | Job completed successfully |
| `failed` | Job failed due to an error |

## Processing Stages

During processing, the `current_stage` field indicates the current phase:

| Stage | Description | Typical Duration |
|-------|-------------|------------------|
| `initializing` | Setting up processing environment | 5% |
| `parsing` | Extracting text from document | 10% |
| `chunking` | Breaking text into analyzable segments | 10% |
| `analyzing` | AI-powered analysis and suggestion generation | 60% |
| `formatting` | Formatting suggestions as comments | 5% |
| `integrating` | Inserting comments into Word document | 8% |
| `finalizing` | Saving final document | 2% |

## Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `validation_error` | Invalid request parameters | 400 |
| `file_not_found` | Requested file does not exist | 404 |
| `processing_error` | Error during document processing | 500 |
| `internal_error` | Internal server error | 500 |

## Rate Limiting

Currently, no rate limiting is implemented. This may be added in future versions.

## Real-time Updates (WebSocket)

For real-time progress updates during processing, connect to the WebSocket endpoint:

```javascript
const socket = io('http://localhost:5000');

// Join job room for updates
socket.emit('join_job', { job_id: 'your-job-id' });

// Listen for progress updates
socket.on('progress_update', function(data) {
    console.log(`Progress: ${data.progress}% - ${data.message}`);
});

// Listen for completion
socket.on('job_completed', function(data) {
    console.log('Job completed!', data);
});
```

## SDK Examples

### Python

```python
import requests
import time

# Upload file
with open('thesis.docx', 'rb') as f:
    upload_response = requests.post(
        'http://localhost:5000/api/v1/upload',
        files={'file': f}
    )
    file_id = upload_response.json()['file_id']

# Submit for processing
process_response = requests.post(
    'http://localhost:5000/api/v1/process',
    json={
        'file_id': file_id,
        'processing_mode': 'complete',
        'options': {
            'categories': ['grammar', 'style', 'clarity']
        }
    }
)
job_id = process_response.json()['job_id']

# Poll for completion
while True:
    status_response = requests.get(f'http://localhost:5000/api/v1/status/{job_id}')
    status = status_response.json()
    
    if status['status'] == 'completed':
        download_url = status['result']['download_url']
        break
    elif status['status'] == 'failed':
        print(f"Processing failed: {status['error_message']}")
        break
    
    time.sleep(5)

# Download result
download_response = requests.get(f'http://localhost:5000{download_url}')
with open('corrected_thesis.docx', 'wb') as f:
    f.write(download_response.content)
```

### JavaScript

```javascript
// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('/api/v1/upload', {
    method: 'POST',
    body: formData
});
const { file_id } = await uploadResponse.json();

// Submit for processing
const processResponse = await fetch('/api/v1/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        file_id: file_id,
        processing_mode: 'complete',
        options: {
            categories: ['grammar', 'style', 'clarity']
        }
    })
});
const { job_id } = await processResponse.json();

// Poll for completion
const pollStatus = async () => {
    const statusResponse = await fetch(`/api/v1/status/${job_id}`);
    const status = await statusResponse.json();
    
    if (status.status === 'completed') {
        window.location.href = status.result.download_url;
    } else if (status.status === 'failed') {
        console.error('Processing failed:', status.error_message);
    } else {
        setTimeout(pollStatus, 5000);
    }
};
pollStatus();
```

### cURL

```bash
# Upload file
UPLOAD_RESPONSE=$(curl -X POST \
    -F "file=@thesis.docx" \
    http://localhost:5000/api/v1/upload)

FILE_ID=$(echo $UPLOAD_RESPONSE | jq -r '.file_id')

# Submit for processing
PROCESS_RESPONSE=$(curl -X POST \
    -H "Content-Type: application/json" \
    -d "{
        \"file_id\": \"$FILE_ID\",
        \"processing_mode\": \"complete\",
        \"options\": {
            \"categories\": [\"grammar\", \"style\", \"clarity\"]
        }
    }" \
    http://localhost:5000/api/v1/process)

JOB_ID=$(echo $PROCESS_RESPONSE | jq -r '.job_id')

# Check status
curl http://localhost:5000/api/v1/status/$JOB_ID

# Download (when completed)
curl -o corrected_thesis.docx \
    http://localhost:5000/api/v1/download/OUTPUT_FILE_ID
```

## Security Considerations

### File Security
- All uploaded files are validated for type and content
- File paths use UUID-based naming to prevent conflicts and path traversal
- Files are stored in sandboxed directories
- Automatic cleanup of old files

### Download Security
- File access is validated against path traversal attacks
- File integrity is verified using SHA-256 hashes
- Download attempts are logged for audit purposes
- Invalid file IDs are rejected with proper error handling

### Input Validation
- All API inputs are validated for type and format
- File uploads are limited to DOCX format only
- UUIDs are validated for proper format
- Processing options are validated against allowed values

## Deployment

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional (with defaults)
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
TEMP_FOLDER=temp
MAX_CONTENT_LENGTH=104857600  # 100MB
JOB_STORAGE_PATH=jobs.json
```

### Docker Deployment
```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "web/app.py"]
```

### Health Check
```bash
curl http://localhost:5000/health
```

## Troubleshooting

### Common Issues

1. **"File not found" errors**
   - Ensure file was uploaded successfully before processing
   - Check that file ID is correct and properly formatted UUID

2. **Processing timeouts**
   - Large documents may take longer to process
   - Use performance mode for large files
   - Check system resources (CPU, memory)

3. **Download failures**
   - Files are automatically cleaned up after 24 hours
   - Ensure output file ID is from completed job result

### Logging

The API provides comprehensive logging at these levels:
- `INFO`: Normal operations, job lifecycle events
- `WARNING`: Security events, validation failures
- `ERROR`: Processing failures, system errors

### Performance Optimization

- Use `performance` mode for documents >50 pages
- Consider processing fewer categories for faster results
- Monitor system resources during heavy usage

## Changelog

### Version 1.0.0
- Initial release with complete processing pipeline integration
- Support for both complete and performance processing modes
- Real-time progress tracking via WebSocket
- Comprehensive security features
- Integration tests and documentation