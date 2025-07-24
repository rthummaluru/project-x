# backend/app/models/lead.py
"""
Lead database model for storing prospect information.

This model demonstrates:
- Multi-tenant design (each lead belongs to a company)
- Proper indexing for performance
- JSON fields for flexible data storage
- Audit fields (created_at, updated_at)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Index
import uuid
from datetime import datetime

from app.core.database import Base

class Lead(Base):
    """
    Lead model stores information about potential customers.
    
    Multi-tenant design: Each lead belongs to a company_id, ensuring
    data isolation between different SaaS customers.
    """
    
    __tablename__ = "leads"
    
    # Primary key - using auto-incrementing integer for performance
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenancy: Every lead belongs to a company
    # This ensures data isolation between your SaaS customers
    company_id = Column(
        Integer, 
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # Index for fast company-based queries
    )
    
    # Core lead information
    email = Column(String(255), nullable=False, index=True)  # Primary contact method
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    company_name = Column(String(200), nullable=True, index=True)  # Indexed for searching
    job_title = Column(String(150), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Lead source tracking (important for ROI analysis)
    source = Column(String(100), nullable=True)  # "apollo", "linkedin", "website", etc.
    source_url = Column(Text, nullable=True)     # Original URL/reference
    
    # Lead qualification and status
    status = Column(
        String(50), 
        default="new",  # new -> qualified -> contacted -> converted -> closed
        nullable=False,
        index=True  # Index for status-based filtering
    )
    
    # Lead scoring (0-100, helps prioritize outreach)
    score = Column(Integer, default=0, nullable=True)
    
    # Flexible data storage for custom fields
    # JSON field allows each company to store custom lead data
    custom_fields = Column(
        JSON, 
        default={}, 
        nullable=True,
        comment="Flexible storage for company-specific lead data"
    )
    
    # Communication tracking
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)
    next_follow_up_at = Column(DateTime(timezone=True), nullable=True)
    contact_attempts = Column(Integer, default=0, nullable=False)
    
    # Notes and context (for AI agent personalization)
    notes = Column(Text, nullable=True)
    research_data = Column(
        JSON, 
        default={}, 
        nullable=True,
        comment="AI-gathered research about this lead/company"
    )
    
    # Audit fields - crucial for debugging and compliance
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
    created_by = Column(
        Integer, 
        ForeignKey("users.id"),
        nullable=True  # Can be null for system-created leads
    )
    
    # Soft delete flag (never actually delete leads for compliance)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    
    # Relationships
    company = relationship("Company", back_populates="leads")
    creator = relationship("User", back_populates="created_leads")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        # Fast lookups for company's active leads
        Index("ix_leads_company_status", "company_id", "status", "is_deleted"),
        
        # Email uniqueness per company (prevent duplicate leads)
        Index("ix_leads_company_email", "company_id", "email", unique=True),
        
        # Follow-up scheduling queries
        Index("ix_leads_follow_up", "company_id", "next_follow_up_at", "is_deleted"),
        
        # Lead scoring and prioritization
        Index("ix_leads_score", "company_id", "score", "status"),
    )
    
    def __repr__(self):
        return f"<Lead(id={self.id}, email={self.email}, company={self.company_name})>"
    
    @property
    def full_name(self) -> str:
        """Convenience property to get full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return ""
    
    @property
    def is_qualified(self) -> bool:
        """Check if lead meets qualification criteria."""
        return (
            self.email is not None and
            self.score >= 50 and  # Configurable threshold
            self.status != "closed"
        )
    
    def update_last_contact(self):
        """Update contact tracking when lead is contacted."""
        self.last_contacted_at = datetime.utcnow()
        self.contact_attempts += 1