#!/usr/bin/env python3
"""
Script to set up the database and import leads for local development.

This script:
1. Sets up SQLite database for local development
2. Creates all tables
3. Imports leads from CSV
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_db, AsyncSessionLocal
from app.models.company import Company
from app.models.lead import Lead
from app.models.user import User
from app.models.campaign import Campaign
from app.models.campaign_email import CampaignEmail

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def setup_database():
    """Set up the database with initial data."""
    
    try:
        # Initialize database (creates all tables)
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Create a default company if none exists
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            
            # Check if any companies exist
            result = await db.execute(select(Company))
            companies = result.scalars().all()
            
            if not companies:
                # Create default company
                default_company = Company(name="Default Company")
                db.add(default_company)
                await db.flush()
                await db.refresh(default_company)
                logger.info(f"✅ Created default company: {default_company.name} (ID: {default_company.id})")
            else:
                logger.info(f"✅ Found {len(companies)} existing companies")
            
            await db.commit()
        
        logger.info("✅ Database setup completed")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

async def main():
    """Main function to set up database and import leads."""
    
    try:
        # Set up database
        await setup_database()
        
        # Import leads
        logger.info("🔄 Starting lead import...")
        from import_leads import CSVLeadImporter
        
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
            logger.info("✅ Setup and import completed successfully!")
            logger.info("🚀 You can now start the API server with: python -m app.main")
        else:
            logger.warning("⚠️  No leads were imported. Check the logs for details.")
            
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 