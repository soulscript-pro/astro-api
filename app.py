import os
import traceback
import swisseph as swe
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

EPHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ephe")

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "Chiron": swe.CHIRON,
    "NorthNode": swe.MEAN_NODE,
}

ASTEROID_PACKS = {
    "relationnel": [
        {"key": "adonis", "name": "Adonis", "id": 2101},
        {"key": "aphrodite", "name": "Aphrodite", "id": 1388},
        {"key": "eros", "name": "Éros", "id": 433},
        {"key": "junon", "name": "Junon", "id": 3},
        {"key": "psyche", "name": "Psyché", "id": 16},
    ],
    "karma": [
        {"key": "karma", "name": "Karma", "id": 3811},
        {"key": "moira", "name": "Moira", "id": 638},
        {"key": "klotho", "name": "Klotho", "id": 97},
        {"key": "lachesis", "name": "Lachesis", "id": 120},
        {"key": "atropos", "name": "Atropos", "id": 273},
    ],
    "ombre": [
        {"key": "nessus", "name": "Nessus", "id": 7066},
        {"key": "dejanire", "name": "Déjanire", "id": 157},
        {"key": "phedre", "name": "Phèdre", "id": 174},
        {"key": "lust", "name": "Lust", "id": 4386},
    ],
    "mission": [
        {"key": "vesta", "name": "Vesta", "id": 4},
        {"key": "pallas", "name": "Pallas", "id": 2},
        {"key": "fama", "name": "Fama", "id": 408},
        {"key": "apollo", "name": "Apollo", "id": 1862},
        {"key": "destinn", "name": "Destinn", "id": 6583},
    ],
    "sante": [
        {"key": "hygie", "name": "Hygie", "id": 10},
        {"key": "panacea", "name": "Panacea", "id": 2878},
        {"key": "asclepius", "name": "Asclepius", "id": 4581},
        {"key": "aesculapia", "name": "Aesculapia", "id": 1027},
        {"key": "chariklo", "name": "Chariklo", "id": 10199},
    ],
}


def lon_to_dms(lon):
    sign_idx = int(lon / 30) % 12
    deg_in_sign = lon % 30
    degree = int(deg_in_sign)
    minute = int((deg_in_sign - degree) * 60)
    return {
        "longitude": round(lon, 6),
        "sign": SIGNS[sign_idx],
        "degree": degree,
        "minute": minute,
    }


def whole_sign_house(body_lon, asc_lon):
    asc_sign = int(asc_lon / 30) % 12
    body_sign = int(body_lon / 30) % 12
    return (body_sign - asc_sign) % 12 + 1


def parse_params(data):
    required = ["year", "month", "day", "hour", "minute", "lat", "lon"]
    missing = [f for f in required if f not in data]

    if missing:
        return None, ({"error": f"Missing required fields: {', '.join(missing)}"}, 400)

    try:
        values = (
            int(data["year"]),
            int(data["month"]),
            int(data["day"]),
            int(data["hour"]),
            int(data["minute"]),
            float(data["lat"]),
            float(data["lon"]),
        )
        return values, None
    except Exception as exc:
        return None, ({"error": str(exc)}, 400)


def calculate_natal_chart(year, month, day, hour, minute, lat, lon):
    swe.set_ephe_path(EPHE_PATH)

    jd = swe.julday(year, month, day, hour + minute / 60.0)
    _, ascmc = swe.houses(jd, lat, lon, b"W")

    asc_lon = ascmc[0]
    mc_lon = ascmc[1]

    result = {
        "ascendant": {**lon_to_dms(asc_lon), "house": 1},
        "mc": {**lon_to_dms(mc_lon), "house": whole_sign_house(mc_lon, asc_lon)},
        "planets": {},
    }

    for name, planet_id in PLANETS.items():
        try:
            pos, _ = swe.calc_ut(jd, planet_id)
            body_lon = pos[0]
            speed = pos[3]
            result["planets"][name] = {
                **lon_to_dms(body_lon),
                "house": whole_sign_house(body_lon, asc_lon),
                "retrograde": speed < 0,
            }
        except Exception as exc:
            result["planets"][name] = {"error": str(exc)}

    return result


@app.errorhandler(Exception)
def handle_exception(exc):
    traceback.print_exc()
    return jsonify({"error": str(exc)}), 500


@app.route("/")
def root():
    return jsonify({"status": "SOULSCRIPT astro-api online"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/test")
def test():
    return jsonify(calculate_natal_chart(1984, 2, 27, 7, 30, 47.7508, 7.3359))


@app.route("/natal", methods=["GET", "POST"])
def natal():
    data = request.args if request.method == "GET" else request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    values, err = parse_params(data)
    if err:
        body, status = err
        return jsonify(body), status

    return jsonify(calculate_natal_chart(*values))


@app.route("/asteroids", methods=["POST"])
def asteroids():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    packs_requested = data.get("packs", [])

    if not packs_requested:
        return jsonify({"error": "Missing 'packs' field"}), 400

    values, err = parse_params(data)
    if err:
        body, status = err
        return jsonify(body), status

    year, month, day, hour, minute, lat, lon = values

    swe.set_ephe_path(EPHE_PATH)

    jd = swe.julday(year, month, day, hour + minute / 60.0)
    _, ascmc = swe.houses(jd, lat, lon, b"W")
    asc_lon = ascmc[0]

    result = {}

    for pack_name in packs_requested:
        pack_key = pack_name.lower()

        if pack_key not in ASTEROID_PACKS:
            result[pack_key] = {"error": f"Pack inconnu: {pack_name}"}
            continue

        pack_result = {}

        for asteroid in ASTEROID_PACKS[pack_key]:
            try:
                pos, _ = swe.calc_ut(jd, swe.AST_OFFSET + asteroid["id"])
                body_lon = pos[0]

                pack_result[asteroid["key"]] = {
                    "id": asteroid["id"],
                    "name": asteroid["name"],
                    **lon_to_dms(body_lon),
                    "house": whole_sign_house(body_lon, asc_lon),
                }

            except Exception as exc:
                pack_result[asteroid["key"]] = {
                    "id": asteroid["id"],
                    "name": asteroid["name"],
                    "error": str(exc),
                }

        result[pack_key] = pack_result

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
