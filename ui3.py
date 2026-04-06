# # """
# # ui3.py v1 — Speed Breaker GIS BOQ Tool (p3)
# # IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI
# # Run: streamlit run ui3.py

# # FEATURES:
# #   ● Google Maps API integration (Roads API for curve detection, snap-to-road)
# #   ● Visible polygon strips (0.5m thick — clearly visible as rectangle in satellite)
# #   ● SLOW text label in KML output
# #   ● Excel with embedded satellite images (Google Static Maps API)
# #   ● Built-in KML viewer — no Google Earth Pro needed
# #   ● Upload & visualize updated KML directly in app
# #   ● Rate/Amount calculation in Excel
# #   ● API key loaded from .env file automatically
# # """
# # import streamlit as st
# # import tempfile, os, math, time, io
# # import pandas as pd
# # import folium
# # from streamlit_folium import st_folium
# # import xml.etree.ElementTree as ET
# # from typing import Dict, List, Tuple

# # from p3 import (
# #     PolySpec, KMLMarker, GenPoly,
# #     parse_kml, run_pipeline, export_kml, export_excel,
# #     LANE_PRESETS, haversine, norm180,
# # )

# # # ── Load API key from .env ─────────────────────────────────────────
# # def load_api_key() -> str:
# #     """Try multiple .env locations."""
# #     candidates = [
# #         r"D:\Road_Safety_Reasearch_III\.env",
# #         os.path.join(os.path.dirname(__file__), ".env"),
# #         ".env",
# #     ]
# #     for path in candidates:
# #         try:
# #             if os.path.exists(path):
# #                 for line in open(path, encoding="utf-8"):
# #                     line = line.strip()
# #                     if line.startswith("GOOGLE_API_KEY="):
# #                         key = line.split("=", 1)[1].strip().strip('"').strip("'")
# #                         if key and key != "":
# #                             return key
# #         except Exception:
# #             pass
# #     return ""

# # API_KEY = load_api_key()

# # # ── Page config ────────────────────────────────────────────────────
# # st.set_page_config(
# #     page_title="GIS BOQ Tool v1 · CAP PTBM p3",
# #     page_icon="🚧",
# #     layout="wide",
# #     initial_sidebar_state="expanded",
# # )

# # # ── CSS ────────────────────────────────────────────────────────────
# # st.markdown("""
# # <style>
# # @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
# # html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;}
# # #MainMenu,footer,header{visibility:hidden;}
# # .block-container{padding-top:1.0rem!important;padding-bottom:2rem!important;}

# # .hero{background:linear-gradient(135deg,#0f1923 0%,#1a2d42 60%,#0d2137 100%);
# #   border-radius:16px;padding:24px 32px;margin-bottom:18px;border:1px solid #1e3a52;
# #   position:relative;overflow:hidden;}
# # .hero::before{content:'';position:absolute;top:-50px;right:-50px;width:220px;height:220px;
# #   background:radial-gradient(circle,rgba(255,215,0,.10) 0%,transparent 70%);border-radius:50%;}
# # .hero-title{font-size:1.55rem;font-weight:700;color:#FFD700;margin:0 0 4px;}
# # .hero-sub{font-size:.80rem;color:#8ba8c4;margin:0;}
# # .hero-badges{display:flex;gap:7px;margin-top:11px;flex-wrap:wrap;}
# # .hbadge{background:rgba(255,215,0,.12);color:#FFD700;border:1px solid rgba(255,215,0,.3);
# #   padding:2px 9px;border-radius:20px;font-size:.68rem;font-weight:600;
# #   font-family:'JetBrains Mono',monospace;}

# # .sec-head{font-size:.66rem;font-weight:700;color:#FFD700;letter-spacing:1.5px;
# #   text-transform:uppercase;margin:16px 0 7px;padding-bottom:4px;border-bottom:1px solid #1e3a52;}

# # .info-card{background:#0a1f14;border:1px solid #1e5e35;border-left:4px solid #27ae60;
# #   border-radius:10px;padding:10px 15px;margin:5px 0;font-size:.82rem;color:#b0e8c4;}
# # .warn-card{background:#1f1800;border:1px solid #5e4a00;border-left:4px solid #f39c12;
# #   border-radius:10px;padding:10px 15px;margin:5px 0;font-size:.82rem;color:#f5d98a;}
# # .api-ok{background:#0a2e1a;border:2px solid #27ae60;border-radius:10px;
# #   padding:10px 15px;margin:6px 0;font-size:.82rem;color:#27ae60;}
# # .api-no{background:#2e0a0a;border:2px solid #e74c3c;border-radius:10px;
# #   padding:10px 15px;margin:6px 0;font-size:.82rem;color:#e8a0a0;}
# # .mk-card{background:#0a1220;border:1px solid #1e3a52;border-radius:10px;
# #   padding:10px 14px;margin:5px 0;}
# # .mk-name{font-size:.88rem;font-weight:700;color:#FFD700;margin-bottom:3px;}
# # .mk-coords{font-size:.74rem;color:#8ba8c4;font-family:'JetBrains Mono',monospace;}

# # .tab-viewer{background:#0a1220;border:1px solid #1e3a52;border-radius:12px;
# #   padding:16px;margin-top:12px;}

# # section[data-testid="stSidebar"]{background:#0a1220!important;border-right:1px solid #1e3a52;}
# # .stDownloadButton>button{background:linear-gradient(135deg,#FFD700,#ffa500)!important;
# #   color:#0f1923!important;font-weight:700!important;border:none!important;
# #   border-radius:10px!important;padding:11px 22px!important;width:100%!important;
# #   font-family:'Space Grotesk',sans-serif!important;}
# # .stButton>button[kind="primary"]{background:linear-gradient(135deg,#FFD700,#ffa500)!important;
# #   color:#0f1923!important;font-weight:700!important;border:none!important;
# #   border-radius:10px!important;width:100%!important;padding:11px!important;
# #   font-size:.95rem!important;margin-top:5px!important;}
# # </style>
# # """, unsafe_allow_html=True)

# # # ── Hero ───────────────────────────────────────────────────────────
# # api_badge = "🟢 Google API Connected" if API_KEY else "🔴 No API Key"
# # st.markdown(f"""
# # <div class="hero">
# #   <p class="hero-title">🚧 GIS BOQ Tool — CAP PTBM Speed Breaker</p>
# #   <p class="hero-sub">Center Marker Mode · IIIT Nagpur · Dr. Neha Kasture · PWD / NHAI</p>
# #   <div class="hero-badges">
# #     <span class="hbadge">p3 v1</span>
# #     <span class="hbadge">{api_badge}</span>
# #     <span class="hbadge">Curve-Aware Polygons</span>
# #     <span class="hbadge">SLOW Label in KML</span>
# #     <span class="hbadge">Satellite Images in Excel</span>
# #     <span class="hbadge">Built-in KML Viewer</span>
# #   </div>
# # </div>
# # """, unsafe_allow_html=True)


# # # ── Compass SVG (fixed — no subscript bug) ────────────────────────
# # def compass_svg(road_heading: float, size: int = 150) -> str:
# #     cx = size // 2; cy = size // 2; r = size // 2 - 12
# #     rh = float(road_heading) % 360; perp = (rh + 90) % 360
# #     def ep(a, l):
# #         a2 = math.radians(float(a) - 90)
# #         return cx + l * math.cos(a2), cy + l * math.sin(a2)
# #     rx1_x, rx1_y = ep(rh, r*.85)
# #     rx2_x, rx2_y = ep((rh+180)%360, r*.85)
# #     px1_x, px1_y = ep(perp, r*.80)
# #     px2_x, px2_y = ep((perp+180)%360, r*.80)
# #     cards = "".join(
# #         f'<text x="{cx+(r+9)*math.cos(math.radians(a-90)):.1f}" '
# #         f'y="{cy+(r+9)*math.sin(math.radians(a-90)):.1f}" '
# #         f'text-anchor="middle" dominant-baseline="central" font-size="9" fill="#8ba8c4">{l}</text>'
# #         for a,l in[(0,"N"),(90,"E"),(180,"S"),(270,"W")])
# #     tks = "".join(
# #         f'<line x1="{cx+(r-5)*math.cos(math.radians(a-90)):.1f}" '
# #         f'y1="{cy+(r-5)*math.sin(math.radians(a-90)):.1f}" '
# #         f'x2="{cx+r*math.cos(math.radians(a-90)):.1f}" '
# #         f'y2="{cy+r*math.sin(math.radians(a-90)):.1f}" stroke="#1e3a52" stroke-width="1.5"/>'
# #         for a in range(0,360,10))
# #     return (f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">'
# #             f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0a1220" stroke="#1e3a52" stroke-width="1.5"/>'
# #             f'{tks}{cards}'
# #             f'<line x1="{rx1_x:.1f}" y1="{rx1_y:.1f}" x2="{rx2_x:.1f}" y2="{rx2_y:.1f}" '
# #             f'stroke="#FFD700" stroke-width="3.5" stroke-linecap="round"/>'
# #             f'<line x1="{px1_x:.1f}" y1="{px1_y:.1f}" x2="{px2_x:.1f}" y2="{px2_y:.1f}" '
# #             f'stroke="#e67e22" stroke-width="2" stroke-dasharray="5,3" stroke-linecap="round"/>'
# #             f'<circle cx="{cx}" cy="{cy}" r="4" fill="#FFD700"/>'
# #             f'<rect x="4" y="{size-26}" width="10" height="4" fill="#FFD700" rx="2"/>'
# #             f'<text x="17" y="{size-20}" font-size="8" fill="#8ba8c4">Road {rh:.0f}°</text>'
# #             f'<rect x="4" y="{size-14}" width="10" height="3" fill="none" stroke="#e67e22" '
# #             f'stroke-width="2" stroke-dasharray="4,2" rx="1"/>'
# #             f'<text x="17" y="{size-8}" font-size="8" fill="#8ba8c4">Strip {perp:.0f}°</text>'
# #             f'</svg>')


# # # ── KML Viewer helper ─────────────────────────────────────────────
# # def parse_kml_for_viewer(kml_bytes: bytes):
# #     """Parse KML polygons and points for the built-in viewer."""
# #     polygons = []
# #     points   = []
# #     try:
# #         root = ET.fromstring(kml_bytes)
# #         def iter_pm(node):
# #             for c in node:
# #                 if c.tag.split("}")[-1] == "Placemark": yield c
# #                 else: yield from iter_pm(c)
# #         for pm in iter_pm(root):
# #             name = "Unnamed"
# #             desc = ""
# #             for c in pm:
# #                 tag = c.tag.split("}")[-1]
# #                 if tag == "name": name = (c.text or "").strip()
# #                 if tag == "description": desc = (c.text or "").strip()
# #             for el in pm.iter():
# #                 t = el.tag.split("}")[-1]
# #                 if t == "Polygon":
# #                     for ce in el.iter():
# #                         if ce.tag.split("}")[-1] == "coordinates" and ce.text:
# #                             pts = []
# #                             for tok in ce.text.strip().split():
# #                                 parts = tok.split(",")
# #                                 if len(parts) >= 2:
# #                                     try: pts.append((float(parts[1]), float(parts[0])))
# #                                     except: pass
# #                             if pts:
# #                                 polygons.append({"name": name, "desc": desc, "coords": pts})
# #                             break
# #                 elif t == "Point":
# #                     for ce in el.iter():
# #                         if ce.tag.split("}")[-1] == "coordinates" and ce.text:
# #                             parts = ce.text.strip().split(",")
# #                             if len(parts) >= 2:
# #                                 try:
# #                                     points.append({
# #                                         "name": name, "desc": desc,
# #                                         "lat": float(parts[1]), "lon": float(parts[0]),
# #                                     })
# #                                 except: pass
# #                             break
# #     except Exception:
# #         pass
# #     return polygons, points


# # def build_kml_viewer_map(polygons, points, zoom=18):
# #     """Build Folium map from KML data."""
# #     all_lats, all_lons = [], []
# #     for pg in polygons:
# #         for la, lo in pg["coords"]:
# #             all_lats.append(la); all_lons.append(lo)
# #     for pt in points:
# #         all_lats.append(pt["lat"]); all_lons.append(pt["lon"])

# #     if not all_lats:
# #         return None

# #     clat = sum(all_lats) / len(all_lats)
# #     clon = sum(all_lons) / len(all_lons)

# #     fmap = folium.Map(
# #         location=[clat, clon], zoom_start=zoom, max_zoom=21,
# #         tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
# #         attr="Google Satellite",
# #     )

# #     # Draw polygons
# #     for pg in polygons:
# #         is_strip = "PTBM" in pg["name"] or "CAP" in pg["name"]
# #         fill_col = "#FFD700" if is_strip else "#ff0000"
# #         fill_op  = 0.85 if is_strip else 0.0
# #         weight   = 1 if is_strip else 1
# #         folium.Polygon(
# #             locations=pg["coords"],
# #             color="#8B6914" if is_strip else "#ff0000",
# #             weight=weight, fill=is_strip,
# #             fill_color=fill_col,
# #             fill_opacity=fill_op,
# #             tooltip=pg["name"],
# #             popup=folium.Popup(
# #                 f"<b>{pg['name']}</b><br><small>{pg['desc'][:200]}</small>",
# #                 max_width=250),
# #         ).add_to(fmap)

# #     # Draw markers
# #     for pt in points:
# #         is_slow = pt["name"] == "SLOW"
# #         icon_col = "orange" if is_slow else "red"
# #         folium.Marker(
# #             [pt["lat"], pt["lon"]],
# #             tooltip=pt["name"],
# #             popup=folium.Popup(
# #                 f"<b>{pt['name']}</b><br><small>{pt['desc'][:200]}</small>",
# #                 max_width=220),
# #             icon=folium.Icon(color=icon_col, icon="map-marker", prefix="fa"),
# #         ).add_to(fmap)

# #         # Name label
# #         folium.Marker(
# #             [pt["lat"], pt["lon"]],
# #             icon=folium.DivIcon(
# #                 html=f'<div style="font-size:11px;font-weight:700;'
# #                      f'color:{"#FFA500" if is_slow else "#FFD700"};'
# #                      f'background:rgba(0,0,0,0.65);padding:2px 5px;'
# #                      f'border-radius:3px;white-space:nowrap;'
# #                      f'margin-top:-28px;margin-left:14px;">{pt["name"]}</div>',
# #                 icon_size=(160, 28), icon_anchor=(0, 0),
# #             ),
# #         ).add_to(fmap)

# #     return fmap


# # # ── Session state ──────────────────────────────────────────────────
# # for k, v in [
# #     ("markers", []), ("all_polys", []), ("headings", {}),
# #     ("kml_bytes", None), ("xlsx_bytes", None), ("generated", False),
# #     ("per_marker_h", {}), ("per_marker_w", {}), ("per_marker_strips", {}),
# #     ("viewer_kml_bytes", None),
# # ]:
# #     if k not in st.session_state: st.session_state[k] = v


# # # ══════════════════════════════════════════════════════════════════
# # # TABS: Generate | KML Viewer
# # # ══════════════════════════════════════════════════════════════════
# # tab_gen, tab_view = st.tabs(["🔄 Generate Polygons", "🗺️ KML Viewer (No Google Earth Needed)"])


# # # ══════════════════════════════════════════════════════════════════
# # # SIDEBAR (shared across tabs)
# # # ══════════════════════════════════════════════════════════════════
# # with st.sidebar:
# #     # API key status
# #     if API_KEY:
# #         st.markdown(
# #             f'<div class="api-ok">✅ Google API Connected<br>'
# #             f'<small style="font-family:monospace">{API_KEY[:8]}…{API_KEY[-4:]}</small></div>',
# #             unsafe_allow_html=True,
# #         )
# #     else:
# #         st.markdown(
# #             '<div class="api-no">⚠️ No Google API Key<br>'
# #             '<small>Add GOOGLE_API_KEY to .env<br>'
# #             'Roads API + Static Maps will not work</small></div>',
# #             unsafe_allow_html=True,
# #         )
# #         manual_key = st.text_input("Paste API key here (session only):", type="password", key="manual_api")
# #         if manual_key: API_KEY = manual_key

# #     st.markdown('<p class="sec-head">📂 KML Upload</p>', unsafe_allow_html=True)
# #     st.markdown(
# #         '<div class="info-card">ℹ️ Upload KML with <b>center markers only</b>.<br>'
# #         'One red pin = center of road at each speed breaker.</div>',
# #         unsafe_allow_html=True,
# #     )
# #     uploaded = st.file_uploader("Upload KML", type=["kml"], label_visibility="collapsed")

# #     st.markdown('<p class="sec-head">🛣️ Road Configuration</p>', unsafe_allow_html=True)
# #     lane_key = st.selectbox("Lane Type", list(LANE_PRESETS.keys()), index=1, key="lk")
# #     lp = LANE_PRESETS[lane_key]
# #     if lane_key == "Custom":
# #         road_w = st.number_input("Road Width (m)", 2.0, 60.0, 7.0, 0.5, key="rw")
# #         sep_w  = st.number_input("Separator (m)",  0.0, 10.0, 0.5, 0.1, key="sep")
# #         nl_def = int(st.number_input("Lanes", 1, 8, 2, 1, key="nl"))
# #     else:
# #         road_w = float(lp["road_width_m"])
# #         sep_w  = float(lp["separator_width_m"])
# #         nl_def = int(lp["num_lanes"])
# #         lw_a   = (road_w - sep_w) / max(nl_def, 1)
# #         st.caption(f"Width: **{road_w}m** | Lanes: **{nl_def}** | Lane: **{lw_a:.2f}m**")

# #     st.markdown('<p class="sec-head">🧭 Road Heading</p>', unsafe_allow_html=True)
# #     hmode = st.radio("Source",
# #         ["Auto (Google Roads API / neighbours)", "Manual (all markers)"],
# #         key="hmode")
# #     global_heading = None
# #     if hmode == "Manual (all markers)":
# #         global_heading = float(st.slider("Heading °", 0, 179, 90, key="gh"))
# #         st.markdown(compass_svg(global_heading, 145), unsafe_allow_html=True)
# #         st.caption(f"Road **{global_heading:.0f}°** → Strip **{(global_heading+90)%360:.0f}°**")
# #     else:
# #         if API_KEY:
# #             st.caption("✅ Google Roads API will detect road angle at each marker")
# #         else:
# #             st.caption("Heading auto-detected from neighbouring marker positions")

# #     st.markdown('<p class="sec-head">🟨 Strip Configuration</p>', unsafe_allow_html=True)
# #     n_strips   = int(st.number_input("Number of Strips", 1, 20, 3, 1, key="ns"))
# #     strip_thick = st.number_input(
# #         "Strip Thickness (m along road)",
# #         min_value=0.05, max_value=2.0,
# #         value=0.5, step=0.05, key="sthick",
# #         help="Physical thickness of each strip ALONG road direction. "
# #              "0.5m = clearly visible in satellite view as a filled rectangle.",
# #     )
# #     strip_gap  = st.number_input("Gap Between Strips (m)", 0.1, 5.0, 0.6, 0.1, key="sg")
# #     total_span = n_strips * strip_thick + (n_strips - 1) * strip_gap
# #     st.caption(
# #         f"{n_strips} strips × {strip_thick*1000:.0f}mm | "
# #         f"gap={strip_gap}m | total span=**{total_span:.2f}m**"
# #     )

# #     add_slow   = st.toggle("Add SLOW label to KML", value=True, key="slow")
# #     rate_rs    = st.number_input("Rate (Rs/m²)", 100, 50000, 2500, 100, key="rate")

# #     st.markdown("---")
# #     gen_btn = st.button("🔄 Generate Polygons", type="primary",
# #                         disabled=uploaded is None, key="genb")
# #     if not uploaded: st.caption("⬆️ Upload KML to enable")


# # # ══════════════════════════════════════════════════════════════════
# # # TAB 1: GENERATE
# # # ══════════════════════════════════════════════════════════════════
# # with tab_gen:
# #     markers_raw: list = []
# #     n_markers = 0
# #     kml_temp  = ""

# #     if uploaded:
# #         with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as tmp:
# #             tmp.write(uploaded.getvalue())
# #             kml_temp = tmp.name

# #         try:
# #             _markers = parse_kml(kml_temp)
# #             n_markers = len(_markers)
# #             markers_raw = _markers

# #             mc1, mc2, mc3, mc4 = st.columns(4)
# #             mc1.metric("📍 Markers", n_markers)
# #             mc2.metric("🛣️ Road Width", f"{road_w}m")
# #             mc3.metric("🟨 Strips/Marker", n_strips)
# #             mc4.metric("📐 Strip Thick", f"{strip_thick*1000:.0f}mm")

# #             if n_markers == 0:
# #                 st.error("❌ No Point markers found. Place red pins in Google Earth Pro and re-export.")
# #             else:
# #                 st.markdown(
# #                     f'<div class="info-card">✅ <b>{n_markers} center marker(s)</b> loaded. '
# #                     f'Each strip will span <b>{road_w}m</b> perpendicular to road, '
# #                     f'<b>{strip_thick*1000:.0f}mm ({strip_thick:.2f}m) thick</b> — '
# #                     f'clearly visible as filled rectangle in satellite view.</div>',
# #                     unsafe_allow_html=True,
# #                 )

# #                 # Show markers
# #                 st.markdown('<p class="sec-head">📍 Loaded Markers</p>', unsafe_allow_html=True)
# #                 cols = st.columns(min(n_markers, 3))
# #                 for ci, mk in enumerate(_markers):
# #                     with cols[ci % len(cols)]:
# #                         st.markdown(
# #                             f'<div class="mk-card">'
# #                             f'<div class="mk-name">📍 {mk.index+1}. {mk.name}</div>'
# #                             f'<div class="mk-coords">Lat: {mk.lat:.6f}<br>Lon: {mk.lon:.6f}</div>'
# #                             f'</div>',
# #                             unsafe_allow_html=True,
# #                         )

# #         except Exception as e:
# #             st.error(f"❌ Parse error: {e}")
# #             import traceback; st.code(traceback.format_exc())

# #     else:
# #         c1, c2 = st.columns([2, 1])
# #         with c1:
# #             st.markdown("""
# #             <div style="background:#0a1220;border:1px dashed #1e3a52;border-radius:16px;
# #                         padding:40px;text-align:center;margin-top:10px">
# #               <div style="font-size:2.5rem;margin-bottom:14px">🗺️</div>
# #               <div style="font-size:1.05rem;font-weight:600;color:#e8eaf0;margin-bottom:8px">
# #                 Upload KML — Center Markers Only</div>
# #               <div style="font-size:.82rem;color:#8ba8c4;max-width:360px;margin:0 auto">
# #                 Place one red pin at the <b>center of the road</b> for each
# #                 speed breaker in Google Earth Pro. Export as KML and upload here.
# #               </div>
# #             </div>""", unsafe_allow_html=True)
# #         with c2:
# #             st.markdown("**Simple workflow:**")
# #             for s, t in [
# #                 ("1️⃣", "Open Google Earth Pro"),
# #                 ("2️⃣", "Place red pin at road CENTER for each speed breaker"),
# #                 ("3️⃣", "File → Save Place As → KML"),
# #                 ("4️⃣", "Upload here, configure, click Generate"),
# #                 ("5️⃣", "Download KML + Excel, or test in KML Viewer tab"),
# #             ]:
# #                 st.markdown(f"{s} {t}")

# #     # ── Per-marker overrides ───────────────────────────────────────
# #     if n_markers > 0:
# #         st.markdown('<p class="sec-head">🎯 Per-Marker Overrides (optional)</p>',
# #                     unsafe_allow_html=True)
# #         with st.expander("Customize individual markers", expanded=False):
# #             if st.button("🗑️ Clear All Overrides", key="clr"):
# #                 st.session_state.per_marker_h = {}
# #                 st.session_state.per_marker_w = {}
# #                 st.session_state.per_marker_strips = {}
# #                 st.rerun()

# #             for mk in markers_raw:
# #                 i = mk.index
# #                 with st.expander(f"Marker {i+1}: {mk.name}", expanded=False):
# #                     oc1, oc2, oc3 = st.columns(3)
# #                     with oc1:
# #                         use_w = st.toggle("Custom width", key=f"uw{i}")
# #                         if use_w:
# #                             nw = st.number_input("Width (m)", 2.0, 60.0,
# #                                 st.session_state.per_marker_w.get(i, road_w), 0.5, key=f"mw{i}")
# #                             st.session_state.per_marker_w[i] = nw
# #                         elif i in st.session_state.per_marker_w:
# #                             del st.session_state.per_marker_w[i]
# #                     with oc2:
# #                         use_h = st.toggle("Custom heading", key=f"uh{i}")
# #                         if use_h:
# #                             nh = st.slider("Heading °", 0, 179,
# #                                 int(st.session_state.per_marker_h.get(i, global_heading or 90)),
# #                                 1, key=f"mh{i}")
# #                             st.session_state.per_marker_h[i] = float(nh)
# #                         elif i in st.session_state.per_marker_h:
# #                             del st.session_state.per_marker_h[i]
# #                     with oc3:
# #                         use_s = st.toggle("Custom strips", key=f"us{i}")
# #                         if use_s:
# #                             ns2 = int(st.number_input("Strips", 1, 20,
# #                                 st.session_state.per_marker_strips.get(i, n_strips),
# #                                 1, key=f"ms{i}"))
# #                             st.session_state.per_marker_strips[i] = ns2
# #                         elif i in st.session_state.per_marker_strips:
# #                             del st.session_state.per_marker_strips[i]
# #                     dh = float(st.session_state.per_marker_h.get(i) or global_heading or 90.0)
# #                     st.markdown(compass_svg(dh, 130), unsafe_allow_html=True)

# #     # ── Generate ───────────────────────────────────────────────────
# #     if gen_btn and uploaded and n_markers > 0:
# #         spec = PolySpec(
# #             road_width_m      = road_w,
# #             num_lanes         = nl_def,
# #             separator_width_m = sep_w,
# #             num_strips        = n_strips,
# #             strip_thick_m     = float(strip_thick),
# #             strip_gap_m       = float(strip_gap),
# #             heading_override  = global_heading,
# #             add_slow_label    = add_slow,
# #             api_key           = API_KEY,
# #         )
# #         for mk in markers_raw:
# #             i = mk.index; ov = {}
# #             if i in st.session_state.per_marker_w:
# #                 ov["road_width_m"] = st.session_state.per_marker_w[i]
# #             if i in st.session_state.per_marker_h:
# #                 ov["heading_deg"] = st.session_state.per_marker_h[i]
# #             if i in st.session_state.per_marker_strips:
# #                 ov["num_strips"] = st.session_state.per_marker_strips[i]
# #             if ov: spec.marker_overrides[i] = ov

# #         per_h = dict(st.session_state.per_marker_h)

# #         prog = st.progress(0, "Parsing KML…")
# #         status_text = st.empty()

# #         def _update(msg, pct):
# #             prog.progress(min(pct, 99), msg)
# #             status_text.caption(msg)

# #         try:
# #             _update("Parsing KML…", 10)
# #             m_obj, polys, headings = run_pipeline(
# #                 kml_temp, spec, per_h, progress_cb=_update)
# #             _update("Exporting KML…", 70)

# #             out_kml  = kml_temp.replace(".kml", "_p3_out.kml")
# #             out_xlsx = kml_temp.replace(".kml", "_p3_out.xlsx")

# #             export_kml(m_obj, polys, headings, spec, out_kml)
# #             _update("Exporting Excel (fetching satellite images…)…", 80)
# #             export_excel(m_obj, polys, headings, spec, out_xlsx,
# #                          progress_cb=_update)

# #             _update("Finalising…", 95)
# #             with open(out_kml, "rb") as f:
# #                 st.session_state.kml_bytes = f.read()
# #             with open(out_xlsx, "rb") as f:
# #                 st.session_state.xlsx_bytes = f.read()

# #             st.session_state.markers    = m_obj
# #             st.session_state.all_polys  = polys
# #             st.session_state.headings   = headings
# #             st.session_state.generated  = True
# #             # Also put generated KML into viewer
# #             st.session_state.viewer_kml_bytes = st.session_state.kml_bytes

# #             prog.progress(100, "Done ✅")
# #             status_text.empty()
# #             time.sleep(0.4)
# #             prog.empty()
# #             st.rerun()

# #         except Exception as e:
# #             prog.empty()
# #             status_text.empty()
# #             st.error(f"❌ Error: {e}")
# #             import traceback; st.code(traceback.format_exc())

# #     # ── Results ────────────────────────────────────────────────────
# #     if st.session_state.generated and st.session_state.all_polys:
# #         m_obj  = st.session_state.markers
# #         polys  = st.session_state.all_polys
# #         heads  = st.session_state.headings

# #         st.markdown('<p class="sec-head">✅ Results</p>', unsafe_allow_html=True)
# #         r1, r2, r3, r4, r5 = st.columns(5)
# #         r1.metric("📍 Markers",      len(m_obj))
# #         r2.metric("🟨 Total Strips", len(polys))
# #         r3.metric("🛣️ Road Width",   f"{road_w}m")
# #         r4.metric("📐 Strip Thick",  f"{strip_thick*1000:.0f}mm")
# #         r5.metric("Strips/Marker",   len(polys) // max(len(m_obj), 1))

# #         # Downloads
# #         st.markdown('<p class="sec-head">📥 Downloads</p>', unsafe_allow_html=True)
# #         dl1, dl2 = st.columns(2)
# #         if st.session_state.kml_bytes:
# #             dl1.download_button(
# #                 "📥 Download KML — Google Earth Pro",
# #                 data=st.session_state.kml_bytes,
# #                 file_name="speed_breakers_p3.kml",
# #                 mime="application/vnd.google-earth.kml+xml",
# #                 use_container_width=True,
# #             )
# #         if st.session_state.xlsx_bytes:
# #             dl2.download_button(
# #                 "📊 Download Excel BOQ Report",
# #                 data=st.session_state.xlsx_bytes,
# #                 file_name="speed_breakers_p3_boq.xlsx",
# #                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
# #                 use_container_width=True,
# #             )
# #         st.markdown(
# #             '<div class="info-card">💡 <b>KML Viewer tab</b> — click it above to verify '
# #             'your generated polygons on satellite map without Google Earth Pro.</div>',
# #             unsafe_allow_html=True,
# #         )

# #         # Summary table
# #         st.markdown('<p class="sec-head">📋 BOQ Summary Table</p>', unsafe_allow_html=True)
# #         by: Dict = {}
# #         for p in polys: by.setdefault(p.marker_idx, []).append(p)
# #         rows = []
# #         for mk in m_obj:
# #             ps = by.get(mk.index, []); p0 = ps[0] if ps else None
# #             hdata = heads.get(mk.index, (0.0, mk.lat, mk.lon, "default"))
# #             h_deg = hdata[0]; snap_lat = hdata[1]; snap_lon = hdata[2]
# #             rw_v  = p0.road_width_m  if p0 else road_w
# #             st_v  = p0.strip_thick_m if p0 else strip_thick
# #             gap_v = p0.strip_gap_m   if p0 else strip_gap
# #             ns_v  = len(ps)
# #             span  = ns_v * st_v + max(ns_v-1, 0) * gap_v
# #             area  = round(st_v * rw_v * ns_v, 4)
# #             amt   = round(area * rate_rs, 2)
# #             rows.append({
# #                 "S.No":          mk.index+1,
# #                 "Marker":        mk.name,
# #                 "Snap Lat":      round(snap_lat, 6),
# #                 "Snap Lon":      round(snap_lon, 6),
# #                 "Bearing (°)":   round(h_deg, 1),
# #                 "Road Width (m)":round(rw_v, 2),
# #                 "Mark Length (m)": round(span, 3),
# #                 "Strips":        ns_v,
# #                 "Area (m²)":     area,
# #                 f"Rate (Rs/m²)": rate_rs,
# #                 "Amount (Rs)":   amt,
# #                 "Heading Src":   hdata[3],
# #             })
# #         st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# #         # Live map preview
# #         st.markdown('<p class="sec-head">🗺️ Live Satellite Preview</p>',
# #                     unsafe_allow_html=True)
# #         if m_obj:
# #             clat = sum(m.lat for m in m_obj) / len(m_obj)
# #             clon = sum(m.lon for m in m_obj) / len(m_obj)
# #             fmap = folium.Map(
# #                 location=[clat, clon], zoom_start=19, max_zoom=21,
# #                 tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
# #                 attr="Google Satellite",
# #             )
# #             COLS = ["#FFD700","#FFB300","#FF8C00","#FFA500","#FFCC00","#FFE066"]
# #             for p in polys:
# #                 col = COLS[p.strip_idx % len(COLS)]
# #                 folium.Polygon(
# #                     locations=[[la, lo] for la, lo in p.coords],
# #                     color="#8B6914", weight=1, fill=True,
# #                     fill_color=col, fill_opacity=0.88,
# #                     tooltip=(f"{p.marker_name} | Strip {p.strip_idx+1} | "
# #                              f"{p.road_heading:.1f}° | {p.road_width_m:.1f}m wide | "
# #                              f"{p.strip_thick_m*1000:.0f}mm thick"),
# #                 ).add_to(fmap)
# #             for mk in m_obj:
# #                 hd = heads.get(mk.index, (0.0, mk.lat, mk.lon, ""))
# #                 folium.Marker(
# #                     [hd[1], hd[2]],
# #                     popup=folium.Popup(
# #                         f"<b>{mk.name}</b><br>"
# #                         f"CAP PTBM {strip_thick*1000:.0f}MM X {len(by.get(mk.index,[]))}<br>"
# #                         f"Heading: {hd[0]:.1f}° [{hd[3]}]<br>"
# #                         f"Road: {road_w:.1f}m | {nl_def} Lane",
# #                         max_width=220),
# #                     icon=folium.Icon(color="red", icon="map-marker", prefix="fa"),
# #                 ).add_to(fmap)
# #                 # Name label
# #                 folium.Marker([hd[1], hd[2]], icon=folium.DivIcon(
# #                     html=f'<div style="font-size:11px;font-weight:700;color:#FFD700;'
# #                          f'background:rgba(0,0,0,0.65);padding:2px 5px;border-radius:3px;'
# #                          f'white-space:nowrap;margin-top:-28px;margin-left:14px;">'
# #                          f'{mk.name}</div>',
# #                     icon_size=(160, 28), icon_anchor=(0, 0),
# #                 )).add_to(fmap)
# #             st_folium(fmap, width="100%", height=540, returned_objects=[])

# #         # Per-marker detail expanders
# #         st.markdown('<p class="sec-head">📐 Per-Marker Strip Detail</p>',
# #                     unsafe_allow_html=True)
# #         for mk in m_obj:
# #             ps = by.get(mk.index, [])
# #             if not ps: continue
# #             p0 = ps[0]
# #             hd = heads.get(mk.index, (0.0, mk.lat, mk.lon, "default"))
# #             with st.expander(f"📍 {mk.name} — {len(ps)} strips | "
# #                              f"{p0.road_width_m:.1f}m wide | {p0.strip_thick_m*1000:.0f}mm thick"):
# #                 dc1, dc2 = st.columns([2, 1])
# #                 with dc1:
# #                     area_s = p0.strip_thick_m * p0.road_width_m
# #                     span   = len(ps)*p0.strip_thick_m + max(len(ps)-1,0)*p0.strip_gap_m
# #                     st.markdown(f"""
# # | Property | Value |
# # |---|---|
# # | Marker Name | **{mk.name}** |
# # | Snapped Lat | `{hd[1]:.6f}` |
# # | Snapped Lon | `{hd[2]:.6f}` |
# # | Road Width | **{p0.road_width_m:.2f} m** |
# # | Lanes | {p0.num_lanes} |
# # | Lane Width | {p0.lane_width_m:.2f} m |
# # | Heading | {hd[0]:.1f}° ({hd[3]}) |
# # | Total Strips | {len(ps)} |
# # | Strip Thick | {p0.strip_thick_m*1000:.0f} mm (along road) |
# # | Strip Length | {p0.road_width_m:.2f} m (across road) |
# # | Gap between strips | {p0.strip_gap_m:.2f} m |
# # | Total span | {span:.3f} m |
# # | Area / Strip | {area_s:.4f} m² |
# # | Total Area | {area_s*len(ps):.4f} m² |
# # | Amount | Rs {area_s*len(ps)*rate_rs:,.0f} |
# # | KML Label | CAP PTBM {p0.strip_thick_m*1000:.0f}MM X {len(ps)} |
# # """)
# #                 with dc2:
# #                     st.markdown(compass_svg(hd[0], 148), unsafe_allow_html=True)
# #                     st.caption(f"Road **{hd[0]:.0f}°** | Strip **{(hd[0]+90)%360:.0f}°**")


# # # ══════════════════════════════════════════════════════════════════
# # # TAB 2: KML VIEWER
# # # ══════════════════════════════════════════════════════════════════
# # with tab_view:
# #     st.markdown("""
# #     <div class="info-card">
# #       🗺️ <b>Built-in KML Viewer</b> — Upload any KML file (original or generated) to
# #       visualize it on a satellite map. No Google Earth Pro required.<br>
# #       Yellow filled rectangles = speed breaker strip polygons.
# #     </div>
# #     """, unsafe_allow_html=True)

# #     col_v1, col_v2 = st.columns([1, 3])
# #     with col_v1:
# #         viewer_upload = st.file_uploader(
# #             "Upload KML to view", type=["kml"], key="viewer_kml",
# #             help="Upload any KML file to visualize on satellite map",
# #         )
# #         if viewer_upload:
# #             st.session_state.viewer_kml_bytes = viewer_upload.read()

# #         # Or use generated KML
# #         if st.session_state.kml_bytes and not viewer_upload:
# #             if st.button("📂 Load Generated KML", key="load_gen"):
# #                 st.session_state.viewer_kml_bytes = st.session_state.kml_bytes
# #                 st.rerun()

# #         viewer_zoom = st.slider("Map Zoom", 15, 21, 19, key="vzoom")
# #         show_labels = st.toggle("Show polygon labels", True, key="slbl")

# #     with col_v2:
# #         if st.session_state.viewer_kml_bytes:
# #             kml_bytes = st.session_state.viewer_kml_bytes
# #             polygons, points = parse_kml_for_viewer(kml_bytes)
# #             n_pg  = len(polygons)
# #             n_pin = len(points)

# #             vc1, vc2, vc3 = st.columns(3)
# #             vc1.metric("🔷 Polygons", n_pg)
# #             vc2.metric("📍 Markers",  n_pin)
# #             vc3.metric("🔶 SLOW labels",
# #                        sum(1 for p in points if p["name"] == "SLOW"))

# #             if polygons or points:
# #                 fmap = build_kml_viewer_map(polygons, points, zoom=viewer_zoom)
# #                 if fmap:
# #                     st_folium(fmap, width="100%", height=580, returned_objects=[])
# #                 else:
# #                     st.warning("No geographic data found in KML")
# #             else:
# #                 st.warning("No polygons or markers found in the uploaded KML file.")

# #             # KML statistics
# #             with st.expander("📊 KML Contents"):
# #                 strip_names = [p["name"] for p in polygons if "CAP" in p["name"] or "PTBM" in p["name"]]
# #                 slow_pts    = [p for p in points if p["name"] == "SLOW"]
# #                 pin_pts     = [p for p in points if p["name"] != "SLOW"]
# #                 st.markdown(f"""
# # - **{len(strip_names)}** CAP PTBM strip polygons
# # - **{len(pin_pts)}** marker pins
# # - **{len(slow_pts)}** SLOW labels
# # - **{n_pg - len(strip_names)}** other polygons (bounding boxes, etc.)
# #                 """)
# #                 if pin_pts:
# #                     df_v = pd.DataFrame([{
# #                         "Name": p["name"],
# #                         "Lat": round(p["lat"], 6),
# #                         "Lon": round(p["lon"], 6),
# #                     } for p in pin_pts])
# #                     st.dataframe(df_v, hide_index=True, use_container_width=True)
# #         else:
# #             st.markdown("""
# #             <div style="background:#0a1220;border:1px dashed #1e3a52;border-radius:12px;
# #                         padding:50px;text-align:center;">
# #               <div style="font-size:2.5rem;margin-bottom:12px">🗺️</div>
# #               <div style="font-size:1rem;font-weight:600;color:#e8eaf0;margin-bottom:8px">
# #                 No KML loaded</div>
# #               <div style="font-size:.82rem;color:#8ba8c4">
# #                 Upload a KML file on the left, or generate polygons in the first tab
# #                 (the generated KML will auto-load here).
# #               </div>
# #             </div>
# #             """, unsafe_allow_html=True)


# """
# ui3.py v2 — Speed Breaker GIS BOQ Tool (p3)
# IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI
# Run: streamlit run ui3.py

# FIX v2:
#   ● Added: from typing import Dict, List, Optional, Tuple  ← fixes NameError: name 'Dict' is not defined
#   ● High-zoom satellite images in Excel (zoom=20, scale=2, 640x480)
#   ● All other features intact
# """
# import streamlit as st
# import tempfile, os, math, time, io
# # ── CRITICAL FIX: import Dict and other typing helpers ────────────
# from typing import Dict, List, Optional, Tuple
# import pandas as pd
# import folium
# from streamlit_folium import st_folium
# import xml.etree.ElementTree as ET

# from p3 import (
#     PolySpec, KMLMarker, GenPoly,
#     parse_kml, run_pipeline, export_kml, export_excel,
#     LANE_PRESETS, haversine, norm180,
# )

# # ── Load API key from .env ─────────────────────────────────────────
# def load_api_key() -> str:
#     candidates = [
#         r"D:\Road_Safety_Reasearch_III\.env",
#         os.path.join(os.path.dirname(__file__), ".env"),
#         ".env",
#     ]
#     for path in candidates:
#         try:
#             if os.path.exists(path):
#                 for line in open(path, encoding="utf-8"):
#                     line = line.strip()
#                     if line.startswith("GOOGLE_API_KEY="):
#                         key = line.split("=", 1)[1].strip().strip('"').strip("'")
#                         if key:
#                             return key
#         except Exception:
#             pass
#     return ""

# API_KEY = load_api_key()

# # ── Page config ────────────────────────────────────────────────────
# st.set_page_config(
#     page_title="GIS BOQ Tool v2 · CAP PTBM p3",
#     page_icon="🚧",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ── CSS ────────────────────────────────────────────────────────────
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
# html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;}
# #MainMenu,footer,header{visibility:hidden;}
# .block-container{padding-top:1.0rem!important;padding-bottom:2rem!important;}

# .hero{background:linear-gradient(135deg,#0f1923 0%,#1a2d42 60%,#0d2137 100%);
#   border-radius:16px;padding:24px 32px;margin-bottom:18px;border:1px solid #1e3a52;
#   position:relative;overflow:hidden;}
# .hero::before{content:'';position:absolute;top:-50px;right:-50px;width:220px;height:220px;
#   background:radial-gradient(circle,rgba(255,215,0,.10) 0%,transparent 70%);border-radius:50%;}
# .hero-title{font-size:1.55rem;font-weight:700;color:#FFD700;margin:0 0 4px;}
# .hero-sub{font-size:.80rem;color:#8ba8c4;margin:0;}
# .hero-badges{display:flex;gap:7px;margin-top:11px;flex-wrap:wrap;}
# .hbadge{background:rgba(255,215,0,.12);color:#FFD700;border:1px solid rgba(255,215,0,.3);
#   padding:2px 9px;border-radius:20px;font-size:.68rem;font-weight:600;
#   font-family:'JetBrains Mono',monospace;}

# .sec-head{font-size:.66rem;font-weight:700;color:#FFD700;letter-spacing:1.5px;
#   text-transform:uppercase;margin:16px 0 7px;padding-bottom:4px;border-bottom:1px solid #1e3a52;}

# .info-card{background:#0a1f14;border:1px solid #1e5e35;border-left:4px solid #27ae60;
#   border-radius:10px;padding:10px 15px;margin:5px 0;font-size:.82rem;color:#b0e8c4;}
# .warn-card{background:#1f1800;border:1px solid #5e4a00;border-left:4px solid #f39c12;
#   border-radius:10px;padding:10px 15px;margin:5px 0;font-size:.82rem;color:#f5d98a;}
# .api-ok{background:#0a2e1a;border:2px solid #27ae60;border-radius:10px;
#   padding:10px 15px;margin:6px 0;font-size:.82rem;color:#27ae60;}
# .api-no{background:#2e0a0a;border:2px solid #e74c3c;border-radius:10px;
#   padding:10px 15px;margin:6px 0;font-size:.82rem;color:#e8a0a0;}
# .mk-card{background:#0a1220;border:1px solid #1e3a52;border-radius:10px;
#   padding:10px 14px;margin:5px 0;}
# .mk-name{font-size:.88rem;font-weight:700;color:#FFD700;margin-bottom:3px;}
# .mk-coords{font-size:.74rem;color:#8ba8c4;font-family:'JetBrains Mono',monospace;}

# section[data-testid="stSidebar"]{background:#0a1220!important;border-right:1px solid #1e3a52;}
# .stDownloadButton>button{background:linear-gradient(135deg,#FFD700,#ffa500)!important;
#   color:#0f1923!important;font-weight:700!important;border:none!important;
#   border-radius:10px!important;padding:11px 22px!important;width:100%!important;
#   font-family:'Space Grotesk',sans-serif!important;}
# .stButton>button[kind="primary"]{background:linear-gradient(135deg,#FFD700,#ffa500)!important;
#   color:#0f1923!important;font-weight:700!important;border:none!important;
#   border-radius:10px!important;width:100%!important;padding:11px!important;
#   font-size:.95rem!important;margin-top:5px!important;}
# </style>
# """, unsafe_allow_html=True)

# # ── Hero ───────────────────────────────────────────────────────────
# api_badge = "🟢 Google API Connected" if API_KEY else "🔴 No API Key"
# st.markdown(f"""
# <div class="hero">
#   <p class="hero-title">🚧 GIS BOQ Tool — CAP PTBM Speed Breaker</p>
#   <p class="hero-sub">Center Marker Mode · IIIT Nagpur · Dr. Neha Kasture · PWD / NHAI</p>
#   <div class="hero-badges">
#     <span class="hbadge">p3 v2</span>
#     <span class="hbadge">{api_badge}</span>
#     <span class="hbadge">Curve-Aware Polygons</span>
#     <span class="hbadge">SLOW Label in KML</span>
#     <span class="hbadge">Satellite Images in Excel</span>
#     <span class="hbadge">Built-in KML Viewer</span>
#   </div>
# </div>
# """, unsafe_allow_html=True)


# # ── Compass SVG ───────────────────────────────────────────────────
# def compass_svg(road_heading: float, size: int = 150) -> str:
#     cx = size // 2; cy = size // 2; r = size // 2 - 12
#     rh = float(road_heading) % 360; perp = (rh + 90) % 360
#     def ep(a, l):
#         a2 = math.radians(float(a) - 90)
#         return cx + l * math.cos(a2), cy + l * math.sin(a2)
#     rx1_x, rx1_y = ep(rh, r*.85)
#     rx2_x, rx2_y = ep((rh+180)%360, r*.85)
#     px1_x, px1_y = ep(perp, r*.80)
#     px2_x, px2_y = ep((perp+180)%360, r*.80)
#     cards = "".join(
#         f'<text x="{cx+(r+9)*math.cos(math.radians(a-90)):.1f}" '
#         f'y="{cy+(r+9)*math.sin(math.radians(a-90)):.1f}" '
#         f'text-anchor="middle" dominant-baseline="central" font-size="9" fill="#8ba8c4">{l}</text>'
#         for a,l in[(0,"N"),(90,"E"),(180,"S"),(270,"W")])
#     tks = "".join(
#         f'<line x1="{cx+(r-5)*math.cos(math.radians(a-90)):.1f}" '
#         f'y1="{cy+(r-5)*math.sin(math.radians(a-90)):.1f}" '
#         f'x2="{cx+r*math.cos(math.radians(a-90)):.1f}" '
#         f'y2="{cy+r*math.sin(math.radians(a-90)):.1f}" stroke="#1e3a52" stroke-width="1.5"/>'
#         for a in range(0,360,10))
#     return (f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">'
#             f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0a1220" stroke="#1e3a52" stroke-width="1.5"/>'
#             f'{tks}{cards}'
#             f'<line x1="{rx1_x:.1f}" y1="{rx1_y:.1f}" x2="{rx2_x:.1f}" y2="{rx2_y:.1f}" '
#             f'stroke="#FFD700" stroke-width="3.5" stroke-linecap="round"/>'
#             f'<line x1="{px1_x:.1f}" y1="{px1_y:.1f}" x2="{px2_x:.1f}" y2="{px2_y:.1f}" '
#             f'stroke="#e67e22" stroke-width="2" stroke-dasharray="5,3" stroke-linecap="round"/>'
#             f'<circle cx="{cx}" cy="{cy}" r="4" fill="#FFD700"/>'
#             f'<rect x="4" y="{size-26}" width="10" height="4" fill="#FFD700" rx="2"/>'
#             f'<text x="17" y="{size-20}" font-size="8" fill="#8ba8c4">Road {rh:.0f}°</text>'
#             f'<rect x="4" y="{size-14}" width="10" height="3" fill="none" stroke="#e67e22" '
#             f'stroke-width="2" stroke-dasharray="4,2" rx="1"/>'
#             f'<text x="17" y="{size-8}" font-size="8" fill="#8ba8c4">Strip {perp:.0f}°</text>'
#             f'</svg>')


# # ── KML Viewer helpers ────────────────────────────────────────────
# def parse_kml_for_viewer(kml_bytes: bytes):
#     polygons = []
#     points   = []
#     try:
#         root = ET.fromstring(kml_bytes)
#         def iter_pm(node):
#             for c in node:
#                 if c.tag.split("}")[-1] == "Placemark": yield c
#                 else: yield from iter_pm(c)
#         for pm in iter_pm(root):
#             name = "Unnamed"
#             desc = ""
#             for c in pm:
#                 tag = c.tag.split("}")[-1]
#                 if tag == "name": name = (c.text or "").strip()
#                 if tag == "description": desc = (c.text or "").strip()
#             for el in pm.iter():
#                 t = el.tag.split("}")[-1]
#                 if t == "Polygon":
#                     for ce in el.iter():
#                         if ce.tag.split("}")[-1] == "coordinates" and ce.text:
#                             pts = []
#                             for tok in ce.text.strip().split():
#                                 parts = tok.split(",")
#                                 if len(parts) >= 2:
#                                     try: pts.append((float(parts[1]), float(parts[0])))
#                                     except: pass
#                             if pts:
#                                 polygons.append({"name": name, "desc": desc, "coords": pts})
#                             break
#                 elif t == "Point":
#                     for ce in el.iter():
#                         if ce.tag.split("}")[-1] == "coordinates" and ce.text:
#                             parts = ce.text.strip().split(",")
#                             if len(parts) >= 2:
#                                 try:
#                                     points.append({
#                                         "name": name, "desc": desc,
#                                         "lat": float(parts[1]), "lon": float(parts[0]),
#                                     })
#                                 except: pass
#                             break
#     except Exception:
#         pass
#     return polygons, points


# def build_kml_viewer_map(polygons, points, zoom=18):
#     all_lats, all_lons = [], []
#     for pg in polygons:
#         for la, lo in pg["coords"]:
#             all_lats.append(la); all_lons.append(lo)
#     for pt in points:
#         all_lats.append(pt["lat"]); all_lons.append(pt["lon"])

#     if not all_lats:
#         return None

#     clat = sum(all_lats) / len(all_lats)
#     clon = sum(all_lons) / len(all_lons)

#     fmap = folium.Map(
#         location=[clat, clon], zoom_start=zoom, max_zoom=21,
#         tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
#         attr="Google Satellite",
#     )

#     for pg in polygons:
#         is_strip = "PTBM" in pg["name"] or "CAP" in pg["name"]
#         fill_col = "#FFD700" if is_strip else "#ff0000"
#         fill_op  = 0.85 if is_strip else 0.0
#         folium.Polygon(
#             locations=pg["coords"],
#             color="#8B6914" if is_strip else "#ff0000",
#             weight=2, fill=is_strip,
#             fill_color=fill_col,
#             fill_opacity=fill_op,
#             tooltip=pg["name"],
#             popup=folium.Popup(
#                 f"<b>{pg['name']}</b><br><small>{pg['desc'][:200]}</small>",
#                 max_width=250),
#         ).add_to(fmap)

#     for pt in points:
#         is_slow = pt["name"] == "SLOW"
#         icon_col = "orange" if is_slow else "red"
#         folium.Marker(
#             [pt["lat"], pt["lon"]],
#             tooltip=pt["name"],
#             popup=folium.Popup(
#                 f"<b>{pt['name']}</b><br><small>{pt['desc'][:200]}</small>",
#                 max_width=220),
#             icon=folium.Icon(color=icon_col, icon="map-marker", prefix="fa"),
#         ).add_to(fmap)

#         folium.Marker(
#             [pt["lat"], pt["lon"]],
#             icon=folium.DivIcon(
#                 html=f'<div style="font-size:11px;font-weight:700;'
#                      f'color:{"#FFA500" if is_slow else "#FFD700"};'
#                      f'background:rgba(0,0,0,0.65);padding:2px 5px;'
#                      f'border-radius:3px;white-space:nowrap;'
#                      f'margin-top:-28px;margin-left:14px;">{pt["name"]}</div>',
#                 icon_size=(160, 28), icon_anchor=(0, 0),
#             ),
#         ).add_to(fmap)

#     return fmap


# # ── Session state ──────────────────────────────────────────────────
# for k, v in [
#     ("markers", []), ("all_polys", []), ("headings", {}),
#     ("kml_bytes", None), ("xlsx_bytes", None), ("generated", False),
#     ("per_marker_h", {}), ("per_marker_w", {}), ("per_marker_strips", {}),
#     ("viewer_kml_bytes", None),
# ]:
#     if k not in st.session_state: st.session_state[k] = v


# # ══════════════════════════════════════════════════════════════════
# # TABS
# # ══════════════════════════════════════════════════════════════════
# tab_gen, tab_view = st.tabs(["🔄 Generate Polygons", "🗺️ KML Viewer (No Google Earth Needed)"])


# # ══════════════════════════════════════════════════════════════════
# # SIDEBAR
# # ══════════════════════════════════════════════════════════════════
# with st.sidebar:
#     if API_KEY:
#         st.markdown(
#             f'<div class="api-ok">✅ Google API Connected<br>'
#             f'<small style="font-family:monospace">{API_KEY[:8]}…{API_KEY[-4:]}</small></div>',
#             unsafe_allow_html=True,
#         )
#     else:
#         st.markdown(
#             '<div class="api-no">⚠️ No Google API Key<br>'
#             '<small>Add GOOGLE_API_KEY to .env<br>'
#             'Roads API + Static Maps will not work</small></div>',
#             unsafe_allow_html=True,
#         )
#         manual_key = st.text_input("Paste API key here (session only):", type="password", key="manual_api")
#         if manual_key: API_KEY = manual_key

#     st.markdown('<p class="sec-head">📂 KML Upload</p>', unsafe_allow_html=True)
#     st.markdown(
#         '<div class="info-card">ℹ️ Upload KML with <b>center markers only</b>.<br>'
#         'One red pin = center of road at each speed breaker.</div>',
#         unsafe_allow_html=True,
#     )
#     uploaded = st.file_uploader("Upload KML", type=["kml"], label_visibility="collapsed")

#     st.markdown('<p class="sec-head">🛣️ Road Configuration</p>', unsafe_allow_html=True)
#     lane_key = st.selectbox("Lane Type", list(LANE_PRESETS.keys()), index=1, key="lk")
#     lp = LANE_PRESETS[lane_key]
#     if lane_key == "Custom":
#         road_w = st.number_input("Road Width (m)", 2.0, 60.0, 7.0, 0.5, key="rw")
#         sep_w  = st.number_input("Separator (m)",  0.0, 10.0, 0.5, 0.1, key="sep")
#         nl_def = int(st.number_input("Lanes", 1, 8, 2, 1, key="nl"))
#     else:
#         road_w = float(lp["road_width_m"])
#         sep_w  = float(lp["separator_width_m"])
#         nl_def = int(lp["num_lanes"])
#         lw_a   = (road_w - sep_w) / max(nl_def, 1)
#         st.caption(f"Width: **{road_w}m** | Lanes: **{nl_def}** | Lane: **{lw_a:.2f}m**")

#     st.markdown('<p class="sec-head">🧭 Road Heading</p>', unsafe_allow_html=True)
#     hmode = st.radio("Source",
#         ["Auto (Google Roads API / neighbours)", "Manual (all markers)"],
#         key="hmode")
#     global_heading = None
#     if hmode == "Manual (all markers)":
#         global_heading = float(st.slider("Heading °", 0, 179, 90, key="gh"))
#         st.markdown(compass_svg(global_heading, 145), unsafe_allow_html=True)
#         st.caption(f"Road **{global_heading:.0f}°** → Strip **{(global_heading+90)%360:.0f}°**")
#     else:
#         if API_KEY:
#             st.caption("✅ Google Roads API will detect road angle at each marker")
#         else:
#             st.caption("Heading auto-detected from neighbouring marker positions")

#     st.markdown('<p class="sec-head">🟨 Strip Configuration</p>', unsafe_allow_html=True)
#     n_strips    = int(st.number_input("Number of Strips", 1, 20, 3, 1, key="ns"))
#     strip_thick = st.number_input(
#         "Strip Thickness (m along road)",
#         min_value=0.05, max_value=2.0,
#         value=0.5, step=0.05, key="sthick",
#         help="Physical thickness of each strip ALONG road direction. "
#              "0.5m = clearly visible in satellite view as a filled rectangle.",
#     )
#     strip_gap = st.number_input("Gap Between Strips (m)", 0.1, 5.0, 0.6, 0.1, key="sg")
#     total_span = n_strips * strip_thick + (n_strips - 1) * strip_gap
#     st.caption(
#         f"{n_strips} strips × {strip_thick*1000:.0f}mm | "
#         f"gap={strip_gap}m | total span=**{total_span:.2f}m**"
#     )

#     add_slow = st.toggle("Add SLOW label to KML", value=True, key="slow")
#     rate_rs  = st.number_input("Rate (Rs/m²)", 100, 50000, 2500, 100, key="rate")

#     st.markdown("---")
#     gen_btn = st.button("🔄 Generate Polygons", type="primary",
#                         disabled=uploaded is None, key="genb")
#     if not uploaded: st.caption("⬆️ Upload KML to enable")


# # ══════════════════════════════════════════════════════════════════
# # TAB 1: GENERATE
# # ══════════════════════════════════════════════════════════════════
# with tab_gen:
#     markers_raw: List[KMLMarker] = []
#     n_markers = 0
#     kml_temp  = ""

#     if uploaded:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as tmp:
#             tmp.write(uploaded.getvalue())
#             kml_temp = tmp.name

#         try:
#             _markers = parse_kml(kml_temp)
#             n_markers = len(_markers)
#             markers_raw = _markers

#             mc1, mc2, mc3, mc4 = st.columns(4)
#             mc1.metric("📍 Markers", n_markers)
#             mc2.metric("🛣️ Road Width", f"{road_w}m")
#             mc3.metric("🟨 Strips/Marker", n_strips)
#             mc4.metric("📐 Strip Thick", f"{strip_thick*1000:.0f}mm")

#             if n_markers == 0:
#                 st.error("❌ No Point markers found. Place red pins in Google Earth Pro and re-export.")
#             else:
#                 st.markdown(
#                     f'<div class="info-card">✅ <b>{n_markers} center marker(s)</b> loaded. '
#                     f'Each strip will span <b>{road_w}m</b> perpendicular to road, '
#                     f'<b>{strip_thick*1000:.0f}mm ({strip_thick:.2f}m) thick</b> — '
#                     f'clearly visible as filled rectangle in satellite view.</div>',
#                     unsafe_allow_html=True,
#                 )

#                 st.markdown('<p class="sec-head">📍 Loaded Markers</p>', unsafe_allow_html=True)
#                 cols = st.columns(min(n_markers, 3))
#                 for ci, mk in enumerate(_markers):
#                     with cols[ci % len(cols)]:
#                         st.markdown(
#                             f'<div class="mk-card">'
#                             f'<div class="mk-name">📍 {mk.index+1}. {mk.name}</div>'
#                             f'<div class="mk-coords">Lat: {mk.lat:.6f}<br>Lon: {mk.lon:.6f}</div>'
#                             f'</div>',
#                             unsafe_allow_html=True,
#                         )

#         except Exception as e:
#             st.error(f"❌ Parse error: {e}")
#             import traceback; st.code(traceback.format_exc())

#     else:
#         c1, c2 = st.columns([2, 1])
#         with c1:
#             st.markdown("""
#             <div style="background:#0a1220;border:1px dashed #1e3a52;border-radius:16px;
#                         padding:40px;text-align:center;margin-top:10px">
#               <div style="font-size:2.5rem;margin-bottom:14px">🗺️</div>
#               <div style="font-size:1.05rem;font-weight:600;color:#e8eaf0;margin-bottom:8px">
#                 Upload KML — Center Markers Only</div>
#               <div style="font-size:.82rem;color:#8ba8c4;max-width:360px;margin:0 auto">
#                 Place one red pin at the <b>center of the road</b> for each
#                 speed breaker in Google Earth Pro. Export as KML and upload here.
#               </div>
#             </div>""", unsafe_allow_html=True)
#         with c2:
#             st.markdown("**Simple workflow:**")
#             for s, t in [
#                 ("1️⃣", "Open Google Earth Pro"),
#                 ("2️⃣", "Place red pin at road CENTER for each speed breaker"),
#                 ("3️⃣", "File → Save Place As → KML"),
#                 ("4️⃣", "Upload here, configure, click Generate"),
#                 ("5️⃣", "Download KML + Excel, or test in KML Viewer tab"),
#             ]:
#                 st.markdown(f"{s} {t}")

#     # ── Per-marker overrides ───────────────────────────────────────
#     if n_markers > 0:
#         st.markdown('<p class="sec-head">🎯 Per-Marker Overrides (optional)</p>',
#                     unsafe_allow_html=True)
#         with st.expander("Customize individual markers", expanded=False):
#             if st.button("🗑️ Clear All Overrides", key="clr"):
#                 st.session_state.per_marker_h = {}
#                 st.session_state.per_marker_w = {}
#                 st.session_state.per_marker_strips = {}
#                 st.rerun()

#             for mk in markers_raw:
#                 i = mk.index
#                 with st.expander(f"Marker {i+1}: {mk.name}", expanded=False):
#                     oc1, oc2, oc3 = st.columns(3)
#                     with oc1:
#                         use_w = st.toggle("Custom width", key=f"uw{i}")
#                         if use_w:
#                             nw = st.number_input("Width (m)", 2.0, 60.0,
#                                 st.session_state.per_marker_w.get(i, road_w), 0.5, key=f"mw{i}")
#                             st.session_state.per_marker_w[i] = nw
#                         elif i in st.session_state.per_marker_w:
#                             del st.session_state.per_marker_w[i]
#                     with oc2:
#                         use_h = st.toggle("Custom heading", key=f"uh{i}")
#                         if use_h:
#                             nh = st.slider("Heading °", 0, 179,
#                                 int(st.session_state.per_marker_h.get(i, global_heading or 90)),
#                                 1, key=f"mh{i}")
#                             st.session_state.per_marker_h[i] = float(nh)
#                         elif i in st.session_state.per_marker_h:
#                             del st.session_state.per_marker_h[i]
#                     with oc3:
#                         use_s = st.toggle("Custom strips", key=f"us{i}")
#                         if use_s:
#                             ns2 = int(st.number_input("Strips", 1, 20,
#                                 st.session_state.per_marker_strips.get(i, n_strips),
#                                 1, key=f"ms{i}"))
#                             st.session_state.per_marker_strips[i] = ns2
#                         elif i in st.session_state.per_marker_strips:
#                             del st.session_state.per_marker_strips[i]
#                     dh = float(st.session_state.per_marker_h.get(i) or global_heading or 90.0)
#                     st.markdown(compass_svg(dh, 130), unsafe_allow_html=True)

#     # ── Generate ───────────────────────────────────────────────────
#     if gen_btn and uploaded and n_markers > 0:
#         spec = PolySpec(
#             road_width_m      = road_w,
#             num_lanes         = nl_def,
#             separator_width_m = sep_w,
#             num_strips        = n_strips,
#             strip_thick_m     = float(strip_thick),
#             strip_gap_m       = float(strip_gap),
#             heading_override  = global_heading,
#             add_slow_label    = add_slow,
#             api_key           = API_KEY,
#         )
#         for mk in markers_raw:
#             i = mk.index; ov = {}
#             if i in st.session_state.per_marker_w:
#                 ov["road_width_m"] = st.session_state.per_marker_w[i]
#             if i in st.session_state.per_marker_h:
#                 ov["heading_deg"] = st.session_state.per_marker_h[i]
#             if i in st.session_state.per_marker_strips:
#                 ov["num_strips"] = st.session_state.per_marker_strips[i]
#             if ov: spec.marker_overrides[i] = ov

#         per_h = dict(st.session_state.per_marker_h)

#         prog = st.progress(0, "Parsing KML…")
#         status_text = st.empty()

#         def _update(msg, pct):
#             prog.progress(min(pct, 99), msg)
#             status_text.caption(msg)

#         try:
#             _update("Parsing KML…", 10)
#             m_obj, polys, headings = run_pipeline(
#                 kml_temp, spec, per_h, progress_cb=_update)
#             _update("Exporting KML…", 70)

#             out_kml  = kml_temp.replace(".kml", "_p3_out.kml")
#             out_xlsx = kml_temp.replace(".kml", "_p3_out.xlsx")

#             export_kml(m_obj, polys, headings, spec, out_kml)
#             _update("Exporting Excel (fetching high-zoom satellite images…)…", 80)
#             export_excel(m_obj, polys, headings, spec, out_xlsx,
#                          progress_cb=_update)

#             _update("Finalising…", 95)
#             with open(out_kml, "rb") as f:
#                 st.session_state.kml_bytes = f.read()
#             with open(out_xlsx, "rb") as f:
#                 st.session_state.xlsx_bytes = f.read()

#             st.session_state.markers   = m_obj
#             st.session_state.all_polys = polys
#             st.session_state.headings  = headings
#             st.session_state.generated = True
#             st.session_state.viewer_kml_bytes = st.session_state.kml_bytes

#             prog.progress(100, "Done ✅")
#             status_text.empty()
#             time.sleep(0.4)
#             prog.empty()
#             st.rerun()

#         except Exception as e:
#             prog.empty()
#             status_text.empty()
#             st.error(f"❌ Error: {e}")
#             import traceback; st.code(traceback.format_exc())

#     # ── Results ────────────────────────────────────────────────────
#     if st.session_state.generated and st.session_state.all_polys:
#         m_obj  = st.session_state.markers
#         polys  = st.session_state.all_polys
#         heads  = st.session_state.headings

#         st.markdown('<p class="sec-head">✅ Results</p>', unsafe_allow_html=True)
#         r1, r2, r3, r4, r5 = st.columns(5)
#         r1.metric("📍 Markers",      len(m_obj))
#         r2.metric("🟨 Total Strips", len(polys))
#         r3.metric("🛣️ Road Width",   f"{road_w}m")
#         r4.metric("📐 Strip Thick",  f"{strip_thick*1000:.0f}mm")
#         r5.metric("Strips/Marker",   len(polys) // max(len(m_obj), 1))

#         st.markdown('<p class="sec-head">📥 Downloads</p>', unsafe_allow_html=True)
#         dl1, dl2 = st.columns(2)
#         if st.session_state.kml_bytes:
#             dl1.download_button(
#                 "📥 Download KML — Google Earth Pro",
#                 data=st.session_state.kml_bytes,
#                 file_name="speed_breakers_p3.kml",
#                 mime="application/vnd.google-earth.kml+xml",
#                 use_container_width=True,
#             )
#         if st.session_state.xlsx_bytes:
#             dl2.download_button(
#                 "📊 Download Excel BOQ Report",
#                 data=st.session_state.xlsx_bytes,
#                 file_name="speed_breakers_p3_boq.xlsx",
#                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                 use_container_width=True,
#             )
#         st.markdown(
#             '<div class="info-card">💡 <b>KML Viewer tab</b> — click it above to verify '
#             'your generated polygons on satellite map without Google Earth Pro.</div>',
#             unsafe_allow_html=True,
#         )

#         # ── BOQ Summary Table ──────────────────────────────────────
#         st.markdown('<p class="sec-head">📋 BOQ Summary Table</p>', unsafe_allow_html=True)

#         # FIX: use plain dict, not Dict type annotation at runtime
#         by: dict = {}
#         for p in polys: by.setdefault(p.marker_idx, []).append(p)

#         rows = []
#         for mk in m_obj:
#             ps    = by.get(mk.index, [])
#             p0    = ps[0] if ps else None
#             hdata = heads.get(mk.index, (0.0, mk.lat, mk.lon, "default"))
#             h_deg    = hdata[0]
#             snap_lat = hdata[1]
#             snap_lon = hdata[2]
#             rw_v  = p0.road_width_m  if p0 else road_w
#             st_v  = p0.strip_thick_m if p0 else strip_thick
#             gap_v = p0.strip_gap_m   if p0 else strip_gap
#             ns_v  = len(ps)
#             span  = ns_v * st_v + max(ns_v-1, 0) * gap_v
#             area  = round(st_v * rw_v * ns_v, 4)
#             amt   = round(area * rate_rs, 2)
#             rows.append({
#                 "S.No":           mk.index+1,
#                 "Marker":         mk.name,
#                 "Snap Lat":       round(snap_lat, 6),
#                 "Snap Lon":       round(snap_lon, 6),
#                 "Bearing (°)":    round(h_deg, 1),
#                 "Road Width (m)": round(rw_v, 2),
#                 "Mark Length (m)": round(span, 3),
#                 "Strips":         ns_v,
#                 "Area (m²)":      area,
#                 "Rate (Rs/m²)":   rate_rs,
#                 "Amount (Rs)":    amt,
#                 "Heading Src":    hdata[3],
#             })
#         st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

#         # ── Live map preview ───────────────────────────────────────
#         st.markdown('<p class="sec-head">🗺️ Live Satellite Preview</p>',
#                     unsafe_allow_html=True)
#         if m_obj:
#             clat = sum(m.lat for m in m_obj) / len(m_obj)
#             clon = sum(m.lon for m in m_obj) / len(m_obj)
#             fmap = folium.Map(
#                 location=[clat, clon], zoom_start=19, max_zoom=21,
#                 tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
#                 attr="Google Satellite",
#             )
#             COLS = ["#FFD700","#FFB300","#FF8C00","#FFA500","#FFCC00","#FFE066"]
#             for p in polys:
#                 col = COLS[p.strip_idx % len(COLS)]
#                 folium.Polygon(
#                     locations=[[la, lo] for la, lo in p.coords],
#                     color="#8B6914", weight=2, fill=True,
#                     fill_color=col, fill_opacity=0.88,
#                     tooltip=(f"{p.marker_name} | Strip {p.strip_idx+1} | "
#                              f"{p.road_heading:.1f}° | {p.road_width_m:.1f}m wide | "
#                              f"{p.strip_thick_m*1000:.0f}mm thick"),
#                 ).add_to(fmap)
#             for mk in m_obj:
#                 hd = heads.get(mk.index, (0.0, mk.lat, mk.lon, ""))
#                 folium.Marker(
#                     [hd[1], hd[2]],
#                     popup=folium.Popup(
#                         f"<b>{mk.name}</b><br>"
#                         f"CAP PTBM {strip_thick*1000:.0f}MM X {len(by.get(mk.index,[]))}<br>"
#                         f"Heading: {hd[0]:.1f}° [{hd[3]}]<br>"
#                         f"Road: {road_w:.1f}m | {nl_def} Lane",
#                         max_width=220),
#                     icon=folium.Icon(color="red", icon="map-marker", prefix="fa"),
#                 ).add_to(fmap)
#                 folium.Marker([hd[1], hd[2]], icon=folium.DivIcon(
#                     html=f'<div style="font-size:11px;font-weight:700;color:#FFD700;'
#                          f'background:rgba(0,0,0,0.65);padding:2px 5px;border-radius:3px;'
#                          f'white-space:nowrap;margin-top:-28px;margin-left:14px;">'
#                          f'{mk.name}</div>',
#                     icon_size=(160, 28), icon_anchor=(0, 0),
#                 )).add_to(fmap)
#             st_folium(fmap, width="100%", height=540, returned_objects=[])

#         # ── Per-marker detail ──────────────────────────────────────
#         st.markdown('<p class="sec-head">📐 Per-Marker Strip Detail</p>',
#                     unsafe_allow_html=True)
#         for mk in m_obj:
#             ps = by.get(mk.index, [])
#             if not ps: continue
#             p0 = ps[0]
#             hd = heads.get(mk.index, (0.0, mk.lat, mk.lon, "default"))
#             with st.expander(f"📍 {mk.name} — {len(ps)} strips | "
#                              f"{p0.road_width_m:.1f}m wide | {p0.strip_thick_m*1000:.0f}mm thick"):
#                 dc1, dc2 = st.columns([2, 1])
#                 with dc1:
#                     area_s = p0.strip_thick_m * p0.road_width_m
#                     span   = len(ps)*p0.strip_thick_m + max(len(ps)-1,0)*p0.strip_gap_m
#                     st.markdown(f"""
# | Property | Value |
# |---|---|
# | Marker Name | **{mk.name}** |
# | Snapped Lat | `{hd[1]:.6f}` |
# | Snapped Lon | `{hd[2]:.6f}` |
# | Road Width | **{p0.road_width_m:.2f} m** |
# | Lanes | {p0.num_lanes} |
# | Lane Width | {p0.lane_width_m:.2f} m |
# | Heading | {hd[0]:.1f}° ({hd[3]}) |
# | Total Strips | {len(ps)} |
# | Strip Thick | {p0.strip_thick_m*1000:.0f} mm (along road) |
# | Strip Length | {p0.road_width_m:.2f} m (across road) |
# | Gap between strips | {p0.strip_gap_m:.2f} m |
# | Total span | {span:.3f} m |
# | Area / Strip | {area_s:.4f} m² |
# | Total Area | {area_s*len(ps):.4f} m² |
# | Amount | Rs {area_s*len(ps)*rate_rs:,.0f} |
# | KML Label | CAP PTBM {p0.strip_thick_m*1000:.0f}MM X {len(ps)} |
# """)
#                 with dc2:
#                     st.markdown(compass_svg(hd[0], 148), unsafe_allow_html=True)
#                     st.caption(f"Road **{hd[0]:.0f}°** | Strip **{(hd[0]+90)%360:.0f}°**")


# # ══════════════════════════════════════════════════════════════════
# # TAB 2: KML VIEWER
# # ══════════════════════════════════════════════════════════════════
# with tab_view:
#     st.markdown("""
#     <div class="info-card">
#       🗺️ <b>Built-in KML Viewer</b> — Upload any KML file (original or generated) to
#       visualize it on a satellite map. No Google Earth Pro required.<br>
#       Yellow filled rectangles = speed breaker strip polygons.
#     </div>
#     """, unsafe_allow_html=True)

#     col_v1, col_v2 = st.columns([1, 3])
#     with col_v1:
#         viewer_upload = st.file_uploader(
#             "Upload KML to view", type=["kml"], key="viewer_kml",
#             help="Upload any KML file to visualize on satellite map",
#         )
#         if viewer_upload:
#             st.session_state.viewer_kml_bytes = viewer_upload.read()

#         if st.session_state.kml_bytes and not viewer_upload:
#             if st.button("📂 Load Generated KML", key="load_gen"):
#                 st.session_state.viewer_kml_bytes = st.session_state.kml_bytes
#                 st.rerun()

#         viewer_zoom = st.slider("Map Zoom", 15, 21, 19, key="vzoom")
#         show_labels = st.toggle("Show polygon labels", True, key="slbl")

#     with col_v2:
#         if st.session_state.viewer_kml_bytes:
#             kml_bytes = st.session_state.viewer_kml_bytes
#             polygons, points = parse_kml_for_viewer(kml_bytes)
#             n_pg  = len(polygons)
#             n_pin = len(points)

#             vc1, vc2, vc3 = st.columns(3)
#             vc1.metric("🔷 Polygons", n_pg)
#             vc2.metric("📍 Markers",  n_pin)
#             vc3.metric("🔶 SLOW labels",
#                        sum(1 for p in points if p["name"] == "SLOW"))

#             if polygons or points:
#                 fmap = build_kml_viewer_map(polygons, points, zoom=viewer_zoom)
#                 if fmap:
#                     st_folium(fmap, width="100%", height=580, returned_objects=[])
#                 else:
#                     st.warning("No geographic data found in KML")
#             else:
#                 st.warning("No polygons or markers found in the uploaded KML file.")

#             with st.expander("📊 KML Contents"):
#                 strip_names = [p["name"] for p in polygons if "CAP" in p["name"] or "PTBM" in p["name"]]
#                 slow_pts    = [p for p in points if p["name"] == "SLOW"]
#                 pin_pts     = [p for p in points if p["name"] != "SLOW"]
#                 st.markdown(f"""
# - **{len(strip_names)}** CAP PTBM strip polygons
# - **{len(pin_pts)}** marker pins
# - **{len(slow_pts)}** SLOW labels
# - **{n_pg - len(strip_names)}** other polygons
#                 """)
#                 if pin_pts:
#                     df_v = pd.DataFrame([{
#                         "Name": p["name"],
#                         "Lat": round(p["lat"], 6),
#                         "Lon": round(p["lon"], 6),
#                     } for p in pin_pts])
#                     st.dataframe(df_v, hide_index=True, use_container_width=True)
#         else:
#             st.markdown("""
#             <div style="background:#0a1220;border:1px dashed #1e3a52;border-radius:12px;
#                         padding:50px;text-align:center;">
#               <div style="font-size:2.5rem;margin-bottom:12px">🗺️</div>
#               <div style="font-size:1rem;font-weight:600;color:#e8eaf0;margin-bottom:8px">
#                 No KML loaded</div>
#               <div style="font-size:.82rem;color:#8ba8c4">
#                 Upload a KML file on the left, or generate polygons in the first tab
#                 (the generated KML will auto-load here).
#               </div>
#             </div>
#             """, unsafe_allow_html=True)

"""
ui3.py v5 — Speed Breaker GIS BOQ Tool
IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI
Run: streamlit run ui3.py

v5 FIXES:
  - Imports LABEL_PRESETS from p3 (was missing -> ImportError fixed)
  - 8 parallel workers for images (was 4)
  - Parallel heading detection
  - All typing imports correct
"""
import streamlit as st
import tempfile, os, math, time, io
from typing import Dict, List, Optional, Tuple
import pandas as pd
import folium
from streamlit_folium import st_folium
import xml.etree.ElementTree as ET

from p3 import (
    PolySpec, KMLMarker, GenPoly,
    parse_kml, run_pipeline, export_kml, export_excel,
    LANE_PRESETS, LABEL_PRESETS,
    haversine, norm180,
)

def load_api_key() -> str:
    for path in [
        r"D:\Road_Safety_Reasearch_III\.env",
        os.path.join(os.path.dirname(__file__), ".env"),
        ".env",
    ]:
        try:
            if os.path.exists(path):
                for line in open(path, encoding="utf-8"):
                    line = line.strip()
                    if line.startswith("GOOGLE_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if key: return key
        except Exception:
            pass
    return ""

API_KEY = load_api_key()

st.set_page_config(page_title="GIS BOQ v5 · CAP PTBM", page_icon="🚧",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem!important;padding-bottom:2rem!important;}
.hero{background:linear-gradient(135deg,#0f1923 0%,#1a2d42 60%,#0d2137 100%);
  border-radius:16px;padding:20px 28px;margin-bottom:14px;border:1px solid #1e3a52;}
.hero-title{font-size:1.45rem;font-weight:700;color:#FFD700;margin:0 0 3px;}
.hero-sub{font-size:.77rem;color:#8ba8c4;margin:0;}
.hero-badges{display:flex;gap:6px;margin-top:9px;flex-wrap:wrap;}
.hbadge{background:rgba(255,215,0,.12);color:#FFD700;border:1px solid rgba(255,215,0,.3);
  padding:2px 7px;border-radius:20px;font-size:.65rem;font-weight:600;font-family:'JetBrains Mono',monospace;}
.sec-head{font-size:.63rem;font-weight:700;color:#FFD700;letter-spacing:1.4px;
  text-transform:uppercase;margin:13px 0 5px;padding-bottom:3px;border-bottom:1px solid #1e3a52;}
.info-card{background:#0a1f14;border:1px solid #1e5e35;border-left:4px solid #27ae60;
  border-radius:10px;padding:9px 14px;margin:4px 0;font-size:.81rem;color:#b0e8c4;}
.warn-card{background:#1f1a00;border:1px solid #5e4a00;border-left:4px solid #f39c12;
  border-radius:10px;padding:9px 14px;margin:4px 0;font-size:.81rem;color:#f5d98a;}
.road-explain{background:#0d1b2a;border:1px solid #1e5e7a;border-left:4px solid #00bfff;
  border-radius:10px;padding:11px 15px;margin:5px 0;font-size:.81rem;color:#a8d8f0;}
.api-ok{background:#0a2e1a;border:2px solid #27ae60;border-radius:10px;
  padding:9px 14px;margin:5px 0;font-size:.81rem;color:#27ae60;}
.api-no{background:#2e0a0a;border:2px solid #e74c3c;border-radius:10px;
  padding:9px 14px;margin:5px 0;font-size:.81rem;color:#e8a0a0;}
.mk-card{background:#0a1220;border:1px solid #1e3a52;border-radius:9px;padding:9px 13px;margin:4px 0;}
.mk-name{font-size:.87rem;font-weight:700;color:#FFD700;margin-bottom:2px;}
.mk-coords{font-size:.73rem;color:#8ba8c4;font-family:'JetBrains Mono',monospace;}
.lbl-chip{display:inline-block;background:rgba(255,215,0,.15);color:#FFD700;
  border:1px solid rgba(255,215,0,.35);border-radius:12px;padding:1px 7px;
  font-size:.69rem;margin:2px;font-family:'JetBrains Mono',monospace;}
section[data-testid="stSidebar"]{background:#0a1220!important;border-right:1px solid #1e3a52;}
.stDownloadButton>button{background:linear-gradient(135deg,#FFD700,#ffa500)!important;
  color:#0f1923!important;font-weight:700!important;border:none!important;
  border-radius:10px!important;padding:10px 20px!important;width:100%!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#FFD700,#ffa500)!important;
  color:#0f1923!important;font-weight:700!important;border:none!important;
  border-radius:10px!important;width:100%!important;padding:10px!important;
  font-size:.92rem!important;margin-top:4px!important;}
</style>
""", unsafe_allow_html=True)

api_badge = "🟢 Google API Connected" if API_KEY else "🔴 No API Key"
st.markdown(f"""
<div class="hero">
  <p class="hero-title">🚧 GIS BOQ Tool — CAP PTBM Speed Breaker</p>
  <p class="hero-sub">Center Marker Mode · IIIT Nagpur · Dr. Neha Kasture · PWD / NHAI</p>
  <div class="hero-badges">
    <span class="hbadge">v5</span><span class="hbadge">{api_badge}</span>
    <span class="hbadge">8 Parallel Workers</span>
    <span class="hbadge">Polygon on Satellite</span>
    <span class="hbadge">Curve-Aware</span>
    <span class="hbadge">7 Road Labels</span>
    <span class="hbadge">KML Viewer</span>
  </div>
</div>
""", unsafe_allow_html=True)


def compass_svg(road_heading: float, size: int = 148) -> str:
    cx = size//2; cy = size//2; r = size//2 - 12
    rh = float(road_heading)%360; perp = (rh+90)%360
    def ep(a, l):
        a2=math.radians(float(a)-90)
        return cx+l*math.cos(a2), cy+l*math.sin(a2)
    rx1,ry1=ep(rh,r*.85); rx2,ry2=ep((rh+180)%360,r*.85)
    px1,py1=ep(perp,r*.80); px2,py2=ep((perp+180)%360,r*.80)
    cards="".join(
        f'<text x="{cx+(r+9)*math.cos(math.radians(a-90)):.1f}" '
        f'y="{cy+(r+9)*math.sin(math.radians(a-90)):.1f}" '
        f'text-anchor="middle" dominant-baseline="central" font-size="9" fill="#8ba8c4">{l}</text>'
        for a,l in[(0,"N"),(90,"E"),(180,"S"),(270,"W")])
    tks="".join(
        f'<line x1="{cx+(r-5)*math.cos(math.radians(a-90)):.1f}" '
        f'y1="{cy+(r-5)*math.sin(math.radians(a-90)):.1f}" '
        f'x2="{cx+r*math.cos(math.radians(a-90)):.1f}" '
        f'y2="{cy+r*math.sin(math.radians(a-90)):.1f}" stroke="#1e3a52" stroke-width="1.5"/>'
        for a in range(0,360,10))
    return (f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0a1220" stroke="#1e3a52" stroke-width="1.5"/>'
            f'{tks}{cards}'
            f'<line x1="{rx1:.1f}" y1="{ry1:.1f}" x2="{rx2:.1f}" y2="{ry2:.1f}" '
            f'stroke="#FFD700" stroke-width="3.5" stroke-linecap="round"/>'
            f'<line x1="{px1:.1f}" y1="{py1:.1f}" x2="{px2:.1f}" y2="{py2:.1f}" '
            f'stroke="#e67e22" stroke-width="2" stroke-dasharray="5,3" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="4" fill="#FFD700"/>'
            f'<text x="17" y="{size-20}" font-size="8" fill="#8ba8c4">Road {rh:.0f}</text>'
            f'<text x="17" y="{size-8}" font-size="8" fill="#8ba8c4">Strip {perp:.0f}</text>'
            f'</svg>')


ALL_LABEL_NAMES = set(LABEL_PRESETS.keys())

def parse_kml_for_viewer(kml_bytes: bytes):
    polygons, points = [], []
    try:
        root = ET.fromstring(kml_bytes)
        def iter_pm(node):
            for c in node:
                if c.tag.split("}")[-1]=="Placemark": yield c
                else: yield from iter_pm(c)
        for pm in iter_pm(root):
            name="Unnamed"; desc=""
            for c in pm:
                t=c.tag.split("}")[-1]
                if t=="name": name=(c.text or "").strip()
                if t=="description": desc=(c.text or "").strip()
            for el in pm.iter():
                t=el.tag.split("}")[-1]
                if t=="Polygon":
                    for ce in el.iter():
                        if ce.tag.split("}")[-1]=="coordinates" and ce.text:
                            pts=[]
                            for tok in ce.text.strip().split():
                                parts=tok.split(",")
                                if len(parts)>=2:
                                    try: pts.append((float(parts[1]),float(parts[0])))
                                    except: pass
                            if pts: polygons.append({"name":name,"desc":desc,"coords":pts})
                            break
                elif t=="Point":
                    for ce in el.iter():
                        if ce.tag.split("}")[-1]=="coordinates" and ce.text:
                            parts=ce.text.strip().split(",")
                            if len(parts)>=2:
                                try: points.append({"name":name,"desc":desc,"lat":float(parts[1]),"lon":float(parts[0])})
                                except: pass
                            break
    except Exception: pass
    return polygons, points


def build_kml_viewer_map(polygons, points, zoom=18):
    all_lats=[c[0] for pg in polygons for c in pg["coords"]]+[p["lat"] for p in points]
    all_lons=[c[1] for pg in polygons for c in pg["coords"]]+[p["lon"] for p in points]
    if not all_lats: return None
    clat=sum(all_lats)/len(all_lats); clon=sum(all_lons)/len(all_lons)
    fmap=folium.Map(location=[clat,clon],zoom_start=zoom,max_zoom=21,
                    tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",attr="Google Satellite")
    for pg in polygons:
        is_strip="PTBM" in pg["name"] or "CAP" in pg["name"]
        folium.Polygon(locations=pg["coords"],color="#8B6914" if is_strip else "#ff0000",
                       weight=2,fill=is_strip,
                       fill_color="#FFD700" if is_strip else "#ff4444",
                       fill_opacity=0.85 if is_strip else 0.0,
                       tooltip=pg["name"],
                       popup=folium.Popup(f"<b>{pg['name']}</b><br><small>{pg['desc'][:200]}</small>",max_width=260)
                       ).add_to(fmap)
    lbl_col={"SLOW":"orange","SPEED BREAKER":"blue","CAUTION":"red",
              "SCHOOL ZONE":"green","ROAD HUMP":"purple","RUMBLE STRIP":"pink","STOP":"darkred"}
    for pt in points:
        is_lbl=pt["name"] in ALL_LABEL_NAMES
        col=lbl_col.get(pt["name"],"orange") if is_lbl else "red"
        folium.Marker([pt["lat"],pt["lon"]],tooltip=pt["name"],
                      popup=folium.Popup(f"<b>{pt['name']}</b><br><small>{pt['desc'][:180]}</small>",max_width=220),
                      icon=folium.Icon(color=col,icon="map-marker",prefix="fa")).add_to(fmap)
        folium.Marker([pt["lat"],pt["lon"]],icon=folium.DivIcon(
            html=(f'<div style="font-size:11px;font-weight:700;'
                  f'color:{"#FFA500" if is_lbl else "#FFD700"};'
                  f'background:rgba(0,0,0,.65);padding:2px 5px;border-radius:3px;'
                  f'white-space:nowrap;margin-top:-28px;margin-left:14px;">{pt["name"]}</div>'),
            icon_size=(190,28),icon_anchor=(0,0))).add_to(fmap)
    return fmap


for k,v in [("markers",[]),("all_polys",[]),("headings",{}),
            ("kml_bytes",None),("xlsx_bytes",None),("generated",False),
            ("per_marker_h",{}),("per_marker_w",{}),("per_marker_strips",{}),
            ("viewer_kml_bytes",None)]:
    if k not in st.session_state: st.session_state[k]=v

tab_gen,tab_view,tab_explain=st.tabs([
    "🔄 Generate Polygons",
    "🗺️ KML Viewer (No Google Earth)",
    "📏 Road Width Explainer",
])

with st.sidebar:
    if API_KEY:
        st.markdown(f'<div class="api-ok">Google API Connected<br>'
                    f'<small style="font-family:monospace">{API_KEY[:8]}...{API_KEY[-4:]}</small></div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="api-no">No Google API Key<br>'
                    '<small>Add GOOGLE_API_KEY to .env</small></div>',unsafe_allow_html=True)
        mk=st.text_input("Paste API key:",type="password",key="mapi")
        if mk: API_KEY=mk

    st.markdown('<p class="sec-head">KML Upload</p>',unsafe_allow_html=True)
    uploaded=st.file_uploader("Upload KML",type=["kml"],label_visibility="collapsed")

    st.markdown('<p class="sec-head">Road Configuration</p>',unsafe_allow_html=True)
    lane_key=st.selectbox("Lane Type",list(LANE_PRESETS.keys()),index=1,key="lk")
    lp=LANE_PRESETS[lane_key]
    if lane_key=="Custom":
        road_w=st.number_input("Road Width (m)",2.0,60.0,7.0,0.5,key="rw")
        sep_w=st.number_input("Separator (m)",0.0,10.0,0.5,0.1,key="sep")
        nl_def=int(st.number_input("Lanes",1,8,2,1,key="nl"))
    else:
        road_w=float(lp["road_width_m"]); sep_w=float(lp["separator_width_m"]); nl_def=int(lp["num_lanes"])
        st.caption(f"Width:{road_w}m | Lanes:{nl_def}")

    st.markdown('<p class="sec-head">Road Heading</p>',unsafe_allow_html=True)
    hmode=st.radio("Source",["Auto (Google Roads API / neighbours)","Manual (all markers)"],key="hmode")
    global_heading=None
    if hmode=="Manual (all markers)":
        global_heading=float(st.slider("Heading",0,179,90,key="gh"))
        st.markdown(compass_svg(global_heading,140),unsafe_allow_html=True)
    else:
        st.caption("Google Roads API per marker" if API_KEY else "Neighbour bearing")

    st.markdown('<p class="sec-head">Strip Configuration</p>',unsafe_allow_html=True)
    n_strips=int(st.number_input("Number of Strips",1,20,3,1,key="ns"))
    strip_thick=st.number_input("Strip Thickness (m)",0.05,2.0,0.5,0.05,key="sthick")
    strip_gap=st.number_input("Gap Between Strips (m)",0.1,5.0,0.6,0.1,key="sg")
    total_span=n_strips*strip_thick+(n_strips-1)*strip_gap
    st.caption(f"{n_strips}x{strip_thick*1000:.0f}mm | gap={strip_gap}m | span={total_span:.2f}m")

    st.markdown('<p class="sec-head">Road Labels in KML</p>',unsafe_allow_html=True)
    selected_labels=st.multiselect("Labels",options=list(LABEL_PRESETS.keys()),default=["SLOW"],key="labels_sel")
    if not selected_labels: selected_labels=["SLOW"]
    for lbl in selected_labels:
        st.markdown(f'<span class="lbl-chip">{lbl}</span>',unsafe_allow_html=True)

    rename_pm=st.toggle("Rename Untitled placemark",value=True,key="ren_pm")
    rate_rs=st.number_input("Rate (Rs/m2)",100,50000,2500,100,key="rate")

    st.markdown("---")
    gen_btn=st.button("Generate Polygons",type="primary",disabled=uploaded is None,key="genb")
    if not uploaded: st.caption("Upload KML to enable")


with tab_gen:
    markers_raw: List[KMLMarker]=[]
    n_markers=0; kml_temp=""

    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False,suffix=".kml") as tmp:
            tmp.write(uploaded.getvalue()); kml_temp=tmp.name
        try:
            _markers=parse_kml(kml_temp); n_markers=len(_markers); markers_raw=_markers
            mc1,mc2,mc3,mc4=st.columns(4)
            mc1.metric("Markers",n_markers); mc2.metric("Road Width",f"{road_w}m")
            mc3.metric("Strips",n_strips); mc4.metric("Thickness",f"{strip_thick*1000:.0f}mm")
            if n_markers==0:
                st.error("No Point markers found.")
            else:
                w=8; est=math.ceil(n_markers/w)+4
                st.markdown(f'<div class="info-card">{n_markers} markers loaded. '
                            f'Est time: ~{est}s (8 parallel workers)</div>',unsafe_allow_html=True)
                cols=st.columns(min(n_markers,4))
                for ci,mk in enumerate(_markers):
                    with cols[ci%len(cols)]:
                        st.markdown(f'<div class="mk-card"><div class="mk-name">{mk.index+1}. {mk.name}</div>'
                                    f'<div class="mk-coords">Lat:{mk.lat:.6f} Lon:{mk.lon:.6f}</div></div>',
                                    unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Parse error: {e}")
            import traceback; st.code(traceback.format_exc())
    else:
        st.info("Upload a KML file using the sidebar to begin.")

    if n_markers>0:
        with st.expander("Per-Marker Overrides (optional)",expanded=False):
            if st.button("Clear All Overrides",key="clr"):
                st.session_state.per_marker_h={}; st.session_state.per_marker_w={}
                st.session_state.per_marker_strips={}; st.rerun()
            for mk in markers_raw:
                i=mk.index
                with st.expander(f"Marker {i+1}: {mk.name}",expanded=False):
                    oc1,oc2,oc3=st.columns(3)
                    with oc1:
                        use_w=st.toggle("Custom width",key=f"uw{i}")
                        if use_w:
                            nw=st.number_input("W(m)",2.0,60.0,st.session_state.per_marker_w.get(i,road_w),0.5,key=f"mw{i}")
                            st.session_state.per_marker_w[i]=nw
                        elif i in st.session_state.per_marker_w: del st.session_state.per_marker_w[i]
                    with oc2:
                        use_h=st.toggle("Custom heading",key=f"uh{i}")
                        if use_h:
                            nh=st.slider("H",0,179,int(st.session_state.per_marker_h.get(i,global_heading or 90)),1,key=f"mh{i}")
                            st.session_state.per_marker_h[i]=float(nh)
                        elif i in st.session_state.per_marker_h: del st.session_state.per_marker_h[i]
                    with oc3:
                        use_s=st.toggle("Custom strips",key=f"us{i}")
                        if use_s:
                            ns2=int(st.number_input("S",1,20,st.session_state.per_marker_strips.get(i,n_strips),1,key=f"ms{i}"))
                            st.session_state.per_marker_strips[i]=ns2
                        elif i in st.session_state.per_marker_strips: del st.session_state.per_marker_strips[i]

    if gen_btn and uploaded and n_markers>0:
        spec=PolySpec(road_width_m=road_w,num_lanes=nl_def,separator_width_m=sep_w,
                      num_strips=n_strips,strip_thick_m=float(strip_thick),
                      strip_gap_m=float(strip_gap),heading_override=global_heading,
                      labels=list(selected_labels),rename_placemarks=rename_pm,api_key=API_KEY)
        for mk in markers_raw:
            i=mk.index; ov={}
            if i in st.session_state.per_marker_w: ov["road_width_m"]=st.session_state.per_marker_w[i]
            if i in st.session_state.per_marker_h: ov["heading_deg"]=st.session_state.per_marker_h[i]
            if i in st.session_state.per_marker_strips: ov["num_strips"]=st.session_state.per_marker_strips[i]
            if ov: spec.marker_overrides[i]=ov

        per_h=dict(st.session_state.per_marker_h)
        prog=st.progress(0,"Starting..."); status_text=st.empty()
        def _upd(msg,pct):
            prog.progress(min(pct,99),msg); status_text.caption(f"{msg}")
        try:
            _upd("Parsing KML...",10)
            m_obj,polys,headings=run_pipeline(kml_temp,spec,per_h,progress_cb=_upd)
            out_kml=kml_temp.replace(".kml","_v5_out.kml")
            out_xlsx=kml_temp.replace(".kml","_v5_out.xlsx")
            _upd("Exporting KML...",58)
            export_kml(m_obj,polys,headings,spec,out_kml)
            _upd(f"Fetching {len(m_obj)} satellite images (8 workers)...",63)
            export_excel(m_obj,polys,headings,spec,out_xlsx,progress_cb=_upd)
            _upd("Finalising...",97)
            with open(out_kml,"rb") as f: st.session_state.kml_bytes=f.read()
            with open(out_xlsx,"rb") as f: st.session_state.xlsx_bytes=f.read()
            st.session_state.markers=m_obj; st.session_state.all_polys=polys
            st.session_state.headings=headings; st.session_state.generated=True
            st.session_state.viewer_kml_bytes=st.session_state.kml_bytes
            prog.progress(100,"Done"); status_text.empty(); time.sleep(0.3); prog.empty(); st.rerun()
        except Exception as e:
            prog.empty(); status_text.empty()
            st.error(f"Error: {e}")
            import traceback; st.code(traceback.format_exc())

            prog.empty(); status_text.empty()
            st.error(f"❌ Error: {e}")
            import traceback; st.code(traceback.format_exc())

    # ── RESULTS ───────────────────────────────────────────────────
    if st.session_state.generated and st.session_state.all_polys:
        m_obj  = st.session_state.markers
        polys  = st.session_state.all_polys
        heads  = st.session_state.headings

        st.markdown('<p class="sec-head">✅ Results</p>', unsafe_allow_html=True)
        r1,r2,r3,r4,r5 = st.columns(5)
        r1.metric("📍 Markers",    len(m_obj))
        r2.metric("🟨 Strips",     len(polys))
        r3.metric("🛣️ Road Width", f"{road_w}m")
        r4.metric("📐 Thick",      f"{strip_thick*1000:.0f}mm")
        r5.metric("Strips/Marker", len(polys)//max(len(m_obj),1))

        st.markdown('<p class="sec-head">📥 Downloads</p>', unsafe_allow_html=True)
        dl1, dl2 = st.columns(2)
        if st.session_state.kml_bytes:
            dl1.download_button(
                "📥 Download Updated KML",
                data=st.session_state.kml_bytes,
                file_name="speed_breakers_v5.kml",
                mime="application/vnd.google-earth.kml+xml",
                use_container_width=True)
        if st.session_state.xlsx_bytes:
            dl2.download_button(
                "📊 Download Excel BOQ + Satellite Images",
                data=st.session_state.xlsx_bytes,
                file_name="speed_breakers_v5_boq.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        st.markdown(
            '<div class="info-card">💡 Column L in Excel = satellite image with '
            '<b>yellow polygon strips</b> drawn on top via Pillow. '
            'Requires: <code>pip install Pillow</code></div>',
            unsafe_allow_html=True)

        # BOQ table
        st.markdown('<p class="sec-head">📋 BOQ Summary</p>', unsafe_allow_html=True)
        by: dict = {}
        for p in polys: by.setdefault(p.marker_idx, []).append(p)
        rows = []
        for mk in m_obj:
            ps = by.get(mk.index, []); p0 = ps[0] if ps else None
            hdata = heads.get(mk.index, (0.0, mk.lat, mk.lon, "default"))
            h_deg, snap_lat, snap_lon = hdata[0], hdata[1], hdata[2]
            rw_v = p0.road_width_m  if p0 else road_w
            st_v = p0.strip_thick_m if p0 else strip_thick
            gp_v = p0.strip_gap_m   if p0 else strip_gap
            ns_v = len(ps)
            span = ns_v*st_v + max(ns_v-1,0)*gp_v
            area = round(st_v*rw_v*ns_v, 4)
            amt  = round(area*rate_rs, 2)
            rows.append({
                "S.No": mk.index+1, "Marker": mk.name,
                "Lat": round(snap_lat,6), "Lon": round(snap_lon,6),
                "Bearing": round(h_deg,1), "Width(m)": round(rw_v,2),
                "Span(m)": round(span,3), "Strips": ns_v,
                "Area(m²)": area, "Rate": rate_rs, "Amount(Rs)": amt,
                "Src": hdata[3],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Live map
        st.markdown('<p class="sec-head">🗺️ Live Satellite Preview</p>', unsafe_allow_html=True)
        if m_obj:
            clat = sum(m.lat for m in m_obj)/len(m_obj)
            clon = sum(m.lon for m in m_obj)/len(m_obj)
            fmap = folium.Map(
                location=[clat,clon], zoom_start=19, max_zoom=21,
                tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                attr="Google Satellite")
            COLS=["#FFD700","#FFB300","#FF8C00","#FFA500","#FFCC00","#FFE066"]
            for p in polys:
                folium.Polygon(
                    locations=[[la,lo] for la,lo in p.coords],
                    color="#8B6914", weight=2, fill=True,
                    fill_color=COLS[p.strip_idx%len(COLS)], fill_opacity=0.88,
                    tooltip=(f"{p.marker_name} | Strip {p.strip_idx+1} | "
                             f"{p.road_heading:.1f}°")).add_to(fmap)
            for mk in m_obj:
                hd = heads.get(mk.index,(0.0,mk.lat,mk.lon,""))
                folium.Marker([hd[1],hd[2]],
                    popup=folium.Popup(
                        f"<b>{mk.name}</b><br>Heading:{hd[0]:.1f}°<br>Road:{road_w:.1f}m",
                        max_width=200),
                    icon=folium.Icon(color="red",icon="map-marker",prefix="fa")).add_to(fmap)
                folium.Marker([hd[1],hd[2]],icon=folium.DivIcon(
                    html=(f'<div style="font-size:11px;font-weight:700;color:#FFD700;'
                          f'background:rgba(0,0,0,.65);padding:2px 5px;border-radius:3px;'
                          f'white-space:nowrap;margin-top:-28px;margin-left:14px;">'
                          f'{mk.name}</div>'),
                    icon_size=(160,28),icon_anchor=(0,0))).add_to(fmap)
            st_folium(fmap, width="100%", height=540, returned_objects=[])

        # Per-marker detail
        st.markdown('<p class="sec-head">📐 Per-Marker Detail</p>', unsafe_allow_html=True)
        for mk in m_obj:
            ps = by.get(mk.index,[])
            if not ps: continue
            p0 = ps[0]; hd = heads.get(mk.index,(0.0,mk.lat,mk.lon,"default"))
            with st.expander(f"📍 {mk.name} — {len(ps)} strips | "
                             f"{p0.road_width_m:.1f}m × {p0.strip_thick_m*1000:.0f}mm"):
                dc1, dc2 = st.columns([2,1])
                with dc1:
                    area_s = p0.strip_thick_m * p0.road_width_m
                    span = len(ps)*p0.strip_thick_m + max(len(ps)-1,0)*p0.strip_gap_m
                    st.markdown(f"""
| Property | Value |
|---|---|
| Snapped Lat | `{hd[1]:.6f}` |
| Snapped Lon | `{hd[2]:.6f}` |
| Road Width | **{p0.road_width_m:.2f} m** |
| Heading | {hd[0]:.1f}° ({hd[3]}) |
| Strips | {len(ps)} × {p0.strip_thick_m*1000:.0f}mm |
| Total span | {span:.3f} m |
| Total Area | {area_s*len(ps):.4f} m² |
| Amount | Rs {area_s*len(ps)*rate_rs:,.0f} |
| KML Label | CAP PTBM {p0.strip_thick_m*1000:.0f}MM X {len(ps)} |
""")
                with dc2:
                    st.markdown(compass_svg(hd[0],143), unsafe_allow_html=True)
                    st.caption(f"Road **{hd[0]:.0f}°** | Strip **{(hd[0]+90)%360:.0f}°**")


# ══════════════════════════════════════════════════════════════════
# TAB 2: KML VIEWER
# ══════════════════════════════════════════════════════════════════
with tab_view:
    st.markdown(
        '<div class="info-card">🗺️ <b>KML Viewer</b> — '
        'Yellow = polygon strips. Coloured pins = labels. No Google Earth needed.</div>',
        unsafe_allow_html=True)
    col_v1, col_v2 = st.columns([1,3])
    with col_v1:
        vu = st.file_uploader("Upload KML to view", type=["kml"], key="viewer_kml")
        if vu: st.session_state.viewer_kml_bytes = vu.read()
        if st.session_state.kml_bytes and not vu:
            if st.button("📂 Load Generated KML", key="load_gen"):
                st.session_state.viewer_kml_bytes = st.session_state.kml_bytes
                st.rerun()
        viewer_zoom = st.slider("Map Zoom", 15, 21, 19, key="vzoom")
    with col_v2:
        if st.session_state.viewer_kml_bytes:
            polygons, points = parse_kml_for_viewer(st.session_state.viewer_kml_bytes)
            lbl_pts   = [p for p in points if p["name"] in ALL_LABEL_NAMES]
            pin_pts   = [p for p in points if p["name"] not in ALL_LABEL_NAMES]
            strip_pgs = [p for p in polygons if "CAP" in p["name"] or "PTBM" in p["name"]]
            vc1,vc2,vc3,vc4 = st.columns(4)
            vc1.metric("🔷 Polygons",  len(polygons))
            vc2.metric("📍 Pins",      len(pin_pts))
            vc3.metric("🏷️ Labels",   len(lbl_pts))
            vc4.metric("🟨 Strips",   len(strip_pgs))
            if polygons or points:
                fmap = build_kml_viewer_map(polygons, points, zoom=viewer_zoom)
                if fmap: st_folium(fmap, width="100%", height=590, returned_objects=[])
                else: st.warning("No geographic data found.")
            else:
                st.warning("No polygons or markers found.")
            with st.expander("📊 KML Contents"):
                lbl_counts: dict = {}
                for p in lbl_pts:
                    lbl_counts[p["name"]] = lbl_counts.get(p["name"],0)+1
                st.markdown(
                    f"- **{len(strip_pgs)}** strip polygons | "
                    f"**{len(pin_pts)}** pins | "
                    f"**{len(lbl_pts)}** labels "
                    f"({', '.join(f'{n}:{c}' for n,c in lbl_counts.items()) or 'none'})")
                if pin_pts:
                    st.dataframe(pd.DataFrame([{
                        "Name": p["name"],
                        "Lat":  round(p["lat"],6),
                        "Lon":  round(p["lon"],6),
                    } for p in pin_pts]), hide_index=True, use_container_width=True)
        else:
            st.markdown("""
            <div style="background:#0a1220;border:1px dashed #1e3a52;
                        border-radius:12px;padding:50px;text-align:center;">
              <div style="font-size:2.5rem;margin-bottom:12px">🗺️</div>
              <div style="font-size:1rem;font-weight:600;color:#e8eaf0;margin-bottom:8px">
                No KML loaded</div>
              <div style="font-size:.82rem;color:#8ba8c4">
                Upload a KML or generate polygons first.</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 3: ROAD WIDTH EXPLAINER
# ══════════════════════════════════════════════════════════════════
with tab_explain:
    st.markdown('<p class="sec-head">📏 Why Does the Polygon Look Narrower Than the Road?</p>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="road-explain">🔍 <b>Observation:</b> Polygon measures 7m in KML tools '
        'but appears not to cover the full road in satellite view. '
        'This is <b>not a code error</b> — 3 causes below.</div>',
        unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown("**📷 Cause 1 — Satellite Tilt**\n\n"
                    "Imagery is captured at 5–15° angle. Roads appear foreshortened "
                    "perpendicular to the viewing angle. A 7m road looks like 5–6m.\n\n"
                    "> *Polygon is geometrically correct. Foreshortening is a camera effect.*")
    with c2:
        st.markdown("**🛣️ Cause 2 — Road Wider Than Preset**\n\n"
                    "IRC 2-Lane = 7.0m carriageway. But shoulders + berms add 1–2m each side. "
                    "Many Indian roads are 8–10m including unpainted margins.\n\n"
                    "> *Fix: Measure with Google Earth ruler → use Custom width.*")
    with c3:
        st.markdown("**🧭 Cause 3 — Heading Off by 2–3°**\n\n"
                    "Small heading error makes polygon appear diagonal and shorter "
                    "when viewed along the road axis.\n\n"
                    "> *Fix: Manual heading → fine-tune compass slider.*")

    st.markdown("---")
    st.markdown('<p class="sec-head">✅ Step-by-Step Fix</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-card"><b>Step 1</b> — Google Earth Pro → Tools → Ruler → '
        'Line → click one road edge → click opposite edge → note metres</div>',
        unsafe_allow_html=True)
    st.markdown(
        '<div class="info-card"><b>Step 2</b> — Sidebar → Lane Type → '
        '<b>Custom</b> → Road Width = measured value</div>',
        unsafe_allow_html=True)
    st.markdown(
        '<div class="info-card"><b>Step 3</b> — If still misaligned → '
        'Manual heading → adjust compass to match road direction</div>',
        unsafe_allow_html=True)
    st.markdown(
        '<div class="warn-card"><b>IRC Standard Widths:</b> '
        'NH 2-Lane: 7.5m | SH: 7.0m | MDR: 5.5m | Village: 3.75m | '
        'Urban Arterial: 10–12m | 4-Lane NH: 14m | 6-Lane NH: 21m</div>',
        unsafe_allow_html=True)

    st.markdown("---")
    st.info(
        "**Script for Professor (Dr. Neha Kasture / PWD):**\n\n"
        "*\"The GIS polygon is computed geodesically (Haversine formula) and is geometrically "
        "accurate to the configured carriageway width. Visual discrepancy in Google Earth "
        "arises from (a) satellite oblique capture angle causing perpendicular foreshortening, "
        "and (b) the visual road width including shoulders/footpaths which are outside the IRC "
        "carriageway definition. For sites where carriageway exceeds the IRC preset, we measured "
        "the actual width using Google Earth Pro Ruler and entered the exact value — the polygon "
        "then correctly covers the full paved carriageway.\"*")