from enum import Enum

class UserRole(Enum):
    """User roles in the system"""
    STUDENT = "student"
    ADVISOR = "advisor"
    ADMIN = "admin"

    @classmethod
    def values(cls):
        return [role.value for role in cls]


class ThesisStatus(Enum):
    """Thesis submission status"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    NEEDS_REVISION = "needs_revision"
    APPROVED = "approved"
    REJECTED = "rejected"

    @classmethod
    def values(cls):
        return [status.value for status in cls]


class ThesisType(Enum):
    """Type of thesis submission"""
    DRAFT = "draft"
    FINAL = "final"

    @classmethod
    def values(cls):
        return [type.value for type in cls]


class NotificationType(Enum):
    """Types of notifications in the system"""
    NEW_SUBMISSION = "new_submission"
    REVIEW_COMPLETE = "review_complete"
    FEEDBACK_PROVIDED = "feedback_provided"
    REVISION_REQUESTED = "revision_requested"
    THESIS_APPROVED = "thesis_approved"
    THESIS_REJECTED = "thesis_rejected"

    @classmethod
    def values(cls):
        return [notification.value for notification in cls]


# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    ThesisStatus.DRAFT: [ThesisStatus.SUBMITTED],
    ThesisStatus.SUBMITTED: [ThesisStatus.UNDER_REVIEW],
    ThesisStatus.UNDER_REVIEW: [ThesisStatus.NEEDS_REVISION, ThesisStatus.APPROVED, ThesisStatus.REJECTED],
    ThesisStatus.NEEDS_REVISION: [ThesisStatus.SUBMITTED],
    ThesisStatus.APPROVED: [],  # Terminal state
    ThesisStatus.REJECTED: []   # Terminal state
}
