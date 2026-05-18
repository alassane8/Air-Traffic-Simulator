import math
import random

from air_corridor.domain.air_corridor import AirCorridor
from aircraft.domain.aircraft import Aircraft
from flight.domain.enums.flight_status import FlightStatus
from flight.domain.flight import Flight


def compute_flight_fuel(
    aircraft: Aircraft,
    flight: Flight,
    air_corridors: dict,
) -> tuple[float, float]:
    """
    Calcule le carburant total nécessaire (kg) et le fuel_burn_rate de
    croisière (kg/s) à partir des caractéristiques de l'appareil et du vol.

    Méthode :
    ---------
    1. Fuel des phases sol/transition (taxi, décollage, montée, descente,
       atterrissage) : consommation fixe (BASE_FUEL_FLOW × durée phase).

    2. Fuel croisière via la formule de Breguet Range (4 itérations pour
       converger, car la masse initiale dépend du fuel lui-même) :

           fuel_trip = W_initial × (1 - exp(-R × TSFC / (L/D × V)))

         où :
           R    = distance (m)
           TSFC = Thrust Specific Fuel Consumption ≈ 0.000018 kg/(N·s)
           L/D  = finesse aérodynamique (aircraft.ld_ratio)
           V    = vitesse croisière (m/s)

    3. total_fuel = (trip_fuel + phase_fuel) × (1 + 15 % réserve)
       plafonné à aircraft.max_fuel_kg.

    Retourne
    --------
    (total_fuel_kg, fuel_burn_rate_kg_per_s)
    """

    TSFC = 0.000018           # kg/(N·s)
    AVG_PAX_WEIGHT_KG = 95
    RESERVE_RATIO = 0.15      # réserve réglementaire ICAO
    CARGO_PAYLOAD_KG = 100_000

    # air_corridor: AirCorridor | None = air_corridors.get(flight.corridor_code)
    # if air_corridor is None:
    #     return aircraft.max_fuel_kg * 0.5, aircraft.BASE_FUEL_FLOW["cruise"]

    for air_corridor in air_corridors.values():
        if air_corridor.air_corridor_code == flight.corridor_code: 
            distance_m = float(air_corridor.distance) * 1_000

    if aircraft.is_cargo():
        payload_kg = CARGO_PAYLOAD_KG
    else:
        aircraft.load_passengers(random.randrange(aircraft.seats))
        payload_kg = aircraft.passengers * AVG_PAX_WEIGHT_KG

    phase_durations = {
        "lineup":   FlightStatus.LINEUP.duration_seconds,
        "takeoff":  FlightStatus.TAKEOFF.duration_seconds,
        "climb":    FlightStatus.CLIMBING.duration_seconds,
        "descent":  FlightStatus.DESCENDING.duration_seconds,
        "landing":  FlightStatus.LANDING.duration_seconds,
        "taxi":     FlightStatus.TAXI.duration_seconds,
    }
    phase_fuel_kg = sum(
        aircraft.BASE_FUEL_FLOW.get(phase, 0.0) * duration
        for phase, duration in phase_durations.items()
    )

    speed_m_s = aircraft.cruising_speed / 3.6
    oew = aircraft.operating_empty_weight_kg

    fuel_estimate_kg = 5_000.0
    for _ in range(4):
        w_initial_kg = oew + payload_kg + phase_fuel_kg + fuel_estimate_kg
        breguet_exp = (distance_m * TSFC) / (aircraft.ld_ratio * speed_m_s)
        trip_fuel_kg = w_initial_kg * (1 - math.exp(-breguet_exp))
        fuel_estimate_kg = trip_fuel_kg

    total_fuel_kg = min(
        (trip_fuel_kg + phase_fuel_kg) * (1 + RESERVE_RATIO),
        aircraft.max_fuel_kg,
    )

    fuel_burn_rate_kg_per_s = (
        aircraft.fuel_flow_cruise_kg_per_s
        if aircraft.fuel_flow_cruise_kg_per_s > 0
        else aircraft.BASE_FUEL_FLOW["cruise"]
    )

    return total_fuel_kg, fuel_burn_rate_kg_per_s