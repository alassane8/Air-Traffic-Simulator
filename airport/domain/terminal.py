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

    def get_status(self) -> str:
        return self.status

    def is_full(self) -> bool:
        return self.planes_on_deck >= self.max_planes

    def available_capacity(self) -> int:
        return self.max_planes - self.planes_on_deck