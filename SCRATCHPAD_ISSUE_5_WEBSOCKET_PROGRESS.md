# GitHub Issue #5: Add progress tracking and WebSocket support

**Issue Link**: https://github.com/m2ix4i/Korrekturtool-BA/issues/5  
**Current Status**: 🚀 **READY TO IMPLEMENT** - Dependencies satisfied

## Issue Analysis Summary

### Requirements from Issue Description
- [ ] Add WebSocket endpoint for real-time communication
- [ ] Implement progress tracking in processing pipeline  
- [ ] Create job status broadcasting system
- [ ] Add processing stage indicators (parsing, analyzing, integrating, etc.)
- [ ] Include time estimates and completion percentage
- [ ] Handle WebSocket connection management
- [ ] Add error broadcasting for failed jobs

### Current Infrastructure State ✅ READY

**Backend Structure**: ✅ Complete (Issue #2 solved)
- Flask application with blueprint structure
- **Flask-SocketIO==5.3.6** already installed as dependency
- Configuration management system ready
- Error handling middleware in place

**File Upload API**: ✅ Complete (Issue #3 solved)  
- Secure file upload with validation
- File ID generation system
- Upload/cleanup endpoints working

**Processing Integration**: 🔄 Planned (Issue #4 in progress)
- Detailed implementation plan exists (`issue-4-plan.md`)
- API routes already defined but processor.py missing
- Job management system designed but not implemented

## Technical Architecture Analysis

### WebSocket Event System Design
Based on issue requirements, implementing standardized message format:

```javascript
// Connection Management
connect -> join room with job_id

// Progress Updates  
progress_update: {
  "job_id": "uuid",
  "stage": "parsing|analyzing|integrating|formatting", 
  "progress": 45,
  "message": "Analyzing text chunks...",
  "estimated_remaining": "30 seconds"
}

// Completion Events
job_completed: {
  "job_id": "uuid", 
  "success": true,
  "download_url": "/api/download/uuid",
  "processing_time": "87 seconds"
}

// Error Events
job_failed: {
  "job_id": "uuid",
  "success": false, 
  "error": "Processing failed: Invalid document structure",
  "stage": "parsing"
}
```

### Integration Strategy
Since Issue #4 (processing integration) is planned but not implemented, I'll design Issue #5 to be **ready for integration**:

1. **Create WebSocket infrastructure** independent of specific job system
2. **Design progress tracking service** with generic interfaces  
3. **Implement broadcasting system** that can work with any job management
4. **Create progress emitter utility** for easy processor integration

## Implementation Plan

### Phase 1: WebSocket Infrastructure Setup
**File**: `web/websocket/__init__.py`
**Purpose**: Flask-SocketIO initialization and configuration

```python
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")

def init_websocket(app):
    """Initialize WebSocket with Flask app"""
    socketio.init_app(app, 
                     cors_allowed_origins=app.config.get('CORS_ORIGINS'),
                     logger=True,
                     engineio_logger=True)
    return socketio
```

### Phase 2: Progress Tracking Service  
**File**: `web/services/progress_tracker.py`
**Purpose**: Centralized progress tracking and broadcasting

```python
class ProgressTracker:
    """Centralized progress tracking with WebSocket broadcasting"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.active_jobs = {}  # job_id -> job_info
        
    def start_job(self, job_id: str, stages: List[str]) -> None:
        """Initialize job tracking"""
        
    def update_progress(self, job_id: str, stage: str, progress: int, message: str) -> None:
        """Update and broadcast progress"""
        
    def complete_job(self, job_id: str, success: bool, result_data: dict) -> None:
        """Mark job complete and broadcast final status"""
        
    def fail_job(self, job_id: str, error: str, stage: str) -> None:
        """Mark job failed and broadcast error"""
```

### Phase 3: WebSocket Event Handlers
**File**: `web/websocket/progress.py`  
**Purpose**: WebSocket connection and event management

```python
from flask_socketio import emit, join_room, leave_room, disconnect

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    
@socketio.on('join_job')  
def handle_join_job(data):
    """Join room for specific job updates"""
    
@socketio.on('leave_job')
def handle_leave_job(data):
    """Leave job room"""
    
@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
```

### Phase 4: Progress Emitter Utility
**File**: `src/utils/progress_emitter.py`
**Purpose**: Generic progress emission for processor integration

```python
class ProgressEmitter:
    """Generic progress emitter for processing pipeline integration"""
    
    def __init__(self, job_id: str, progress_tracker: ProgressTracker):
        self.job_id = job_id
        self.progress_tracker = progress_tracker
        self.current_stage = None
        self.stage_progress = 0
        
    def set_stages(self, stages: List[str]) -> None:
        """Define processing stages"""
        
    def start_stage(self, stage: str) -> None:
        """Start new processing stage"""
        
    def update_stage_progress(self, progress: int, message: str) -> None:
        """Update current stage progress"""
        
    def complete_stage(self) -> None:
        """Mark current stage complete"""
```

### Phase 5: Flask App Integration
**File**: `web/app.py` (modifications)
**Purpose**: Integrate WebSocket with Flask application

```python
from web.websocket import init_websocket

def create_app(config_class=WebConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # ... existing setup ...
    
    # Initialize WebSocket
    socketio = init_websocket(app)
    
    return app, socketio  # Return both app and socketio
```

### Phase 6: Configuration Updates
**File**: `web/config.py` (additions)
**Purpose**: WebSocket-specific configuration

```python
class Config:
    # ... existing config ...
    
    # WebSocket configuration
    WEBSOCKET_PING_TIMEOUT = int(os.environ.get('WEBSOCKET_PING_TIMEOUT', 60))
    WEBSOCKET_PING_INTERVAL = int(os.environ.get('WEBSOCKET_PING_INTERVAL', 25))
    WEBSOCKET_MAX_CONNECTIONS = int(os.environ.get('WEBSOCKET_MAX_CONNECTIONS', 100))
    
    # Progress tracking configuration
    PROGRESS_UPDATE_INTERVAL = float(os.environ.get('PROGRESS_UPDATE_INTERVAL', 1.0))
    JOB_CLEANUP_TIMEOUT = int(os.environ.get('JOB_CLEANUP_TIMEOUT', 3600))  # 1 hour
```

## Detailed Technical Specifications

### WebSocket Event Specification
```yaml
Events:
  client_to_server:
    - connect: Client establishes connection
    - join_job: {"job_id": "uuid"} - Join job-specific room
    - leave_job: {"job_id": "uuid"} - Leave job room
    - disconnect: Client disconnects
    
  server_to_client:
    - job_started: {"job_id": "uuid", "stages": ["parsing", "analyzing", ...]}
    - progress_update: {"job_id": "uuid", "stage": "analyzing", "progress": 45, "message": "..."}
    - stage_completed: {"job_id": "uuid", "stage": "parsing", "next_stage": "analyzing"}
    - job_completed: {"job_id": "uuid", "success": true, "download_url": "...", "metrics": {...}}
    - job_failed: {"job_id": "uuid", "error": "...", "stage": "parsing"}
```

### Progress Calculation Strategy
```python
# Stage-based progress calculation
stages = ["parsing", "analyzing", "integrating", "formatting"]
stage_weights = {"parsing": 0.15, "analyzing": 0.60, "integrating": 0.20, "formatting": 0.05}

def calculate_overall_progress(current_stage: str, stage_progress: int) -> int:
    """Calculate overall job progress based on stage weights"""
    # Implementation accounts for stage weights and current stage progress
```

### Connection Management Strategy
```python
# Room-based connection management
# Each job gets its own room: f"job_{job_id}"
# Clients join/leave rooms as needed
# Broadcast updates only to relevant room members
```

## Integration Points with Future Issue #4

### Job System Integration
When Issue #4 (processing integration) is implemented, the WebSocket system will integrate via:

1. **Job Creation**: `ProgressTracker.start_job(job_id, stages)`  
2. **Processing Updates**: `ProgressEmitter` used within processors
3. **Job Completion**: `ProgressTracker.complete_job(job_id, success, result)`

### Processor Integration Pattern
```python
# Example integration in future processor.py
def process_document_with_progress(file_path: str, job_id: str):
    emitter = ProgressEmitter(job_id, progress_tracker)
    emitter.set_stages(["parsing", "analyzing", "integrating", "formatting"])
    
    # Parsing stage
    emitter.start_stage("parsing")
    # ... parsing logic with progress updates ...
    emitter.complete_stage()
    
    # Continue for other stages...
```

## File Structure After Implementation

```
web/
├── websocket/
│   ├── __init__.py          # SocketIO initialization
│   └── progress.py          # WebSocket event handlers
├── services/
│   ├── __init__.py         
│   └── progress_tracker.py  # Progress tracking service
├── app.py                   # Modified for WebSocket integration
└── config.py                # WebSocket configuration added

src/utils/
└── progress_emitter.py      # Generic progress emitter utility

tests/
├── test_websocket_progress.py   # WebSocket testing
└── test_progress_tracker.py     # Progress tracking tests
```

## Testing Strategy

### Unit Tests
- `ProgressTracker` class functionality
- `ProgressEmitter` utility functions  
- Progress calculation algorithms
- Configuration loading

### Integration Tests  
- WebSocket connection establishment
- Room join/leave functionality
- Progress event broadcasting
- Error event handling

### Manual Testing
- Multiple client connections
- Progress updates across multiple jobs
- Connection cleanup on disconnect
- Error broadcasting scenarios

## Risk Assessment & Mitigation

### Technical Risks
- **WebSocket connection stability**: Mitigated by proper error handling and reconnection logic
- **Memory usage with many connections**: Mitigated by connection limits and cleanup
- **Event ordering**: Mitigated by proper sequencing in progress tracker

### Integration Risks  
- **Issue #4 dependency**: Mitigated by designing generic interfaces
- **Performance impact**: Mitigated by efficient broadcasting and rate limiting
- **Scalability**: Mitigated by room-based connection management

## Dependencies & Blockers

### Dependencies: ✅ ALL SATISFIED
- Issue #2 (Flask backend): ✅ Complete with SocketIO dependency
- Issue #3 (File upload API): ✅ Complete - provides file IDs
- Flask-SocketIO library: ✅ Already installed

### No Current Blockers
Ready to proceed with implementation immediately.

## Success Criteria

### Functional Requirements
- [ ] WebSocket endpoint operational with client connections
- [ ] Progress tracking service broadcasting standardized events
- [ ] Job status management with room-based connections
- [ ] Processing stage indicators with time estimates
- [ ] Error broadcasting for failed operations  
- [ ] Connection cleanup and management
- [ ] Ready for processor integration (Issue #4)

### Non-Functional Requirements  
- [ ] WebSocket connections stable and reliable
- [ ] Progress updates delivered within 1 second
- [ ] Support for 50+ concurrent connections
- [ ] Proper cleanup preventing memory leaks
- [ ] Comprehensive error handling and logging

## Implementation Steps (Small, Manageable Tasks)

### Step 1: WebSocket Infrastructure (30 minutes)
- Create `web/websocket/__init__.py` with SocketIO setup
- Modify `web/app.py` for WebSocket integration
- Add WebSocket configuration to `web/config.py`

### Step 2: Progress Tracking Service (45 minutes)  
- Implement `web/services/progress_tracker.py`
- Create job tracking data structures
- Add progress calculation and broadcasting logic

### Step 3: WebSocket Event Handlers (30 minutes)
- Implement `web/websocket/progress.py` 
- Add connection management (connect, disconnect, rooms)
- Create event handlers for job tracking

### Step 4: Progress Emitter Utility (30 minutes)
- Create `src/utils/progress_emitter.py`
- Implement generic progress emission interface
- Add stage management and progress calculation

### Step 5: Testing and Integration (45 minutes)
- Create unit tests for all components
- Manual testing with WebSocket clients  
- Integration testing with mock jobs
- Documentation and cleanup

## Timeline Estimate
- **Total Effort**: 3 hours (as estimated in issue)
- **Implementation**: 2.5 hours (5 steps above)
- **Testing/Documentation**: 0.5 hours
- **Ready for Issue #4 Integration**: Immediately upon completion

## Integration Readiness for Issue #4

This implementation provides a **complete WebSocket infrastructure** that Issue #4 can immediately use:

1. **ProgressTracker**: Ready for job management integration
2. **ProgressEmitter**: Ready for processor pipeline integration  
3. **WebSocket Infrastructure**: Fully operational for broadcasting
4. **Standardized Events**: Consistent messaging format defined

When Issue #4 is implemented, integration requires only:
- Adding `progress_emitter` to processing functions
- Calling `progress_tracker.start_job()` when jobs begin
- Using standard progress update calls throughout processing

---

**Analysis Date**: 2025-07-24  
**Analyst**: Claude Code  
**Confidence**: 95% - Clear requirements, dependencies satisfied, integration strategy defined