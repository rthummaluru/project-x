"""
Campaign services for managing email campaigns.

This module contains the core business logic for creating,
updating, and managing email campaigns.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select, where

from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_email import CampaignEmail, CampaignEmailStatus
from app.models.lead import Lead
from app.services.email_services import EmailService
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignContext, CampaignDelays
from app.schemas.lead import LeadFilter


class CampaignService:
    """
    Service for managing email campaigns.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_service = EmailService()

    async def create_campaign(self, campaign_data: CampaignCreate, company_id: int, user_id: int) -> Campaign:
        """
        Create a new campaign.
        """
        # Step 1: Create campaign object
        campaign = Campaign(
            name=campaign_data.name,
            company_id=company_id,
            user_id=user_id,
            context_json=campaign_data.context.dict(),
            delays_json=campaign_data.delays.delays if campaign_data.delays else {"1": 0},
            max_sequence_length=campaign_data.max_sequence_length or 4,
            status=CampaignStatus.DRAFT,
            scheduled_start=campaign_data.scheduled_start,
            is_active=True
        )
        
        # Step 2: Save to database
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        
        # Step 3: Get filtered leads  
        leads = await self._get_filtered_leads(company_id, campaign_data.lead_filter)
        
        # Step 4: Check if any leads found
        if len(leads) == 0:
            raise ValueError("No leads found matching the campaign criteria. Please check your lead filters or add more leads.")
        
        # Step 5: Generate emails (batch process)
        await self._batch_generate_emails(campaign, leads)
        
        # Step 6: Return campaign
        return campaign
    
    async def _get_filtered_leads(self, company_id: int, lead_filter: Optional[LeadFilter]) -> list[Lead]:
        
        query = select(Lead).where(Lead.company_id == company_id)

        """
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
        """

        if lead_filter:
            if lead_filter.min_score is not None:
                query = query.where(Lead.score >= lead_filter.min_score)
            if lead_filter.status:
                query = query.where(Lead.status == lead_filter.status)
            if lead_filter.source:
                query = query.where(Lead.source == lead_filter.source)
            if lead_filter.company_name:
                query = query.where(Lead.company_name.ilike(f"%{lead_filter.company_name}%"))
            if lead_filter.max_score is not None:
                query = query.where(Lead.score <= lead_filter.max_score)
            if lead_filter.created_after:
                query = query.where(Lead.created_at >= lead_filter.created_after)
            if lead_filter.created_before:
                query = query.where(Lead.created_at <= lead_filter.created_before)
            if lead_filter.search:
                search_term = f"%{lead_filter.search}%"
                query = query.where(
                    (Lead.first_name.ilike(search_term)) |
                    (Lead.last_name.ilike(search_term)) |
                    (Lead.email.ilike(search_term)) |
                    (Lead.company_name.ilike(search_term))
                )
            
        result = await self.db.execute(query) 
        return result.scalars().all()
    

    async def _batch_generate_emails(self, campaign: Campaign, leads: list[Lead]) -> list[CampaignEmail]:

        email_list = []
               
        if campaign:
            context_dict = campaign.context_json
            context = CampaignContext(**context_dict)      
        for lead in leads:
            try:
                # Generate email
                email_data = await self.email_service.generate_email(lead, context)
                
                # Create successful CampaignEmail record
                campaign_email = CampaignEmail(
                    campaign_id=campaign.id,
                    lead_id=lead.id,
                    from_email="user@company.com",  # TODO: Get from user settings
                    provider="gmail",  # TODO: Auto-detect
                    sequence_position=1,  # TODO: Handle sequences later
                    status=CampaignEmailStatus.GENERATED,
                    subject_line=email_data["subject"],
                    email_content=email_data["body"]
                )
                
                self.db.add(campaign_email)
                email_list.append(campaign_email)
                
            except Exception as e:
                # Create failed CampaignEmail record
                failed_email = CampaignEmail(
                    campaign_id=campaign.id,
                    lead_id=lead.id,
                    sequence_position=1,
                    status=CampaignEmailStatus.FAILED,
                    error_message=str(e),
                    subject_line=None,
                    email_content=None
                )
                
                self.db.add(failed_email)
                email_list.append(failed_email)
             # Save all records and return
        
        await self.db.commit()
        return email_list

