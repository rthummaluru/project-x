# backend/app/api/v1/campaigns.py
"""
Campaign API endpoints.

This module provides REST API endpoints for managing email campaigns.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.company import Company
from app.services.campaign_services import CampaignService
from app.schemas.campaign import (
    CampaignCreate, 
    CampaignUpdate, 
    CampaignResponse, 
    CampaignListResponse,
    CampaignFilter
)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.get("/test", tags=["Campaigns"])
async def test_campaign_endpoint():
    """
    Simple test endpoint to verify campaigns router is working.
    """
    return {"message": "Campaigns endpoint is working!", "status": "ok"}

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new email campaign.
    """
    try:
        campaign_service = CampaignService(db)
        campaign = await campaign_service.create_campaign(
            campaign_data=campaign_data,
            company_id=current_user.company_id,
            user_id=current_user.id
        )
        return campaign
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create campaign"
        )

@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search campaign names"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List campaigns for the current user's company.
    """
    try:
        campaign_service = CampaignService(db)
        
        # Build filter object
        filters = CampaignFilter(
            search=search,
            status=status,
            is_active=is_active
        )
        
        campaigns, total = await campaign_service.list_campaigns(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            filters=filters
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "campaigns": campaigns,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list campaigns"
        )

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific campaign by ID.
    """
    try:
        campaign_service = CampaignService(db)
        campaign = await campaign_service.get_campaign(
            campaign_id=campaign_id,
            company_id=current_user.company_id
        )
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign"
        )

@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a campaign.
    """
    try:
        campaign_service = CampaignService(db)
        campaign = await campaign_service.update_campaign(
            campaign_id=campaign_id,
            company_id=current_user.company_id,
            update_data=campaign_data
        )
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return campaign
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update campaign"
        )

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a campaign.
    """
    try:
        campaign_service = CampaignService(db)
        success = await campaign_service.delete_campaign(
            campaign_id=campaign_id,
            company_id=current_user.company_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return {"message": "Campaign deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete campaign"
        ) 