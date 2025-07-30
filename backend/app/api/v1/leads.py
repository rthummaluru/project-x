# backend/app/api/v1/leads.py
"""
Lead API endpoints.

This file contains all HTTP endpoints for lead operations.
The endpoints are thin - they just handle HTTP concerns and
delegate business logic to the service layer.

Key concepts:
- Dependency Injection: FastAPI automatically provides dependencies
- Error Handling: Proper HTTP status codes and error messages
- Validation: Pydantic automatically validates request data
- Documentation: FastAPI auto-generates API docs
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging

from app.core.database import get_db
from app.services.lead_service import LeadService
from app.services.email_services import EmailService
from app.schemas.lead import (
    LeadCreate, 
    LeadUpdate, 
    LeadResponse, 
    LeadListResponse,
    LeadFilter,
    LeadBulkCreate,
    LeadBulkResponse
)
# We'll create this dependency nextyou
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

# Create router with prefix and tags for organization
router = APIRouter(prefix="/leads", tags=["leads"])

@router.get("/debug", tags=["leads"])
async def debug_leads_endpoint():
    """
    Debug endpoint to test if leads router is working.
    """
    return {"message": "Leads endpoint is working!", "status": "ok"}

@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new lead.
    
    This endpoint:
    1. Validates the lead data (Pydantic does this automatically)
    2. Checks for duplicates within the company
    3. Calculates initial lead score
    4. Saves to database
    
    **Example Request:**
    ```json
    {
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company_name": "Example Corp",
        "job_title": "VP of Sales",
        "source": "linkedin",
        "custom_fields": {
            "industry": "SaaS",
            "company_size": "100-500"
        }
    }
    ```
    """
    
    try:
        # Create lead service instance
        lead_service = LeadService(db)
        
        # Create the lead (service handles all business logic)
        lead = await lead_service.create_lead(
            lead_data=lead_data,
            company_id=current_user.company_id,  # Multi-tenant security
            created_by=current_user.id
        )
        
        logger.info(f"Lead created: {lead.id} by user {current_user.id}")
        
        # Return the created lead (Pydantic converts SQLAlchemy model to JSON)
        return lead
        
    except ValueError as e:
        # Business logic errors (duplicate lead, validation, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error creating lead: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/", response_model=LeadListResponse)
async def list_leads(
    # Query parameters for filtering and pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    company_name: Optional[str] = Query(None, description="Filter by company name"),
    search: Optional[str] = Query(None, description="Search across name, email, company"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum lead score"),
    max_score: Optional[int] = Query(None, ge=0, le=100, description="Maximum lead score"),
    
    # Dependencies
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get a paginated list of leads with optional filtering.
    
    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 50, max: 100)
    - `status`: Filter by lead status
    - `source`: Filter by lead source
    - `search`: Search across name, email, and company
    - `min_score`/`max_score`: Filter by lead score range
    
    **Example Response:**
    ```json
    {
        "leads": [
            {
                "id": 1,
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "company_name": "Example Corp",
                "score": 85,
                "status": "qualified"
            }
        ],
        "total": 150,
        "page": 1,
        "page_size": 50,
        "total_pages": 3
    }
    ```
    """
    
    try:
        # Build filters from query parameters
        filters = LeadFilter(
            status=status,
            source=source,
            company_name=company_name,
            search=search,
            min_score=min_score,
            max_score=max_score
        )
        
        # Get leads from service
        lead_service = LeadService(db)
        leads, total = await lead_service.list_leads(
            company_id=current_user.company_id,
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size  # Ceiling division
        
        return LeadListResponse(
            leads=leads,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing leads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching leads"
        )

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get a specific lead by ID.
    
    Returns 404 if the lead doesn't exist or doesn't belong to the user's company.
    """
    
    lead_service = LeadService(db)
    lead = await lead_service.get_lead(
        lead_id=lead_id,
        company_id=current_user.company_id
    )
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    
    return lead

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update an existing lead.
    
    You can update any subset of fields. Only provided fields will be updated.
    """
    
    try:
        lead_service = LeadService(db)
        lead = await lead_service.update_lead(
            lead_id=lead_id,
            company_id=current_user.company_id,
            lead_data=lead_data
        )
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {lead_id} not found"
            )
        
        logger.info(f"Lead updated: {lead_id} by user {current_user.id}")
        return lead
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the lead"
        )

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a lead (soft delete).
    
    The lead will be marked as deleted but not removed from the database.
    Returns 204 No Content on success, 404 if lead not found.
    """
    
    lead_service = LeadService(db)
    deleted = await lead_service.delete_lead(
        lead_id=lead_id,
        company_id=current_user.company_id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    
    logger.info(f"Lead deleted: {lead_id} by user {current_user.id}")
    # 204 No Content - successful deletion with no response body

@router.post("/bulk", response_model=LeadBulkResponse)
async def create_leads_bulk(
    bulk_data: LeadBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create multiple leads at once.
    
    **Benefits of bulk creation:**
    - More efficient for large imports
    - Atomic transaction (all succeed or all fail)
    - Detailed error reporting per lead
    
    **Limits:**
    - Maximum 100 leads per request
    - Duplicate emails within the batch will be rejected
    """
    
    lead_service = LeadService(db)
    created_leads = []
    errors = []
    
    # Process each lead
    for i, lead_data in enumerate(bulk_data.leads):
        try:
            lead = await lead_service.create_lead(
                lead_data=lead_data,
                company_id=current_user.company_id,
                created_by=current_user.id
            )
            created_leads.append(lead)
            
        except Exception as e:
            errors.append({
                "index": i,
                "email": lead_data.email,
                "error": str(e)
            })
    
    logger.info(
        f"Bulk lead creation: {len(created_leads)} created, "
        f"{len(errors)} errors for user {current_user.id}"
    )
    
    return LeadBulkResponse(
        created=created_leads,
        errors=errors
    )

@router.post("/{lead_id}/generate-email", response_model=dict)
async def generate_email(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate an email for a lead.
    """
    try:
        lead_service = LeadService(db)
        lead = await lead_service.get_lead(lead_id=lead_id, company_id=current_user.company_id)

        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead with ID {lead_id} not found"
            )
        
        email_service = EmailService()
        email_data = await email_service.generate_email(lead)

        return email_data
    
    except Exception as e:
        logger.error(f"Error generating email for lead {lead_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the email"
        )
            