# backend/app/models/company.py
"""
Minimal Company model for multi-tenancy.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

class Company(Base):
    """Company model for multi-tenant SaaS."""
    
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    leads = relationship("Lead", back_populates="company")
    campaigns = relationship("Campaign", back_populates="company")