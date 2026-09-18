from fastapi import FastAPI, HTTPException, Request
from datetime import datetime
from zoneinfo import ZoneInfo
import swisseph as swe

app = FastAPI(
    title="Tara Sutra Astrology Engine",
    version="1.0.0"
)

# Lahiri / Sidereal
swe.set_sid_mode(swe.SIDM_LAHIRI)


# ---------------------------------------------------------
# PLANETS
# ---------------------------------------------------------

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}


# ---------------------------------------------------------
# NAKSHATRA
# ---------------------------------------------------------

NAKSHATRAS = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]


def nakshatra(longitude: float):
    longitude = longitude % 360

    span = 360.0 / 27.0

    index = int(longitude / span)

    if index >= 27:
        index = 26

    inside = longitude - (index * span)

    pada = int(inside / (span / 4.0)) + 1

    if pada > 4:
        pada = 4

    return NAKSHATRAS[index], pada


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "ok": True,
        "engine": "Swiss Ephemeris",
        "ayanamsa": "Lahiri",
        "version": "1.0.0"
    }


# ---------------------------------------------------------
# VALIDATION HELPERS
# ---------------------------------------------------------

def required_string(data, field):
    value = data.get(field)

    if value is None:
        raise ValueError(f"Missing required field: {field}")

    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")

    value = value.strip()

    if not value:
        raise ValueError(f"{field} cannot be empty")

    return value


def required_number(data, field):
    value = data.get(field)

    if value is None:
        raise ValueError(f"Missing required field: {field}")

    try:
        return float(value)
    except Exception:
        raise ValueError(f"{field} must be a number")


# ---------------------------------------------------------
# CALCULATE
# ---------------------------------------------------------

@app.post("/calculate")
async def calculate(request: Request):

    # ---------------------------------------------
    # READ JSON
    # ---------------------------------------------

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Request body must contain valid JSON."
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail="Request body must be a JSON object."
        )

    # ---------------------------------------------
    # READ REQUIRED FIELDS
    # ---------------------------------------------

    try:
        name = required_string(data, "name")
        gender = required_string(data, "gender")
        dob = required_string(data, "dob")
        birth_time = required_string(data, "time")
        place_id = required_string(data, "placeId")
        place_label = required_string(data, "placeLabel")
        timezone_name = required_string(data, "timezone")

        latitude = required_number(data, "latitude")
        longitude = required_number(data, "longitude")

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # ---------------------------------------------
    # COORDINATE VALIDATION
    # ---------------------------------------------

    if latitude < -90 or latitude > 90:
        raise HTTPException(
            status_code=400,
            detail="latitude must be between -90 and 90."
        )

    if longitude < -180 or longitude > 180:
        raise HTTPException(
            status_code=400,
            detail="longitude must be between -180 and 180."
        )

    # ---------------------------------------------
    # TIMEZONE
    # ---------------------------------------------

    try:
        timezone = ZoneInfo(timezone_name)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid IANA timezone: {timezone_name}"
        )

    # ---------------------------------------------
    # DATE + TIME
    # ---------------------------------------------

    try:
        local_datetime = datetime.fromisoformat(
            f"{dob}T{birth_time}"
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid date/time. "
                "Use dob as YYYY-MM-DD and time as HH:MM."
            )
        )

    local_datetime = local_datetime.replace(tzinfo=timezone)

    # ---------------------------------------------
    # UTC
    # ---------------------------------------------

    utc_datetime = local_datetime.astimezone(ZoneInfo("UTC"))

    hour = (
        utc_datetime.hour
        + utc_datetime.minute / 60.0
        + utc_datetime.second / 3600.0
        + utc_datetime.microsecond / 3600000000.0
    )

    # ---------------------------------------------
    # JULIAN DAY
    # ---------------------------------------------

    jd = swe.julday(
        utc_datetime.year,
        utc_datetime.month,
        utc_datetime.day,
        hour
    )

    # ---------------------------------------------
    # LAHIRI AYANAMSA
    # ---------------------------------------------

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    ayanamsa = swe.get_ayanamsa_ut(jd)

    # ---------------------------------------------
    # PLANETS
    # ---------------------------------------------

    planets = {}

    calculation_flags = (
        swe.FLG_SWIEPH
        | swe.FLG_SIDEREAL
        | swe.FLG_SPEED
    )

    for planet_name, planet_id in PLANETS.items():

        xx, flags = swe.calc_ut(
            jd,
            planet_id,
            calculation_flags
        )

        longitude_value = xx[0] % 360.0

        rashi = int(longitude_value // 30.0) + 1

        degree = longitude_value % 30.0

        nak_name, pada = nakshatra(longitude_value)

        planets[planet_name] = {
            "longitude": round(longitude_value, 6),
            "degree": round(degree, 6),
            "rashi": rashi,
            "nakshatra": nak_name,
            "pada": pada,
            "retrograde": bool(xx[3] < 0)
        }

    # ---------------------------------------------
    # KETU
    # ---------------------------------------------

    rahu_longitude = planets["Rahu"]["longitude"]

    ketu_longitude = (rahu_longitude + 180.0) % 360.0

    ketu_nakshatra, ketu_pada = nakshatra(ketu_longitude)

    planets["Ketu"] = {
        "longitude": round(ketu_longitude, 6),
        "degree": round(ketu_longitude % 30.0, 6),
        "rashi": int(ketu_longitude // 30.0) + 1,
        "nakshatra": ketu_nakshatra,
        "pada": ketu_pada,
        "retrograde": True
    }

    # ---------------------------------------------
    # ASCENDANT / LAGNA
    # ---------------------------------------------

    try:
        cusps, ascmc = swe.houses_ex(
            jd,
            latitude,
            longitude,
            b"P",
            swe.FLG_SIDEREAL
        )

        ascendant_longitude = ascmc[0] % 360.0

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to calculate Lagna: {str(e)}"
        )

    lagna_rashi = int(ascendant_longitude // 30.0) + 1

    lagna_degree = ascendant_longitude % 30.0

    lagna_nakshatra, lagna_pada = nakshatra(
        ascendant_longitude
    )

    # ---------------------------------------------
    # RESPONSE
    # ---------------------------------------------

    return {
        "success": True,

        "engine": {
            "name": "Swiss Ephemeris",
            "ayanamsa": "Lahiri",
            "mode": "Sidereal"
        },

        "birth": {
            "name": name,
            "gender": gender,
            "dob": dob,
            "time": birth_time,
            "placeId": place_id,
            "place": place_label,
            "timezone": timezone_name,
            "latitude": latitude,
            "longitude": longitude,
            "localTime": local_datetime.isoformat(),
            "utc": utc_datetime.isoformat()
        },

        "ayanamsa": round(ayanamsa, 6),

        "lagna": {
            "longitude": round(ascendant_longitude, 6),
            "degree": round(lagna_degree, 6),
            "rashi": lagna_rashi,
            "nakshatra": lagna_nakshatra,
            "pada": lagna_pada
        },

        "planets": planets,

        "moon_nakshatra": {
            "name": planets["Moon"]["nakshatra"],
            "pada": planets["Moon"]["pada"]
        },

        "dasha": [],

        "d1": {
            "houses": [
                round(float(x), 6)
                for x in cusps
            ]
        },

        "d9": {
            "status": "calculation module pending"
        }
    }


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "name": "Tara Sutra Astrology Engine",
        "status": "online",
        "engine": "Swiss Ephemeris",
        "docs": "/docs"
    }
