# models/terminal.py
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class TerminalStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    MAINTENANCE = "MAINTENANCE"

@dataclass
class Terminal:
    id: str
    terminal_code: str
    airport_id: str  # référence à Airport.id
    max_planes: int
    planes_on_deck: int
    status: TerminalStatus
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)