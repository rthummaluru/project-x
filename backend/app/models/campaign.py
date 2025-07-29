# backend/app/models/campaign.py
"""
Campaign model for storing email campaign information.

This model represents the configuration and metadata for email campaigns.
Individual emails are stored in the CampaignEmail model.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.core.database import Base

# Enum Definitions
class CampaignStatus(str, Enum):
    """
    Campaign status enum.
    
    - DRAFT: Campaign is being configured, not yet active
    - ACTIVE: Campaign is running and sending emails
    - INACTIVE: Campaign has been paused or stopped
    """
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"

class Campaign(Base):
    """
    Campaign model stores email campaign configuration and metadata.
    
    Multi-tenant design: Each campaign belongs to a company and is created by a user.
    This stores the campaign template - individual email executions are in CampaignEmail.
    """
    
    __tablename__ = "campaigns"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenant Foreign Keys (CRITICAL: These need indexes for performance!)
    company_id = Column(
        Integer, 
        ForeignKey("companies.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True  # Essential for multi-tenant queries
    )
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True  # Essential for "show my campaigns" queries
    )
    
    # Campaign Basic Info
    name = Column(String(200), nullable=False)
    
    # Campaign Configuration (JSON Fields)
    context_json = Column(
        JSON, 
        nullable=False,
        default=dict,
        comment="User-provided context: company_name, product_description, problem_solved, call_to_action, tone"
    )
    delays_json = Column(
        JSON,
        nullable=False, 
        default=dict,
        comment="Sequence delays: {'1': 0, '2': 3, '3': 7, '4': 14} (days)"
    )
    
    # Campaign Settings
    max_sequence_length = Column(
        Integer, 
        nullable=False, 
        default=4,
        comment="Maximum number of emails in sequence (1-4)"
    )
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Campaign Status & Timing
    status = Column(
        SQLEnum(CampaignStatus), 
        default=CampaignStatus.DRAFT, 
        nullable=False, 
        index=True  # Frequently filtered by status
    )
    scheduled_start = Column(
        DateTime(timezone=True), 
        nullable=True,
        index=True  # Useful for finding campaigns starting soon
    )
    
    # Audit Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        index=True  # Useful for "recent campaigns" queries
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    # Note: These assume Company and User models exist with back_populates
    company = relationship("Company", back_populates="campaigns")
    user = relationship("User", back_populates="campaigns")
    emails = relationship("CampaignEmail", back_populates="campaign", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"