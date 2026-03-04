#!/usr/bin/env python3
"""Base email template class for MGLTickets."""

from dataclasses import dataclass
from typing import List, Dict, Optional
from abc import ABC, abstractmethod


@dataclass
class EmailTemplate(ABC):
    """Base class for all email templates."""
    
    id: str
    name: str
    category: str  # 'user', 'organizer', 'admin'
    description: str
    required_variables: List[str]
    
    @abstractmethod
    def get_subject(self, variables: Dict[str, str]) -> str:
        """Get email subject with variables replaced."""
        pass
    
    @abstractmethod
    def get_body(self, variables: Dict[str, str]) -> str:
        """Get email body with variables replaced."""
        pass
    
    def validate_variables(self, variables: Dict[str, str]) -> tuple[bool, List[str]]:
        """
        Validate that all required variables are present.
        
        Returns:
            tuple: (is_valid, missing_variables)
        """
        missing = [var for var in self.required_variables if var not in variables]
        return (len(missing) == 0, missing)
    
    def render_subject(self, variables: Dict[str, str]) -> str:
        """Render subject with variable replacement."""
        is_valid, missing = self.validate_variables(variables)
        if not is_valid:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")
        
        subject = self.get_subject(variables)
        return self._replace_variables(subject, variables)
    
    def render_body(self, variables: Dict[str, str]) -> str:
        """Render body with variable replacement."""
        is_valid, missing = self.validate_variables(variables)
        if not is_valid:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")
        
        body = self.get_body(variables)
        return self._replace_variables(body, variables)
    
    def _replace_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Replace {variable} placeholders with actual values."""
        result = text
        for key, value in variables.items():
            placeholder = f'{{{key}}}'
            result = result.replace(placeholder, str(value))
        return result
    
    def get_metadata(self) -> Dict:
        """Get template metadata."""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'required_variables': self.required_variables
        }