import math
import requests
from geopy.distance import geodesic
import numpy as np

# ---------------------------
# API KEYS (Direct, no .env)
# ---------------------------
OWM_API_KEY = "f79e348ae2f4d7e4c15eaddeb534f33f"  # OpenWeatherMap

SESSION = requests.Session()
TIMEOUT = 15  # seconds


# ---------------------------
# WEATHER (OpenWeatherMap)
# ---------------------------
def fetch_weather(lat: float, lon: float):
    """Fetch current weather for given coordinates."""
    try:
        if not OWM_API_KEY:
            raise RuntimeError("Missing OpenWeatherMap API key")

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": OWM_API_KEY, "units": "metric"}
        r = SESSION.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json() or {}
        return {
            "temperature": (data.get("main") or {}).get("temp"),
            "wind_speed": (data.get("wind") or {}).get("speed"),
            "description": (data.get("weather") or [{}])[0].get("description"),
        }
    except Exception as e:
        print("❌ Weather API Error:", e)
        return {"temperature": None, "wind_speed": None, "description": None}


# ---------------------------
# SEA ROUTE (Straight Line)
# ---------------------------
def get_sea_route(src_lat, src_lon, dst_lat, dst_lon, num_points=20):
    """Generate a straight-line route over sea from port to fishing ground."""
    lats = np.linspace(src_lat, dst_lat, num_points)
    lons = np.linspace(src_lon, dst_lon, num_points)
    coords = list(zip(lats, lons))

    # Distance in km (geodesic)
    distance_km = geodesic((src_lat, src_lon), (dst_lat, dst_lon)).km
    duration_min = round((distance_km / 20) * 60, 1)  # assume 20 km/h boat speed

    return {
        "provider": "sea_direct",
        "distance_km": round(distance_km, 2),
        "duration_min": duration_min,
        "coords": coords,
    }


# ---------------------------
# WEATHER ALONG ROUTE
# ---------------------------
def sample_points(coords, every_km=25.0, max_points=10):
    """Down-sample polyline coords every `every_km`. Include start & end."""
    if not coords:
        return []
    pts = [coords[0]]
    acc = 0.0
    for i in range(1, len(coords)):
        d = geodesic(coords[i - 1], coords[i]).km
        acc += d
        if acc >= every_km:
            pts.append(coords[i])
            acc = 0.0
        if len(pts) >= max_points - 1:
            break
    if coords[-1] != pts[-1]:
        pts.append(coords[-1])
    return pts[:max_points]


def weather_along_route(coords, every_km=25.0, max_points=10):
    """Fetch weather for sampled route points."""
    points = sample_points(coords, every_km=every_km, max_points=max_points)
    out = []
    for lat, lon in points:
        w = fetch_weather(lat, lon)
        out.append({"lat": lat, "lon": lon, **w})
    return out


# ---------------------------
# FUEL MODEL
# ---------------------------
def estimate_fuel_liters(distance_km: float, efficiency_kmpl: float = 0.5, reserve_pct: float = 0.1):
    """Estimate fuel usage with a reserve margin."""
    try:
        if distance_km is None or efficiency_kmpl <= 0:
            return None
        base = distance_km / efficiency_kmpl
        total = base * (1.0 + max(0.0, reserve_pct))
        return round(total, 2)
    except Exception as e:
        print("❌ Fuel estimate error:", e)
        return None


# ---------------------------
# HIGH-LEVEL PLANNER
# ---------------------------
def plan_trip(src_lat, src_lon, dst_lat, dst_lon,
              efficiency_kmpl=0.5, reserve_pct=0.1, cost_per_liter=None):
    """Plan trip: sea route, weather, and fuel estimate."""
    route = get_sea_route(src_lat, src_lon, dst_lat, dst_lon)

    weather_points = weather_along_route(route.get("coords", []), every_km=25.0, max_points=10)
    fuel_liters = estimate_fuel_liters(route.get("distance_km"), efficiency_kmpl, reserve_pct)
    fuel_cost = round(fuel_liters * float(cost_per_liter), 2) if (fuel_liters and cost_per_liter) else None

    return [{
        "route_index": 0,
        "provider": route.get("provider"),
        "distance_km": route.get("distance_km"),
        "duration_min": route.get("duration_min"),
        "fuel_liters": fuel_liters,
        "fuel_cost": fuel_cost,
        "weather_points": weather_points,
        "preview_coords": route.get("coords", [])[::2],
    }]
