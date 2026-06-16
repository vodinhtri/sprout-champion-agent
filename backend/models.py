from pydantic import BaseModel
from typing import List, Optional


class UserPreferences(BaseModel):
    interests: List[str] = ["finance", "news", "tech"]
    name: Optional[str] = "User"


class TodoItem(BaseModel):
    id: str
    title: str
    description: str
    action: str
    rationale: str
    priority: str  # urgent | normal | info
    category: str  # finance | news | lifestyle | work | entertainment
    data_point: Optional[str] = None
