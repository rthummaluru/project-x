# backend/app/schemas/campaign.py
"""
Pydantic schemas for Campaign API endpoints.

These schemas define the API contracts - what data flows in and out of your endpoints.
They provide validation, documentation, and type safety for your campaign features.
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.campaign import CampaignStatus
from app.schemas.lead import LeadFilter

# Nested Models for JSON Field Validation
class CampaignContext(BaseModel):
    """
    Structured validation for campaign context.
    
    These are the 4 key inputs users provide in the campaign wizard
    to customize how AI generates emails for their campaign.
    """
    company_name: str = Field(..., min_length=1, max_length=200, description="User's company name")
    product_description: str = Field(..., min_length=10, max_length=500, description="What the company sells")
    problem_solved: str = Field(..., min_length=10, max_length=500, description="Main customer problem being solved")
    call_to_action: str = Field(..., min_length=5, max_length=100, description="What action you want leads to take")
    tone: str = Field(default="Professional", description="Email tone: Professional, Casual, Direct")
    
    @validator('tone')
    def validate_tone(cls, v):
        """Ensure tone is one of the allowed values."""
        allowed_tones = ["Professional", "Casual", "Direct"]
        if v not in allowed_tones:
            raise ValueError(f"Tone must be one of: {', '.join(allowed_tones)}")
        return v

class CampaignDelays(BaseModel):
    """
    Structured validation for email sequence timing.
    
    Users configure when each email in the sequence should be sent.
    Keys are sequence positions (1-4), values are delay in days.
    """
    # Direct dict mapping - cleaner than nested structure
    delays: Dict[str, int] = Field(
        default={"1": 0},  # Default: single email, send immediately
        description="Sequence delays: {'1': 0, '2': 3, '3': 7, '4': 14} (position: days)"
    )
    
    @validator('delays')
    def validate_delays(cls, v):
        """Validate delay structure and values."""
        # Ensure keys are valid sequence positions (1-4)
        valid_positions = {'1', '2', '3', '4'}
        invalid_keys = set(v.keys()) - valid_positions
        if invalid_keys:
            raise ValueError(f"Invalid sequence positions: {invalid_keys}. Use '1', '2', '3', or '4'")
        
        # Ensure delay values are non-negative integers
        for position, days in v.items():
            if not isinstance(days, int) or days < 0:
                raise ValueError(f"Delay for position {position} must be a non-negative integer, got: {days}")
        
        # Ensure sequence positions are in ascending order by delay
        positions = sorted(v.items(), key=lambda x: int(x[0]))
        prev_delay = -1
        for position, delay in positions:
            if delay < prev_delay:
                raise ValueError("Email delays must be in ascending order (later emails can't be sent before earlier ones)")
            prev_delay = delay
            
        return v

# Base Schema (Common Fields)
class CampaignBase(BaseModel):
    """Base schema with fields common to multiple campaign operations."""
    name: str = Field(..., min_length=1, max_length=200, description="Campaign name")

# Create Schema (POST /campaigns)
class CampaignCreate(CampaignBase):
    """
    Schema for creating a new campaign.
    
    Users provide the campaign name, context for AI email generation,
    and optionally configure sequence timing and start date.
    """
    context: CampaignContext = Field(..., description="Campaign context for AI email generation")
    delays: Optional[CampaignDelays] = Field(
        default_factory=lambda: CampaignDelays(delays={"1": 0}),
        description="Email sequence timing configuration"
    )
    scheduled_start: Optional[datetime] = Field(None, description="When campaign should begin (defaults to now)")
    max_sequence_length: Optional[int] = Field(4, ge=1, le=4, description="Maximum emails in sequence (1-4)")
    lead_filter: Optional[LeadFilter] = Field(None, description="Lead targeting criteria")

# Update Schema (PATCH /campaigns/{id})
class CampaignUpdate(BaseModel):
    """
    Schema for updating an existing campaign.
    
    All fields are optional since users might only want to update specific aspects.
    Only draft campaigns can be updated.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    context: Optional[CampaignContext] = None
    delays: Optional[CampaignDelays] = None
    scheduled_start: Optional[datetime] = None
    status: Optional[CampaignStatus] = None
    is_active: Optional[bool] = None

# Response Schema (What API returns)
class CampaignResponse(CampaignBase):
    """
    Schema for campaign data returned by API.
    
    Includes all campaign data plus system-generated fields like ID,
    status, and timestamps. This is what users see when they fetch campaigns.
    """
    id: int
    context: CampaignContext
    delays: CampaignDelays
    status: CampaignStatus
    max_sequence_length: int
    is_active: bool
    
    # Timing fields
    scheduled_start: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Computed properties (calculated in service layer)
    email_count: Optional[int] = Field(None, description="Number of emails generated for this campaign")
    sent_count: Optional[int] = Field(None, description="Number of emails sent")
    failed_count: Optional[int] = Field(None, description="Number of emails that failed to send")
    
    class Config:
        
        from_attributes = True
        populate_by_name = True

# List Response Schema (GET /campaigns)
class CampaignListResponse(BaseModel):
    """Response schema for paginated campaign lists."""
    campaigns: List[CampaignResponse]
    total: int = Field(..., description="Total number of campaigns")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of campaigns per page")
    total_pages: int = Field(..., description="Total number of pages")

# Filter Schema (for list queries)
class CampaignFilter(BaseModel):
    """Schema for filtering campaigns in list endpoints."""
    status: Optional[CampaignStatus] = None
    is_active: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search: Optional[str] = Field(None, max_length=255, description="Search in campaign names")

# Campaign Stats Schema (for analytics)
class CampaignStats(BaseModel):
    """Campaign performance statistics."""
    campaign_id: int
    total_emails: int = 0
    emails_sent: int = 0
    emails_failed: int = 0
    emails_pending: int = 0
    emails_bounced: int = 0
    
    # Calculated metrics
    success_rate: float = Field(0.0, ge=0.0, le=1.0, description="Percentage of emails successfully sent")
    open_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Email open rate (if tracking enabled)")
    reply_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Email reply rate")
    
    class Config:
        from_attributes = True