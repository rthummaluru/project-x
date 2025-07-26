# backend/app/services/email_service.py
"""
Email generation service using OpenAI API.

This service takes lead data and generates personalized emails
using AI. It will be the core of your agent functionality.
"""

import openai
from typing import Optional, Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.core.config import settings

from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class EmailService:
    """
    Service for generating personalized emails using OpenAI.
    
    """
    
    def __init__(self):
        
        self.client = openai.OpenAI(api_key=settings.openai_api_key)

    async def generate_email(self, lead: Lead) -> Dict[str, Any]:
        """
        Generate a personalized email for a lead.

        Args:
            lead: Lead object containing lead data

        Returns:
            Dict containing email subject, body, and other details
        """

        try:
            #Build the prompt with the lead data
            prompt = self._generate_email_prompt(lead)

            #Call the OpenAI API
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert sales email writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            #Parse the response
            email_content = response.choices[0].message.content

            # Split into subject and body (we'll improve this)
            lines = email_content.strip().split('\n')
            subject = lines[0].replace("Subject: ", "")
            body = '\n'.join(lines[1:]).strip()

            return {
                "subject": subject,
                "body": body,
                "lead_id": lead.id,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "model_used": "gpt-4o",
                "tokens_used": response.usage.total_tokens,
            }
        
        except Exception as e:
            logger.error(f"Failed to generated email for lead {lead.id}: {e}")
            raise e
    

    def _generate_email_prompt(self, lead: Lead) -> str:
        """
        Generate a prompt for the email generation model.
        """
        prompt = f"""
            Generate a personalized email for this lead:"
            Name: {lead.full_name}
            Company: {lead.company_name}
            Email: {lead.email}
            Phone: {lead.phone}
            LinkedIn: {lead.linkedin_url}

                    Email Requirements:
            - Keep it under 150 words
            - Professional but friendly tone
            - Mention their specific role and company
            - Include a clear call-to-action
            - Format: Subject line first, then email body

            Write the email now
        """
        return prompt

if __name__ == "__main__":
    pass