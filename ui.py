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
#     st.markdown("## 🛣️ Road Dimensions — MEASURE IN GOOGLE EARTH")

#     with st.expander("📏 How to measure road width (MUST DO)", expanded=True):
#         st.markdown("""
#         **Step 1 — Measure TOTAL road width:**
#         - Google Earth Pro → `Tools → Ruler → Line`
#         - Draw across the road from left edge to right edge
#         - Note the distance in metres

#         **Step 2 — Measure SEPARATOR width:**
#         - Draw across only the centre divider/kerb
#         - Note the distance

#         **Step 3 — Enter below:**
#         - `Total Road Width` = Step 1 value
#         - `Separator Width`  = Step 2 value
#         - `Lane Width` = (Total − Separator) ÷ Lanes (auto-calculated)

#         ⚠️ **If you set wrong values, strips will overflow onto buildings or be too narrow!**
#         """)

#     num_lanes    = st.number_input("Number of Lanes", 1, 8, 2, 1,
#                                     help="2 = 1 going + 1 incoming")
#     road_width_m = st.number_input(
#         "Total Road Width (m) ← MEASURE THIS",
#         min_value=2.0, max_value=60.0, value=14.0, step=0.5,
#         help="Measure from outer edge to outer edge of the full carriageway in Google Earth Ruler")
#     has_sep = st.toggle("Has Centre Separator/Divider", value=True)
#     sep_w   = 0.0
#     if has_sep and num_lanes > 1:
#         sep_w = st.number_input(
#             "Separator Width (m) ← MEASURE THIS",
#             min_value=0.0, max_value=10.0, value=2.0, step=0.5,
#             help="Measure only the centre divider width in Google Earth Ruler")

#     drv_lw = (road_width_m - (sep_w if has_sep and num_lanes > 1 else 0.0)) / num_lanes

#     # Visual road cross-section
#     total_w = road_width_m
#     sep_pct = (sep_w / total_w * 100) if has_sep and num_lanes > 1 else 0
#     lane_pct = ((total_w - sep_w) / total_w * 100) / num_lanes if num_lanes > 0 else 50

#     st.markdown(f"""
#     <div style="background:#06111f;border:1px solid #1e3a5f;border-radius:8px;padding:10px 12px;margin-top:8px;">
#       <div style="font-size:.75rem;color:#94a3b8;margin-bottom:6px;">Road cross-section preview:</div>
#       <div style="display:flex;height:28px;border-radius:4px;overflow:hidden;font-size:.7rem;font-weight:700;">
#         <div style="background:#FFD700;flex:{lane_pct:.0f};display:flex;align-items:center;justify-content:center;color:#000;">
#           L1 {drv_lw:.1f}m
#         </div>
#         {'<div style="background:#4B5563;flex:' + f'{sep_pct:.0f}' + ';display:flex;align-items:center;justify-content:center;color:#9CA3AF;">SEP ' + f'{sep_w:.1f}m' + '</div>' if has_sep and num_lanes > 1 else ''}
#         <div style="background:#FFA500;flex:{lane_pct:.0f};display:flex;align-items:center;justify-content:center;color:#000;">
#           L2 {drv_lw:.1f}m
#         </div>
#       </div>
#       <div style="font-size:.73rem;color:#60a5fa;margin-top:5px;">
#         ← {road_width_m:.1f}m total road width →
#       </div>
#     </div>
#     """, unsafe_allow_html=True)
#     st.caption(f"↳ Strips will be **{drv_lw:.2f}m long** (one per lane)")

#     st.markdown("---")

#     # ── Strip spec ────────────────────────────────────────────────────────────
#     st.markdown("## 🟨 Strip Specification")

#     strip_mm   = st.number_input("Strip Width (mm)", 5.0, 200.0, 15.0, 5.0,
#                                   help="CAP PTBM thickness along road direction: 10mm or 15mm")
#     num_strips = st.number_input("Total Strips (all lanes)", 1, 60, 6, 1)
#     gap_m      = st.number_input("Gap Between Strips (m)", 0.01, 2.0, 0.10, 0.05,
#                                   help="Along-road spacing between consecutive strips")

#     # ── Lane Group Gap ────────────────────────────────────────────────────────
#     st.markdown("**Gap Between Lane Groups (at road centre)**")
#     # Auto-default = separator_width + 10% of lane_w, min 0.5m
#     _auto_lane_gap = round(sep_w + max(0.3, drv_lw * 0.10), 2) if has_sep and num_lanes > 1 else 0.0
#     use_manual_gap = st.toggle(
#         "Override lane group gap manually",
#         value=False,
#         help=(
#             "The clear zone between Lane 1 strips and Lane 2 strips at road centre. "
#             f"Auto-default = separator ({sep_w}m) + 10% of lane width = {_auto_lane_gap:.2f}m. "
#             "Increase this if the two lane groups look too close in Google Earth."
#         )
#     )
#     if use_manual_gap and num_lanes > 1:
#         lane_gap_m = st.number_input(
#             "Lane Group Gap (m)  ← manual",
#             min_value=0.1,
#             max_value=float(road_width_m) / 2.0,
#             value=_auto_lane_gap,
#             step=0.25,
#             help="Total clear space at road centre between the two groups of strips"
#         )
#         st.caption(f"↳ Each lane group starts **{lane_gap_m/2:.2f}m** from road centre")
#     else:
#         lane_gap_m = -1.0   # signal auto
#         if num_lanes > 1:
#             st.caption(
#                 f"↳ Auto gap = **{_auto_lane_gap:.2f}m** "
#                 f"(sep {sep_w:.1f}m + {max(0.3, drv_lw*0.10):.2f}m clearance)"
#             )

#     # ── Strip Length (manual override) ───────────────────────────────────────
#     st.markdown("**Strip Length (across road)**")
#     use_manual_len = st.toggle(
#         "Override strip length manually",
#         value=False,
#         help=(
#             "By default, strip length = lane width (auto from road width ÷ lanes). "
#             "Enable this to set a custom length — useful when your actual painted "
#             "strip is shorter than the full lane width."
#         )
#     )

#     if use_manual_len:
#         strip_length_m = st.number_input(
#             "Strip Length (m)  ← manual",
#             min_value=0.5,
#             max_value=float(road_width_m),
#             value=round(drv_lw, 1),
#             step=0.5,
#             help=(
#                 "Length of each strip measured across the road "
#                 "(perpendicular to traffic direction). "
#                 "Default = lane width = (road_width − separator) ÷ lanes"
#             )
#         )
#         # Warn if manual length exceeds lane width
#         if strip_length_m > drv_lw + 0.1:
#             st.markdown(
#                 f'<div style="background:#3b1f00;border:1px solid #d97706;'
#                 f'border-radius:7px;padding:7px 11px;color:#fde68a;font-size:.78rem;">'
#                 f'⚠️ Length {strip_length_m:.1f}m exceeds lane width {drv_lw:.2f}m '
#                 f'— strip may overflow into separator or opposite lane.</div>',
#                 unsafe_allow_html=True
#             )
#         elif strip_length_m < drv_lw - 0.5:
#             st.markdown(
#                 f'<div style="background:#052e16;border:1px solid #16a34a;'
#                 f'border-radius:7px;padding:7px 11px;color:#86efac;font-size:.78rem;">'
#                 f'✅ Strip shorter than lane — leaves {drv_lw - strip_length_m:.2f}m '
#                 f'clearance from road edge.</div>',
#                 unsafe_allow_html=True
#             )
#     else:
#         strip_length_m = drv_lw   # auto = full lane width
#         st.caption(f"↳ Auto: **{drv_lw:.2f}m** (= lane width from road dimensions above)")

#     spl = int(num_strips) // int(num_lanes)
#     area_one = (strip_mm / 1000.0) * strip_length_m
#     area_total = area_one * int(num_strips)

#     st.info(
#         f"**{int(num_strips)} strips ÷ {int(num_lanes)} lanes = {spl}/lane**\n\n"
#         f"Code: `CAP PTBM {int(strip_mm)}MM X {int(num_strips)}`\n\n"
#         f"Strip: **{strip_mm}mm** × **{strip_length_m:.2f}m** "
#         f"{'(manual)' if use_manual_len else '(auto)'}\n\n"
#         f"Area/strip: **{area_one:.4f} Sqm** | Total: **{area_total:.4f} Sqm**"
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
#             strip_width_mm           = float(strip_mm),
#             num_strips               = int(num_strips),
#             gap_between_strips_m     = float(gap_m),
#             strip_length_override_m  = float(strip_length_m) if use_manual_len else -1.0,
#             num_lanes                = int(num_lanes),
#             road_width_m             = float(road_width_m),
#             separator_width_m        = float(sep_w),
#             has_separator            = bool(has_sep),
#             lane_gap_m               = float(lane_gap_m) if use_manual_gap and num_lanes > 1 else -1.0,
#             heading_override         = float(heading_override),
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
ui.py  v6  —  Speed Breaker GIS BOQ Tool
Per-marker heading assignment with range support
IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI
Run:  streamlit run ui.py
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
    page_title="GIS BOQ — Speed Breaker v6",
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
.banner h1{color:#FFD700;font-size:1.65rem;font-weight:700;margin:0 0 4px;}
.banner p{color:#94a3b8;font-size:.86rem;margin:0;}
.tag{display:inline-block;background:#1e3a5f;color:#60a5fa;border-radius:20px;
  padding:2px 10px;font-size:.7rem;font-weight:600;margin:5px 4px 0 0;}
.hdg-panel{background:#06111f;border:2px solid #FFD700;border-radius:12px;
  padding:14px 16px;margin-bottom:12px;}
.hdg-panel h4{color:#FFD700;margin:0 0 8px;font-size:.9rem;}
.stat{background:#0d1a2e;border:1px solid #1e3a5f;border-left:4px solid #FFD700;
  border-radius:9px;padding:11px 12px;text-align:center;}
.stat .v{font-size:1.5rem;font-weight:700;color:#FFD700;}
.stat .l{font-size:.65rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;}
.mk-row{background:#0d1a2e;border:1px solid #1e3a5f;border-left:3px solid #FFD700;
  border-radius:7px;padding:7px 11px;margin-bottom:5px;
  font-family:'JetBrains Mono',monospace;font-size:.75rem;}
.mk-row.curve{border-left-color:#FF8C00;}
.mk-row .n{color:#FFD700;font-weight:600;margin-bottom:2px;}
.mk-row.curve .n{color:#FF8C00;}
.warn{background:#2d1400;border:1px solid #d97706;border-radius:7px;
  padding:8px 12px;color:#fde68a;font-size:.8rem;margin:6px 0;}
.ok{background:#052e16;border:1px solid #16a34a;border-radius:7px;
  padding:8px 12px;color:#86efac;font-size:.8rem;margin:6px 0;}
.hdg-table{background:#06111f;border:1px solid #1e3a5f;border-radius:10px;
  padding:14px 16px;margin:10px 0;}
.hdg-table h5{color:#FFD700;margin:0 0 10px;font-size:.88rem;}
.range-row{background:#0d1a2e;border-radius:6px;padding:8px 10px;
  margin-bottom:6px;border:1px solid #1e3a5f;display:flex;
  align-items:center;gap:8px;font-size:.8rem;}
div[data-testid="stSidebar"]{background:#050d1a;}
.stButton>button{background:linear-gradient(135deg,#d97706,#b45309);
  color:#fff;border:none;border-radius:8px;font-weight:600;transition:all .2s;}
.stButton>button:hover{transform:translateY(-1px);}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="banner">
  <h1>🚧 GIS BOQ Tool — CAP PTBM Speed Breaker Generator v6</h1>
  <p>Per-marker heading assignment for curves · Parallel strips · BOQ Excel</p>
  <span class="tag">IIIT Nagpur</span><span class="tag">Dr. Neha Kasture</span>
  <span class="tag">PWD/NHAI</span><span class="tag">v6 — Per-marker heading</span>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧭 Global Road Heading")
    st.markdown('<div class="hdg-panel"><h4>Default heading for ALL markers</h4>',
                unsafe_allow_html=True)
    st.markdown("Set the straight-road angle. You can override individual markers below after uploading.")

    use_manual = st.toggle("✏️ Set global heading manually", value=True)
    heading_val = 0
    if use_manual:
        heading_val = st.slider("Global Heading (°)", 0, 179, 45, 1,
                                 help="0=N–S | 45=NE–SW | 90=E–W | 135=SE–NW")
        strip_dir = (heading_val + 90) % 180
        st.caption(f"Road: {heading_val}° | Strips run at: {strip_dir}°")
        heading_override = float(heading_val)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="ok">✅ Global heading set</div>', unsafe_allow_html=True)
    else:
        heading_override = -1.0
        use_osm = st.toggle("🌐 Try OSM", value=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="warn">⚠️ Auto-detect. Use manual if strips wrong angle.</div>',
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 🛣️ Road Dimensions")
    num_lanes    = st.number_input("Number of Lanes", 1, 8, 2, 1)
    road_width_m = st.number_input("Total Road Width (m) ← MEASURE IN GEP", 2.0, 60.0, 7.0, 0.5)
    has_sep      = st.toggle("Has Centre Separator", value=True)
    sep_w        = 0.0
    if has_sep and num_lanes > 1:
        sep_w = st.number_input("Separator Width (m) ← MEASURE IN GEP", 0.0, 10.0, 0.5, 0.25)
    drv_lw = (road_width_m - (sep_w if has_sep and num_lanes > 1 else 0.0)) / num_lanes

    _auto_gap = round(sep_w + max(0.3, drv_lw * 0.10), 2) if has_sep and num_lanes > 1 else 0.0
    use_manual_gap = st.toggle("Override lane group gap", value=False)
    lane_gap_m = -1.0
    if use_manual_gap and num_lanes > 1:
        lane_gap_m = st.number_input("Lane Group Gap (m)", 0.1, road_width_m/2, _auto_gap, 0.25)
    else:
        if num_lanes > 1:
            st.caption(f"↳ Auto gap = {_auto_gap:.2f}m")

    st.markdown("---")
    st.markdown("## 🟨 Strip Specification")
    strip_mm   = st.number_input("Strip Width (mm)", 5.0, 200.0, 15.0, 5.0)
    num_strips = st.number_input("Total Strips (all lanes)", 1, 60, 6, 1)
    gap_m      = st.number_input("Gap Between Strips (m)", 0.01, 2.0, 0.10, 0.05)

    use_manual_len = st.toggle("Override strip length", value=False)
    strip_length_m = drv_lw
    if use_manual_len:
        strip_length_m = st.number_input("Strip Length (m)", 0.5, road_width_m, round(drv_lw,1), 0.5)

    spl = int(num_strips)//int(num_lanes)
    st.info(f"**{int(num_strips)} ÷ {int(num_lanes)} = {spl}/lane** | "
            f"`CAP PTBM {int(strip_mm)}MM X {int(num_strips)}`\n\n"
            f"Strip: **{strip_mm}mm × {strip_length_m:.2f}m**")


# ── Main columns ──────────────────────────────────────────────────────────────
cL, cR = st.columns([1, 1.8], gap="large")

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
            if "per_marker_headings" not in st.session_state:
                st.session_state["per_marker_headings"] = {}
            pca_h = pca_heading(markers)
            st.markdown(f"**{len(markers)} marker(s) loaded**")
            if pca_h:
                st.markdown(f'<div class="ok">🔵 PCA heading: <b>{pca_h:.1f}°</b></div>',
                            unsafe_allow_html=True)
        except Exception as e:
            st.error(f"KML error: {e}")

    # ── Per-Marker Heading Assignment ─────────────────────────────────────────
    if "markers" in st.session_state:
        markers = st.session_state["markers"]
        pmh     = st.session_state.get("per_marker_headings", {})

        st.markdown("---")
        st.markdown("### 🎯 Per-Marker Heading Assignments")
        st.markdown("""
        <div style="background:#06111f;border:1px solid #1e3a5f;border-radius:8px;
          padding:10px 14px;font-size:.8rem;color:#94a3b8;margin-bottom:10px;">
        💡 <b>How to use:</b><br/>
        • Straight section markers → leave blank (uses global heading)<br/>
        • Curve markers → set individual angle (measured in Google Earth Pro)<br/>
        • Use <b>Set Range</b> to assign one angle to many markers at once
        </div>
        """, unsafe_allow_html=True)

        # ── Range assignment tool ─────────────────────────────────────────────
        with st.expander("⚡ Quick Range Assignment", expanded=True):
            st.markdown("Set the **same heading for a range of markers** in one click:")
            rc1, rc2, rc3 = st.columns([1, 1, 1])
            with rc1:
                range_from = st.number_input("From marker #", 1, len(markers), 1, 1, key="rf")
            with rc2:
                range_to   = st.number_input("To marker #",   1, len(markers), min(6, len(markers)), 1, key="rt")
            with rc3:
                range_hdg  = st.number_input("Heading (°)",   0, 179, int(heading_val) if use_manual else 45, 1, key="rh")

            rcol1, rcol2 = st.columns(2)
            with rcol1:
                if st.button("✅ Apply to Range", use_container_width=True):
                    for mk_i in range(int(range_from), int(range_to) + 1):
                        pmh[mk_i] = float(range_hdg)
                    st.session_state["per_marker_headings"] = pmh
                    st.success(f"Set markers {int(range_from)}–{int(range_to)} → {range_hdg}°")
                    st.rerun()
            with rcol2:
                if st.button("🗑️ Clear Range", use_container_width=True):
                    for mk_i in range(int(range_from), int(range_to) + 1):
                        pmh.pop(mk_i, None)
                    st.session_state["per_marker_headings"] = pmh
                    st.rerun()

        # ── Individual marker table ───────────────────────────────────────────
        st.markdown("**Individual Marker Headings:**")

        # Show all markers in a compact table
        cols_per_row = 1
        for mk in markers:
            has_override = mk.index in pmh
            cur_hdg = pmh.get(mk.index, None)

            mc1, mc2, mc3 = st.columns([2, 1.5, 0.8])
            with mc1:
                is_curve = has_override
                style_cls = "curve" if is_curve else ""
                st.markdown(
                    f'<div class="mk-row {style_cls}">'
                    f'<div class="n">📍 {mk.index}. {mk.name}</div>'
                    f'<div style="color:#6b7280;">{mk.lat:.5f}, {mk.lon:.5f}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with mc2:
                new_val = st.number_input(
                    f"Heading°",
                    min_value=0, max_value=179,
                    value=int(cur_hdg) if cur_hdg is not None else int(heading_val if use_manual else 45),
                    step=1,
                    key=f"mk_hdg_{mk.index}",
                    label_visibility="collapsed",
                    help=f"Heading for marker {mk.index}. Change to override."
                )
            with mc3:
                if st.button("📌 Set", key=f"set_{mk.index}", use_container_width=True):
                    pmh[mk.index] = float(new_val)
                    st.session_state["per_marker_headings"] = pmh
                    st.rerun()
                if has_override:
                    if st.button("✖", key=f"clr_{mk.index}", use_container_width=True,
                                  help="Remove per-marker override"):
                        pmh.pop(mk.index, None)
                        st.session_state["per_marker_headings"] = pmh
                        st.rerun()

        # Summary of overrides
        if pmh:
            st.markdown("---")
            st.markdown(f"**Active overrides: {len(pmh)} markers**")
            override_rows = []
            for mk_i, hdg in sorted(pmh.items()):
                mk_name = next((m.name for m in markers if m.index == mk_i), f"M{mk_i}")
                override_rows.append({"Marker #": mk_i, "Name": mk_name, "Heading°": hdg})
            st.dataframe(pd.DataFrame(override_rows), use_container_width=True,
                         hide_index=True, height=min(200, 40 + 36*len(override_rows)))

            if st.button("🗑️ Clear ALL overrides", use_container_width=True):
                st.session_state["per_marker_headings"] = {}
                st.rerun()

    st.markdown("---")
    st.markdown("### 🚀 Generate")
    gen = st.button("⚡ Generate Polygons & Export BOQ",
                    disabled=not uploaded, use_container_width=True)

    if gen and "tmp_kml" in st.session_state:
        pmh = st.session_state.get("per_marker_headings", {})
        spec = PolygonSpec(
            strip_width_mm          = float(strip_mm),
            num_strips              = int(num_strips),
            gap_between_strips_m    = float(gap_m),
            strip_length_override_m = float(strip_length_m) if use_manual_len else -1.0,
            num_lanes               = int(num_lanes),
            road_width_m            = float(road_width_m),
            separator_width_m       = float(sep_w),
            has_separator           = bool(has_sep),
            lane_gap_m              = float(lane_gap_m) if use_manual_gap and num_lanes>1 else -1.0,
            heading_override        = float(heading_override),
        )
        pb = st.progress(0); txt = st.empty()
        def prog(i, tot, nm):
            pb.progress(int(i/tot*100)); txt.text(f"{i+1}/{tot}: {nm}")
        try:
            ko = st.session_state["tmp_kml"].replace(".kml","_out.kml")
            xo = st.session_state["tmp_kml"].replace(".kml","_out.xlsx")
            osm_flag = (not use_manual) and locals().get('use_osm', True)
            _, pols = run_pipeline(
                st.session_state["tmp_kml"], ko, xo, spec,
                per_marker_headings=pmh,
                use_osm=osm_flag,
                progress_callback=prog)
            pb.progress(100); time.sleep(0.3); pb.empty(); txt.empty()
            st.session_state.update({
                "polygons": pols, "out_kml": ko, "out_excel": xo, "spec": spec})

            src_c = {}
            for pg in pols: src_c[pg.heading_source] = src_c.get(pg.heading_source,0)+1
            curve_count = sum(1 for pg in pols if pg.heading_source=="per-marker")
            st.success(
                f"✅ {len(pols)} markers × {spec.num_strips} strips = "
                f"**{len(pols)*spec.num_strips} polygons**")
            if curve_count:
                st.warning(f"🔶 {curve_count} markers used per-marker heading (curve overrides)")
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


# ── RIGHT: Map ────────────────────────────────────────────────────────────────
with cR:
    st.markdown("### 🗺️ Satellite Preview")
    polygons = st.session_state.get("polygons")
    markers  = st.session_state.get("markers")
    spec     = st.session_state.get("spec")
    pmh_disp = st.session_state.get("per_marker_headings", {})

    if polygons and markers and spec:
        curv = {"straight":0,"slight_curve":0,"sharp_curve":0}
        src_c = {}
        curve_markers = []
        for pg in polygons:
            curv[pg.road_curvature] = curv.get(pg.road_curvature,0)+1
            src_c[pg.heading_source] = src_c.get(pg.heading_source,0)+1
            if pg.heading_source == "per-marker":
                curve_markers.append(pg.marker.index)

        cols = st.columns(5)
        for col,(v,l) in zip(cols,[
            (len(polygons),"Markers"),
            (spec.num_strips,"Strips/mkr"),
            (spec.num_lanes,"Lanes"),
            (len(curve_markers),"Curve Overrides"),
            (len(polygons)*spec.num_strips,"Total Strips"),
        ]):
            with col:
                st.markdown(f'<div class="stat"><div class="v">{v}</div>'
                            f'<div class="l">{l}</div></div>', unsafe_allow_html=True)

        if curve_markers:
            st.markdown(
                f'<div class="warn">🔶 Per-marker heading active on markers: '
                f'<b>{", ".join(str(i) for i in sorted(curve_markers))}</b> '
                f'— shown as 🔴 red pins in map</div>',
                unsafe_allow_html=True)

        avg_lat = sum(m.lat for m in markers)/len(markers)
        avg_lon = sum(m.lon for m in markers)/len(markers)
        fmap = folium.Map(
            location=[avg_lat,avg_lon], zoom_start=17,
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google Satellite")
        folium.TileLayer("OpenStreetMap",name="Street").add_to(fmap)
        folium.LayerControl().add_to(fmap)

        LC = ["#FFD700","#FFA500","#00FF88","#AA00FF"]

        for pg in polygons:
            mk = pg.marker
            is_curve_mk = pg.heading_source == "per-marker"
            icon_color = "red" if is_curve_mk else \
                         {"straight":"green","slight_curve":"orange","sharp_curve":"red"}.get(pg.road_curvature,"blue")
            popup = (
                f"<b>{mk.name}</b><br/>"
                f"Heading: <b>{pg.heading_deg:.1f}°</b> [{pg.heading_source}]<br/>"
                f"{'🔶 PER-MARKER OVERRIDE<br/>' if is_curve_mk else ''}"
                f"Curvature: {pg.road_curvature.replace('_',' ').title()}<br/>"
                f"Lanes: {spec.num_lanes} | Strips: {spec.num_strips}<br/>"
                f"{mk.lat:.6f}, {mk.lon:.6f}"
            )
            folium.Marker(
                [mk.lat,mk.lon],
                popup=folium.Popup(popup,max_width=250),
                tooltip=f"M{mk.index}: {pg.heading_deg:.0f}°[{pg.heading_source}]",
                icon=folium.Icon(
                    color=icon_color,
                    icon='exclamation-circle' if is_curve_mk else 'road',
                    prefix='fa'),
            ).add_to(fmap)

            for strip, ln in zip(pg.strip_polygons, pg.lane_assignments):
                ll = [[la,lo] for lo,la in strip]
                c  = LC[(ln-1) % len(LC)]
                folium.Polygon(
                    locations=ll, color=c, fill=True,
                    fill_color=c, fill_opacity=0.85,
                    weight=1.5,
                    tooltip=f"M{mk.index} L{ln} {pg.heading_deg:.0f}°",
                ).add_to(fmap)

            if len(pg.coordinates) >= 3:
                folium.Polygon(
                    locations=[[la,lo] for lo,la in pg.coordinates],
                    color="#FF4444",fill=False,weight=2,dash_array="5",
                ).add_to(fmap)

        st_folium(fmap, width="100%", height=460, returned_objects=[])

        # Heading summary table
        st.markdown("### 📋 Heading Summary")
        rows = []
        for pg in polygons:
            src_icon = {"per-marker":"🔶","global":"🟡","osm":"🟢",
                        "pca":"🔵","neighbour":"🔴"}.get(pg.heading_source,"⚪")
            curv_icon = {"straight":"🟢","slight_curve":"🟡","sharp_curve":"🔴"}.get(pg.road_curvature,"")
            rows.append({
                "#":  pg.marker.index,
                "Name": pg.marker.name[:20],
                "Heading°": f"{pg.heading_deg:.1f}",
                "Source": f"{src_icon} {pg.heading_source}",
                "Curve": f"{curv_icon} {pg.road_curvature.replace('_',' ')}",
                "Override": f"✅ {pmh_disp[pg.marker.index]:.0f}°" if pg.marker.index in pmh_disp else "—",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True,
                     height=min(400, 40+36*len(rows)))

    elif markers:
        avg_lat = sum(m.lat for m in markers)/len(markers)
        avg_lon = sum(m.lon for m in markers)/len(markers)
        fmap = folium.Map(location=[avg_lat,avg_lon],zoom_start=16,tiles="OpenStreetMap")
        for mk in markers:
            has_ov = mk.index in st.session_state.get("per_marker_headings",{})
            folium.Marker([mk.lat,mk.lon],
                          tooltip=f"M{mk.index}: {mk.name}" + (f" [{st.session_state['per_marker_headings'][mk.index]:.0f}°]" if has_ov else ""),
                          icon=folium.Icon(color='orange' if not has_ov else 'red',
                                           icon='map-marker')).add_to(fmap)
        st_folium(fmap, width="100%", height=380, returned_objects=[])

        # Show heading assignment preview even before generate
        pmh_cur = st.session_state.get("per_marker_headings",{})
        if pmh_cur:
            st.markdown("**Heading assignments set (not yet generated):**")
            prev_rows=[{"#":i,"Heading°":h} for i,h in sorted(pmh_cur.items())]
            st.dataframe(pd.DataFrame(prev_rows),use_container_width=True,hide_index=True,height=150)
        st.info("Set per-marker headings above → click Generate")

    else:
        st.markdown("""<div style="background:#0d1a2e;border-radius:12px;
            padding:50px 25px;text-align:center;border:1px dashed #1e3a5f;">
          <div style="font-size:3rem">🗺️</div>
          <div style="color:#64748b;margin-top:11px">Upload KML to begin</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("### 📖 Per-Marker Heading Workflow")
        for n,d in [
            ("1","Upload KML — all markers load in left panel"),
            ("2","Set global heading for straight sections (sidebar slider)"),
            ("3","Use ⚡ Quick Range to assign one angle to markers 1–6 in one click"),
            ("4","For each curve marker (e.g. M7, M8), click 📌 Set with its angle"),
            ("5","Click Generate — straight markers use global, curve markers use their own angle"),
            ("6","Map shows 🔶 orange highlight for per-marker overrides"),
            ("7","Excel includes 'Heading Assignments' sheet showing every marker's source"),
        ]:
            st.markdown(
                f'<div style="background:#0d1a2e;border-radius:7px;padding:9px 13px;'
                f'margin-bottom:6px;border:1px solid #1e3a5f;">'
                f'<span style="color:#FFD700;font-weight:700;margin-right:8px;">Step {n}</span>{d}</div>',
                unsafe_allow_html=True)