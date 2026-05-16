"""
flight_layer.py
───────────────
Dessine les vols en cours sur la carte radar :
  - Icône avion (triangle orienté selon le cap)
  - Trail de trajet parcouru
  - Code vol (IATA)
  - Indicateur de statut coloré (CLIMBING / CRUISE / DESCENDING)
  - Sélection au clic → renvoie le vol cliqué

Seuls les vols en status CLIMBING, CRUISE ou DESCENDING sont affichés.
"""

import math
import pygame
from flight.domain.enums.flight_status import FlightStatus
from shared.adapter.visualizer.renderer.world_map import geo_to_screen

# ── Palette ──────────────────────────────────────────────────────
COLOR_CLIMBING   = (80,  220, 120, 230)   # vert clair
COLOR_CRUISE     = (80,  180, 255, 230)   # bleu ciel
COLOR_DESCENDING = (255, 180,  60, 230)   # ambre-orange
COLOR_SELECTED   = (255, 255, 100, 255)   # jaune vif
COLOR_TRAIL      = (100, 200, 255, 120)   # trace de vol
COLOR_FUEL_WARN  = (255,  50,  50, 220)   # rouge si fuel critique

AIRCRAFT_SIZE  = 7     # demi-taille du triangle avion (px)
LABEL_OFFSET_X = 10
LABEL_OFFSET_Y = -8
HIT_RADIUS     = 14    # px pour détecter le clic


def _status_color(status: FlightStatus, fuel_critical: bool) -> tuple:
    if fuel_critical:
        return COLOR_FUEL_WARN
    if status == FlightStatus.CLIMBING:
        return COLOR_CLIMBING
    if status == FlightStatus.DESCENDING:
        return COLOR_DESCENDING
    return COLOR_CRUISE


def _draw_aircraft_icon(surface: pygame.Surface, px: int, py: int,
                        heading: float, color: tuple, selected: bool, size: int = AIRCRAFT_SIZE):
    """Dessine un triangle orienté selon le cap (heading en degrés, 0=Nord)."""
    # heading 0 = nord = haut de l'écran → angle pygame = -90°
    angle_rad = math.radians(heading - 90)

    def rot(dx, dy):
        x = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
        y = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
        return int(px + x), int(py + y)

    # Nez, aile gauche, queue, aile droite
    nose  = rot(0,         -size * 1.6)
    wingL = rot(-size,      size * 0.6)
    tail  = rot(0,          size * 0.4)
    wingR = rot( size,      size * 0.6)

    pts = [nose, wingL, tail, wingR]

    if selected:
        # Halo de sélection
        halo = pygame.Surface((size * 6, size * 6), pygame.SRCALPHA)
        hc = size * 3
        pygame.draw.circle(halo, (*COLOR_SELECTED[:3], 50), (hc, hc), size * 2 + 2)
        pygame.draw.circle(halo, (*COLOR_SELECTED[:3], 120), (hc, hc), size * 2 + 2, 1)
        surface.blit(halo, (px - hc, py - hc))

    pygame.draw.polygon(surface, color, pts)
    # contour légèrement plus clair
    pygame.draw.polygon(surface, (*color[:3], min(255, color[3] + 50) if len(color) > 3 else 255), pts, 1)


class FlightMarker:
    """État et rendu d'un seul vol sur la carte."""

    def __init__(self, flight, map_w: int, map_h: int):
        self.flight_id = flight.id
        self._map_w = map_w
        self._map_h = map_h
        self.selected = False

        # Trail de positions
        self._trail: list[tuple[int, int]] = []
        self._trail_max = 30

        self._blink_t = 0.0

    def update(self, flight, elapsed_ms: float):
        """Met à jour la position et le trail depuis les données du vol."""
        px, py = geo_to_screen(flight.lon, flight.lat, self._map_w, self._map_h)
        if not self._trail or self._trail[-1] != (px, py):
            self._trail.append((px, py))
            if len(self._trail) > self._trail_max:
                self._trail.pop(0)
        self._blink_t = (self._blink_t + elapsed_ms / 1000.0 * 2.0) % 1.0

    def draw(self, surface: pygame.Surface, flight,
             font_small: pygame.font.Font, font_tiny: pygame.font.Font):
        px, py = geo_to_screen(flight.lon, flight.lat, self._map_w, self._map_h)

        color = _status_color(flight.flight_status, flight.is_fuel_critical)
        if self.selected:
            color = COLOR_SELECTED

        # ── Trail ───────────────────────────────────────────────
        if len(self._trail) >= 2:
            n = len(self._trail)
            for i in range(1, n):
                if _crosses_antimeridian(self._trail[i - 1], self._trail[i], self._map_w):
                    continue
                alpha = int(130 * i / n)
                pygame.draw.line(
                    surface,
                    (*COLOR_TRAIL[:3], alpha),
                    self._trail[i - 1],
                    self._trail[i],
                    1,
                )

        # ── Icône avion ─────────────────────────────────────────
        _draw_aircraft_icon(surface, px, py, flight.heading, color, self.selected)

        # ── Label vol ───────────────────────────────────────────
        lx = px + LABEL_OFFSET_X
        ly = py + LABEL_OFFSET_Y

        # Code vol
        label_surf = font_small.render(flight.flight_code, True, color)
        surface.blit(label_surf, (lx, ly))

        # Statut en dessous
        alt_ft = int(flight.altitude_m * 3.28084 / 100)  # flight level
        status_line = f"FL{alt_ft:03d}  {int(flight.speed_km_h)}kt"
        status_surf = font_tiny.render(status_line, True,
                                       (*color[:3], 160) if not self.selected else COLOR_SELECTED)
        surface.blit(status_surf, (lx, ly + label_surf.get_height() + 1))

        # Alerte fuel
        if flight.is_fuel_critical:
            warn_visible = self._blink_t < 0.5
            if warn_visible:
                warn_surf = font_tiny.render("⚠ FUEL", True, COLOR_FUEL_WARN)
                surface.blit(warn_surf, (lx, ly + label_surf.get_height() + 12))

    def hit_test(self, flight, mx: int, my: int) -> bool:
        px, py = geo_to_screen(flight.lon, flight.lat, self._map_w, self._map_h)
        return math.hypot(mx - px, my - py) <= HIT_RADIUS


# ── Helpers ───────────────────────────────────────────────────────

def _crosses_antimeridian(start: tuple, end: tuple, map_w: int) -> bool:
    """True si le segment traverse l'antiméridien (saut horizontal > moitié écran)."""
    return abs(end[0] - start[0]) > map_w * 0.5


def _draw_dashed_line(surface, color, start, end, dash=8, gap=4, map_w: int = 1400):
    """Ligne pointillée entre deux points. Ignorée si elle traverse l'antiméridien."""
    if _crosses_antimeridian(start, end, map_w):
        return
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    drawing = True
    while pos < length:
        seg_end = min(pos + (dash if drawing else gap), length)
        if drawing:
            x0 = int(start[0] + ux * pos)
            y0 = int(start[1] + uy * pos)
            x1 = int(start[0] + ux * seg_end)
            y1 = int(start[1] + uy * seg_end)
            pygame.draw.line(surface, color, (x0, y0), (x1, y1), 1)
        pos = seg_end
        drawing = not drawing


# ── Renderer principal ────────────────────────────────────────────

AIRBORNE_STATUSES = {FlightStatus.CLIMBING, FlightStatus.CRUISE, FlightStatus.DESCENDING}


class FlightLayerRenderer:
    """
    Gère et dessine tous les marqueurs de vols en vol.

    Usage :
        layer = FlightLayerRenderer(map_w, map_h)
        # chaque frame :
        layer.update(elapsed_ms, active_flights)
        layer.draw(surface, active_flights)
        # au clic souris :
        clicked_flight = layer.handle_click(mx, my, active_flights)
    """

    def __init__(self, map_w: int, map_h: int):
        self._map_w = map_w
        self._map_h = map_h
        self._markers: dict[str, FlightMarker] = {}
        self._selected_id: str | None = None

        self._font_small: pygame.font.Font | None = None
        self._font_tiny:  pygame.font.Font | None = None

    def _ensure_fonts(self):
        if self._font_small is not None:
            return
        pygame.font.init()
        for name in ["couriernew", "courier", "liberationmono", "dejavusansmono", "monospace"]:
            try:
                self._font_small = pygame.font.SysFont(name, 12, bold=True)
                self._font_tiny  = pygame.font.SysFont(name, 10)
                return
            except Exception:
                pass
        self._font_small = pygame.font.Font(None, 14)
        self._font_tiny  = pygame.font.Font(None, 12)

    def _airborne_flights(self, active_flights: list) -> list:
        return [f for f in active_flights if f.flight_status in AIRBORNE_STATUSES]

    def update(self, elapsed_ms: float, active_flights: list):
        airborne = self._airborne_flights(active_flights)
        current_ids = {f.id for f in airborne}

        # Supprimer les marqueurs de vols atterris / disparus
        for fid in list(self._markers.keys()):
            if fid not in current_ids:
                del self._markers[fid]

        # Mettre à jour / créer les marqueurs
        for flight in airborne:
            if flight.id not in self._markers:
                self._markers[flight.id] = FlightMarker(flight, self._map_w, self._map_h)
            marker = self._markers[flight.id]
            marker.selected = (flight.id == self._selected_id)
            marker.update(flight, elapsed_ms)

    def draw(self, surface: pygame.Surface, active_flights: list):
        self._ensure_fonts()
        airborne = self._airborne_flights(active_flights)

        # flight dict pour accès rapide
        flight_map = {f.id: f for f in airborne}

        # Dessiner les non-sélectionnés d'abord, sélectionné en dernier (par-dessus)
        for fid, marker in self._markers.items():
            if fid != self._selected_id and fid in flight_map:
                marker.draw(surface, flight_map[fid], self._font_small, self._font_tiny)

        if self._selected_id and self._selected_id in self._markers and self._selected_id in flight_map:
            self._markers[self._selected_id].draw(
                surface, flight_map[self._selected_id],
                self._font_small, self._font_tiny
            )

    def handle_click(self, mx: int, my: int, active_flights: list):
        """
        Détecte si un clic (mx, my) touche un vol affiché.
        Retourne le vol cliqué, ou None.
        Met à jour la sélection.
        """
        airborne = self._airborne_flights(active_flights)
        flight_map = {f.id: f for f in airborne}

        # Chercher le vol le plus proche dans le rayon de hit
        best_flight = None
        best_dist = float("inf")

        for fid, marker in self._markers.items():
            if fid not in flight_map:
                continue
            flight = flight_map[fid]
            px, py = geo_to_screen(flight.lon, flight.lat, self._map_w, self._map_h)
            dist = math.hypot(mx - px, my - py)
            if dist <= HIT_RADIUS and dist < best_dist:
                best_dist = dist
                best_flight = flight

        if best_flight:
            self._selected_id = best_flight.id
        else:
            self._selected_id = None

        return best_flight

    def deselect(self):
        self._selected_id = None

    @property
    def selected_id(self) -> str | None:
        return self._selected_id