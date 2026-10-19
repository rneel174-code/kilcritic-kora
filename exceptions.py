# app/exceptions.py
# CUSTOM EXCEPTION CLASSES FOR KILCRITIC v6.1.1-POWER

class KilcriticException(Exception):
    """Base exception for all KILCRITIC errors"""
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self):
        return {
            'ok': False,
            'error': self.code,
            'message': self.message,
            'details': self.details
        }


class ValidationError(KilcriticException):
    """400/422 - Input validation failed"""
    def __init__(self, message: str, field: str = None, details: dict = None):
        d = details or {}
        if field:
            d['field'] = field
        super().__init__('validation_error', message, d)


class ProcessingError(KilcriticException):
    """500 - Internal processing error"""
    def __init__(self, message: str, service: str = None, details: dict = None):
        d = details or {}
        if service:
            d['service'] = service
        super().__init__('processing_error', message, d)


class NotFoundError(KilcriticException):
    """404 - Resource not found"""
    def __init__(self, resource: str, identifier: str = None):
        d = {'resource': resource}
        if identifier:
            d['id'] = identifier
        msg = f"{resource} not found"
        if identifier:
            msg += f": {identifier}"
        super().__init__('not_found', msg, d)


class ContentPolicyError(KilcriticException):
    """400 - Content violates policy"""
    def __init__(self, reason: str, policy_type: str = None, details: dict = None):
        d = details or {}
        if policy_type:
            d['policy_type'] = policy_type
        super().__init__('content_policy_violation', reason, d)


class PlatformError(KilcriticException):
    """500 - Platform integration error"""
    def __init__(self, platform: str, message: str, details: dict = None):
        d = details or {}
        d['platform'] = platform
        super().__init__('platform_error', message, d)


class AudioError(KilcriticException):
    """500 - AI/LLM service error"""
    def __init__(self, message: str, details: dict = None):
        super().__init__('ai_service_error', message, details or {})


class DatabaseError(KilcriticException):
    """500 - Database error"""
    def __init__(self, operation: str, details: dict = None):
        d = details or {}
        d['operation'] = operation
        super().__init__('database_error', f"Database {operation} failed", d)


class WorkerError(KilcriticException):
    """500 - Background worker error"""
    def __init__(self, message: str, job_id: str = None, details: dict = None):
        d = details or {}
        if job_id:
            d['job_id'] = job_id
        super().__init__('worker_error', message, d)
