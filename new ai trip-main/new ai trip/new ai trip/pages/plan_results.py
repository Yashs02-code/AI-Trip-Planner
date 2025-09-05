import streamlit as st
import folium
from streamlit_folium import st_folium

# --- Page Setup ---
st.set_page_config(page_title="Fishing Trip Results", layout="wide")

# --- If no results, redirect back ---
if "results" not in st.session_state or st.session_state["results"] is None:
    st.warning("⚠️ No trip planned yet. Please plan a trip first.")
    st.page_link("streamlit_app.py", label="⬅️ Go to Planner")
    st.stop()

results = st.session_state["results"]
trip_details = st.session_state.get("trip_details", {})

src_lat = trip_details.get("src_lat")
src_lon = trip_details.get("src_lon")
dst_lat = trip_details.get("dst_lat")
dst_lon = trip_details.get("dst_lon")
port_name = trip_details.get("port_name", "Selected Port")

# --- Custom UI ---
st.markdown(
    """
    <style>
    div[data-testid="stAppViewContainer"], div[data-testid="stMainContent"] {
        background: linear-gradient(135deg, #6A11CB 0%, #2575FC 100%) fixed;
        color: #ffffff;
    }

    .block-container {
        background: transparent !important;
        max-width: 100% !important;
        padding: 1rem !important;
    }

    h1, h2, h3, h4, h5, h6, p, label {
        color: #fff !important;
        word-wrap: break-word;
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

st.title("Fishing Trip Plan Results")

# --- Show routes ---
for r in results:
    dist = r.get("distance_km", None)
    dur = r.get("duration_min", None)
    fuel_l = r.get("fuel_liters", None)
    fuel_cost = r.get("fuel_cost", None)

    exp_title = f"🛥️ Route • {dist:.2f} km • {dur:.1f} min" if dist and dur else "🛥️ Route"
    with st.expander(exp_title, expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Distance (km)", f"{dist:.2f}" if dist else "N/A")
        col2.metric("Duration (min)", f"{dur:.1f}" if dur else "N/A")
        col3.metric("Fuel Needed (L)", f"{fuel_l:.2f}" if isinstance(fuel_l, (int, float)) else (fuel_l or "N/A"))
        col4.metric("Estimated Fuel Cost (₹)", f"{fuel_cost:.2f}" if isinstance(fuel_cost, (int, float)) else (fuel_cost or "N/A"))

        st.markdown("### 🌦 Weather Along Route")
        weather_points = r.get("weather_points", [])
        if weather_points:
            st.dataframe(weather_points)
        else:
            st.write("No weather data available for this route.")

        if r.get("preview_coords"):
            st.markdown("### 🗺 Sea Route Map")
            m = folium.Map(location=[src_lat, src_lon], zoom_start=9, control_scale=True)
            folium.Marker([src_lat, src_lon], popup=f"Port: {port_name}", icon=folium.Icon(color="green")).add_to(m)
            folium.Marker([dst_lat, dst_lon], popup="Fishing Spot 🎣", icon=folium.Icon(color="blue")).add_to(m)
            folium.PolyLine(locations=r["preview_coords"], weight=4, color="blue").add_to(m)

            for wp in weather_points:
                lat_wp = wp.get("lat")
                lon_wp = wp.get("lon")
                if lat_wp and lon_wp:
                    popup_text = ", ".join(
                        str(x) for x in (wp.get("description"), wp.get("temperature")) if x
                    )
                    folium.CircleMarker(
                        location=[lat_wp, lon_wp], radius=5, color="white", fill=True, popup=popup_text
                    ).add_to(m)

            st_folium(m, width=600, height=400)
        else:
            st.warning("🌍 Map preview not available.")

# --- Back Button ---
st.page_link("streamlit_app.py", label="⬅️ Plan Another Trip")
