import sys
import time


def log(message: str):
    for char in message:
        sys.stdout.write(char)
        sys.stdout.flush()
    print()


def phase(title: str):
    print()
    log(f"[INIT] :: {title}")


def success(message: str):
    log(f"[OK] :: {message}")


def loading(message: str, duration: float = 1, width: int = 30):
    log(f"[LOADING] :: {message}")
    steps = width
    for i in range(steps + 1):
        filled = "█" * i
        empty = "░" * (steps - i)
        percent = int((i / steps) * 100)
        sys.stdout.write(f"\r   [{filled}{empty}] {percent}%")
        sys.stdout.flush()
        time.sleep(duration / steps)
    print()


def log_runways(runways: dict):
    for runway in runways.values():
        print(f"\n{'='*60}")
        print(f"RUNWAY: {runway.id}")
        print(f"{'='*60}")

        if not runway.scheduled_flights:
            print("  Aucun vol schedulé")
            continue

        for flight in runway.scheduled_flights:
            print(f"\n  ✈ {flight.flight_code}")
            print(f"    Time Spent      : {flight.time_spent}")
            print(f"    Priorité        : {flight.priority.label}")
            print(f"    Status          : {flight.status.label}")
            print(f"    Usage Runway    : {flight.runway_usage.label}")
            print(f"    Départ airport  : {flight.depart_airport_id}")
            print(f"    LAT             : {flight.lat}")
            print(f"    LON             : {flight.lon}")
            print(f"    dest lat        : {flight.dest_lat}")
            print(f"    dest lon        : {flight.dest_lon}")
            print(f"    EST. départ     : {flight.estimated_departure_time}")
            print(f"    EST. arrivée    : {flight.estimated_arrival_time}")
            print(f"    Corridor        : {flight.corridor_code}")
            print(f"    {'─'*40}")

    total = sum(len(r.scheduled_flights) for r in runways.values())
    departures = sum(
        1
        for r in runways.values()
        for f in r.scheduled_flights
        if f.runway_usage.value == "DEPARTURE"
    )
    arrivals = sum(
        1
        for r in runways.values()
        for f in r.scheduled_flights
        if f.runway_usage.value == "ARRIVAL"
    )

    print(f"\nTotal entrées runways : {total}")
    print(f"Départs              : {departures}")
    print(f"Arrivées             : {arrivals}")
