# -*- coding: utf-8 -*-
"""
astro.py — Motor de cálculo astrológico con Swiss Ephemeris (pyswisseph).

Calcula, para una fecha/hora/lugar:
  - Planetas (Sol..Plutón) con efemérides Moshier (sin archivos externos)
  - Nodos lunares (medio) y Luna Negra (apogeo lunar medio = MEAN_APOG)
  - Quirón (usa los archivos seas_*.se1 incluidos en ./ephe)
  - Casas (Placidus), Ascendente y Medio Cielo
  - Parte de la Fortuna (fórmula diurna/nocturna)
  - Aspectos mayores entre planetas

No requiere flatlib. Todo se resuelve con Swiss Ephemeris.
"""
import os
from datetime import datetime

import swisseph as swe

# ── Ruta a los archivos de efemérides (Quirón / asteroides) ─────────────
_EPHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ephe")
if os.path.isdir(_EPHE):
    swe.set_ephe_path(_EPHE)

_MOS = swe.FLG_MOSEPH | swe.FLG_SPEED   # analítico, sin archivos
_SWI = swe.FLG_SWIEPH | swe.FLG_SPEED   # usa archivos .se1 (Quirón)

SIGNS_EN = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
            'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
SIGNS_ES = ['Aries', 'Tauro', 'Géminis', 'Cáncer', 'Leo', 'Virgo', 'Libra',
            'Escorpio', 'Sagitario', 'Capricornio', 'Acuario', 'Piscis']

# (clave, nombre_es, id_swe, flag)
PLANETS = [
    ('aSol', 'Sol', swe.SUN, _MOS),
    ('aLuna', 'Luna', swe.MOON, _MOS),
    ('aMercurio', 'Mercurio', swe.MERCURY, _MOS),
    ('aVenus', 'Venus', swe.VENUS, _MOS),
    ('aMarte', 'Marte', swe.MARS, _MOS),
    ('aJupiter', 'Júpiter', swe.JUPITER, _MOS),
    ('aSaturno', 'Saturno', swe.SATURN, _MOS),
    ('aUrano', 'Urano', swe.URANUS, _MOS),
    ('aNeptuno', 'Neptuno', swe.NEPTUNE, _MOS),
    ('aPluton', 'Plutón', swe.PLUTO, _MOS),
    ('aChiron', 'Quirón', swe.CHIRON, _SWI),
    ('aNoduloNorte', 'Nodo Norte', swe.MEAN_NODE, _MOS),
    ('aLunaNegra', 'Luna Negra', swe.MEAN_APOG, _MOS),
]

ASPECTS = [
    ('Conjunction', 'Conjunción', 0, 8),
    ('Sextile', 'Sextil', 60, 4),
    ('Square', 'Cuadratura', 90, 6),
    ('Trine', 'Trígono', 120, 6),
    ('Opposition', 'Oposición', 180, 8),
]

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']


# ── Helpers ─────────────────────────────────────────────────────────────

def _sign(lon):
    idx = int(lon // 30) % 12
    return idx, SIGNS_EN[idx], SIGNS_ES[idx]


def _dms(lon):
    d = lon % 30
    deg = int(d)
    minute = int(round((d - deg) * 60))
    if minute == 60:
        deg += 1
        minute = 0
    return deg, minute


def _house_of(lon, cusps):
    for i in range(12):
        a = cusps[i]
        b = cusps[(i + 1) % 12]
        if a < b:
            if a <= lon < b:
                return i + 1
        else:
            if lon >= a or lon < b:
                return i + 1
    return 1


def _angle_diff(a, b):
    d = abs(a - b) % 360
    return 360 - d if d > 180 else d


def offset_hours(tz, y, mo, d, hh, mi):
    """Devuelve el offset UTC en horas (con DST) para la fecha dada.
    `tz` puede ser:
      - un nombre IANA, ej. 'America/Santiago'  (se aplica horario de verano)
      - un offset fijo, ej. '-04:00' o '-4'
    """
    tz = (tz or '').strip()
    if not tz:
        return 0.0
    # Offset fijo tipo +HH:MM / -HH:MM / -4
    if tz[0] in '+-' and ':' in tz:
        sign = 1 if tz[0] == '+' else -1
        parts = tz[1:].split(':')
        return sign * (int(parts[0]) + int(parts[1]) / 60.0)
    try:
        return float(tz)
    except ValueError:
        pass
    # Nombre IANA -> offset con DST
    try:
        from zoneinfo import ZoneInfo
        naive = datetime(y, mo, d, hh, mi)
        aware = naive.replace(tzinfo=ZoneInfo(tz))
        off = aware.utcoffset()
        return off.total_seconds() / 3600.0
    except Exception:
        return 0.0


def julian_day(date_str, time_str, tz):
    """date 'YYYY-MM-DD' (o YYYY/MM/DD), time 'HH:MM'. Devuelve el JD en UT."""
    ds = date_str.replace('-', '/').split('/')
    y, mo, d = int(ds[0]), int(ds[1]), int(ds[2])
    tp = (time_str or '12:00').split(':')
    hh = int(tp[0]); mi = int(tp[1]) if len(tp) > 1 else 0
    off = offset_hours(tz, y, mo, d, hh, mi)
    ut = hh + mi / 60.0 - off
    return swe.julday(y, mo, d, ut), off


def _body(key, name, lon, speed, cusps):
    idx, sen, ses = _sign(lon)
    deg, minute = _dms(lon)
    return {
        'key': key,
        'name': name,
        'lon': round(lon, 4),
        'sign': sen,
        'sign_es': ses,
        'sign_index': idx + 1,
        'deg': deg,
        'min': minute,
        'sign_deg': round(lon % 30, 4),
        'house': _house_of(lon, cusps),
        'retrograde': bool(speed < 0),
        'speed': round(speed, 4),
    }


def _aspects(positions):
    keys = list(positions.keys())
    out = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            ka, kb = keys[i], keys[j]
            d = _angle_diff(positions[ka], positions[kb])
            for en, es, ang, orb in ASPECTS:
                if abs(d - ang) <= orb:
                    out.append({
                        'a': ka, 'b': kb,
                        'type': en, 'type_es': es,
                        'angle': ang, 'orb': round(abs(d - ang), 2),
                    })
                    break
    return out


# ── Cálculo principal ───────────────────────────────────────────────────

def compute_chart(date, time, lat, lon, tz, hsys='P'):
    """Calcula una carta. lat/lon en grados decimales (sur/oeste negativos)."""
    # La ruta de efemérides en Swiss Ephemeris es por hilo; FastAPI ejecuta los
    # endpoints sync en un thread pool, así que la fijamos en cada llamada para
    # que Quirón (que usa archivos .se1) siempre se encuentre.
    if os.path.isdir(_EPHE):
        swe.set_ephe_path(_EPHE)
    jd, off = julian_day(date, time, tz)
    cusps, ascmc = swe.houses(jd, float(lat), float(lon), hsys.encode())
    asc, mc = ascmc[0], ascmc[1]
    cusps = list(cusps[:12])

    planets = []
    positions = {}
    for key, name, pid, flag in PLANETS:
        try:
            r = swe.calc_ut(jd, pid, flag)
            p_lon = r[0][0] % 360.0
            speed = r[0][3]
        except Exception:
            continue
        positions[key] = p_lon
        planets.append(_body(key, name, p_lon, speed, cusps))

    # Nodo Sur = Nodo Norte + 180
    if 'aNoduloNorte' in positions:
        sn = (positions['aNoduloNorte'] + 180.0) % 360.0
        positions['aNoduloSur'] = sn
        planets.append(_body('aNoduloSur', 'Nodo Sur', sn, -0.05, cusps))

    # Parte de la Fortuna (diurna/nocturna)
    if 'aSol' in positions and 'aLuna' in positions:
        sun = positions['aSol']; moon = positions['aLuna']
        sun_house = _house_of(sun, cusps)
        is_day = sun_house >= 7  # Sol sobre el horizonte
        pf = (asc + moon - sun) % 360 if is_day else (asc + sun - moon) % 360
        positions['aRuedaFortuna'] = pf
        planets.append(_body('aRuedaFortuna', 'Parte de la Fortuna', pf, 0.0, cusps))

    houses = []
    for i, c in enumerate(cusps):
        idx, sen, ses = _sign(c)
        deg, minute = _dms(c)
        houses.append({
            'num': i + 1, 'roman': ROMAN[i], 'lon': round(c, 4),
            'sign': sen, 'sign_es': ses, 'sign_index': idx + 1,
            'deg': deg, 'min': minute,
        })

    ang = {}
    for nm, val in (('asc', asc), ('mc', mc)):
        idx, sen, ses = _sign(val)
        deg, minute = _dms(val)
        ang[nm] = {'lon': round(val, 4), 'sign': sen, 'sign_es': ses,
                   'deg': deg, 'min': minute}

    return {
        'input': {'date': date, 'time': time, 'lat': float(lat),
                  'lon': float(lon), 'tz': tz, 'utc_offset_hours': round(off, 2),
                  'house_system': 'Placidus'},
        'julian_day_ut': round(jd, 6),
        'angles': ang,
        'houses': houses,
        'planets': planets,
        'aspects': _aspects(positions),
    }


def _cross_aspects(a_pos, b_pos, a_label='transit', b_label='natal'):
    out = []
    for ak, al in a_pos.items():
        for bk, bl in b_pos.items():
            d = _angle_diff(al, bl)
            for en, es, ang, orb in ASPECTS:
                if abs(d - ang) <= orb:
                    out.append({a_label: ak, b_label: bk, 'type': en,
                                'type_es': es, 'angle': ang,
                                'orb': round(abs(d - ang), 2)})
                    break
    return out


def compute_transits(natal, transit):
    """natal/transit = dicts con date,time,lat,lon,tz. Devuelve la carta natal,
    los planetas transitando y los aspectos tránsito→natal."""
    base = compute_chart(**natal)
    trans = compute_chart(**transit)
    natal_pos = {p['key']: p['lon'] for p in base['planets']}
    trans_pos = {p['key']: p['lon'] for p in trans['planets']}
    natal_cusps = [h['lon'] for h in base['houses']]
    # planetas en tránsito ubicados en las casas natales
    for p in trans['planets']:
        p['natal_house'] = _house_of(p['lon'], natal_cusps)
    return {'natal': base, 'transit': trans,
            'cross_aspects': _cross_aspects(trans_pos, natal_pos, 'transit', 'natal')}


# ── Nombre legible por clave (para cartas ensambladas) ──────────────────
_NAME_BY_KEY = {
    'aSol': 'Sol', 'aLuna': 'Luna', 'aMercurio': 'Mercurio', 'aVenus': 'Venus',
    'aMarte': 'Marte', 'aJupiter': 'Júpiter', 'aSaturno': 'Saturno',
    'aUrano': 'Urano', 'aNeptuno': 'Neptuno', 'aPluton': 'Plutón',
    'aChiron': 'Quirón', 'aNoduloNorte': 'Nodo Norte', 'aNoduloSur': 'Nodo Sur',
    'aLunaNegra': 'Luna Negra', 'aRuedaFortuna': 'Parte de la Fortuna',
}
_ORDER = ['aSol', 'aLuna', 'aMercurio', 'aVenus', 'aMarte', 'aJupiter',
          'aSaturno', 'aUrano', 'aNeptuno', 'aPluton', 'aChiron',
          'aNoduloNorte', 'aNoduloSur', 'aLunaNegra', 'aRuedaFortuna']


def _midpoint(a, b):
    d = abs(a - b)
    if d > 180:
        if a > b:
            a -= 360
        else:
            b -= 360
    return (a + b) / 2 % 360


def _assemble(positions, cusps, asc, mc, input_meta):
    """Construye un chart-dict (mismo formato que compute_chart) a partir de
    longitudes de planetas + cúspides + ángulos (para la carta combinada)."""
    planets = []
    for key in _ORDER:
        if key in positions:
            planets.append(_body(key, _NAME_BY_KEY.get(key, key),
                                 positions[key], 0.0, cusps))
    houses = []
    for i, c in enumerate(cusps):
        idx, sen, ses = _sign(c)
        deg, minute = _dms(c)
        houses.append({'num': i + 1, 'roman': ROMAN[i], 'lon': round(c, 4),
                       'sign': sen, 'sign_es': ses, 'sign_index': idx + 1,
                       'deg': deg, 'min': minute})
    ang = {}
    for nm, val in (('asc', asc), ('mc', mc)):
        idx, sen, ses = _sign(val)
        deg, minute = _dms(val)
        ang[nm] = {'lon': round(val, 4), 'sign': sen, 'sign_es': ses,
                   'deg': deg, 'min': minute}
    return {'input': input_meta, 'angles': ang, 'houses': houses,
            'planets': planets, 'aspects': _aspects(positions)}


def compute_solar_return(natal, year, reloc=None):
    """Retorno solar del año `year`. reloc={'lat','lon','tz'} para relocalizar."""
    import swisseph as swe
    base = compute_chart(**natal)
    natal_sun = next(p['lon'] for p in base['planets'] if p['key'] == 'aSol')
    ds = natal['date'].replace('-', '/').split('/')
    bmonth, bday = int(ds[1]), int(ds[2])
    jd = swe.julday(int(year), bmonth, bday, 12.0)
    for _ in range(12):
        lon = swe.calc_ut(jd, swe.SUN, _MOS)[0][0]
        diff = ((natal_sun - lon + 180) % 360) - 180
        if abs(diff) < 1e-7:
            break
        jd += diff / 0.9856
    y, m, d, hd = swe.revjul(jd)
    hh = int(hd); mm = int(round((hd - hh) * 60))
    if mm == 60:
        hh += 1; mm = 0
    sr_date = '%04d/%02d/%02d' % (y, m, d)
    sr_time = '%02d:%02d' % (hh, mm)
    lat = (reloc or {}).get('lat', natal['lat'])
    lon_ = (reloc or {}).get('lon', natal['lon'])
    sr = compute_chart(sr_date, sr_time, lat, lon_, '+00:00', natal.get('hsys', 'P'))
    sr['input']['label'] = 'Retorno solar %s (UT)' % year
    return {'natal': base, 'solar_return': sr, 'year': int(year)}


def compute_progressed(natal, target_date):
    """Progresión secundaria: 1 día tras el nacimiento = 1 año de vida."""
    from datetime import datetime, timedelta
    base = compute_chart(**natal)
    nd = datetime.strptime(natal['date'].replace('-', '/'), '%Y/%m/%d')
    td = datetime.strptime(target_date.replace('-', '/'), '%Y/%m/%d')
    years = (td - nd).days / 365.25
    prog_dt = nd + timedelta(days=years)
    prog_date = prog_dt.strftime('%Y/%m/%d')
    prog = compute_chart(prog_date, natal['time'], natal['lat'], natal['lon'],
                         natal['tz'], natal.get('hsys', 'P'))
    prog['input']['label'] = 'Progresada a %s' % target_date
    return {'natal': base, 'progressed': prog, 'years': round(years, 1)}


def compute_combined(person_a, person_b):
    """Carta combinada (composite de puntos medios) entre dos personas."""
    ca = compute_chart(**person_a)
    cb = compute_chart(**person_b)
    pa = {p['key']: p['lon'] for p in ca['planets']}
    pb = {p['key']: p['lon'] for p in cb['planets']}
    positions = {}
    for key in _ORDER:
        if key in pa and key in pb:
            positions[key] = _midpoint(pa[key], pb[key])
    ha = {h['num']: h['lon'] for h in ca['houses']}
    hb = {h['num']: h['lon'] for h in cb['houses']}
    cusps = [_midpoint(ha[i + 1], hb[i + 1]) for i in range(12)]
    asc = _midpoint(ca['angles']['asc']['lon'], cb['angles']['asc']['lon'])
    mc = _midpoint(ca['angles']['mc']['lon'], cb['angles']['mc']['lon'])
    comb = _assemble(positions, cusps, asc, mc,
                     {'label': 'Carta combinada', 'house_system': 'Composite (puntos medios)'})
    return {'a': ca, 'b': cb, 'combined': comb}
