"""
flight_info_panel.py
────────────────────
Panel d'information détaillé sur un vol sélectionné (clic sur la carte).

Affiche en temps réel :
  - Identité : code vol, compagnie, appareil
  - Itinéraire : départ → arrivée (aéroports, terminaux, gates, pistes)
  - Navigation : lat/lon, cap, altitude (ft + m), vitesse (kt + km/h)
  - Physique : fuel restant, burn rate, autonomie restante
  - Timing : départ estimé, arrivée estimée, time_spent
  - Statut : badge coloré + waypoint courant
  - Corridor aérien
  - Priorité

Style : panneau demi-transparent calé en bas à droite, brackets HUD.
"""

import math
import pygame
from datetime import datetime
from flight.domain.enums.flight_status import FlightStatus

# ── Palette ──────────────────────────────────────────────────────
HUD_BG        = (  0,   0,   0, 185)
HUD_AMBER     = (  0, 200, 255, 235)
HUD_DIM       = (  0, 100, 160, 180)
HUD_WHITE     = (200, 240, 255, 200)
HUD_GREEN     = ( 80, 220,  80, 220)
HUD_RED       = (255,  60,  60, 220)
HUD_BLUE      = (  0, 200, 255, 220)
HUD_ORANGE    = (  0, 160, 220, 220)
BRACKET_COL   = (  0, 200, 255, 180)

STATUS_COLORS = {
    FlightStatus.CLIMBING:   ( 80, 220, 120),
    FlightStatus.CRUISE:     (  0, 200, 255),
    FlightStatus.DESCENDING: (  0, 160, 220),
}

PANEL_W  = 320
MARGIN   = 14
LINE_H   = 16
GAP      = 6


class FlightInfoPanelRenderer:
    """
    Affiche le panel de détail d'un vol sélectionné.

    Usage :
        panel = FlightInfoPanelRenderer(screen_w, screen_h)
        panel.set_flight(flight_obj, airlines_dict, aircrafts_dict)   # au clic
        panel.clear()                                                   # désélection
        # chaque frame :
        panel.update(elapsed_ms, flight_obj)
        panel.draw(surface)
    """

    def __init__(self, screen_w: int, screen_h: int):
        self._w = screen_w
        self._h = screen_h
        self._flight = None
        self._airlines: dict = {}
        self._aircrafts: dict = {}
        self._t = 0.0

        self._font_title  = None
        self._font_main   = None
        self._font_small  = None
        self._font_tiny   = None
        self._fonts_ready = False

    # ── Fonts ─────────────────────────────────────────────────────

    def _ensure_fonts(self):
        if self._fonts_ready:
            return
        pygame.font.init()
        for name in ["couriernew", "courier", "liberationmono", "dejavusansmono", "monospace"]:
            try:
                self._font_title = pygame.font.SysFont(name, 15, bold=True)
                self._font_main  = pygame.font.SysFont(name, 13, bold=True)
                self._font_small = pygame.font.SysFont(name, 12)
                self._font_tiny  = pygame.font.SysFont(name, 10)
                self._fonts_ready = True
                return
            except Exception:
                pass
        self._font_title = pygame.font.Font(None, 18)
        self._font_main  = pygame.font.Font(None, 15)
        self._font_small = pygame.font.Font(None, 14)
        self._font_tiny  = pygame.font.Font(None, 12)
        self._fonts_ready = True

    # ── Public API ────────────────────────────────────────────────

    def set_flight(self, flight, airlines: dict = None, aircrafts: dict = None):
        self._flight   = flight
        self._airlines  = airlines  or {}
        self._aircrafts = aircrafts or {}

    def clear(self):
        self._flight = None

    def update(self, elapsed_ms: float, flight=None):
        self._t += elapsed_ms / 1000.0
        if flight is not None:
            self._flight = flight

    # ── Draw ──────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        if self._flight is None:
            return
        self._ensure_fonts()
        self._draw_panel(surface, self._flight)

    def _draw_panel(self, surface: pygame.Surface, flight):
        lines = self._build_lines(flight)

        # Calcul hauteur
        ph = MARGIN
        for line in lines:
            if line is None:
                ph += GAP
            elif line[0] == "TITLE":
                ph += LINE_H + 4
            else:
                ph += LINE_H
        ph += MARGIN

        px = self._w - PANEL_W - 18
        py = self._h - ph - 18

        # Background
        bg = pygame.Surface((PANEL_W, ph), pygame.SRCALPHA)
        bg.fill(HUD_BG)
        surface.blit(bg, (px, py))

        # Brackets
        self._bracket_rect(surface, pygame.Rect(px, py, PANEL_W, ph))

        # Ligne de fermeture (indice visuel)
        close_surf = self._font_tiny.render("[ ESC / CLICK TO DISMISS ]", True, HUD_DIM)
        surface.blit(close_surf, (px + PANEL_W - close_surf.get_width() - 8,
                                   py + ph - close_surf.get_height() - 5))

        # Contenu
        cy = py + MARGIN
        for line in lines:
            if line is None:
                cy += GAP
                continue
            kind = line[0]

            if kind == "TITLE":
                _, text, color = line
                surf = self._font_title.render(text, True, color)
                surface.blit(surf, (px + MARGIN, cy))
                cy += LINE_H + 4
                # Underline
                pygame.draw.line(surface, (*HUD_DIM[:3], 100),
                                 (px + MARGIN, cy - 2),
                                 (px + PANEL_W - MARGIN, cy - 2), 1)

            elif kind == "SECTION":
                _, text = line
                surf = self._font_tiny.render(text, True, HUD_DIM)
                surface.blit(surf, (px + MARGIN, cy))
                cy += LINE_H

            elif kind == "ROW":
                _, label, value, value_color = line
                lsurf = self._font_small.render(label, True, HUD_DIM)
                vsurf = self._font_main.render(str(value), True, value_color)
                surface.blit(lsurf, (px + MARGIN, cy))
                surface.blit(vsurf, (px + PANEL_W - MARGIN - vsurf.get_width(), cy))
                cy += LINE_H

            elif kind == "BADGE":
                _, text, bg_color = line
                badge_w = self._font_main.size(text)[0] + 10
                badge_surf = pygame.Surface((badge_w, LINE_H), pygame.SRCALPHA)
                badge_surf.fill((*bg_color, 60))
                pygame.draw.rect(badge_surf, (*bg_color, 200),
                                 badge_surf.get_rect(), 1)
                btext = self._font_main.render(text, True, (*bg_color, 230))
                badge_surf.blit(btext, (5, 1))
                surface.blit(badge_surf, (px + MARGIN, cy))
                cy += LINE_H

    def _build_lines(self, flight) -> list:
        """Construit la liste des lignes à afficher."""
        status = flight.flight_status
        status_color = STATUS_COLORS.get(status, (220, 220, 220))

        airline = self._airlines.get(flight.airline_id)
        aircraft = self._aircrafts.get(flight.aircraft_id)
        airline_name  = getattr(airline,  "name",    flight.airline_id)
        aircraft_type = getattr(aircraft, "model",   flight.aircraft_id)
        aircraft_reg  = getattr(aircraft, "registration", "—")

        # Fuel
        if flight.fuel_burn_rate_kg_per_s > 0:
            autonomy_s = flight.fuel_kg / flight.fuel_burn_rate_kg_per_s
            autonomy_min = int(autonomy_s / 60)
            fuel_color = HUD_RED if flight.is_fuel_critical else HUD_GREEN
        else:
            autonomy_min = 0
            fuel_color = HUD_DIM

        # Altitude
        alt_ft = int(flight.altitude_m * 3.28084)
        fl     = alt_ft // 100

        # Speed
        speed_kt = int(flight.speed_km_h / 1.852)

        # Heading
        hdg = int(flight.heading) % 360

        # Times
        dep_str = _fmt_time(flight.departure_time)
        arr_str = _fmt_time(flight.estimated_arrival_time)
        eta_str = _fmt_time(flight.estimated_arrival_time)

        lines = [
            # ── Header ──────────────────────────────────────────
            ("TITLE", f" {flight.flight_code}  ─  {airline_name}", HUD_AMBER),
            ("BADGE", f" {status.label} ", status_color),
            None,

            # ── Identité ────────────────────────────────────────
            ("SECTION", "── AIRCRAFT"),
            ("ROW", "TYPE",         aircraft_type,    HUD_WHITE),
            ("ROW", "REG",          aircraft_reg,     HUD_WHITE),
            ("ROW", "PRIORITY",     flight.priority.name, HUD_AMBER),
            None,

            # ── Route ───────────────────────────────────────────
            ("SECTION", "── ROUTE"),
            ("ROW", "FROM",         flight.depart_airport_id,   HUD_BLUE),
            ("ROW", "TERMINAL",     flight.depart_terminal_code, HUD_DIM[:3] + (200,)),
            ("ROW", "GATE",         flight.depart_gate_code,    HUD_WHITE),
            ("ROW", "RUNWAY DEP",   flight.depart_runway_code,  HUD_WHITE),
            ("ROW", "TO",           flight.arrival_airport_code, HUD_ORANGE),
            ("ROW", "TERMINAL",     flight.arrival_terminal_code, HUD_DIM[:3] + (200,)),
            ("ROW", "GATE",         flight.arrival_gate_code,   HUD_WHITE),
            ("ROW", "RUNWAY ARR",   flight.arrival_runway_code, HUD_WHITE),
            ("ROW", "CORRIDOR",     flight.corridor_code,       HUD_DIM[:3] + (200,)),
            None,

            # ── Navigation ──────────────────────────────────────
            ("SECTION", "── NAVIGATION"),
            ("ROW", "LAT",          f"{flight.lat:+.4f}°",       HUD_WHITE),
            ("ROW", "LON",          f"{flight.lon:+.4f}°",       HUD_WHITE),
            ("ROW", "ALTITUDE",     f"FL{fl:03d}  ({alt_ft} ft)", HUD_WHITE),
            ("ROW", "ALT (m)",      f"{int(flight.altitude_m)} m", HUD_DIM[:3] + (180,)),
            ("ROW", "HEADING",      f"{hdg:03d}°",                HUD_WHITE),
            ("ROW", "SPEED",        f"{speed_kt} kt  ({int(flight.speed_km_h)} km/h)", HUD_WHITE),
            None,

            # ── Fuel ────────────────────────────────────────────
            ("SECTION", "── FUEL"),
            ("ROW", "ON BOARD",     f"{int(flight.fuel_kg)} kg",   fuel_color),
            ("ROW", "BURN RATE",    f"{flight.fuel_burn_rate_kg_per_s:.2f} kg/s", HUD_DIM[:3] + (200,)),
            ("ROW", "AUTONOMY",     f"{autonomy_min} min",          fuel_color),
            None,

            # ── Timing ──────────────────────────────────────────
            ("SECTION", "── TIMING"),
            ("ROW", "DEPARTED",     dep_str,  HUD_DIM[:3] + (200,)),
            ("ROW", "ETA",          eta_str,  HUD_AMBER),
            ("ROW", "WPT INDEX",    str(flight.current_waypoint_index), HUD_WHITE),
        ]
        return lines

    # ── Helpers ───────────────────────────────────────────────────

    def _bracket_rect(self, surface: pygame.Surface, rect: pygame.Rect,
                      color=BRACKET_COL, size: int = 12, thick: int = 1):
        x, y, w, h = rect
        segs = [
            ((x, y), (x + size, y)),           ((x, y), (x, y + size)),
            ((x + w - size, y), (x + w, y)),   ((x + w, y), (x + w, y + size)),
            ((x, y + h - size), (x, y + h)),   ((x, y + h), (x + size, y + h)),
            ((x + w - size, y + h), (x + w, y + h)), ((x + w, y + h - size), (x + w, y + h)),
        ]
        for a, b in segs:
            pygame.draw.line(surface, color, a, b, thick)


def _fmt_time(dt) -> str:
    if dt is None:
        return "—"
    try:
        return dt.strftime("%H:%M:%S")
    except Exception:
        return "—"
