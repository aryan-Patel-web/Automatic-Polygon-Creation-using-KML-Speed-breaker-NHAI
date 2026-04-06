# """
# ui2.py v1 — Speed Breaker GIS BOQ Tool (Center Marker Only)
# IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI
# Run: streamlit run ui2.py
# """
# import streamlit as st
# import tempfile, os, math, time
# import pandas as pd
# import folium
# from streamlit_folium import st_folium

# from p2 import (
#     PolySpec, KMLMarker, GenPoly,
#     parse_kml, run_pipeline, export_kml, export_excel,
#     LANE_PRESETS, haversine, norm180,
# )

# # ── Page config ────────────────────────────────────────────────────
# st.set_page_config(
#     page_title="GIS BOQ Tool v2 · Center Marker Mode",
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
# .block-container{padding-top:1.2rem!important;padding-bottom:2rem!important;}

# .hero{background:linear-gradient(135deg,#0f1923 0%,#1a2d42 50%,#0d2137 100%);
#   border-radius:16px;padding:26px 32px;margin-bottom:20px;
#   border:1px solid #1e3a52;position:relative;overflow:hidden;}
# .hero::before{content:'';position:absolute;top:-40px;right:-40px;
#   width:200px;height:200px;
#   background:radial-gradient(circle,rgba(255,215,0,.12) 0%,transparent 70%);border-radius:50%;}
# .hero-title{font-size:1.6rem;font-weight:700;color:#FFD700;margin:0 0 4px;}
# .hero-sub{font-size:.82rem;color:#8ba8c4;margin:0;}
# .hero-badges{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;}
# .hbadge{background:rgba(255,215,0,.12);color:#FFD700;
#   border:1px solid rgba(255,215,0,.3);padding:2px 10px;border-radius:20px;
#   font-size:.7rem;font-weight:600;font-family:'JetBrains Mono',monospace;}

# .sec-head{font-size:.68rem;font-weight:700;color:#FFD700;letter-spacing:1.5px;
#   text-transform:uppercase;margin:18px 0 8px;padding-bottom:5px;
#   border-bottom:1px solid #1e3a52;}

# .info-card{background:#0a1f14;border:1px solid #1e5e35;border-left:4px solid #27ae60;
#   border-radius:10px;padding:12px 16px;margin:5px 0;font-size:.84rem;color:#b0e8c4;}
# .warn-card{background:#1f1800;border:1px solid #5e4a00;border-left:4px solid #f39c12;
#   border-radius:10px;padding:12px 16px;margin:5px 0;font-size:.84rem;color:#f5d98a;}

# .mk-card{background:#0a1220;border:1px solid #1e3a52;border-radius:10px;
#   padding:12px 16px;margin:6px 0;}
# .mk-name{font-size:.9rem;font-weight:700;color:#FFD700;margin-bottom:4px;}
# .mk-coords{font-size:.76rem;color:#8ba8c4;font-family:'JetBrains Mono',monospace;}

# section[data-testid="stSidebar"]{background:#0a1220!important;border-right:1px solid #1e3a52;}
# .stDownloadButton>button{
#   background:linear-gradient(135deg,#FFD700,#ffa500)!important;
#   color:#0f1923!important;font-weight:700!important;border:none!important;
#   border-radius:10px!important;padding:12px 24px!important;width:100%!important;}
# .stButton>button[kind="primary"]{
#   background:linear-gradient(135deg,#FFD700,#ffa500)!important;
#   color:#0f1923!important;font-weight:700!important;border:none!important;
#   border-radius:10px!important;width:100%!important;padding:12px!important;
#   font-size:1rem!important;margin-top:6px!important;}
# </style>
# """, unsafe_allow_html=True)

# # ── Hero banner ────────────────────────────────────────────────────
# st.markdown("""
# <div class="hero">
#   <p class="hero-title">🚧 GIS BOQ Tool v2 — Center Marker Mode</p>
#   <p class="hero-sub">CAP PTBM Speed Breaker Strip Polygon Generator &nbsp;·&nbsp;
#      IIIT Nagpur &nbsp;·&nbsp; Dr. Neha Kasture &nbsp;·&nbsp; PWD / NHAI</p>
#   <div class="hero-badges">
#     <span class="hbadge">v2</span>
#     <span class="hbadge">Center Marker Only</span>
#     <span class="hbadge">Auto Road Width</span>
#     <span class="hbadge">3 Strips Default</span>
#     <span class="hbadge">KML + Excel Export</span>
#   </div>
# </div>
# """, unsafe_allow_html=True)

# # ── Compass SVG ────────────────────────────────────────────────────
# def compass_svg(road_heading: float, size: int = 150) -> str:
#     cx = size // 2
#     cy = size // 2
#     r  = size // 2 - 12
#     rh   = float(road_heading) % 360
#     perp = (rh + 90) % 360

#     def ep(angle_deg, length):
#         a = math.radians(float(angle_deg) - 90)
#         return cx + length * math.cos(a), cy + length * math.sin(a)

#     rx1 = ep(rh, r * 0.85)
#     rx2 = ep((rh + 180) % 360, r * 0.85)
#     px1 = ep(perp, r * 0.80)
#     px2 = ep((perp + 180) % 360, r * 0.80)

#     cardinals = ""
#     for angle, lbl in [(0,"N"),(90,"E"),(180,"S"),(270,"W")]:
#         lx = cx + (r+9)*math.cos(math.radians(angle-90))
#         ly = cy + (r+9)*math.sin(math.radians(angle-90))
#         cardinals += (
#             f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
#             f'dominant-baseline="central" font-size="9" fill="#8ba8c4">{lbl}</text>'
#         )

#     ticks = "".join(
#         f'<line x1="{cx+(r-5)*math.cos(math.radians(a-90)):.1f}" '
#         f'y1="{cy+(r-5)*math.sin(math.radians(a-90)):.1f}" '
#         f'x2="{cx+r*math.cos(math.radians(a-90)):.1f}" '
#         f'y2="{cy+r*math.sin(math.radians(a-90)):.1f}" '
#         f'stroke="#1e3a52" stroke-width="1.5"/>'
#         for a in range(0, 360, 10)
#     )

#     return f"""<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
#   <circle cx="{cx}" cy="{cy}" r="{r}" fill="#0a1220" stroke="#1e3a52" stroke-width="1.5"/>
#   {ticks}{cardinals}
#   <line x1="{rx1[0]:.1f}" y1="{rx1[1]:.1f}" x2="{rx2[0]:.1f}" y2="{rx2[1]:.1f}"
#         stroke="#FFD700" stroke-width="3.5" stroke-linecap="round"/>
#   <line x1="{px1[0]:.1f}" y1="{px1[1]:.1f}" x2="{px2[0]:.1f}" y2="{px2[1]:.1f}"
#         stroke="#e67e22" stroke-width="2" stroke-dasharray="5,3" stroke-linecap="round"/>
#   <circle cx="{cx}" cy="{cy}" r="4" fill="#FFD700"/>
#   <rect x="4" y="{size-26}" width="10" height="4" fill="#FFD700" rx="2"/>
#   <text x="17" y="{size-20}" font-size="8" fill="#8ba8c4">Road {rh:.0f}°</text>
#   <rect x="4" y="{size-14}" width="10" height="3" fill="none" stroke="#e67e22"
#         stroke-width="2" stroke-dasharray="4,2" rx="1"/>
#   <text x="17" y="{size-8}" font-size="8" fill="#8ba8c4">Strip {perp:.0f}°</text>
# </svg>"""


# # ── Session state ──────────────────────────────────────────────────
# for k, v in [
#     ("markers",   []),
#     ("all_polys", []),
#     ("headings",  {}),
#     ("kml_bytes", None),
#     ("xlsx_bytes",None),
#     ("generated", False),
#     ("per_marker_h", {}),
#     ("per_marker_w", {}),
#     ("per_marker_strips", {}),
# ]:
#     if k not in st.session_state:
#         st.session_state[k] = v


# # ════════════════════════════════════════════════════════════════════
# # SIDEBAR
# # ════════════════════════════════════════════════════════════════════
# with st.sidebar:

#     # ── KML Upload ─────────────────────────────────────────────────
#     st.markdown('<p class="sec-head">📂 KML Upload</p>', unsafe_allow_html=True)
#     st.markdown("""
#     <div class="info-card">
#       ℹ️ Upload KML with <b>center markers only</b>.<br>
#       One marker = center of road at that speed breaker.<br>
#       No green lines needed.
#     </div>
#     """, unsafe_allow_html=True)
#     uploaded = st.file_uploader(
#         "Upload KML", type=["kml"], label_visibility="collapsed"
#     )

#     # ── Road Width ─────────────────────────────────────────────────
#     st.markdown('<p class="sec-head">🛣️ Road Width</p>', unsafe_allow_html=True)
#     lane_key = st.selectbox(
#         "Lane Type (sets default width)",
#         list(LANE_PRESETS.keys()), index=1, key="lk"
#     )
#     lp = LANE_PRESETS[lane_key]

#     if lane_key == "Custom":
#         road_w = st.number_input("Road Width (m)", 2.0, 60.0, 7.0, 0.5, key="rw")
#         sep_w  = st.number_input("Separator (m)",  0.0, 10.0, 0.5, 0.1, key="sep")
#         nl_def = int(st.number_input("Lanes", 1, 8, 2, 1, key="nl"))
#     else:
#         road_w = float(lp["road_width_m"])
#         sep_w  = float(lp["separator_width_m"])
#         nl_def = int(lp["num_lanes"])
#         st.caption(
#             f"Width: **{road_w}m** | Lanes: **{nl_def}** | Sep: **{sep_w}m** | "
#             f"Lane width: **{(road_w-sep_w)/max(nl_def,1):.2f}m**"
#         )

#     # ── Heading ────────────────────────────────────────────────────
#     st.markdown('<p class="sec-head">🧭 Road Heading</p>', unsafe_allow_html=True)
#     heading_mode = st.radio(
#         "Heading source",
#         ["Auto (from marker neighbours)", "Manual (all markers)"],
#         key="hmode"
#     )
#     global_heading = None
#     if heading_mode == "Manual (all markers)":
#         global_heading = float(st.slider("Heading °", 0, 179, 90, key="gh"))
#         st.markdown(compass_svg(global_heading, 148), unsafe_allow_html=True)
#         st.caption(f"Road **{global_heading:.0f}°** → Strip direction **{(global_heading+90)%360:.0f}°**")
#     else:
#         st.caption("Heading auto-detected from neighbouring marker positions")

#     # ── Strip Config ───────────────────────────────────────────────
#     st.markdown('<p class="sec-head">🟨 Strip Configuration</p>', unsafe_allow_html=True)
#     n_strips  = int(st.number_input("Number of Strips", 1, 50, 3, 1, key="ns"))
#     sw_mm     = float(st.number_input("Strip Width (mm)", 5.0, 100.0, 15.0, 5.0, key="swmm"))
#     strip_gap = float(st.number_input("Gap Between Strips (m)", 0.0, 2.0, 0.50, 0.01, key="sg"))

#     lw_auto = (road_w - sep_w) / max(nl_def, 1)
#     total_strip_span = n_strips * (sw_mm/1000) + (n_strips-1) * strip_gap
#     st.caption(
#         f"{n_strips} strips × {sw_mm:.0f}mm | "
#         f"Total span along road: **{total_strip_span*100:.1f} cm**"
#     )

#     st.markdown("---")
#     gen_btn = st.button(
#         "🔄 Generate Polygons", type="primary",
#         disabled=uploaded is None, key="genb"
#     )
#     if not uploaded:
#         st.caption("⬆️ Upload a KML file to enable")


# # ════════════════════════════════════════════════════════════════════
# # PARSE KML & SHOW MARKERS
# # ════════════════════════════════════════════════════════════════════
# markers_raw = []
# n_markers   = 0
# kml_temp    = ""

# if uploaded:
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as tmp:
#         tmp.write(uploaded.getvalue())
#         kml_temp = tmp.name

#     try:
#         _markers = parse_kml(kml_temp)
#         n_markers = len(_markers)
#         markers_raw = _markers

#         # Metrics
#         mc1, mc2, mc3 = st.columns(3)
#         mc1.metric("📍 Markers Found", n_markers)
#         mc2.metric("🛣️ Road Width", f"{road_w} m")
#         mc3.metric("🟨 Strips / Marker", n_strips)

#         if n_markers == 0:
#             st.error("❌ No Point markers found in KML. Place red pins in Google Earth Pro and re-export.")
#         else:
#             st.markdown(
#                 f'<div class="info-card">✅ <b>{n_markers} center marker(s)</b> found. '
#                 f'Each marker = center of road. Polygon will span <b>{road_w}m</b> '
#                 f'(±{road_w/2:.1f}m each side).</div>',
#                 unsafe_allow_html=True
#             )

#             # Show markers
#             st.markdown('<p class="sec-head">📍 Markers Preview</p>', unsafe_allow_html=True)
#             for mk in _markers:
#                 st.markdown(
#                     f'<div class="mk-card">'
#                     f'<div class="mk-name">{mk.index+1}. {mk.name}</div>'
#                     f'<div class="mk-coords">Lat: {mk.lat:.6f} | Lon: {mk.lon:.6f}</div>'
#                     f'</div>',
#                     unsafe_allow_html=True
#                 )

#     except Exception as e:
#         st.error(f"❌ Parse error: {e}")
#         import traceback; st.code(traceback.format_exc())

# else:
#     # Welcome screen
#     col1, col2 = st.columns([2, 1])
#     with col1:
#         st.markdown("""
#         <div style="background:#0a1220;border:1px dashed #1e3a52;border-radius:16px;
#                     padding:40px;text-align:center;margin-top:20px">
#           <div style="font-size:3rem;margin-bottom:16px">🗺️</div>
#           <div style="font-size:1.1rem;font-weight:600;color:#e8eaf0;margin-bottom:8px">
#             Upload KML — Center Markers Only</div>
#           <div style="font-size:.84rem;color:#8ba8c4;max-width:380px;margin:0 auto">
#             Place <b>one red pin at the center of the road</b> for each speed breaker
#             in Google Earth Pro. Export as KML and upload here.
#           </div>
#         </div>""", unsafe_allow_html=True)
#     with col2:
#         st.markdown("**Simple 4-step workflow:**")
#         for s, t in [
#             ("1️⃣", "Open Google Earth Pro"),
#             ("2️⃣", "Place red pin at road CENTER for each speed breaker"),
#             ("3️⃣", "File → Save → Save Place As → KML"),
#             ("4️⃣", "Upload here, set road width & strips, click Generate"),
#         ]:
#             st.markdown(f"{s} {t}")


# # ════════════════════════════════════════════════════════════════════
# # PER-MARKER OVERRIDES
# # ════════════════════════════════════════════════════════════════════
# if n_markers > 0:
#     st.markdown('<p class="sec-head">🎯 Per-Marker Overrides (optional)</p>', unsafe_allow_html=True)

#     with st.expander("Customize individual markers", expanded=False):
#         st.caption("Override road width, heading, or strip count for specific markers.")

#         # Quick clear
#         if st.button("🗑️ Clear All Overrides", key="clr"):
#             st.session_state.per_marker_h = {}
#             st.session_state.per_marker_w = {}
#             st.session_state.per_marker_strips = {}
#             st.rerun()

#         for mk in markers_raw:
#             i = mk.index
#             with st.expander(f"Marker {i+1}: {mk.name}", expanded=False):
#                 oc1, oc2, oc3 = st.columns(3)

#                 # Width override
#                 with oc1:
#                     use_w = st.toggle("Custom width", key=f"uw{i}")
#                     if use_w:
#                         new_w = st.number_input(
#                             "Width (m)", 2.0, 60.0,
#                             st.session_state.per_marker_w.get(i, road_w),
#                             0.5, key=f"mw{i}"
#                         )
#                         st.session_state.per_marker_w[i] = new_w
#                     elif i in st.session_state.per_marker_w:
#                         del st.session_state.per_marker_w[i]

#                 # Heading override
#                 with oc2:
#                     use_h = st.toggle("Custom heading", key=f"uh{i}")
#                     if use_h:
#                         new_h = st.slider(
#                             "Heading °", 0, 179,
#                             int(st.session_state.per_marker_h.get(i, global_heading or 90)),
#                             1, key=f"mh{i}"
#                         )
#                         st.session_state.per_marker_h[i] = float(new_h)
#                     elif i in st.session_state.per_marker_h:
#                         del st.session_state.per_marker_h[i]

#                 # Strips override
#                 with oc3:
#                     use_s = st.toggle("Custom strips", key=f"us{i}")
#                     if use_s:
#                         new_s = int(st.number_input(
#                             "Strips", 1, 50,
#                             st.session_state.per_marker_strips.get(i, n_strips),
#                             1, key=f"ms{i}"
#                         ))
#                         st.session_state.per_marker_strips[i] = new_s
#                     elif i in st.session_state.per_marker_strips:
#                         del st.session_state.per_marker_strips[i]

#                 # Show compass for this marker
#                 disp_h = float(
#                     st.session_state.per_marker_h.get(i)
#                     or global_heading
#                     or 90.0
#                 )
#                 st.markdown(compass_svg(disp_h, 130), unsafe_allow_html=True)


# # ════════════════════════════════════════════════════════════════════
# # GENERATE
# # ════════════════════════════════════════════════════════════════════
# if gen_btn and uploaded and n_markers > 0:

#     spec = PolySpec(
#         road_width_m=road_w,
#         num_lanes=nl_def,
#         separator_width_m=sep_w,
#         num_strips=n_strips,
#         strip_width_mm=sw_mm,
#         strip_gap_m=strip_gap,
#         heading_override=global_heading,
#     )

#     # Apply per-marker overrides
#     for mk in markers_raw:
#         i = mk.index
#         ov = {}
#         if i in st.session_state.per_marker_w:
#             ov["road_width_m"] = st.session_state.per_marker_w[i]
#         if i in st.session_state.per_marker_h:
#             ov["heading_deg"] = st.session_state.per_marker_h[i]
#         if i in st.session_state.per_marker_strips:
#             ov["num_strips"] = st.session_state.per_marker_strips[i]
#         if ov:
#             spec.marker_overrides[i] = ov

#     prog = st.progress(0, "Parsing KML…")
#     try:
#         m_obj, polys, headings = run_pipeline(kml_temp, spec)
#         prog.progress(40, "Generating polygons…")

#         out_kml  = kml_temp.replace(".kml", "_p2_out.kml")
#         out_xlsx = kml_temp.replace(".kml", "_p2_out.xlsx")

#         export_kml(m_obj, polys, headings, out_kml)
#         prog.progress(70, "Exporting Excel…")
#         export_excel(m_obj, polys, headings, spec, out_xlsx)
#         prog.progress(90, "Preparing preview…")

#         with open(out_kml, "rb") as f:
#             st.session_state.kml_bytes = f.read()
#         with open(out_xlsx, "rb") as f:
#             st.session_state.xlsx_bytes = f.read()

#         st.session_state.markers   = m_obj
#         st.session_state.all_polys = polys
#         st.session_state.headings  = headings
#         st.session_state.generated = True

#         prog.progress(100, "Done ✅")
#         time.sleep(0.3)
#         prog.empty()
#         st.rerun()

#     except Exception as e:
#         prog.empty()
#         st.error(f"❌ Error: {e}")
#         import traceback; st.code(traceback.format_exc())


# # ════════════════════════════════════════════════════════════════════
# # RESULTS
# # ════════════════════════════════════════════════════════════════════
# if st.session_state.generated and st.session_state.all_polys:
#     m_obj  = st.session_state.markers
#     polys  = st.session_state.all_polys
#     heads  = st.session_state.headings

#     st.markdown('<p class="sec-head">✅ Results</p>', unsafe_allow_html=True)

#     r1, r2, r3, r4 = st.columns(4)
#     r1.metric("📍 Markers",       len(m_obj))
#     r2.metric("🟨 Total Strips",  len(polys))
#     r3.metric("🛣️ Road Width",   f"{road_w} m")
#     r4.metric("Strips/Marker",    len(polys) // max(len(m_obj), 1))

#     # ── Downloads ──────────────────────────────────────────────────
#     st.markdown('<p class="sec-head">📥 Downloads</p>', unsafe_allow_html=True)
#     dl1, dl2 = st.columns(2)
#     if st.session_state.kml_bytes:
#         dl1.download_button(
#             "📥 Download KML — Google Earth Pro",
#             data=st.session_state.kml_bytes,
#             file_name="speed_breakers_p2.kml",
#             mime="application/vnd.google-earth.kml+xml",
#             use_container_width=True,
#         )
#     if st.session_state.xlsx_bytes:
#         dl2.download_button(
#             "📊 Download Excel BOQ Report",
#             data=st.session_state.xlsx_bytes,
#             file_name="speed_breakers_p2_boq.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             use_container_width=True,
#         )

#     # ── Summary Table ──────────────────────────────────────────────
#     st.markdown('<p class="sec-head">📋 Marker Summary</p>', unsafe_allow_html=True)
#     by = {}
#     for p in polys:
#         by.setdefault(p.marker_idx, []).append(p)

#     rows = []
#     for mk in m_obj:
#         ps = by.get(mk.index, [])
#         p0 = ps[0] if ps else None
#         h, hsrc = heads.get(mk.index, (0.0, "default"))
#         rows.append({
#             "#": mk.index + 1,
#             "Marker Name": mk.name,
#             "Lat": round(mk.lat, 6),
#             "Lon": round(mk.lon, 6),
#             "Road Width (m)": round(p0.road_width_m, 2) if p0 else road_w,
#             "Lanes": p0.num_lanes if p0 else nl_def,
#             "Lane Width (m)": round(p0.lane_width_m, 2) if p0 else round(lw_auto, 2),
#             "Heading °": round(h, 1),
#             "Heading Src": hsrc,
#             "Strips": len(ps),
#             "Area/Strip m²": round(p0.strip_width_m * p0.strip_len_m, 4) if p0 else 0,
#             "Total Area m²": round(sum(p.strip_width_m * p.strip_len_m for p in ps), 4),
#         })
#     st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

#     # ── Folium Map ─────────────────────────────────────────────────
#     st.markdown('<p class="sec-head">🗺️ Satellite Preview</p>', unsafe_allow_html=True)
#     if m_obj:
#         clat = sum(m.lat for m in m_obj) / len(m_obj)
#         clon = sum(m.lon for m in m_obj) / len(m_obj)

#         fmap = folium.Map(
#             location=[clat, clon], zoom_start=19,
#             tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
#             attr="Google Satellite",
#         )

#         COLOURS = ["#FFD700","#FF8C00","#00FF88","#FF44AA","#44FFCC","#CC44FF"]

#         for p in polys:
#             folium.Polygon(
#                 locations=[[la, lo] for la, lo in p.coords],
#                 color=COLOURS[p.lane_idx % len(COLOURS)],
#                 fill=True,
#                 fill_color=COLOURS[p.lane_idx % len(COLOURS)],
#                 fill_opacity=0.85,
#                 weight=2,
#                 tooltip=(
#                     f"{p.marker_name} | Lane {p.lane_idx+1} | "
#                     f"Strip {p.strip_idx+1} | {p.road_heading:.1f}° | "
#                     f"Width {p.road_width_m:.2f}m"
#                 ),
#             ).add_to(fmap)

#         for mk in m_obj:
#             h, _ = heads.get(mk.index, (0.0, "default"))
#             folium.Marker(
#                 [mk.lat, mk.lon],
#                 popup=folium.Popup(
#                     f"<b>{mk.name}</b><br>"
#                     f"Lat: {mk.lat:.6f}<br>"
#                     f"Lon: {mk.lon:.6f}<br>"
#                     f"Heading: {h:.1f}°",
#                     max_width=200,
#                 ),
#                 icon=folium.Icon(color="red", icon="map-marker", prefix="fa"),
#             ).add_to(fmap)

#         st_folium(fmap, width="100%", height=520, returned_objects=[])

#     # ── Per-marker detail ───────────────────────────────────────────
#     st.markdown('<p class="sec-head">📐 Strip Details</p>', unsafe_allow_html=True)
#     for mk in m_obj:
#         ps = by.get(mk.index, [])
#         if not ps:
#             continue
#         p0 = ps[0]
#         h, hsrc = heads.get(mk.index, (0.0, "default"))
#         with st.expander(f"📍 {mk.name} — {len(ps)} strips | {p0.road_width_m:.1f}m wide"):
#             dc1, dc2 = st.columns([2, 1])
#             with dc1:
#                 st.markdown(f"""
# | Property | Value |
# |---|---|
# | Center Lat | `{mk.lat:.6f}` |
# | Center Lon | `{mk.lon:.6f}` |
# | Road Width | **{p0.road_width_m:.2f} m** |
# | Lanes | {p0.num_lanes} |
# | Lane Width | {p0.lane_width_m:.2f} m |
# | Heading | {h:.1f}° ({hsrc}) |
# | Total Strips | {len(ps)} |
# | Strip Width | {p0.strip_width_m*1000:.0f} mm |
# | Strip Length | {p0.strip_len_m:.2f} m |
# | Area / Strip | {p0.strip_width_m*p0.strip_len_m:.4f} m² |
# | Total Area | {sum(p.strip_width_m*p.strip_len_m for p in ps):.4f} m² |
# """)
#             with dc2:
#                 st.markdown(compass_svg(h, 148), unsafe_allow_html=True)













"""
ui2.py v3 — Speed Breaker GIS BOQ Tool (Center Marker Mode)
IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI
Run: streamlit run ui2.py

FIXES in v3:
  ● Fixed AttributeError: 'GenPoly' object has no attribute 'lane_width_m'
  ● Map zoom level 20 (max satellite detail — no need to open Google Earth)
  ● Marker name labels shown on map like in screenshot
  ● CAP PTBM label on polygons like in screenshot
  ● Strip gap default 0.5m (visible at satellite zoom)
"""
import streamlit as st
import tempfile, os, math, time
import pandas as pd
import folium
from streamlit_folium import st_folium

from p2 import (
    PolySpec, KMLMarker, GenPoly,
    parse_kml, run_pipeline, export_kml, export_excel,
    LANE_PRESETS, haversine, norm180,
)

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="GIS BOQ Tool v3 · CAP PTBM",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.2rem!important;padding-bottom:2rem!important;}

.hero{background:linear-gradient(135deg,#0f1923 0%,#1a2d42 50%,#0d2137 100%);
  border-radius:16px;padding:26px 32px;margin-bottom:20px;border:1px solid #1e3a52;}
.hero-title{font-size:1.6rem;font-weight:700;color:#FFD700;margin:0 0 4px;}
.hero-sub{font-size:.82rem;color:#8ba8c4;margin:0;}
.hero-badges{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;}
.hbadge{background:rgba(255,215,0,.12);color:#FFD700;border:1px solid rgba(255,215,0,.3);
  padding:2px 10px;border-radius:20px;font-size:.7rem;font-weight:600;}

.sec-head{font-size:.68rem;font-weight:700;color:#FFD700;letter-spacing:1.5px;
  text-transform:uppercase;margin:18px 0 8px;padding-bottom:5px;border-bottom:1px solid #1e3a52;}

.info-card{background:#0a1f14;border:1px solid #1e5e35;border-left:4px solid #27ae60;
  border-radius:10px;padding:12px 16px;margin:5px 0;font-size:.84rem;color:#b0e8c4;}
.warn-card{background:#1f1800;border:1px solid #5e4a00;border-left:4px solid #f39c12;
  border-radius:10px;padding:12px 16px;margin:5px 0;font-size:.84rem;color:#f5d98a;}
.mk-card{background:#0a1220;border:1px solid #1e3a52;border-radius:10px;padding:12px 16px;margin:6px 0;}
.mk-name{font-size:.9rem;font-weight:700;color:#FFD700;margin-bottom:4px;}
.mk-coords{font-size:.76rem;color:#8ba8c4;font-family:'JetBrains Mono',monospace;}

section[data-testid="stSidebar"]{background:#0a1220!important;border-right:1px solid #1e3a52;}
.stDownloadButton>button{background:linear-gradient(135deg,#FFD700,#ffa500)!important;
  color:#0f1923!important;font-weight:700!important;border:none!important;
  border-radius:10px!important;padding:12px 24px!important;width:100%!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#FFD700,#ffa500)!important;
  color:#0f1923!important;font-weight:700!important;border:none!important;
  border-radius:10px!important;width:100%!important;padding:12px!important;
  font-size:1rem!important;margin-top:6px!important;}
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <p class="hero-title">🚧 GIS BOQ Tool v3 — CAP PTBM Speed Breaker</p>
  <p class="hero-sub">Center Marker Mode &nbsp;·&nbsp; IIIT Nagpur &nbsp;·&nbsp;
     Dr. Neha Kasture &nbsp;·&nbsp; PWD / NHAI</p>
  <div class="hero-badges">
    <span class="hbadge">v3</span>
    <span class="hbadge">Center Marker Only</span>
    <span class="hbadge">Perpendicular Strips</span>
    <span class="hbadge">3 Strips Default</span>
    <span class="hbadge">Zoom-20 Preview</span>
    <span class="hbadge">KML + Excel Export</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Compass SVG ────────────────────────────────────────────────────
def compass_svg(road_heading:float, size:int=150)->str:
    cx=size//2; cy=size//2; r=size//2-12
    rh=float(road_heading)%360; perp=(rh+90)%360
    def ep(a,l):
        a2=math.radians(float(a)-90)
        return cx+l*math.cos(a2), cy+l*math.sin(a2)
    rx1=ep(rh,r*.85); rx2=ep((rh+180)%360,r*.85)
    px1=ep(perp,r*.80); px2=ep((perp+180)%360,r*.80)
    cardinals="".join(
        f'<text x="{cx+(r+9)*math.cos(math.radians(a-90)):.1f}" '
        f'y="{cy+(r+9)*math.sin(math.radians(a-90)):.1f}" '
        f'text-anchor="middle" dominant-baseline="central" font-size="9" fill="#8ba8c4">{l}</text>'
        for a,l in[(0,"N"),(90,"E"),(180,"S"),(270,"W")]
    )
    ticks="".join(
        f'<line x1="{cx+(r-5)*math.cos(math.radians(a-90)):.1f}" '
        f'y1="{cy+(r-5)*math.sin(math.radians(a-90)):.1f}" '
        f'x2="{cx+r*math.cos(math.radians(a-90)):.1f}" '
        f'y2="{cy+r*math.sin(math.radians(a-90)):.1f}" stroke="#1e3a52" stroke-width="1.5"/>'
        for a in range(0,360,10))
    return (f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0a1220" stroke="#1e3a52" stroke-width="1.5"/>'
            f'{ticks}{cardinals}'
            f'<line x1="{rx1[0]:.1f}" y1="{rx1[1]:.1f}" x2="{rx2[0]:.1f}" y2="{rx2[1]:.1f}" '
            f'stroke="#FFD700" stroke-width="3.5" stroke-linecap="round"/>'
            f'<line x1="{px1[0]:.1f}" y1="{px1[1]:.1f}" x2="{px2[0]:.1f}" y2="{px2[1]:.1f}" '
            f'stroke="#e67e22" stroke-width="2" stroke-dasharray="5,3" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="4" fill="#FFD700"/>'
            f'<rect x="4" y="{size-26}" width="10" height="4" fill="#FFD700" rx="2"/>'
            f'<text x="17" y="{size-20}" font-size="8" fill="#8ba8c4">Road {rh:.0f}°</text>'
            f'<rect x="4" y="{size-14}" width="10" height="3" fill="none" stroke="#e67e22" '
            f'stroke-width="2" stroke-dasharray="4,2" rx="1"/>'
            f'<text x="17" y="{size-8}" font-size="8" fill="#8ba8c4">Strip {perp:.0f}°</text>'
            f'</svg>')

# ── Session state ──────────────────────────────────────────────────
for k,v in [("markers",[]),("all_polys",[]),("headings",{}),
            ("kml_bytes",None),("xlsx_bytes",None),("generated",False),
            ("per_marker_h",{}),("per_marker_w",{}),("per_marker_strips",{})]:
    if k not in st.session_state: st.session_state[k]=v

# ════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<p class="sec-head">📂 KML Upload</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">ℹ️ Upload KML with <b>center markers only</b>.<br>'
                'One red pin = center of road at that speed breaker.</div>', unsafe_allow_html=True)
    uploaded=st.file_uploader("Upload KML",type=["kml"],label_visibility="collapsed")

    st.markdown('<p class="sec-head">🛣️ Road Width</p>', unsafe_allow_html=True)
    lane_key=st.selectbox("Lane Type",list(LANE_PRESETS.keys()),index=1,key="lk")
    lp=LANE_PRESETS[lane_key]
    if lane_key=="Custom":
        road_w=st.number_input("Road Width (m)",2.0,60.0,7.0,0.5,key="rw")
        sep_w =st.number_input("Separator (m)", 0.0,10.0,0.5,0.1,key="sep")
        nl_def=int(st.number_input("Lanes",1,8,2,1,key="nl"))
    else:
        road_w=float(lp["road_width_m"]); sep_w=float(lp["separator_width_m"]); nl_def=int(lp["num_lanes"])
        st.caption(f"Width: **{road_w}m** | Lanes: **{nl_def}** | Sep: **{sep_w}m** | "
                   f"Lane: **{(road_w-sep_w)/max(nl_def,1):.2f}m**")

    st.markdown('<p class="sec-head">🧭 Road Heading</p>', unsafe_allow_html=True)
    heading_mode=st.radio("Heading source",
        ["Auto (from marker neighbours)","Manual (all markers)"],key="hmode")
    global_heading=None
    if heading_mode=="Manual (all markers)":
        global_heading=float(st.slider("Heading °",0,179,90,key="gh"))
        st.markdown(compass_svg(global_heading,148),unsafe_allow_html=True)
        st.caption(f"Road **{global_heading:.0f}°** → Strip **{(global_heading+90)%360:.0f}°**")
    else:
        st.caption("Auto-detected from neighbouring marker positions")

    st.markdown('<p class="sec-head">🟨 Strip Configuration</p>', unsafe_allow_html=True)
    n_strips =int(st.number_input("Number of Strips",1,50,3,1,key="ns"))
    sw_mm    =float(st.number_input("Strip Width (mm)",5.0,100.0,15.0,5.0,key="swmm"))
    strip_gap=float(st.number_input("Gap Between Strips (m)",0.0,5.0,0.50,0.05,key="sg"))
    lw_auto=(road_w-sep_w)/max(nl_def,1)
    total_span=n_strips*(sw_mm/1000)+(n_strips-1)*strip_gap
    st.caption(f"{n_strips} strips × {sw_mm:.0f}mm | gap={strip_gap}m | span=**{total_span:.3f}m**")

    st.markdown("---")
    gen_btn=st.button("🔄 Generate Polygons",type="primary",disabled=uploaded is None,key="genb")
    if not uploaded: st.caption("⬆️ Upload a KML file to enable")

# ════════════════════════════════════════════════════════════════════
# PARSE KML
# ════════════════════════════════════════════════════════════════════
markers_raw=[]; n_markers=0; kml_temp=""

if uploaded:
    with tempfile.NamedTemporaryFile(delete=False,suffix=".kml") as tmp:
        tmp.write(uploaded.getvalue()); kml_temp=tmp.name
    try:
        _markers=parse_kml(kml_temp); n_markers=len(_markers); markers_raw=_markers
        mc1,mc2,mc3=st.columns(3)
        mc1.metric("📍 Markers Found",n_markers)
        mc2.metric("🛣️ Road Width",f"{road_w} m")
        mc3.metric("🟨 Strips/Marker",n_strips)
        if n_markers==0:
            st.error("❌ No Point markers found. Place red pins in Google Earth Pro and re-export.")
        else:
            st.markdown(f'<div class="info-card">✅ <b>{n_markers} center marker(s)</b> found. '
                        f'Each strip will span <b>{road_w}m</b> (±{road_w/2:.1f}m each side of marker).</div>',
                        unsafe_allow_html=True)
            st.markdown('<p class="sec-head">📍 Markers</p>', unsafe_allow_html=True)
            for mk in _markers:
                st.markdown(f'<div class="mk-card"><div class="mk-name">{mk.index+1}. {mk.name}</div>'
                            f'<div class="mk-coords">Lat: {mk.lat:.6f} | Lon: {mk.lon:.6f}</div></div>',
                            unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Parse error: {e}")
        import traceback; st.code(traceback.format_exc())
else:
    c1,c2=st.columns([2,1])
    with c1:
        st.markdown("""<div style="background:#0a1220;border:1px dashed #1e3a52;border-radius:16px;
            padding:40px;text-align:center;margin-top:20px">
          <div style="font-size:3rem;margin-bottom:16px">🗺️</div>
          <div style="font-size:1.1rem;font-weight:600;color:#e8eaf0;margin-bottom:8px">
            Upload KML — Center Markers Only</div>
          <div style="font-size:.84rem;color:#8ba8c4;max-width:380px;margin:0 auto">
            Place one red pin at the <b>center of the road</b> for each speed breaker.
            Export as KML and upload here.</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("**Workflow:**")
        for s,t in [("1️⃣","Open Google Earth Pro"),
                    ("2️⃣","Place red pin at road CENTER"),
                    ("3️⃣","File → Save Place As → KML"),
                    ("4️⃣","Upload, set width & strips, Generate")]:
            st.markdown(f"{s} {t}")

# ════════════════════════════════════════════════════════════════════
# PER-MARKER OVERRIDES
# ════════════════════════════════════════════════════════════════════
if n_markers>0:
    st.markdown('<p class="sec-head">🎯 Per-Marker Overrides (optional)</p>', unsafe_allow_html=True)
    with st.expander("Customize individual markers",expanded=False):
        if st.button("🗑️ Clear All Overrides",key="clr"):
            st.session_state.per_marker_h={}; st.session_state.per_marker_w={}
            st.session_state.per_marker_strips={}; st.rerun()
        for mk in markers_raw:
            i=mk.index
            with st.expander(f"Marker {i+1}: {mk.name}",expanded=False):
                oc1,oc2,oc3=st.columns(3)
                with oc1:
                    use_w=st.toggle("Custom width",key=f"uw{i}")
                    if use_w:
                        new_w=st.number_input("Width (m)",2.0,60.0,
                            st.session_state.per_marker_w.get(i,road_w),0.5,key=f"mw{i}")
                        st.session_state.per_marker_w[i]=new_w
                    elif i in st.session_state.per_marker_w: del st.session_state.per_marker_w[i]
                with oc2:
                    use_h=st.toggle("Custom heading",key=f"uh{i}")
                    if use_h:
                        new_h=st.slider("Heading °",0,179,
                            int(st.session_state.per_marker_h.get(i,global_heading or 90)),1,key=f"mh{i}")
                        st.session_state.per_marker_h[i]=float(new_h)
                    elif i in st.session_state.per_marker_h: del st.session_state.per_marker_h[i]
                with oc3:
                    use_s=st.toggle("Custom strips",key=f"us{i}")
                    if use_s:
                        new_s=int(st.number_input("Strips",1,50,
                            st.session_state.per_marker_strips.get(i,n_strips),1,key=f"ms{i}"))
                        st.session_state.per_marker_strips[i]=new_s
                    elif i in st.session_state.per_marker_strips: del st.session_state.per_marker_strips[i]
                disp_h=float(st.session_state.per_marker_h.get(i) or global_heading or 90.0)
                st.markdown(compass_svg(disp_h,130),unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
# GENERATE
# ════════════════════════════════════════════════════════════════════
if gen_btn and uploaded and n_markers>0:
    spec=PolySpec(road_width_m=road_w,num_lanes=nl_def,separator_width_m=sep_w,
                  num_strips=n_strips,strip_width_mm=sw_mm,strip_gap_m=strip_gap,
                  heading_override=global_heading)
    for mk in markers_raw:
        i=mk.index; ov={}
        if i in st.session_state.per_marker_w:    ov["road_width_m"]=st.session_state.per_marker_w[i]
        if i in st.session_state.per_marker_h:    ov["heading_deg"]=st.session_state.per_marker_h[i]
        if i in st.session_state.per_marker_strips: ov["num_strips"]=st.session_state.per_marker_strips[i]
        if ov: spec.marker_overrides[i]=ov
    prog=st.progress(0,"Parsing KML…")
    try:
        m_obj,polys,headings=run_pipeline(kml_temp,spec)
        prog.progress(40,"Generating polygons…")
        out_kml =kml_temp.replace(".kml","_p2_out.kml")
        out_xlsx=kml_temp.replace(".kml","_p2_out.xlsx")
        export_kml(m_obj,polys,headings,spec,out_kml)
        prog.progress(70,"Exporting Excel…")
        export_excel(m_obj,polys,headings,spec,out_xlsx)
        prog.progress(90,"Preparing preview…")
        with open(out_kml,"rb") as f: st.session_state.kml_bytes=f.read()
        with open(out_xlsx,"rb") as f: st.session_state.xlsx_bytes=f.read()
        st.session_state.markers=m_obj; st.session_state.all_polys=polys
        st.session_state.headings=headings; st.session_state.generated=True
        prog.progress(100,"Done ✅"); time.sleep(0.3); prog.empty(); st.rerun()
    except Exception as e:
        prog.empty(); st.error(f"❌ Error: {e}")
        import traceback; st.code(traceback.format_exc())

# ════════════════════════════════════════════════════════════════════
# RESULTS
# ════════════════════════════════════════════════════════════════════
if st.session_state.generated and st.session_state.all_polys:
    m_obj=st.session_state.markers; polys=st.session_state.all_polys; heads=st.session_state.headings

    st.markdown('<p class="sec-head">✅ Results</p>', unsafe_allow_html=True)
    r1,r2,r3,r4=st.columns(4)
    r1.metric("📍 Markers",len(m_obj))
    r2.metric("🟨 Total Strips",len(polys))
    r3.metric("🛣️ Road Width",f"{road_w} m")
    r4.metric("Strips/Marker",len(polys)//max(len(m_obj),1))

    # ── Downloads ──────────────────────────────────────────────────
    st.markdown('<p class="sec-head">📥 Downloads</p>', unsafe_allow_html=True)
    dl1,dl2=st.columns(2)
    if st.session_state.kml_bytes:
        dl1.download_button("📥 Download KML — Google Earth Pro",
            data=st.session_state.kml_bytes,file_name="speed_breakers_v3.kml",
            mime="application/vnd.google-earth.kml+xml",use_container_width=True)
    if st.session_state.xlsx_bytes:
        dl2.download_button("📊 Download Excel BOQ Report",
            data=st.session_state.xlsx_bytes,file_name="speed_breakers_v3_boq.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)

    # ── Summary Table ──────────────────────────────────────────────
    st.markdown('<p class="sec-head">📋 Marker Summary</p>', unsafe_allow_html=True)
    by={}
    for p in polys: by.setdefault(p.marker_idx,[]).append(p)
    rows=[]
    for mk in m_obj:
        ps=by.get(mk.index,[]); p0=ps[0] if ps else None
        h,hsrc=heads.get(mk.index,(0.0,"default"))
        rows.append({
            "#":mk.index+1,"Marker Name":mk.name,
            "Lat":round(mk.lat,6),"Lon":round(mk.lon,6),
            "Road Width (m)":round(p0.road_width_m,2) if p0 else road_w,
            "Lanes":p0.num_lanes if p0 else nl_def,
            "Lane Width (m)":round(p0.lane_width_m,2) if p0 else round(lw_auto,2),
            "Heading °":round(h,1),"Heading Src":hsrc,
            "Strips":len(ps),
            "Area/Strip m²":round(p0.strip_width_m*p0.road_width_m,4) if p0 else 0,
            "Total Area m²":round(sum(p.strip_width_m*p.road_width_m for p in ps),4),
        })
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    # ── HIGH ZOOM Satellite Map ────────────────────────────────────
    st.markdown('<p class="sec-head">🗺️ Satellite Preview (Zoom 20 — No Google Earth needed)</p>',
                unsafe_allow_html=True)
    st.markdown('<div class="info-card">🔍 Map is at <b>maximum satellite zoom (level 20)</b>. '
                'You can verify strip placement directly here without opening Google Earth.</div>',
                unsafe_allow_html=True)

    if m_obj:
        clat=sum(m.lat for m in m_obj)/len(m_obj)
        clon=sum(m.lon for m in m_obj)/len(m_obj)

        # Zoom 20 = maximum Google satellite detail
        fmap=folium.Map(
            location=[clat,clon],
            zoom_start=20,
            max_zoom=21,
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google Satellite",
        )

        # Strip colours matching screenshot (yellow/gold like CAP PTBM)
        STRIP_COLOURS=["#FFD700","#FFB300","#FF8C00","#FFA500","#FFCC00","#FFE066"]

        # Draw strip polygons
        for p in polys:
            col=STRIP_COLOURS[p.strip_idx%len(STRIP_COLOURS)]
            label=f"CAP PTBM {p.strip_width_m*1000:.0f}MM X {len(by.get(p.marker_idx,[]))}"
            folium.Polygon(
                locations=[[la,lo] for la,lo in p.coords],
                color="#8B6914",        # dark border
                weight=1,
                fill=True,
                fill_color=col,
                fill_opacity=0.85,
                tooltip=f"{p.marker_name} | {label} | Strip {p.strip_idx+1} | {p.road_heading:.1f}°",
            ).add_to(fmap)

        # Marker pins with name labels (like screenshot)
        for mk in m_obj:
            ps=by.get(mk.index,[])
            h,hsrc=heads.get(mk.index,(0.0,"default"))
            n_s=len(ps)
            sw_mm_val=ps[0].strip_width_m*1000 if ps else spec.strip_width_mm if 'spec' in dir() else sw_mm
            rw_val=ps[0].road_width_m if ps else road_w

            # DivIcon with name label visible on map like screenshot
            folium.Marker(
                [mk.lat,mk.lon],
                popup=folium.Popup(
                    f"<b>{mk.name}</b><br>"
                    f"CAP PTBM {sw_mm_val:.0f}MM X {n_s}<br>"
                    f"Road: {rw_val:.1f}m | {nl_def} Lane<br>"
                    f"Heading: {h:.1f}° [{hsrc}]<br>"
                    f"Lat: {mk.lat:.6f}<br>Lon: {mk.lon:.6f}",
                    max_width=220,
                ),
                # Red pushpin icon
                icon=folium.Icon(color="red",icon="map-marker",prefix="fa"),
                # Name label shown on map
                tooltip=f"📍 {mk.name}",
            ).add_to(fmap)

            # Add visible name label on map (like screenshot)
            folium.Marker(
                [mk.lat,mk.lon],
                icon=folium.DivIcon(
                    html=f'<div style="font-size:11px;font-weight:700;color:#FFD700;'
                         f'background:rgba(0,0,0,0.6);padding:2px 5px;border-radius:3px;'
                         f'white-space:nowrap;margin-top:-30px;margin-left:15px;">'
                         f'{mk.name}</div>',
                    icon_size=(150,30),
                    icon_anchor=(0,0),
                ),
            ).add_to(fmap)

        st_folium(fmap,width="100%",height=600,returned_objects=[])

    # ── Per-marker detail ───────────────────────────────────────────
    st.markdown('<p class="sec-head">📐 Strip Details per Marker</p>', unsafe_allow_html=True)
    for mk in m_obj:
        ps=by.get(mk.index,[]); p0=ps[0] if ps else None
        if not p0: continue
        h,hsrc=heads.get(mk.index,(0.0,"default"))
        with st.expander(f"📍 {mk.name} — {len(ps)} strips | {p0.road_width_m:.1f}m wide"):
            dc1,dc2=st.columns([2,1])
            with dc1:
                sw_mm_val=p0.strip_width_m*1000
                st.markdown(f"""
| Property | Value |
|---|---|
| Marker Name | **{mk.name}** |
| Center Lat | `{mk.lat:.6f}` |
| Center Lon | `{mk.lon:.6f}` |
| Road Width | **{p0.road_width_m:.2f} m** |
| Lanes | {p0.num_lanes} |
| Lane Width | {p0.lane_width_m:.2f} m |
| Heading | {h:.1f}° ({hsrc}) |
| Total Strips | {len(ps)} |
| Strip Thick | {sw_mm_val:.0f} mm (along road) |
| Strip Length | {p0.road_width_m:.2f} m (across road) |
| Gap between strips | {p0.strip_gap_m:.2f} m |
| Area / Strip | {p0.strip_width_m*p0.road_width_m:.4f} m² |
| Total Area | {sum(p.strip_width_m*p.road_width_m for p in ps):.4f} m² |
| KML Label | CAP PTBM {sw_mm_val:.0f}MM X {len(ps)} |
""")
            with dc2:
                st.markdown(compass_svg(h,148),unsafe_allow_html=True)
                st.caption(f"Road **{h:.0f}°** | Strip **{(h+90)%360:.0f}°**")