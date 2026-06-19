import os
import threading
import time
import urllib.request
import swisseph as swe
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Absolute path to the local ephe directory — resolved once at module load
EPHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ephe")

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

PLANETS = {
    "Sun":       swe.SUN,
    "Moon":      swe.MOON,
    "Mercury":   swe.MERCURY,
    "Venus":     swe.VENUS,
    "Mars":      swe.MARS,
    "Jupiter":   swe.JUPITER,
    "Saturn":    swe.SATURN,
    "Uranus":    swe.URANUS,
    "Neptune":   swe.NEPTUNE,
    "Pluto":     swe.PLUTO,
    "Chiron":    swe.CHIRON,
    "NorthNode": swe.MEAN_NODE,
}


def lon_to_dms(lon: float) -> dict:
    sign_idx = int(lon / 30) % 12
    deg_in_sign = lon % 30
    degree = int(deg_in_sign)
    minute = int((deg_in_sign - degree) * 60)
    return {
        "longitude": round(lon, 6),
        "sign": SIGNS[sign_idx],
        "degree": degree,
        "minute": minute,
        "_sign_idx": sign_idx,
    }


def whole_sign_house(planet_lon: float, asc_lon: float) -> int:
    asc_sign = int(asc_lon / 30) % 12
    planet_sign = int(planet_lon / 30) % 12
    return (planet_sign - asc_sign) % 12 + 1


def calculate_natal_chart(year: int, month: int, day: int,
                           hour: int, minute: int,
                           lat: float, lon: float) -> dict:
    """Core natal chart calculation. All times are Universal Time (UTC)."""
    # Set ephe path before every calculation so it's active in any thread/worker.
    swe.set_ephe_path(EPHE_PATH)

    jd = swe.julday(year, month, day, hour + minute / 60.0)

    cusps, ascmc = swe.houses(jd, lat, lon, b"W")
    asc_lon = ascmc[0]
    mc_lon = ascmc[1]

    asc_info = lon_to_dms(asc_lon)
    mc_info = lon_to_dms(mc_lon)

    result = {
        "ascendant": {
            "longitude": asc_info["longitude"],
            "sign": asc_info["sign"],
            "degree": asc_info["degree"],
            "minute": asc_info["minute"],
            "house": 1,
        },
        "mc": {
            "longitude": mc_info["longitude"],
            "sign": mc_info["sign"],
            "degree": mc_info["degree"],
            "minute": mc_info["minute"],
            "house": whole_sign_house(mc_lon, asc_lon),
        },
        "planets": {},
    }

    for name, planet_id in PLANETS.items():
        try:
            pos, _ret = swe.calc_ut(jd, planet_id)
            p_lon = pos[0]
            speed = pos[3]
            info = lon_to_dms(p_lon)
            result["planets"][name] = {
                "longitude": info["longitude"],
                "sign": info["sign"],
                "degree": info["degree"],
                "minute": info["minute"],
                "house": whole_sign_house(p_lon, asc_lon),
                "retrograde": speed < 0,
            }
        except Exception as exc:
            result["planets"][name] = {"error": str(exc)}

    return result


def parse_params(data: dict) -> tuple:
    """Extract and validate required fields from a dict. Returns (values, error_response)."""
    required = ["year", "month", "day", "hour", "minute", "lat", "lon"]
    missing = [f for f in required if f not in data]
    if missing:
        return None, ({"error": f"Missing required fields: {', '.join(missing)}"}, 400)

    try:
        year   = int(data["year"])
        month  = int(data["month"])
        day    = int(data["day"])
        hour   = int(data["hour"])
        minute = int(data["minute"])
        lat    = float(data["lat"])
        lon    = float(data["lon"])
    except (ValueError, TypeError) as exc:
        return None, ({"error": f"Invalid parameter value: {exc}"}, 400)

    if not (1 <= month <= 12):
        return None, ({"error": "month must be 1–12"}, 400)
    if not (1 <= day <= 31):
        return None, ({"error": "day must be 1–31"}, 400)
    if not (0 <= hour <= 23):
        return None, ({"error": "hour must be 0–23"}, 400)
    if not (0 <= minute <= 59):
        return None, ({"error": "minute must be 0–59"}, 400)
    if not (-90 <= lat <= 90):
        return None, ({"error": "lat must be -90 to 90"}, 400)
    if not (-180 <= lon <= 180):
        return None, ({"error": "lon must be -180 to 180"}, 400)

    return (year, month, day, hour, minute, lat, lon), None


# ---------------------------------------------------------------------------
# Keep-alive background thread
# ---------------------------------------------------------------------------

def _keep_alive(port: int, interval: int = 240):
    """Ping /health every `interval` seconds so the service never idles out."""
    time.sleep(30)  # wait for Flask to finish starting up
    url = f"http://127.0.0.1:{port}/health"
    while True:
        try:
            urllib.request.urlopen(url, timeout=10)
        except Exception:
            pass
        time.sleep(interval)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/test")
def natal_chart_test():
    """Hardcoded test chart: 1984-02-27 07:30 UTC, Mulhouse FR."""
    return jsonify(calculate_natal_chart(1984, 2, 27, 7, 30, 47.7508, 7.3359))


@app.route("/natal")
def natal_chart_get():
    """GET /natal?year=&month=&day=&hour=&minute=&lat=&lon=  (all times UTC)"""
    values, err = parse_params(request.args)
    if err:
        body, status = err
        return jsonify(body), status
    return jsonify(calculate_natal_chart(*values))


@app.route("/natal", methods=["POST"])
def natal_chart_post():
    """POST /natal  — JSON body: {year, month, day, hour, minute, lat, lon}  (UTC)"""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400
    values, err = parse_params(data)
    if err:
        body, status = err
        return jsonify(body), status
    return jsonify(calculate_natal_chart(*values))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    t = threading.Thread(target=_keep_alive, args=(port,), daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=port, debug=False)
