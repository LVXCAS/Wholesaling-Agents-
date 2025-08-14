# 🔧 Data Processor Troubleshooting Guide

## Common Issues and Solutions

### 1. "Failed to fetch" Error

**Problem:** The frontend shows "Processing failed: Failed to fetch"

**Causes & Solutions:**

#### A. API Server Not Running
```bash
# Check if server is running
curl http://localhost:8000/docs

# If not running, start it:
python start_api_server.py
# OR
uvicorn app.api.main:app --reload
```

#### B. Port Conflicts
```bash
# Check what's using port 8000
netstat -an | findstr :8000

# Use different port
uvicorn app.api.main:app --reload --port 8001
```

#### C. CORS Issues
The API should have CORS enabled. Check `app/api/main.py` has:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Import Errors

**Problem:** `ModuleNotFoundError` when starting server

**Solution:**
```bash
# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd real-estate-empire
python -m uvicorn app.api.main:app --reload
```

### 3. Gemini API Issues

**Problem:** AI processing fails

**Solutions:**

#### A. Missing API Key
```bash
# Set environment variable
export GEMINI_API_KEY=your_api_key_here

# Or create .env file
echo "GEMINI_API_KEY=your_key" > .env
```

#### B. Invalid API Key
- Get new key from: https://makersuite.google.com/app/apikey
- Verify key format: `AIza...` (39 characters)

#### C. API Quota Exceeded
- Check your Google AI Studio quota
- Wait for quota reset or upgrade plan

### 4. File Upload Issues

**Problem:** ZIP files won't upload or process

**Solutions:**

#### A. File Size Limits
```python
# In main.py, increase limits:
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]
)

# Set max file size (default 16MB)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
```

#### B. Unsupported File Formats
Supported formats inside ZIP:
- `.csv` - Comma-separated values
- `.xlsx`, `.xls` - Excel files
- `.json` - JSON data
- `.tsv` - Tab-separated values
- `.txt` - Plain text

#### C. Corrupted ZIP Files
```bash
# Test ZIP file
unzip -t your_file.zip

# Create new ZIP
zip -r new_file.zip your_data_folder/
```

### 5. Database Connection Issues

**Problem:** Database errors on startup

**Solutions:**

#### A. SQLite Issues (Default)
```bash
# Remove corrupted database
rm -f *.db

# Restart server to recreate
python start_api_server.py
```

#### B. PostgreSQL Issues
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
sudo service postgresql start
```

### 6. Memory Issues

**Problem:** Server crashes with large files

**Solutions:**

#### A. Increase Memory Limits
```bash
# Start with more memory
uvicorn app.api.main:app --reload --workers 1 --limit-max-requests 1000
```

#### B. Process Files in Chunks
```python
# In data_processor_service.py
CHUNK_SIZE = 10000  # Process 10k rows at a time
```

## 🧪 Testing Steps

### 1. Basic API Test
```bash
# Test API connection
python test_data_processor_api.py
```

### 2. Manual Endpoint Test
```bash
# Test supported formats
curl http://localhost:8000/api/v1/data-processor/supported-formats

# Test with sample file
curl -X POST "http://localhost:8000/api/v1/data-processor/auto-format" \
     -F "file=@sample.zip"
```

### 3. Frontend Test
```bash
# Open standalone test page
open data_processor_standalone.html
```

## 🔍 Debug Mode

### Enable Detailed Logging
```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# In data_processor_service.py
logger.setLevel(logging.DEBUG)
```

### Check Server Logs
```bash
# Start with verbose logging
uvicorn app.api.main:app --reload --log-level debug
```

## 📊 Performance Optimization

### 1. Large File Handling
```python
# Stream processing for large files
async def process_large_file(file_path):
    chunk_size = 1024 * 1024  # 1MB chunks
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            yield chunk
```

### 2. Memory Management
```python
# Clear memory after processing
import gc
gc.collect()
```

### 3. Async Processing
```python
# Use background tasks for long operations
from fastapi import BackgroundTasks

@router.post("/process-async")
async def process_async(background_tasks: BackgroundTasks, file: UploadFile):
    background_tasks.add_task(process_file_background, file)
    return {"message": "Processing started"}
```

## 🚨 Emergency Recovery

### 1. Reset Everything
```bash
# Stop all servers
pkill -f uvicorn

# Clear temp files
rm -rf /tmp/data_processor_*
rm -rf /tmp/export_*

# Reset database
rm -f *.db

# Restart fresh
python start_api_server.py
```

### 2. Minimal Test Setup
```bash
# Create minimal test
echo "name,value" > test.csv
echo "test,123" >> test.csv
zip test.zip test.csv

# Test with curl
curl -X POST "http://localhost:8000/api/v1/data-processor/auto-format" \
     -F "file=@test.zip"
```

## 📞 Getting Help

### 1. Check Logs
```bash
# Server logs
tail -f server.log

# System logs
journalctl -f -u your-service
```

### 2. Environment Info
```bash
# Python version
python --version

# Installed packages
pip list | grep -E "(fastapi|uvicorn|pandas|google)"

# System info
uname -a
```

### 3. Create Issue Report
Include:
- Error message (full traceback)
- Python version
- Operating system
- File size and type
- Steps to reproduce

## 🎯 Quick Fixes

### Most Common Solutions:
1. **Restart the API server**
2. **Check GEMINI_API_KEY is set**
3. **Verify you're in the right directory**
4. **Clear browser cache**
5. **Try a smaller test file first**

### Emergency Commands:
```bash
# Kill all Python processes
pkill -f python

# Restart everything
python start_api_server.py

# Test with minimal data
python test_data_processor_api.py
```

---

**Still having issues?** Check the server logs and try the standalone test page first!