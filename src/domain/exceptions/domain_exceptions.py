class DomainException(Exception):
    """Base exception for domain-related errors"""
    pass


class EntityNotFoundException(DomainException):
    """Exception raised when an entity is not found"""

    def __init__(self, entity_type, entity_id):
        self.message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(self.message)


class ValidationException(DomainException):
    """Exception raised when validation fails"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class AuthorizationException(DomainException):
    """Exception raised when a user is not authorized to perform an action"""

    def __init__(self, message="You are not authorized to perform this action"):
        self.message = message
        super().__init__(self.message)


class ThesisAlreadySubmittedException(DomainException):
    """Exception raised when a thesis has already been submitted"""

    def __init__(self, thesis_id):
        self.message = f"Thesis with ID {thesis_id} has already been submitted and cannot be modified"
        super().__init__(self.message)


class InvalidStatusTransitionException(DomainException):
    """Exception raised when an invalid status transition is attempted"""

    def __init__(self, current_status, new_status):
        self.message = f"Cannot transition from {current_status} to {new_status}"
        super().__init__(self.message)


class FileStorageException(DomainException):
    """Exception raised when there is an error storing a file"""

    def __init__(self, message="Error storing file"):
        self.message = message
        super().__init__(self.message)
