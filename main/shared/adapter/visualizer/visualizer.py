"""
visualizer.py
─────────────
Entry-point for the AeroSim radar-style visualizer.

Run standalone:
    cd AeroSim/main
    python shared/adapter/visualizer/visualizer.py

Or import and drive from the simulator:
    from shared.adapter.visualizer.visualizer import Visualizer
    vis = Visualizer(airports_data)
    while running:
        vis.update(elapsed_ms, active_flights=n, tick=t)
        vis.draw()
        vis.tick()
"""

import os
import sys
import json
import math

# Make sure project root is on path when run standalone
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pygame

from shared.adapter.visualizer.renderer.world_map       import WorldMapRenderer
from shared.adapter.visualizer.renderer.airport_layer   import AirportLayerRenderer
from shared.adapter.visualizer.renderer.hud_overlay     import HUDOverlayRenderer
from shared.adapter.visualizer.renderer.flight_layer    import FlightLayerRenderer
from shared.adapter.visualizer.renderer.flight_info_panel import FlightInfoPanelRenderer

# ── Config ────────────────────────────────────────────────────────
WIDTH      = 1400
HEIGHT     = 800
FPS_TARGET = 60
WINDOW_TITLE = "AEROSIM  //  ATC RADAR  //  GNC MODULE"


class Visualizer:
    """
    Self-contained pygame visualizer.

    Lifecycle:
        vis = Visualizer.from_config_path("main/config/airports.json")
        vis.run()          # blocking loop (standalone mode)

        # or non-blocking (embedded in sim loop):
        while sim_running:
            events = vis.handle_events()
            if not events:
                break
            vis.update(elapsed_ms, active_flights, tick, time_scale,
                       flights=active_flights_list,
                       airlines=airlines_dict, aircrafts=aircrafts_dict)
            vis.draw()
            vis.tick()
    """

    # ── Constructor ───────────────────────────────────────────────

    def __init__(self, airports_data: dict,
                 width: int = WIDTH, height: int = HEIGHT):
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        self._screen  = pygame.display.set_mode((width, height))
        self._clock   = pygame.time.Clock()
        self._running = True

        self._w = width
        self._h = height

        # Renderers
        self._world_map   = WorldMapRenderer(width, height)
        self._airports    = AirportLayerRenderer(airports_data, width, height)
        self._hud         = HUDOverlayRenderer(width, height)
        self._flights_layer = FlightLayerRenderer(width, height)
        self._flight_panel  = FlightInfoPanelRenderer(width, height)

        # Live flight data (injected each frame via update())
        self._active_flights: list = []
        self._airlines:  dict = {}
        self._aircrafts: dict = {}

        # Reverse geo lookup: pixel → lon/lat (for mouse coord display)
        self._last_mouse_lon = 0.0
        self._last_mouse_lat = 0.0

    # ── Factory ───────────────────────────────────────────────────

    @classmethod
    def from_config_path(cls, airports_json_path: str, **kwargs) -> "Visualizer":
        with open(airports_json_path, "r") as f:
            airports_data = json.load(f)
        return cls(airports_data, **kwargs)

    # ── Geo helpers ───────────────────────────────────────────────

    def _pixel_to_geo(self, px: int, py: int) -> tuple[float, float]:
        """Approximate Mercator inverse: pixel → (lon, lat)."""
        lon = (px / self._w) * 360.0 - 180.0

        # inverse Mercator for lat
        norm_y  = py / self._h   # 0 = top, 1 = bottom
        MAX_MERC = math.log(math.tan(math.pi / 4 + math.radians(85.0) / 2))
        merc    = (1.0 - norm_y) * 2 * MAX_MERC - MAX_MERC
        lat     = math.degrees(2 * math.atan(math.exp(merc)) - math.pi / 2)
        return lon, lat

    # ── Public API ────────────────────────────────────────────────

    def handle_events(self) -> bool:
        """Process pygame events. Returns False if user requested quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False
                if event.key == pygame.K_ESCAPE:
                    # ESC : désélectionner le vol, ne pas quitter
                    self._flights_layer.deselect()
                    self._flight_panel.clear()
            if event.type == pygame.MOUSEMOTION:
                mx, my = pygame.mouse.get_pos()
                lon, lat = self._pixel_to_geo(mx, my)
                self._last_mouse_lon = lon
                self._last_mouse_lat = lat
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                clicked = self._flights_layer.handle_click(mx, my, self._active_flights)
                if clicked:
                    self._flight_panel.set_flight(clicked, self._airlines, self._aircrafts)
                else:
                    self._flight_panel.clear()
        return True

    def update(self, elapsed_ms: float,
               active_flights: int = 0,
               tick_count:     int = 0,
               time_scale:     int = 60,
               flights:        list = None,
               airlines:       dict = None,
               aircrafts:      dict = None):
        """Advance all animations. Pass flights list for live flight tracking."""
        # Stocker les données de vol pour handle_events (clic) et draw
        if flights is not None:
            self._active_flights = flights
        if airlines is not None:
            self._airlines = airlines
        if aircrafts is not None:
            self._aircrafts = aircrafts

        self._world_map.update(elapsed_ms)
        self._airports.update(elapsed_ms)
        self._flights_layer.update(elapsed_ms, self._active_flights)

        # Mettre à jour le panel si un vol est sélectionné
        selected_id = self._flights_layer.selected_id
        if selected_id:
            selected_flight = next((f for f in self._active_flights if f.id == selected_id), None)
            self._flight_panel.update(elapsed_ms, selected_flight)
        else:
            self._flight_panel.update(elapsed_ms)

        self._hud.update(
            elapsed_ms,
            active_flights = len(self._active_flights),
            tick_count     = tick_count,
            time_scale     = time_scale,
            mouse_lon      = self._last_mouse_lon,
            mouse_lat      = self._last_mouse_lat,
        )

    def draw(self):
        """Render one frame to the screen."""
        self._world_map.draw(self._screen)
        self._airports.draw(self._screen)
        self._flights_layer.draw(self._screen, self._active_flights)
        self._hud.draw(self._screen)
        self._flight_panel.draw(self._screen)
        pygame.display.flip()

    def tick(self):
        """Cap framerate."""
        self._clock.tick(FPS_TARGET)

    def trigger_airport_ping(self, airport_code: str):
        """Trigger a ripple ping on a specific airport (e.g. on departure)."""
        self._airports.trigger_ping(airport_code)

    def quit(self):
        pygame.quit()

    # ── Standalone blocking loop ───────────────────────────────────

    def run(self):
        """
        Blocking demo loop — shows the static map with animated radar sweep
        and airport markers. Used for standalone testing.
        """
        tick_count = 0
        last_time  = pygame.time.get_ticks()

        # Trigger startup pings staggered
        import time as _time
        airport_codes = []
        for layer in self._airports._markers:
            airport_codes.append(layer.code)

        ping_scheduled = {code: i * 600 for i, code in enumerate(airport_codes)}
        elapsed_total  = 0

        print(f"[AEROSIM] Visualizer running — {len(airport_codes)} airports loaded")
        print("[AEROSIM] Press ESC or Q to quit")

        while self._running:
            now        = pygame.time.get_ticks()
            elapsed_ms = now - last_time
            last_time  = now

            self._running = self.handle_events()

            # Staggered startup pings
            elapsed_total += elapsed_ms
            for code, delay in list(ping_scheduled.items()):
                if elapsed_total >= delay:
                    self.trigger_airport_ping(code)
                    del ping_scheduled[code]

            self.update(elapsed_ms, active_flights=0,
                        tick_count=tick_count, time_scale=60)
            self.draw()
            self.tick()
            tick_count += 1

        self.quit()


# ── Standalone entry point ────────────────────────────────────────

if __name__ == "__main__":
    # Resolve config path relative to project root
    config_dir = os.path.join(_ROOT, "main", "config")
    airports_path = os.path.join(config_dir, "airports.json")

    if not os.path.exists(airports_path):
        # Try relative to cwd
        airports_path = os.path.join("config", "airports.json")

    if not os.path.exists(airports_path):
        print(f"[ERROR] airports.json not found. Run from AeroSim/main/")
        sys.exit(1)

    vis = Visualizer.from_config_path(airports_path)
    vis.run()