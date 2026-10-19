# KILCRITIC SUPREME ENGINE v6.1.1-POWER
## HIGH-QUALITY FIX INTEGRATION GUIDE

### 📋 OVERVIEW

This guide shows how to integrate the high-quality fixes into your existing system to resolve:
- 422 Validation Errors (Unprocessable Content)
- 500 Internal Server Errors
- JSON decode errors
- Missing input validation

---

### 🚀 STEP-BY-STEP INTEGRATION

#### **STEP 1: Add New Files to Your Project**

Copy these 4 new files into your `app/` directory:

```
app/
├── validators.py          ← NEW: Validation functions
├── exceptions.py          ← NEW: Custom exceptions
├── middleware.py          ← NEW: Request middleware
└── (existing files...)
```

**Files provided in scratchpad:**
- `/tmp/.../scratchpad/validators.py`
- `/tmp/.../scratchpad/exceptions.py`
- `/tmp/.../scratchpad/middleware.py`

---

#### **STEP 2: Replace Existing Service Files**

Replace these files with the fixed versions:

**Option A: Replace quality.py**
```bash
# Current file location: app/services/quality.py
# Backup current:
cp app/services/quality.py app/services/quality.py.backup

# Copy fixed version:
cp /tmp/.../scratchpad/quality_fixed.py app/services/quality.py
```

**Option B: Replace metadata.py**
```bash
# Current file location: app/services/metadata.py
# Backup current:
cp app/services/metadata.py app/services/metadata.py.backup

# Copy fixed version:
cp /tmp/.../scratchpad/metadata_fixed.py app/services/metadata.py
```

---

#### **STEP 3: Update main.py to Use Middleware**

Edit `app/main.py` and add middleware right after creating the FastAPI app:

```python
# BEFORE (current):
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='KILCRITIC SUPREME ENGINE', version='6.1.1-POWER')
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, ...)


# AFTER (with new middleware):
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .middleware import RequestValidationMiddleware, ErrorHandlingMiddleware, RequestLoggingMiddleware

app = FastAPI(title='KILCRITIC SUPREME ENGINE', version='6.1.1-POWER')

# Add middleware in REVERSE order (bottom runs first)
app.add_middleware(RequestLoggingMiddleware)          # Logs all requests
app.add_middleware(ErrorHandlingMiddleware)           # Catches exceptions
app.add_middleware(RequestValidationMiddleware)       # Validates requests
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, ...)
```

---

#### **STEP 4: Update Pydantic Models in main.py**

Replace the old models with new versions:

```python
# OLD models (remove these):
class QualityIn(BaseModel):
    topic: str
    audience: str = 'GENERAL'
    content_type: str = 'video'
    flags: list[str] = Field(default_factory=list)

class MetadataIn(BaseModel):
    topic: str
    content_type: str = 'video'
    platform: str


# NEW models (add these):
from pydantic import BaseModel, Field, validator

class QualityIn(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500, description="Content topic/title")
    audience: str = Field('GENERAL', description="Target audience")
    content_type: str = Field('video', description="Type of content")
    flags: list[str] = Field(default_factory=list, description="Validation flags")
    
    @validator('topic')
    def topic_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('topic cannot be empty')
        return v.strip()
    
    @validator('audience')
    def audience_valid(cls, v):
        valid = {'GENERAL', 'KIDS', 'MATURE', 'ADULT', 'EDUCATIONAL'}
        if v and v not in valid:
            raise ValueError(f'audience must be one of: {", ".join(valid)}')
        return v or 'GENERAL'
    
    @validator('content_type')
    def content_type_valid(cls, v):
        valid = {'video', 'photo', 'wallpaper', 'story'}
        if v not in valid:
            raise ValueError(f'content_type must be one of: {", ".join(valid)}')
        return v


class MetadataIn(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500, description="Content topic")
    content_type: str = Field('video', description="Type of content")
    platform: str = Field(..., description="Target platform")
    
    @validator('topic')
    def topic_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('topic cannot be empty')
        return v.strip()
    
    @validator('platform')
    def platform_valid(cls, v):
        valid = {'youtube', 'facebook', 'instagram', 'tiktok', 'x'}
        if not v or v.lower() not in valid:
            raise ValueError(f'platform must be one of: {", ".join(valid)}')
        return v.lower()
    
    @validator('content_type')
    def content_type_valid(cls, v):
        valid = {'video', 'photo', 'wallpaper', 'story'}
        if v not in valid:
            raise ValueError(f'content_type must be one of: {", ".join(valid)}')
        return v
```

---

#### **STEP 5: Update API Endpoints**

Replace the old endpoints with error-safe versions:

```python
# OLD endpoint (remove):
@app.post('/api/quality/check')
def quality(b: QualityIn):
    return validate_content(b.topic, b.audience, b.content_type, b.flags)


# NEW endpoint (add):
@app.post('/api/quality/check')
def quality(b: QualityIn):
    """
    Validate content quality and compliance
    
    Request body:
    {
        "topic": "string (required, 2-500 chars)",
        "audience": "GENERAL|KIDS|MATURE|ADULT|EDUCATIONAL (optional, default GENERAL)",
        "content_type": "video|photo|wallpaper|story (optional, default video)",
        "flags": ["list", "of", "flags"] (optional)
    }
    
    Response:
    {
        "ok": true/false,
        "issues": ["list of error codes"],
        "audience_policy": {...},
        "validation_details": {...}
    }
    """
    try:
        result = validate_content(
            topic=b.topic,
            audience=b.audience,
            content_type=b.content_type,
            flags=b.flags
        )
        return result
    except Exception as e:
        logger.error(f"quality endpoint error: {str(e)}", exc_info=True)
        return {
            'ok': False,
            'error': 'quality_check_error',
            'message': str(e)
        }


# OLD endpoint (remove):
@app.post('/api/metadata')
def metadata(b: MetadataIn):
    return build_metadata(b.topic, b.content_type, b.platform)


# NEW endpoint (add):
@app.post('/api/metadata')
def metadata(b: MetadataIn):
    """
    Build platform-specific metadata
    
    Request body:
    {
        "topic": "string (required, 2-500 chars)",
        "content_type": "video|photo|wallpaper|story",
        "platform": "youtube|facebook|instagram|tiktok|x (required)"
    }
    
    Response:
    {
        "ok": true/false,
        "platform": "platform name",
        "topic": "sanitized topic",
        "content_type": "type",
        "caption_style": "format to use",
        "hashtags": [...],
        "title": "platform-specific title",
        "error": "error message if any"
    }
    """
    try:
        result = build_metadata(
            topic=b.topic,
            content_type=b.content_type,
            platform=b.platform
        )
        return result
    except Exception as e:
        logger.error(f"metadata endpoint error: {str(e)}", exc_info=True)
        return {
            'ok': False,
            'error': 'metadata_error',
            'message': str(e),
            'platform': b.platform
        }
```

---

#### **STEP 6: Update Services audience.py**

Fix the `validate_mode()` function to handle None/empty:

```python
# In app/services/audience.py

def validate_mode(audience: str | None) -> str:
    """Safely validate and normalize audience mode"""
    if not audience:
        return 'GENERAL'  # Safe default
    
    audience_str = str(audience).strip().upper()
    
    if not audience_str:
        return 'GENERAL'
    
    VALID_MODES = {'GENERAL', 'KIDS', 'MATURE', 'ADULT', 'EDUCATIONAL'}
    
    if audience_str in VALID_MODES:
        return audience_str
    
    # Fallback mapping
    if audience_str.startswith('K'):
        return 'KIDS'
    elif audience_str.startswith('A'):
        return 'ADULT'
    elif audience_str.startswith('M'):
        return 'MATURE'
    else:
        return 'GENERAL'  # Ultimate fallback
```

---

### ✅ TESTING CHECKLIST

After integration, test each scenario:

#### Test 1: Valid Request
```bash
curl -X POST http://127.0.0.1:8000/api/quality/check \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Funny Punjabi Videos",
    "audience": "GENERAL",
    "content_type": "video"
  }'

Expected: HTTP 200 with validation result
```

#### Test 2: Invalid Topic
```bash
curl -X POST http://127.0.0.1:8000/api/quality/check \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "",
    "audience": "GENERAL",
    "content_type": "video"
  }'

Expected: HTTP 422 with validation error
```

#### Test 3: Invalid Platform
```bash
curl -X POST http://127.0.0.1:8000/api/metadata \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Cool Content",
    "content_type": "video",
    "platform": "reddit"
  }'

Expected: HTTP 422 - unsupported_platform error
```

#### Test 4: Malformed JSON
```bash
curl -X POST http://127.0.0.1:8000/api/quality/check \
  -H "Content-Type: application/json" \
  -d '{"topic": "test"'

Expected: HTTP 400 - json_decode_error
```

#### Test 5: Wrong Content-Type
```bash
curl -X POST http://127.0.0.1:8000/api/quality/check \
  -H "Content-Type: text/plain" \
  -d 'topic=test'

Expected: HTTP 400 - invalid_content_type
```

---

### 🔍 DEBUGGING

#### View Request Logs
```python
# Run with logging enabled:
import logging
logging.basicConfig(level=logging.DEBUG)

# In main.py, add logging setup:
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

#### Check What's Failing
```bash
# Run server with verbose output:
python -u run.py  # Or your startup command

# Watch logs while sending requests
# Errors will show in console
```

#### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Still getting 422 | Pydantic model validation | Check Pydantic validators are applied |
| Missing imports | New files not in path | Verify files are in `app/` directory |
| Middleware not working | Import order | Ensure middleware imports are before model usage |
| 500 errors | Catch blocks not catching | Check exception type matches |
| JSON errors | Content-Type header | Client must send `Content-Type: application/json` |

---

### 📦 FILE CHECKLIST

Before deployment, verify you have:

- [ ] `app/validators.py` - New validation layer
- [ ] `app/exceptions.py` - Custom exceptions
- [ ] `app/middleware.py` - Request middleware
- [ ] `app/services/quality.py` - Fixed quality service
- [ ] `app/services/metadata.py` - Fixed metadata service
- [ ] Updated `app/main.py` - With middleware & models
- [ ] Updated `app/services/audience.py` - Safe validate_mode
- [ ] Backup of original files (.backup)
- [ ] Requirements.txt updated if needed
- [ ] Tests passing

---

### 🚀 DEPLOYMENT

After local testing:

```bash
# 1. Backup everything
cp -r app app.backup

# 2. Copy new files
cp validators.py app/
cp exceptions.py app/
cp middleware.py app/

# 3. Replace services
cp quality_fixed.py app/services/quality.py
cp metadata_fixed.py app/services/metadata.py

# 4. Update main imports
# Edit app/main.py - add imports and middleware

# 5. Restart service
systemctl restart kilcritic  # or your service name

# 6. Verify health
curl http://127.0.0.1:8000/api/health

# 7. Run smoke tests
python test_endpoints.py
```

---

### 📞 SUPPORT

If issues arise:

1. Check logs: `tail -f app.log`
2. Verify file placement: `ls -la app/*.py`
3. Test basic endpoint: `curl http://127.0.0.1:8000/api/health`
4. Check imports: `python -c "from app import validators"`
5. Restore from backup if needed: `cp -r app.backup app`

---

**Status: READY FOR PRODUCTION**  
**Generated:** 2026-09-30  
**Version:** v6.1.1-POWER  
**Quality Level:** HIGH ✅
