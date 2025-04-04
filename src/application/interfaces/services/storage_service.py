from abc import ABC, abstractmethod
from typing import Dict, BinaryIO, Optional, Tuple
from uuid import UUID


class StorageService(ABC):
    """Interface for file storage service operations"""

    @abstractmethod
    def upload_file(self, file_data: BinaryIO, file_name: str,
                    user_id: UUID, thesis_id: UUID) -> Dict:
        """
        Upload a file to storage
        
        Returns:
            Dict containing file info like path, size, type, etc.
        """
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> Optional[BinaryIO]:
        """Get a file from storage"""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage"""
        pass

    @abstractmethod
    def generate_download_link(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate a temporary download link for a file"""
        pass

    @abstractmethod
    def validate_file(self, file_data: BinaryIO, file_name: str) -> Tuple[bool, str]:
        """
        Validate a file (type, size, content, etc.)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
