# -*- coding: utf-8 -*-
"""
weekly_esencial.py — Página ESENCIAL y PORTADILLA del Reporte Semanal (v2).
Especificación: INSTRUCCIONES_PDF_Semanal_v2.md (modo B: un solo PDF).

  build_esencial(data, L)  → dict con todo lo que dibuja la página esencial
  draw_esencial(d, E, L, brand, web)
  draw_portadilla(d, L, web)

Usa la capa de dibujo D de weekly_pdf (medidas en px, origen arriba-izquierda).
"""
import os
from datetime import date, timedelta

import report_chart as rc
from weekly import NOMBRE, _fecha, ROMAN
import weekly_layout as wl

# Regentes (los mismos que usa el reporte natal de Mauricio Puerta)
REG = {'Aries': 'aMarte', 'Taurus': 'aVenus', 'Gemini': 'aMercurio',
       'Cancer': 'aLuna', 'Leo': 'aSol', 'Virgo': 'aChiron', 'Libra': 'aVenus',
       'Scorpio': 'aPluton', 'Sagittarius': 'aJupiter', 'Capricorn': 'aSaturno',
       'Aquarius': 'aUrano', 'Pisces': 'aNeptuno'}

DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
DIAS_AB = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

# «su zona de …» (nombres de casas de Mauricio Puerta, en lenguaje común)
ZONA = ["la personalidad", "el dinero", "la mente y los hermanos", "el hogar",
        "los hijos y el amor", "la salud y el trabajo", "el matrimonio y los socios",
        "la transformación", "los viajes y los estudios", "la profesión",
        "los amigos y las esperanzas", "lo interior"]
FOCO = ["ocuparse de usted mismo y de su carácter",
        "ordenar su dinero y su seguridad material",
        "estudiar, escribir y hablar con los suyos",
        "ordenar la casa (la de adentro y la de afuera)",
        "crear, disfrutar y querer sin miedo",
        "cuidar su salud y poner orden en el trabajo",
        "cuidar su matrimonio y sus sociedades",
        "transformarse y soltar lo que cumplió su ciclo",
        "ampliar la mente y mirar más lejos",
        "trabajar por su misión y su profesión",
        "rodearse de amigos y alimentar sus esperanzas",
        "mirar hacia adentro y saldar cuentas pendientes"]

ARMONICO = ('Trine', 'Sextile')
TENSO = ('Square', 'Opposition')
BENEF = ('aVenus', 'aJupiter', 'aSol', 'aMercurio', 'aLuna', 'aNoduloNorte')
VERBO = {'Trine': "apoya a", 'Sextile': "apoya a", 'Square': "presiona a",
         'Opposition': "frente a", 'Conjunction': "sobre"}
NATAL_N = {'aSol': "su Sol", 'aLuna': "su Luna", 'aAsc': "su Ascendente",
           'aMc': "su Medio Cielo"}


def _art(k):
    return {'aSol': 'El Sol', 'aLuna': 'La Luna', 'aNoduloNorte': 'El Nodo Norte'}.get(
        k, NOMBRE.get(k, k))


def _natal(k):
    return NATAL_N.get(k, "su " + NOMBRE.get(k, k))


def _nat(a):
    """armónico (+1), tenso (−1) o neutro (0)."""
    t = a['type']
    if t in ARMONICO:
        return 1
    if t in TENSO:
        return -1
    return 1 if a['transit'] in BENEF else -1


def _dia(ev):
    return DIAS[ev['weekday']]


# ── Textos (plantillas breves; la lectura completa está en el detalle) ──
AREA_FRASE = {
    'amor': {1: "Buen clima para acercarse y decir lo que siente.",
             0: "Afectos tranquilos: cuide lo que ya tiene.",
             -1: "Más escucha y menos exigencia en lo afectivo."},
    'dinero': {1: "Momento propicio para ordenar y hacer crecer.",
               0: "Cuentas estables: revise antes de gastar.",
               -1: "Revise gastos y no firme a la carrera."},
    'trabajo': {1: "Sus ideas y su esfuerzo se notan.",
                0: "Avance con lo pendiente, paso a paso.",
                -1: "Paciencia con jefes y plazos esta semana."},
    'energia': {1: "Buena energía para moverse y empezar.",
                0: "Energía pareja: mantenga sus rutinas.",
                -1: "Descanse más y no se exceda."},
    'hogar': {1: "Buen momento para la familia y la casa.",
              0: "Hogar en calma: disfrute lo cotidiano.",
              -1: "Paciencia en casa; evite discusiones."},
}
AREA_HAGA = {'amor': ("Dedicar tiempo a quien quiere", "su zona del amor tiene viento a favor"),
             'dinero': ("Ordenar y revisar sus cuentas", "su zona del dinero viene favorecida"),
             'trabajo': ("Presentar sus ideas", "su zona de la profesión está favorecida"),
             'energia': ("Moverse y hacer ejercicio", "tiene la energía de su lado"),
             'hogar': ("Arreglar y disfrutar la casa", "su zona del hogar viene favorecida")}
AREA_NOHAGA = {'amor': ("Exigir sin escuchar", "su zona del amor pide atención"),
               'dinero': ("Gastar por impulso", "su zona del dinero pide atención"),
               'trabajo': ("Renunciar en caliente", "su zona de la profesión pide atención"),
               'energia': ("Excederse o desvelarse", "su energía pide cuidado"),
               'hogar': ("Discutir en familia", "su zona del hogar pide atención")}
GESTO = {'amor': "Escriba un mensaje sincero a alguien que quiere, sin esperar nada a cambio.",
         'dinero': "Anote cada gasto de la semana y el domingo revise en qué se le fue el dinero.",
         'trabajo': "Termine una tarea pendiente antes del miércoles y ordene su lugar de trabajo.",
         'energia': "Camine veinte minutos al día al aire libre y acuéstese media hora antes.",
         'hogar': "Ordene un rincón de su casa y regale lo que ya no usa."}
# acción en infinitivo para los días favorables, según el planeta en tránsito
DIA_FAVOR = {'aMercurio': "Proponer, vender y pedir ayuda", 'aVenus': "Reconciliar y agradar",
             'aMarte': "Empezar y tomar la iniciativa", 'aJupiter': "Pedir, ampliar y viajar",
             'aSaturno': "Ordenar y comprometerse", 'aSol': "Mostrarse y decidir",
             'aLuna': "Cuidar a los suyos", 'aUrano': "Probar algo distinto",
             'aNeptuno': "Crear e intuir", 'aPluton': "Cambiar a fondo",
             'aChiron': "Sanar y perdonar", 'aNoduloNorte': "Crecer y aprender"}
DIA_CALMA = {'aMercurio': "Releer antes de firmar", 'aVenus': "No gastar por impulso",
             'aMarte': "Evitar peleas y apuros", 'aJupiter': "No prometer de más",
             'aSaturno': "Tener paciencia", 'aSol': "No imponerse por orgullo",
             'aLuna': "No tomarlo como personal", 'aUrano': "No romper en caliente",
             'aNeptuno': "Verificar antes de creer", 'aPluton': "Soltar el control",
             'aChiron': "Cuidar las viejas heridas", 'aNoduloNorte': "No repetir viejos errores"}
NO_HAGA = {'aMercurio': "Firmar sin releer", 'aVenus': "Gastar por impulso",
           'aMarte': "Pelear o apurarse", 'aJupiter': "Prometer de más",
           'aSaturno': "Cargar con todo solo", 'aSol': "Imponerse por orgullo",
           'aLuna': "Tomarlo todo como personal", 'aUrano': "Romper en caliente",
           'aNeptuno': "Creer sin verificar", 'aPluton': "Querer controlarlo todo",
           'aChiron': "Reabrir viejas heridas", 'aNoduloNorte': "Repetir viejos patrones"}
FAVOR_DE = {'aMercurio': "conversar, proponer y negociar", 'aVenus': "el afecto y los acuerdos",
            'aMarte': "tomar la iniciativa", 'aJupiter': "crecer y pedir apoyo",
            'aSaturno': "ordenar y asumir compromisos", 'aUrano': "probar algo nuevo",
            'aNeptuno': "la intuición y lo creativo", 'aPluton': "transformar a fondo",
            'aSol': "mostrarse y decidir", 'aLuna': "lo afectivo y lo familiar",
            'aChiron': "sanar", 'aNoduloNorte': "aprender y crecer"}
CUIDAR_DE = {'aMercurio': "relea y confirme antes de decidir",
             'aVenus': "no gaste ni prometa por impulso",
             'aMarte': "evite peleas y apuros", 'aJupiter': "no exagere ni prometa de más",
             'aSaturno': "tenga paciencia con los límites",
             'aUrano': "no rompa nada en caliente", 'aNeptuno': "verifique antes de creer",
             'aPluton': "suelte el control", 'aSol': "no se imponga por orgullo",
             'aLuna': "no decida con la emoción revuelta",
             'aChiron': "cuide las viejas heridas", 'aNoduloNorte': "no repita viejos patrones"}
ESTACION_D = "Retomar lo detenido"
ESTACION_R = "Revisar antes de actuar"


def _corte(t, n):
    """Recorta en palabra completa (sin puntos suspensivos si cabe)."""
    t = ' '.join((t or '').split())
    if len(t) <= n:
        return t
    t = t[:n]
    return t[:t.rfind(' ')].rstrip(' ,;:') + '.'


def build_esencial(data, L):
    natal = data['natal']
    cusps = {h['num']: h for h in natal['houses']}
    snap = {p['key']: p for p in data['transit']['planets']}
    wk = data['week']
    y1, m1, d1 = _fecha(wk['start'])
    base = date(y1, m1, d1)

    def ruler(h):
        return REG.get(cusps[h]['sign'])

    AREAS = [
        ('amor', "Amor y pareja", 'heart', (5, 7), {'aVenus', 'aLuna', ruler(7)}),
        ('dinero', "Dinero", 'coins', (2, 8), {'aVenus', 'aJupiter', ruler(2), ruler(8)}),
        ('trabajo', "Trabajo", 'case', (6, 10), {'aSol', 'aSaturno', ruler(10), 'aMc'}),
        ('energia', "Energía y salud", 'bolt', (1, 6), {'aAsc', 'aSol', 'aMarte'}),
        ('hogar', "Hogar y familia", 'home', (4,), {'aLuna', ruler(4)}),
    ]
    exact = [a for a in data.get('all_aspects', []) if a.get('exact') and a['transit'] != 'aLuna']
    moon_ex = [a for a in data.get('moon_all', []) if a.get('exact')]

    areas = []
    for key, nombre, icon, casas, rel in AREAS:
        score, n_ev, pistas = 0, 0, []      # pistas: (peso, glifos, frase)
        for a in exact:
            if a['natal'] in rel:
                v = _nat(a)
                score += 2 * v; n_ev += 1
                pistas.append((3 + (1 if a['transit'] in wl.ORDEN_RETRO[3:] else 0), a, None, v))
        for a in moon_ex:
            if a['natal'] in rel:
                score += _nat(a); n_ev += 1
                pistas.append((1, a, None, _nat(a)))
        for k, p in snap.items():
            if p['natal_house'] in casas and k not in ('aLuna', 'aNoduloSur', 'aLunaNegra',
                                                       'aRuedaFortuna'):
                n_ev += 1
                if k in ('aVenus', 'aJupiter') and not p.get('retrograde'):
                    score += 1
                if k in ('aSaturno', 'aNeptuno', 'aPluton'):
                    score -= 1
        for f in data['phases']:
            if f['index'] == 0 and f['moon']['natal_house'] in casas:
                score += 1
                pistas.append((2, None, ('phase', f), 1))
        for s in data['stations']:
            if s['at']['natal_house'] in casas:
                n_ev += 1
                score += -2 if s['kind'] == 'retrograde' else 1
                pistas.append((4, None, ('station', s), -1 if s['kind'] == 'retrograde' else 1))
        nivel = 1 if score >= 2 else (-1 if score <= -2 else 0)
        inten = 1 if n_ev <= 1 else (2 if n_ev <= 3 else 3)
        areas.append({'key': key, 'nombre': nombre, 'icon': icon, 'casas': casas,
                      'score': score, 'nivel': nivel, 'inten': inten, 'pistas': pistas})
    # como máximo 2 áreas «Con atención»
    att = sorted([a for a in areas if a['nivel'] == -1], key=lambda a: a['score'])
    for a in att[2:]:
        a['nivel'] = 0

    # pista astrológica de cada área (glifos + frase común, ≤ 70)
    for a in areas:
        a['frase'] = AREA_FRASE[a['key']][a['nivel']]
        a['pista'] = _pista(a, snap)

    # ── días ─────────────────────────────────────────────────────────────
    dias = []
    for i in range(7):
        dd = data['days'][i]
        ev, nivel, texto = None, 0, "Avanzar con lo pendiente"
        isod = (base + timedelta(days=i)).isoformat()
        st = [s for s in data['stations'] if s['date'] == isod]
        fs = [f for f in data['phases'] if f['date'] == isod and f['index'] in (0, 4)]
        asp = [a for a in list(data['aspects']) + list(data['moon_aspects'])
               if a.get('exact') and a['date'] == isod]
        asp.sort(key=lambda a: (a['transit'] == 'aLuna', a['jd']))
        malo = [a for a in asp if _nat(a) < 0] + [s for s in st if s['kind'] == 'retrograde']
        bueno = [a for a in asp if _nat(a) > 0]
        if malo:
            nivel = -1
            m = malo[0]
            if 'kind' in m:
                ev, texto = ('station', m), ESTACION_R
            else:
                ev, texto = ('aspect', m), DIA_CALMA.get(m['transit'], "Ir con calma")
        elif bueno or fs or [s for s in st if s['kind'] == 'direct']:
            nivel = 1
            sd = [s for s in st if s['kind'] == 'direct']
            if bueno:
                ev, texto = ('aspect', bueno[0]), DIA_FAVOR.get(bueno[0]['transit'], "Avanzar")
            elif fs:
                ev = ('phase', fs[0])
                texto = "Sembrar un propósito" if fs[0]['index'] == 0 else "Cosechar y mirar claro"
            else:
                ev, texto = ('station', sd[0]), ESTACION_D
        # si hay estación y además aspecto, la estación también se muestra
        if ev and ev[0] == 'aspect' and st and nivel == 1:
            pass
        dias.append({'ab': DIAS_AB[i], 'num': (base + timedelta(days=i)).day,
                     'nivel': nivel, 'ev': ev, 'texto': _corte(texto, 32),
                     'elong': dd['elong'], 'msign': dd['moon_sign_index'], 'mejor': False})
    fav = [(i, a) for i, x in enumerate(dias) if x['ev'] and x['ev'][0] == 'aspect'
           and x['nivel'] == 1 for a in [x['ev'][1]]]
    if fav:
        fav.sort(key=lambda t: (t[1]['transit'] == 'aLuna', t[1]['jd']))
        dias[fav[0][0]]['mejor'] = True
    else:
        for x in dias:
            if x['nivel'] == 1:
                x['mejor'] = True
                break

    # ── tres tarjetas ────────────────────────────────────────────────────
    s_l_a = [a for a in data['aspects'] if a.get('exact')]
    arm = sorted([a for a in s_l_a if _nat(a) > 0], key=lambda a: a['jd'])
    ten = sorted([a for a in s_l_a + [m for m in data['moon_aspects'] if m.get('exact')]
                  if _nat(a) < 0], key=lambda a: (a['transit'] == 'aLuna', a['jd']))
    mejor_area = max(areas, key=lambda a: (a['nivel'], a['score']))
    if arm:
        a = arm[0]
        fav_txt = "%s %s %s el %s: buen momento para %s. Lo más favorecido: %s." % (
            _art(a['transit']), VERBO[a['type']], _natal(a['natal']), _dia(a),
            FAVOR_DE.get(a['transit'], "avanzar"), mejor_area['nombre'].lower())
    else:
        fav_txt = "Sin aspectos fáciles exactos: el buen día lo pone usted. Lo más favorecido: %s." \
            % mejor_area['nombre'].lower()
    peor = min(areas, key=lambda a: (a['nivel'], a['score']))
    if ten:
        a = ten[0]
        cui_txt = "%s %s %s el %s: %s." % (_art(a['transit']), VERBO[a['type']],
                                           _natal(a['natal']), _dia(a),
                                           CUIDAR_DE.get(a['transit'], "vaya con calma"))
    else:
        rs = [s for s in data['stations'] if s['kind'] == 'retrograde']
        if rs:
            s = rs[0]
            cui_txt = "%s se detiene a revisar el %s en su zona de %s: %s." % (
                s['name'], _dia(s), ZONA[s['at']['natal_house'] - 1],
                CUIDAR_DE.get(s['key'], "revise antes de actuar"))
        else:
            cui_txt = "Semana sin tensiones fuertes; cuide igual %s." % peor['nombre'].lower()
    cons = L['elementos']['consejo']
    tarjetas = [("Lo que le favorece", '#7E9B78', 'up', _corte(fav_txt, 140)),
                ("Lo que debe cuidar", '#C08A7B', 'pause', _corte(cui_txt, 140)),
                ("Su consejo", '#B8863B', 'star',
                 _corte("%s. %s" % (cons[0], cons[1]), 140))]

    # ── frase de la semana (≤ 130) ───────────────────────────────────────
    hs = snap['aSol']['natal_house'] if 'aSol' in snap else 1
    frase = "Una semana para %s" % FOCO[hs - 1]
    ext = []
    for s in data['stations']:
        z = ZONA[s['at']['natal_house'] - 1]
        ext.append((" y destrabar lo que estaba detenido en su zona de %s" if s['kind'] == 'direct'
                    else " y revisar con calma lo que toca a su zona de %s") % z)
    for f in data['phases']:
        if f['index'] == 0:
            ext.append(" y sembrar algo nuevo en su zona de %s" % ZONA[f['moon']['natal_house'] - 1])
        if f['index'] == 4:
            ext.append(" y cosechar en su zona de %s" % ZONA[f['moon']['natal_house'] - 1])
    for e in ext:
        if len(frase + e) + 1 <= 130:
            frase += e
            break
    frase += "."

    # ── haga / no haga / gesto ───────────────────────────────────────────
    haga, nohaga = [], []
    md = next((x for x in dias if x['mejor']), None)
    if md and md['ev'] and md['ev'][0] == 'aspect':
        a = md['ev'][1]
        haga.append((_corte("%s el %s" % (md['texto'].split(',')[0].split(' y ')[0], _dia(a)), 32),
                     _corte("%s %s %s" % (_art(a['transit']), VERBO[a['type']],
                                          _natal(a['natal'])), 45)))
    for s in data['stations']:
        if s['kind'] == 'direct' and len(haga) < 3:
            haga.append(("Retomar lo detenido", _corte("%s retoma la marcha el %s" % (
                s['name'], _dia(s)), 45)))
            break
    for f in data['phases']:
        if f['index'] == 0 and len(haga) < 3:
            haga.append(("Sembrar un propósito", _corte("Luna Nueva el %s" % _dia(f), 45)))
    for a in sorted(areas, key=lambda a: -a['score']):
        if a['nivel'] == 1 and len(haga) < 3:
            haga.append(AREA_HAGA[a['key']])
    while len(haga) < 3:
        extra = [("Avanzar con lo pendiente", "la semana premia la constancia"),
                 ("Ordenar su agenda", "un plan claro le ahorra apuros"),
                 ("Descansar bien", "el cuerpo también trabaja")]
        haga.append(extra[len(haga)])
    peor_d = next((x for x in dias if x['nivel'] == -1), None)
    if peor_d and peor_d['ev']:
        kind, e = peor_d['ev']
        if kind == 'aspect':
            nohaga.append((NO_HAGA.get(e['transit'], "Apurarse"),
                           _corte("%s %s %s, el %s" % (_art(e['transit']), VERBO[e['type']],
                                                        _natal(e['natal']), _dia(e)), 45)))
        else:
            nohaga.append((NO_HAGA.get(e['key'], "Apurarse"),
                           _corte("%s se detiene a revisar el %s" % (e['name'], _dia(e)), 45)))
    for s in data['stations']:
        if s['kind'] == 'retrograde' and len(nohaga) < 3:
            t = (NO_HAGA.get(s['key'], "Apurarse"),
                 _corte("%s se detiene a revisar el %s" % (s['name'], _dia(s)), 45))
            if t[0] not in [x[0] for x in nohaga]:
                nohaga.append(t)
    for a in sorted(areas, key=lambda a: a['score']):
        if a['nivel'] == -1 and len(nohaga) < 3:
            nohaga.append(AREA_NOHAGA[a['key']])
    for k in data.get('retro_now', []):
        if len(nohaga) < 3:
            t = (NO_HAGA.get(k, "Apurarse"), _corte("%s sigue retrógrado" % NOMBRE[k], 45))
            if t[0] not in [x[0] for x in nohaga]:
                nohaga.append(t)
    while len(nohaga) < 3:
        extra = [("Dejar todo para el domingo", "el ritmo parejo rinde más"),
                 ("Discutir por cansancio", "descanse antes de responder"),
                 ("Compararse con otros", "cada cielo tiene su tiempo")]
        nohaga.append(extra[len(nohaga)])
    top_int = max(areas, key=lambda a: (a['inten'], abs(a['score'])))
    gesto = GESTO[top_int['key']]

    # ── Retorno Solar en la semana ───────────────────────────────────────
    rs = next((a for a in data.get('all_aspects', []) if a['transit'] == 'aSol'
               and a['natal'] == 'aSol' and a['type'] == 'Conjunction' and a.get('exact')), None)
    banda = None
    if rs:
        _, mm, dd_ = _fecha(rs['date'])
        banda = "(%s %d de %s, %s h)" % (DIAS[rs['weekday']], dd_, MESES[mm - 1], rs['time'])

    return {'frase': frase, 'tarjetas': tarjetas, 'areas': areas, 'dias': dias,
            'haga': haga[:3], 'nohaga': nohaga[:3], 'gesto': gesto, 'banda': banda,
            'rango': "del %d al %d de %s de %d" % (d1, _fecha(wk['end'])[2],
                                                  MESES[_fecha(wk['end'])[1] - 1],
                                                  _fecha(wk['end'])[0])
            if m1 == _fecha(wk['end'])[1] else
            "del %d de %s al %d de %s de %d" % (d1, MESES[m1 - 1], _fecha(wk['end'])[2],
                                                 MESES[_fecha(wk['end'])[1] - 1],
                                                 _fecha(wk['end'])[0])}


def _pista(a, snap):
    """(glifos, frase) de la pista más fuerte de un área."""
    if not a['pistas']:
        ks = [k for k, p in snap.items() if p['natal_house'] in a['casas']
              and k not in ('aLuna', 'aNoduloSur', 'aLunaNegra', 'aRuedaFortuna')]
        if ks:
            k = ks[0]
            h = snap[k]['natal_house']
            return ([('p', k)], "%s pasa por su zona de %s" % (_art(k), ZONA[h - 1]))
        return ([], "Sin tránsitos fuertes en esta área")
    # la pista acompaña al nivel: favorable → evento a favor; con atención → tenso
    want = a['nivel']
    pool = [t for t in a['pistas'] if (want == 0 or t[3] == want)] or a['pistas']
    peso, asp, otro, _sg = max(pool, key=lambda t: t[0])
    if asp:
        tgt = ('t', 'Ac') if asp['natal'] == 'aAsc' else (
            ('t', 'MC') if asp['natal'] == 'aMc' else ('p', asp['natal']))
        g = [('p', asp['transit']), ('a', asp['type']), tgt]
        return (g, "%s %s %s, el %s" % (_art(asp['transit']), VERBO[asp['type']],
                                        _natal(asp['natal']), _dia(asp)))
    kind, e = otro
    if kind == 'station':
        mism = [x[2][1] for x in a['pistas'] if x[2] and x[2][0] == 'station'
                and x[2][1]['kind'] == e['kind']
                and x[2][1]['at']['natal_house'] == e['at']['natal_house']]
        nombres = [m['name'] for m in mism][:2]
        verbo = ("retoman la marcha" if len(nombres) > 1 else "retoma la marcha") \
            if e['kind'] == 'direct' else \
            ("se detienen a revisar" if len(nombres) > 1 else "se detiene a revisar")
        return ([('p', m['key']) for m in mism[:2]],
                "%s %s en su zona de %s" % (" y ".join(nombres), verbo,
                                            ZONA[e['at']['natal_house'] - 1]))
    return ([('ph', e['elong'])], "Luna Nueva en su zona de %s, el %s" % (
        ZONA[e['moon']['natal_house'] - 1], _dia(e)))


# ════════════════════════════════════════════════════════════════════════
#  Dibujo
# ════════════════════════════════════════════════════════════════════════

NAVY = '#0F1B3D'; INK = '#26304F'; MUTED = '#5A6178'; GOLD = '#B8863B'
GOLD_D = '#96682A'; GOLD_S = '#C9A063'; CREAM = '#F7F0D3'; TINT = '#FBF7EC'
HAIR = '#E2D3B4'; RETRO = '#C0392B'; WHITE = '#FFFFFF'
NIVEL = {1: ("Viento a favor", '#EEF3EC', '#7E9B78', '#4F6B4A', 'up'),
         0: ("Estable", '#F7F0DE', '#B8863B', '#96682A', 'flat'),
         -1: ("Con atención", '#F6E9E5', '#C08A7B', '#9A4F42', 'pause')}
DOT = {1: '#7E9B78', 0: '#B8863B', -1: '#C08A7B'}
_STARS = [(64, 22, 1.1), (130, 64, 0.8), (205, 18, 1.0), (262, 96, 0.7), (318, 40, 1.2),
          (372, 84, 0.8), (430, 26, 0.9), (488, 70, 0.7), (612, 14, 0.9), (700, 98, 0.8),
          (756, 30, 1.1), (96, 104, 0.7), (540, 104, 0.9), (16, 60, 0.8)]


def _stars(d, h, scale=1.0):
    for x, y, r in _STARS:
        if y * scale < h:
            d.circ(x, y * scale, r, fill=CREAM)


def _icon(d, kind, cx, cy, s, col):
    """Íconos de trazo simples (s = tamaño en px)."""
    h = s / 2.0
    lw = 1.6
    if kind == 'up':
        d.poly([(cx - h, cy + h * 0.6), (cx - h * 0.2, cy - h * 0.1), (cx + h * 0.2, cy + h * 0.3),
                (cx + h, cy - h * 0.6)], col, lw)
        d.poly([(cx + h * 0.4, cy - h * 0.6), (cx + h, cy - h * 0.6), (cx + h, cy)], col, lw)
    elif kind == 'flat':
        d.ln(cx - h, cy, cx + h, cy, col, lw + 0.4, cap=1)
    elif kind == 'pause':
        d.ln(cx - h * 0.35, cy - h * 0.7, cx - h * 0.35, cy + h * 0.7, col, lw + 0.4, cap=1)
        d.ln(cx + h * 0.35, cy - h * 0.7, cx + h * 0.35, cy + h * 0.7, col, lw + 0.4, cap=1)
    elif kind == 'star':
        import math
        pts = []
        for i in range(11):
            r = h if i % 2 == 0 else h * 0.42
            a = math.radians(-90 + i * 36)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.poly(pts, col, lw)
    elif kind == 'heart':
        import math
        pts = []
        for i in range(41):
            t = 2 * math.pi * i / 40
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts.append((cx + x * h / 17.0, cy - y * h / 17.0 + h * 0.08))
        d.poly(pts, col, lw)
    elif kind == 'coins':
        d.circ(cx - h * 0.25, cy - h * 0.15, h * 0.62, stroke=col, lw=lw)
        d.c.saveState()
        d.circ(cx + h * 0.32, cy + h * 0.3, h * 0.55, fill=TINT, stroke=col, lw=lw)
        d.c.restoreState()
    elif kind == 'case':
        d.rr(cx - h, cy - h * 0.45, 2 * h, h * 1.35, 2.5, stroke=col, lw=lw)
        d.rr(cx - h * 0.4, cy - h * 0.85, h * 0.8, h * 0.4, 1.5, stroke=col, lw=lw)
        d.ln(cx - h, cy + h * 0.1, cx + h, cy + h * 0.1, col, lw)
    elif kind == 'bolt':
        d.poly([(cx + h * 0.2, cy - h), (cx - h * 0.55, cy + h * 0.15), (cx, cy + h * 0.15),
                (cx - h * 0.2, cy + h), (cx + h * 0.55, cy - h * 0.15), (cx, cy - h * 0.15),
                (cx + h * 0.2, cy - h)], col, lw)
    elif kind == 'home':
        d.poly([(cx - h, cy - h * 0.05), (cx, cy - h), (cx + h, cy - h * 0.05)], col, lw)
        d.poly([(cx - h * 0.7, cy - h * 0.3), (cx - h * 0.7, cy + h * 0.9),
                (cx + h * 0.7, cy + h * 0.9), (cx + h * 0.7, cy - h * 0.3)], col, lw)
        d.rr(cx - h * 0.2, cy + h * 0.3, h * 0.4, h * 0.6, 0, stroke=col, lw=lw)
    elif kind == 'check':
        d.poly([(cx - h * 0.8, cy), (cx - h * 0.2, cy + h * 0.6), (cx + h * 0.85, cy - h * 0.6)],
               col, 2.0)
    elif kind == 'cross':
        d.ln(cx - h * 0.6, cy - h * 0.6, cx + h * 0.6, cy + h * 0.6, col, 2.0, cap=1)
        d.ln(cx + h * 0.6, cy - h * 0.6, cx - h * 0.6, cy + h * 0.6, col, 2.0, cap=1)


def _glifos(d, x, y, items, size, col=None):
    """Dibuja una secuencia de glifos (planeta, aspecto, texto) desde x; devuelve el ancho."""
    x0 = x
    for kind, v in items:
        if kind == 'p':
            d.planet(v, x + size * 0.5, y, size)
            x += size + 2
        elif kind == 'a':
            c_, g_, _ = rc.ASPECTS[v.lower()]
            d.gch(g_, x + size * 0.45, y, size * 0.9, c_)
            x += size + 1
        elif kind == 't':
            w = d.tx(x, y + size * 0.35, v, 'b', size * 0.72, col or INK)
            x += w + 3
        elif kind == 'ph':
            d.moon(x + size * 0.5, y, size * 0.45, v, ring=0.5)
            x += size + 2
        elif kind == 'R':
            w = d.tx(x - 1, y + size * 0.35, v, 'b', size * 0.7, RETRO if v == 'R' else GOLD_D)
            x += w + 2
    return x - x0


def _bg(d, path, x, y, w, h, alpha):
    from weekly_pdf import faded
    img = faded(path, alpha, int(min(w * 1.25, 1000)))
    if img is not None:
        d.c.drawImage(img, d.X(x), d.Y(y + h), w * 0.75, h * 0.75, mask='auto')


def draw_esencial(d, E, L, web, n=1):
    from weekly_pdf import ASSETS, footer
    PW, ML = 794.0, 40.0
    CW = PW - 2 * ML
    c = d.c
    # fondo de ruedas (17 %)
    _bg(d, os.path.join(ASSETS, 'fondo_ruedas.png'), 0, 568, 794, 550, 0.17)

    # 3.1 encabezado
    H = 116
    d.rr(0, 0, PW, H, fill=NAVY)
    c.saveState()
    p = c.beginPath(); p.rect(0, d.Y(H), PW * 0.75, H * 0.75); c.clipPath(p, stroke=0, fill=0)
    _bg(d, os.path.join(ASSETS, 'rueda_dorada.png'), 544, -110, 340, 340, 0.36)
    c.restoreState()
    _stars(d, H)
    d.tx(ML, 34, "REPORTE ASTRAL · SU SEMANA", 'sb', 9.5, GOLD_S, track=4)
    d.tx(ML, 70, "El cielo en esta semana", 'b', 30, WHITE, track=-0.5)
    d.tx(ML, 94, E['rango'], 'mi', 13, GOLD_S)
    nm = L.get('name') or ''
    if nm:
        s_, z_ = d.fit(nm, 'b', 24, 250, 0, 14)
        d.tx(PW - ML, 64, s_, 'b', z_, WHITE, 'r')
    lug = (L.get('lugar') or '') + "*"
    s_, z_ = d.fit(lug, 'r', 10, 250, 0, 8)
    d.tx(PW - ML, 84, s_, 'r', z_, CREAM, 'r')
    y = H

    # 3.2 banda de Retorno Solar
    if E['banda']:
        bh = 44
        c.saveState()
        from reportlab.lib.colors import HexColor
        sh = c.linearGradient
        p = c.beginPath(); p.rect(0, d.Y(y + bh), PW * 0.75, bh * 0.75); c.clipPath(p, stroke=0, fill=0)
        c.linearGradient(0, d.Y(y), PW * 0.75, d.Y(y), (HexColor('#E8C98A'), HexColor('#C9A063')),
                         extend=True)
        c.restoreState()
        d.circ(ML + 13, y + bh / 2.0, 13, fill=NAVY)
        d.planet('aSol', ML + 13, y + bh / 2.0, 15, '#E8C98A')
        d.para(ML + 36, y + 7, CW - 36,
               "<b>Esta semana es su Retorno Solar</b> %s. Feliz año nuevo solar: lo que "
               "siembre estos días marca el tono de sus próximos doce meses." % d.esc(E['banda']),
               'r', 10.5, NAVY, 1.35)
        y += bh
    gap = 9 if E['banda'] else 11
    y += 14 if E['banda'] else 18

    # 3.3 frase
    fh = d.ph(d.esc(E['frase']), CW - 20, 'mi', 16, NAVY, 1.35)
    d.rr(ML, y, 4, 18 + fh, fill=GOLD)
    d.tx(ML + 16, y + 10, "SU SEMANA EN UNA FRASE", 'sb', 8.5, GOLD_D, track=3)
    d.para(ML + 16, y + 16, CW - 20, d.esc(E['frase']), 'mi', 16, NAVY, 1.35)
    y += 18 + fh + gap

    # 3.4 tres tarjetas
    tw_ = (CW - 20) / 3.0
    th = max(d.ph(d.esc(t[3]), tw_ - 28, 'r', 11, INK, 1.4) for t in E['tarjetas']) + 50
    for i, (tit, col, ic, tx) in enumerate(E['tarjetas']):
        x = ML + i * (tw_ + 10)
        c.saveState()
        p = c.beginPath(); p.roundRect(d.X(x), d.Y(y + th), tw_ * 0.75, th * 0.75, 14 * 0.75)
        c.clipPath(p, stroke=0, fill=0)
        d.rr(x, y, tw_, th, fill=WHITE)
        d.rr(x, y, tw_, 3, fill=col)
        c.restoreState()
        d.rr(x, y, tw_, th, 14, stroke=HAIR, lw=1)
        _icon(d, ic, x + 14 + 8.5, y + 23, 15, col)
        d.tx(x + 14 + 24, y + 27, tit, 'b', 12, NAVY)
        d.para(x + 14, y + 40, tw_ - 28, d.esc(tx), 'r', 11, INK, 1.4)
    y += th + gap

    # 3.5 áreas de la vida
    d.tx(ML, y + 9, "SUS ÁREAS DE LA VIDA", 'sb', 8.5, GOLD_D, track=3)
    y += 16
    rh = 50
    for a in E['areas']:
        d.ln(ML, y, PW - ML, y, HAIR, 1)
        cy = y + rh / 2.0
        d.circ(ML + 17, cy, 17, fill=TINT)
        _icon(d, a['icon'], ML + 17, cy, 16, NAVY)
        x2 = ML + 34 + 12
        d.tx(x2, cy - 2, a['nombre'], 'b', 12.5, NAVY)
        for k in range(3):
            d.circ(x2 + 3 + k * 9, cy + 11, 3, fill=GOLD if k < a['inten'] else HAIR)
        d.tx(x2 + 30, cy + 14, "intensidad", 'r', 8.5, MUTED)
        lab, bg_, br_, tc_, ic_ = NIVEL[a['nivel']]
        x3 = ML + 34 + 12 + 120 + 12
        d.rr(x3, cy - 11, 128, 22, 11, fill=bg_, stroke=br_, lw=1)
        _icon(d, ic_, x3 + 15, cy, 11, tc_)
        d.tx(x3 + 26, cy + 3.8, lab, 'sb', 10, tc_)
        x4 = x3 + 128 + 14
        w4 = PW - ML - x4
        s_, z_ = d.fit(a['frase'], 'r', 11.5, w4, 0, 9.5)
        d.tx(x4, cy - 3, s_, 'r', z_, INK)
        gl, fr = a['pista']
        gw = _glifos(d, x4, cy + 12, gl, 11)
        s_, z_ = d.fit(fr, 'r', 9.5, w4 - gw - 6, 0, 7.5)
        d.tx(x4 + gw + (6 if gw else 0), cy + 15.5, s_, 'r', z_, MUTED)
        y += rh
    d.ln(ML, y, PW - ML, y, HAIR, 1)
    y += gap + 2

    # 3.6 mejores días
    d.tx(ML, y + 9, "MEJORES DÍAS PARA…", 'sb', 8.5, GOLD_D, track=3)
    y += 16
    cw7 = (CW - 6 * 6) / 7.0
    ch = 112
    for i, x_ in enumerate(E['dias']):
        x = ML + i * (cw7 + 6)
        if x_['mejor']:
            d.rr(x, y, cw7, ch, 12, fill='#FFFBF1', stroke=GOLD, lw=1.5)
            d.tx(x + cw7 - 6, y + 12, "MEJOR", 'b', 7, GOLD_D, 'r', track=0.8)
        else:
            d.rr(x, y, cw7, ch, 12, fill=WHITE, stroke=HAIR, lw=1)
        d.moon(x + 12, y + 12, 6, x_['elong'], ring=0.5)
        si = x_['msign']
        d.gch(rc.SIGN_GLYPH[si], x + 25, y + 12, 10, rc.SIGN_COL[si])
        d.tx(x + cw7 / 2.0, y + 34, x_['ab'], 'sb', 9, MUTED, 'c', track=1.5)
        d.tx(x + cw7 / 2.0, y + 54, str(x_['num']), 'b', 17, NAVY, 'c')
        ev = x_['ev']
        items = []
        if ev:
            k, e = ev
            if k == 'aspect':
                tgt = ('t', 'Ac') if e['natal'] == 'aAsc' else ('p', e['natal'])
                items = [('p', e['transit']), ('a', e['type']), tgt]
            elif k == 'station':
                items = [('p', e['key']), ('R', 'R' if e['kind'] == 'retrograde' else 'D')]
            elif k == 'phase':
                items = [('ph', e['elong'])]
        # ancho para centrar
        tmpw = sum(13 if it[0] != 't' else d.tw(it[1], 'b', 8) + 3 for it in items)
        tot = 8 + (5 + tmpw if items else 0)
        sx = x + cw7 / 2.0 - tot / 2.0
        d.circ(sx + 4, y + 70, 4, fill=DOT[x_['nivel']])
        if items:
            _glifos(d, sx + 13, y + 70, items, 11)
        d.para(x + 4, y + 80, cw7 - 8, d.esc(x_['texto']), 'r', 9.5, INK, 1.25, 'c')
    y += ch + gap + 2

    # 3.7 haga / no haga / gesto
    tot = 1 + 1 + 1.05
    wA = (CW - 24) * 1 / tot
    wC = (CW - 24) * 1.05 / tot
    def lista(x, w, titulo, items, ic, col):
        d.tx(x, y + 9, titulo, 'sb', 8.5, GOLD_D, track=3)
        yy = y + 20
        for acc, porq in items:
            _icon(d, ic, x + 6, yy + 6, 10, col)
            s_, z_ = d.fit(acc, 'b', 11, w - 18, 0, 9)
            d.tx(x + 18, yy + 10, s_, 'b', z_, NAVY)
            s_, z_ = d.fit(porq, 'r', 10, w - 18, 0, 8)
            d.tx(x + 18, yy + 23, s_, 'r', z_, MUTED)
            yy += 33
        return yy
    y1_ = lista(ML, wA, "HAGA", E['haga'], 'check', '#7E9B78')
    lista(ML + wA + 12, wA, "NO HAGA", E['nohaga'], 'cross', '#C08A7B')
    gx = ML + 2 * (wA + 12)
    gh = y1_ - y
    d.rr(gx, y, wC, gh, 14, fill=CREAM)
    d.tx(gx + 14, y + 20, "UN GESTO PARA ESTA SEMANA", 'sb', 8, GOLD_D, track=2)
    d.para(gx + 14, y + 28, wC - 28, d.esc(E['gesto']), 'r', 11.5, NAVY, 1.4)
    y = y1_ + gap

    # 3.8 cierre con enlace
    from weekly_pdf import ASSETS as _A
    nota = L['nota_esencial']
    nota_h = d.ph(d.esc(nota), CW, 'r', 8.5, MUTED, 1.4)
    bh = 76
    by = min(y, 1079 - 10 - nota_h - 10 - bh)
    d.rr(ML, by, CW, bh, 16, fill=NAVY)
    for sx_, sy_ in ((ML + 300, by + 14), (ML + 420, by + 60), (ML + 520, by + 20), (ML + 610, by + 64)):
        d.circ(sx_, sy_, 0.9, fill=CREAM)
    d.rr(ML + 16, by + 12, 52, 52, 12, fill=CREAM)
    logo = os.path.join(_A, 'logo_diario_astral.png')
    if os.path.exists(logo):
        from reportlab.lib.utils import ImageReader
        c.drawImage(ImageReader(logo), d.X(ML + 22), d.Y(by + 12 + 46), 40 * 0.75, 46 * 0.75,
                    mask='auto', preserveAspectRatio=True, anchor='c')
    tx_ = ML + 16 + 52 + 16
    d.tx(tx_, by + 28, "¿Quiere saber más?", 'b', 13.5, WHITE)
    d.para(tx_, by + 34, CW - (tx_ - ML) - 200, (
        "En el detalle astrológico está la lectura completa de su semana. Para un estudio "
        "completo, visite <font color='%s'><b>%s</b></font> o la app "
        "<font color='%s'><b>Diario Astral</b></font>." % (GOLD_S, web, GOLD_S)),
        'r', 10.5, CREAM, 1.35)
    d.tx(PW - ML - 20, by + bh / 2.0 + 4, "Ver el detalle astrológico ›", 'b', 11.5, GOLD_S, 'r')
    c.linkRect("", "detalle", (d.X(ML), d.Y(by + bh), d.X(ML + CW), d.Y(by)), relative=0,
               thickness=0)
    # nota + pie
    d.para(ML, 1079 - 10 - nota_h, CW, d.esc(nota), 'r', 8.5, MUTED, 1.4)
    footer(d, n, web)


def draw_portadilla(d, L, web, n=2, pags=(3, 4, 5)):
    from weekly_pdf import ASSETS, footer
    PW, ML = 794.0, 56.0
    CW = PW - 2 * ML
    c = d.c
    c.bookmarkPage("detalle")
    c.addOutlineEntry("Detalle astrológico", "detalle", level=0)
    _bg(d, os.path.join(ASSETS, 'fondo_constelaciones.png'), 0, 420, 794, 461, 0.28)
    _bg(d, os.path.join(ASSETS, 'fondo_constelaciones.png'), 0, 881, 794, 461, 0.28)
    H = 420
    d.rr(0, 0, PW, H, fill=NAVY)
    c.saveState()
    p = c.beginPath(); p.rect(0, d.Y(H), PW * 0.75, H * 0.75); c.clipPath(p, stroke=0, fill=0)
    _bg(d, os.path.join(ASSETS, 'rueda_dorada.png'), 384, -120, 560, 560, 0.39)
    c.restoreState()
    _stars(d, H, 3.6)
    d.tx(ML, 262, "PARA QUIENES QUIEREN SABER MÁS", 'sb', 10, GOLD_S, track=4)
    d.tx(ML, 312, "Detalle astrológico", 'b', 42, WHITE, track=-0.8)
    d.para(ML, 330, 470, d.esc(
        "La página anterior le dice qué hacer. Las siguientes le muestran por qué: el "
        "cielo de la semana tal como lo lee un astrólogo, con sus planetas, casas y aspectos."),
        'r', 14, CREAM, 1.5)

    y = H + 44
    colw = (CW - 40) / 2.0
    # qué encontrará
    d.tx(ML, y, "QUÉ ENCONTRARÁ", 'sb', 9, GOLD_D, track=3)
    items = [("El cielo y la agenda", "La rueda de la semana sobre su carta natal, el reparto "
              "de elementos y la agenda día por día."),
             ("Su semana de un vistazo", "El recorrido de los planetas por sus casas, las fases "
              "de la Luna y los tránsitos más importantes."),
             ("Lo que el cielo le hace a usted", "Su Sol, su Luna, su Ascendente y su regente, "
              "el tablero de retrógrados y las claves de la semana.")]
    yy = y + 14
    for (tit, desc), pg in zip(items, pags):
        hh = d.ph(d.esc(desc), colw - 50, 'r', 10.5, INK, 1.45) + 34
        d.rr(ML, yy, colw, hh, 12, fill=WHITE, stroke=HAIR, lw=1)
        d.diamond(ML + 22, yy + 22, 13, stroke=GOLD, lw=1)
        d.tx(ML + 22, yy + 26, str(pg), 'b', 11, NAVY, 'c')
        d.tx(ML + 46, yy + 22, tit, 'b', 12.5, NAVY)
        d.para(ML + 46, yy + 28, colw - 56, d.esc(desc), 'r', 10.5, INK, 1.45)
        c.linkRect("", "pag%d" % pg, (d.X(ML), d.Y(yy + hh), d.X(ML + colw), d.Y(yy)),
                   relative=0, thickness=0)
        yy += hh + 10
    # glosario
    gx = ML + colw + 40
    d.tx(gx, y, "PEQUEÑO GLOSARIO", 'sb', 9, GOLD_D, track=3)
    glos = [("Tránsito", "dónde están hoy los planetas comparado con dónde estaban cuando usted nació."),
            ("Casa", "cada una de las 12 áreas de la vida en su carta (dinero, pareja, trabajo, hogar…)."),
            ("Ascendente", "el signo que salía por el horizonte al nacer; su manera de presentarse ante el mundo."),
            ("Aspecto", "la relación entre dos planetas. Los armónicos facilitan; los tensos piden ajuste."),
            ("Retrógrado", "un planeta que parece andar hacia atrás; pide revisar y terminar antes que estrenar."),
            ("Estación", "el día en que un planeta se detiene para cambiar de rumbo. Se siente con fuerza."),
            ("Fases de la Luna", "Nueva para sembrar, creciente para impulsar, llena para cosechar, menguante para soltar."),
            ("Elementos", "Fuego (impulso), Tierra (concreción), Aire (ideas) y Agua (emociones).")]
    yy = y + 16
    for t, x_ in glos:
        hh = d.para(gx, yy, colw, "<b><font color='%s'>%s:</font></b> %s" % (NAVY, t, d.esc(x_)),
                    'r', 10.5, INK, 1.45)
        yy += hh + 9
    footer(d, n, web)
