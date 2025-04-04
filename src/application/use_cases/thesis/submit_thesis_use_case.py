from typing import Optional, BinaryIO
from uuid import UUID

from src.application.dtos.thesis_dto import ThesisCreateDTO, ThesisResponseDTO
from src.application.interfaces.repositories.thesis_repository import ThesisRepository
from src.application.interfaces.repositories.user_repository import UserRepository
from src.application.interfaces.services.storage_service import StorageService
from src.application.interfaces.services.notification_service import NotificationService
from src.domain.entities.thesis import Thesis
from src.domain.exceptions.domain_exceptions import ValidationException, FileStorageException
from src.domain.value_objects.status import ThesisType, ThesisStatus, UserRole, NotificationType


class SubmitThesisUseCase:
    """Use case for submitting a thesis"""

    def __init__(
        self,
        thesis_repository: ThesisRepository,
        user_repository: UserRepository,
        storage_service: StorageService,
        notification_service: Optional[NotificationService] = None
    ):
        self.thesis_repository = thesis_repository
        self.user_repository = user_repository
        self.storage_service = storage_service
        self.notification_service = notification_service

    def execute(
        self,
        dto: ThesisCreateDTO,
        student_id: UUID,
        file_data: Optional[BinaryIO] = None,
        file_name: Optional[str] = None
    ) -> ThesisResponseDTO:
        """
        Submit a new thesis
        
        Args:
            dto: Thesis creation data
            student_id: ID of the student submitting the thesis
            file_data: Binary file data (optional)
            file_name: Original filename (optional)
            
        Returns:
            ThesisResponseDTO with created thesis data
            
        Raises:
            ValidationException: If validation fails
            FileStorageException: If file storage fails
        """
        # Validate student exists and has student role
        student = self.user_repository.get_by_id(student_id)
        if not student:
            raise ValidationException("Student not found")

        if student.role != UserRole.STUDENT:
            raise ValidationException("Only students can submit theses")

        # Parse thesis type
        try:
            thesis_type = ThesisType(dto.thesis_type.lower())
        except ValueError:
            raise ValidationException(
                f"Invalid thesis type. Must be one of: {', '.join(ThesisType.values())}")

        # Create thesis entity
        thesis = Thesis(
            title=dto.title,
            student_id=student_id,
            thesis_type=thesis_type,
            description=dto.description,
            metadata=dto.metadata,
            status=ThesisStatus.DRAFT
        )

        # Handle file upload if provided
        file_info = None
        if file_data and file_name:
            # Validate file
            is_valid, error_message = self.storage_service.validate_file(
                file_data, file_name)
            if not is_valid:
                raise ValidationException(f"Invalid file: {error_message}")

            # Upload file
            try:
                file_info = self.storage_service.upload_file(
                    file_data=file_data,
                    file_name=file_name,
                    user_id=student_id,
                    thesis_id=thesis.id
                )

                # Update thesis with file info
                thesis.update_file_info(
                    file_path=file_info.get('file_path'),
                    file_name=file_info.get('file_name'),
                    file_size=file_info.get('file_size'),
                    file_type=file_info.get('file_type')
                )
            except Exception as e:
                raise FileStorageException(f"Failed to upload file: {str(e)}")

        # Save thesis
        created_thesis = self.thesis_repository.create(thesis)

        # Send notification if notification service is available
        if self.notification_service and thesis_type == ThesisType.FINAL:
            # Notify advisors about the submission
            self.notification_service.notify_new_thesis_submission(
                created_thesis.id)

        # Get student name for response
        student_name = student.full_name()

        # Generate download URL if file was uploaded
        download_url = None
        if file_info and 'file_path' in file_info:
            download_url = self.storage_service.generate_download_link(
                file_info['file_path'])

        # Return response
        return ThesisResponseDTO.from_entity(
            created_thesis,
            student_name=student_name,
            download_url=download_url
        )
