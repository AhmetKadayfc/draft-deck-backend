import re
import secrets
import string
from typing import Tuple, Optional


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    # Check for lowercase
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    # Check for uppercase
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    # Check for digit
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    # Check for special character
    special_chars = r'[!@#$%^&*(),.?":{}|<>]'
    if not re.search(special_chars, password):
        return False, "Password must contain at least one special character"

    return True, None


def generate_random_password(length: int = 12) -> str:
    """
    Generate a random secure password
    
    Args:
        length: Length of the password
        
    Returns:
        Randomly generated password
    """
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = '!@#$%^&*(),.?":{}|<>'

    # Ensure at least one of each type
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]

    # Fill the rest with random characters
    remaining = length - 4
    all_chars = lowercase + uppercase + digits + special

    password.extend(secrets.choice(all_chars) for _ in range(remaining))

    # Shuffle the password
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def mask_email(email: str) -> str:
    """
    Mask an email address for privacy
    
    Args:
        email: Email address to mask
        
    Returns:
        Masked email
    """
    if not email or '@' not in email:
        return email

    username, domain = email.split('@')

    # Show only first and last character of username
    if len(username) <= 2:
        masked_username = username
    else:
        masked_username = username[0] + '*' * \
            (len(username) - 2) + username[-1]

    return f"{masked_username}@{domain}"
