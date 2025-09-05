import streamlit as st
import ai_trip_recommendation_live as ai
from fishing_ports import FISHING_PORTS
import traceback

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except Exception:
    FOLIUM_AVAILABLE = False

# --- Page Setup ---
st.set_page_config(page_title="Fishing Trip Planner", layout="wide")

# initialize session state
if "results" not in st.session_state:
    st.session_state["results"] = None

# --- Custom CSS for Modern Responsive UI ---
st.markdown(
    """
    <style>
    
    /* Make only form field labels white */
label, [data-testid="stWidgetLabel"] {
    color: white !important;
    font-weight: 600;   /* make them bold for visibility */
}

    
    div[data-testid="stAppViewContainer"], div[data-testid="stMainContent"] {
        background: linear-gradient(135deg, #6A11CB 0%, #2575FC 100%) fixed;
        color: #ffffff;
    }

    .block-container {
        background: transparent !important;
        max-width: 100% !important;
        padding: 1rem !important;
    }

    .stButton > button {
        background: linear-gradient(90deg, #2575FC, #6A11CB);
        color: white !important;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        font-size: 1rem;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        border: none;
    }
    .stButton > button:hover {
        transform: scale(1.03);
        transition: all 0.2s ease-in-out;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Smart Fishing Trip Planner — Port to Sea")

# --- Input Section ---
st.subheader("⚓ Select Source Port")
city = st.selectbox("City", options=list(FISHING_PORTS.keys()))
ports = [p["name"] for p in FISHING_PORTS[city]]
port_name = st.selectbox("Port", options=ports)
chosen_port = next(p for p in FISHING_PORTS[city] if p["name"] == port_name)
src_lat, src_lon = chosen_port["lat"], chosen_port["lon"]

# --- Destination ---
st.subheader("🎯 Destination (Fishing Ground)")

if FOLIUM_AVAILABLE:
    st.markdown("Click on map to set fishing spot (or use inputs below).")
    m_select = folium.Map(location=[src_lat, src_lon], zoom_start=8, control_scale=True)
    folium.Marker([src_lat, src_lon], popup=f"Port: {port_name}", icon=folium.Icon(color="green")).add_to(m_select)

    map_out = st_folium(m_select, width=500, height=300)
    if map_out and map_out.get("last_clicked"):
        dst_lat = map_out["last_clicked"]["lat"]
        dst_lon = map_out["last_clicked"]["lng"]
        st.success(f"📍 Fishing Spot Selected: {dst_lat:.4f}, {dst_lon:.4f}")
    else:
        dst_lat = st.number_input("Fishing Spot Latitude", value=18.9581, format="%.6f")
        dst_lon = st.number_input("Fishing Spot Longitude", value=72.8408, format="%.6f")
else:
    dst_lat = st.number_input("Fishing Spot Latitude", value=18.9581, format="%.6f")
    dst_lon = st.number_input("Fishing Spot Longitude", value=72.8408, format="%.6f")

# --- Options ---
st.subheader("⚙️ Trip Options")
eff_kmpl = st.number_input("Boat Efficiency (km/l)", value=0.5, min_value=0.1, max_value=5.0, step=0.1)
reserve_pct = st.slider("Reserve %", 0.0, 0.5, 0.1, step=0.05)
cost_per_liter = st.number_input("Fuel cost per liter (₹)", value=6.0, min_value=0.0, step=0.5)

# --- Plan Button ---
if st.button("🚀 Plan Fishing Trip"):
    with st.spinner("🌊 Calculating sea route and fetching weather..."):
        try:
            st.session_state["results"] = ai.plan_trip(
                src_lat,
                src_lon,
                dst_lat,
                dst_lon,
                efficiency_kmpl=eff_kmpl,
                reserve_pct=reserve_pct,
                cost_per_liter=(cost_per_liter if cost_per_liter > 0 else None),
            )
            st.session_state["trip_details"] = {
                "src_lat": src_lat,
                "src_lon": src_lon,
                "dst_lat": dst_lat,
                "dst_lon": dst_lon,
                "port_name": port_name,
            }
            st.switch_page("pages/plan_results.py")
        except Exception:
            st.session_state["results"] = None
            st.error("Failed to plan trip — see details below.")
            st.text(traceback.format_exc())
