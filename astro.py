# -*- coding: utf-8 -*-
"""
astro.py — Motor de cálculo astrológico con Swiss Ephemeris (pyswisseph).

Calcula, para una fecha/hora/lugar:
  - Planetas (Sol..Plutón) con efemérides Moshier (sin archivos externos)
  - Nodos lunares (verdaderos = TRUE_NODE) y Luna Negra (apogeo verdadero = OSCU_APOG)
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
    ('aNoduloNorte', 'Nodo Norte', swe.TRUE_NODE, _MOS),
    ('aLunaNegra', 'Luna Negra', swe.OSCU_APOG, _MOS),
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

    # Momento exacto del retorno en hora local del lugar (relocalizado o natal).
    from datetime import datetime as _dt, timedelta as _td
    disp_tz = (reloc or {}).get('tz') or natal.get('tz') or '+00:00'
    off = offset_hours(disp_tz, int(y), int(m), int(d), hh, mm)
    ut_dt = _dt(int(y), int(m), int(d), hh, mm)
    loc_dt = ut_dt + _td(hours=off)
    sr['input']['return_ut'] = '%04d-%02d-%02d %02d:%02d' % (y, m, d, hh, mm)
    sr['input']['return_local'] = loc_dt.strftime('%Y-%m-%d %H:%M')
    sr['input']['return_tz'] = disp_tz
    sr['input']['relocated'] = bool(reloc)
    sr['input']['lat'] = float(lat)
    sr['input']['lon'] = float(lon_)
    return {'natal': base, 'solar_return': sr, 'year': int(year)}


def compute_progressed(natal, target_date, reloc=None):
    """Progresión secundaria: 1 día tras el nacimiento = 1 año de vida.
    reloc={'lat','lon','tz'} para relocalizar (mismo instante, casas del lugar)."""
    from datetime import datetime, timedelta
    base = compute_chart(**natal)
    nd = datetime.strptime(natal['date'].replace('-', '/'), '%Y/%m/%d')
    td = datetime.strptime(target_date.replace('-', '/'), '%Y/%m/%d')
    years = (td - nd).days / 365.25
    prog_dt = nd + timedelta(days=years)
    prog_date = prog_dt.strftime('%Y/%m/%d')
    # Relocalización: mismo momento (hora y tz natales) pero lat/lon del lugar
    # elegido → los planetas no cambian, sí las casas, el Asc y el MC.
    lat = (reloc or {}).get('lat', natal['lat'])
    lon_ = (reloc or {}).get('lon', natal['lon'])
    prog = compute_chart(prog_date, natal['time'], lat, lon_,
                         natal['tz'], natal.get('hsys', 'P'))
    prog['input']['label'] = 'Progresada a %s' % target_date
    prog['input']['relocated'] = bool(reloc)
    prog['input']['lat'] = float(lat)
    prog['input']['lon'] = float(lon_)
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


# ════════════════════════════════════════════════════════════════════════
#  TRÁNSITOS SEMANALES (resumen de lunes 00:00 a domingo 24:00, hora local)
# ════════════════════════════════════════════════════════════════════════

# Cuerpos que se siguen durante la semana (la Luna se trata aparte)
_WK_BODIES = [k for k in PLANETS if k[0] not in ('aLuna', 'aLunaNegra')]
_WK_STATION = ('aMercurio', 'aVenus', 'aMarte', 'aJupiter', 'aSaturno',
               'aUrano', 'aNeptuno', 'aPluton', 'aChiron')
_WK_SLOW = ('aJupiter', 'aSaturno', 'aUrano', 'aNeptuno', 'aPluton',
            'aChiron', 'aNoduloNorte')
# (ángulo sobre el círculo, tipo, tipo_es)
_WK_ANGLES = [(0, 'Conjunction', 'Conjunción'), (60, 'Sextile', 'Sextil'),
              (90, 'Square', 'Cuadratura'), (120, 'Trine', 'Trígono'),
              (180, 'Opposition', 'Oposición'), (240, 'Trine', 'Trígono'),
              (270, 'Square', 'Cuadratura'), (300, 'Sextile', 'Sextil')]
PHASES_ES = ['Luna Nueva', 'Luna Creciente', 'Cuarto Creciente', 'Luna Gibosa',
             'Luna Llena', 'Luna Menguante', 'Cuarto Menguante', 'Luna Balsámica']
DIAS_ES = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']


def _wk_pos(jd, pid, flag):
    r = swe.calc_ut(jd, pid, flag)
    return r[0][0] % 360.0, r[0][3]


def _wdiff(a, b):
    """Diferencia con signo a−b en (−180, 180]."""
    return ((a - b + 180.0) % 360.0) - 180.0


def _local_dt(jd, tz):
    """JD (UT) → datetime en la hora local de `tz` (IANA u offset fijo)."""
    from datetime import timedelta, timezone
    y, m, d, hd = swe.revjul(jd)
    ut = datetime(int(y), int(m), int(d)) + timedelta(hours=hd)
    ut = (ut + timedelta(seconds=30)).replace(second=0, microsecond=0)
    tz = (tz or '').strip()
    try:
        from zoneinfo import ZoneInfo
        if tz and tz[0] not in '+-' and not tz.replace('.', '').isdigit():
            return ut.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(tz)).replace(tzinfo=None)
    except Exception:
        pass
    return ut + timedelta(hours=offset_hours(tz, ut.year, ut.month, ut.day, ut.hour, ut.minute))


def _bisect(f, a, b, n=40):
    fa = f(a)
    for _ in range(n):
        m = (a + b) / 2.0
        fm = f(m)
        if (fa <= 0) == (fm <= 0):
            a, fa = m, fm
        else:
            b = m
    return (a + b) / 2.0


def _stamp(jd, tz):
    dt = _local_dt(jd, tz)
    return {'jd': round(jd, 5), 'local': dt.strftime('%Y-%m-%d %H:%M'),
            'date': dt.strftime('%Y-%m-%d'), 'time': dt.strftime('%H:%M'),
            'weekday': dt.weekday(), 'weekday_es': DIAS_ES[dt.weekday()]}


def _where(lon, cusps):
    idx, sen, ses = _sign(lon)
    deg, minute = _dms(lon)
    return {'lon': round(lon, 4), 'sign': sen, 'sign_es': ses, 'deg': deg,
            'min': minute, 'natal_house': _house_of(lon, cusps)}


def compute_weekly(natal, week_date, reloc=None):
    """Resumen semanal de tránsitos sobre la carta natal.

    La semana va del lunes 00:00 al lunes siguiente 00:00, en la hora local
    del lugar natal o —si se relocaliza— del lugar indicado en `reloc`
    ({'lat','lon','tz'}). `week_date` es cualquier día de la semana deseada.

    Devuelve la carta natal, el cielo del lunes a las 00:00 (bi-rueda) y:
      aspects      → aspectos de los planetas al Sol, la Luna y el Asc natales
      moon_aspects → conjunciones/oposiciones de la Luna a esos tres puntos
      stations     → planetas que inician o terminan su retrogradación
      phases       → fases lunares (de las 8) que comienzan en la semana
    """
    from datetime import timedelta
    if os.path.isdir(_EPHE):
        swe.set_ephe_path(_EPHE)
    lat = (reloc or {}).get('lat', natal['lat'])
    lon_ = (reloc or {}).get('lon', natal['lon'])
    tz = (reloc or {}).get('tz') or natal.get('tz') or '+00:00'
    # Relocalizado: mismo instante natal, casas (y Ascendente) del lugar elegido.
    # Los planetas natales no cambian.
    if reloc:
        base = compute_chart(natal['date'], natal['time'], lat, lon_,
                             natal.get('tz', ''), natal.get('hsys', 'P'))
        base['input']['relocated'] = True
    else:
        base = compute_chart(**natal)

    d0 = datetime.strptime(week_date.replace('/', '-')[:10], '%Y-%m-%d')
    monday = d0 - timedelta(days=d0.weekday())
    nxt = monday + timedelta(days=7)
    jd0, _ = julian_day(monday.strftime('%Y-%m-%d'), '00:00', tz)
    jd1, _ = julian_day(nxt.strftime('%Y-%m-%d'), '00:00', tz)

    # Cielo del lunes 00:00 (para la bi-rueda y el clima general)
    snap = compute_chart(monday.strftime('%Y-%m-%d'), '00:00', lat, lon_, tz,
                         natal.get('hsys', 'P'))
    cusps = [h['lon'] for h in base['houses']]
    for p in snap['planets']:
        p['natal_house'] = _house_of(p['lon'], cusps)
    natal_pos = {p['key']: p['lon'] for p in base['planets']}
    snap_pos = {p['key']: p['lon'] for p in snap['planets']}
    # Cielo del lunes siguiente 00:00 (para las flechas de recorrido semanal)
    snap_end = compute_chart(nxt.strftime('%Y-%m-%d'), '00:00', lat, lon_, tz,
                             natal.get('hsys', 'P'))
    end_pos = {p['key']: {'lon': p['lon'], 'sign': p['sign'], 'sign_es': p['sign_es'],
                          'natal_house': _house_of(p['lon'], cusps)}
               for p in snap_end['planets']}

    targets = {'aSol': natal_pos.get('aSol'), 'aLuna': natal_pos.get('aLuna'),
               'aAsc': base['angles']['asc']['lon']}
    targets = {k: v for k, v in targets.items() if v is not None}

    step = 1.0 / 24.0                      # muestreo cada hora
    n = int(round((jd1 - jd0) / step))
    grid = [jd0 + i * step for i in range(n)] + [jd1]

    def scan(key, pid, flag, only=None, tgts=None):
        """Aspectos exactos (o en orbe estrecho) de un cuerpo durante la semana."""
        out = []
        tgts = targets if tgts is None else tgts
        try:
            lons = [_wk_pos(t, pid, flag)[0] for t in grid]
        except Exception:
            return out
        max_orb = 1.5 if key in _WK_SLOW else 1.0
        for tk, tl in tgts.items():
            for ang, typ, typ_es in _WK_ANGLES:
                if only and typ not in only:
                    continue
                goal = (tl + ang) % 360.0
                ds = [_wdiff(l, goal) for l in lons]
                hit = None
                for i in range(len(ds) - 1):
                    a, b = ds[i], ds[i + 1]
                    if abs(a) < 20 and abs(b) < 20 and (a <= 0) != (b <= 0):
                        hit = _bisect(lambda t: _wdiff(_wk_pos(t, pid, flag)[0], goal),
                                      grid[i], grid[i + 1])
                        break
                best = min(abs(x) for x in ds)
                if hit is None and (only or best > max_orb):
                    continue
                ev = {'transit': key, 'natal': tk, 'type': typ, 'type_es': typ_es,
                      'angle': ang if ang <= 180 else 360 - ang,
                      'exact': hit is not None, 'orb': round(best, 2),
                      'applying': abs(ds[-1]) < abs(ds[0])}
                if hit is not None:
                    ev['orb'] = 0.0
                    ev.update(_stamp(hit, tz))
                    ev['at'] = _where(_wk_pos(hit, pid, flag)[0], cusps)
                out.append(ev)
        return out

    aspects = []
    for key, name, pid, flag in _WK_BODIES:
        aspects += scan(key, pid, flag)
    # un aspecto por terna (el nodo verdadero oscila y puede repetir)
    seen, uniq = set(), []
    for a in aspects:
        k = (a['transit'], a['natal'], a['type'], a['angle'])
        if k not in seen:
            seen.add(k); uniq.append(a)
    aspects = sorted(uniq, key=lambda a: (0 if a['exact'] else 1, a.get('jd', 0)))

    moon_all = sorted(scan('aLuna', swe.MOON, _MOS,
                           only=('Conjunction', 'Opposition', 'Square',
                                 'Trine', 'Sextile')),
                      key=lambda a: a.get('jd', 0))
    moon_aspects = [a for a in moon_all if a['type'] in ('Conjunction', 'Opposition')]

    # ── Cambios de signo (todos los planetas, incluida la Luna) ───────────
    ingresses = []
    for key, name, pid, flag in PLANETS:
        if key in ('aNoduloNorte', 'aLunaNegra'):
            continue
        try:
            ls = [_wk_pos(t, pid, flag)[0] for t in grid]
        except Exception:
            continue
        for i in range(len(ls) - 1):
            sa, sb = int(ls[i] // 30), int(ls[i + 1] // 30)
            if sa != sb:
                retro = _wdiff(ls[i + 1], ls[i]) < 0
                goal = (sa * 30.0) if retro else (sb * 30.0)
                t = _bisect(lambda x: _wdiff(_wk_pos(x, pid, flag)[0], goal),
                            grid[i], grid[i + 1])
                ev = {'key': key, 'name': name, 'retrograde': retro,
                      'sign': SIGNS_EN[sb % 12], 'sign_es': SIGNS_ES[sb % 12],
                      'sign_index': sb % 12}
                ev.update(_stamp(t, tz))
                ingresses.append(ev)
    ingresses.sort(key=lambda e: e['jd'])

    # ── Planetas que se detienen (inicio / fin de retrogradación) ─────────
    stations, retro_now = [], []
    for key, name, pid, flag in PLANETS:
        if key not in _WK_STATION:
            continue
        try:
            sp = [_wk_pos(t, pid, flag)[1] for t in grid]
        except Exception:
            continue
        if sp[0] < 0:
            retro_now.append(key)
        for i in range(len(sp) - 1):
            if (sp[i] <= 0) != (sp[i + 1] <= 0):
                t = _bisect(lambda x: _wk_pos(x, pid, flag)[1], grid[i], grid[i + 1])
                ev = {'key': key, 'name': name,
                      'kind': 'retrograde' if sp[i] > 0 else 'direct'}
                ev.update(_stamp(t, tz))
                ev['hours'] = round((t - jd0) * 24.0, 2)
                ev['at'] = _where(_wk_pos(t, pid, flag)[0], cusps)
                stations.append(ev)
                break
    stations.sort(key=lambda s: s['jd'])

    # ── Fases de la Luna (8 fases de 45°) ─────────────────────────────────
    def elong(t):
        return (_wk_pos(t, swe.MOON, _MOS)[0] - _wk_pos(t, swe.SUN, _MOS)[0]) % 360.0

    def phase_info(t, idx):
        ml = _wk_pos(t, swe.MOON, _MOS)[0]
        sl = _wk_pos(t, swe.SUN, _MOS)[0]
        ev = {'index': idx, 'name': PHASES_ES[idx], 'moon': _where(ml, cusps),
              'sun': _where(sl, cusps), 'elong': round((ml - sl) % 360.0, 2)}
        ev.update(_stamp(t, tz))
        return ev

    es = [elong(t) for t in grid]
    phase_start = phase_info(jd0, int(es[0] // 45) % 8)
    phases = []
    for i in range(len(es) - 1):
        ia, ib = int(es[i] // 45) % 8, int(es[i + 1] // 45) % 8
        if ia != ib:
            goal = (ib * 45) % 360
            t = _bisect(lambda x: _wdiff(elong(x), goal), grid[i], grid[i + 1])
            phases.append(phase_info(t, ib))

    # ── Regente de la carta (planeta que rige el Ascendente natal) ───────
    _REG = {'Aries': 'aMarte', 'Taurus': 'aVenus', 'Gemini': 'aMercurio',
            'Cancer': 'aLuna', 'Leo': 'aSol', 'Virgo': 'aChiron', 'Libra': 'aVenus',
            'Scorpio': 'aPluton', 'Sagittarius': 'aJupiter', 'Capricorn': 'aSaturno',
            'Aquarius': 'aUrano', 'Pisces': 'aNeptuno'}
    ruler = None
    rk = _REG.get(base['angles']['asc']['sign'])
    rdef = next((x for x in PLANETS if x[0] == rk), None)
    if rdef and rk in snap_pos:
        _, rname, rpid, rflag = rdef
        tg_all = {k: v for k, v in natal_pos.items()
                  if k in ('aSol', 'aLuna', 'aMercurio', 'aVenus', 'aMarte', 'aJupiter',
                           'aSaturno', 'aUrano', 'aNeptuno', 'aPluton', 'aChiron',
                           'aNoduloNorte')}
        tg_all['aAsc'] = base['angles']['asc']['lon']
        tg_all['aMc'] = base['angles']['mc']['lon']
        r_asp = scan(rk, rpid, rflag, tgts=tg_all)
        seen, ra = set(), []
        for a in sorted(r_asp, key=lambda a: (0 if a['exact'] else 1, a.get('jd', 0), a['orb'])):
            kk = (a['natal'], a['type'])
            if kk not in seen:
                seen.add(kk); ra.append(a)
        sp = next(p for p in snap['planets'] if p['key'] == rk)
        ruler = {'key': rk, 'name': rname, 'asc_sign_es': base['angles']['asc']['sign_es'],
                 'sign': sp['sign'], 'sign_es': sp['sign_es'], 'deg': sp['deg'],
                 'min': sp['min'], 'lon': sp['lon'], 'natal_house': sp['natal_house'],
                 'retrograde': sp['retrograde'],
                 'end_house': end_pos.get(rk, {}).get('natal_house'),
                 'stations': [x for x in stations if x['key'] == rk],
                 'ingresses': [x for x in ingresses if x['key'] == rk],
                 'aspects': ra}

    sunday = monday + timedelta(days=6)
    return {
        'ruler': ruler,
        'natal': base, 'transit': snap, 'transit_end': end_pos,
        'ingresses': ingresses, 'moon_all': moon_all,
        'cross_aspects': _cross_aspects(snap_pos, natal_pos, 'transit', 'natal'),
        'week': {'start': monday.strftime('%Y-%m-%d'), 'end': sunday.strftime('%Y-%m-%d'),
                 'tz': tz, 'lat': float(lat), 'lon': float(lon_),
                 'relocated': bool(reloc)},
        'targets': {k: _where(v, cusps) for k, v in targets.items()},
        'aspects': aspects, 'moon_aspects': moon_aspects,
        'stations': stations, 'retro_now': retro_now,
        'phase_start': phase_start, 'phases': phases,
    }
