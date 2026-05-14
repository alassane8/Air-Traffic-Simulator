"""
airport_layer.py
────────────────
Draws airport markers on the map in radar/HUD style:
  - blinking square reticle  ■
  - IATA code label (monospace, amber)
  - coordinate readout below label
  - ping ripple animation on hover / on new flight
"""

import math
import pygame
from shared.adapter.visualizer.renderer.world_map import geo_to_screen

# ── Palette ──────────────────────────────────────────────────────
COLOR_MARKER   = (255,  60,  60, 255)   # red-hot square
COLOR_LABEL    = (255, 100,   0, 230)   # amber text
COLOR_COORDS   = (180,  60,   0, 160)   # dimmer for coord line
COLOR_RETICLE  = (255,  60,  60, 120)   # reticle cross arms
COLOR_PING     = (255,  80,  20, 200)   # ripple ring color

MARKER_SIZE    = 5     # half-size of the square marker (px)
LABEL_OFFSET_Y = 14    # px below marker centre


class AirportMarker:
    """State for one airport's animated marker."""

    def __init__(self, airport_code: str, lon: float, lat: float, px: int, py: int):
        self.code  = airport_code
        self.lon   = lon
        self.lat   = lat
        self.px    = px
        self.py    = py

        # Blink state
        self._blink_t     = 0.0
        self._blink_speed = 1.8    # Hz

        # Ping ripple (triggered externally)
        self._ping_r      = 0.0
        self._ping_alpha  = 0
        self._ping_active = False

    def trigger_ping(self):
        self._ping_r      = 0.0
        self._ping_alpha  = 255
        self._ping_active = True

    def update(self, elapsed_ms: float):
        dt = elapsed_ms / 1000.0
        self._blink_t = (self._blink_t + dt * self._blink_speed) % 1.0
        if self._ping_active:
            self._ping_r     += dt * 40       # px/s expansion
            self._ping_alpha -= int(dt * 400)
            if self._ping_alpha <= 0:
                self._ping_active = False
                self._ping_alpha  = 0

    def draw(self, surface: pygame.Surface, font_small: pygame.font.Font,
             font_tiny: pygame.font.Font):
        px, py = self.px, self.py

        # ── Ping ripple ────────────────────────────────────────────
        if self._ping_active and self._ping_r > 0:
            a     = max(0, min(255, self._ping_alpha))
            color = (*COLOR_PING[:3], a)
            ring  = pygame.Surface((int(self._ping_r * 2 + 4),) * 2, pygame.SRCALPHA)
            cx, cy = int(self._ping_r + 2), int(self._ping_r + 2)
            pygame.draw.circle(ring, color, (cx, cy), int(self._ping_r), 1)
            surface.blit(ring, (px - cx, py - cy))

        # ── Cross-hair reticle arms ────────────────────────────────
        arm = MARKER_SIZE + 6
        pygame.draw.line(surface, COLOR_RETICLE,
                         (px - arm, py), (px - MARKER_SIZE - 1, py), 1)
        pygame.draw.line(surface, COLOR_RETICLE,
                         (px + MARKER_SIZE + 1, py), (px + arm, py), 1)
        pygame.draw.line(surface, COLOR_RETICLE,
                         (px, py - arm), (px, py - MARKER_SIZE - 1), 1)
        pygame.draw.line(surface, COLOR_RETICLE,
                         (px, py + MARKER_SIZE + 1), (px, py + arm), 1)

        # ── Blinking square marker ─────────────────────────────────
        visible = self._blink_t < 0.85     # off for 15 % of cycle
        if visible:
            rect = pygame.Rect(px - MARKER_SIZE, py - MARKER_SIZE,
                               MARKER_SIZE * 2, MARKER_SIZE * 2)
            pygame.draw.rect(surface, COLOR_MARKER, rect)
            # inner bright core
            inner = pygame.Rect(px - 2, py - 2, 4, 4)
            pygame.draw.rect(surface, (255, 200, 200), inner)

        # ── IATA label ─────────────────────────────────────────────
        label_surf = font_small.render(self.code, True, COLOR_LABEL)
        lx = px + MARKER_SIZE + 6
        ly = py - label_surf.get_height() // 2
        surface.blit(label_surf, (lx, ly))

        # ── Coordinate line ────────────────────────────────────────
        lat_str = f"{abs(self.lat):.2f}{'N' if self.lat >= 0 else 'S'}"
        lon_str = f"{abs(self.lon):.2f}{'E' if self.lon >= 0 else 'W'}"
        coord_surf = font_tiny.render(f"{lat_str} {lon_str}", True, COLOR_COORDS)
        surface.blit(coord_surf, (lx, ly + label_surf.get_height() + 1))


class AirportLayerRenderer:
    """
    Manages and draws all airport markers.

    Usage:
        layer = AirportLayerRenderer(airports_data, map_w, map_h)
        # each frame:
        layer.update(elapsed_ms)
        layer.draw(surface)
    """

    def __init__(self, airports_data: dict, map_w: int, map_h: int):
        """
        airports_data: raw dict loaded from airports.json
                       {group_id: [{"airport_code", "lat", "lon", ...}, ...], ...}
        """
        self._markers: list[AirportMarker] = []
        self._font_small: pygame.font.Font | None = None
        self._font_tiny:  pygame.font.Font | None = None

        for group in airports_data.values():
            for apt in group:
                px, py = geo_to_screen(apt["lon"], apt["lat"], map_w, map_h)
                marker = AirportMarker(
                    airport_code=apt["airport_code"],
                    lon=apt["lon"],
                    lat=apt["lat"],
                    px=px,
                    py=py,
                )
                self._markers.append(marker)

        # Trigger a staggered ping on startup
        import random
        for i, m in enumerate(self._markers):
            m._blink_t = random.random()   # randomise blink phase

    def _ensure_fonts(self):
        if self._font_small is None:
            pygame.font.init()
            # Try to load a monospace font; fall back to default
            for name in ["couriernew", "courier", "liberationmono", "dejavusansmono"]:
                try:
                    self._font_small = pygame.font.SysFont(name, 13, bold=True)
                    self._font_tiny  = pygame.font.SysFont(name, 10)
                    break
                except Exception:
                    pass
            if self._font_small is None:
                self._font_small = pygame.font.Font(None, 16)
                self._font_tiny  = pygame.font.Font(None, 13)

    def trigger_ping(self, airport_code: str):
        """Call this when a flight departs or arrives at an airport."""
        for m in self._markers:
            if m.code == airport_code:
                m.trigger_ping()
                break

    def update(self, elapsed_ms: float):
        for m in self._markers:
            m.update(elapsed_ms)

    def draw(self, surface: pygame.Surface):
        self._ensure_fonts()
        for m in self._markers:
            m.draw(surface, self._font_small, self._font_tiny)