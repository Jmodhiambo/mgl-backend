#!/usr/bin/env python3
"""Template registry for managing all email templates."""

from typing import Dict, Optional, List
from app.emails.templates.email_template_base import EmailTemplate
from app.core.logging_config import logger


class TemplateRegistry:
    """Registry for managing and accessing email templates."""
    
    def __init__(self):
        """Initialize registry and register all templates."""
        self.templates: Dict[str, EmailTemplate] = {}
        self._register_all_templates()
        logger.info(f"Template registry initialized with {len(self.templates)} templates")
    
    def _register_all_templates(self):
        """Register all available email templates."""
        # Import and register user templates
        from app.emails.templates.user.verification_email import VerificationEmailTemplate
        from app.emails.templates.user.password_reset import PasswordResetEmailTemplate
        from app.emails.templates.user.account_reactivation import AccountReactivationEmailTemplate
        
        # Import and register organizer templates
        from app.emails.templates.organizer.booking_reminder import BookingReminderTemplate
        from app.emails.templates.organizer.event_update import EventUpdateTemplate
        from app.emails.templates.organizer.thank_you import ThankYouTemplate
        from app.emails.templates.organizer.event_cancellation import EventCancellationTemplate
        from app.emails.templates.organizer.venue_change import VenueChangeTemplate
        from app.emails.templates.organizer.time_change import TimeChangeTemplate
        from app.emails.templates.organizer.co_organizer_invitation import CoOrganizerInvitationTemplate
        
        # Register user templates
        self.register(VerificationEmailTemplate())
        self.register(PasswordResetEmailTemplate())
        self.register(AccountReactivationEmailTemplate())
        
        # Register organizer templates
        self.register(BookingReminderTemplate())
        self.register(EventUpdateTemplate())
        self.register(ThankYouTemplate())
        self.register(EventCancellationTemplate())
        self.register(VenueChangeTemplate())
        self.register(TimeChangeTemplate())
        self.register(CoOrganizerInvitationTemplate())
    
    def register(self, template: EmailTemplate):
        """
        Register a template.
        
        Args:
            template: EmailTemplate instance to register
        """
        self.templates[template.id] = template
        logger.debug(f"Registered template: {template.id}")
    
    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template identifier
        
        Returns:
            EmailTemplate instance or None if not found
        """
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> Dict:
        """
        List all templates or filter by category.
        
        Args:
            category: Optional category filter ('user', 'organizer', 'admin')
        
        Returns:
            Dictionary of template metadata
        """
        if category:
            filtered = {
                tid: t.get_metadata() 
                for tid, t in self.templates.items() 
                if t.category == category
            }
            return filtered
        
        return {tid: t.get_metadata() for tid, t in self.templates.items()}
    
    def get_template_ids(self, category: Optional[str] = None) -> List[str]:
        """
        Get list of template IDs.
        
        Args:
            category: Optional category filter
        
        Returns:
            List of template IDs
        """
        if category:
            return [tid for tid, t in self.templates.items() if t.category == category]
        return list(self.templates.keys())