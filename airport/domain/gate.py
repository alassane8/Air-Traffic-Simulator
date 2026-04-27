# models/gate.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Gate:
    id: str
    gate_code: str
    terminal: str  # référence à Terminal.id
    status: str    # "FREE" | "OCCUPIED" | "MAINTENANCE"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_terminal(self) -> str:
        return self.terminal

    def get_status(self) -> str:
        return self.status

    def is_available(self) -> bool:
        return self.status == "FREE"