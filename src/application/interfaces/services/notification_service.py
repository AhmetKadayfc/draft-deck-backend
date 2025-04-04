from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from uuid import UUID

from src.domain.value_objects.status import NotificationType


class NotificationService(ABC):
    """Interface for notification service operations"""

    @abstractmethod
    def send_email(self, recipient_email: str, subject: str, body: str,
                   html_body: Optional[str] = None, attachments: Optional[List[Dict]] = None) -> bool:
        """Send an email notification"""
        pass

    @abstractmethod
    def send_notification(self, user_id: UUID, notification_type: NotificationType,
                          data: Dict[str, Any], send_email: bool = True) -> bool:
        """Send a system notification (and optionally email)"""
        pass

    @abstractmethod
    def get_user_notifications(self, user_id: UUID, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Get notifications for a user"""
        pass

    @abstractmethod
    def mark_notification_as_read(self, notification_id: UUID) -> bool:
        """Mark a notification as read"""
        pass

    @abstractmethod
    def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user, returns count"""
        pass

    @abstractmethod
    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user"""
        pass

    @abstractmethod
    def notify_new_thesis_submission(self, thesis_id: UUID) -> bool:
        """Notify advisors about a new thesis submission"""
        pass

    @abstractmethod
    def notify_feedback_provided(self, thesis_id: UUID, feedback_id: UUID) -> bool:
        """Notify student about new feedback"""
        pass

    @abstractmethod
    def notify_status_change(self, thesis_id: UUID, old_status: str, new_status: str) -> bool:
        """Notify relevant users about thesis status change"""
        pass
