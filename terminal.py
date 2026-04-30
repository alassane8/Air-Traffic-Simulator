# models/terminal.py
from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class Terminal:
    id: str
    terminal_code: str
    terminal_airport: str  # référence à Airport.id
    max_planes: int
    planes_on_deck: int
    status: str            # "OPEN" | "CLOSED" | "MAINTENANCE"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)