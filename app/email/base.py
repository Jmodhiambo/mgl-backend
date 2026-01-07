#!/usr/bin/env python3
"""Base email class for MGLTickets."""

from abc import ABC ,abstractmethod
from typing import Dict, Optional

class BaseEmail(ABC):
    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        template_data: Optional[Dict] = None
    ) -> None:
        pass