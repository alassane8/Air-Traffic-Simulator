from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class GateStatus(str, Enum):
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"


@dataclass
class Gate:
    id: str
    gate_code: str
    terminal: str  # référence à Terminal.id
    aircraft_id: Optional[str]
    status: GateStatus

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_free(self) -> bool:
        return self.status == GateStatus.FREE and self.aircraft_id is None

    def is_occupied(self) -> bool:
        return self.status == GateStatus.OCCUPIED

    def is_available(self) -> bool:
        return self.status == GateStatus.FREE

    def assign_aircraft(self, aircraft_id: str) -> bool:
        if not self.is_free():
            return False
        self.aircraft_id = aircraft_id
        self.status = GateStatus.OCCUPIED
        self.updated_at = datetime.now()
        return True

    def release_aircraft(self) -> None:
        self.aircraft_id = None
        if self.status != GateStatus.MAINTENANCE:
            self.status = GateStatus.FREE
        self.updated_at = datetime.now()

    def set_maintenance(self) -> None:
        self.status = GateStatus.MAINTENANCE
        self.aircraft_id = None
        self.updated_at = datetime.now()

    def set_status(self, status: GateStatus) -> None:
        self.status = status
        if status != GateStatus.OCCUPIED:
            self.aircraft_id = None
        self.updated_at = datetime.now()
