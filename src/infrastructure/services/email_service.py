import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

from src.application.interfaces.services.notification_service import NotificationService
from src.application.interfaces.repositories.user_repository import UserRepository
from src.application.interfaces.repositories.thesis_repository import ThesisRepository
from src.application.interfaces.repositories.feedback_repository import FeedbackRepository
from src.domain.value_objects.status import NotificationType, UserRole


class EmailNotificationService(NotificationService):
    """Email implementation of the notification service"""

    def __init__(
        self,
        user_repository: UserRepository,
        thesis_repository: ThesisRepository = None,
        feedback_repository: FeedbackRepository = None
    ):
        self.user_repository = user_repository
        self.thesis_repository = thesis_repository
        self.feedback_repository = feedback_repository

        # Email configuration
        self.smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("MAIL_PORT", 587))
        self.smtp_username = os.getenv("MAIL_USERNAME")
        self.smtp_password = os.getenv("MAIL_PASSWORD")
        self.default_sender = os.getenv(
            "MAIL_DEFAULT_SENDER", self.smtp_username)
        self.use_tls = os.getenv("MAIL_USE_TLS", "True").lower() in [
            "true", "1", "yes"]
        # In-memory notification storage (for demo)
        # In production, use a database table
        self.notifications = []

    def send_email(self, recipient_email: str, subject: str, body: str,
                   html_body: Optional[str] = None, attachments: Optional[List[Dict]] = None) -> bool:
        """Send an email notification"""
        if not self.smtp_username or not self.smtp_password:
            # Log that email sending is disabled
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.default_sender
        msg["To"] = recipient_email

        # Attach plain text body
        msg.attach(MIMEText(body, "plain"))

        # Attach HTML body if provided
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        # Attach files if provided
        if attachments:
            for attachment in attachments:
                file_data = attachment.get("data")
                file_name = attachment.get("filename", "attachment")

                if file_data:
                    part = MIMEApplication(file_data.read())
                    part.add_header("Content-Disposition",
                                    f"attachment; filename={file_name}")
                    msg.attach(part)

        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.ehlo()

            if self.use_tls:
                server.starttls()
                server.ehlo()

            # Login and send email
            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(self.default_sender,
                            recipient_email, msg.as_string())
            server.close()

            return True
        except Exception as e:
            # Log the error
            print(f"Failed to send email: {str(e)}")
            return False

    def send_notification(self, user_id: UUID, notification_type: NotificationType,
                          data: Dict[str, Any], send_email: bool = True) -> bool:
        """Send a system notification (and optionally email)"""
        user = self.user_repository.get_by_id(user_id)

        if not user:
            return False

        # Create notification record
        notification = {
            # Simple ID generation
            "id": UUID(int=len(self.notifications) + 1),
            "user_id": user_id,
            "type": notification_type.value,
            "data": data,
            "is_read": False,
            "created_at": datetime.utcnow()
        }

        # Store notification
        self.notifications.append(notification)

        # Send email if requested
        if send_email:
            subject, body = self._get_notification_email_content(
                notification_type, data)

            if subject and body:
                self.send_email(
                    recipient_email=user.email,
                    subject=subject,
                    body=body
                )

        return True

    def get_user_notifications(self, user_id: UUID, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Get notifications for a user"""
        user_notifications = [
            n for n in self.notifications
            if n["user_id"] == user_id
        ]

        # Sort by created_at (newest first)
        sorted_notifications = sorted(
            user_notifications,
            key=lambda n: n["created_at"],
            reverse=True
        )

        # Apply pagination
        return sorted_notifications[offset:offset + limit]

    def mark_notification_as_read(self, notification_id: UUID) -> bool:
        """Mark a notification as read"""
        for notification in self.notifications:
            if notification["id"] == notification_id:
                notification["is_read"] = True
                return True

        return False

    def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user, returns count"""
        count = 0

        for notification in self.notifications:
            if notification["user_id"] == user_id and not notification["is_read"]:
                notification["is_read"] = True
                count += 1

        return count

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user"""
        return len([
            n for n in self.notifications
            if n["user_id"] == user_id and not n["is_read"]
        ])

    def notify_new_thesis_submission(self, thesis_id: UUID) -> bool:
        """Notify advisors about a new thesis submission"""
        if not self.thesis_repository:
            return False

        thesis = self.thesis_repository.get_by_id(thesis_id)

        if not thesis:
            return False

        # Get student
        student = self.user_repository.get_by_id(thesis.student_id)

        if not student:
            return False

        # If thesis already has an assigned advisor, notify only them
        if thesis.advisor_id:
            advisor = self.user_repository.get_by_id(thesis.advisor_id)

            if advisor:
                return self.send_notification(
                    user_id=advisor.id,
                    notification_type=NotificationType.NEW_SUBMISSION,
                    data={
                        "thesis_id": str(thesis.id),
                        "thesis_title": thesis.title,
                        "student_name": f"{student.first_name} {student.last_name}",
                        "student_id": str(student.id),
                        "submitted_at": thesis.submitted_at.isoformat() if thesis.submitted_at else None
                    }
                )
        else:
            # Notify all advisors (in a real app, only notify advisors in the same department)
            advisors = self.user_repository.get_by_role(UserRole.ADVISOR)

            success = True
            for advisor in advisors:
                result = self.send_notification(
                    user_id=advisor.id,
                    notification_type=NotificationType.NEW_SUBMISSION,
                    data={
                        "thesis_id": str(thesis.id),
                        "thesis_title": thesis.title,
                        "student_name": f"{student.first_name} {student.last_name}",
                        "student_id": str(student.id),
                        "submitted_at": thesis.submitted_at.isoformat() if thesis.submitted_at else None
                    }
                )
                success = success and result

            return success

        return False

    def notify_feedback_provided(self, thesis_id: UUID, feedback_id: UUID) -> bool:
        """Notify student about new feedback"""
        if not self.thesis_repository or not self.feedback_repository:
            return False

        thesis = self.thesis_repository.get_by_id(thesis_id)
        feedback = self.feedback_repository.get_by_id(feedback_id)

        if not thesis or not feedback:
            return False

        # Get advisor
        advisor = self.user_repository.get_by_id(feedback.advisor_id)

        if not advisor:
            return False

        # Notify student
        return self.send_notification(
            user_id=thesis.student_id,
            notification_type=NotificationType.FEEDBACK_PROVIDED,
            data={
                "thesis_id": str(thesis.id),
                "thesis_title": thesis.title,
                "feedback_id": str(feedback.id),
                "advisor_name": f"{advisor.first_name} {advisor.last_name}",
                "advisor_id": str(advisor.id),
                "feedback_date": feedback.created_at.isoformat()
            }
        )

    def notify_status_change(self, thesis_id: UUID, old_status: str, new_status: str) -> bool:
        """Notify relevant users about thesis status change"""
        if not self.thesis_repository:
            return False

        thesis = self.thesis_repository.get_by_id(thesis_id)

        if not thesis:
            return False

        # Get student
        student = self.user_repository.get_by_id(thesis.student_id)

        if not student:
            return False

        # Determine notification type based on status change
        notification_type = None
        if new_status == "needs_revision":
            notification_type = NotificationType.REVISION_REQUESTED
        elif new_status == "approved":
            notification_type = NotificationType.THESIS_APPROVED
        elif new_status == "rejected":
            notification_type = NotificationType.THESIS_REJECTED
        else:
            notification_type = NotificationType.REVIEW_COMPLETE

        # Notify student about status change
        student_notification = self.send_notification(
            user_id=thesis.student_id,
            notification_type=notification_type,
            data={
                "thesis_id": str(thesis.id),
                "thesis_title": thesis.title,
                "old_status": old_status,
                "new_status": new_status,
                "updated_at": thesis.updated_at.isoformat() if thesis.updated_at else None
            }
        )

        # If thesis has an advisor, notify them too
        advisor_notification = True
        if thesis.advisor_id:
            advisor_notification = self.send_notification(
                user_id=thesis.advisor_id,
                notification_type=notification_type,
                data={
                    "thesis_id": str(thesis.id),
                    "thesis_title": thesis.title,
                    "student_name": f"{student.first_name} {student.last_name}",
                    "student_id": str(student.id),
                    "old_status": old_status,
                    "new_status": new_status,
                    "updated_at": thesis.updated_at.isoformat() if thesis.updated_at else None
                }
            )

        return student_notification and advisor_notification

    def _get_notification_email_content(self, notification_type: NotificationType, data: Dict) -> tuple[str, str]:
        """Generate subject and body for notification emails"""
        if notification_type == NotificationType.NEW_SUBMISSION:
            subject = f"New Thesis Submission: {data.get('thesis_title', 'Untitled')}"
            body = f"A new thesis has been submitted by {data.get('student_name', 'a student')}.\n\n"
            body += f"Thesis: {data.get('thesis_title', 'Untitled')}\n"
            body += f"Submitted: {data.get('submitted_at', 'recently')}\n\n"
            body += "Please login to the Thesis Management System to review this submission."

            return subject, body

        elif notification_type == NotificationType.FEEDBACK_PROVIDED:
            subject = f"Feedback Provided on Thesis: {data.get('thesis_title', 'Untitled')}"
            body = f"Feedback has been provided by {data.get('advisor_name', 'your advisor')}.\n\n"
            body += f"Thesis: {data.get('thesis_title', 'Untitled')}\n"
            body += f"Feedback Date: {data.get('feedback_date', 'recently')}\n\n"
            body += "Please login to the Thesis Management System to view the feedback."

            return subject, body

        elif notification_type == NotificationType.REVISION_REQUESTED:
            subject = f"Revision Requested for Thesis: {data.get('thesis_title', 'Untitled')}"
            body = f"Your thesis status has been updated from {data.get('old_status', 'previous status')} "
            body += f"to {data.get('new_status', 'Needs Revision')}.\n\n"
            body += f"Thesis: {data.get('thesis_title', 'Untitled')}\n"
            body += f"Updated: {data.get('updated_at', 'recently')}\n\n"
            body += "Please login to the Thesis Management System to view feedback and make necessary revisions."

            return subject, body

        elif notification_type == NotificationType.THESIS_APPROVED:
            subject = f"Thesis Approved: {data.get('thesis_title', 'Untitled')}"
            body = "Congratulations! Your thesis has been approved.\n\n"
            body += f"Thesis: {data.get('thesis_title', 'Untitled')}\n"
            body += f"Updated: {data.get('updated_at', 'recently')}\n\n"
            body += "Please login to the Thesis Management System for more details."

            return subject, body

        elif notification_type == NotificationType.THESIS_REJECTED:
            subject = f"Thesis Status Update: {data.get('thesis_title', 'Untitled')}"
            body = f"Your thesis status has been updated from {data.get('old_status', 'previous status')} "
            body += f"to {data.get('new_status', 'Rejected')}.\n\n"
            body += f"Thesis: {data.get('thesis_title', 'Untitled')}\n"
            body += f"Updated: {data.get('updated_at', 'recently')}\n\n"
            body += "Please login to the Thesis Management System to view feedback and learn about next steps."

            return subject, body

        elif notification_type == NotificationType.REVIEW_COMPLETE:
            subject = f"Thesis Review Complete: {data.get('thesis_title', 'Untitled')}"
            body = f"Your thesis review has been completed and the status has been updated to {data.get('new_status', 'updated status')}.\n\n"
            body += f"Thesis: {data.get('thesis_title', 'Untitled')}\n"
            body += f"Updated: {data.get('updated_at', 'recently')}\n\n"
            body += "Please login to the Thesis Management System for more details."

            return subject, body

        # Default/unknown notification type
        return ("Thesis Management System Notification", "You have a new notification in the Thesis Management System. Please login to view it.")
