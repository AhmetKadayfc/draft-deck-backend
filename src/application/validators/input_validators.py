import re
from typing import Tuple, Optional, Dict, Any, List
import uuid
from datetime import datetime

from domain.exceptions.domain_exceptions import ValidationException


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format

    Args:
        email: Email to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"

    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, None


def validate_uuid(uuid_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate UUID format
    
    Args:
        uuid_str: UUID string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not uuid_str:
        return False, "UUID is required"
    
    try:
        uuid.UUID(uuid_str)
        return True, None
    except ValueError:
        return False, "Invalid UUID format"


def validate_date_format(date_str: str, format_str: str = '%Y-%m-%d') -> Tuple[bool, Optional[str]]:
    """
    Validate date format
    
    Args:
        date_str: Date string to validate
        format_str: Expected date format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_str:
        return False, "Date is required"
    
    try:
        datetime.strptime(date_str, format_str)
        return True, None
    except ValueError:
        return False, f"Invalid date format, expected {format_str}"


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate required fields in a dictionary
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            return False, f"Field '{field}' is required"
    
    return True, None


def validate_string_length(value: str, field_name: str, min_length: int = 1, max_length: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate string length
    
    Args:
        value: String to validate
        field_name: Name of the field (for error message)
        min_length: Minimum length
        max_length: Maximum length (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value:
        return False, f"{field_name} is required"
    
    if len(value) < min_length:
        return False, f"{field_name} must be at least {min_length} characters"
    
    if max_length and len(value) > max_length:
        return False, f"{field_name} must not exceed {max_length} characters"
    
    return True, None


def validate_numeric_range(value: int, field_name: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate numeric range
    
    Args:
        value: Number to validate
        field_name: Name of the field (for error message)
        min_value: Minimum value (optional)
        max_value: Maximum value (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if min_value is not None and value < min_value:
        return False, f"{field_name} must be at least {min_value}"
    
    if max_value is not None and value > max_value:
        return False, f"{field_name} must not exceed {max_value}"
    
    return True, None


def validate_thesis_input(title: str, thesis_type: str) -> None:
    """
    Validate thesis input fields
    
    Args:
        title: Thesis title
        thesis_type: Thesis type
        
    Raises:
        ValidationException: If validation fails
    """
    if not title:
        raise ValidationException("Thesis title is required")
    
    if len(title) < 3:
        raise ValidationException("Thesis title must be at least 3 characters")
    
    if len(title) > 255:
        raise ValidationException("Thesis title must not exceed 255 characters")
    
    from domain.value_objects.status import ThesisType
    valid_types = ThesisType.values()
    
    if thesis_type not in valid_types:
        raise ValidationException(f"Invalid thesis type. Must be one of: {', '.join(valid_types)}")


def validate_feedback_input(thesis_id: str, overall_comments: str, rating: Optional[int] = None) -> None:
    """
    Validate feedback input fields
    
    Args:
        thesis_id: Thesis ID
        overall_comments: Overall comments
        rating: Rating (1-5)
        
    Raises:
        ValidationException: If validation fails
    """
    # Validate thesis ID
    is_valid, error = validate_uuid(thesis_id)
    if not is_valid:
        raise ValidationException(error)
    
    # Validate overall comments
    if not overall_comments:
        raise ValidationException("Overall comments are required")
    
    # Validate rating
    if rating is not None:
        if not isinstance(rating, int):
            raise ValidationException("Rating must be an integer")
        
        if rating < 1 or rating > 5:
            raise ValidationException("Rating must be between 1 and 5")


def validate_status_transition(current_status: str, new_status: str) -> None:
    """
    Validate thesis status transition
    
    Args:
        current_status: Current thesis status
        new_status: New thesis status
        
    Raises:
        ValidationException: If transition is invalid
    """
    from domain.value_objects.status import ThesisStatus, VALID_STATUS_TRANSITIONS
    
    try:
        current = ThesisStatus(current_status)
        new = ThesisStatus(new_status)
    except ValueError:
        raise ValidationException(f"Invalid status value")
    
    valid_transitions = VALID_STATUS_TRANSITIONS.get(current, [])
    
    if new not in valid_transitions:
        valid_values = [status.value for status in valid_transitions]
        raise ValidationException(
            f"Cannot transition from '{current.value}' to '{new.value}'. "
            f"Valid transitions: {', '.join(valid_values) if valid_values else 'None'}"
        )