# backend/app/schemas/lead.py
"""
Pydantic schemas for Lead API endpoints.

Key concept: Schemas vs Models
- Models (SQLAlchemy): Define database structure
- Schemas (Pydantic): Define API request/response structure

Why separate them?
- API can expose different fields than database stores
- Validation happens automatically with Pydantic
- API versioning without changing database
- Security (hide sensitive database fields)
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums for controlled values (prevents invalid data)
class LeadStatus(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CONVERTED = "converted"
    CLOSED = "closed"
    UNQUALIFIED = "unqualified"

class LeadSource(str, Enum):
    APOLLO = "apollo"
    LINKEDIN = "linkedin"
    WEBSITE = "website"
    REFERRAL = "referral"
    COLD_EMAIL = "cold_email"
    EVENT = "event"
    OTHER = "other"

# Base schema with common fields
class LeadBase(BaseModel):
    """Base schema with fields common to all lead operations."""
    
    email: EmailStr  # Pydantic automatically validates email format
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$')  # Basic phone validation
    
    source: Optional[LeadSource] = None
    source_url: Optional[str] = None
    
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)

# Schema for creating a new lead (POST request)
class LeadCreate(LeadBase):
    """
    Schema for creating a new lead.
    
    This defines what fields are required vs optional when creating a lead.
    Notice: company_id is not here - it comes from the authenticated user.
    """
    
    # Email is the only truly required field
    email: EmailStr
    
    # Optional initial scoring
    score: Optional[int] = Field(0, ge=0, le=100, description="Lead score 0-100")
    
    @validator('custom_fields')
    def validate_custom_fields(cls, v):
        """Ensure custom_fields doesn't contain sensitive keys."""
        if v is None:
            return {}
        
        # Prevent overriding system fields
        forbidden_keys = ['id', 'company_id', 'created_at', 'updated_at']
        for key in forbidden_keys:
            if key in v:
                raise ValueError(f"Cannot use '{key}' in custom_fields")
        
        return v

# Schema for updating an existing lead (PUT/PATCH request)
class LeadUpdate(BaseModel):
    """
    Schema for updating a lead.
    
    All fields are optional since you might only want to update specific fields.
    """
    
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$')
    
    status: Optional[LeadStatus] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    
    source: Optional[LeadSource] = None
    source_url: Optional[str] = None
    
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    
    next_follow_up_at: Optional[datetime] = None

# Schema for lead responses (what API returns)
class LeadResponse(LeadBase):
    """
    Schema for lead data returned by API.
    
    This includes all the data from LeadBase plus system-generated fields.
    """
    
    id: int
    company_id: int
    status: LeadStatus
    score: int
    
    # Computed properties
    full_name: str
    is_qualified: bool
    
    # Contact tracking
    last_contacted_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None
    contact_attempts: int = 0
    
    # Research data from AI agents
    research_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        # Enable ORM mode so Pydantic can work with SQLAlchemy models
        from_attributes = True

# Schema for lead lists (with pagination)
class LeadListResponse(BaseModel):
    """Response schema for paginated lead lists."""
    
    leads: list[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# Schema for lead search/filtering
class LeadFilter(BaseModel):
    """Schema for filtering leads in list endpoints."""
    
    status: Optional[LeadStatus] = None
    source: Optional[LeadSource] = None
    company_name: Optional[str] = None
    min_score: Optional[int] = Field(None, ge=0, le=100)
    max_score: Optional[int] = Field(None, ge=0, le=100)
    
    # Date filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    
    # Search term (searches across name, email, company)
    search: Optional[str] = Field(None, max_length=255)
    
    @validator('max_score')
    def validate_score_range(cls, v, values):
        """Ensure min_score <= max_score"""
        if v is not None and 'min_score' in values and values['min_score'] is not None:
            if v < values['min_score']:
                raise ValueError('max_score must be >= min_score')
        return v

# Bulk operations schema
class LeadBulkCreate(BaseModel):
    """Schema for creating multiple leads at once."""
    
    leads: list[LeadCreate] = Field(..., min_items=1, max_items=100)  # Limit bulk size
    
    @validator('leads')
    def validate_unique_emails(cls, v):
        """Ensure no duplicate emails in bulk create."""
        emails = [lead.email for lead in v]
        if len(emails) != len(set(emails)):
            raise ValueError('Duplicate emails found in lead list')
        return v

class LeadBulkResponse(BaseModel):
    """Response for bulk lead creation."""
    
    created: list[LeadResponse]
    errors: list[Dict[str, Any]] = Field(default_factory=list)
    
    @property
    def success_count(self) -> int:
        return len(self.created)
    
    @property 
    def error_count(self) -> int:
        return len(self.errors)