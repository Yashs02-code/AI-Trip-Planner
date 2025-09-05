from flask import Flask, jsonify, request
from flask_cors import CORS
import ai_trip_recommendation_live as ai
from fishing_ports import FISHING_PORTS

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Fishing Trip Planner API (Sea Route + Weather + Fuel)"})


@app.route("/ports", methods=["GET"])
def get_ports():
    return jsonify(FISHING_PORTS)


def _find_port(city, port_name):
    """Find a port by city + name"""
    city_list = FISHING_PORTS.get(city, [])
    for p in city_list:
        if p["name"].lower() == port_name.lower() or port_name.lower() in p["name"].lower():
            return p
    return None


@app.route("/plan", methods=["GET"])
def plan():
    """Plan a fishing trip (port → sea destination)."""
    efficiency_kmpl = float(request.args.get("efficiency_kmpl", 0.5))
    reserve_pct = float(request.args.get("reserve_pct", 0.1))
    cost_per_liter = request.args.get("cost_per_liter")

    # Destination can be selected from port list OR entered manually
    city_dst = request.args.get("city_dst")
    port_dst = request.args.get("port_dst")
    if city_dst and port_dst:
        p = _find_port(city_dst, port_dst)
        if not p:
            return jsonify({"error": "Destination port not found"}), 400
        dst_lat, dst_lon = p["lat"], p["lon"]
    else:
        try:
            dst_lat = float(request.args.get("dst_lat"))
            dst_lon = float(request.args.get("dst_lon"))
        except (TypeError, ValueError):
            return jsonify({"error": "Provide destination via city_dst+port_dst or dst_lat+dst_lon"}), 400

    try:
        src_lat = float(request.args.get("src_lat"))
        src_lon = float(request.args.get("src_lon"))
    except (TypeError, ValueError):
        return jsonify({"error": "src_lat and src_lon are required"}), 400

    try:
        results = ai.plan_trip(
            src_lat, src_lon, dst_lat, dst_lon,
            efficiency_kmpl=efficiency_kmpl,
            reserve_pct=reserve_pct,
            cost_per_liter=cost_per_liter
        )
        return jsonify({
            "source": {"lat": src_lat, "lon": src_lon},
            "destination": {"lat": dst_lat, "lon": dst_lon},
            "routes": results
        })
    except Exception as e:
        print("❌ Plan error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
