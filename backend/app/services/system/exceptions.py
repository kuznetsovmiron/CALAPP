# Base service exception
class ServiceError(Exception):
    """Base class for all service-layer exceptions."""

# HTTP-like exceptions

class BadRequestError(ServiceError):
    """Bad request (maps to 400)."""

class UnauthorizedError(ServiceError):
    """Unauthorized (maps to 401)."""

class NotFoundError(ServiceError):
    """Resource not found (maps to 404)."""
    
class NotUpdatedError(ServiceError):
    """Resource is not updated (maps to 404)."""

class ForbiddenError(ServiceError):
    """Action forbidden (maps to 403)."""

class UnprocessableEntityError(ServiceError):
    """Unprocessable entity (maps to 422)."""

class InternalError(ServiceError):
    """Internal error (maps to 500).""" 

class ConflictError(ServiceError):
    """Conflict (maps to 409)."""

class ToolExecutionError(ServiceError):
    """Tool execution error (maps to 400)."""