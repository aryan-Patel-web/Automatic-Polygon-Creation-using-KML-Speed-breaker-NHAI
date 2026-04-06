"""
ui1.py v10 — Speed Breaker GIS BOQ Tool
IIIT Nagpur | Dr. Neha Kasture | PWD / NHAI
Run: streamlit run ui1.py
"""
import streamlit as st
import tempfile, os, math, time
import pandas as pd
import folium
from streamlit_folium import st_folium

from p1 import (
    PolygonSpec, MarkerOverride, GreenLine, KMLMarker, GenPoly,
    run_pipeline, export_kml, export_excel,
    LANE_PRESETS, MARKER_POSITION_LABELS,
    haversine, norm180, GL_MODE_ALONG, GL_MODE_ACROSS,
)

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="GIS BOQ Tool · NHAI Speed Breaker",
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
  border-radius:16px;padding:26px 32px;margin-bottom:20px;
  border:1px solid #1e3a52;position:relative;overflow:hidden;}
.hero::before{content:'';position:absolute;top:-40px;right:-40px;
  width:200px;height:200px;
  background:radial-gradient(circle,rgba(255,215,0,.12) 0%,transparent 70%);border-radius:50%;}
.hero-title{font-size:1.6rem;font-weight:700;color:#FFD700;margin:0 0 4px;}
.hero-sub{font-size:.82rem;color:#8ba8c4;margin:0;}
.hero-badges{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;}
.hbadge{background:rgba(255,215,0,.12);color:#FFD700;
  border:1px solid rgba(255,215,0,.3);padding:2px 10px;border-radius:20px;
  font-size:.7rem;font-weight:600;font-family:'JetBrains Mono',monospace;}

.sec-head{font-size:.68rem;font-weight:700;color:#FFD700;letter-spacing:1.5px;
  text-transform:uppercase;margin:18px 0 8px;padding-bottom:5px;
  border-bottom:1px solid #1e3a52;}

/* GL mode card */
.glmode-card{border-radius:10px;padding:12px 16px;margin:4px 0;cursor:pointer;}
.glmode-along{background:#0a1a2e;border:2px solid #3498db;}
.glmode-across{background:#0a1f14;border:2px solid #27ae60;}
.glmode-title{font-size:.88rem;font-weight:700;margin-bottom:2px;}
.glmode-along .glmode-title{color:#3498db;}
.glmode-across .glmode-title{color:#27ae60;}
.glmode-desc{font-size:.76rem;color:#8ba8c4;}

.gl-card{background:#0a1f14;border:1px solid #1e5e35;border-left:4px solid #27ae60;
  border-radius:10px;padding:12px 16px;margin:5px 0;}
.gl-card-warn{background:#1f1800;border:1px solid #5e4a00;border-left:4px solid #f39c12;
  border-radius:10px;padding:12px 16px;margin:5px 0;}
.gl-none{background:#1f0a0a;border:1px solid #5e1e1e;border-left:4px solid #e74c3c;
  border-radius:10px;padding:14px 18px;margin:5px 0;font-size:.86rem;color:#e8a0a0;}
.gl-width{font-size:1.25rem;font-weight:700;color:#FFD700;
  font-family:'JetBrains Mono',monospace;}
.gl-name{font-size:.78rem;color:#8ba8c4;margin-bottom:2px;}

.badge{font-size:.68rem;font-weight:700;padding:2px 8px;border-radius:12px;
  font-family:'JetBrains Mono',monospace;}
.badge-gl{background:#0a2e1a;color:#27ae60;border:1px solid #27ae60;}
.badge-h{background:#2e1a00;color:#f39c12;border:1px solid #f39c12;}
.badge-l{background:#001a2e;color:#3498db;border:1px solid #3498db;}

section[data-testid="stSidebar"]{background:#0a1220!important;border-right:1px solid #1e3a52;}
.stDownloadButton>button{
  background:linear-gradient(135deg,#FFD700,#ffa500)!important;
  color:#0f1923!important;font-weight:700!important;border:none!important;
  border-radius:10px!important;padding:12px 24px!important;width:100%!important;
  font-family:'Space Grotesk',sans-serif!important;}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#FFD700,#ffa500)!important;
  color:#0f1923!important;font-weight:700!important;border:none!important;
  border-radius:10px!important;width:100%!important;padding:12px!important;
  font-size:1rem!important;margin-top:6px!important;}
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <p class="hero-title">🚧 GIS BOQ Automation Tool</p>
  <p class="hero-sub">CAP PTBM Speed Breaker Strip Polygon Generator &nbsp;·&nbsp;
     IIIT Nagpur &nbsp;·&nbsp; Dr. Neha Kasture &nbsp;·&nbsp; PWD / NHAI</p>
  <div class="hero-badges">
    <span class="hbadge">v10</span>
    <span class="hbadge">GL Along/Across Fix</span>
    <span class="hbadge">Multi-Marker GL Match</span>
    <span class="hbadge">Rotated Bounding Box</span>
    <span class="hbadge">Per-Marker Config</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Compass SVG (FIXED — separate x/y variables, no subscript) ────
def compass_svg(road_heading: float, size: int = 160) -> str:
    cx = size // 2
    cy = size // 2
    r  = size // 2 - 12
    rh   = float(road_heading) % 360
    perp = (rh + 90) % 360

    def ep(angle_deg: float, length: float):
        a = math.radians(float(angle_deg) - 90)
        return cx + length * math.cos(a), cy + length * math.sin(a)

    rx1_x, rx1_y = ep(rh, r * 0.85)
    rx2_x, rx2_y = ep((rh + 180) % 360, r * 0.85)
    px1_x, px1_y = ep(perp, r * 0.82)
    px2_x, px2_y = ep((perp + 180) % 360, r * 0.82)

    cardinals = ""
    for angle, lbl in [(0,"N"),(90,"E"),(180,"S"),(270,"W")]:
        lx = cx + (r+9)*math.cos(math.radians(angle-90))
        ly = cy + (r+9)*math.sin(math.radians(angle-90))
        cardinals += (f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
                      f'dominant-baseline="central" font-size="9" fill="#8ba8c4" '
                      f'font-family="Space Grotesk,sans-serif">{lbl}</text>')

    ticks = "".join(
        f'<line x1="{cx+(r-5)*math.cos(math.radians(a-90)):.1f}" '
        f'y1="{cy+(r-5)*math.sin(math.radians(a-90)):.1f}" '
        f'x2="{cx+r*math.cos(math.radians(a-90)):.1f}" '
        f'y2="{cy+r*math.sin(math.radians(a-90)):.1f}" '
        f'stroke="#1e3a52" stroke-width="1.5"/>'
        for a in range(0, 360, 10)
    )
    return f"""<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="#0a1220" stroke="#1e3a52" stroke-width="1.5"/>
  {ticks}{cardinals}
  <line x1="{rx1_x:.1f}" y1="{rx1_y:.1f}" x2="{rx2_x:.1f}" y2="{rx2_y:.1f}"
        stroke="#FFD700" stroke-width="3.5" stroke-linecap="round"/>
  <line x1="{px1_x:.1f}" y1="{px1_y:.1f}" x2="{px2_x:.1f}" y2="{px2_y:.1f}"
        stroke="#e67e22" stroke-width="2.5" stroke-dasharray="6,4" stroke-linecap="round"/>
  <circle cx="{cx}" cy="{cy}" r="4" fill="#FFD700"/>
  <rect x="4" y="{size-26}" width="12" height="4" fill="#FFD700" rx="2"/>
  <text x="19" y="{size-20}" font-size="8" fill="#8ba8c4"
        font-family="JetBrains Mono,monospace">Road {rh:.0f}°</text>
  <rect x="4" y="{size-14}" width="12" height="3" fill="none" stroke="#e67e22"
        stroke-width="2" stroke-dasharray="4,2" rx="1"/>
  <text x="19" y="{size-8}" font-size="8" fill="#8ba8c4"
        font-family="JetBrains Mono,monospace">Strip {perp:.0f}°</text>
</svg>"""


# ── Session state ──────────────────────────────────────────────────
for k, v in [("markers",[]),("greenlines",[]),("gl_matches",{}),
              ("all_polygons",[]),("kml_bytes",None),("excel_bytes",None),
              ("per_marker_h",{}),("per_marker_lanes",{}),("generated",False)]:
    if k not in st.session_state: st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<p class="sec-head">📂 KML Upload</p>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload KML from Google Earth Pro", type=["kml"],
        label_visibility="collapsed",
    )

    # ── GL Mode (the key new control) ──────────────────────────
    st.markdown('<p class="sec-head">📏 Green Line Direction</p>', unsafe_allow_html=True)
    st.markdown("""
<div class="glmode-card glmode-along">
  <div class="glmode-title">↔ Along Road</div>
  <div class="glmode-desc">Line drawn <b>parallel to road</b><br>
  → Bearing = road heading<br>
  → Length = segment (not width)<br>
  → Road width from manual input</div>
</div>
<div class="glmode-card glmode-across" style="margin-top:6px">
  <div class="glmode-title">↕ Across Road</div>
  <div class="glmode-desc">Line drawn <b>perpendicular to road</b><br>
  → Length = road width (auto-fill)<br>
  → Bearing + 90° = road heading</div>
</div>
""", unsafe_allow_html=True)

    gl_mode_choice = st.radio(
        "How did you draw the green lines?",
        options=["Along road (parallel)", "Across road (perpendicular)"],
        index=0, key="glmode",
    )
    gl_mode = GL_MODE_ALONG if "Along" in gl_mode_choice else GL_MODE_ACROSS

    if gl_mode == GL_MODE_ALONG:
        st.info("📐 Road width will use manual input below", icon="ℹ️")
    else:
        st.success("📏 Road width auto-filled from line length", icon="✅")

    with st.expander("How to draw lines in Google Earth Pro"):
        if gl_mode == GL_MODE_ALONG:
            st.markdown("""
**Along road (current mode):**
1. Add Path → draw line **along the road** from one end to another
2. This gives road direction (heading) automatically
3. Set road width manually in the Road Config section below
            """)
        else:
            st.markdown("""
**Across road (current mode):**
1. Add Path → draw line **across the full road width** at each marker
2. Line length = road width (auto-filled in Excel)
3. Road heading = line bearing + 90°
            """)

    st.markdown('<p class="sec-head">🧭 Road Heading</p>', unsafe_allow_html=True)
    use_global_h = st.toggle("Set manually (override GL)", False, key="ugh")
    global_heading = 90.0
    if use_global_h:
        global_heading = float(st.slider("Heading °", 0, 179, 90, key="ghs"))
        st.markdown(compass_svg(global_heading, 148), unsafe_allow_html=True)
        st.caption(f"Road **{global_heading:.0f}°** → Strip **{(global_heading+90)%360:.0f}°**")
    else:
        st.caption("Auto from green lines / neighbouring markers")

    st.markdown('<p class="sec-head">📍 Marker Position</p>', unsafe_allow_html=True)
    default_pos = st.radio(
        "Where is the pin placed on the road?",
        options=list(MARKER_POSITION_LABELS.keys()),
        format_func=lambda k: MARKER_POSITION_LABELS[k],
        index=0, key="dpos",
    )
    custom_offset = 0.0
    if default_pos == "custom":
        custom_offset = st.number_input("Offset from road centre (m)", -20.0,20.0,0.0,0.1,key="co")

    st.markdown('<p class="sec-head">🛣️ Road Configuration</p>', unsafe_allow_html=True)
    lp_key = st.selectbox("Lane Type", list(LANE_PRESETS.keys()), index=1, key="lpk")
    lp     = LANE_PRESETS[lp_key]
    road_w = st.number_input("Total Road Width (m)", 2.0, 60.0, float(lp["road_width_m"]), 0.5, key="rw")
    sep_w  = st.number_input("Separator Width (m)", 0.0, 10.0, float(lp["separator_width_m"]), 0.1, key="sep")
    nl_def = int(lp["num_lanes"])
    lw_auto = (road_w - sep_w) / max(nl_def, 1)
    st.caption(f"↳ Each lane = **{lw_auto:.2f} m**")

    use_lg = st.toggle("Override lane group gap", False, key="ulg")
    lane_gap = -1.0
    if use_lg:
        ag = sep_w + max(0.3, lw_auto*0.10)
        lane_gap = float(st.number_input("Lane group gap (m)", 0.1, 10.0, round(ag,2), 0.1, key="lg"))

    st.markdown('<p class="sec-head">🟨 Strip Spec</p>', unsafe_allow_html=True)
    sw_mm    = st.number_input("Strip Width (mm)", 5.0, 100.0, 15.0, 5.0, key="swmm")
    n_strips = int(st.number_input("Total Strips (all lanes)", 1, 50, 6, 1, key="ns"))
    s_gap    = st.number_input("Gap Between Strips (m)", 0.0, 1.0, 0.10, 0.01, key="sg")
    st.caption(f"{n_strips} ÷ {nl_def} = **{n_strips//nl_def}/lane** | "
               f"CAP PTBM {sw_mm:.0f}MM X {n_strips}")

    use_sl = st.toggle("Override strip length", False, key="usl")
    strip_len = None
    if use_sl:
        strip_len = float(st.number_input("Strip Length (m)", 0.5, 30.0,
                                           round(lw_auto,2), 0.1, key="slen"))
        if strip_len > lw_auto: st.warning(f"⚠️ {strip_len:.2f}m > lane {lw_auto:.2f}m")

    st.markdown("---")
    gen_btn = st.button("🔄 Generate Polygons", type="primary",
                        disabled=uploaded is None, key="genb")
    if not uploaded: st.caption("⬆️ Upload KML to enable")


# ══════════════════════════════════════════════════════════════════
# PARSE KML
# ══════════════════════════════════════════════════════════════════
markers_raw=[]; gl_raw=[]; kml_temp=""; n_markers=0

if uploaded:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".kml") as tmp:
        tmp.write(uploaded.getvalue()); kml_temp=tmp.name
    try:
        from p1 import parse_kml as _pk, match_gl as _mg
        _m, _g = _pk(kml_temp)
        _glm   = _mg(_m, _g, max_dist_m=50.0, gl_mode=gl_mode)
        markers_raw=[{"name":m.name,"lat":m.lat,"lon":m.lon,"index":m.index} for m in _m]
        gl_raw=_g; n_markers=len(markers_raw)

        # Metrics
        mc1,mc2,mc3,mc4 = st.columns(4)
        mc1.metric("📍 Markers",      n_markers)
        mc2.metric("📏 Green Lines",  len(_g),
                   delta="headings auto-filled ✓" if _g else None)
        mc3.metric("🟢 GL Matched",   len(_glm))
        mc4.metric("Mode",
                   "Along →" if gl_mode==GL_MODE_ALONG else "Across ↕",
                   delta="heading only" if gl_mode==GL_MODE_ALONG else "width+heading")

        # GL cards
        if _g:
            st.markdown('<p class="sec-head">📏 Green Line Analysis</p>',
                        unsafe_allow_html=True)
            # Show what each GL contributes
            cols_gl = st.columns(min(len(_g), 3))
            for i, gl in enumerate(_g):
                matched_names=[m.name for m in _m
                               if haversine(gl.midpoint_lat,gl.midpoint_lon,
                                            m.lat,m.lon)<50]
                card_cls = "gl-card" if matched_names else "gl-card-warn"
                mode_lbl = "↔ Along → heading only" if gl_mode==GL_MODE_ALONG else "↕ Across → width + heading"
                with cols_gl[i % len(cols_gl)]:
                    if gl_mode == GL_MODE_ACROSS:
                        width_str = f'<div class="gl-width">{gl.length_m:.2f} m</div>'
                    else:
                        width_str = f'<div style="font-size:.8rem;color:#8ba8c4;">Length: {gl.length_m:.2f}m (segment)</div>'
                    st.markdown(
                        f'<div class="{card_cls}">'
                        f'<div class="gl-name">📏 {gl.name}</div>'
                        f'{width_str}'
                        f'<div style="font-size:.74rem;color:#8ba8c4;margin-top:4px">'
                        f'Road heading: <b>{gl.road_heading:.1f}°</b><br>'
                        f'{mode_lbl}<br>'
                        f'{"✅ → " + ", ".join(matched_names) if matched_names else "⚠️ No marker within 50m"}'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
        else:
            if n_markers > 0:
                st.markdown(
                    '<div class="gl-none"><strong>No green lines found.</strong> '
                    'Road heading will be auto-detected from marker neighbours. '
                    'Draw lines in Google Earth Pro to improve accuracy.</div>',
                    unsafe_allow_html=True,
                )

        if n_markers == 0:
            st.error("❌ No Point markers found. Add red pins in Google Earth Pro and re-upload.")

    except Exception as e:
        st.error(f"❌ Parse error: {e}")
        import traceback; st.code(traceback.format_exc())
        n_markers=0

else:
    # Welcome
    wc1, wc2 = st.columns([2,1])
    with wc1:
        st.markdown("""
        <div style="background:#0a1220;border:1px dashed #1e3a52;border-radius:16px;
                    padding:40px;text-align:center;margin-top:20px">
          <div style="font-size:3rem;margin-bottom:16px">🗺️</div>
          <div style="font-size:1.1rem;font-weight:600;color:#e8eaf0;margin-bottom:8px">
            Upload a KML File to Begin</div>
          <div style="font-size:.84rem;color:#8ba8c4;max-width:380px;margin:0 auto">
            Export your Google Earth Pro markers as KML, upload here,
            configure road settings, and generate yellow speed breaker polygons.
          </div>
        </div>""", unsafe_allow_html=True)
    with wc2:
        st.markdown("**Workflow**")
        for s,t in [("1️⃣","Place red pins at each speed breaker location"),
                    ("2️⃣","Draw green lines along OR across the road at each marker"),
                    ("3️⃣","File → Save → Save Place As → KML"),
                    ("4️⃣","Upload KML, set GL mode (Along/Across), configure, generate"),
                    ("5️⃣","Download annotated KML + Excel BOQ report")]:
            st.markdown(f"{s} {t}")


# ══════════════════════════════════════════════════════════════════
# PER-MARKER CONFIG
# ══════════════════════════════════════════════════════════════════
if n_markers > 0:
    st.markdown('<p class="sec-head">🎯 Per-Marker Configuration</p>',
                unsafe_allow_html=True)

    with st.expander("⚡ Quick Range Assignment"):
        qc1,qc2,qc3,qc4 = st.columns(4)
        r_from = int(qc1.number_input("From #",1,n_markers,1,1,key="qrf"))
        r_to   = int(qc2.number_input("To #",r_from,n_markers,min(r_from+5,n_markers),1,key="qrt"))
        r_hdg  = float(qc3.number_input("Heading °",0,179,90,1,key="qrh"))
        if qc4.button("✅ Apply",key="qra"):
            for i in range(r_from-1,r_to):
                st.session_state.per_marker_h[i]=r_hdg
            st.success(f"Markers {r_from}–{r_to} → {r_hdg}°")
        if st.button("🗑️ Clear All Overrides",key="clr"):
            st.session_state.per_marker_h={}; st.session_state.per_marker_lanes={}
            st.rerun()

    for mk in markers_raw:
        i=mk["index"]; name=mk["name"]
        h_ov=st.session_state.per_marker_h.get(i)
        l_ov=st.session_state.per_marker_lanes.get(i)
        gl_hit=any(haversine(gl.midpoint_lat,gl.midpoint_lon,mk["lat"],mk["lon"])<50
                   for gl in gl_raw)

        badges=""
        if gl_hit: badges+=' <span class="badge badge-gl">📏GL</span>'
        if h_ov is not None: badges+=' <span class="badge badge-h">H</span>'
        if l_ov is not None: badges+=' <span class="badge badge-l">L</span>'

        with st.expander(f"{i+1}. {name}", expanded=False):
            if badges: st.markdown(badges, unsafe_allow_html=True)

            if gl_hit:
                mgl=next((gl for gl in gl_raw
                           if haversine(gl.midpoint_lat,gl.midpoint_lon,
                                        mk["lat"],mk["lon"])<50),None)
                if mgl:
                    if gl_mode==GL_MODE_ALONG:
                        st.info(f"📏 GL matched → Road heading **{mgl.road_heading:.1f}°** "
                                f"(line along road, bearing={mgl.bearing_deg:.1f}°). "
                                f"Width = manual ({road_w:.1f}m).")
                    else:
                        st.success(f"📏 GL matched → Road width **{mgl.length_m:.2f}m** | "
                                   f"Road heading **{mgl.road_heading:.1f}°** (bearing+90°)")

            ec1,ec2=st.columns([3,2])
            with ec1:
                use_h=st.toggle("Manual heading",value=h_ov is not None,key=f"uh{i}")
                if use_h:
                    cur_h=float(h_ov if h_ov is not None else (global_heading if use_global_h else 90))
                    new_h=float(st.slider(f"Heading #{i+1}",0,179,int(cur_h),1,key=f"hs{i}"))
                    if st.button("📌 Set",key=f"seth{i}"):
                        st.session_state.per_marker_h[i]=new_h; st.rerun()
                    if h_ov is not None:
                        st.caption(f"Active: **{h_ov:.0f}°**")
                        if st.button("✖ Remove",key=f"rmh{i}"):
                            del st.session_state.per_marker_h[i]; st.rerun()
                elif h_ov is not None:
                    del st.session_state.per_marker_h[i]

                use_l=st.toggle("Manual lane type",value=l_ov is not None,key=f"ul{i}")
                if use_l:
                    cur_l=l_ov if l_ov in LANE_PRESETS else lp_key
                    new_l=st.selectbox(f"Lane type #{i+1}",list(LANE_PRESETS.keys()),
                                       index=list(LANE_PRESETS.keys()).index(cur_l),key=f"lps{i}")
                    if st.button("📌 Set",key=f"setl{i}"):
                        st.session_state.per_marker_lanes[i]=new_l; st.rerun()
                    if l_ov is not None:
                        st.caption(f"Active: **{l_ov}**")
                        if st.button("✖ Remove",key=f"rml{i}"):
                            del st.session_state.per_marker_lanes[i]; st.rerun()
                elif l_ov is not None:
                    del st.session_state.per_marker_lanes[i]

            with ec2:
                disp_h=float(st.session_state.per_marker_h.get(i)
                              or (global_heading if use_global_h else 90.0))
                st.markdown(compass_svg(disp_h,148),unsafe_allow_html=True)
                st.caption(f"Road **{disp_h:.0f}°** | Strip **{(disp_h+90)%360:.0f}°**")


# ══════════════════════════════════════════════════════════════════
# GENERATE
# ══════════════════════════════════════════════════════════════════
if gen_btn and uploaded and n_markers>0:
    spec=PolygonSpec(
        strip_width_mm=float(sw_mm), num_strips=n_strips,
        strip_gap_m=float(s_gap), num_lanes=nl_def,
        road_width_m=float(road_w), separator_width_m=float(sep_w),
        lane_gap_m=float(lane_gap),
        heading_override=float(global_heading) if use_global_h else None,
        strip_length_m=float(strip_len) if use_sl and strip_len else None,
        gl_mode=gl_mode,
    )
    for mk in markers_raw:
        i=mk["index"]
        ov=MarkerOverride(marker_position=default_pos, custom_offset_m=float(custom_offset))
        lp_ov=st.session_state.per_marker_lanes.get(i)
        if lp_ov and lp_ov in LANE_PRESETS:
            p2=LANE_PRESETS[lp_ov]
            ov.num_lanes=p2["num_lanes"]; ov.road_width_m=p2["road_width_m"]
            ov.separator_width_m=p2["separator_width_m"]
        spec.marker_overrides[i]=ov

    per_h=dict(st.session_state.per_marker_h)
    prog=st.progress(0,"Parsing KML…")
    try:
        m_obj,g_obj,glm_obj,polys=run_pipeline(kml_temp,spec,per_h)
        prog.progress(40,"Generating strips…")
        out_kml =kml_temp.replace(".kml","_out.kml")
        out_xlsx=kml_temp.replace(".kml","_out.xlsx")
        export_kml(m_obj,polys,spec,out_kml)
        prog.progress(70,"Exporting Excel…")
        export_excel(m_obj,g_obj,glm_obj,polys,spec,out_xlsx)
        prog.progress(90,"Building preview…")
        with open(out_kml,"rb") as f: st.session_state.kml_bytes=f.read()
        with open(out_xlsx,"rb") as f: st.session_state.excel_bytes=f.read()
        st.session_state.markers=m_obj; st.session_state.greenlines=g_obj
        st.session_state.gl_matches=glm_obj; st.session_state.all_polygons=polys
        st.session_state.generated=True
        prog.progress(100,"Done ✅"); time.sleep(0.3); prog.empty()
        st.rerun()
    except Exception as e:
        prog.empty(); st.error(f"❌ Error: {e}")
        import traceback; st.code(traceback.format_exc())


# ══════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════
if st.session_state.generated and st.session_state.all_polygons:
    m_obj=st.session_state.markers; g_obj=st.session_state.greenlines
    glm_obj=st.session_state.gl_matches; polys=st.session_state.all_polygons

    st.markdown('<p class="sec-head">✅ Results</p>', unsafe_allow_html=True)
    r1,r2,r3,r4,r5=st.columns(5)
    r1.metric("📍 Markers",     len(m_obj))
    r2.metric("🟨 Strips",      len(polys))
    r3.metric("📏 Green Lines", len(g_obj))
    r4.metric("🟢 Matched",     len(glm_obj))
    r5.metric("Strips/Marker",  len(polys)//max(len(m_obj),1))

    st.markdown('<p class="sec-head">📥 Downloads</p>', unsafe_allow_html=True)
    dl1,dl2=st.columns(2)
    if st.session_state.kml_bytes:
        dl1.download_button("📥 Download KML — Google Earth Pro",
            data=st.session_state.kml_bytes, file_name="speed_breakers.kml",
            mime="application/vnd.google-earth.kml+xml",
            use_container_width=True)
    if st.session_state.excel_bytes:
        dl2.download_button("📊 Download Excel BOQ Report",
            data=st.session_state.excel_bytes, file_name="speed_breakers_boq.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)

    # Marker summary
    st.markdown('<p class="sec-head">📋 Marker Summary</p>', unsafe_allow_html=True)
    by={}
    for p in polys: by.setdefault(p.marker_idx,[]).append(p)
    rows=[]
    for mk in m_obj:
        ps=by.get(mk.index,[]); p0=ps[0] if ps else None
        gl=glm_obj.get(mk.index)
        rows.append({
            "#": mk.index+1, "Marker": mk.name,
            "Road Width (m)": round(p0.road_width_m,2) if p0 else "—",
            "Width Src": p0.rw_src if p0 else "—",
            "Heading °": round(p0.road_heading,1) if p0 else "—",
            "Heading Src": p0.heading_src if p0 else "—",
            "GL Mode": ("Across" if gl and gl.gives_width
                        else "Along" if gl else "—"),
            "Lanes": p0.num_lanes if p0 else "—",
            "Strips": len(ps),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Folium map
    st.markdown('<p class="sec-head">🗺️ Satellite Preview</p>', unsafe_allow_html=True)
    if m_obj:
        clat=sum(m.lat for m in m_obj)/len(m_obj)
        clon=sum(m.lon for m in m_obj)/len(m_obj)
        fmap=folium.Map(location=[clat,clon],zoom_start=19,
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google Satellite")
        COLS=["#FFD700","#FF8C00","#00FF88","#FF44AA","#44FFCC","#CC44FF"]
        for p in polys:
            folium.Polygon(
                locations=[[la,lo] for la,lo in p.coords],
                color=COLS[p.lane_idx%len(COLS)],fill=True,
                fill_color=COLS[p.lane_idx%len(COLS)],fill_opacity=0.85,
                weight=2,
                tooltip=(f"{p.marker_name} | Lane {p.lane_idx+1} | "
                         f"Strip {p.strip_idx+1} | {p.road_heading:.1f}° | "
                         f"Width {p.road_width_m:.2f}m [{p.rw_src}]"),
            ).add_to(fmap)
        for mk in m_obj:
            gl=glm_obj.get(mk.index)
            gl_tip=(f"<br>📏 GL heading: <b>{gl.road_heading:.1f}°</b>"
                    +(f"<br>Width: <b>{gl.length_m:.2f}m</b>" if gl and gl.gives_width else "")
                    if gl else "")
            folium.Marker([mk.lat,mk.lon],
                popup=folium.Popup(f"<b>{mk.name}</b>{gl_tip}",max_width=220),
                icon=folium.Icon(color="red",icon="map-marker",prefix="fa"),
            ).add_to(fmap)
        for gl in g_obj:
            folium.PolyLine([[gl.start_lat,gl.start_lon],[gl.end_lat,gl.end_lon]],
                color="#00cc44",weight=3,dash_array="8,4",
                tooltip=f"GL: {gl.length_m:.2f}m | heading={gl.road_heading:.1f}°",
            ).add_to(fmap)
        st_folium(fmap,width="100%",height=520,returned_objects=[])