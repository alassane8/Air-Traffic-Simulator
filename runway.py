# models/runway.py
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Runway:
    id: str
    length: float
    heading: int
    status: str  # "FREE" | "OCCUPIED" | "CLOSED" | "MAINTENANCE"
    current_aircraft: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)