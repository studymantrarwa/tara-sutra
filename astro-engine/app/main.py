from fastapi import FastAPI, HTTPException, Body
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import swisseph as swe

app = FastAPI(
    title="Tara Sutra Astrology Engine",
    version="1.2.0"
)

# ---------------------------------------------------------
# SWISS EPHEMERIS
# ---------------------------------------------------------

swe.set_sid_mode(swe.SIDM_LAHIRI)

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

RASHIS = [
    "Mesha",
    "Vrishabha",
    "Mithuna",
    "Karka",
    "Simha",
    "Kanya",
    "Tula",
    "Vrishchika",
    "Dhanu",
    "Makara",
    "Kumbha",
    "Meena",
]

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

# ---------------------------------------------------------
# VIMSHOTTARI DASHA
# ---------------------------------------------------------

DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

DASHA_SEQUENCE = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

TOTAL_DASHA_YEARS = 120.0
DAYS_PER_DASHA_YEAR = 365.25


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
# DATE HELPERS
# ---------------------------------------------------------

def safe_date(value):
    return value.isoformat()


def add_dasha_years(date_value, years):
    return date_value + timedelta(
        days=years * DAYS_PER_DASHA_YEAR
    )


# ---------------------------------------------------------
# NAKSHATRA
# ---------------------------------------------------------

def nakshatra(longitude):
    longitude = longitude % 360.0

    span = 360.0 / 27.0

    index = int(longitude / span)

    if index >= 27:
        index = 26

    inside = longitude - (index * span)

    pada = int(
        inside / (span / 4.0)
    ) + 1

    if pada > 4:
        pada = 4

    return NAKSHATRAS[index], pada


# ---------------------------------------------------------
# RASHI
# ---------------------------------------------------------

def rashi_info(longitude):
    longitude = longitude % 360.0

    rashi_index = int(
        longitude // 30.0
    )

    degree = longitude % 30.0

    return {
        "number": rashi_index + 1,
        "name": RASHIS[rashi_index],
        "degree": round(degree, 6),
    }


# ---------------------------------------------------------
# NAVAMSA / D9
# ---------------------------------------------------------

def navamsa_sign(longitude):
    longitude = longitude % 360.0

    rashi_index = int(
        longitude // 30.0
    )

    degree_in_sign = longitude % 30.0

    navamsa_part = int(
        degree_in_sign / (30.0 / 9.0)
    )

    if navamsa_part > 8:
        navamsa_part = 8

    # Movable signs:
    # Mesha, Karka, Tula, Makara
    if rashi_index in [0, 3, 6, 9]:
        start = rashi_index

    # Fixed signs:
    # Vrishabha, Simha, Vrishchika, Kumbha
    elif rashi_index in [1, 4, 7, 10]:
        start = (rashi_index + 8) % 12

    # Dual signs:
    # Mithuna, Kanya, Dhanu, Meena
    else:
        start = (rashi_index + 4) % 12

    d9_index = (
        start + navamsa_part
    ) % 12

    navamsa_degree = (
        degree_in_sign % (30.0 / 9.0)
    ) * 9.0

    return {
        "rashi": d9_index + 1,
        "rashiName": RASHIS[d9_index],
        "navamsaPart": navamsa_part + 1,
        "degree": round(
            navamsa_degree,
            6
        ),
    }


# ---------------------------------------------------------
# PLANET DATA
# ---------------------------------------------------------

def make_planet_data(
    longitude,
    retrograde=False
):
    longitude = longitude % 360.0

    rashi = rashi_info(
        longitude
    )

    nak_name, pada = nakshatra(
        longitude
    )

    d9 = navamsa_sign(
        longitude
    )

    return {
        "longitude": round(
            longitude,
            6
        ),
        "degree": rashi["degree"],
        "rashi": rashi["number"],
        "rashiName": rashi["name"],
        "nakshatra": nak_name,
        "pada": pada,
        "retrograde": bool(
            retrograde
        ),
        "d9": d9,
    }


# ---------------------------------------------------------
# DASHA HELPERS
# ---------------------------------------------------------

def next_dasha_lord(lord):
    index = DASHA_SEQUENCE.index(
        lord
    )

    return DASHA_SEQUENCE[
        (index + 1) % len(DASHA_SEQUENCE)
    ]


def calculate_antardashas(
    mahadasha_lord,
    start_date,
    mahadasha_years
):
    result = []

    current_date = start_date

    lord = mahadasha_lord

    for _ in range(9):

        ad_years = (
            mahadasha_years
            * DASHA_YEARS[lord]
            / TOTAL_DASHA_YEARS
        )

        end_date = add_dasha_years(
            current_date,
            ad_years
        )

        result.append({
            "lord": lord,
            "start": safe_date(
                current_date
            ),
            "end": safe_date(
                end_date
            ),
            "years": round(
                ad_years,
                8
            ),
            "pratyantardasha": [],
        })

        current_date = end_date

        lord = next_dasha_lord(
            lord
        )

    return result


def calculate_pratyantardashas(
    antardasha_lord,
    antardasha_start,
    antardasha_end
):
    result = []

    total_seconds = (
        antardasha_end
        - antardasha_start
    ).total_seconds()

    current_date = antardasha_start

    lord = antardasha_lord

    for _ in range(9):

        fraction = (
            DASHA_YEARS[lord]
            / TOTAL_DASHA_YEARS
        )

        duration_seconds = (
            total_seconds
            * fraction
        )

        end_date = (
            current_date
            + timedelta(
                seconds=duration_seconds
            )
        )

        result.append({
            "lord": lord,
            "start": safe_date(
                current_date
            ),
            "end": safe_date(
                end_date
            ),
        })

        current_date = end_date

        lord = next_dasha_lord(
            lord
        )

    if result:
        result[-1]["end"] = safe_date(
            antardasha_end
        )

    return result


# ---------------------------------------------------------
# VIMSHOTTARI DASHA
# ---------------------------------------------------------

def calculate_vimshottari(
    birth_date,
    moon_longitude
):
    moon_longitude = (
        moon_longitude % 360.0
    )

    nak_span = (
        360.0 / 27.0
    )

    nak_index = int(
        moon_longitude
        / nak_span
    )

    if nak_index >= 27:
        nak_index = 26

    starting_lord = (
        DASHA_SEQUENCE[
            nak_index % 9
        ]
    )

    position_in_nak = (
        moon_longitude
        - (
            nak_index
            * nak_span
        )
    )

    fraction_elapsed = (
        position_in_nak
        / nak_span
    )

    fraction_remaining = (
        1.0
        - fraction_elapsed
    )

    balance_years = (
        DASHA_YEARS[
            starting_lord
        ]
        * fraction_remaining
    )

    mahadashas = []

    current_date = birth_date

    lord = starting_lord

    first = True

    for _ in range(9):

        if first:
            md_years = balance_years
            first = False
        else:
            md_years = DASHA_YEARS[
                lord
            ]

        end_date = add_dasha_years(
            current_date,
            md_years
        )

        antardashas = (
            calculate_antardashas(
                lord,
                current_date,
                md_years
            )
        )

        for ad in antardashas:

            ad_start = (
                datetime.fromisoformat(
                    ad["start"]
                )
            )

            ad_end = (
                datetime.fromisoformat(
                    ad["end"]
                )
            )

            ad["pratyantardasha"] = (
                calculate_pratyantardashas(
                    ad["lord"],
                    ad_start,
                    ad_end
                )
            )

        mahadashas.append({
            "lord": lord,
            "start": safe_date(
                current_date
            ),
            "end": safe_date(
                end_date
            ),
            "years": round(
                md_years,
                8
            ),
            "antardasha": antardashas,
        })

        current_date = end_date

        lord = next_dasha_lord(
            lord
        )

    return {
        "startingLord": starting_lord,
        "birthNakshatra": NAKSHATRAS[
            nak_index
        ],
        "nakshatraNumber": (
            nak_index + 1
        ),
        "elapsedFraction": round(
            fraction_elapsed,
            8
        ),
        "remainingFraction": round(
            fraction_remaining,
            8
        ),
        "balanceYears": round(
            balance_years,
            8
        ),
        "mahadasha": mahadashas,
    }


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "ok": True,
        "engine": "Swiss Ephemeris",
        "ayanamsa": "Lahiri",
        "mode": "Sidereal",
        "version": "1.2.0",
    }


# ---------------------------------------------------------
# CALCULATE
# ---------------------------------------------------------

@app.post("/calculate")
def calculate(
    body: dict = Body(
        ...,
        example={
            "name": "Test User",
            "gender": "male",
            "dob": "1995-05-15",
            "time": "10:30",
            "placeId": "varanasi",
            "placeLabel": "Varanasi, Uttar Pradesh, India",
            "latitude": 25.3176,
            "longitude": 82.9739,
            "timezone": "Asia/Kolkata",
        },
    )
):

    # -----------------------------------------------------
    # CHECK BODY
    # -----------------------------------------------------

    if not isinstance(body, dict):
        raise HTTPException(
            status_code=400,
            detail=(
                "Request body must be "
                "a JSON object."
            ),
        )

    data = body

    # -----------------------------------------------------
    # VALIDATE INPUT
    # -----------------------------------------------------

    try:

        name = required_string(
            data,
            "name"
        )

        gender = required_string(
            data,
            "gender"
        )

        dob = required_string(
            data,
            "dob"
        )

        birth_time = required_string(
            data,
            "time"
        )

        place_id = required_string(
            data,
            "placeId"
        )

        place_label = required_string(
            data,
            "placeLabel"
        )

        timezone_name = required_string(
            data,
            "timezone"
        )

        latitude = required_number(
            data,
            "latitude"
        )

        longitude = required_number(
            data,
            "longitude"
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # -----------------------------------------------------
    # COORDINATE VALIDATION
    # -----------------------------------------------------

    if latitude < -90 or latitude > 90:

        raise HTTPException(
            status_code=400,
            detail=(
                "latitude must be "
                "between -90 and 90."
            ),
        )

    if longitude < -180 or longitude > 180:

        raise HTTPException(
            status_code=400,
            detail=(
                "longitude must be "
                "between -180 and 180."
            ),
        )

    # -----------------------------------------------------
    # TIMEZONE VALIDATION
    # -----------------------------------------------------

    try:

        timezone = ZoneInfo(
            timezone_name
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid IANA timezone: "
                f"{timezone_name}"
            ),
        )

    # -----------------------------------------------------
    # DATE/TIME VALIDATION
    # -----------------------------------------------------

    try:

        local_datetime = (
            datetime.fromisoformat(
                f"{dob}T{birth_time}"
            )
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid date/time. "
                "Use dob as YYYY-MM-DD "
                "and time as HH:MM."
            ),
        )

    # Attach IANA timezone

    local_datetime = (
        local_datetime.replace(
            tzinfo=timezone
        )
    )

    # -----------------------------------------------------
    # UTC CONVERSION
    # -----------------------------------------------------

    utc_datetime = (
        local_datetime.astimezone(
            ZoneInfo("UTC")
        )
    )

    hour = (
        utc_datetime.hour
        + utc_datetime.minute / 60.0
        + utc_datetime.second / 3600.0
        + utc_datetime.microsecond
        / 3600000000.0
    )

    # -----------------------------------------------------
    # JULIAN DAY
    # -----------------------------------------------------

    jd = swe.julday(
        utc_datetime.year,
        utc_datetime.month,
        utc_datetime.day,
        hour
    )

    # -----------------------------------------------------
    # LAHIRI AYANAMSA
    # -----------------------------------------------------

    swe.set_sid_mode(
        swe.SIDM_LAHIRI
    )

    ayanamsa = (
        swe.get_ayanamsa_ut(jd)
    )

    # -----------------------------------------------------
    # PLANETS
    # -----------------------------------------------------

    planets = {}

    calculation_flags = (
        swe.FLG_SWIEPH
        | swe.FLG_SIDEREAL
        | swe.FLG_SPEED
    )

    for planet_name, planet_id in PLANETS.items():

        try:

            xx, flags = swe.calc_ut(
                jd,
                planet_id,
                calculation_flags
            )

        except Exception as e:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unable to calculate "
                    f"{planet_name}: {str(e)}"
                ),
            )

        longitude_value = (
            xx[0] % 360.0
        )

        planets[planet_name] = (
            make_planet_data(
                longitude_value,
                xx[3] < 0
            )
        )

    # -----------------------------------------------------
    # KETU
    # -----------------------------------------------------

    rahu_longitude = (
        planets["Rahu"]["longitude"]
    )

    ketu_longitude = (
        rahu_longitude
        + 180.0
    ) % 360.0

    planets["Ketu"] = (
        make_planet_data(
            ketu_longitude,
            True
        )
    )

    # -----------------------------------------------------
    # LAGNA / ASCENDANT
    # -----------------------------------------------------

    try:

        cusps, ascmc = (
            swe.houses_ex(
                jd,
                latitude,
                longitude,
                b"P",
                swe.FLG_SIDEREAL
            )
        )

        ascendant_longitude = (
            ascmc[0] % 360.0
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to calculate "
                f"Lagna: {str(e)}"
            ),
        )

    # -----------------------------------------------------
    # LAGNA DATA
    # -----------------------------------------------------

    lagna_rashi = rashi_info(
        ascendant_longitude
    )

    lagna_nakshatra, lagna_pada = (
        nakshatra(
            ascendant_longitude
        )
    )

    lagna_d9 = navamsa_sign(
        ascendant_longitude
    )

    # -----------------------------------------------------
    # MOON NAKSHATRA
    # -----------------------------------------------------

    moon_longitude = (
        planets["Moon"]["longitude"]
    )

    moon_nak_name = (
        planets["Moon"]["nakshatra"]
    )

    moon_nak_pada = (
        planets["Moon"]["pada"]
    )

    # -----------------------------------------------------
    # DASHA
    # -----------------------------------------------------

    dasha = (
        calculate_vimshottari(
            local_datetime.replace(
                tzinfo=None
            ),
            moon_longitude
        )
    )

    # -----------------------------------------------------
    # D1 HOUSE CUSPS
    # -----------------------------------------------------

    d1_houses = [
        round(
            float(value),
            6
        )
        for value in cusps
    ]

    # -----------------------------------------------------
    # D9 PLANETS
    # -----------------------------------------------------

    d9_planets = {}

    for planet_name, planet_data in planets.items():

        d9_planets[planet_name] = (
            planet_data["d9"]
        )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "success": True,

        "engine": {
            "name": "Swiss Ephemeris",
            "ayanamsa": "Lahiri",
            "mode": "Sidereal",
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

            "localTime": (
                local_datetime.isoformat()
            ),

            "utc": (
                utc_datetime.isoformat()
            ),
        },

        "ayanamsa": round(
            ayanamsa,
            6
        ),

        "lagna": {

            "longitude": round(
                ascendant_longitude,
                6
            ),

            "degree": (
                lagna_rashi["degree"]
            ),

            "rashi": (
                lagna_rashi["number"]
            ),

            "rashiName": (
                lagna_rashi["name"]
            ),

            "nakshatra": (
                lagna_nakshatra
            ),

            "pada": lagna_pada,

            "d9": lagna_d9,
        },

        "planets": planets,

        "moon_nakshatra": {

            "name": moon_nak_name,

            "pada": moon_nak_pada,
        },

        "dasha": dasha,

        "d1": {

            "type": "Rashi",

            "system": (
                "Sidereal Lahiri"
            ),

            "houses": d1_houses,
        },

        "d9": {

            "type": "Navamsa",

            "system": (
                "Vedic Navamsa"
            ),

            "lagna": lagna_d9,

            "planets": d9_planets,
        },
    }


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():

    return {

        "name": (
            "Tara Sutra Astrology Engine"
        ),

        "status": "online",

        "engine": "Swiss Ephemeris",

        "ayanamsa": "Lahiri",

        "mode": "Sidereal",

        "version": "1.2.0",

        "docs": "/docs",
    }
