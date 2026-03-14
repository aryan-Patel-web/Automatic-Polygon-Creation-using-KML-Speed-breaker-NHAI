# 🚧 GIS BOQ — Speed Breaker Polygon Generator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-77B829?style=for-the-badge&logo=leaflet&logoColor=white)
![OpenStreetMap](https://img.shields.io/badge/OpenStreetMap-7EBC6F?style=for-the-badge&logo=openstreetmap&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Automated GIS tool for PWD / NHAI road safety marking automation**

*Replaces 45–50 min manual workflow per site with a one-click pipeline*

[Features](#features) • [Demo](#demo) • [Installation](#installation) • [Usage](#usage) • [Architecture](#architecture) • [Approach](#technical-approach)

</div>

---

## 📌 Project Context

This tool was developed as part of a **Research Internship at IIIT Nagpur** under **Dr. Neha Kasture**, in collaboration with **Kataline India Pvt. Ltd.** and **PWD (Public Works Department)**.

The client's current workflow for preparing road safety site proposals is entirely manual:

| Step | Manual Process | Time |
|------|---------------|------|
| 1 | Open Google Earth Pro, draw paths, place coded placemarks | ~15 min |
| 2 | Manually draw yellow/red polygons over satellite imagery | ~10 min |
| 3 | Open Excel, hand-enter measurements, quantities, rates, BOQ amounts | ~15 min |
| 4 | Export KMZ, attach to submission | ~5 min |
| **Total** | **Per site** | **~45–50 min** |

> They handle **multiple sites per week**. The work is repetitive, error-prone, and amenable to automation — which is precisely why this tool was built.

---

## ✨ Features

- 📂 **KML Upload** — Parses Google Earth Pro KML files with point Placemarks
- 🧭 **Smart Heading Detection** — 3-tier fallback: Manual → OSM Overpass → PCA → Neighbour bearing
- 🟨 **CAP PTBM Strip Generation** — Precise yellow strip polygons perpendicular to road
- 🛣️ **Lane-Aware Placement** — Strips split across lanes with separator gap respected
- 📐 **Curve Detection** — Bearing-delta curvature classification (straight / slight / sharp)
- 🗺️ **Live Satellite Preview** — Folium map with Google Satellite tile overlay
- 📤 **KML Export** — Google Earth Pro-compatible KML with styled polygons per marker
- 📊 **Excel BOQ Export** — 4-sheet workbook matching PWD Annexure-1 format
- 🔄 **Heading Normalization** — 0–180° normalization prevents bearing-reversal zig-zag bug
- 🌐 **OSM Integration** — Queries OpenStreetMap Overpass API for road geometry

---

## 🖥️ Demo

```
Upload KML → Set heading (130°) → Set road width (14m) → Set separator (2m) → Generate

Output:
  ✅ speed_breaker_polygons.kml   → Open in Google Earth Pro
  ✅ speed_breaker_BOQ.xlsx       → Send to client
```

**Strip geometry verified:**
```
Strip dimensions:  6.000m × 0.015m  (lane width × strip thickness)
Strips per lane:   3 (Lane 1 going) + 3 (Lane 2 incoming)
Separator gap:     2.0m (skipped at road centre)
All strips:        Perfectly parallel ✓  Perpendicular to road ✓
```

---

## 🏗️ Project Structure

```
gis-boq-speed-breaker/
│
├── polygon.py          # Core geometry engine + KML/Excel export
├── ui.py               # Streamlit web interface
├── requirements.txt    # Python dependencies
├── README.md
│
└── samples/
    ├── sample_input.kml        # Example KML with 5 markers
    ├── sample_output.kml       # Generated polygons
    └── sample_output.xlsx      # Generated BOQ report
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10 or higher
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/gis-boq-speed-breaker.git
cd gis-boq-speed-breaker

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run ui.py
```

### Requirements

```txt
streamlit>=1.32.0
folium>=0.16.0
streamlit-folium>=0.20.0
openpyxl>=3.1.0
pandas>=2.0.0
```

---

## 🚀 Usage

### Step 1 — Prepare your KML
Open Google Earth Pro, mark speed breaker locations as Point Placemarks.
Name them using standard codes like `CAP PTBM 15MM X 6` or `CAP PTBM 10MM X 6`.
Save as `.kml` file.

### Step 2 — Set Road Heading
The most critical input. Use Google Earth Pro ruler:
```
Tools → Ruler → Line → draw along road centre → note heading in degrees
```

| Road Direction | Enter |
|---------------|-------|
| North–South   | 0°    |
| NE–SW         | 45°   |
| East–West     | 90°   |
| SE–NW         | 135°  |

### Step 3 — Measure Road Dimensions
```
Tools → Ruler → Line → drag across full road → note metres  →  Total Road Width
                     → drag across separator →  note metres  →  Separator Width
```

### Step 4 — Configure Strip Spec
Based on client's BOQ specification:
- Strip Width: `10mm` or `15mm` (CAP PTBM thickness)
- Number of Strips: `6`, `9`, etc. (distributed across all lanes)
- Gap Between Strips: typically `0.10m`

### Step 5 — Generate & Download
Click **Generate Polygons & Export BOQ** — downloads:
1. `speed_breaker_polygons.kml` — Open in Google Earth Pro
2. `speed_breaker_BOQ.xlsx` — 4-sheet Excel report for client

---

## 🔬 Technical Approach

### Problem: Why is road heading detection hard?

The naive approach of computing bearing between consecutive markers fails for several reasons:

1. **Clustered markers** — Client places multiple markers (`15MM X 9`, `15MM X 6`, `10MM X 6`) at nearly the same GPS coordinate (1–3m apart). Bearing between points 1m apart = random noise.

2. **Bearing reversal bug** — When computing weighted average of bearings from ±3 neighbours, a marker at the start of a sequence has only forward neighbours (bearing ~22°) while a middle marker has both prev and next (sometimes computing to ~202°). A circular mean of 22° and 202° gives 112° — completely wrong.

3. **Single isolated markers** — No neighbours → default heading = 0° (North) regardless of actual road direction.

### Solution: 3-Tier Heading Detection

```
Priority 1: Manual Override  (slider 0–179°)
    ↓ if not set
Priority 2: OSM Overpass API
    → Query nearest highway way within 40m
    → Compute heading from closest road segment nodes
    ↓ if OSM unavailable
Priority 3: PCA (Principal Component Analysis)
    → Convert all marker lat/lon to local metre coordinates
    → Compute 2×2 covariance matrix
    → Extract principal eigenvector → road axis direction
    → Only used if marker spread > 10m (else unreliable)
    ↓ if markers too clustered
Priority 4: Neighbour Bearing (least reliable)
    → Weighted average of ±3 neighbours
    → WITH heading normalisation to 0–180° (fixes reversal bug)
```

### Heading Normalisation Fix

```python
def normalise_heading(h: float) -> float:
    """
    Reduce to [0, 180°) — road direction is bidirectional.
    
    Without this: avg(22°, 202°) = 112°  ← WRONG (strips at 90° off)
    With this:    avg(22°,  22°) = 22°   ← CORRECT
    """
    h = h % 360
    return h - 180 if h >= 180 else h
```

### Strip Rectangle Geometry

Each CAP PTBM strip is a thin rectangle:
- **Long side** = lane width (perpendicular to road heading, across the lane)
- **Short side** = strip_width_mm (parallel to road heading, the thin dimension)

```
Road  ──────────────────────────────────────────────► heading H

←── lane_w ──→  ←── sep ──→  ←── lane_w ──→
┌──────────────┐              ┌──────────────┐
│ ════════════ │              │ ════════════ │  strip 1 & 4
│ ════════════ │              │ ════════════ │  strip 2 & 5
│ ════════════ │              │ ════════════ │  strip 3 & 6
└──────────────┘              └──────────────┘
   Lane 1 (→)     SEPARATOR      Lane 2 (←)
```

Construction of one strip rectangle:

```python
def make_strip(mk_lat, mk_lon, hdg, along_m, sw_m, pa, pb):
    """
    hdg    = road heading
    along_m = strip centre offset along road from marker
    sw_m   = strip width in metres (e.g. 0.015 for 15mm)
    pa, pb  = perpendicular extents: +ve = left of heading, -ve = right
    """
    h_fwd  = hdg
    h_bwd  = (hdg + 180) % 360
    h_left = (hdg - 90 + 360) % 360
    h_rgt  = (hdg + 90) % 360
    half   = sw_m / 2.0

    # Strip centre on road axis
    sc = offset_point(mk_lat, mk_lon, along_m, h_fwd)

    # Forward and backward edges (the thin dimension)
    fe = offset_point(sc, half, h_fwd)
    be = offset_point(sc, half, h_bwd)

    # 4 corners from perpendicular moves
    fn = go_perp(fe, pa)   # forward-near
    ff = go_perp(fe, pb)   # forward-far
    bf = go_perp(be, pb)   # backward-far
    bn = go_perp(be, pa)   # backward-near

    return [fn, ff, bf, bn, fn]  # closed ring
```

### Lane-Aware Separator Model

```
Road centre = marker position

Lane 0 (left, +perp direction):
  inner edge = +sep_half          (separator edge)
  outer edge = +sep_half + lane_w (road outer edge)

Lane 1 (right, -perp direction):
  inner edge = -sep_half
  outer edge = -(sep_half + lane_w)

Gap between inner edges = separator_width_m (no strips drawn here)
```

### Curve Detection

```python
def detect_curvature(markers, idx):
    b_in  = bearing(markers[idx-1] → markers[idx])
    b_out = bearing(markers[idx]   → markers[idx+1])
    delta = |normalise(b_in) - normalise(b_out)|

    if delta < 5°:   return "straight"
    if delta < 20°:  return "slight_curve"
    else:            return "sharp_curve"
```

On curved roads, each marker gets its own heading computed from its local neighbourhood — the polygon naturally tilts to follow the road curve.

---

## 📊 Excel BOQ Format

The exported Excel matches the client's **Annexure 1 — Estimate** format used for PWD site proposals:

| Sheet | Contents |
|-------|----------|
| **BOQ Sheet 1** | S.No, Description, Code, Nos, Length(m), Breadth(m), Area(Sqm), Total Qty, Rate, Amount |
| **Marker Details** | Per-marker: lat/lon, heading, curvature, lane width, area per strip |
| **Strip Coordinates** | All 4 corners of every generated strip polygon |
| **Project Spec** | Material spec, road config, heading source, totals |

---

## 🗺️ KML Output Structure

```xml
<Document>
  <Folder name="CAP PTBM 15MM X 6">
    <Placemark>  <!-- Original marker pin -->
    <Placemark>  <!-- Bounding outline (red dashed) -->
    <Placemark>  <!-- Lane 1 Strip 1 (yellow filled) -->
    <Placemark>  <!-- Lane 1 Strip 2 -->
    <Placemark>  <!-- Lane 1 Strip 3 -->
    <Placemark>  <!-- Lane 2 Strip 4 (orange filled) -->
    <Placemark>  <!-- Lane 2 Strip 5 -->
    <Placemark>  <!-- Lane 2 Strip 6 -->
  </Folder>
  <!-- ... repeated for each marker -->
</Document>
```

---

## 🧪 Geometry Verification

All strips are verified programmatically:

```
Marker 1: heading=130.0° source=manual
  Strip 1 Lane 1: length=6.000m  width=0.01500m ✓
  Strip 2 Lane 1: length=6.000m  width=0.01500m ✓
  Strip 3 Lane 1: length=6.000m  width=0.01500m ✓
  Strip 4 Lane 2: length=6.000m  width=0.01500m ✓
  Strip 5 Lane 2: length=6.000m  width=0.01500m ✓
  Strip 6 Lane 2: length=6.000m  width=0.01500m ✓
  All parallel (heading difference = 180.000° exactly) ✓
```

---

## 🏛️ Research Context

**Institution:** Indian Institute of Information Technology Manipur  
**Research Site:** IIIT Nagpur (Remote Internship)  
**Guide:** Dr. Neha Kasture  
**Client:** Kataline India Pvt. Ltd. / PWD  
**Domain:** Geospatial Automation, Road Safety Engineering  

**Problem Statement from Client Email (Mar 7, 2026):**
> *"Our current workflow for preparing site proposals is largely manual... This process takes 45–50 minutes per site. We handle multiple sites per week. The work is repetitive, error-prone, and amenable to automation."*

**Specific client requirements:**
1. Read a KMZ file exported from Google Earth Pro and extract placemark names and coordinates
2. Parse coded placemark names (e.g. `CAP PTBM 15MM X 6`) and auto-populate an editable Excel Bill of Quantities
3. Automatically calculate road marking quantities, road stud counts, and primer areas
4. Generate an updated KMZ file with representational polygon overlays
5. Bundle the Road Safety BOQ and KMZ into a single downloadable package

---

## 🔧 Configuration Reference

| Parameter | Description | Typical Values |
|-----------|-------------|----------------|
| `strip_width_mm` | CAP PTBM thickness | `10` or `15` |
| `num_strips` | Total strips all lanes | `6`, `9`, `12` |
| `gap_between_strips_m` | Along-road gap between strips | `0.10` |
| `num_lanes` | Total carriageway lanes | `2`, `4` |
| `road_width_m` | Full road width (measure in GEP) | `7–20` |
| `separator_width_m` | Centre divider width (measure in GEP) | `0.5–4.0` |
| `heading_override` | Road heading degrees (0–179, -1=auto) | `0–179` |

---

## 🤝 Contributing

Pull requests welcome. For major changes please open an issue first.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Aryan Patel**  
B.Tech Computer Science — IIIT Manipur  
Research Intern — IIIT Nagpur (Under Dr. Neha Kasture)  
[GitHub](https://github.com/aryan-patel-web) • [LinkedIn](https://linkedin.com/in/aryan-patel-97396524b)

---

<div align="center">
  <sub>Built for PWD / NHAI road safety automation | IIIT Nagpur Research Internship 2026</sub>
</div>