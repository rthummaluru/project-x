# backend/app/models/campaign_email.py
"""
CampaignEmail model for tracking individual email executions within campaigns.

This model represents each specific email sent to a lead as part of a campaign sequence.
While Campaign stores the configuration, CampaignEmail tracks the actual execution.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.core.database import Base

# Enum Definitions
class CampaignEmailStatus(str, Enum):
    """
    Individual email status tracking through the sending pipeline.
    
    - PENDING: Email is queued for generation
    - GENERATED: AI has created the email content
    - SCHEDULED: Email is ready and scheduled for sending
    - SENT: Email has been successfully sent
    - FAILED: Email sending failed (see error_message)
    - BOUNCED: Email was sent but bounced back
    """
    PENDING = "pending"
    GENERATED = "generated"
    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"

class CampaignEmail(Base):
    """
    CampaignEmail tracks individual email executions within a campaign.
    
    Each row represents one email to one lead at a specific sequence position.
    This enables detailed tracking of the email sending pipeline and performance analytics.
    """
    
    __tablename__ = "campaign_emails"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys (Critical for performance - these will be queried frequently)
    campaign_id = Column(
        Integer, 
        ForeignKey("campaigns.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True  # Essential for "show all emails in campaign" queries
    )
    lead_id = Column(
        Integer, 
        ForeignKey("leads.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True  # Essential for "show all emails to this lead" queries
    )
    
    # Email Source Information  
    from_email = Column(
        String(255), 
        nullable=False,
        comment="Email address this email is sent from (user's sending address)"
    )
    provider = Column(
        String(50), 
        nullable=True,
        comment="Email provider auto-detected from from_email: gmail, outlook, etc."
    )
    
    # Sequence Information
    sequence_position = Column(
        Integer, 
        nullable=False,
        comment="Position in email sequence: 1, 2, 3, or 4 (max 4 per campaign)"
    )
    
    # Email Content
    subject_line = Column(String(255), nullable=False)
    email_content = Column(Text, nullable=False, comment="Full email body content")
    
    # Status Tracking
    status = Column(
        SQLEnum(CampaignEmailStatus), 
        nullable=False, 
        default=CampaignEmailStatus.PENDING,
        index=True  # Frequently filtered by status for pipeline views
    )
    
    # Timing Fields
    scheduled_send_at = Column(
        DateTime(timezone=True), 
        nullable=True,
        index=True,  # Useful for finding emails ready to send
        comment="When this email should be sent (calculated from campaign delays)"
    )
    sent_at = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="Actual timestamp when email was sent"
    )
    
    # Future Email Tracking (for analytics)
    opened_at = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="When recipient opened the email (requires email tracking pixels)"
    )
    replied_at = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="When recipient replied to the email"
    )
    
    # Error Handling
    error_message = Column(
        Text, 
        nullable=True,
        comment="Detailed error message if sending failed (for debugging)"
    )
    
    # Audit Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    campaign = relationship("Campaign", back_populates="emails")
    lead = relationship("Lead", back_populates="campaign_emails")
    
    def __repr__(self):
        return f"<CampaignEmail(id={self.id}, campaign_id={self.campaign_id}, lead_id={self.lead_id}, status='{self.status}')>"
    
    @property
    def is_sent(self) -> bool:
        """Helper property to check if email has been sent."""
        return self.status in [CampaignEmailStatus.SENT, CampaignEmailStatus.BOUNCED]
    
    @property  
    def is_ready_to_send(self) -> bool:
        """Helper property to check if email is ready for sending."""
        return (
            self.status == CampaignEmailStatus.SCHEDULED and 
            self.scheduled_send_at is not None and
            self.scheduled_send_at <= func.now()
        )