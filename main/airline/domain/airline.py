from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Airline:
    id: str
    name: str
    iata_code: str
    icao_code: str
    country: str

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def matches_iata(self, code: str) -> bool:
        return self.iata_code.upper() == code.upper()

    def matches_icao(self, code: str) -> bool:
        return self.icao_code.upper() == code.upper()

    def is_from_country(self, country: str) -> bool:
        return self.country.lower() == country.lower()

    def update_name(self, name: str) -> None:
        self.name = name
        self.updated_at = datetime.now()

    def update_codes(self, iata_code: str = None, icao_code: str = None) -> None:
        if iata_code:
            self.iata_code = iata_code
        if icao_code:
            self.icao_code = icao_code
        self.updated_at = datetime.now()
