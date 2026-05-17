"""
hud_overlay.py
──────────────
Draws the tactical HUD overlay:
  - top-right panel: project name, active flight count, tick, time_scale
  - bottom-left: coordinate readout under mouse cursor
  - top-left: system status / version tag
  - animated corner brackets (engineering aesthetic)
"""

import math
import pygame
from datetime import datetime

# ── Palette ──────────────────────────────────────────────────────
HUD_AMBER    = (  0, 200, 255, 230)
HUD_DIM      = (  0, 120, 180, 160)
HUD_RED      = (255,  50,  50, 200)
HUD_WHITE    = (200, 240, 255, 220)
HUD_BG       = (  0,   0,   0, 160)
BRACKET_COL  = (  0, 200, 255, 180)
HUD_YELLOW   = (  0, 240, 255, 220)
HUD_GREY     = ( 80, 160, 180, 180)

MARGIN       = 18
LINE_H       = 17
PANEL_W      = 260
PANEL_H_EST  = 160


class HUDOverlayRenderer:
    """
    Draws static + dynamic HUD elements each frame.

    Call update() each frame, then draw(surface).
    """

    def __init__(self, width: int, height: int,
                 sim_name: str = "AIR TRAFFIC SIMULATOR",
                 version: str  = "v1.0"):
        self.w        = width
        self.h        = height
        self.sim_name = sim_name
        self.version  = version

        # Live data (caller updates these)
        self.active_flights   = 0
        self.inactive_flights = 0   # TAXI, BOARDING, PLANNED, LINEUP
        self.parked_flights   = 0   # PARKED
        self.tick_count       = 0
        self.time_scale       = 60
        self.mouse_lon        = 0.0
        self.mouse_lat        = 0.0

        self._t = 0.0          # animation time (s)

        pygame.font.init()
        self._font_title  = None
        self._font_main   = None
        self._font_small  = None
        self._font_tiny   = None
        self._ensure_fonts()

    def _ensure_fonts(self):
        for name in ["couriernew", "courier", "liberationmono", "dejavusansmono",
                     "ubuntumono", "monospace"]:
            try:
                self._font_title = pygame.font.SysFont(name, 16, bold=True)
                self._font_main  = pygame.font.SysFont(name, 13, bold=True)
                self._font_small = pygame.font.SysFont(name, 12)
                self._font_tiny  = pygame.font.SysFont(name, 10)
                return
            except Exception:
                pass
        self._font_title = pygame.font.Font(None, 20)
        self._font_main  = pygame.font.Font(None, 16)
        self._font_small = pygame.font.Font(None, 14)
        self._font_tiny  = pygame.font.Font(None, 12)

    # ── Helpers ───────────────────────────────────────────────────

    def _text(self, surface, text, font, color, x, y):
        surf = font.render(text, True, color)
        surface.blit(surf, (x, y))
        return surf.get_height()

    def _bracket_rect(self, surface, rect: pygame.Rect,
                      color=BRACKET_COL, size: int = 10, thick: int = 1):
        """Draw corner brackets around a rect."""
        x, y, w, h = rect
        segs = [
            # TL
            ((x, y), (x + size, y)),
            ((x, y), (x, y + size)),
            # TR
            ((x + w - size, y), (x + w, y)),
            ((x + w, y), (x + w, y + size)),
            # BL
            ((x, y + h - size), (x, y + h)),
            ((x, y + h), (x + size, y + h)),
            # BR
            ((x + w - size, y + h), (x + w, y + h)),
            ((x + w, y + h - size), (x + w, y + h)),
        ]
        for a, b in segs:
            pygame.draw.line(surface, color, a, b, thick)

    # ── Top-right status panel ────────────────────────────────────

    def _draw_status_panel(self, surface: pygame.Surface):
        total = self.active_flights + self.inactive_flights + self.parked_flights
        lines = [
            ("PROJECT", None),
            (self.sim_name, "title"),
            ("", None),
            # ── Flight counts ──────────────────────────────────────
            (f"TOTAL FLIGHTS    {total:>4}", "total"),
            ("", None),
            (f"  AIRBORNE       {self.active_flights:>4}", "active"),
            (f"  ON GROUND      {self.inactive_flights:>4}", "inactive"),
            (f"  PARKED         {self.parked_flights:>4}", "parked"),
            ("", None),
            # ── Sim info ───────────────────────────────────────────
            (f"SIM TICK         {self.tick_count:>7}", "data"),
            (f"TIME SCALE       {self.time_scale:>4}x", "data"),
            ("", None),
            (datetime.now().strftime("UTC  %H:%M:%S"), "time"),
        ]

        # Measure panel height
        ph = MARGIN
        for line, kind in lines:
            if kind == "title":
                ph += LINE_H + 4
            else:
                ph += LINE_H
        ph += MARGIN

        px = self.w - PANEL_W - MARGIN
        py = MARGIN

        # Background rect
        bg = pygame.Surface((PANEL_W, ph), pygame.SRCALPHA)
        bg.fill(HUD_BG)
        surface.blit(bg, (px, py))

        # Bracket decoration
        self._bracket_rect(surface, pygame.Rect(px, py, PANEL_W, ph), size=12, thick=1)

        # Render lines
        cursor_y = py + MARGIN
        for text, kind in lines:
            if not text:
                cursor_y += LINE_H // 2
                continue
            if kind == "title":
                self._text(surface, text, self._font_title, HUD_AMBER, px + MARGIN, cursor_y)
                cursor_y += LINE_H + 4
                # underline
                pygame.draw.line(surface, (*HUD_DIM[:3], 120),
                                 (px + MARGIN, cursor_y),
                                 (px + PANEL_W - MARGIN, cursor_y), 1)
            elif kind == "total":
                self._text(surface, text, self._font_main, HUD_AMBER, px + MARGIN, cursor_y)
                cursor_y += LINE_H
            elif kind == "active":
                self._text(surface, text, self._font_main, HUD_WHITE, px + MARGIN, cursor_y)
                cursor_y += LINE_H
            elif kind == "inactive":
                self._text(surface, text, self._font_main, HUD_YELLOW, px + MARGIN, cursor_y)
                cursor_y += LINE_H
            elif kind == "parked":
                self._text(surface, text, self._font_main, HUD_GREY, px + MARGIN, cursor_y)
                cursor_y += LINE_H
            elif kind == "data":
                self._text(surface, text, self._font_main, HUD_AMBER, px + MARGIN, cursor_y)
                cursor_y += LINE_H
            elif kind == "time":
                self._text(surface, text, self._font_small, HUD_DIM, px + MARGIN, cursor_y)
                cursor_y += LINE_H
            else:
                # section header (small)
                self._text(surface, text, self._font_tiny, HUD_DIM, px + MARGIN, cursor_y)
                cursor_y += LINE_H

    # ── Top-left version tag ──────────────────────────────────────

    def _draw_version_tag(self, surface: pygame.Surface):
        tag_lines = [
            f"AIR TRAFFIC SIMULATOR  {self.version}",
            "ATC SIMULATION SYSTEM",
            "GNC / TRAJECTORY MODULE",
        ]
        cursor_y = MARGIN
        for i, line in enumerate(tag_lines):
            color = HUD_AMBER if i == 0 else HUD_DIM
            font  = self._font_main if i == 0 else self._font_tiny
            self._text(surface, line, font, color, MARGIN, cursor_y)
            cursor_y += LINE_H if i == 0 else 14

    # ── Bottom-left coordinate readout ────────────────────────────

    def _draw_coord_readout(self, surface: pygame.Surface):
        lat_s = f"{abs(self.mouse_lat):.4f}{'N' if self.mouse_lat >= 0 else 'S'}"
        lon_s = f"{abs(self.mouse_lon):.4f}{'E' if self.mouse_lon >= 0 else 'W'}"
        text  = f"CURSOR  {lat_s}  {lon_s}"
        self._text(surface, text, self._font_tiny, HUD_DIM,
                   MARGIN, self.h - MARGIN - 12)

    # ── Animated corner marks on screen edges ─────────────────────

    def _draw_screen_corners(self, surface: pygame.Surface):
        """Subtle corner brackets for the full screen."""
        pulse = 0.5 + 0.5 * math.sin(self._t * 1.5)
        alpha = int(80 + 60 * pulse)
        color = (*BRACKET_COL[:3], alpha)
        size  = 20
        w, h  = self.w, self.h
        segs  = [
            ((0, 0), (size, 0)), ((0, 0), (0, size)),
            ((w - size, 0), (w, 0)), ((w, 0), (w, size)),
            ((0, h - size), (0, h)), ((0, h), (size, h)),
            ((w - size, h), (w, h)), ((w, h - size), (w, h)),
        ]
        # draw on a temp surface for alpha
        tmp = pygame.Surface((w, h), pygame.SRCALPHA)
        for a, b in segs:
            pygame.draw.line(tmp, color, a, b, 2)
        surface.blit(tmp, (0, 0))

    # ── Public API ────────────────────────────────────────────────

    def update(self, elapsed_ms: float, active_flights: int = 0,
               inactive_flights: int = 0, parked_flights: int = 0,
               tick_count: int = 0, time_scale: int = 60,
               mouse_lon: float = 0.0, mouse_lat: float = 0.0):
        self._t              += elapsed_ms / 1000.0
        self.active_flights   = active_flights
        self.inactive_flights = inactive_flights
        self.parked_flights   = parked_flights
        self.tick_count       = tick_count
        self.time_scale       = time_scale
        self.mouse_lon        = mouse_lon
        self.mouse_lat        = mouse_lat

    def draw(self, surface: pygame.Surface):
        self._draw_screen_corners(surface)
        self._draw_version_tag(surface)
        self._draw_status_panel(surface)
        self._draw_coord_readout(surface)