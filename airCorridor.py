from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from aircraft import Aircraft


@dataclass
class AirCorridor:
    id: str
    air_corridor_code: str
    from_airport: str
    to_airport: str
    flight_time: datetime = field(default_factory=datetime.now)  
    minimum_time_separation: datetime = field(default_factory=datetime.now)
    aircrafts: List[Aircraft] = field(default_factory=list)
    altitude: str
    distance:str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
