import os
import mimetypes
import uuid
import hashlib
from typing import Tuple, Dict, List, Optional, BinaryIO
import io


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Original filename
        
    Returns:
        File extension without dot
    """
    return os.path.splitext(filename)[1][1:].lower()


def get_file_mimetype(filename: str) -> str:
    """
    Get file MIME type from filename
    
    Args:
        filename: Original filename
        
    Returns:
        MIME type
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename based on original filename
    
    Args:
        original_filename: Original filename
        
    Returns:
        Unique filename
    """
    ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{ext}" if ext else unique_id


def calculate_file_hash(file_data: BinaryIO, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of file data
    
    Args:
        file_data: File data
        algorithm: Hash algorithm
        
    Returns:
        File hash
    """
    hasher = hashlib.new(algorithm)

    # Save current position
    current_pos = file_data.tell()

    # Reset to beginning
    file_data.seek(0)

    # Read in chunks to handle large files
    chunk_size = 8192
    while True:
        data = file_data.read(chunk_size)
        if not data:
            break
        hasher.update(data)

    # Restore position
    file_data.seek(current_pos)

    return hasher.hexdigest()


def get_safe_filename(filename: str) -> str:
    """
    Make a filename safe for storage
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Remove potentially dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    safe_name = ''.join(c if c in safe_chars else '_' for c in filename)

    # Limit length
    if len(safe_name) > 100:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:95] + ext

    return safe_name


def is_pdf_file(file_data: BinaryIO) -> bool:
    """
    Check if file is a PDF by examining its header
    
    Args:
        file_data: File data
        
    Returns:
        True if file is a PDF, False otherwise
    """
    # Save current position
    current_pos = file_data.tell()

    # Reset to beginning
    file_data.seek(0)

    # Read header (first 4 bytes)
    header = file_data.read(4)

    # Restore position
    file_data.seek(current_pos)

    # Check if header matches PDF signature (%PDF)
    return header == b'%PDF'


def is_docx_file(file_data: BinaryIO) -> bool:
    """
    Check if file is a DOCX by examining its header
    
    Args:
        file_data: File data
        
    Returns:
        True if file is a DOCX, False otherwise
    """
    # Save current position
    current_pos = file_data.tell()

    # Reset to beginning
    file_data.seek(0)

    # Read header (first 4 bytes)
    header = file_data.read(4)

    # Restore position
    file_data.seek(current_pos)

    # Check if header matches DOCX/ZIP signature (PK\x03\x04)
    return header == b'PK\x03\x04'


def extract_text_from_pdf(file_data: BinaryIO) -> str:
    """
    Extract text content from a PDF file
    
    Args:
        file_data: PDF file data
        
    Returns:
        Extracted text
    """
    try:
        from PyPDF2 import PdfReader

        # Save current position
        current_pos = file_data.tell()

        # Reset to beginning
        file_data.seek(0)

        # Create PDF reader
        pdf = PdfReader(file_data)

        # Extract text from each page
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

        # Restore position
        file_data.seek(current_pos)

        return text
    except Exception as e:
        # Log error
        print(f"Error extracting text from PDF: {str(e)}")
        return ""


def create_thumbnail(file_data: BinaryIO, mimetype: str, max_size: Tuple[int, int] = (200, 200)) -> Optional[bytes]:
    """
    Create a thumbnail for an image file
    
    Args:
        file_data: Image file data
        mimetype: MIME type of the image
        max_size: Maximum thumbnail size (width, height)
        
    Returns:
        Thumbnail data or None if not an image
    """
    if not mimetype.startswith('image/'):
        return None

    try:
        from PIL import Image

        # Save current position
        current_pos = file_data.tell()

        # Reset to beginning
        file_data.seek(0)

        # Open image
        img = Image.open(file_data)

        # Resize image
        img.thumbnail(max_size)

        # Save thumbnail to memory
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)

        # Restore position
        file_data.seek(current_pos)

        return output.getvalue()
    except Exception as e:
        # Log error
        print(f"Error creating thumbnail: {str(e)}")
        return None
