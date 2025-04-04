import os
import uuid
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Dict, BinaryIO, Optional, Tuple, List
from uuid import UUID
import io
import mimetypes

from src.application.interfaces.services.storage_service import StorageService
from src.domain.exceptions.domain_exceptions import FileStorageException


class CloudinaryStorageService(StorageService):
    """Cloudinary implementation of the storage service"""

    # Allowed file types and their MIME types
    ALLOWED_FILE_TYPES = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "txt": "text/plain"
    }

    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(self):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True
        )

    def upload_file(self, file_data: BinaryIO, file_name: str,
                    user_id: UUID, thesis_id: UUID) -> Dict:
        """
        Upload a file to Cloudinary
        
        Returns:
            Dict containing file info like path, size, type, etc.
        """
        # First validate the file
        is_valid, error_message = self.validate_file(file_data, file_name)
        if not is_valid:
            raise FileStorageException(error_message)

        # Get file size
        file_data.seek(0, 2)  # Go to end of file
        file_size = file_data.tell()  # Get position (size)
        file_data.seek(0)  # Go back to beginning

        # Get file extension and type
        file_ext = file_name.split(".")[-1].lower() if "." in file_name else ""
        file_type = self.ALLOWED_FILE_TYPES.get(
            file_ext, "application/octet-stream")

        # Generate unique folder path
        folder_path = f"theses/{user_id}/{thesis_id}"

        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_data,
                folder=folder_path,
                resource_type="raw",
                public_id=f"{uuid.uuid4()}_{file_name}",
                use_filename=True,
                unique_filename=True,
                overwrite=False
            )

            # Return file info
            return {
                "file_path": upload_result["secure_url"],
                "file_name": file_name,
                "file_size": file_size,
                "file_type": file_type,
                "public_id": upload_result["public_id"],
                "resource_type": upload_result["resource_type"]
            }
        except Exception as e:
            raise FileStorageException(
                f"Failed to upload file to Cloudinary: {str(e)}")

    def get_file(self, file_path: str) -> Optional[BinaryIO]:
        """Get a file from Cloudinary"""
        try:
            # Extract public_id from the URL
            if "cloudinary.com" not in file_path:
                return None

            # Get the last part of the URL
            parts = file_path.split("/")
            public_id = parts[-1]

            # Download the file
            response = cloudinary.api.resource(public_id, resource_type="raw")

            if response and "secure_url" in response:
                # Create a file-like object
                file_data = io.BytesIO()

                # Fetch the file content from secure_url
                import requests
                file_content = requests.get(response["secure_url"]).content
                file_data.write(file_content)
                file_data.seek(0)

                return file_data

            return None
        except Exception:
            return None

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from Cloudinary"""
        try:
            # Extract public_id from the URL
            if "cloudinary.com" not in file_path:
                return False

            # Get the public ID
            parts = file_path.split("/")
            resource_type = "raw"  # Default to raw for documents

            # Extract public_id without version number
            url_parts = file_path.split("/")
            if "upload" in url_parts:
                upload_index = url_parts.index("upload")
                public_id = "/".join(url_parts[upload_index + 2:])
            else:
                public_id = parts[-1]

            # Delete the file
            result = cloudinary.uploader.destroy(
                public_id, resource_type=resource_type)

            return result.get("result") == "ok"
        except Exception:
            return False

    def generate_download_link(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate a temporary download link for a file"""
        # For Cloudinary, we can just return the secure URL as it's already accessible
        # In a production environment, you might want to generate a signed URL with expiration
        return file_path

    def validate_file(self, file_data: BinaryIO, file_name: str) -> Tuple[bool, str]:
        """
        Validate a file (type, size, content, etc.)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        if "." not in file_name:
            return False, "File must have an extension"

        file_ext = file_name.split(".")[-1].lower()

        if file_ext not in self.ALLOWED_FILE_TYPES:
            allowed_exts = ", ".join(self.ALLOWED_FILE_TYPES.keys())
            return False, f"File type not allowed. Allowed types: {allowed_exts}"

        # Check file size
        file_data.seek(0, 2)  # Go to end of file
        file_size = file_data.tell()  # Get position (size)
        file_data.seek(0)  # Go back to beginning

        if file_size > self.MAX_FILE_SIZE:
            max_size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_size_mb}MB"

        # Additional security checks could be added here
        # For example, checking the actual content type using python-magic

        return True, ""
