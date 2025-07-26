# Issue #26: Core API Integration Plan

**Issue URL**: https://github.com/m2ix4i/Korrekturtool-BA/issues/26

## 🎯 Problem Analysis

The frontend UI is complete but currently shows placeholder messages instead of processing documents. The main gap is at **line 467 in `web/static/js/app.js`** where there's a TODO that needs to be replaced with actual API integration.

## 🔍 Current Architecture Understanding

### Frontend Components:
- **Upload Handler** (`upload-handler.js`): Manages file state with `getState()` method returning:
  ```javascript
  {
    hasFile: boolean,
    selectedFile: File object,
    fileName: string,
    fileSize: number
  }
  ```

- **Config Manager** (`config-manager.js`): Exports processing configuration via `exportForProcessing()`:
  ```javascript
  {
    processing_mode: string,
    categories: array,
    output_filename: string,
    processing_priority: string,
    comment_density: string
  }
  ```

### Backend API Endpoints:
- `POST /api/v1/upload` - File upload with validation
- `POST /api/v1/process` - Document processing request
- `GET /api/v1/status/<job_id>` - Processing status polling
- `GET /api/v1/download/<file_id>` - Result download

## 📋 Implementation Plan

### Step 1: Create API Service Module
Create `web/static/js/services/api-service.js` to centralize all API interactions:
- Upload file method
- Process document method
- Check status method
- Download result method
- Error handling utilities

### Step 2: Implement File Upload Integration
Modify the main form submission handler to:
1. Get selected file from upload handler
2. Create FormData with the file
3. Call upload API endpoint
4. Handle upload response and errors
5. Extract file_id for processing

### Step 3: Implement Processing Integration
After successful upload:
1. Get configuration from config manager
2. Combine file_id with configuration
3. Call process API endpoint
4. Handle processing response
5. Store job_id for status tracking

### Step 4: Add Application State Management
Update application state to track:
- Current file_id
- Current job_id
- Processing status
- Error states

### Step 5: Integrate with Existing UI Patterns
- Use existing `showSuccessMessage()` and `handleError()` methods
- Maintain current event bus communication
- Preserve existing loading states and transitions

## 🔧 Implementation Details

### Current TODO Location (app.js:467):
```javascript
// Current implementation:
// TODO: Implement actual processing logic
this.showSuccessMessage('Konfiguration validiert! Verarbeitung würde hier starten...');

// Will be replaced with:
await this.processDocument();
```

### New Method Structure:
```javascript
async processDocument() {
    try {
        // 1. Validate prerequisites
        const uploadState = this.uploadHandler.getState();
        if (!uploadState.hasFile) {
            throw new Error('Keine Datei ausgewählt');
        }
        
        // 2. Upload file
        const uploadResult = await this.apiService.uploadFile(uploadState.selectedFile);
        this.state.currentFileId = uploadResult.file_id;
        
        // 3. Get configuration
        const config = this.configManager.exportForProcessing();
        
        // 4. Start processing
        const processResult = await this.apiService.processDocument({
            file_id: this.state.currentFileId,
            ...config
        });
        this.state.currentJobId = processResult.job_id;
        
        // 5. Update UI state
        this.showProcessingState();
        
        // 6. Emit events for other components
        this.eventBus.emit('processing:started', {
            jobId: this.state.currentJobId,
            fileId: this.state.currentFileId
        });
        
    } catch (error) {
        this.handleError(error, 'Fehler beim Starten der Verarbeitung');
    }
}
```

## 🧪 Testing Plan

### Manual Testing:
1. Upload a test DOCX file
2. Configure processing options
3. Submit for processing
4. Verify API calls are made correctly
5. Check error handling for various scenarios

### API Testing:
- Test upload with valid/invalid files
- Test processing with different configurations
- Test error responses and network failures

## 🎯 Success Criteria

- [ ] TODO placeholder replaced with actual API integration
- [ ] File upload works through web interface
- [ ] Processing request submitted successfully
- [ ] Application state updates correctly
- [ ] Error handling maintains user experience
- [ ] All existing UI patterns preserved

## 📝 Files to Modify

1. **New File**: `web/static/js/services/api-service.js` - API communication layer
2. **Modify**: `web/static/js/app.js` - Replace TODO with processDocument() method
3. **Update**: Application state management for tracking IDs

## 🔗 Integration Points

- Upload Handler: `getState()` method for file access
- Config Manager: `exportForProcessing()` method for configuration
- Event Bus: Emit processing events for other components
- Error Handling: Use existing `handleError()` method
- UI Feedback: Use existing `showSuccessMessage()` and loading states