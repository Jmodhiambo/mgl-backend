#!/usr/bin/env python3
"""Centralized email manager for MGLTickets."""

from typing import Dict, Optional
from app.emails.base import EmailService
from app.emails.sendgrid_service import SendGridEmailService
from app.emails.templates.template_registry import TemplateRegistry
from app.core.logging_config import logger


class EmailManager:
    """
    Centralized email manager that handles all email sending operations.
    Uses template registry and email service to send templated emails.
    """
    
    def __init__(self, service: Optional[EmailService] = None):
        """
        Initialize email manager.
        
        Args:
            service: Email service to use. If None, uses SendGridEmailService.
        """
        self.service = service or SendGridEmailService()
        self.registry = TemplateRegistry()
        logger.info("Email manager initialized")
    
    async def send_from_template(
        self,
        template_id: str,
        to_email: str,
        variables: Dict[str, str],
        from_email: str = "no_reply"
    ) -> bool:
        """
        Send email using a registered template.
        
        Args:
            template_id: ID of the template to use (e.g., 'user.verification')
            to_email: Recipient email address
            variables: Dictionary of variables to replace in template
            from_email: Sender email identifier ('no_reply', 'support', 'billing', etc.)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        
        Raises:
            ValueError: If template not found or missing required variables
        """
        try:
            # Get template from registry
            template = self.registry.get_template(template_id)
            if not template:
                raise ValueError(f"Template '{template_id}' not found")
            
            # Render email content
            subject = template.render_subject(variables)
            body = template.render_body(variables)
            
            # Send email
            logger.info(f"Sending email using template '{template_id}' to {to_email}")
            
            self.service.send_email(
                to_email=to_email,
                subject=subject,
                html_content=body,
                template_data={'from_email': from_email}
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except ValueError as e:
            logger.error(f"Template error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def list_templates(self, category: Optional[str] = None) -> Dict:
        """
        List available email templates.
        
        Args:
            category: Optional category filter ('user', 'organizer', 'admin')
        
        Returns:
            Dictionary of template metadata
        """
        return self.registry.list_templates(category)
    
    def get_template_info(self, template_id: str) -> Optional[Dict]:
        """
        Get information about a specific template.
        
        Args:
            template_id: Template identifier
        
        Returns:
            Template metadata or None if not found
        """
        template = self.registry.get_template(template_id)
        return template.get_metadata() if template else None


# Global instance
email_manager = EmailManager()