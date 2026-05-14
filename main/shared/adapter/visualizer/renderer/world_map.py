"""
world_map.py
────────────
Renders the radar-style world map background:
  - solid black background
  - subtle lat/lon grid (amber, low opacity)
  - animated radar sweep line
  - continental coastlines via geodatasets + geopandas (Natural Earth 110m)
  - CRT scanline overlay

Dépendances :
    pip install pygame geodatasets geopandas
"""

import math
import pygame
from shapely.geometry import MultiPolygon, Polygon

# ── Palette ──────────────────────────────────────────────────────
BG          = (0,   0,   0)
COAST       = (220, 100, 0,  180)
COAST_GLOW  = (255, 140, 0,   40)
SWEEP_COLOR = (255, 100, 0,   90)

_GEO_LINES: list | None = None   # cache: list of list of (x_norm, y_norm)


def _load_geo_lines() -> list:
    """
    Charge les polygones Natural Earth via geodatasets et les convertit
    en polylignes normalisées [0,1] prêtes pour la projection Mercator.
    Téléchargement unique (~400 KB), mis en cache par geodatasets.
    """
    global _GEO_LINES
    if _GEO_LINES is not None:
        return _GEO_LINES

    try:
        import geodatasets
        import geopandas as gpd
        world = gpd.read_file(geodatasets.get_path("naturalearth.land"))
    except Exception as e:
        print(f"[WorldMap] geodatasets indisponible ({e}), carte vide.")
        _GEO_LINES = []
        return _GEO_LINES

    lines = []

    def _extract(polygon: Polygon):
        """Extrait le contour extérieur d'un polygone en coords normalisées."""
        coords = list(polygon.exterior.coords)
        pts = []
        for lon, lat in coords:
            nx = (lon + 180.0) / 360.0
            ny = _lat_to_y_norm(lat)
            pts.append((nx, ny))
        if len(pts) >= 2:
            lines.append(pts)

    for geom in world.geometry:
        if geom is None:
            continue
        if geom.geom_type == "Polygon":
            _extract(geom)
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                _extract(poly)

    _GEO_LINES = lines
    print(f"[WorldMap] {len(lines)} polygones chargés depuis Natural Earth.")
    return _GEO_LINES


# ── Mercator projection ───────────────────────────────────────────

_MAX_MERC = math.log(math.tan(math.pi / 4 + math.radians(85.0) / 2))


def _lat_to_y_norm(lat: float) -> float:
    """Mercator: latitude → [0,1] (0 = pôle nord, 1 = pôle sud), clampé ±85°."""
    lat = max(-85.0, min(85.0, lat))
    merc = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return (1.0 - (merc + _MAX_MERC) / (2 * _MAX_MERC))


def geo_to_screen(lon: float, lat: float, w: int, h: int) -> tuple[int, int]:
    x = int((lon + 180.0) / 360.0 * w)
    y = int(_lat_to_y_norm(lat) * h)
    return x, y


# ── Renderer ─────────────────────────────────────────────────────

class WorldMapRenderer:
    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height

        self._bg_surf    = pygame.Surface((width, height), pygame.SRCALPHA)
        self._coast_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        self._grid_surf  = pygame.Surface((width, height), pygame.SRCALPHA)
        self._scan_surf  = pygame.Surface((width, height), pygame.SRCALPHA)

        self._sweep_angle = 0.0
        self._sweep_speed = 20.0    # degrés/seconde

        self._build_background()
        self._build_grid()
        self._build_coastlines()
        self._build_scanlines()

    def _build_background(self):
        self._bg_surf.fill(BG)
        border = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for i in range(30):
            a = int(80 * i / 30)
            pygame.draw.rect(border, (0, 0, 0, a),
                             (i, i, self.w - 2*i, self.h - 2*i), 1)
        self._bg_surf.blit(border, (0, 0))

    def _build_grid(self):
        self._grid_surf.fill((0, 0, 0, 0))
        dim    = (180, 80, 0, 28)
        bright = (220, 100, 0, 50)

        for lat in range(-60, 91, 30):
            y = int(_lat_to_y_norm(lat) * self.h)
            pygame.draw.line(self._grid_surf, dim, (0, y), (self.w, y), 1)

        for lon in range(-180, 181, 30):
            x = int((lon + 180) / 360 * self.w)
            pygame.draw.line(self._grid_surf, dim, (x, 0), (x, self.h), 1)

        eq_y = int(_lat_to_y_norm(0) * self.h)
        pygame.draw.line(self._grid_surf, bright, (0, eq_y), (self.w, eq_y), 1)
        pm_x = int(180 / 360 * self.w)
        pygame.draw.line(self._grid_surf, bright, (pm_x, 0), (pm_x, self.h), 1)

    def _build_coastlines(self):
        self._coast_surf.fill((0, 0, 0, 0))
        geo_lines = _load_geo_lines()

        for polyline in geo_lines:
            pts = [(int(nx * self.w), int(ny * self.h)) for nx, ny in polyline]
            if len(pts) < 2:
                continue
            pygame.draw.lines(self._coast_surf, COAST_GLOW, False, pts, 3)
            pygame.draw.lines(self._coast_surf, COAST,      False, pts, 1)

    def _build_scanlines(self):
        self._scan_surf.fill((0, 0, 0, 0))
        for y in range(0, self.h, 3):
            pygame.draw.line(self._scan_surf, (0, 0, 0, 40), (0, y), (self.w, y), 1)

    def _draw_sweep(self, target: pygame.Surface):
        sweep_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        cx, cy   = self.w // 2, self.h // 2
        max_r    = math.hypot(cx, cy) * 1.5
        angle_r  = math.radians(self._sweep_angle)
        wedge_w  = math.radians(22)

        for i in range(14):
            t       = i / 14
            a_start = angle_r - wedge_w * t
            a_end   = angle_r - wedge_w * (t + 1 / 14)
            alpha   = int(SWEEP_COLOR[3] * (1 - t) ** 1.8)
            pts = [(cx, cy),
                   (cx + max_r * math.cos(a_start), cy - max_r * math.sin(a_start)),
                   (cx + max_r * math.cos(a_end),   cy - max_r * math.sin(a_end))]
            pygame.draw.polygon(sweep_surf, (*SWEEP_COLOR[:3], alpha), pts)

        ex = cx + max_r * math.cos(angle_r)
        ey = cy - max_r * math.sin(angle_r)
        pygame.draw.line(sweep_surf, (255, 160, 20, 200), (cx, cy), (int(ex), int(ey)), 1)
        target.blit(sweep_surf, (0, 0))

    def update(self, elapsed_ms: float):
        self._sweep_angle = (self._sweep_angle + self._sweep_speed * elapsed_ms / 1000.0) % 360.0

    def draw(self, target: pygame.Surface):
        target.blit(self._bg_surf,    (0, 0))
        target.blit(self._grid_surf,  (0, 0))
        target.blit(self._coast_surf, (0, 0))
        target.blit(self._scan_surf,  (0, 0))

    def geo_to_screen(self, lon: float, lat: float) -> tuple[int, int]:
        return geo_to_screen(lon, lat, self.w, self.h)