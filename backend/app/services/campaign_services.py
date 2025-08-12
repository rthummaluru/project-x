"""
Campaign services for managing email campaigns.

This module contains the core business logic for creating,
updating, and managing email campaigns.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, or_
import logging

from app.models.campaign import Campaign, CampaignStatus
from app.models.campaign_email import CampaignEmail, CampaignEmailStatus
from app.models.lead import Lead
from app.services.email_services import EmailService
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignContext, CampaignDelays, CampaignFilter
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
        try:
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
            
            # Step 6: Convert JSON fields for response
            # Add context and delays fields to the campaign object for response serialization
            campaign.context = CampaignContext(**campaign.context_json)
            campaign.delays = CampaignDelays(delays=campaign.delays_json)
            
            return campaign
            
        except Exception as e:
            # Log the full error for debugging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating campaign: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def _get_filtered_leads(self, company_id: int, lead_filter: Optional[LeadFilter]) -> list[Lead]:
        
        logger = logging.getLogger(__name__)
        try:
            query = select(Lead).where(Lead.company_id == company_id)

            if lead_filter:
                logger.info(f"Applying lead filter: {lead_filter}")
                
                if lead_filter.min_score is not None:
                    query = query.where(Lead.score >= lead_filter.min_score)
                    logger.info(f"Added min_score filter: >= {lead_filter.min_score}")
                    
                if lead_filter.status:
                    query = query.where(Lead.status == lead_filter.status)
                    logger.info(f"Added status filter: = {lead_filter.status}")
                    
                if lead_filter.source:
                    query = query.where(Lead.source == lead_filter.source)
                    logger.info(f"Added source filter: = {lead_filter.source}")
                    
                if lead_filter.company_name:
                    query = query.where(Lead.company_name.ilike(f"%{lead_filter.company_name}%"))
                    logger.info(f"Added company_name filter: LIKE %{lead_filter.company_name}%")
                    
                if lead_filter.max_score is not None:
                    query = query.where(Lead.score <= lead_filter.max_score)
                    logger.info(f"Added max_score filter: <= {lead_filter.max_score}")
                    
                if lead_filter.created_after:
                    query = query.where(Lead.created_at >= lead_filter.created_after)
                    logger.info(f"Added created_after filter: >= {lead_filter.created_after}")
                    
                if lead_filter.created_before:
                    query = query.where(Lead.created_at <= lead_filter.created_before)
                    logger.info(f"Added created_before filter: <= {lead_filter.created_before}")
                    
                if lead_filter.search:
                    search_term = f"%{lead_filter.search}%"
                    query = query.where(
                        (Lead.first_name.ilike(search_term)) |
                        (Lead.last_name.ilike(search_term)) |
                        (Lead.email.ilike(search_term)) |
                        (Lead.company_name.ilike(search_term))
                    )
                    logger.info(f"Added search filter: LIKE %{lead_filter.search}%")
                
            result = await self.db.execute(query) 
            leads = result.scalars().all()
            
            # Debug logging
            logger = logging.getLogger(__name__)
            logger.info(f"Found {len(leads)} leads for company {company_id}")
            
            return leads
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting filtered leads: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    

    async def _batch_generate_emails(self, campaign: Campaign, leads: list[Lead]) -> list[CampaignEmail]:

        email_list = []
        
        try:
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
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in batch email generation: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def list_campaigns(
        self, 
        company_id: int, 
        page: int = 1, 
        page_size: int = 10,
        filters: Optional[CampaignFilter] = None
    ) -> tuple[List[Campaign], int]:
        """
        List campaigns with pagination and filtering.
        """
        try:
            # Base query
            query = select(Campaign).where(Campaign.company_id == company_id)
            count_query = select(func.count()).select_from(Campaign).where(Campaign.company_id == company_id)
            
            # Apply filters
            if filters:
                if filters.search:
                    search_term = f"%{filters.search}%"
                    query = query.where(Campaign.name.ilike(search_term))
                    count_query = count_query.where(Campaign.name.ilike(search_term))
                
                if filters.status:
                    query = query.where(Campaign.status == filters.status)
                    count_query = count_query.where(Campaign.status == filters.status)
                
                if filters.is_active is not None:
                    query = query.where(Campaign.is_active == filters.is_active)
                    count_query = count_query.where(Campaign.is_active == filters.is_active)
                
                if filters.created_after:
                    query = query.where(Campaign.created_at >= filters.created_after)
                    count_query = count_query.where(Campaign.created_at >= filters.created_after)
                
                if filters.created_before:
                    query = query.where(Campaign.created_at <= filters.created_before)
                    count_query = count_query.where(Campaign.created_at <= filters.created_before)
            
            # Add ordering and pagination
            query = query.order_by(Campaign.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # Execute queries
            campaigns_result = await self.db.execute(query)
            campaigns = campaigns_result.scalars().all()
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Add computed fields for each campaign
            for campaign in campaigns:
                campaign.context = CampaignContext(**campaign.context_json)
                campaign.delays = CampaignDelays(delays=campaign.delays_json)
                
                # Get email counts
                email_count_query = select(func.count()).select_from(CampaignEmail).where(
                    CampaignEmail.campaign_id == campaign.id
                )
                email_count_result = await self.db.execute(email_count_query)
                campaign.email_count = email_count_result.scalar() or 0
                
                sent_count_query = select(func.count()).select_from(CampaignEmail).where(
                    and_(
                        CampaignEmail.campaign_id == campaign.id,
                        CampaignEmail.status == CampaignEmailStatus.SENT
                    )
                )
                sent_count_result = await self.db.execute(sent_count_query)
                campaign.sent_count = sent_count_result.scalar() or 0
                
                failed_count_query = select(func.count()).select_from(CampaignEmail).where(
                    and_(
                        CampaignEmail.campaign_id == campaign.id,
                        CampaignEmail.status == CampaignEmailStatus.FAILED
                    )
                )
                failed_count_result = await self.db.execute(failed_count_query)
                campaign.failed_count = failed_count_result.scalar() or 0
            
            return campaigns, total
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error listing campaigns: {str(e)}")
            raise

    async def get_campaign(self, campaign_id: int, company_id: int) -> Optional[Campaign]:
        """
        Get a specific campaign by ID.
        """
        try:
            query = select(Campaign).where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.company_id == company_id
                )
            )
            
            result = await self.db.execute(query)
            campaign = result.scalar_one_or_none()
            
            if campaign:
                # Add computed fields
                campaign.context = CampaignContext(**campaign.context_json)
                campaign.delays = CampaignDelays(delays=campaign.delays_json)
                
                # Get email counts
                email_count_query = select(func.count()).select_from(CampaignEmail).where(
                    CampaignEmail.campaign_id == campaign.id
                )
                email_count_result = await self.db.execute(email_count_query)
                campaign.email_count = email_count_result.scalar() or 0
                
                sent_count_query = select(func.count()).select_from(CampaignEmail).where(
                    and_(
                        CampaignEmail.campaign_id == campaign.id,
                        CampaignEmail.status == CampaignEmailStatus.SENT
                    )
                )
                sent_count_result = await self.db.execute(sent_count_query)
                campaign.sent_count = sent_count_result.scalar() or 0
                
                failed_count_query = select(func.count()).select_from(CampaignEmail).where(
                    and_(
                        CampaignEmail.campaign_id == campaign.id,
                        CampaignEmail.status == CampaignEmailStatus.FAILED
                    )
                )
                failed_count_result = await self.db.execute(failed_count_query)
                campaign.failed_count = failed_count_result.scalar() or 0
            
            return campaign
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting campaign: {str(e)}")
            raise

    async def update_campaign(
        self, 
        campaign_id: int, 
        company_id: int, 
        update_data: CampaignUpdate
    ) -> Optional[Campaign]:
        """
        Update a campaign.
        """
        try:
            # First get the campaign
            campaign = await self.get_campaign(campaign_id, company_id)
            if not campaign:
                return None
            
            # Check if campaign can be updated (only drafts typically)
            if campaign.status != CampaignStatus.DRAFT:
                raise ValueError("Only draft campaigns can be updated")
            
            # Apply updates
            if update_data.name is not None:
                campaign.name = update_data.name
            
            if update_data.context is not None:
                campaign.context_json = update_data.context.dict()
            
            if update_data.delays is not None:
                campaign.delays_json = update_data.delays.delays
            
            if update_data.scheduled_start is not None:
                campaign.scheduled_start = update_data.scheduled_start
            
            if update_data.status is not None:
                campaign.status = update_data.status
            
            if update_data.is_active is not None:
                campaign.is_active = update_data.is_active
            
            campaign.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(campaign)
            
            # Add computed fields for response
            campaign.context = CampaignContext(**campaign.context_json)
            campaign.delays = CampaignDelays(delays=campaign.delays_json)
            
            return campaign
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating campaign: {str(e)}")
            raise

    async def delete_campaign(self, campaign_id: int, company_id: int) -> bool:
        """
        Delete a campaign (soft delete).
        """
        try:
            query = select(Campaign).where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.company_id == company_id
                )
            )
            
            result = await self.db.execute(query)
            campaign = result.scalar_one_or_none()
            
            if not campaign:
                return False
            
            # Soft delete
            campaign.is_active = False
            campaign.updated_at = datetime.utcnow()
            
            await self.db.commit()
            return True
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error deleting campaign: {str(e)}")
            raise

