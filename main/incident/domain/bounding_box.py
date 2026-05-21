from dataclasses import dataclass


@dataclass 
class Zone:
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float

    def contains(self, lat: float, lon: float) -> bool:
        return self.lat_min <= lat <= self.lat_max and self.lon_min <= lon <= self.lon_max

    def overlaps(self, other: "Zone") -> bool:
        return not (
            self.lat_max < other.lat_min or self.lat_min > other.lat_max or
            self.lon_max < other.lon_min or self.lon_min > other.lon_max
        )