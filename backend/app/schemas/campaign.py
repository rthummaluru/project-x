"""
Pydantic schemas for Campaign API endpoints.

"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class CampaignBase(BaseModel):
    """
    Base schema for campaign operations.
    """
    name: str = Field(..., min_length=3, max_length=255, description="Campaign name")
    description: Optional[str] = Field(None, max_length=500, description="Campaign description")
    status: str = Field(..., description="Campaign status")
    start_date: Optional[datetime] = Field(None, description="Campaign start date")
    end_date: Optional[datetime] = Field(None, description="Campaign end date")
    context_json: Optional[Dict[str, Any]] = Field(None, description="Campaign context")
    delays_json: Optional[Dict[str, Any]] = Field(None, description="Campaign scheduling")

class CampaignCreate(CampaignBase):
    """
    Schema for creating a new campaign.
    """
    

class CampaignUpdate(CampaignBase):
