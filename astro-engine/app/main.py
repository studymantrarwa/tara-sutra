from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import swisseph as swe

app=FastAPI(title="Tara Sutra Astrology Engine")
swe.set_sid_mode(swe.SIDM_LAHIRI)

class Birth(BaseModel):
    name:str
    gender:str
    dob:str
    time:str
    placeId:str
    placeLabel:str
    latitude:float
    longitude:float
    timezone:str

PLANETS={"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN,"Rahu":swe.MEAN_NODE}

def nakshatra(lon:float):
    names=["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"]
    span=360/27
    idx=int(lon/span)
    pada=int((lon-idx*span)/(span/4))+1
    return names[idx],pada

@app.get("/health")
def health(): return {"ok":True,"engine":"Swiss Ephemeris","ayanamsa":"Lahiri"}

@app.post("/calculate")
def calculate(b:Birth):
    try:
        local=datetime.fromisoformat(f"{b.dob}T{b.time}").replace(tzinfo=ZoneInfo(b.timezone))
        utc=local.astimezone(ZoneInfo("UTC"))
        hour=utc.hour+utc.minute/60+utc.second/3600
        jd=swe.julday(utc.year,utc.month,utc.day,hour)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        ay=swe.get_ayanamsa_ut(jd)
        planets={}
        for name,pid in PLANETS.items():
            xx,flags=swe.calc_ut(jd,pid,swe.FLG_SWIEPH|swe.FLG_SIDEREAL|swe.FLG_SPEED)
            lon=xx[0]%360
            rashi=int(lon//30)+1
            nak,pad=nakshatra(lon)
            planets[name]={"longitude":round(lon,6),"degree":round(lon%30,6),"rashi":rashi,"nakshatra":nak,"pada":pad,"retrograde":bool(xx[3]<0)}
        rahu=planets["Rahu"]["longitude"]
        ketu=(rahu+180)%360
        kn,kp=nakshatra(ketu)
        planets["Ketu"]={"longitude":round(ketu,6),"degree":round(ketu%30,6),"rashi":int(ketu//30)+1,"nakshatra":kn,"pada":kp,"retrograde":True}
        cusps,asc=swe.houses_ex(jd,b.latitude,b.longitude,b'P',swe.FLG_SIDEREAL)
        asc_lon=asc[0]%360
        an,ap=nakshatra(asc_lon)
        return {"birth":{"name":b.name,"gender":b.gender,"dob":b.dob,"time":b.time,"place":b.placeLabel,"timezone":b.timezone,"latitude":b.latitude,"longitude":b.longitude,"utc":utc.isoformat()},"ayanamsa":round(ay,6),"lagna":{"longitude":round(asc_lon,6),"degree":round(asc_lon%30,6),"rashi":int(asc_lon//30)+1,"nakshatra":an,"pada":ap},"planets":planets,"moon_nakshatra":{"name":planets["Moon"]["nakshatra"],"pada":planets["Moon"]["pada"]},"dasha":[],"d1":{"houses":list(cusps)},"d9":{"status":"calculation module to be completed"}}
    except Exception as e:
        raise HTTPException(status_code=400,detail="Invalid birth data or calculation input.")
