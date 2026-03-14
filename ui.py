# """
# ui.py  v5  —  Speed Breaker GIS BOQ Tool
# IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI
# streamlit run ui.py
# """

# import streamlit as st
# import tempfile, time, math
# import pandas as pd
# import folium
# from streamlit_folium import st_folium
# from polygon import (
#     parse_kml_markers, run_pipeline, pca_heading,
#     PolygonSpec, GeneratedPolygon, MarkerInfo,
#     haversine_distance, forward_bearing, normalise_heading,
# )

# st.set_page_config(
#     page_title="GIS BOQ — Speed Breaker v5",
#     page_icon="🚧", layout="wide",
#     initial_sidebar_state="expanded",
# )

# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap');
# html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}

# .banner{background:linear-gradient(135deg,#050d1a,#0d1a2e,#142340);
#   border:1px solid #FFD700;border-radius:14px;padding:20px 28px 14px;
#   margin-bottom:18px;box-shadow:0 4px 24px rgba(255,215,0,.1);}
# .banner h1{color:#FFD700;font-size:1.7rem;font-weight:700;margin:0 0 4px;}
# .banner p{color:#94a3b8;font-size:.87rem;margin:0;}
# .tag{display:inline-block;background:#1e3a5f;color:#60a5fa;border-radius:20px;
#   padding:2px 10px;font-size:.7rem;font-weight:600;margin:5px 4px 0 0;}

# .hdg-panel{background:#06111f;border:2px solid #FFD700;border-radius:12px;
#   padding:16px 18px;margin-bottom:12px;}
# .hdg-panel h4{color:#FFD700;margin:0 0 10px;font-size:.93rem;}

# .compass-ring{position:relative;width:120px;height:120px;margin:0 auto 12px;
#   border-radius:50%;border:3px solid #FFD700;background:#06111f;}

# .stat{background:#0d1a2e;border:1px solid #1e3a5f;border-left:4px solid #FFD700;
#   border-radius:9px;padding:12px 13px;text-align:center;}
# .stat .v{font-size:1.6rem;font-weight:700;color:#FFD700;}
# .stat .l{font-size:.67rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;}

# .mk{background:#0d1a2e;border:1px solid #1e3a5f;border-left:3px solid #FFD700;
#   border-radius:7px;padding:8px 11px;margin-bottom:6px;
#   font-family:'JetBrains Mono',monospace;font-size:.76rem;}
# .mk .n{color:#FFD700;font-weight:600;margin-bottom:2px;}
# .mk .c{color:#60a5fa;}.mk .g{color:#6b7280;}

# .warn{background:#2d1400;border:1px solid #d97706;border-radius:8px;
#   padding:9px 13px;color:#fde68a;font-size:.82rem;margin:7px 0;}
# .ok{background:#052e16;border:1px solid #16a34a;border-radius:8px;
#   padding:9px 13px;color:#86efac;font-size:.82rem;margin:7px 0;}
# .info2{background:#06111f;border:1px dashed #FFD700;border-radius:8px;
#   padding:9px 13px;color:#94a3b8;font-size:.8rem;margin:8px 0;}

# .step{background:#0d1a2e;border-radius:7px;padding:9px 13px;
#   margin-bottom:6px;border:1px solid #1e3a5f;}
# .step .n{color:#FFD700;font-weight:700;margin-right:7px;}

# div[data-testid="stSidebar"]{background:#050d1a;}
# .stButton>button{background:linear-gradient(135deg,#d97706,#b45309);
#   color:#fff;border:none;border-radius:8px;font-weight:600;transition:all .2s;}
# .stButton>button:hover{transform:translateY(-1px);}
# </style>
# """, unsafe_allow_html=True)

# st.markdown("""
# <div class="banner">
#   <h1>🚧 GIS BOQ Tool — CAP PTBM Speed Breaker Generator v5</h1>
#   <p>KML → parallel perpendicular strips → BOQ Excel | Visual heading picker</p>
#   <span class="tag">IIIT Nagpur</span><span class="tag">Dr. Neha Kasture</span>
#   <span class="tag">PWD/NHAI</span><span class="tag">v5</span>
# </div>
# """, unsafe_allow_html=True)


# # ── Sidebar ───────────────────────────────────────────────────────────────────
# with st.sidebar:

#     # ── HEADING (top priority control) ────────────────────────────────────────
#     st.markdown("## 🧭 Road Heading — MOST IMPORTANT")
#     st.markdown('<div class="hdg-panel"><h4>Set the angle your road runs</h4>',
#                 unsafe_allow_html=True)

#     st.markdown("""
#     **Why this matters:** strips must be perpendicular to your road.
#     If you don't set this correctly, strips will be at wrong angle.

#     **How to measure in Google Earth Pro:**
#     1. `Tools → Ruler → Line`
#     2. Draw a line **along the centre of your road**
#     3. Note the **Heading** value shown (e.g. 135°)
#     4. Enter it below
#     """)

#     use_manual = st.toggle("✏️ Set heading manually (RECOMMENDED)", value=True,
#         help="Turn this ON and set the angle below. Much more reliable than auto-detect.")

#     heading_val = 0
#     if use_manual:
#         heading_val = st.slider(
#             "Road Heading (° from North, 0–179)",
#             min_value=0, max_value=179, value=45, step=1,
#             help="0=N–S road | 45=NE–SW | 90=E–W | 135=SE–NW"
#         )

#         # Visual compass
#         strip_dir = (heading_val + 90) % 180
#         road_dir_name = (
#             "North–South" if heading_val < 15 else
#             "NNE–SSW"     if heading_val < 35 else
#             "NE–SW"       if heading_val < 60 else
#             "ENE–WSW"     if heading_val < 80 else
#             "East–West"   if heading_val < 100 else
#             "ESE–WNW"     if heading_val < 115 else
#             "SE–NW"       if heading_val < 150 else
#             "SSE–NNW"
#         )

#         # Simple SVG compass showing road direction and strip direction
#         angle_rad = math.radians(heading_val)
#         cx, cy, r2 = 60, 60, 45
#         ex = cx + r2 * math.sin(angle_rad)
#         ey = cy - r2 * math.cos(angle_rad)
#         ex2 = cx - r2 * math.sin(angle_rad)
#         ey2 = cy + r2 * math.cos(angle_rad)
#         # Strip direction (perpendicular)
#         perp_rad = math.radians(heading_val + 90)
#         sx  = cx + r2 * math.sin(perp_rad)
#         sy  = cy - r2 * math.cos(perp_rad)
#         sx2 = cx - r2 * math.sin(perp_rad)
#         sy2 = cy + r2 * math.cos(perp_rad)

#         st.markdown(f"""
#         <div style="text-align:center;">
#         <svg width="130" height="130" viewBox="0 0 120 120">
#           <!-- compass background -->
#           <circle cx="60" cy="60" r="55" fill="#06111f" stroke="#FFD700" stroke-width="2"/>
#           <!-- N label -->
#           <text x="60" y="14" text-anchor="middle" fill="#94a3b8" font-size="9">N</text>
#           <text x="60" y="112" text-anchor="middle" fill="#94a3b8" font-size="9">S</text>
#           <text x="10" y="64" text-anchor="middle" fill="#94a3b8" font-size="9">W</text>
#           <text x="110" y="64" text-anchor="middle" fill="#94a3b8" font-size="9">E</text>
#           <!-- Road direction (yellow line) -->
#           <line x1="{ex2:.1f}" y1="{ey2:.1f}" x2="{ex:.1f}" y2="{ey:.1f}"
#                 stroke="#FFD700" stroke-width="3" stroke-linecap="round"/>
#           <!-- Strip direction (orange, perpendicular) -->
#           <line x1="{sx2:.1f}" y1="{sy2:.1f}" x2="{sx:.1f}" y2="{sy:.1f}"
#                 stroke="#FF8C00" stroke-width="2" stroke-dasharray="4 2" stroke-linecap="round"/>
#           <!-- Centre dot -->
#           <circle cx="60" cy="60" r="4" fill="#FFD700"/>
#           <!-- Legend -->
#           <rect x="5" y="90" width="12" height="3" fill="#FFD700" rx="1"/>
#           <text x="20" y="94" fill="#FFD700" font-size="8">Road {heading_val}°</text>
#           <rect x="5" y="100" width="12" height="2" fill="#FF8C00" rx="1"/>
#           <text x="20" y="104" fill="#FF8C00" font-size="8">Strip {strip_dir}°</text>
#         </svg>
#         <div style="color:#fde68a;font-size:.78rem;margin-top:2px;">
#           Road: <b>{road_dir_name}</b><br/>
#           Strip runs at <b>{strip_dir}°</b> (perpendicular)
#         </div>
#         </div>
#         """, unsafe_allow_html=True)

#         heading_override = float(heading_val)
#         st.markdown('</div>', unsafe_allow_html=True)
#         st.markdown('<div class="ok">✅ Manual heading active</div>', unsafe_allow_html=True)
#     else:
#         heading_override = -1.0
#         st.markdown('</div>', unsafe_allow_html=True)
#         use_osm = st.toggle("🌐 Try OSM (needs internet)", value=True)
#         st.markdown('<div class="warn">⚠️ Auto-detect unreliable for clustered markers. '
#                     'Use manual heading if strips are wrong angle.</div>',
#                     unsafe_allow_html=True)

#     st.markdown("---")

#     # ── Road layout ───────────────────────────────────────────────────────────
#     st.markdown("## 🛣️ Road Layout")
#     num_lanes    = st.number_input("Number of Lanes", 1, 8, 2, 1,
#                                     help="2 = 1 going + 1 incoming")
#     road_width_m = st.number_input("Total Road Width (m)", 2.0, 60.0, 7.0, 0.5,
#                                     help="Full road width. 2-lane≈7m, 4-lane≈14m")
#     has_sep      = st.toggle("Has Centre Separator/Divider", value=True)
#     sep_w        = 0.0
#     if has_sep and num_lanes > 1:
#         sep_w = st.number_input("Separator Width (m)", 0.1, 5.0, 0.5, 0.1,
#                                  help="The raised kerb or painted centre divider")
#     drv_lw = (road_width_m - (sep_w if has_sep and num_lanes > 1 else 0.0)) / num_lanes
#     st.caption(f"↳ Each lane drivable width = **{drv_lw:.2f} m**")

#     st.markdown("---")

#     # ── Strip spec ────────────────────────────────────────────────────────────
#     st.markdown("## 🟨 Strip Specification")
#     strip_mm   = st.number_input("Strip Width (mm)", 5.0, 200.0, 15.0, 5.0,
#                                   help="CAP PTBM thickness: 10mm or 15mm")
#     num_strips = st.number_input("Total Strips (all lanes)", 1, 60, 6, 1)
#     gap_m      = st.number_input("Gap Between Strips (m)", 0.01, 2.0, 0.10, 0.05)

#     spl = int(num_strips) // int(num_lanes)
#     st.info(
#         f"**{int(num_strips)} strips ÷ {int(num_lanes)} lanes = {spl}/lane**\n\n"
#         f"Code: `CAP PTBM {int(strip_mm)}MM X {int(num_strips)}`\n\n"
#         f"Strip: **{strip_mm}mm** × **{drv_lw:.2f}m** per lane"
#     )


# # ── Main columns ──────────────────────────────────────────────────────────────
# cL, cR = st.columns([1, 1.7], gap="large")

# with cL:
#     st.markdown("### 📂 Upload KML")
#     uploaded = st.file_uploader("KML from Google Earth Pro", type=["kml"])

#     if uploaded:
#         st.success(f"✅ **{uploaded.name}** — {uploaded.size:,} bytes")
#         with tempfile.NamedTemporaryFile(suffix=".kml", delete=False) as tmp:
#             tmp.write(uploaded.read()); tmp_path = tmp.name
#         try:
#             markers = parse_kml_markers(tmp_path)
#             st.session_state.update({"markers": markers, "tmp_kml": tmp_path})

#             # Spread analysis
#             pca_h = pca_heading(markers)
#             if len(markers) > 1:
#                 spread = max(
#                     haversine_distance(markers[i].lat, markers[i].lon,
#                                        markers[j].lat, markers[j].lon)
#                     for i in range(len(markers))
#                     for j in range(i+1, min(i+3, len(markers)))
#                 )
#             else:
#                 spread = 0.0

#             st.markdown(f"**{len(markers)} marker(s)** | spread ≈ {spread:.1f}m")

#             if pca_h is not None:
#                 st.markdown(f'<div class="ok">🔵 PCA heading: <b>{pca_h:.1f}°</b> '
#                             f'(auto-detected from marker spread)</div>',
#                             unsafe_allow_html=True)
#             else:
#                 st.markdown(
#                     '<div class="warn">⚠️ Markers too close for auto-heading. '
#                     'Use manual heading slider!</div>',
#                     unsafe_allow_html=True)

#             for mk in markers[:8]:
#                 st.markdown(
#                     f'<div class="mk"><div class="n">📍 {mk.index}. {mk.name}</div>'
#                     f'<div class="c">{mk.placement_code or "—"}</div>'
#                     f'<div class="g">{mk.lat:.6f}, {mk.lon:.6f}</div></div>',
#                     unsafe_allow_html=True)
#             if len(markers) > 8:
#                 st.caption(f"… +{len(markers)-8} more")
#         except Exception as e:
#             st.error(f"KML parse error: {e}")

#     # Lane diagram
#     if uploaded and "markers" in st.session_state:
#         st.markdown("### 🛤️ Cross-Road Layout")
#         nl  = int(num_lanes)
#         ns  = int(num_strips)
#         b2  = ns // nl; r2 = ns % nl
#         rows = []; sc = 1
#         for li in range(nl):
#             n_in = b2 + (1 if li < r2 else 0)
#             sl   = " ".join([f"S{sc+i}" for i in range(n_in)]); sc += n_in
#             rows.append(f"Lane {li+1} ({'→' if li%2==0 else '←'}): [{sl}]")
#             if has_sep and num_lanes > 1 and li < nl-1:
#                 rows.append(f"    ~~~ SEP {sep_w:.1f}m ~~~")
#         st.code("\n".join(rows), language=None)
#         st.caption(
#             f"Strip: {strip_mm}mm wide, {drv_lw:.2f}m long | "
#             f"Perpendicular to road ({(heading_val+90)%180}°)"
#             if use_manual else
#             f"Strip: {strip_mm}mm wide, {drv_lw:.2f}m long"
#         )

#     st.markdown("---")
#     st.markdown("### 🚀 Generate")
#     gen = st.button("⚡ Generate Polygons & Export BOQ",
#                     disabled=not uploaded, use_container_width=True)

#     if gen and "tmp_kml" in st.session_state:
#         spec = PolygonSpec(
#             strip_width_mm       = float(strip_mm),
#             num_strips           = int(num_strips),
#             gap_between_strips_m = float(gap_m),
#             num_lanes            = int(num_lanes),
#             road_width_m         = float(road_width_m),
#             separator_width_m    = float(sep_w),
#             has_separator        = bool(has_sep),
#             heading_override     = float(heading_override),
#         )
#         pb  = st.progress(0); txt = st.empty()
#         def prog(i, tot, nm):
#             pb.progress(int(i/tot*100)); txt.text(f"{i+1}/{tot}: {nm}")

#         try:
#             ko = st.session_state["tmp_kml"].replace(".kml","_out.kml")
#             xo = st.session_state["tmp_kml"].replace(".kml","_out.xlsx")
#             osm_flag = (not use_manual) and locals().get('use_osm', True)
#             _, pols = run_pipeline(
#                 st.session_state["tmp_kml"], ko, xo, spec,
#                 use_osm=osm_flag, progress_callback=prog)
#             pb.progress(100); time.sleep(0.3); pb.empty(); txt.empty()
#             st.session_state.update({
#                 "polygons": pols, "out_kml": ko,
#                 "out_excel": xo, "spec": spec,
#             })
#             src_c = {}
#             for pg in pols: src_c[pg.heading_source] = src_c.get(pg.heading_source,0)+1
#             st.success(
#                 f"✅ {len(pols)} markers × {spec.num_strips} strips = "
#                 f"**{len(pols)*spec.num_strips} polygons**"
#             )
#             st.info("📡 " + " | ".join(f"{k}:{v}" for k,v in src_c.items()))
#         except Exception as e:
#             pb.empty(); txt.empty(); st.error(f"Error: {e}")
#             import traceback; st.code(traceback.format_exc())

#     if "out_kml" in st.session_state:
#         st.markdown("---")
#         st.markdown("### 📥 Download")
#         with open(st.session_state["out_kml"],"rb") as f:
#             st.download_button("⬇️ KML (Google Earth Pro)", f,
#                                "speed_breaker_polygons.kml",
#                                "application/vnd.google-earth.kml+xml",
#                                use_container_width=True)
#         with open(st.session_state["out_excel"],"rb") as f:
#             st.download_button("⬇️ Excel BOQ Report", f,
#                                "speed_breaker_BOQ.xlsx",
#                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                                use_container_width=True)
#         if use_manual:
#             st.markdown(
#                 f'<div class="ok">Heading used: <b>{heading_val}°</b> (manual). '
#                 f'Strips run at {(heading_val+90)%180}°.</div>', unsafe_allow_html=True)
#         else:
#             st.markdown('<div class="info2">💡 Strips still wrong angle? '
#                         'Toggle "Set heading manually" in sidebar.</div>',
#                         unsafe_allow_html=True)


# # ── RIGHT: Map ─────────────────────────────────────────────────────────────────
# with cR:
#     st.markdown("### 🗺️ Satellite Preview")
#     polygons = st.session_state.get("polygons")
#     markers  = st.session_state.get("markers")
#     spec     = st.session_state.get("spec")

#     if polygons and markers and spec:
#         # Stats
#         curv = {"straight":0,"slight_curve":0,"sharp_curve":0}
#         src_c = {}
#         for pg in polygons:
#             curv[pg.road_curvature] = curv.get(pg.road_curvature,0)+1
#             src_c[pg.heading_source] = src_c.get(pg.heading_source,0)+1

#         cols = st.columns(5)
#         for col,(v,l) in zip(cols,[
#             (len(polygons),"Markers"),
#             (spec.num_strips,"Strips/mkr"),
#             (spec.num_lanes,"Lanes"),
#             (curv["sharp_curve"],"Sharp Curves"),
#             (len(polygons)*spec.num_strips,"Total Strips"),
#         ]):
#             with col:
#                 st.markdown(f'<div class="stat"><div class="v">{v}</div>'
#                             f'<div class="l">{l}</div></div>',
#                             unsafe_allow_html=True)

#         src_html = " ".join(
#             f'<span style="background:#1e3a5f;color:#93c5fd;border-radius:10px;'
#             f'padding:2px 8px;font-size:.75rem;font-weight:700;">{k}:{v}</span>'
#             for k,v in src_c.items())
#         st.markdown(f'<div style="margin:8px 0;font-size:.8rem;color:#94a3b8;">'
#                     f'📡 Heading: {src_html}</div>', unsafe_allow_html=True)

#         if spec.has_separator and spec.num_lanes > 1:
#             lw2 = (spec.road_width_m - spec.separator_width_m) / spec.num_lanes
#             st.markdown(
#                 f'<div style="background:#06111f;border:1px solid #FFD700;'
#                 f'border-radius:7px;padding:6px 12px;font-size:.79rem;'
#                 f'color:#fde68a;margin-bottom:6px;">'
#                 f'🚧 Sep: {spec.separator_width_m}m | Lane: {lw2:.2f}m | '
#                 f'Heading: {spec.heading_deg if hasattr(spec,"heading_deg") else spec.heading_override:.0f}°</div>',
#                 unsafe_allow_html=True)

#         # Map
#         avg_lat = sum(m.lat for m in markers)/len(markers)
#         avg_lon = sum(m.lon for m in markers)/len(markers)
#         fmap = folium.Map(
#             location=[avg_lat, avg_lon], zoom_start=18,
#             tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
#             attr="Google Satellite")
#         folium.TileLayer("OpenStreetMap", name="Street").add_to(fmap)
#         folium.LayerControl().add_to(fmap)

#         LC = ["#FFD700","#FFA500","#FF6B00","#FFEC00"]
#         CC = {"straight":"green","slight_curve":"orange","sharp_curve":"red"}

#         for pg in polygons:
#             mk = pg.marker
#             popup = (
#                 f"<b>{mk.name}</b><br/>"
#                 f"Heading: {pg.heading_deg:.1f}° [{pg.heading_source}]<br/>"
#                 f"Curvature: {pg.road_curvature.replace('_',' ').title()}<br/>"
#                 f"Lanes: {spec.num_lanes} | Strips: {spec.num_strips}<br/>"
#                 f"Code: {mk.placement_code or '—'}<br/>"
#                 f"{mk.lat:.6f}, {mk.lon:.6f}"
#             )
#             folium.Marker(
#                 [mk.lat, mk.lon],
#                 popup=folium.Popup(popup, max_width=240),
#                 tooltip=f"{mk.name} [{pg.heading_deg:.0f}°]",
#                 icon=folium.Icon(color=CC.get(pg.road_curvature,"blue"),
#                                   icon='road', prefix='fa'),
#             ).add_to(fmap)

#             for strip, ln in zip(pg.strip_polygons, pg.lane_assignments):
#                 ll = [[la, lo] for lo, la in strip]
#                 c  = LC[(ln-1) % len(LC)]
#                 folium.Polygon(
#                     locations=ll, color=c, fill=True,
#                     fill_color=c, fill_opacity=0.85,
#                     weight=1.5,
#                     tooltip=f"{mk.name} Lane {ln}",
#                 ).add_to(fmap)

#             if len(pg.coordinates) >= 3:
#                 folium.Polygon(
#                     locations=[[la,lo] for lo,la in pg.coordinates],
#                     color="#FF4444", fill=False, weight=2, dash_array="5",
#                 ).add_to(fmap)

#         st_folium(fmap, width="100%", height=490, returned_objects=[])

#         st.markdown("""<div style="display:flex;gap:10px;flex-wrap:wrap;
#             font-size:.77rem;color:#94a3b8;margin-top:5px;">
#           <span>🟡 Lane 1 (going)</span><span>🟠 Lane 2 (incoming)</span>
#           <span>🔴 Bounding outline</span>
#           <span>🟢 Straight road</span><span>🟡 Slight curve</span><span>🔴 Sharp curve</span>
#         </div>""", unsafe_allow_html=True)

#         # Detail table
#         st.markdown("### 📋 Details")
#         rows = []
#         for pg in polygons:
#             cb = {"straight":"🟢","slight_curve":"🟡","sharp_curve":"🔴"}.get(pg.road_curvature,"")
#             sb = {"osm":"🟢OSM","pca":"🔵PCA","manual":"🟡Man",
#                   "neighbour":"🔴Nbr"}.get(pg.heading_source, pg.heading_source)
#             rows.append({
#                 "#": pg.marker.index, "Name": pg.marker.name,
#                 "Code": pg.marker.placement_code or "—",
#                 "Lat": f"{pg.marker.lat:.5f}", "Lon": f"{pg.marker.lon:.5f}",
#                 "Hdg°": f"{pg.heading_deg:.1f}", "Src": sb,
#                 "Road": f"{cb} {pg.road_curvature.replace('_',' ')}",
#                 "L": spec.num_lanes, "S": spec.num_strips,
#             })
#         st.dataframe(pd.DataFrame(rows), use_container_width=True,
#                      hide_index=True, height=220)

#     elif markers:
#         avg_lat = sum(m.lat for m in markers)/len(markers)
#         avg_lon = sum(m.lon for m in markers)/len(markers)
#         fmap = folium.Map(location=[avg_lat,avg_lon], zoom_start=16, tiles="OpenStreetMap")
#         for mk in markers:
#             folium.Marker([mk.lat,mk.lon], tooltip=mk.name,
#                           icon=folium.Icon(color='orange',icon='map-marker')).add_to(fmap)
#         st_folium(fmap, width="100%", height=380, returned_objects=[])
#         st.info("Set road heading in sidebar → click Generate")

#     else:
#         st.markdown("""<div style="background:#0d1a2e;border-radius:12px;
#             padding:50px 25px;text-align:center;border:1px dashed #1e3a5f;">
#           <div style="font-size:3rem">🗺️</div>
#           <div style="color:#64748b;margin-top:11px">Upload KML to begin</div>
#         </div>""", unsafe_allow_html=True)

#         st.markdown("### 📖 Steps")
#         for n, d in [
#             ("1", "Mark speed breaker locations in Google Earth Pro → Save as KML"),
#             ("2", "Upload the KML file above"),
#             ("3", "⚠️ Open Google Earth → Ruler tool → draw along road → note heading angle"),
#             ("4", "Set that angle in the sidebar slider (0–179°)"),
#             ("5", "Set number of lanes, road width, separator if present"),
#             ("6", "Set strip spec (15mm × 6 strips etc.)"),
#             ("7", "Click Generate → parallel strips perpendicular to road"),
#             ("8", "Download KML for Google Earth Pro + Excel BOQ"),
#         ]:
#             st.markdown(f'<div class="step"><span class="n">Step {n}</span>{d}</div>',
#                         unsafe_allow_html=True)

#         st.markdown("""<div class="info2">
#         💡 <b>Heading reference:</b><br/>
#         Road going N–S → set 0° | E–W → set 90° | NE–SW → set 45° | SE–NW → set 135°<br/>
#         <b>From your screenshot: road looks like ~130–140° (SE direction)</b>
#         </div>""", unsafe_allow_html=True)

"""
ui.py  v5  —  Speed Breaker GIS BOQ Tool
IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI
streamlit run ui.py
"""

import streamlit as st
import tempfile, time, math
import pandas as pd
import folium
from streamlit_folium import st_folium
from polygon import (
    parse_kml_markers, run_pipeline, pca_heading,
    PolygonSpec, GeneratedPolygon, MarkerInfo,
    haversine_distance, forward_bearing, normalise_heading,
)

st.set_page_config(
    page_title="GIS BOQ — Speed Breaker v5",
    page_icon="🚧", layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}

.banner{background:linear-gradient(135deg,#050d1a,#0d1a2e,#142340);
  border:1px solid #FFD700;border-radius:14px;padding:20px 28px 14px;
  margin-bottom:18px;box-shadow:0 4px 24px rgba(255,215,0,.1);}
.banner h1{color:#FFD700;font-size:1.7rem;font-weight:700;margin:0 0 4px;}
.banner p{color:#94a3b8;font-size:.87rem;margin:0;}
.tag{display:inline-block;background:#1e3a5f;color:#60a5fa;border-radius:20px;
  padding:2px 10px;font-size:.7rem;font-weight:600;margin:5px 4px 0 0;}

.hdg-panel{background:#06111f;border:2px solid #FFD700;border-radius:12px;
  padding:16px 18px;margin-bottom:12px;}
.hdg-panel h4{color:#FFD700;margin:0 0 10px;font-size:.93rem;}

.compass-ring{position:relative;width:120px;height:120px;margin:0 auto 12px;
  border-radius:50%;border:3px solid #FFD700;background:#06111f;}

.stat{background:#0d1a2e;border:1px solid #1e3a5f;border-left:4px solid #FFD700;
  border-radius:9px;padding:12px 13px;text-align:center;}
.stat .v{font-size:1.6rem;font-weight:700;color:#FFD700;}
.stat .l{font-size:.67rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;}

.mk{background:#0d1a2e;border:1px solid #1e3a5f;border-left:3px solid #FFD700;
  border-radius:7px;padding:8px 11px;margin-bottom:6px;
  font-family:'JetBrains Mono',monospace;font-size:.76rem;}
.mk .n{color:#FFD700;font-weight:600;margin-bottom:2px;}
.mk .c{color:#60a5fa;}.mk .g{color:#6b7280;}

.warn{background:#2d1400;border:1px solid #d97706;border-radius:8px;
  padding:9px 13px;color:#fde68a;font-size:.82rem;margin:7px 0;}
.ok{background:#052e16;border:1px solid #16a34a;border-radius:8px;
  padding:9px 13px;color:#86efac;font-size:.82rem;margin:7px 0;}
.info2{background:#06111f;border:1px dashed #FFD700;border-radius:8px;
  padding:9px 13px;color:#94a3b8;font-size:.8rem;margin:8px 0;}

.step{background:#0d1a2e;border-radius:7px;padding:9px 13px;
  margin-bottom:6px;border:1px solid #1e3a5f;}
.step .n{color:#FFD700;font-weight:700;margin-right:7px;}

div[data-testid="stSidebar"]{background:#050d1a;}
.stButton>button{background:linear-gradient(135deg,#d97706,#b45309);
  color:#fff;border:none;border-radius:8px;font-weight:600;transition:all .2s;}
.stButton>button:hover{transform:translateY(-1px);}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="banner">
  <h1>🚧 GIS BOQ Tool — CAP PTBM Speed Breaker Generator v5</h1>
  <p>KML → parallel perpendicular strips → BOQ Excel | Visual heading picker</p>
  <span class="tag">IIIT Nagpur</span><span class="tag">Dr. Neha Kasture</span>
  <span class="tag">PWD/NHAI</span><span class="tag">v5</span>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # ── HEADING (top priority control) ────────────────────────────────────────
    st.markdown("## 🧭 Road Heading — MOST IMPORTANT")
    st.markdown('<div class="hdg-panel"><h4>Set the angle your road runs</h4>',
                unsafe_allow_html=True)

    st.markdown("""
    **Why this matters:** strips must be perpendicular to your road.
    If you don't set this correctly, strips will be at wrong angle.

    **How to measure in Google Earth Pro:**
    1. `Tools → Ruler → Line`
    2. Draw a line **along the centre of your road**
    3. Note the **Heading** value shown (e.g. 135°)
    4. Enter it below
    """)

    use_manual = st.toggle("✏️ Set heading manually (RECOMMENDED)", value=True,
        help="Turn this ON and set the angle below. Much more reliable than auto-detect.")

    heading_val = 0
    if use_manual:
        heading_val = st.slider(
            "Road Heading (° from North, 0–179)",
            min_value=0, max_value=179, value=45, step=1,
            help="0=N–S road | 45=NE–SW | 90=E–W | 135=SE–NW"
        )

        # Visual compass
        strip_dir = (heading_val + 90) % 180
        road_dir_name = (
            "North–South" if heading_val < 15 else
            "NNE–SSW"     if heading_val < 35 else
            "NE–SW"       if heading_val < 60 else
            "ENE–WSW"     if heading_val < 80 else
            "East–West"   if heading_val < 100 else
            "ESE–WNW"     if heading_val < 115 else
            "SE–NW"       if heading_val < 150 else
            "SSE–NNW"
        )

        # Simple SVG compass showing road direction and strip direction
        angle_rad = math.radians(heading_val)
        cx, cy, r2 = 60, 60, 45
        ex = cx + r2 * math.sin(angle_rad)
        ey = cy - r2 * math.cos(angle_rad)
        ex2 = cx - r2 * math.sin(angle_rad)
        ey2 = cy + r2 * math.cos(angle_rad)
        # Strip direction (perpendicular)
        perp_rad = math.radians(heading_val + 90)
        sx  = cx + r2 * math.sin(perp_rad)
        sy  = cy - r2 * math.cos(perp_rad)
        sx2 = cx - r2 * math.sin(perp_rad)
        sy2 = cy + r2 * math.cos(perp_rad)

        st.markdown(f"""
        <div style="text-align:center;">
        <svg width="130" height="130" viewBox="0 0 120 120">
          <!-- compass background -->
          <circle cx="60" cy="60" r="55" fill="#06111f" stroke="#FFD700" stroke-width="2"/>
          <!-- N label -->
          <text x="60" y="14" text-anchor="middle" fill="#94a3b8" font-size="9">N</text>
          <text x="60" y="112" text-anchor="middle" fill="#94a3b8" font-size="9">S</text>
          <text x="10" y="64" text-anchor="middle" fill="#94a3b8" font-size="9">W</text>
          <text x="110" y="64" text-anchor="middle" fill="#94a3b8" font-size="9">E</text>
          <!-- Road direction (yellow line) -->
          <line x1="{ex2:.1f}" y1="{ey2:.1f}" x2="{ex:.1f}" y2="{ey:.1f}"
                stroke="#FFD700" stroke-width="3" stroke-linecap="round"/>
          <!-- Strip direction (orange, perpendicular) -->
          <line x1="{sx2:.1f}" y1="{sy2:.1f}" x2="{sx:.1f}" y2="{sy:.1f}"
                stroke="#FF8C00" stroke-width="2" stroke-dasharray="4 2" stroke-linecap="round"/>
          <!-- Centre dot -->
          <circle cx="60" cy="60" r="4" fill="#FFD700"/>
          <!-- Legend -->
          <rect x="5" y="90" width="12" height="3" fill="#FFD700" rx="1"/>
          <text x="20" y="94" fill="#FFD700" font-size="8">Road {heading_val}°</text>
          <rect x="5" y="100" width="12" height="2" fill="#FF8C00" rx="1"/>
          <text x="20" y="104" fill="#FF8C00" font-size="8">Strip {strip_dir}°</text>
        </svg>
        <div style="color:#fde68a;font-size:.78rem;margin-top:2px;">
          Road: <b>{road_dir_name}</b><br/>
          Strip runs at <b>{strip_dir}°</b> (perpendicular)
        </div>
        </div>
        """, unsafe_allow_html=True)

        heading_override = float(heading_val)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="ok">✅ Manual heading active</div>', unsafe_allow_html=True)
    else:
        heading_override = -1.0
        st.markdown('</div>', unsafe_allow_html=True)
        use_osm = st.toggle("🌐 Try OSM (needs internet)", value=True)
        st.markdown('<div class="warn">⚠️ Auto-detect unreliable for clustered markers. '
                    'Use manual heading if strips are wrong angle.</div>',
                    unsafe_allow_html=True)

    st.markdown("---")

    # ── Road layout ───────────────────────────────────────────────────────────
    st.markdown("## 🛣️ Road Dimensions — MEASURE IN GOOGLE EARTH")

    with st.expander("📏 How to measure road width (MUST DO)", expanded=True):
        st.markdown("""
        **Step 1 — Measure TOTAL road width:**
        - Google Earth Pro → `Tools → Ruler → Line`
        - Draw across the road from left edge to right edge
        - Note the distance in metres

        **Step 2 — Measure SEPARATOR width:**
        - Draw across only the centre divider/kerb
        - Note the distance

        **Step 3 — Enter below:**
        - `Total Road Width` = Step 1 value
        - `Separator Width`  = Step 2 value
        - `Lane Width` = (Total − Separator) ÷ Lanes (auto-calculated)

        ⚠️ **If you set wrong values, strips will overflow onto buildings or be too narrow!**
        """)

    num_lanes    = st.number_input("Number of Lanes", 1, 8, 2, 1,
                                    help="2 = 1 going + 1 incoming")
    road_width_m = st.number_input(
        "Total Road Width (m) ← MEASURE THIS",
        min_value=2.0, max_value=60.0, value=14.0, step=0.5,
        help="Measure from outer edge to outer edge of the full carriageway in Google Earth Ruler")
    has_sep = st.toggle("Has Centre Separator/Divider", value=True)
    sep_w   = 0.0
    if has_sep and num_lanes > 1:
        sep_w = st.number_input(
            "Separator Width (m) ← MEASURE THIS",
            min_value=0.0, max_value=10.0, value=2.0, step=0.5,
            help="Measure only the centre divider width in Google Earth Ruler")

    drv_lw = (road_width_m - (sep_w if has_sep and num_lanes > 1 else 0.0)) / num_lanes

    # Visual road cross-section
    total_w = road_width_m
    sep_pct = (sep_w / total_w * 100) if has_sep and num_lanes > 1 else 0
    lane_pct = ((total_w - sep_w) / total_w * 100) / num_lanes if num_lanes > 0 else 50

    st.markdown(f"""
    <div style="background:#06111f;border:1px solid #1e3a5f;border-radius:8px;padding:10px 12px;margin-top:8px;">
      <div style="font-size:.75rem;color:#94a3b8;margin-bottom:6px;">Road cross-section preview:</div>
      <div style="display:flex;height:28px;border-radius:4px;overflow:hidden;font-size:.7rem;font-weight:700;">
        <div style="background:#FFD700;flex:{lane_pct:.0f};display:flex;align-items:center;justify-content:center;color:#000;">
          L1 {drv_lw:.1f}m
        </div>
        {'<div style="background:#4B5563;flex:' + f'{sep_pct:.0f}' + ';display:flex;align-items:center;justify-content:center;color:#9CA3AF;">SEP ' + f'{sep_w:.1f}m' + '</div>' if has_sep and num_lanes > 1 else ''}
        <div style="background:#FFA500;flex:{lane_pct:.0f};display:flex;align-items:center;justify-content:center;color:#000;">
          L2 {drv_lw:.1f}m
        </div>
      </div>
      <div style="font-size:.73rem;color:#60a5fa;margin-top:5px;">
        ← {road_width_m:.1f}m total road width →
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"↳ Strips will be **{drv_lw:.2f}m long** (one per lane)")

    st.markdown("---")

    # ── Strip spec ────────────────────────────────────────────────────────────
    st.markdown("## 🟨 Strip Specification")
    strip_mm   = st.number_input("Strip Width (mm)", 5.0, 200.0, 15.0, 5.0,
                                  help="CAP PTBM thickness: 10mm or 15mm")
    num_strips = st.number_input("Total Strips (all lanes)", 1, 60, 6, 1)
    gap_m      = st.number_input("Gap Between Strips (m)", 0.01, 2.0, 0.10, 0.05)

    spl = int(num_strips) // int(num_lanes)
    st.info(
        f"**{int(num_strips)} strips ÷ {int(num_lanes)} lanes = {spl}/lane**\n\n"
        f"Code: `CAP PTBM {int(strip_mm)}MM X {int(num_strips)}`\n\n"
        f"Strip: **{strip_mm}mm** × **{drv_lw:.2f}m** per lane"
    )


# ── Main columns ──────────────────────────────────────────────────────────────
cL, cR = st.columns([1, 1.7], gap="large")

with cL:
    st.markdown("### 📂 Upload KML")
    uploaded = st.file_uploader("KML from Google Earth Pro", type=["kml"])

    if uploaded:
        st.success(f"✅ **{uploaded.name}** — {uploaded.size:,} bytes")
        with tempfile.NamedTemporaryFile(suffix=".kml", delete=False) as tmp:
            tmp.write(uploaded.read()); tmp_path = tmp.name
        try:
            markers = parse_kml_markers(tmp_path)
            st.session_state.update({"markers": markers, "tmp_kml": tmp_path})

            # Spread analysis
            pca_h = pca_heading(markers)
            if len(markers) > 1:
                spread = max(
                    haversine_distance(markers[i].lat, markers[i].lon,
                                       markers[j].lat, markers[j].lon)
                    for i in range(len(markers))
                    for j in range(i+1, min(i+3, len(markers)))
                )
            else:
                spread = 0.0

            st.markdown(f"**{len(markers)} marker(s)** | spread ≈ {spread:.1f}m")

            if pca_h is not None:
                st.markdown(f'<div class="ok">🔵 PCA heading: <b>{pca_h:.1f}°</b> '
                            f'(auto-detected from marker spread)</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="warn">⚠️ Markers too close for auto-heading. '
                    'Use manual heading slider!</div>',
                    unsafe_allow_html=True)

            for mk in markers[:8]:
                st.markdown(
                    f'<div class="mk"><div class="n">📍 {mk.index}. {mk.name}</div>'
                    f'<div class="c">{mk.placement_code or "—"}</div>'
                    f'<div class="g">{mk.lat:.6f}, {mk.lon:.6f}</div></div>',
                    unsafe_allow_html=True)
            if len(markers) > 8:
                st.caption(f"… +{len(markers)-8} more")
        except Exception as e:
            st.error(f"KML parse error: {e}")

    # Lane diagram
    if uploaded and "markers" in st.session_state:
        st.markdown("### 🛤️ Cross-Road Layout")
        nl  = int(num_lanes)
        ns  = int(num_strips)
        b2  = ns // nl; r2 = ns % nl
        rows = []; sc = 1
        for li in range(nl):
            n_in = b2 + (1 if li < r2 else 0)
            sl   = " ".join([f"S{sc+i}" for i in range(n_in)]); sc += n_in
            rows.append(f"Lane {li+1} ({'→' if li%2==0 else '←'}): [{sl}]")
            if has_sep and num_lanes > 1 and li < nl-1:
                rows.append(f"    ~~~ SEP {sep_w:.1f}m ~~~")
        st.code("\n".join(rows), language=None)
        st.caption(
            f"Strip: {strip_mm}mm wide, {drv_lw:.2f}m long | "
            f"Perpendicular to road ({(heading_val+90)%180}°)"
            if use_manual else
            f"Strip: {strip_mm}mm wide, {drv_lw:.2f}m long"
        )

    st.markdown("---")
    st.markdown("### 🚀 Generate")
    gen = st.button("⚡ Generate Polygons & Export BOQ",
                    disabled=not uploaded, use_container_width=True)

    if gen and "tmp_kml" in st.session_state:
        spec = PolygonSpec(
            strip_width_mm       = float(strip_mm),
            num_strips           = int(num_strips),
            gap_between_strips_m = float(gap_m),
            num_lanes            = int(num_lanes),
            road_width_m         = float(road_width_m),
            separator_width_m    = float(sep_w),
            has_separator        = bool(has_sep),
            heading_override     = float(heading_override),
        )
        pb  = st.progress(0); txt = st.empty()
        def prog(i, tot, nm):
            pb.progress(int(i/tot*100)); txt.text(f"{i+1}/{tot}: {nm}")

        try:
            ko = st.session_state["tmp_kml"].replace(".kml","_out.kml")
            xo = st.session_state["tmp_kml"].replace(".kml","_out.xlsx")
            osm_flag = (not use_manual) and locals().get('use_osm', True)
            _, pols = run_pipeline(
                st.session_state["tmp_kml"], ko, xo, spec,
                use_osm=osm_flag, progress_callback=prog)
            pb.progress(100); time.sleep(0.3); pb.empty(); txt.empty()
            st.session_state.update({
                "polygons": pols, "out_kml": ko,
                "out_excel": xo, "spec": spec,
            })
            src_c = {}
            for pg in pols: src_c[pg.heading_source] = src_c.get(pg.heading_source,0)+1
            st.success(
                f"✅ {len(pols)} markers × {spec.num_strips} strips = "
                f"**{len(pols)*spec.num_strips} polygons**"
            )
            st.info("📡 " + " | ".join(f"{k}:{v}" for k,v in src_c.items()))
        except Exception as e:
            pb.empty(); txt.empty(); st.error(f"Error: {e}")
            import traceback; st.code(traceback.format_exc())

    if "out_kml" in st.session_state:
        st.markdown("---")
        st.markdown("### 📥 Download")
        with open(st.session_state["out_kml"],"rb") as f:
            st.download_button("⬇️ KML (Google Earth Pro)", f,
                               "speed_breaker_polygons.kml",
                               "application/vnd.google-earth.kml+xml",
                               use_container_width=True)
        with open(st.session_state["out_excel"],"rb") as f:
            st.download_button("⬇️ Excel BOQ Report", f,
                               "speed_breaker_BOQ.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        if use_manual:
            st.markdown(
                f'<div class="ok">Heading used: <b>{heading_val}°</b> (manual). '
                f'Strips run at {(heading_val+90)%180}°.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info2">💡 Strips still wrong angle? '
                        'Toggle "Set heading manually" in sidebar.</div>',
                        unsafe_allow_html=True)


# ── RIGHT: Map ─────────────────────────────────────────────────────────────────
with cR:
    st.markdown("### 🗺️ Satellite Preview")
    polygons = st.session_state.get("polygons")
    markers  = st.session_state.get("markers")
    spec     = st.session_state.get("spec")

    if polygons and markers and spec:
        # Stats
        curv = {"straight":0,"slight_curve":0,"sharp_curve":0}
        src_c = {}
        for pg in polygons:
            curv[pg.road_curvature] = curv.get(pg.road_curvature,0)+1
            src_c[pg.heading_source] = src_c.get(pg.heading_source,0)+1

        cols = st.columns(5)
        for col,(v,l) in zip(cols,[
            (len(polygons),"Markers"),
            (spec.num_strips,"Strips/mkr"),
            (spec.num_lanes,"Lanes"),
            (curv["sharp_curve"],"Sharp Curves"),
            (len(polygons)*spec.num_strips,"Total Strips"),
        ]):
            with col:
                st.markdown(f'<div class="stat"><div class="v">{v}</div>'
                            f'<div class="l">{l}</div></div>',
                            unsafe_allow_html=True)

        src_html = " ".join(
            f'<span style="background:#1e3a5f;color:#93c5fd;border-radius:10px;'
            f'padding:2px 8px;font-size:.75rem;font-weight:700;">{k}:{v}</span>'
            for k,v in src_c.items())
        st.markdown(f'<div style="margin:8px 0;font-size:.8rem;color:#94a3b8;">'
                    f'📡 Heading: {src_html}</div>', unsafe_allow_html=True)

        if spec.has_separator and spec.num_lanes > 1:
            lw2 = (spec.road_width_m - spec.separator_width_m) / spec.num_lanes
            st.markdown(
                f'<div style="background:#06111f;border:1px solid #FFD700;'
                f'border-radius:7px;padding:6px 12px;font-size:.79rem;'
                f'color:#fde68a;margin-bottom:6px;">'
                f'🚧 Sep: {spec.separator_width_m}m | Lane: {lw2:.2f}m | '
                f'Heading: {spec.heading_deg if hasattr(spec,"heading_deg") else spec.heading_override:.0f}°</div>',
                unsafe_allow_html=True)

        # Map
        avg_lat = sum(m.lat for m in markers)/len(markers)
        avg_lon = sum(m.lon for m in markers)/len(markers)
        fmap = folium.Map(
            location=[avg_lat, avg_lon], zoom_start=18,
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google Satellite")
        folium.TileLayer("OpenStreetMap", name="Street").add_to(fmap)
        folium.LayerControl().add_to(fmap)

        LC = ["#FFD700","#FFA500","#FF6B00","#FFEC00"]
        CC = {"straight":"green","slight_curve":"orange","sharp_curve":"red"}

        for pg in polygons:
            mk = pg.marker
            popup = (
                f"<b>{mk.name}</b><br/>"
                f"Heading: {pg.heading_deg:.1f}° [{pg.heading_source}]<br/>"
                f"Curvature: {pg.road_curvature.replace('_',' ').title()}<br/>"
                f"Lanes: {spec.num_lanes} | Strips: {spec.num_strips}<br/>"
                f"Code: {mk.placement_code or '—'}<br/>"
                f"{mk.lat:.6f}, {mk.lon:.6f}"
            )
            folium.Marker(
                [mk.lat, mk.lon],
                popup=folium.Popup(popup, max_width=240),
                tooltip=f"{mk.name} [{pg.heading_deg:.0f}°]",
                icon=folium.Icon(color=CC.get(pg.road_curvature,"blue"),
                                  icon='road', prefix='fa'),
            ).add_to(fmap)

            for strip, ln in zip(pg.strip_polygons, pg.lane_assignments):
                ll = [[la, lo] for lo, la in strip]
                c  = LC[(ln-1) % len(LC)]
                folium.Polygon(
                    locations=ll, color=c, fill=True,
                    fill_color=c, fill_opacity=0.85,
                    weight=1.5,
                    tooltip=f"{mk.name} Lane {ln}",
                ).add_to(fmap)

            if len(pg.coordinates) >= 3:
                folium.Polygon(
                    locations=[[la,lo] for lo,la in pg.coordinates],
                    color="#FF4444", fill=False, weight=2, dash_array="5",
                ).add_to(fmap)

        st_folium(fmap, width="100%", height=490, returned_objects=[])

        st.markdown("""<div style="display:flex;gap:10px;flex-wrap:wrap;
            font-size:.77rem;color:#94a3b8;margin-top:5px;">
          <span>🟡 Lane 1 (going)</span><span>🟠 Lane 2 (incoming)</span>
          <span>🔴 Bounding outline</span>
          <span>🟢 Straight road</span><span>🟡 Slight curve</span><span>🔴 Sharp curve</span>
        </div>""", unsafe_allow_html=True)

        # Detail table
        st.markdown("### 📋 Details")
        rows = []
        for pg in polygons:
            cb = {"straight":"🟢","slight_curve":"🟡","sharp_curve":"🔴"}.get(pg.road_curvature,"")
            sb = {"osm":"🟢OSM","pca":"🔵PCA","manual":"🟡Man",
                  "neighbour":"🔴Nbr"}.get(pg.heading_source, pg.heading_source)
            rows.append({
                "#": pg.marker.index, "Name": pg.marker.name,
                "Code": pg.marker.placement_code or "—",
                "Lat": f"{pg.marker.lat:.5f}", "Lon": f"{pg.marker.lon:.5f}",
                "Hdg°": f"{pg.heading_deg:.1f}", "Src": sb,
                "Road": f"{cb} {pg.road_curvature.replace('_',' ')}",
                "L": spec.num_lanes, "S": spec.num_strips,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True,
                     hide_index=True, height=220)

    elif markers:
        avg_lat = sum(m.lat for m in markers)/len(markers)
        avg_lon = sum(m.lon for m in markers)/len(markers)
        fmap = folium.Map(location=[avg_lat,avg_lon], zoom_start=16, tiles="OpenStreetMap")
        for mk in markers:
            folium.Marker([mk.lat,mk.lon], tooltip=mk.name,
                          icon=folium.Icon(color='orange',icon='map-marker')).add_to(fmap)
        st_folium(fmap, width="100%", height=380, returned_objects=[])
        st.info("Set road heading in sidebar → click Generate")

    else:
        st.markdown("""<div style="background:#0d1a2e;border-radius:12px;
            padding:50px 25px;text-align:center;border:1px dashed #1e3a5f;">
          <div style="font-size:3rem">🗺️</div>
          <div style="color:#64748b;margin-top:11px">Upload KML to begin</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("### 📖 Steps")
        for n, d in [
            ("1", "Mark speed breaker locations in Google Earth Pro → Save as KML"),
            ("2", "Upload the KML file above"),
            ("3", "⚠️ Open Google Earth → Ruler tool → draw along road → note heading angle"),
            ("4", "Set that angle in the sidebar slider (0–179°)"),
            ("5", "Set number of lanes, road width, separator if present"),
            ("6", "Set strip spec (15mm × 6 strips etc.)"),
            ("7", "Click Generate → parallel strips perpendicular to road"),
            ("8", "Download KML for Google Earth Pro + Excel BOQ"),
        ]:
            st.markdown(f'<div class="step"><span class="n">Step {n}</span>{d}</div>',
                        unsafe_allow_html=True)

        st.markdown("""<div class="info2">
        💡 <b>Heading reference:</b><br/>
        Road going N–S → set 0° | E–W → set 90° | NE–SW → set 45° | SE–NW → set 135°<br/>
        <b>From your screenshot: road looks like ~130–140° (SE direction)</b>
        </div>""", unsafe_allow_html=True)