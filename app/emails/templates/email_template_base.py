#!/usr/bin/env python3
# app/emails/templates/email_template_base.py
"""Base email template class for MGLTickets."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class EmailTemplate(ABC):
    """
    Base class for all email templates.

    Each concrete subclass declares its required variables and the name of its
    Jinja2 HTML template file.  Rendering (Jinja2 + premailer CSS inlining) is
    handled centrally by EmailManager so individual templates stay thin.
    """

    id: str                        # e.g. 'user.verification'
    name: str                      # Human-readable label
    category: str                  # 'user' | 'organizer' | 'admin'
    description: str
    required_variables: List[str]  # Variables the caller must supply
    template_file: str             # Relative path under templates/, e.g. 'user/verification_email.html'

    @abstractmethod
    def get_subject(self, variables: Dict[str, str]) -> str:
        """Return the email subject line, optionally using variables."""
        pass

    # ------------------------------------------------------------------ #
    # Variable validation                                                  #
    # ------------------------------------------------------------------ #

    def validate_variables(self, variables: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Check that all required variables are present.

        Returns:
            (is_valid, missing_variable_names)
        """
        missing = [v for v in self.required_variables if v not in variables]
        return (len(missing) == 0, missing)

    # ------------------------------------------------------------------ #
    # Metadata                                                             #
    # ------------------------------------------------------------------ #

    def get_metadata(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "required_variables": self.required_variables,
            "template_file": self.template_file,
        }