import streamlit as st
import json
import plotly.graph_objects as go
from PIL import Image
import numpy as np
import os
import time

# ── Page Config ──
st.set_page_config(page_title="LILA BLACK — Player Journey Tool", page_icon="🎮", layout="wide", initial_sidebar_state="expanded")

# ── Custom CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

.stApp { 
    background-color: #0b0f19;
    background-image: radial-gradient(circle at top right, rgba(79, 195, 247, 0.05), transparent 40%),
                      radial-gradient(circle at bottom left, rgba(206, 147, 216, 0.05), transparent 40%);
}
section[data-testid="stSidebar"] { 
    background-color: rgba(18, 24, 38, 0.85); 
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(48, 54, 61, 0.5); 
}
section[data-testid="stSidebar"] .stMarkdown p { color: #94a3b8; font-family: 'Inter', sans-serif; }
.hdr { font-family: 'Rajdhani', sans-serif; font-size:2rem; font-weight:700; background:linear-gradient(90deg,#4FC3F7,#CE93D8,#EF5350);
       -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0; text-transform: uppercase; letter-spacing: 1px; }
.sub { font-family: 'Inter', sans-serif; color:#64748b; font-size:0.9rem; margin-top:0; font-weight: 500; }

/* HUD Stat Cards */
.stat-row { display:flex; gap:12px; margin-bottom:12px; }
.stat-card { 
    background: rgba(18, 24, 38, 0.6); 
    backdrop-filter: blur(8px);
    border: 1px solid rgba(48, 54, 61, 0.6); 
    border-radius: 6px; 
    padding: 10px 12px; 
    flex: 1; 
    text-align: center; 
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.2s ease;
}
.stat-card:hover { border-color: rgba(79, 195, 247, 0.4); box-shadow: 0 0 15px rgba(79, 195, 247, 0.15); }
.stat-value { font-family: 'Rajdhani', sans-serif; font-size:1.6rem; font-weight:700; color:#f8fafc; text-shadow: 0 0 10px rgba(255,255,255,0.1); }
.stat-label { font-family: 'Inter', sans-serif; font-size:0.65rem; color:#94a3b8; text-transform:uppercase; letter-spacing:1px; font-weight: 600; margin-top: 2px; }

/* Section Headers */
.sec { font-family: 'Rajdhani', sans-serif; font-size:0.85rem; font-weight:600; color:#cbd5e1; text-transform:uppercase; letter-spacing:1.5px;
       padding: 8px 0 4px; border-bottom: 1px solid rgba(48, 54, 61, 0.5); margin-top:16px; margin-bottom: 8px; }

/* Legend */
.lg { background: rgba(18, 24, 38, 0.6); backdrop-filter: blur(8px); border:1px solid rgba(48, 54, 61, 0.6); border-radius:6px; padding:12px; margin-top:8px; }
.li { display:flex; align-items:center; gap:10px; padding:3px 0; font-size:0.85rem; color:#cbd5e1; font-family: 'Inter', sans-serif; }

/* Timestamp Display */
.ts-display { font-family: 'Rajdhani', sans-serif; font-size:1.3rem; color:#4FC3F7; font-weight:700; letter-spacing: 1px; text-shadow: 0 0 8px rgba(79, 195, 247, 0.3); }

/* Custom Scrollbar for Event Feed */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(11, 15, 25, 0.5); border-radius: 4px; }
::-webkit-scrollbar-thumb { background: rgba(48, 54, 61, 0.8); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(79, 195, 247, 0.5); }

/* Skeleton Loader Animation */
@keyframes pulse {
    0% { opacity: 0.6; }
    50% { opacity: 0.3; }
    100% { opacity: 0.6; }
}
.skeleton-box {
    background: rgba(48, 54, 61, 0.5);
    border-radius: 6px;
    animation: pulse 1.5s infinite ease-in-out;
}

/* Playback Control Buttons */
.stButton > button {
    background: rgba(18, 24, 38, 0.6) !important;
    border: 1px solid rgba(79, 195, 247, 0.3) !important;
    backdrop-filter: blur(8px) !important;
    color: #4FC3F7 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
}
.stButton > button:hover {
    border-color: #4FC3F7 !important;
    box-shadow: 0 0 15px rgba(79, 195, 247, 0.2) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    background: rgba(79, 195, 247, 0.1) !important;
    transform: translateY(1px) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ──
BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
MATCHES_DIR = os.path.join(PROCESSED_DATA_DIR, "matches")
HEATMAPS_DIR = os.path.join(PROCESSED_DATA_DIR, "heatmaps")
MINIMAP_DIR = os.path.join(BASE, "assets", "minimaps")

MAP_FILES = {"AmbroseValley": "AmbroseValley_Minimap.png", "GrandRift": "GrandRift_Minimap.png", "Lockdown": "Lockdown_Minimap.jpg"}
MAP_ICON = {"AmbroseValley": "Ambrose Valley", "GrandRift": "Grand Rift", "Lockdown": "Lockdown"}
DATE_LABEL = {"February_10": "Feb 10", "February_11": "Feb 11", "February_12": "Feb 12", "February_13": "Feb 13", "February_14": "Feb 14"}

EVENT_STYLE = {
    "Kill":          ("#EF5350", "x",           "Kill (Human)",  14),
    "Killed":        ("#C62828", "cross",        "Death (Human)", 12),
    "BotKill":       ("#FFA726", "diamond",      "Kill (Bot)",    12),
    "BotKilled":     ("#FB8C00", "diamond-open", "Death (Bot)",   10),
    "KilledByStorm": ("#26C6DA", "star",         "Storm Death",   14),
    "Loot":          ("#FFD54F", "circle",       "Loot Pickup",    7),
}
HUMAN_COLOR = "#4FC3F7"
BOT_COLOR = "#CE93D8"

def fmt_time(ms):
    """Format milliseconds as M:SS.s"""
    if ms < 0: ms = 0
    s = ms / 1000
    m = int(s // 60)
    sec = s % 60
    return f"{m}:{sec:04.1f}"

# ── Data Loaders ──
@st.cache_data
def load_index():
    with open(os.path.join(PROCESSED_DATA_DIR, "index.json")) as f: return json.load(f)

@st.cache_data
def load_match(mid):
    with open(os.path.join(MATCHES_DIR, f"{mid}.json")) as f: return json.load(f)

@st.cache_data
def load_heatmaps(map_id):
    p = os.path.join(HEATMAPS_DIR, f"{map_id}_heatmaps.json")
    if not os.path.exists(p): return None
    with open(p) as f: return json.load(f)

@st.cache_data
def load_minimap(map_id):
    return Image.open(os.path.join(MINIMAP_DIR, MAP_FILES[map_id]))

# ── Session State Init ──
if "playing" not in st.session_state: st.session_state.playing = False
if "ts" not in st.session_state: st.session_state.ts = None

# ── Load Index ──
if not os.path.exists(os.path.join(PROCESSED_DATA_DIR, "index.json")):
    st.error("Run `python scripts/process_data.py` first."); st.stop()
index = load_index()
all_matches = index["matches"]

# ══════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown('<p class="hdr">LILA BLACK</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub">Player Journey Tool v1.0</p>', unsafe_allow_html=True)

    # ── Map Selector ──
    st.markdown('<div class="sec">Map</div>', unsafe_allow_html=True)
    # Only show maps that actually have matches in the index
    maps_with_data = sorted(list({v["map_id"] for v in all_matches.values()}))
    if not maps_with_data:
        st.error("No map data found in index."); st.stop()
        
    sel_map = st.selectbox(
        "Map", maps_with_data, 
        format_func=lambda k: MAP_ICON.get(k, k), 
        label_visibility="collapsed",
        key="map_selector"
    )

    # ── Date Selector (Cascading: Filtered by Map) ──
    st.markdown('<div class="sec">Date</div>', unsafe_allow_html=True)
    dates_for_map = sorted(
        {v["date"] for v in all_matches.values() if v["map_id"] == sel_map}, 
        key=lambda d: index["dates"].index(d) if d in index["dates"] else 0
    )
    
    if not dates_for_map:
        st.warning(f"No dates available for {sel_map}"); st.stop()
        
    sel_date = st.selectbox(
        "Date", dates_for_map, 
        format_func=lambda d: DATE_LABEL.get(d, d), 
        label_visibility="collapsed",
        key="date_selector"
    )

    # ── Match Selector (Cascading: Filtered by Map + Date) ──
    st.markdown('<div class="sec">Match</div>', unsafe_allow_html=True)
    filt = {
        k: v for k, v in all_matches.items() 
        if v["map_id"] == sel_map and v["date"] == sel_date
    }
    
    if not filt:
        st.warning("No matches found for this selection."); st.stop()
        
    mids = sorted(list(filt.keys()))
    sel_mid = st.selectbox(
        "Match", mids, 
        format_func=lambda m: f"{m[:12]}… ({filt[m]['human_count']}H / {filt[m]['bot_count']}B)", 
        label_visibility="collapsed",
        key="match_selector"
    )
    meta = filt[sel_mid]

    # Layers
    st.markdown('<div class="sec">Layers</div>', unsafe_allow_html=True)
    show_human = st.toggle("Human Trails", True)
    show_bot = st.toggle("Bot Trails", True)
    show_combat = st.toggle("Combat Events", True)
    show_loot = st.toggle("Loot Pickups", False)
    show_storm = st.toggle("Storm Deaths", True)

    # Heatmap
    st.markdown('<div class="sec">Heatmap Overlay</div>', unsafe_allow_html=True)
    hm_layer = st.selectbox("Layer", ["None", "Traffic", "Kills", "Deaths", "Storm Deaths"], label_visibility="collapsed")
    hm_opacity = st.slider("Opacity", 0.1, 0.9, 0.4, 0.05, disabled=(hm_layer == "None"))

    # Legend
    st.markdown('<div class="sec">Legend</div>', unsafe_allow_html=True)
    st.markdown(f"""<div class="lg">
      <div class="li"><div style="width:20px;height:3px;background:{HUMAN_COLOR};border-radius:2px"></div> Human Trail</div>
      <div class="li"><div style="width:20px;height:0;border-top:2px dashed {BOT_COLOR}"></div> Bot Trail</div>
      <div class="li"><span style="color:#EF5350;font-weight:700">✕</span> Kill (Human)</div>
      <div class="li"><span style="color:#C62828;font-weight:700">✛</span> Death (Human)</div>
      <div class="li"><span style="color:#FFA726;font-weight:700">◆</span> Kill (Bot)</div>
      <div class="li"><span style="color:#26C6DA;font-weight:700">★</span> Storm Death</div>
      <div class="li"><div style="width:10px;height:10px;border-radius:50%;background:#FFD54F"></div> Loot</div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# MAIN AREA
# Loading state
skeleton_placeholder = st.empty()
skeleton_placeholder.markdown("""
    <div style="display:flex; gap:12px; margin-bottom:12px;">
        <div class="skeleton-box" style="flex:1; height:70px;"></div>
        <div class="skeleton-box" style="flex:1; height:70px;"></div>
        <div class="skeleton-box" style="flex:1; height:70px;"></div>
        <div class="skeleton-box" style="flex:1; height:70px;"></div>
    </div>
    <div class="skeleton-box" style="width:100%; height:600px; margin-top:20px;"></div>
""", unsafe_allow_html=True)

with st.spinner("Initializing Data Link..."):
    try:
        match = load_match(sel_mid)
        if not match: 
            st.error("Match file missing or could not be loaded."); st.stop()
    except Exception as e:
        st.error(f"Error loading match: {e}")
        st.stop()

# Clear the skeleton loader once data is fetched
skeleton_placeholder.empty()
        
players = match["players"]

# Compute stats & max timestamp
max_ts = 0
kills = deaths = loot_n = storm_n = 0
for p in players.values():
    for e in p["events"]:
        ev = e["event"]
        if e["ts"] > max_ts: max_ts = e["ts"]
        if ev in ("Kill", "BotKill"): kills += 1
        elif ev in ("Killed", "BotKilled"): deaths += 1
        elif ev == "Loot": loot_n += 1
        elif ev == "KilledByStorm": storm_n += 1

if max_ts == 0: 
    st.warning("No events found in this match.")
    st.stop()

# Reset ts when match changes
if st.session_state.ts is None or st.session_state.ts > max_ts:
    st.session_state.ts = max_ts
    st.session_state.playing = False

# ── Header ──
st.markdown(f'<p class="hdr">{MAP_ICON[sel_map]}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="sub">{DATE_LABEL[sel_date]} · Match {sel_mid[:20]}… · Duration {fmt_time(max_ts)}</p>', unsafe_allow_html=True)

# ── Stat Cards ──
st.markdown(f"""<div class="stat-row" style="flex-wrap: wrap;">
  <div class="stat-card"><div class="stat-value" style="color:{HUMAN_COLOR}">{meta['human_count']}</div><div class="stat-label">Humans</div></div>
  <div class="stat-card"><div class="stat-value" style="color:{BOT_COLOR}">{meta['bot_count']}</div><div class="stat-label">Bots</div></div>
  <div class="stat-card"><div class="stat-value" style="color:#EF5350">{kills}</div><div class="stat-label">Kills</div></div>
  <div class="stat-card"><div class="stat-value" style="color:#C62828">{deaths}</div><div class="stat-label">Deaths</div></div>
  <div class="stat-card"><div class="stat-value" style="color:#26C6DA">{storm_n}</div><div class="stat-label">Storm</div></div>
  <div class="stat-card"><div class="stat-value" style="color:#FFD54F">{loot_n}</div><div class="stat-label">Loot</div></div>
</div>""", unsafe_allow_html=True)

# ── Playback Controls ──
ctrl_cols = st.columns([1, 1, 1, 6, 2])
with ctrl_cols[0]:
    if st.button("⏮", help="Jump to start"):
        st.session_state.ts = 0; st.session_state.playing = False
with ctrl_cols[1]:
    if st.session_state.playing:
        if st.button("⏸️", help="Pause"):
            st.session_state.playing = False; st.rerun()
    else:
        if st.button("▶️", help="Play"):
            st.session_state.playing = True; st.rerun()
with ctrl_cols[2]:
    if st.button("⏭", help="Jump to end"):
        st.session_state.ts = max_ts; st.session_state.playing = False
with ctrl_cols[3]:
    new_ts = st.slider("Timeline", 0, max_ts, st.session_state.ts, format="%d ms", label_visibility="collapsed")
    if new_ts != st.session_state.ts:
        st.session_state.ts = new_ts
        st.session_state.playing = False
with ctrl_cols[4]:
    speed = st.selectbox("Speed", [1, 2, 5, 10], index=1, format_func=lambda x: f"{x}x", label_visibility="collapsed")

# Timestamp display
st.markdown(f'<div class="ts-display">⏱ {fmt_time(st.session_state.ts)} / {fmt_time(max_ts)}</div>', unsafe_allow_html=True)

current_ts = st.session_state.ts

# ── Pre-collect event feed (must be BEFORE column split) ──
event_feed = []
for uid, pd_ in players.items():
    is_bot = pd_["is_bot"]
    if is_bot and not show_bot: continue
    if not is_bot and not show_human: continue
    for e in pd_["events"]:
        if e["ts"] <= current_ts and e["event"] not in ("Position", "BotPosition"):
            event_feed.append({"ts": e["ts"], "event": e["event"], "uid": uid, "is_bot": is_bot})

# Setup Layout for Chart and Event Feed
main_cols = st.columns([3, 1], gap="medium")

with main_cols[0]:
    with st.spinner("Rendering minimap..."):
        # ══════════════════════════════════════════════
        # BUILD FIGURE
        # ══════════════════════════════════════════════
        fig = go.Figure()
        
        # Background minimap
        try:
            img = load_minimap(sel_map)
            fig.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=1024, sizex=1024, sizey=1024, sizing="stretch", opacity=1, layer="below"))
        except Exception as e:
            st.warning("Could not load minimap image.")
            
        fig.update_xaxes(range=[0, 1024], showgrid=False, zeroline=False, visible=False)
        fig.update_yaxes(range=[0, 1024], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1)
        
        # Heatmap overlay — use modern Plotly colorbar dict API
        if hm_layer != "None":
            hm = load_heatmaps(sel_map)
            if hm:
                key_map = {"Traffic": "traffic_density", "Kills": "kill_density", "Deaths": "death_density", "Storm Deaths": "storm_deaths"}
                z = hm.get(key_map.get(hm_layer))
                if z:
                    gs = len(z)
                    c = np.linspace(1024/(2*gs), 1024 - 1024/(2*gs), gs)
                    fig.add_trace(go.Contour(
                        z=z, x=c, y=c, colorscale="Hot", reversescale=True,
                        opacity=hm_opacity, showlegend=False, ncontours=20,
                        line=dict(width=0), hoverinfo="skip",
                        colorbar=dict(
                            title=dict(text=hm_layer, side="right",
                                       font=dict(color="#c9d1d9", size=11)),
                            thickness=12, len=0.4, y=0.2,
                            tickfont=dict(color="#8b949e", size=10)
                        )
                    ))
        
        # Collect events by type for batched traces
        combat_batches = {}
        loot_xs, loot_ys = [], []
        human_shown = bot_shown = False
        
        for uid, pd_ in players.items():
            is_bot = pd_["is_bot"]
            if is_bot and not show_bot: continue
            if not is_bot and not show_human: continue
        
            vis = [e for e in pd_["events"] if e["ts"] <= current_ts]
            if not vis: continue
        
            pos = [e for e in vis if e["event"] in ("Position", "BotPosition")]
        
            # Trails
            if pos:
                xs = [e["x"] for e in pos]
                ys = [e["y"] for e in pos]
                hover_texts = [f"<b>{'Bot' if is_bot else 'Human'} Path</b><br>ID: {uid[:8]}<br>Time: {fmt_time(e['ts'])}" for e in pos]
                
                if is_bot:
                    show_leg = not bot_shown; bot_shown = True
                    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=1.5, color=BOT_COLOR, dash="dot"),
                                             opacity=0.6, name="🤖 Bot Trail", showlegend=show_leg, 
                                             hoverinfo="text", hovertext=hover_texts, legendgroup="bot"))
                else:
                    show_leg = not human_shown; human_shown = True
                    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=2.5, color=HUMAN_COLOR),
                                             opacity=0.7, name="👤 Human Trail", showlegend=show_leg, 
                                             hoverinfo="text", hovertext=hover_texts, legendgroup="human"))
        
                # Current position dot with white border
                lp = pos[-1]
                col = BOT_COLOR if is_bot else HUMAN_COLOR
                label = "Bot" if is_bot else "Human"
                fig.add_trace(go.Scatter(
                    x=[lp["x"]], y=[lp["y"]], mode="markers",
                    marker=dict(size=10, color=col, symbol="circle", line=dict(width=2, color="#fff")),
                    text=f"<b>{label} Position</b><br>ID: {uid[:8]}<br>Time: {fmt_time(lp['ts'])}",
                    hoverinfo="text", showlegend=False))
        
            # Combat events
            for e in vis:
                et = e["event"]
                if et in ("Kill", "Killed", "BotKill", "BotKilled") and show_combat:
                    if et not in combat_batches: combat_batches[et] = {"x": [], "y": [], "text": []}
                    combat_batches[et]["x"].append(e["x"])
                    combat_batches[et]["y"].append(e["y"])
                    combat_batches[et]["text"].append(f"<b>{EVENT_STYLE[et][2]}</b><br>Player: {uid[:8]}<br>Time: {fmt_time(e['ts'])}")
                elif et == "KilledByStorm" and show_storm:
                    if et not in combat_batches: combat_batches[et] = {"x": [], "y": [], "text": []}
                    combat_batches[et]["x"].append(e["x"])
                    combat_batches[et]["y"].append(e["y"])
                    combat_batches[et]["text"].append(f"<b>Storm Death</b><br>Player: {uid[:8]}<br>Time: {fmt_time(e['ts'])}")
                elif et == "Loot" and show_loot:
                    loot_xs.append(e["x"]); loot_ys.append(e["y"])
        
        # Render batched combat traces
        for et, b in combat_batches.items():
            color, sym, label, sz = EVENT_STYLE[et]
            fig.add_trace(go.Scatter(x=b["x"], y=b["y"], mode="markers",
                                     marker=dict(size=sz, color=color, symbol=sym, line=dict(width=1, color="#fff")),
                                     name=label, text=b["text"], hoverinfo="text", showlegend=True))
        
        if loot_xs:
            fig.add_trace(go.Scatter(x=loot_xs, y=loot_ys, mode="markers",
                                     marker=dict(size=7, color="#FFD54F", symbol="circle", line=dict(width=.5, color="#000")),
                                     name="💰 Loot", hoverinfo="text", hovertext="<b>Loot Pickup</b>", showlegend=True))
        
        fig.update_layout(
            width=1050, height=1050, margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            showlegend=True, dragmode="pan", hovermode="closest",
            legend=dict(yanchor="top", y=.99, xanchor="left", x=.01, bgcolor="rgba(22,27,34,.85)",
                        bordercolor="#30363d", borderwidth=1, font=dict(color="#c9d1d9", size=11)),
            modebar=dict(bgcolor="rgba(0,0,0,0)", color="#8b949e", activecolor="#4FC3F7"),
        )
        
        # ── Render Chart ──
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": True,
                        "modeBarButtonsToRemove": ["autoScale2d", "lasso2d", "select2d"]})

with main_cols[1]:
    st.markdown('<div class="sec">Event Feed (Up to current time)</div>', unsafe_allow_html=True)

    # Sort feed descending by time, take top 50
    event_feed.sort(key=lambda x: x["ts"], reverse=True)
    recent_events = event_feed[:50]

    if not recent_events:
        st.caption("No events up to this point.")
    else:
        # Use a fixed-height container for scrolling (Streamlit ≥1.32)
        try:
            feed_container = st.container(height=900, border=False)
        except TypeError:
            # Fallback for older Streamlit — plain container
            feed_container = st.container()

        with feed_container:
            for ev in recent_events:
                et = ev["event"]
                if et in EVENT_STYLE:
                    color = EVENT_STYLE[et][0]
                    label = EVENT_STYLE[et][2]
                else:
                    color = "#c9d1d9"
                    label = et

                # Render each card as its own markdown call — avoids Streamlit
                # HTML-blob sanitization that corrupts large concatenated strings
                st.markdown(
                    f'<div style="background:rgba(18,24,38,0.7);backdrop-filter:blur(8px);border:1px solid rgba(48,54,61,0.6);'
                    f'border-left:3px solid {color};border-radius:6px;padding:10px 12px;margin-bottom:8px;font-size:0.8rem;'
                    f'box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">'
                    f'<strong style="color:{color}; font-family:\'Rajdhani\', sans-serif; font-size:1.05rem; letter-spacing:0.5px; text-transform:uppercase;">{label}</strong>'
                    f'<span style="color:#64748b; font-size:0.75rem; font-family:monospace; background:rgba(0,0,0,0.2); padding:2px 6px; border-radius:4px;">{fmt_time(ev["ts"])}</span>'
                    f'</div>'
                    f'<div style="color:#94a3b8; font-size:0.75rem; font-family:\'Inter\', sans-serif; margin-top:4px;">Player ID: <span style="color:#cbd5e1;">{ev["uid"][:8]}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


# ══════════════════════════════════════════════
# PLAYBACK ENGINE (must be at end of script)
# ══════════════════════════════════════════════
if st.session_state.playing:
    # Advance by speed-dependent step
    step = max(1, max_ts // 200) * speed
    st.session_state.ts = min(st.session_state.ts + step, max_ts)
    if st.session_state.ts >= max_ts:
        st.session_state.playing = False
    time.sleep(0.05)
    st.rerun()
