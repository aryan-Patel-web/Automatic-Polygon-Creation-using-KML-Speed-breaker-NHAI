"""
polygon.py  v5  —  Speed Breaker CAP PTBM Polygon Engine
IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI Road Safety

GEOMETRY  (per MoRTH/NHAI spec):
  - Strip LENGTH  = lane_width   (ACROSS road, perpendicular to road heading)
  - Strip WIDTH   = strip_mm     (ALONG road, thin dimension = 10mm or 15mm)
  - All strips at one marker share SAME heading → perfectly parallel
  - Separator gap at centre → strips only within their lane

HEADING SOURCES (priority order):
  1. manual   — user sets road_heading_deg directly (most reliable)
  2. osm      — OpenStreetMap Overpass nearest road way
  3. pca      — principal axis of all markers (needs spread > 10m)
  4. neighbour— bearing between adjacent markers (least reliable)
"""

import math, json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import urllib.request, urllib.parse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ─── constants ───────────────────────────────────────────────────────────────
R_EARTH = 6_371_000.0


# ─── data classes ────────────────────────────────────────────────────────────

@dataclass
class MarkerInfo:
    index: int
    name: str
    lat: float
    lon: float
    description: str = ""
    placement_code: str = ""


@dataclass
class PolygonSpec:
    # Strip dimensions
    strip_width_mm: float        = 15.0   # thin dim along road (mm)
    num_strips: int              = 6      # total strips across all lanes
    gap_between_strips_m: float  = 0.10  # gap between strips (along road)
    # Road layout
    num_lanes: int               = 2
    road_width_m: float          = 7.0   # full carriageway width
    separator_width_m: float     = 0.5   # centre divider (0 = no divider)
    has_separator: bool          = True
    # Heading
    heading_override: float      = -1.0  # -1 = auto; 0–179 = forced


@dataclass
class GeneratedPolygon:
    marker: MarkerInfo
    coordinates: List[Tuple[float, float]]           # bounding hull
    heading_deg: float                               # road heading used
    road_curvature: str
    strip_polygons: List[List[Tuple[float, float]]]  # each strip closed ring
    lane_assignments: List[int]
    heading_source: str = "auto"
    spec: PolygonSpec = field(default_factory=PolygonSpec)


# ─── KML parsing ─────────────────────────────────────────────────────────────

def parse_kml_markers(kml_path: str) -> List[MarkerInfo]:
    tree = ET.parse(kml_path)
    root = tree.getroot()
    markers, idx = [], 1
    for pm in root.iter():
        if pm.tag.split('}')[-1] != 'Placemark':
            continue
        ne = _ch(pm, 'name')
        de = _ch(pm, 'description')
        name = (ne.text or '').strip() if ne is not None else f"Marker_{idx}"
        desc = (de.text or '').strip() if de is not None else ""
        coord = _pt(pm)
        if coord is None:
            continue
        lon, lat = coord
        code = name if any(k in name.upper()
                           for k in ['CAP','PTBM','MM','FM','SIGN','GO SLOW']) else ""
        markers.append(MarkerInfo(idx, name, lat, lon, desc, code))
        idx += 1
    return markers


def _ch(el, tag):
    for c in el:
        if c.tag.split('}')[-1] == tag:
            return c
    return None


def _pt(pm) -> Optional[Tuple[float, float]]:
    for el in pm.iter():
        if el.tag.split('}')[-1] == 'coordinates' and el.text:
            p = el.text.strip().split(',')
            if len(p) >= 2:
                try:
                    return float(p[0]), float(p[1])
                except ValueError:
                    pass
    return None


# ─── geodesic maths ──────────────────────────────────────────────────────────

def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin(math.radians(lat2 - lat1) / 2) ** 2 +
         math.cos(φ1) * math.cos(φ2) *
         math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * R_EARTH * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def forward_bearing(lat1, lon1, lat2, lon2) -> float:
    """Forward azimuth in [0, 360)."""
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dλ = math.radians(lon2 - lon1)
    x = math.sin(dλ) * math.cos(φ2)
    y = math.cos(φ1) * math.sin(φ2) - math.sin(φ1) * math.cos(φ2) * math.cos(dλ)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def offset_point(lat, lon, dist_m, hdg_deg) -> Tuple[float, float]:
    """Move (lat, lon) by dist_m in direction hdg_deg. Returns (lat, lon)."""
    if dist_m == 0:
        return lat, lon
    d = dist_m / R_EARTH
    h = math.radians(hdg_deg)
    φ1 = math.radians(lat)
    λ1 = math.radians(lon)
    φ2 = math.asin(math.sin(φ1) * math.cos(d) +
                   math.cos(φ1) * math.sin(d) * math.cos(h))
    λ2 = λ1 + math.atan2(math.sin(h) * math.sin(d) * math.cos(φ1),
                          math.cos(d) - math.sin(φ1) * math.sin(φ2))
    return math.degrees(φ2), math.degrees(λ2)


def normalise_heading(h: float) -> float:
    """Reduce to [0, 180) — road direction is bidirectional."""
    h = h % 360
    return h - 180 if h >= 180 else h


# ─── heading detection ────────────────────────────────────────────────────────

def _osm_heading(lat: float, lon: float, radius_m: int = 40) -> Optional[float]:
    """Query OSM Overpass for nearest road, return heading [0,180)."""
    q = (f'[out:json][timeout:8];'
         f'way(around:{radius_m},{lat:.6f},{lon:.6f})[highway];'
         f'out geom 8;')
    try:
        data = urllib.parse.urlencode({'data': q}).encode()
        req  = urllib.request.Request('https://overpass-api.de/api/interpreter', data)
        req.add_header('User-Agent', 'GIS-BOQ-v5')
        with urllib.request.urlopen(req, timeout=8) as r:
            ways = json.loads(r.read().decode()).get('elements', [])
        best_h, best_d = None, 1e9
        for way in ways:
            geom = way.get('geometry', [])
            for i in range(len(geom) - 1):
                n1, n2 = geom[i], geom[i + 1]
                ml = (n1['lat'] + n2['lat']) / 2
                mo = (n1['lon'] + n2['lon']) / 2
                d  = haversine_distance(lat, lon, ml, mo)
                if d < best_d:
                    best_d = d
                    b = forward_bearing(n1['lat'], n1['lon'], n2['lat'], n2['lon'])
                    best_h = normalise_heading(b)
        return best_h
    except Exception:
        return None


_osm_cache: Dict[Tuple[float, float], Optional[float]] = {}


def _osm_cached(lat, lon):
    key = (round(lat, 4), round(lon, 4))
    if key not in _osm_cache:
        _osm_cache[key] = _osm_heading(lat, lon)
    return _osm_cache[key]


def pca_heading(markers: List[MarkerInfo]) -> Optional[float]:
    """Principal axis through all markers. Returns [0,180) or None if spread < 10m."""
    if len(markers) < 2:
        return None
    lats = [m.lat for m in markers]
    lons = [m.lon for m in markers]
    clat, clon = sum(lats) / len(lats), sum(lons) / len(lons)
    slat = 111_320.0
    slon = 111_320.0 * math.cos(math.radians(clat))
    ys = [(la - clat) * slat for la in lats]
    xs = [(lo - clon) * slon for lo in lons]
    spread = math.sqrt((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2)
    if spread < 10.0:
        return None
    n  = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cxx = sum((x - mx) ** 2 for x in xs) / n
    cxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    cyy = sum((y - my) ** 2 for y in ys) / n
    tr   = cxx + cyy
    det  = cxx * cyy - cxy ** 2
    disc = math.sqrt(max(0.0, (tr / 2) ** 2 - det))
    lam  = tr / 2 + disc
    if abs(cxy) > 1e-12:
        vx, vy = lam - cyy, cxy
    elif cxx >= cyy:
        vx, vy = 1.0, 0.0
    else:
        vx, vy = 0.0, 1.0
    return normalise_heading((math.degrees(math.atan2(vx, vy)) + 360) % 360)


def _neighbour_heading(markers: List[MarkerInfo], idx: int) -> float:
    n   = len(markers)
    cur = markers[idx]
    ws = wc = tw = 0.0
    for off in range(-3, 4):
        if off == 0:
            continue
        j = idx + off
        if not 0 <= j < n:
            continue
        nb = markers[j]
        b  = forward_bearing(nb.lat, nb.lon, cur.lat, cur.lon) if off < 0 \
             else forward_bearing(cur.lat, cur.lon, nb.lat, nb.lon)
        nm = normalise_heading(b)
        w  = 1.0 / abs(off)
        ws += w * math.sin(math.radians(nm))
        wc += w * math.cos(math.radians(nm))
        tw += w
    if tw == 0:
        return 0.0
    return (math.degrees(math.atan2(ws / tw, wc / tw)) + 360) % 360


def resolve_heading(
    markers: List[MarkerInfo],
    idx: int,
    spec: PolygonSpec,
    pca_h: Optional[float],
    use_osm: bool = True,
) -> Tuple[float, str]:
    """Returns (heading [0,180), source_label)."""
    # 1. Manual override
    if 0 <= spec.heading_override < 180:
        return float(spec.heading_override), "manual"
    # 2. OSM
    if use_osm:
        h = _osm_cached(markers[idx].lat, markers[idx].lon)
        if h is not None:
            return h, "osm"
    # 3. PCA
    if pca_h is not None:
        return pca_h, "pca"
    # 4. Neighbour
    return _neighbour_heading(markers, idx), "neighbour"


def detect_curvature(markers: List[MarkerInfo], idx: int) -> str:
    n = len(markers)
    if idx == 0 or idx >= n - 1:
        return "straight"
    b_in  = forward_bearing(markers[idx-1].lat, markers[idx-1].lon,
                             markers[idx].lat,   markers[idx].lon)
    b_out = forward_bearing(markers[idx].lat,    markers[idx].lon,
                             markers[idx+1].lat,  markers[idx+1].lon)
    delta = abs(normalise_heading(b_in) - normalise_heading(b_out))
    delta = min(delta, 180 - delta)
    if delta < 5:   return "straight"
    if delta < 20:  return "slight_curve"
    return "sharp_curve"


# ─── strip rectangle builder ─────────────────────────────────────────────────
#
#  Road  ──────────────────────────────────────────────► heading H
#
#  ←──── lane_w ────→  ←sep→  ←──── lane_w ────→
#  ┌────────────────┐         ┌────────────────┐
#  │ ══════════════ │         │ ══════════════ │   strip 1 & 4
#  │ ══════════════ │         │ ══════════════ │   strip 2 & 5
#  │ ══════════════ │         │ ══════════════ │   strip 3 & 6
#  └────────────────┘         └────────────────┘
#
#  Each ═══ is:
#    long side  = lane_w  (across road, perpendicular to H)
#    short side = 15mm    (along road, parallel to H)
#
#  pa, pb = signed distances from road centre (+ = left of H, − = right)
#
# ─────────────────────────────────────────────────────────────────────────────

def make_strip(
    mk_lat: float, mk_lon: float,
    hdg: float,          # road heading [0,360)
    along_m: float,      # offset of strip centre along road from marker
    sw_m: float,         # strip width in metres (thin dimension, 0.015m)
    pa: float,           # near perpendicular edge (signed metres)
    pb: float,           # far  perpendicular edge (signed metres)
) -> List[Tuple[float, float]]:
    """
    Builds one strip rectangle.
    Returns closed ring [(lon, lat), ...] — 5 points.
    """
    h_fwd  = hdg
    h_bwd  = (hdg + 180) % 360
    h_left = (hdg - 90  + 360) % 360   # perpendicular left
    h_rgt  = (hdg + 90) % 360          # perpendicular right
    half   = sw_m / 2.0

    # Centre of strip on road axis
    sc_lat, sc_lon = offset_point(mk_lat, mk_lon, along_m, h_fwd)

    # Forward and backward edges of the thin strip
    fe_lat, fe_lon = offset_point(sc_lat, sc_lon, half, h_fwd)
    be_lat, be_lon = offset_point(sc_lat, sc_lon, half, h_bwd)

    def go_perp(lat, lon, d):
        """Signed perpendicular move: +d = left of road, -d = right."""
        if d >= 0:
            return offset_point(lat, lon,  d, h_left)
        else:
            return offset_point(lat, lon, -d, h_rgt)

    # 4 corners: forward-near, forward-far, backward-far, backward-near
    fn = go_perp(fe_lat, fe_lon, pa)
    ff = go_perp(fe_lat, fe_lon, pb)
    bf = go_perp(be_lat, be_lon, pb)
    bn = go_perp(be_lat, be_lon, pa)

    ring = [(fn[1], fn[0]), (ff[1], ff[0]), (bf[1], bf[0]), (bn[1], bn[0])]
    ring.append(ring[0])
    return ring   # (lon, lat)


# ─── main polygon generator ───────────────────────────────────────────────────

def generate_polygon_for_marker(
    markers: List[MarkerInfo],
    idx: int,
    spec: PolygonSpec,
    pca_h: Optional[float],
    use_osm: bool = True,
) -> GeneratedPolygon:
    """
    Build parallel, lane-aware speed breaker strips at one marker.

    Cross-section model (2 lanes, separator, 6 strips):

      road centre (marker position)
           │
    ←──────┼──────────────────────────── left side of road (+perp)
           │
    Lane 1 (left):  pa = sep_half,          pb = sep_half + lane_w
    Separator:      from -sep_half to +sep_half  (skipped)
    Lane 2 (right): pa = -sep_half,         pb = -(sep_half + lane_w)

    All strips at this marker get IDENTICAL heading → guaranteed parallel.
    Strips are stacked along-road centred at marker (equal strips forward & back).
    """
    cur  = markers[idx]
    hdg, src = resolve_heading(markers, idx, spec, pca_h, use_osm)
    curv = detect_curvature(markers, idx)

    sw_m  = spec.strip_width_mm / 1000.0
    gap_m = spec.gap_between_strips_m
    nl    = max(1, spec.num_lanes)

    # Separator half-width each side of centre
    sep_h = (spec.separator_width_m / 2.0) if (spec.has_separator and nl > 1) else 0.0

    # Lane drivable width (total drivable / num lanes)
    drv_total = spec.road_width_m - (spec.separator_width_m
                                      if spec.has_separator and nl > 1 else 0.0)
    lane_w    = drv_total / nl
    half_road = spec.road_width_m / 2.0

    # Distribute strips across lanes
    base = spec.num_strips // nl
    rem  = spec.num_strips % nl
    spl  = [base + (1 if i < rem else 0) for i in range(nl)]

    # Along-road span: ALL strips (both lanes) share the same centred stack
    total_along = spec.num_strips * sw_m + (spec.num_strips - 1) * gap_m
    start_along = -total_along / 2.0

    strips: List[List[Tuple[float, float]]] = []
    lanes:  List[int]                        = []
    g_idx = 0   # global strip counter

    for lane_idx in range(nl):
        n_in = spl[lane_idx]
        if n_in == 0:
            continue

        # ── Cross-road (perpendicular) extents ────────────────────────────
        if nl == 1:
            # Single lane: full road width
            pa, pb = -half_road, half_road

        elif lane_idx % 2 == 0:
            # Left side lanes (positive perpendicular)
            tier = lane_idx // 2
            pa   =  sep_h + tier * lane_w          # inner edge (near centre)
            pb   =  sep_h + (tier + 1) * lane_w    # outer edge

        else:
            # Right side lanes (negative perpendicular)
            tier = lane_idx // 2
            pa   = -(sep_h + tier * lane_w)
            pb   = -(sep_h + (tier + 1) * lane_w)

        # ── Build strips for this lane ────────────────────────────────────
        for _ in range(n_in):
            along = start_along + g_idx * (sw_m + gap_m) + sw_m / 2.0
            strips.append(make_strip(cur.lat, cur.lon, hdg, along, sw_m, pa, pb))
            lanes.append(lane_idx + 1)
            g_idx += 1

    # Bounding convex hull
    all_pts = [pt for s in strips for pt in s]
    bnd     = convex_hull(all_pts) if len(all_pts) >= 3 else all_pts

    return GeneratedPolygon(
        marker=cur, coordinates=bnd,
        heading_deg=hdg, road_curvature=curv,
        strip_polygons=strips, lane_assignments=lanes,
        heading_source=src, spec=spec,
    )


# ─── convex hull ─────────────────────────────────────────────────────────────

def convex_hull(pts):
    pts = sorted(set(pts))
    if len(pts) <= 2:
        return pts + ([pts[0]] if pts else [])

    def cross(O, A, B):
        return (A[0]-O[0])*(B[1]-O[1]) - (A[1]-O[1])*(B[0]-O[0])

    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    h = lo[:-1] + up[:-1]
    return h + [h[0]] if h else h


# ─── KML export ──────────────────────────────────────────────────────────────

_STYLES = """
  <Style id="sL1">
    <LineStyle><color>ff00d7ff</color><width>1</width></LineStyle>
    <PolyStyle><color>d000d7ff</color></PolyStyle>
  </Style>
  <Style id="sL2">
    <LineStyle><color>ff0088ff</color><width>1</width></LineStyle>
    <PolyStyle><color>d00088ff</color></PolyStyle>
  </Style>
  <Style id="bnd">
    <LineStyle><color>ff0000ff</color><width>2</width></LineStyle>
    <PolyStyle><color>110000ff</color></PolyStyle>
  </Style>
  <Style id="pin">
    <IconStyle>
      <color>ff00d7ff</color><scale>1.1</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href></Icon>
    </IconStyle>
    <LabelStyle><color>ffffffff</color><scale>0.85</scale></LabelStyle>
  </Style>
"""


def _cs(coords, alt=0):
    return " ".join(f"{lo},{la},{alt}" for lo, la in coords)


def export_kml(markers, polygons, out_path, spec):
    nl = spec.num_lanes
    lw = (spec.road_width_m -
          (spec.separator_width_m if spec.has_separator and nl > 1 else 0.0)) / nl

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '<Document>',
        '  <n>CAP PTBM Speed Breaker Polygons</n>',
        '  <description>Generated by GIS BOQ Tool — IIIT Nagpur</description>',
        _STYLES,
    ]

    for pg in polygons:
        mk  = pg.marker
        sep = f"{spec.separator_width_m}m" if spec.has_separator and nl > 1 else "none"
        info = (
            f"<b>{mk.placement_code or mk.name}</b><br/>"
            f"Heading: {pg.heading_deg:.1f}° [{pg.heading_source}]<br/>"
            f"Road: {pg.road_curvature.replace('_',' ').title()}<br/>"
            f"Lanes: {nl} | Strips: {spec.num_strips} ({spec.num_strips//nl}/lane)<br/>"
            f"Strip: {spec.strip_width_mm}mm × {lw:.2f}m | Sep: {sep}<br/>"
            f"Lat: {mk.lat:.6f}  Lon: {mk.lon:.6f}"
        )
        lines += [
            f'  <Folder>',
            f'    <n>{mk.name}</n>',
            '    <Placemark>',
            f'      <n>{mk.name}</n>',
            '      <styleUrl>#pin</styleUrl>',
            f'      <description><![CDATA[{info}]]></description>',
            f'      <Point><coordinates>{mk.lon},{mk.lat},0</coordinates></Point>',
            '    </Placemark>',
        ]

        if len(pg.coordinates) >= 3:
            lines += [
                '    <Placemark>',
                f'      <n>{mk.name} – Bounding</n>',
                '      <styleUrl>#bnd</styleUrl>',
                '      <Polygon><tessellate>1</tessellate>',
                '        <outerBoundaryIs><LinearRing>',
                f'          <coordinates>{_cs(pg.coordinates)}</coordinates>',
                '        </LinearRing></outerBoundaryIs></Polygon>',
                '    </Placemark>',
            ]

        for i, (strip, ln) in enumerate(
                zip(pg.strip_polygons, pg.lane_assignments), 1):
            lines += [
                '    <Placemark>',
                f'      <n>{mk.name} L{ln}S{i}</n>',
                f'      <styleUrl>#{"sL1" if ln == 1 else "sL2"}</styleUrl>',
                f'      <description><![CDATA[Strip {i} | Lane {ln} | '
                f'{spec.strip_width_mm}mm × {lw:.2f}m]]></description>',
                '      <Polygon><tessellate>1</tessellate>',
                '        <outerBoundaryIs><LinearRing>',
                f'          <coordinates>{_cs(strip)}</coordinates>',
                '        </LinearRing></outerBoundaryIs></Polygon>',
                '    </Placemark>',
            ]

        lines.append('  </Folder>')

    lines += ['</Document>', '</kml>']
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ─── Excel BOQ export ─────────────────────────────────────────────────────────

def export_excel(polygons, out_path, spec):
    wb  = openpyxl.Workbook()
    HF  = PatternFill("solid", start_color="1F3864", end_color="1F3864")
    YF  = PatternFill("solid", start_color="FFD700", end_color="FFD700")
    AF  = PatternFill("solid", start_color="EBF5FB", end_color="EBF5FB")
    WF  = PatternFill("solid", start_color="FFFFFF", end_color="FFFFFF")
    BLF = PatternFill("solid", start_color="D6EAF8", end_color="D6EAF8")
    T   = Border(left=Side(style='thin'), right=Side(style='thin'),
                 top=Side(style='thin'),  bottom=Side(style='thin'))
    CC  = Alignment(horizontal='center', vertical='center', wrap_text=True)
    LC  = Alignment(horizontal='left',   vertical='center', wrap_text=True)

    def hc(ws, r, c, v):
        cell = ws.cell(row=r, column=c, value=v)
        cell.font = Font(bold=True, size=9, color="FFFFFF")
        cell.fill = HF; cell.alignment = CC; cell.border = T
        return cell

    def dc(ws, r, c, v, fill=None, al=None):
        cell = ws.cell(row=r, column=c, value=v)
        cell.font = Font(size=9); cell.fill = fill or WF
        cell.alignment = al or CC; cell.border = T
        return cell

    nl  = spec.num_lanes
    lw  = (spec.road_width_m -
           (spec.separator_width_m if spec.has_separator and nl > 1 else 0.0)) / nl
    swm = spec.strip_width_mm / 1000.0

    # ── Sheet 1: BOQ ─────────────────────────────────────────────────────────
    ws = wb.active; ws.title = "BOQ Sheet 1"
    ws.merge_cells("A1:K1")
    ws['A1'].value = "ANNEXURE 1 - ESTIMATE"; ws['A1'].fill = HF
    ws['A1'].font = Font(bold=True, size=14, color="FFFFFF"); ws['A1'].alignment = CC

    ws.merge_cells("A2:K2")
    ws['A2'].value = "Speed Breaker CAP PTBM Road Marking — Bill of Quantities"
    ws['A2'].font = Font(bold=True, size=11); ws['A2'].alignment = CC

    ws.merge_cells("A3:K3")
    ws['A3'].value = "GIS BOQ Tool v5 | IIIT Nagpur | Dr. Neha Kasture | PWD/NHAI"
    ws['A3'].font = Font(italic=True, size=9, color="555555"); ws['A3'].alignment = CC
    ws.row_dimensions[4].height = 4

    for ci, h in enumerate(["S.No.","Description","Code","Nos.",
                              "Length\n(m)","Breadth\n(m)","Area\n(Sqm)",
                              "Total Qty\n(Sqm)","Rate\n(Rs./Sqm)",
                              "Amount\n(Rs.)","Notes"], 1):
        hc(ws, 5, ci, h)
    ws.row_dimensions[5].height = 40

    sep_str = f"{spec.separator_width_m}m" if spec.has_separator and nl > 1 else "none"
    ws.merge_cells("A6:K6")
    ws['A6'].value = (
        f"  Strip:{spec.strip_width_mm}mm | Strips:{spec.num_strips} | "
        f"Lanes:{nl} | RoadW:{spec.road_width_m}m | LaneW:{lw:.2f}m | "
        f"Sep:{sep_str} | Gap:{spec.gap_between_strips_m}m | "
        f"Heading:{spec.heading_override:.0f}° ({'manual' if spec.heading_override>=0 else 'auto'})"
    )
    ws['A6'].font = Font(bold=True, size=9, color="1F3864")
    ws['A6'].fill = BLF; ws['A6'].alignment = LC; ws['A6'].border = T

    for ri, pg in enumerate(polygons, 1):
        mk   = pg.marker; er = ri + 6
        fill = AF if ri % 2 == 0 else WF
        a1   = swm * lw; ta = a1 * spec.num_strips
        code = mk.placement_code or f"CAP PTBM {int(spec.strip_width_mm)}MM X {spec.num_strips}"
        desc = (f"Supply and Application of Single Rib Pattern Cold Applied Plastic (CAP) "
                f"Parabolic Transverse Bar Rumble Marking (PTBM) — "
                f"{int(spec.strip_width_mm)}mm Thk.")
        notes = (f"{pg.road_curvature.replace('_',' ').title()} | "
                 f"Hdg:{pg.heading_deg:.1f}°[{pg.heading_source}] | "
                 f"{mk.lat:.5f},{mk.lon:.5f}")
        dc(ws,er,1,ri,fill); dc(ws,er,2,desc,fill,al=LC)
        dc(ws,er,3,code,fill); dc(ws,er,4,1,fill)
        dc(ws,er,5,round(spec.road_width_m,2),fill)
        dc(ws,er,6,round(swm,4),fill)
        dc(ws,er,7,round(a1,5),fill)
        dc(ws,er,8,round(ta,4),fill)
        dc(ws,er,9,"",fill)
        amt = ws.cell(row=er, column=10, value=f'=IF(I{er}="","",H{er}*I{er})')
        amt.fill=fill; amt.border=T; amt.alignment=CC; amt.font=Font(size=9)
        dc(ws,er,11,notes,fill,al=LC)

    tr = len(polygons) + 7
    ws.merge_cells(f"A{tr}:G{tr}")
    for ci in range(1, 12):
        c = ws.cell(row=tr, column=ci)
        c.fill=YF; c.border=T; c.font=Font(bold=True,size=10); c.alignment=CC
    ws[f"A{tr}"].value = "TOTAL"
    ws[f"H{tr}"].value = f"=SUM(H7:H{tr-1})"
    ws[f"J{tr}"].value = f"=SUM(J7:J{tr-1})"
    for ci, w in enumerate([6,44,20,6,12,12,12,14,14,14,38], 1):
        ws.column_dimensions[get_column_letter(ci)].width = w

    # ── Sheet 2: Marker Details ───────────────────────────────────────────────
    ws2 = wb.create_sheet("Marker Details")
    for ci, h in enumerate(["#","Name","Code","Lat","Lon","Heading°","Src",
                              "Curvature","Lanes","Strips","Per Lane",
                              "Strip W(mm)","Road W(m)","Lane W(m)","Area/Strip"], 1):
        hc(ws2, 1, ci, h)
    ws2.row_dimensions[1].height = 28
    for ri, pg in enumerate(polygons, 2):
        mk   = pg.marker; fill = AF if ri % 2 == 0 else WF
        lw2  = (pg.spec.road_width_m -
                (pg.spec.separator_width_m if pg.spec.has_separator and pg.spec.num_lanes>1 else 0.0)
                ) / pg.spec.num_lanes
        for ci, v in enumerate([mk.index,mk.name,mk.placement_code or "—",
                                  round(mk.lat,7),round(mk.lon,7),
                                  round(pg.heading_deg,2), pg.heading_source,
                                  pg.road_curvature.replace('_',' ').title(),
                                  pg.spec.num_lanes, pg.spec.num_strips,
                                  pg.spec.num_strips//pg.spec.num_lanes,
                                  pg.spec.strip_width_mm, pg.spec.road_width_m,
                                  round(lw2,3),
                                  round(pg.spec.strip_width_mm/1000*lw2, 5)], 1):
            dc(ws2, ri, ci, v, fill)
    for i in range(1, 16):
        ws2.column_dimensions[get_column_letter(i)].width = 16

    # ── Sheet 3: Strip Coordinates ────────────────────────────────────────────
    ws3 = wb.create_sheet("Strip Coordinates")
    for ci, h in enumerate(["Marker#","Name","Lane","Strip","Corner","Lon","Lat"], 1):
        hc(ws3, 1, ci, h)
    r = 2
    for pg in polygons:
        for si, (strip, ln) in enumerate(zip(pg.strip_polygons, pg.lane_assignments), 1):
            fill = AF if si % 2 == 0 else WF
            for ci2, (lo, la) in enumerate(strip, 1):
                for ci3, v in enumerate(
                        [pg.marker.index, pg.marker.name, ln, si, ci2,
                         round(lo, 8), round(la, 8)], 1):
                    dc(ws3, r, ci3, v, fill)
                r += 1
    for i in range(1, 8):
        ws3.column_dimensions[get_column_letter(i)].width = 20

    # ── Sheet 4: Spec ─────────────────────────────────────────────────────────
    ws4 = wb.create_sheet("Project Spec")
    ws4.merge_cells("A1:B1")
    ws4['A1'].value = "Project Specification — Speed Breaker Installation"
    ws4['A1'].font = Font(bold=True, size=11, color="FFFFFF")
    ws4['A1'].fill = HF; ws4['A1'].alignment = CC; ws4['A1'].border = T
    drv = spec.road_width_m - (spec.separator_width_m if spec.has_separator and nl>1 else 0.0)
    lwa = drv / nl
    src = f"Manual ({spec.heading_override:.0f}°)" if spec.heading_override >= 0 else "OSM > PCA > Neighbour"
    rows = [
        ("Material",              "Cold Applied Plastic (CAP) PTBM — Parabolic Transverse Bar"),
        ("Strip Width",           f"{spec.strip_width_mm} mm"),
        ("Number of Strips",      str(spec.num_strips)),
        ("Number of Lanes",       str(spec.num_lanes)),
        ("Total Road Width",      f"{spec.road_width_m} m"),
        ("Centre Separator",      f"{spec.separator_width_m}m" if spec.has_separator else "None"),
        ("Drivable Width/Lane",   f"{lwa:.2f} m"),
        ("Strips per Lane",       f"≈ {spec.num_strips // nl}"),
        ("Gap Between Strips",    f"{spec.gap_between_strips_m} m"),
        ("Heading Source",        src),
        ("Total Markers",         str(len(polygons))),
        ("Total Strips",          str(len(polygons) * spec.num_strips)),
        ("Area per Strip",        f"{(spec.strip_width_mm/1000) * lwa:.5f} Sqm"),
    ]
    for ri, (lbl, val) in enumerate(rows, 2):
        fill = AF if ri % 2 == 0 else WF
        c1 = ws4.cell(row=ri, column=1, value=lbl)
        c2 = ws4.cell(row=ri, column=2, value=val)
        for c in [c1, c2]:
            c.fill = fill; c.border = T; c.alignment = LC
        c1.font = Font(bold=True, size=10); c2.font = Font(size=10)
    ws4.column_dimensions['A'].width = 30
    ws4.column_dimensions['B'].width = 52

    wb.save(out_path)


# ─── pipeline ────────────────────────────────────────────────────────────────

def run_pipeline(
    kml_in: str,
    kml_out: str,
    xlsx_out: str,
    spec: PolygonSpec,
    use_osm: bool = True,
    progress_callback=None,
) -> Tuple[List[MarkerInfo], List[GeneratedPolygon]]:

    markers = parse_kml_markers(kml_in)
    if not markers:
        raise ValueError("No point markers found in KML file.")

    pca_h = pca_heading(markers)

    polygons = []
    for i, mk in enumerate(markers):
        if progress_callback:
            progress_callback(i, len(markers), mk.name)
        polygons.append(
            generate_polygon_for_marker(markers, i, spec, pca_h, use_osm))

    export_kml(markers, polygons, kml_out, spec)
    export_excel(polygons, xlsx_out, spec)
    return markers, polygons


from typing import Tuple  # placed here to avoid early reference issue