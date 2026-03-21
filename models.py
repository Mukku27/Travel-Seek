"""
models.py

Pydantic models for user preferences and session data.
"""

from pydantic import BaseModel, Field
from typing import Optional


class UserPreferences(BaseModel):
    """Extracted and persisted user travel preferences."""
    destination: Optional[str] = None
    num_days: Optional[int] = None
    budget_tier: Optional[str] = None
    travel_style: Optional[list[str]] = Field(default_factory=list)
    group_size: Optional[int] = None
    special_requirements: Optional[list[str]] = Field(default_factory=list)
    home_currency: Optional[str] = None

    def summary(self) -> str:
        """Return a human-readable summary of current preferences."""
        parts = []
        if self.destination:
            parts.append(f"Destination: {self.destination}")
        if self.num_days:
            parts.append(f"Days: {self.num_days}")
        if self.budget_tier:
            parts.append(f"Budget: {self.budget_tier}")
        if self.travel_style:
            parts.append(f"Style: {', '.join(self.travel_style)}")
        if self.group_size:
            parts.append(f"Group size: {self.group_size}")
        if self.special_requirements:
            parts.append(f"Requirements: {', '.join(self.special_requirements)}")
        if self.home_currency:
            parts.append(f"Currency: {self.home_currency}")
        return "\n".join(parts) if parts else "No preferences set yet."

    def update_from(self, other: "UserPreferences") -> None:
        """Merge non-None fields from another preferences object."""
        for field_name in type(self).model_fields:
            new_val = getattr(other, field_name)
            if new_val is not None and new_val != [] and new_val != "":
                setattr(self, field_name, new_val)
