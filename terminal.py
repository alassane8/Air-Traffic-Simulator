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
    airport_id: str
    max_planes: int
    planes_on_deck: int
    status: TerminalStatus
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def is_open(self) -> bool:
        return self.status == TerminalStatus.OPEN

    def is_full(self) -> bool:
        return self.planes_on_deck >= self.max_planes

    def has_capacity(self) -> bool:
        return self.planes_on_deck < self.max_planes

    def available_slots(self) -> int:
        return max(0, self.max_planes - self.planes_on_deck)

    def can_accept_plane(self) -> bool:
        return self.is_open() and self.has_capacity()

    def add_plane(self, count: int = 1) -> bool:
        if self.planes_on_deck + count > self.max_planes:
            return False
        self.planes_on_deck += count
        self.updated_at = datetime.now()
        return True

    def remove_plane(self, count: int = 1) -> bool:
        if self.planes_on_deck - count < 0:
            return False
        self.planes_on_deck -= count
        self.updated_at = datetime.now()
        return True

    def set_status(self, status: TerminalStatus):
        self.status = status
        self.updated_at = datetime.now()