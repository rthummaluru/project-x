#!/usr/bin/env python3
"""
Script to import leads from CSV file into the database.

This script:
1. Reads the demo_leads.csv file
2. Creates a default company if none exists
3. Maps CSV columns to Lead model fields
4. Imports all leads with proper validation
5. Handles duplicates gracefully
"""

import asyncio
import csv
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, init_db
from app.models.lead import Lead
from app.models.company import Company
from app.services.lead_service import LeadService
from app.schemas.lead import LeadCreate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CSVLeadImporter:
    """Handles importing leads from CSV file."""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.stats = {
            'total_rows': 0,
            'imported': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def _map_csv_row_to_lead_data(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map CSV row data to Lead model fields.
        
        Maps the CSV columns to the appropriate Lead model fields,
        handling any data transformation needed.
        """
        
        # Direct mappings
        lead_data = {
            'email': row.get('email', '').strip().lower(),
            'first_name': row.get('first_name', '').strip(),
            'last_name': row.get('last_name', '').strip(),
            'company_name': row.get('company_name', '').strip(),
            'job_title': row.get('job_title', '').strip(),
            'phone': row.get('phone', '').strip(),
            'linkedin_url': row.get('linkedin_url', '').strip(),
            'notes': row.get('notes', '').strip(),
        }
        
        # Handle source field - map to valid enum values
        source = row.get('source', '').strip().lower()
        if source in ['apollo', 'linkedin', 'website', 'referral', 'cold_email', 'event']:
            lead_data['source'] = source
        elif source:
            lead_data['source'] = 'other'
        else:
            lead_data['source'] = None
        
        # Store additional CSV data in custom_fields
        custom_fields = {}
        
        # Map additional fields that aren't in the base Lead model
        additional_fields = [
            'industry', 'company_size', 'tech_stack', 'funding_stage', 
            'employee_count', 'annual_revenue'
        ]
        
        for field in additional_fields:
            if field in row and row[field]:
                custom_fields[field] = row[field].strip()
        
        if custom_fields:
            lead_data['custom_fields'] = custom_fields
        
        return lead_data
    
    def _validate_lead_data(self, lead_data: Dict[str, Any]) -> bool:
        """Validate lead data before import."""
        
        # Email is required
        if not lead_data.get('email'):
            logger.warning(f"Skipping row: Missing email")
            return False
        
        # Basic email validation
        if '@' not in lead_data['email']:
            logger.warning(f"Skipping row: Invalid email format: {lead_data['email']}")
            return False
        
        return True
    
    async def _get_or_create_default_company(self, db: AsyncSession) -> Company:
        """Get or create a default company for the leads."""
        
        from sqlalchemy import select
        
        # Try to find existing company
        result = await db.execute(
            select(Company).where(Company.name == "Default Company")
        )
        company = result.scalar_one_or_none()
        
        if company:
            logger.info(f"Using existing company: {company.name} (ID: {company.id})")
            return company
        
        # Create new company
        new_company = Company(name="Default Company")
        db.add(new_company)
        await db.flush()
        await db.refresh(new_company)
        
        logger.info(f"Created new company: {new_company.name} (ID: {new_company.id})")
        return new_company
    
    async def import_leads(self) -> Dict[str, int]:
        """Import leads from CSV file."""
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        logger.info(f"Starting import from: {self.csv_path}")
        
        async with AsyncSessionLocal() as db:
            # Get or create default company
            company = await self._get_or_create_default_company(db)
            
            # Initialize lead service
            lead_service = LeadService(db)
            
            # Read CSV file
            with open(self.csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    self.stats['total_rows'] += 1
                    
                    try:
                        # Map CSV data to lead fields
                        lead_data = self._map_csv_row_to_lead_data(row)
                        
                        # Validate data
                        if not self._validate_lead_data(lead_data):
                            self.stats['skipped'] += 1
                            continue
                        
                        # Create LeadCreate schema
                        lead_create = LeadCreate(**lead_data)
                        
                        # Import lead using service
                        lead = await lead_service.create_lead(
                            lead_data=lead_create,
                            company_id=company.id,
                            created_by=None  # System import
                        )
                        
                        self.stats['imported'] += 1
                        logger.info(f"Imported lead: {lead.email} ({lead.full_name})")
                        
                    except ValueError as e:
                        # Handle duplicate leads gracefully
                        if "already exists" in str(e):
                            self.stats['skipped'] += 1
                            logger.info(f"Skipped duplicate: {lead_data.get('email', 'unknown')}")
                        else:
                            self.stats['errors'] += 1
                            logger.error(f"Error importing row {row_num}: {e}")
                    
                    except Exception as e:
                        self.stats['errors'] += 1
                        logger.error(f"Unexpected error importing row {row_num}: {e}")
                
                # Commit all changes
                await db.commit()
        
        return self.stats

async def main():
    """Main function to run the import."""
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Import leads
        importer = CSVLeadImporter("demo_leads.csv")
        stats = await importer.import_leads()
        
        # Print summary
        logger.info("=" * 50)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total rows processed: {stats['total_rows']}")
        logger.info(f"Successfully imported: {stats['imported']}")
        logger.info(f"Skipped (duplicates): {stats['skipped']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info("=" * 50)
        
        if stats['imported'] > 0:
            logger.info("✅ Import completed successfully!")
        else:
            logger.warning("⚠️  No leads were imported. Check the logs for details.")
            
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 