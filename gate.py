# models/gate.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
 
class GateStatus(str, Enum):
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"

@dataclass
class Gate:
    id: str
    gate_code: str
    terminal: str  # référence à Terminal.id
    aircraft_id: str
    status: GateStatus
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
