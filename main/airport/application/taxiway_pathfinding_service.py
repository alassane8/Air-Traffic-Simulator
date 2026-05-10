import heapq
from math import sqrt, radians, sin, cos, atan2
from typing import Protocol


class Locatable(Protocol):
    id: str
    lat: float
    lon: float

    def is_open(self) -> bool: ...


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    φ1, φ2 = radians(lat1), radians(lat2)
    Δφ, Δλ = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(Δφ / 2) ** 2 + cos(φ1) * cos(φ2) * sin(Δλ / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def build_adjacency(nodes: dict[str, Locatable], edges: dict) -> dict:
    graph = {node_id: [] for node_id in nodes}

    for edge in edges.values():
        f, t, d = edge.from_node_id, edge.to_node_id, edge.distance_m
        if not nodes[f].is_open() or not nodes[t].is_open():
            continue
        graph[f].append((t, d))
        graph[t].append((f, d))

    return graph


def find_path_graph(
    nodes: dict[str, Locatable],
    edges: dict,
    start_id: str,
    goal_id: str,
) -> list[str]:
    goal = nodes[goal_id]

    def h(node_id: str) -> float:
        n = nodes[node_id]
        return haversine(n.lat, n.lon, goal.lat, goal.lon)

    graph = build_adjacency(nodes, edges)

    open_heap = [(h(start_id), 0.0, start_id, None)]
    came_from: dict[str, str | None] = {}
    g_score: dict[str, float] = {start_id: 0.0}

    while open_heap:
        f, g, current, parent = heapq.heappop(open_heap)

        if current in came_from:
            continue
        came_from[current] = parent

        if current == goal_id:
            path, node = [], goal_id
            while node is not None:
                path.append(node)
                node = came_from[node]
            return path[::-1]

        for neighbor_id, dist in graph[current]:
            tentative_g = g + dist
            if tentative_g < g_score.get(neighbor_id, float("inf")):
                g_score[neighbor_id] = tentative_g
                heapq.heappush(
                    open_heap,
                    (tentative_g + h(neighbor_id), tentative_g, neighbor_id, current),
                )

    return []


def path_total_distance(path: list[str], nodes: dict, edges: dict) -> float:
    graph = build_adjacency(nodes, edges)
    total = 0.0
    for i in range(len(path) - 1):
        current, next_node = path[i], path[i + 1]
        for neighbor_id, dist in graph[current]:
            if neighbor_id == next_node:
                total += dist
                break
    return total
