"""
world_map.py
────────────
Renders the radar-style world map background:
  - solid black background
  - subtle lat/lon grid (amber, low opacity)
  - animated radar sweep line
  - continental coastlines via geodatasets + geopandas (Natural Earth 110m)
  - CRT scanline overlay
"""

import math
import pygame
from shapely.geometry import MultiPolygon, Polygon

# ── Palette ──────────────────────────────────────────────────────
BG          = (  6,  14,  20)
COAST       = (  0, 200, 255, 180)
COAST_GLOW  = (  0, 200, 255,  40)
SWEEP_COLOR = (  0, 160, 220,  90)

# Cache : liste de polylignes, chacune = liste de (lon, lat) en degrés
_GEO_LINES: list | None = None


def _load_geo_lines() -> list:
    """
    Charge les polygones Natural Earth et les stocke comme polylignes
    de (lon, lat) en degrés — format stable, indépendant de la projection.
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
        coords = list(polygon.exterior.coords)
        if len(coords) >= 2:
            # Stocker directement en (lon, lat) degrés
            lines.append([(lon, lat) for lon, lat in coords])

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
    return 1.0 - (merc + _MAX_MERC) / (2 * _MAX_MERC)


def geo_to_screen(lon: float, lat: float, w: int, h: int,
                  zoom: float = 1.0, pan_x: float = 0.0, pan_y: float = 0.0) -> tuple[int, int]:
    """Mercator lon/lat → pixel, avec support zoom & pan."""
    nx = (lon + 180.0) / 360.0
    ny = _lat_to_y_norm(lat)
    cx, cy = w / 2.0, h / 2.0
    x = int((nx * w - cx) * zoom + cx - pan_x)
    y = int((ny * h - cy) * zoom + cy - pan_y)
    return x, y


# ── Renderer ─────────────────────────────────────────────────────

class WorldMapRenderer:
    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height

        self._bg_surf   = pygame.Surface((width, height), pygame.SRCALPHA)
        self._scan_surf = pygame.Surface((width, height), pygame.SRCALPHA)

        # Surfaces pré-rendues pour zoom=1 (cas le plus fréquent)
        self._coast_surf_base = pygame.Surface((width, height), pygame.SRCALPHA)
        self._grid_surf_base  = pygame.Surface((width, height), pygame.SRCALPHA)

        self._sweep_angle = 0.0
        self._sweep_speed = 20.0  # degrés/seconde

        self._build_background()
        self._build_grid_base()
        self._build_coastlines_base()
        self._build_scanlines()

        # Pré-charger les lignes géo
        _load_geo_lines()

    def _build_background(self):
        self._bg_surf.fill(BG)
        border = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for i in range(30):
            a = int(80 * i / 30)
            pygame.draw.rect(border, (0, 0, 0, a),
                             (i, i, self.w - 2*i, self.h - 2*i), 1)
        self._bg_surf.blit(border, (0, 0))

    def _build_grid_base(self):
        """Grille sans zoom (zoom=1, pan=0)."""
        self._grid_surf_base.fill((0, 0, 0, 0))
        dim    = (180, 80, 0, 28)
        bright = (220, 100, 0, 50)
        for lat in range(-60, 91, 30):
            y = int(_lat_to_y_norm(lat) * self.h)
            pygame.draw.line(self._grid_surf_base, dim, (0, y), (self.w, y), 1)
        for lon in range(-180, 181, 30):
            x = int((lon + 180) / 360 * self.w)
            pygame.draw.line(self._grid_surf_base, dim, (x, 0), (x, self.h), 1)
        eq_y = int(_lat_to_y_norm(0) * self.h)
        pygame.draw.line(self._grid_surf_base, bright, (0, eq_y), (self.w, eq_y), 1)
        pm_x = int(180 / 360 * self.w)
        pygame.draw.line(self._grid_surf_base, bright, (pm_x, 0), (pm_x, self.h), 1)

    def _build_coastlines_base(self):
        """Côtes sans zoom (zoom=1, pan=0)."""
        self._coast_surf_base.fill((0, 0, 0, 0))
        geo_lines = _load_geo_lines()
        for polyline in geo_lines:
            pts = [
                (int((lon + 180.0) / 360.0 * self.w),
                 int(_lat_to_y_norm(lat) * self.h))
                for lon, lat in polyline
            ]
            if len(pts) < 2:
                continue
            pygame.draw.lines(self._coast_surf_base, COAST_GLOW, False, pts, 3)
            pygame.draw.lines(self._coast_surf_base, COAST,      False, pts, 1)

    def _build_scanlines(self):
        self._scan_surf.fill((0, 0, 0, 0))
        for y in range(0, self.h, 3):
            pygame.draw.line(self._scan_surf, (0, 0, 0, 40), (0, y), (self.w, y), 1)

    def _draw_grid_zoomed(self, target: pygame.Surface, zoom: float, pan_x: float, pan_y: float):
        surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        dim    = (180, 80, 0, 28)
        bright = (220, 100, 0, 50)
        for lat in range(-60, 91, 30):
            y = geo_to_screen(0, lat, self.w, self.h, zoom, pan_x, pan_y)[1]
            pygame.draw.line(surf, dim, (0, y), (self.w, y), 1)
        for lon in range(-180, 181, 30):
            x = geo_to_screen(lon, 0, self.w, self.h, zoom, pan_x, pan_y)[0]
            pygame.draw.line(surf, dim, (x, 0), (x, self.h), 1)
        eq_y = geo_to_screen(0, 0, self.w, self.h, zoom, pan_x, pan_y)[1]
        pygame.draw.line(surf, bright, (0, eq_y), (self.w, eq_y), 1)
        target.blit(surf, (0, 0))

    def _draw_coastlines_zoomed(self, target: pygame.Surface, zoom: float, pan_x: float, pan_y: float):
        """Dessine les côtes avec zoom/pan depuis les (lon,lat) stockés."""
        surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        geo_lines = _load_geo_lines()

        cx, cy = self.w / 2.0, self.h / 2.0
        # Pré-calculer les bornes visibles pour clipper (optimisation)
        margin = 50
        x_min, x_max = -margin, self.w + margin
        y_min, y_max = -margin, self.h + margin

        for polyline in geo_lines:
            pts = []
            for lon, lat in polyline:
                nx = (lon + 180.0) / 360.0
                ny = _lat_to_y_norm(lat)
                x = int((nx * self.w - cx) * zoom + cx - pan_x)
                y = int((ny * self.h - cy) * zoom + cy - pan_y)
                pts.append((x, y))

            if len(pts) < 2:
                continue

            # Clipper : ne dessiner que si au moins un point est visible
            if any(x_min <= x <= x_max and y_min <= y <= y_max for x, y in pts):
                pygame.draw.lines(surf, COAST_GLOW, False, pts, 3)
                pygame.draw.lines(surf, COAST,      False, pts, 1)

        target.blit(surf, (0, 0))

    def update(self, elapsed_ms: float):
        self._sweep_angle = (self._sweep_angle + self._sweep_speed * elapsed_ms / 1000.0) % 360.0

    def draw(self, target: pygame.Surface,
             zoom: float = 1.0, pan_x: float = 0.0, pan_y: float = 0.0):
        target.blit(self._bg_surf, (0, 0))

        if zoom == 1.0 and pan_x == 0.0 and pan_y == 0.0:
            # Cas sans zoom : utiliser les surfaces pré-rendues
            target.blit(self._grid_surf_base,  (0, 0))
            target.blit(self._coast_surf_base, (0, 0))
        else:
            # Zoom actif : recalculer depuis les (lon, lat) bruts
            self._draw_grid_zoomed(target, zoom, pan_x, pan_y)
            self._draw_coastlines_zoomed(target, zoom, pan_x, pan_y)

        target.blit(self._scan_surf, (0, 0))

    def geo_to_screen(self, lon: float, lat: float,
                      zoom: float = 1.0, pan_x: float = 0.0, pan_y: float = 0.0) -> tuple[int, int]:
        return geo_to_screen(lon, lat, self.w, self.h, zoom, pan_x, pan_y)