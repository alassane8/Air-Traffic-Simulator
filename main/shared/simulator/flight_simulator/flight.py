from datetime import datetime, timedelta
import math

from airport.application.runway_assignment_service import assign_arrival_runway
from flight.application.flight_physics_service import (
    compute_v_stall,
    get_distance_km,
    has_reached_destination,
    update_position,
    update_flight_fuel,
)
from flight.application.flight_service import advance_status
from flight.domain.flight import FlightStatus
from airport.application.taxiway_pathfinding_service import find_path_graph, haversine
from air_corridor.domain.simple_edge import SimpleEdge
from waypoint.domain.waypoint_status import WaypointStatus
from shared.simulator.landing_simulator.descent import _do_start_descent


def _compute_rho(altitude_m: float) -> float:
    """Densité de l'air (kg/m³) via modèle ISA standard."""
    return 1.225 * max(0.0, (1 - 2.2558e-5 * altitude_m)) ** 4.2561


def _target_altitude_m(waypoint) -> float:
    """Altitude cible (m) = milieu de la plage min/max du waypoint (en ft → m)."""
    return (waypoint.min_alt_ft + waypoint.max_alt_ft) / 2 * 0.3048


def _update_altitude_toward(flight, target_alt_m: float, aircraft, tick_interval: float) -> None:
    """
    Ajuste progressivement l'altitude du vol vers target_alt_m.
    Utilise base_rate_of_climb_ft_per_min converti en m/s.
    """
    rate_m_s = aircraft.base_rate_of_climb_ft_per_min * 0.00508
    delta = target_alt_m - flight.altitude_m
    max_change = rate_m_s * tick_interval
    if abs(delta) <= max_change:
        flight.altitude_m = target_alt_m
    else:
        flight.altitude_m += math.copysign(max_change, delta)


def _update_v_stall(flight, aircraft) -> None:
    """Recalcule v_stall en fonction de l'altitude courante."""
    rho = _compute_rho(flight.altitude_m)
    v_stall = compute_v_stall(flight.fuel_kg, rho, aircraft.wing_area_m2, flight.CL_max) * 3.6
    v_cruise_min = v_stall * 1.3
    if aircraft.cruising_speed >= v_cruise_min:
        flight.speed_km_h = aircraft.cruising_speed
    else:
        flight.speed_km_h = v_cruise_min

def _get_corridor_waypoints(flight, air_corridors: dict):
    """Retourne la liste des waypoints du corridor de ce vol.
    Si le vol parcourt le corridor en sens inverse (reverse_corridor=True),
    les waypoints sont retournés dans l'ordre inverse."""
    corridor = next(
        (c for c in air_corridors.values() if c.air_corridor_code == flight.corridor_code),
        None,
    )
    if corridor:
        waypoints = corridor.waypoints
        if getattr(flight, 'reverse_corridor', False):
            return list(reversed(waypoints))
        return waypoints
    return []

def check_corridor_waypoints_and_reroute(flight, air_corridors: dict, all_waypoints: dict):
    """
    Vérifie le statut des waypoints du corridor du vol.
    Si un waypoint est CLOSED, appelle find_path_graph pour recalculer le chemin
    parmi tous les waypoints OPEN disponibles.

    Returns:
        list: waypoints originaux si tous ouverts, sinon le nouveau chemin calculé par A*
    """
    waypoints = _get_corridor_waypoints(flight, air_corridors)

    if not waypoints:
        return []

    closed_waypoints = [wp for wp in waypoints if wp.status == WaypointStatus.CLOSED]

    if not closed_waypoints:
        return waypoints

    start_id = waypoints[0].id
    goal_id = waypoints[-1].id

    open_waypoints_nodes = {
        wp_id: wp
        for wp_id, wp in all_waypoints.items()
        if wp.status == WaypointStatus.OPEN
    }

    open_waypoints_nodes[start_id] = waypoints[0]
    open_waypoints_nodes[goal_id] = waypoints[-1]

    edges = _build_proximity_edges(open_waypoints_nodes, k=5)

    new_path_ids = find_path_graph(
        nodes=open_waypoints_nodes,
        edges=edges,
        start_id=start_id,
        goal_id=goal_id,
    )

    if not new_path_ids:
        return waypoints

    return [all_waypoints[wp_id] for wp_id in new_path_ids if wp_id in all_waypoints]

def _build_proximity_edges(nodes: dict, k: int = 5) -> dict:
    """
    Construit des edges entre chaque noeud et ses k voisins les plus proches.
    Utilisé quand il n'y a pas d'edges explicites entre waypoints.
    """
    edges = {}
    node_list = list(nodes.items())
    edge_id = 0

    for i, (node_id, node) in enumerate(node_list):
        distances = []
        for other_id, other_node in node_list:
            if other_id == node_id:
                continue
            dist = haversine(node.lat, node.lon, other_node.lat, other_node.lon)
            distances.append((dist, other_id))

        distances.sort()
        for dist, neighbor_id in distances[:k]:
            edges[edge_id] = SimpleEdge(
                from_node_id=node_id,
                to_node_id=neighbor_id,
                distance_m=dist,
            )
            edge_id += 1

    return edges

def _advance_to_next_waypoint(flight, waypoints, airports) -> bool:
    flight.current_waypoint_index += 1

    if flight.current_waypoint_index < len(waypoints):
        wp = waypoints[flight.current_waypoint_index]
        flight.dest_lat = wp.lat
        flight.dest_lon = wp.lon

        distance_km = get_distance_km(flight)
        speed_km_s = flight.speed_km_h / 3600
        if speed_km_s > 0:
            seconds_left = distance_km / speed_km_s
            flight.estimated_arrival_time = datetime.now() + timedelta(seconds=seconds_left)

        return False
    else:
        arrival_airport = airports.get(flight.arrival_airport_code)
        if arrival_airport:
            flight.dest_lat = arrival_airport.lat
            flight.dest_lon = arrival_airport.lon

            distance_km = get_distance_km(flight)
            speed_km_s = flight.speed_km_h / 3600
            if speed_km_s > 0:
                seconds_left = distance_km / speed_km_s
                flight.estimated_arrival_time = datetime.now() + timedelta(seconds=seconds_left)

        flight.current_waypoint_index = len(waypoints)
        return False

def _tick_flight(
    active_flights: list,
    tick_interval: float,
    time_scale: float,
    sim_tick: float,
    air_corridors: dict,
    airports: dict,
    aircrafts: dict,
    all_waypoints: dict
):
    for flight in list(active_flights):
        aircraft = aircrafts.get(flight.aircraft_id)
        update_flight_fuel(flight, tick_interval)

        if flight.status == FlightStatus.CLIMBING:
            rho = _compute_rho(flight.altitude_m)
            v_stall = compute_v_stall(flight.fuel_kg, rho, aircraft.wing_area_m2, flight.CL_max) * 3.6
            flight.speed_km_h = v_stall

            waypoints = _get_corridor_waypoints(flight, air_corridors)
            if waypoints:
                target_alt = _target_altitude_m(waypoints[0])
                _update_altitude_toward(flight, target_alt, aircraft, tick_interval)

            flight.time_spent += tick_interval
            if flight.time_spent >= FlightStatus.CLIMBING.duration_seconds:
                advance_status(flight)
                flight.time_spent = 0
                
                flight.active_waypoints = check_corridor_waypoints_and_reroute(
                    flight, air_corridors, all_waypoints,
                )
                v_cruise_min = v_stall * 1.3
                flight.speed_km_h = (
                    aircraft.cruising_speed
                    if aircraft.cruising_speed >= v_cruise_min
                    else v_cruise_min
                )

            assign_arrival_runway(flight, airports)

        elif flight.status == FlightStatus.CRUISE:
            flight.time_spent += sim_tick

            _update_v_stall(flight, aircraft)

            update_position(flight, sim_tick)

            waypoints = getattr(flight, 'active_waypoints', None) \
                        or _get_corridor_waypoints(flight, air_corridors)
            n_wp = len(waypoints)

            if has_reached_destination(flight):
                if flight.current_waypoint_index < n_wp:
                    _advance_to_next_waypoint(flight, waypoints, airports)

                    if flight.current_waypoint_index < n_wp:
                        target_alt = _target_altitude_m(waypoints[flight.current_waypoint_index])
                        _update_altitude_toward(flight, target_alt, aircraft, sim_tick)
                else:
                    arrival_airport = airports.get(flight.arrival_airport_code)
                    if arrival_airport:
                        flight.dest_lat = arrival_airport.lat
                        flight.dest_lon = arrival_airport.lon
                    _do_start_descent(flight, air_corridors, aircrafts)
            else:
                distance_restante = get_distance_km(flight)
                speed_km_s = flight.speed_km_h / 3600
                
                if speed_km_s > 0:
                    seconds_left = (distance_restante / speed_km_s) / time_scale
                    flight.estimated_arrival_time = datetime.now() + timedelta(seconds=seconds_left)

                if flight.current_waypoint_index < n_wp:
                    target_alt = _target_altitude_m(waypoints[flight.current_waypoint_index])
                    _update_altitude_toward(flight, target_alt, aircraft, sim_tick)

        elif flight.status == FlightStatus.DESCENDING:
            flight.time_spent += tick_interval

            if aircraft:
                _update_altitude_toward(flight, 0.0, aircraft, tick_interval)
                update_position(flight, sim_tick)

            if flight.time_spent >= FlightStatus.DESCENDING.duration_seconds:
                advance_status(flight)
                flight.time_spent = 0