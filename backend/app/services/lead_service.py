# backend/app/services/lead_service.py
"""
Lead service layer - contains all business logic for lead operations.

Why use a service layer?
- Keeps API endpoints thin and focused
- Reusable business logic (can be called from different endpoints)
- Easier testing (mock the service, not the database)
- Clear separation of concerns
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate, LeadFilter
from app.core.database import get_db

logger = logging.getLogger(__name__)

class LeadService:
    """
    Service class for lead operations.
    
    This class encapsulates all business logic related to leads:
    - CRUD operations
    - Lead scoring
    - Duplicate detection
    - Search and filtering
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_lead(
        self, 
        lead_data: LeadCreate, 
        company_id: int, 
        created_by: Optional[int] = None
    ) -> Lead:
        """
        Create a new lead with business logic validation.
        
        Args:
            lead_data: Validated lead data from API
            company_id: Company the lead belongs to (from auth)
            created_by: User who created the lead (optional)
            
        Returns:
            Created lead instance
            
        Raises:
            ValueError: If lead already exists or validation fails
        """
        
        try:
            logger.info(f"Creating lead for company {company_id}, email: {lead_data.email}")
            
            # Check for duplicate leads (same email within company)
            existing_lead = await self._find_duplicate_lead(
                email=lead_data.email,
                company_id=company_id
            )
            
            if existing_lead:
                if existing_lead.is_deleted:
                    # Reactivate soft-deleted lead instead of creating new one
                    return await self._reactivate_lead(existing_lead, lead_data)
                else:
                    raise ValueError(f"Lead with email {lead_data.email} already exists")
            
            # Create new lead
            db_lead = Lead(
                company_id=company_id,
                created_by=created_by,
                **lead_data.model_dump()
            )
            
            # Apply initial lead scoring
            db_lead = await self._calculate_lead_score(db_lead)
            
            # Set initial status based on score
            db_lead.status = "qualified" if db_lead.score >= 50 else "new"
            
            self.db.add(db_lead)
            await self.db.flush()  # Get the ID without committing
            await self.db.refresh(db_lead)
            
            logger.info(f"Created lead {db_lead.id} for company {company_id}")
            return db_lead
            
        except Exception as e:
            logger.error(f"Error creating lead: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def get_lead(self, lead_id: int, company_id: int) -> Optional[Lead]:
        """
        Get a lead by ID, ensuring it belongs to the company.
        
        This is important for multi-tenant security - users can only
        access leads from their own company.
        """
        
        query = select(Lead).where(
            and_(
                Lead.id == lead_id,
                Lead.company_id == company_id,
                Lead.is_deleted == False
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_lead(
        self, 
        lead_id: int, 
        company_id: int, 
        lead_data: LeadUpdate
    ) -> Optional[Lead]:
        """Update a lead with business logic validation."""
        
        # Get existing lead
        lead = await self.get_lead(lead_id, company_id)
        if not lead:
            return None
        
        # Check for email conflicts if email is being changed
        if lead_data.email and lead_data.email != lead.email:
            duplicate = await self._find_duplicate_lead(
                email=lead_data.email,
                company_id=company_id
            )
            if duplicate and duplicate.id != lead_id:
                raise ValueError(f"Lead with email {lead_data.email} already exists")
        
        # Update fields (only non-None values)
        update_data = lead_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)
        
        # Recalculate score if relevant fields changed
        if any(field in update_data for field in ['company_name', 'job_title', 'source']):
            lead = await self._calculate_lead_score(lead)
        
        await self.db.flush()
        await self.db.refresh(lead)
        
        logger.info(f"Updated lead {lead_id}")
        return lead
    
    async def delete_lead(self, lead_id: int, company_id: int) -> bool:
        """
        Soft delete a lead (set is_deleted=True).
        
        We never hard delete leads for compliance and audit purposes.
        """
        
        lead = await self.get_lead(lead_id, company_id)
        if not lead:
            return False
        
        lead.is_deleted = True
        await self.db.flush()
        
        logger.info(f"Soft deleted lead {lead_id}")
        return True
    
    async def list_leads(
        self,
        company_id: int,
        filters: Optional[LeadFilter] = None,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Lead], int]:
        """
        Get a paginated list of leads with filtering.
        
        Returns:
            Tuple of (leads, total_count)
        """
        
        # Base query
        query = select(Lead).where(
            and_(
                Lead.company_id == company_id,
                Lead.is_deleted == False
            )
        )
        
        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(Lead.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        leads = result.scalars().all()
        
        return list(leads), total
    
    async def _find_duplicate_lead(self, email: str, company_id: int) -> Optional[Lead]:
        """Find existing lead with same email in company."""
        
        query = select(Lead).where(
            and_(
                Lead.email == email.lower(),
                Lead.company_id == company_id
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _reactivate_lead(self, lead: Lead, lead_data: LeadCreate) -> Lead:
        """Reactivate a soft-deleted lead with new data."""
        
        # Update with new data
        for field, value in lead_data.model_dump().items():
            setattr(lead, field, value)
        
        # Reactivate
        lead.is_deleted = False
        lead.updated_at = datetime.utcnow()
        
        # Recalculate score
        lead = await self._calculate_lead_score(lead)
        
        await self.db.flush()
        await self.db.refresh(lead)
        
        logger.info(f"Reactivated lead {lead.id}")
        return lead
    
    async def _calculate_lead_score(self, lead: Lead) -> Lead:
        """
        Calculate lead score based on available data.
        
        Scoring algorithm (0-100):
        - Has company name: +20 points
        - Has job title: +15 points
        - Senior position keywords: +20 points
        - High-value company size indicators: +15 points
        - Premium email domain: +10 points
        - Has phone number: +10 points
        - Quality source: +10 points
        """
        
        score = 0
        
        # Company name available
        if lead.company_name:
            score += 20
        
        # Job title available
        if lead.job_title:
            score += 15
            
            # Senior position bonus
            senior_keywords = ['director', 'manager', 'head', 'vp', 'ceo', 'cto', 'cfo']
            if any(keyword in lead.job_title.lower() for keyword in senior_keywords):
                score += 20
        
        # Phone number available
        if lead.phone:
            score += 10
        
        # Email domain quality (basic heuristic)
        if lead.email:
            domain = lead.email.split('@')[1].lower()
            # Avoid free email providers
            free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
            if domain not in free_domains:
                score += 10
        
        # Source quality
        high_quality_sources = ['linkedin', 'referral', 'event']
        if lead.source in high_quality_sources:
            score += 10
        
        # Cap at 100
        lead.score = min(score, 100)
        
        return lead
    
    def _apply_filters(self, query, filters: LeadFilter):
        """Apply filters to the lead query."""
        
        if filters.status:
            query = query.where(Lead.status == filters.status)
        
        if filters.source:
            query = query.where(Lead.source == filters.source)
        
        if filters.company_name:
            query = query.where(
                Lead.company_name.ilike(f"%{filters.company_name}%")
            )
        
        if filters.min_score is not None:
            query = query.where(Lead.score >= filters.min_score)
        
        if filters.max_score is not None:
            query = query.where(Lead.score <= filters.max_score)
        
        if filters.created_after:
            query = query.where(Lead.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.where(Lead.created_at <= filters.created_before)
        
        if filters.search:
            # Search across multiple fields
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Lead.first_name.ilike(search_term),
                    Lead.last_name.ilike(search_term),
                    Lead.email.ilike(search_term),
                    Lead.company_name.ilike(search_term)
                )
            )
        
        return query