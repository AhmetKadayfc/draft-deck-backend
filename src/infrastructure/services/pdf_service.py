import io
import os
from typing import BinaryIO, List

import tempfile

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from src.domain.entities.feedback import Feedback, FeedbackComment
from src.domain.entities.thesis import Thesis
from src.domain.entities.user import User
from src.application.interfaces.services.storage_service import StorageService


class PdfService:
    """Service for PDF generation and manipulation"""

    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service

    def generate_feedback_report(
        self,
        feedback: Feedback,
        thesis: Thesis,
        student: User,
        advisor: User,
        include_inline_comments: bool = True,
        include_original_document: bool = False
    ) -> BinaryIO:
        """
        Generate a PDF report with feedback
        
        Args:
            feedback: Feedback entity
            thesis: Thesis entity
            student: Student entity
            advisor: Advisor entity
            include_inline_comments: Whether to include inline comments
            include_original_document: Whether to include the original document content
            
        Returns:
            File-like object containing the PDF
        """
        # Create a buffer for the PDF
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            title=f"Feedback Report - {thesis.title}",
            author=f"{advisor.first_name} {advisor.last_name}"
        )

        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading1"]
        normal_style = styles["Normal"]

        # Create custom styles
        info_style = ParagraphStyle(
            "InfoStyle",
            parent=styles["Normal"],
            fontSize=10,
            leading=12,
            leftIndent=20
        )

        comment_style = ParagraphStyle(
            "CommentStyle",
            parent=styles["Normal"],
            fontSize=10,
            leading=12,
            leftIndent=20,
            borderWidth=1,
            borderColor=colors.gray,
            borderPadding=5,
            backColor=colors.lightgrey
        )

        # List to hold flowable elements
        elements = []

        # Add title
        elements.append(
            Paragraph(f"Feedback Report: {thesis.title}", title_style))
        elements.append(Spacer(1, 12))

        # Add metadata table
        metadata = [
            ["Submission Date", thesis.submitted_at.strftime(
                "%Y-%m-%d %H:%M") if thesis.submitted_at else "N/A"],
            ["Feedback Date", feedback.created_at.strftime("%Y-%m-%d %H:%M")],
            ["Student",
                f"{student.first_name} {student.last_name} ({student.email})"],
            ["Advisor",
                f"{advisor.first_name} {advisor.last_name} ({advisor.email})"],
            ["Status", thesis.status.value.upper()],
            ["Version", str(thesis.version)]
        ]

        metadata_table = Table(metadata, colWidths=[120, 350])
        metadata_table.setStyle(TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))

        elements.append(metadata_table)
        elements.append(Spacer(1, 20))

        # Add overall assessment
        elements.append(Paragraph("Overall Assessment", heading_style))
        elements.append(Spacer(1, 6))

        if feedback.rating:
            rating_text = f"Rating: {feedback.rating}/5"
            elements.append(Paragraph(rating_text, normal_style))
            elements.append(Spacer(1, 6))

        elements.append(Paragraph("Comments:", normal_style))
        elements.append(Paragraph(feedback.overall_comments, info_style))
        elements.append(Spacer(1, 12))

        if feedback.recommendations:
            elements.append(Paragraph("Recommendations:", normal_style))
            elements.append(Paragraph(feedback.recommendations, info_style))
            elements.append(Spacer(1, 12))

        # Add inline comments if requested
        if include_inline_comments and feedback.comments:
            elements.append(Paragraph("Inline Comments", heading_style))
            elements.append(Spacer(1, 6))

            # Sort comments by page if available
            sorted_comments = sorted(
                feedback.comments,
                key=lambda c: (c.page or 0, c.position_y or 0)
            )

            for comment in sorted_comments:
                location = ""
                if comment.page:
                    location = f"Page {comment.page}"
                    if comment.position_x and comment.position_y:
                        location += f" (x:{comment.position_x:.2f}, y:{comment.position_y:.2f})"

                comment_header = f"Comment {location}"
                elements.append(Paragraph(comment_header, normal_style))
                elements.append(Paragraph(comment.content, comment_style))
                elements.append(Spacer(1, 10))

        # Build PDF
        doc.build(elements)

        # If including original document and it exists, merge with feedback report
        if include_original_document and thesis.file_path:
            # Get original document
            original_file = self.storage_service.get_file(thesis.file_path)

            if original_file and thesis.file_type == "application/pdf":
                # Create a new buffer for the merged PDF
                merged_buffer = io.BytesIO()

                # Reset the buffer position
                buffer.seek(0)

                # Merge PDFs
                merged_buffer = self._merge_pdfs(buffer, original_file)
                return merged_buffer

        # Reset buffer position to beginning
        buffer.seek(0)
        return buffer

    def _merge_pdfs(self, feedback_pdf: BinaryIO, original_pdf: BinaryIO) -> BinaryIO:
        """Merge feedback PDF with original PDF"""
        output_buffer = io.BytesIO()

        # Create PDF readers
        feedback_reader = PdfReader(feedback_pdf)
        original_reader = PdfReader(original_pdf)

        # Create PDF writer
        writer = PdfWriter()

        # Add feedback pages
        for page_num in range(len(feedback_reader.pages)):
            writer.add_page(feedback_reader.pages[page_num])

        # Add original document pages
        for page_num in range(len(original_reader.pages)):
            writer.add_page(original_reader.pages[page_num])

        # Write merged PDF to buffer
        writer.write(output_buffer)
        output_buffer.seek(0)

        return output_buffer

    def add_annotations_to_pdf(
        self,
        original_pdf: BinaryIO,
        comments: List[FeedbackComment]
    ) -> BinaryIO:
        """
        Add annotation highlights and comments to a PDF
        
        Args:
            original_pdf: Original PDF file
            comments: List of feedback comments to add as annotations
            
        Returns:
            File-like object containing the annotated PDF
        """
        # Create temporary files for the PDF operations
        with tempfile.NamedTemporaryFile(delete=False) as temp_original:
            temp_original.write(original_pdf.read())
            temp_original_path = temp_original.name

        try:
            # Create PDF reader for original file
            reader = PdfReader(temp_original_path)
            writer = PdfWriter()

            # Copy all pages from original to writer
            for page_num in range(len(reader.pages)):
                writer.add_page(reader.pages[page_num])

            # Sort comments by page
            page_comments = {}
            for comment in comments:
                if comment.page is not None:
                    page_idx = comment.page - 1  # Convert to 0-based index
                    if page_idx not in page_comments:
                        page_comments[page_idx] = []
                    page_comments[page_idx].append(comment)

            # Add annotations to each page
            for page_idx, page_comment_list in page_comments.items():
                if page_idx < len(reader.pages):
                    page = writer.pages[page_idx]

                    for comment in page_comment_list:
                        # Create annotation on this page
                        # Note: In a real implementation, this would use PyPDF2's annotation features
                        # The implementation depends on the PyPDF2 version and capabilities
                        # This is a simplified placeholder
                        pass

            # Write to output buffer
            output_buffer = io.BytesIO()
            writer.write(output_buffer)
            output_buffer.seek(0)

            return output_buffer

        finally:
            # Clean up temporary file
            if os.path.exists(temp_original_path):
                os.unlink(temp_original_path)
