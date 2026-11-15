# -*- coding: utf-8 -*-
"""
weekly_layout.py — Datos y textos del Reporte de Tránsitos Semanales, diseño v1
(PDF de 3 páginas fijas). Especificación: DISENO_Reporte_Transitos_Semanales.md

build_layout() toma el resultado de astro.compute_weekly() y devuelve un dict
con todo lo que weekly_pdf.py dibuja, con los textos ya recortados a los
límites del diseño (§7).
"""
import re
from datetime import date, timedelta

from weekly import (_palabras_clave, ROMAN, MESES, DIAS, NOMBRE, ASP_ES, CALMA, CASA_TEMA,
                    LUNA_SIGNO, resumen, rango_semana, _fecha, _cuando_corto,
                    _pl, _pos, _casa)

MESES_AB = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep',
            'oct', 'nov', 'dic']
DIAS_MIN = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
SIGNOS_EN = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
             'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
ELEMENTOS = ['Fuego', 'Tierra', 'Aire', 'Agua']          # índice de signo % 4
DIEZ = ['aSol', 'aLuna', 'aMercurio', 'aVenus', 'aMarte', 'aJupiter', 'aSaturno',
        'aUrano', 'aNeptuno', 'aPluton']
RAPIDOS = ['aSol', 'aMercurio', 'aVenus', 'aMarte']
ORDEN_RETRO = ['aMercurio', 'aVenus', 'aMarte', 'aJupiter', 'aSaturno', 'aUrano',
               'aNeptuno', 'aPluton', 'aChiron']

# §6.5 Temas de las casas
CASA_CORTO = ["persona e imagen", "dinero propio", "entorno y palabras",
              "hogar y familia", "placer e hijos", "trabajo y salud",
              "pareja y socios", "dinero compartido", "viajes y estudios",
              "carrera", "amigos y proyectos", "retiro"]
CASA_DE = ["la de su persona y su imagen", "la del dinero propio y sus valores",
           "la del entorno y la comunicación", "la del hogar y la familia",
           "la del placer, los hijos y la creatividad",
           "la del trabajo diario y la salud", "la de la pareja y los socios",
           "la del dinero compartido y la intimidad",
           "la de los viajes, los estudios y las creencias",
           "la de la carrera y la imagen pública",
           "la de los amigos y los proyectos", "la del retiro y lo oculto"]
CASA_HABLA = ["su persona", "su dinero", "su entorno", "su hogar",
              "sus gustos y sus hijos", "su trabajo y su salud",
              "su pareja y sus socios", "el dinero compartido y la intimidad",
              "sus viajes y creencias", "su carrera", "sus amigos y proyectos",
              "su mundo interior"]
# «Su semana en una frase»: foco según la casa que ilumina el Sol
FOCO = ["ocuparse de usted y de su imagen", "ordenar su dinero y lo que valora",
        "conversar, aprender y moverse por su entorno",
        "ordenar la casa —la de adentro y la de afuera—",
        "disfrutar, crear y dedicarse a lo que ama",
        "poner en orden el trabajo, las rutinas y la salud",
        "atender a su pareja, a sus socios y a los demás",
        "sanear las cuentas compartidas y soltar lo que ya murió",
        "ampliar horizontes: estudiar, viajar y creer",
        "ocuparse de su carrera y de sus metas",
        "juntarse con los amigos y empujar proyectos",
        "bajar el ritmo y escucharse por dentro"]
CASA_EN = ["en su persona", "en el dinero propio", "en su entorno", "en el hogar",
           "en sus gustos y afectos", "en el trabajo y la salud", "en la pareja",
           "en el dinero compartido", "en sus viajes y estudios", "en la carrera",
           "en sus proyectos", "en su mundo interior"]

ASP_CORTA = {
    'Conjunction': "El planeta se le monta encima y su tema se vuelve el de la semana.",
    'Sextile': "Puerta entreabierta: la oportunidad está, pero hay que empujarla.",
    'Square': "Aprieta para que usted haga algo: no es castigo, es empujón.",
    'Trine': "Viento a favor: las cosas salen fácil; no se duerma.",
    'Opposition': "Se lo ponen de frente, casi siempre por medio de otro: negocie.",
}
FASE_CORTA = [
    "Semilla del ciclo: empiece algo pequeño y no lo cuente todavía.",
    "El brote rompe la tierra: dé el primer empujón sin mirar atrás.",
    "Primera crisis, y es de acción: decida y actúe; no se quede quieto.",
    "Víspera de Luna Llena: pula y corrija; no empiece nada nuevo.",
    "Todo queda a la vista: mire con claridad y no decida con la marea alta.",
    "La fase del maestro: comparta y enseñe lo que ya aprendió.",
    "Crisis de conciencia: revise, suelte y cierre lo que deba cerrar.",
    "Último suspiro del ciclo: termine, perdone y descanse.",
]
FASE_FRASE = ["sembrar una intención nueva", "dar el primer empujón",
              "decidir y actuar", "pulir lo que ya empezó",
              "ver las cosas con claridad", "compartir lo aprendido",
              "revisar y soltar", "cerrar ciclo y descansar"]

# §6.6 «Qué hacer» del tablero (≤ 36 caracteres)
HACER = {
    'aMercurio': {'retro': "Relea antes de firmar o enviar.",
                  'R': "Respalde, confirme y relea.",
                  'D': "Retome trámites y conversaciones."},
    'aVenus': {'retro': "No decida en amor ni en gastos.",
               'R': "Aplace compras y cambios de imagen.",
               'D': "Ya puede comprometerse o comprar."},
    'aMarte': {'retro': "No pelee; mida sus fuerzas.",
               'R': "Frene la prisa y evite peleas.",
               'D': "Retome lo frenado, con estrategia."},
    'aJupiter': {'retro': "Consolide antes de crecer más.",
                 'R': "No prometa de más; consolide.",
                 'D': "Retome planes, estudios y viajes."},
    'aSaturno': {'retro': "Termine lo pendiente y ordene.",
                 'R': "Revise compromisos y cimientos.",
                 'D': "Retome lo detenido, a paso firme."},
    'aUrano': {'retro': "No rompa nada en caliente.",
               'R': "Madure el cambio antes de darlo.",
               'D': "Dé el salto que venía aplazando."},
    'aNeptuno': {'retro': "Mire la realidad sin maquillaje.",
                 'R': "Desconfíe de sus espejismos.",
                 'D': "Lea la letra chica antes de firmar."},
    'aPluton': {'retro': "Suelte el control y los apegos.",
                'R': "Revise apegos, miedos y obsesiones.",
                'D': "Reconstruya; no se desquite."},
    'aChiron': {'retro': "Hable lo que duele, sin reproches.",
                'R': "Atienda su herida antes que otras.",
                'D': "Enseñe desde lo que ya sanó."},
}
# Ejemplos aprobados por casa (tienen prioridad sobre la tabla general)
HACER_CASA = {
    ('aSaturno', 'D', 8): "Retome trámites de dinero detenidos.",
    ('aUrano', 'retro', 10): "No renuncie en caliente.",
    ('aMercurio', 'retro', 2): "Atención a retrasos en pagos y cobros.",
}

CLAVE_FAVOR = {'aSol': "muéstrese y pida lo que quiere.",
               'aLuna': "buen día para la familia y el corazón.",
               'aAsc': "buen día para citas y presentaciones."}
CLAVE_CALMA = {'aSol': "no se imponga ni discuta por orgullo.",
               'aLuna': "no decida con la emoción revuelta.",
               'aAsc': "ceda un poco; no todo es contra usted."}
CERO_ELEM = {'Fuego': ("el entusiasmo lo pone usted.", "Busque su propio impulso"),
             'Tierra': ("cuide lo práctico.", "Ponga los pies en la tierra"),
             'Aire': ("pregunte antes de suponer.", "Hable antes de suponer"),
             'Agua': ("no deje el corazón por fuera.", "No olvide el corazón")}
CONSEJO_TXT = {
    "Anote, mida y cumpla": "Mucho fuego y poca tierra: lo que no quede escrito y con fecha se lo lleva el viento.",
    "Termine antes de empezar": "Con tanto planeta en Tierra, lo que rinde es cerrar pendientes, no abrir frentes.",
    "Converse, pero decida": "Las ideas sobran esta semana; lo que falta es escoger una y sostenerla.",
    "Cuide su energía": "Todo se siente más: no cargue con lo ajeno y duerma lo que deba dormir.",
    "Escoja sus batallas": "Hay impulso de sobra; gástelo en lo que de verdad le importa.",
    "Busque su propio impulso": "Sin planetas en Fuego nadie lo va a empujar: el primer paso lo da usted.",
    "Ponga los pies en la tierra": "Sin planetas en Tierra es fácil volar: aterrice cada idea en una tarea.",
    "Hable antes de suponer": "Sin planetas en Aire se supone mucho y se pregunta poco: pregunte.",
    "No olvide el corazón": "Sin planetas en Agua todo se vuelve trámite: póngale afecto a lo que haga.",
    "Reparta bien sus fuerzas": "El cielo está equilibrado: un poco de todo y nada en exceso.",
}


def recorta(texto, maximo):
    """Recorta en la última oración completa que quepa en `maximo` caracteres."""
    t = ' '.join((texto or '').split())
    if len(t) <= maximo:
        return t
    return resumen(t, min(120, maximo // 2), maximo)


_STOP = set("esta este toda todas como casa gente para una la se que ahora hasta "
            "cada alguna mucha tanta ella de entre sobre desde durante mientras "
            "aunque porque contra bajo ante tras nada poca otra cierta dicha "
            "misma aquella".split())
_START = re.compile(r'^(no |buen[ao]? |es (época|el momento|tiempo|una? (buen|muy|'
                    r'excelente|magn))|época |tiempo de |momento )', re.I)
_COLA = (' y', ' o', ' es decir', ' si necesita', ' pero', ' para ello', ' que',
         ' de', ' a', ' en', ' con', ' sin', ' por', ' para', ' ni', ' e', ' u')


def _imper(f):
    g = f.lstrip('¿¡"«(').strip()
    if _START.match(g):
        return True
    w = re.split(r'[\s,;:]', g, 1)[0].lower()
    if len(w) < 3 or w in _STOP or not w.isalpha():
        return False
    return w.endswith(('e', 'a'))


def _clausula(f, lo, hi):
    """Corta una oración en una pausa (, ; :) dejando una idea completa."""
    if len(f) <= hi:
        return f
    cortes = [m.start() for m in re.finditer(r'[;:,]', f[:hi + 1]) if m.start() >= lo]
    for cut in reversed(cortes):
        c = f[:cut].rstrip(' ,;:')
        if not c.lower().endswith(_COLA):
            return c + '.'
    return None


def corta(texto, lo=30, hi=90, skip=0, n=10):
    """Frase breve y accionable tomada TAL CUAL de la base de Mauricio Puerta:
    la primera oración en imperativo (consejo) que quepa entre lo y hi
    caracteres; si es larga, se corta en una pausa. Nunca inventa texto."""
    t = ' '.join((texto or '').split())
    if not t:
        return ''
    fr = [f.strip() for f in re.split(r'(?<=[.!?])\s+', t) if len(f.strip()) > 12]
    if not fr:
        return ''
    cand = fr[skip:skip + n] or fr[:n]
    for solo_imp in (True, False):
        for f in cand:
            if solo_imp and not _imper(f):
                continue
            c = _clausula(f, lo, hi)
            if c and len(c) >= lo:
                return c[0].upper() + c[1:]
    f = cand[0]
    return f[:f.rfind(' ', 0, hi)].rstrip(' ,;:') + '…'


def _lista(nombres):
    nombres = list(nombres)
    if len(nombres) <= 1:
        return ''.join(nombres)
    return ', '.join(nombres[:-1]) + ' y ' + nombres[-1]


def _fecha_ab(iso):
    y, m, d = _fecha(iso)
    return "%d %s %d" % (d, MESES_AB[m - 1], y)


def _elem_counts(planets):
    by = {p['key']: p for p in planets}
    cnt = dict((e, 0) for e in ELEMENTOS)
    keys = dict((e, []) for e in ELEMENTOS)
    mods = [0, 0, 0]
    for k in DIEZ:
        if k in by:
            i = SIGNOS_EN.index(by[k]['sign'])
            cnt[ELEMENTOS[i % 4]] += 1
            keys[ELEMENTOS[i % 4]].append(k)
            mods[i % 3] += 1
    return cnt, keys, mods


def _elementos(data):
    ct, keys, mods = _elem_counts(data['transit']['planets'])
    cn, _, _ = _elem_counts(data['natal']['planets'])
    orden = sorted(ELEMENTOS, key=lambda e: -ct[e])
    e1, e2 = orden[0], orden[1]
    ceros = [e for e in ELEMENTOS if ct[e] == 0]
    if ct['Fuego'] >= 4 and ct['Tierra'] <= 1:
        fr, cons = "sobran las ganas, falta el aterrizaje.", "Anote, mida y cumpla"
    elif ct['Tierra'] >= 4:
        fr, cons = "semana para construir paso a paso.", "Termine antes de empezar"
    elif ct['Aire'] >= 4:
        fr, cons = "mucha palabra y mucha idea: elija una.", "Converse, pero decida"
    elif ct['Agua'] >= 4:
        fr, cons = "semana sensible: escuche lo que siente.", "Cuide su energía"
    elif ct['Fuego'] >= 4:
        fr, cons = "mucho impulso: escoja bien sus batallas.", "Escoja sus batallas"
    elif ceros:
        fr, cons = ("sin planetas en %s, %s" % (ceros[0], CERO_ELEM[ceros[0]][0]),
                    CERO_ELEM[ceros[0]][1])
    else:
        fr, cons = "cielo repartido, de todo un poco.", "Reparta bien sus fuerzas"
    frase = "%d planeta%s en %s y %d en %s: %s" % (
        ct[e1], '' if ct[e1] == 1 else 's', e1, ct[e2], e2, fr)
    return {'trans': ct, 'natal': cn, 'glifos': keys, 'mods': mods,
            'frase': frase, 'consejo': (cons, CONSEJO_TXT.get(cons, ''))}


def _agenda(data, snap):
    """7 listas (lunes→domingo) de eventos en orden cronológico. Cada evento:
    {jd, time, prio, red, icon:('planet',key)|('phase',elong), parts:[...]}
    parts = cadenas o tuplas ('sign', idx) / ('asp', type)."""
    wk = data['week']
    base = date(*_fecha(wk['start']))
    dias = [[] for _ in range(7)]

    def put(ev, e):
        i = (date(*_fecha(ev['date'])) - base).days
        if 0 <= i < 7:
            e['jd'] = ev['jd']
            e['time'] = ev['time']
            dias[i].append(e)

    sol, luna = snap.get('aSol'), snap.get('aLuna')
    if sol and luna:
        dias[0].append({'jd': -1, 'time': '00:00', 'prio': 0, 'red': False,
                        'icon': ('planet', 'aSol'),
                        'parts': ["Sol en %s " % sol['sign_es'],
                                  ('sign', SIGNOS_EN.index(sol['sign'])),
                                  ", Luna en %s " % luna['sign_es'],
                                  ('sign', SIGNOS_EN.index(luna['sign']))]})
    for s in data['stations']:
        put(s, {'prio': 1, 'red': True, 'icon': ('planet', s['key']),
                'parts': ["%s %s" % (s['name'], 'se vuelve retrógrado'
                                     if s['kind'] == 'retrograde' else 'queda directo')]})
    for f in data['phases']:
        put(f, {'prio': 2, 'red': False, 'icon': ('phase', f['elong']),
                'parts': ["%s en " % f['name'],
                          ('sign', SIGNOS_EN.index(f['moon']['sign'])),
                          " · %s" % _casa(f['moon']['natal_house'])]})
    for a in list(data['aspects']) + list(data['moon_aspects']):
        if not a.get('exact'):
            continue
        put(a, {'prio': 3, 'red': False, 'icon': ('planet', a['transit']),
                'parts': (["%s " % NOMBRE[a['transit']], ('asp', a['type']),
                           " sobre su %s" % NOMBRE[a['natal']]]
                          if a['type'] == 'Conjunction' else
                          ["%s en %s " % (NOMBRE[a['transit']], ASP_ES[a['type']]),
                           ('asp', a['type']), " a su %s" % NOMBRE[a['natal']]])})
    for g in data.get('ingresses', []):
        put(g, {'prio': 5 if g['key'] == 'aLuna' else 4, 'red': False,
                'icon': ('planet', g['key']),
                'parts': ["%s %s %s " % (g['name'], 'R regresa a' if g['retrograde']
                                         else 'entra a', g['sign_es']),
                          ('sign', g['sign_index'])]})
    for d in dias:
        d.sort(key=lambda e: e['jd'])
    return dias


def build_layout(data, interp, name='', city=''):
    """Todo lo que weekly_pdf necesita dibujar (textos ya recortados).
    `city` = lugar de cálculo de la semana (natal o relocalizado)."""
    tr = interp.get('transit', {})
    asp_db = tr.get('aspects', {})
    fb = interp.get('aspect_fallback', {}).get('transit', {})
    wk = data['week']
    snap = {p['key']: p for p in data['transit']['planets']}
    fin = data.get('transit_end', {})
    tg = data['targets']
    f0 = data['phase_start']
    y1, m1, d1 = _fecha(wk['start'])
    y2, m2, d2 = _fecha(wk['end'])
    n_in = data['natal'].get('input', {})
    lugar = (city or '').strip()
    b = date(y1, m1, d1)
    L = {'name': (name or '').strip(),
         'rango': rango_semana(wk['start'], wk['end']),
         'relocated': bool(wk.get('relocated')), 'lugar': lugar,
         'nac_fecha': _fecha_ab((n_in.get('date') or wk['start']).replace('/', '-')),
         'nac_hora': n_in.get('time', ''),
         'sem_inicio': "Lunes %d %s" % (d1, MESES_AB[m1 - 1]),
         'dias': [(b + timedelta(days=i)).day for i in range(7)]}
    if L['relocated']:
        L['nota'] = ("* Carta relocalizada: calculada para las 00:00 del lunes en %s. "
                     "Sus planetas natales no cambian; las casas se calcularon para "
                     "ese lugar." % (lugar or 'el lugar elegido'))
    else:
        L['nota'] = ("* Calculado para las 00:00 del lunes%s, su lugar natal. Si pasa "
                     "la semana en otra ciudad, puede relocalizar el reporte: el "
                     "cielo es el mismo, pero cae en otras casas de su vida."
                     % ((" en %s" % lugar) if lugar else ""))

    sol, luna = snap.get('aSol'), snap.get('aLuna')
    hs = sol.get('natal_house', 1) if sol else 1

    # ── Su semana en una frase (≤ 130) ───────────────────────────────────
    pih = tr.get('planet_in_house', {})
    sol_db = pih.get('aSol', {}).get(str(hs), '')
    frase = corta(sol_db, 45, 125) or ("El Sol ilumina esta semana su %s." % _casa(hs))
    L['frase'] = frase

    L['elementos'] = _elementos(data)
    L['agenda'] = _agenda(data, snap)

    # ── Página 2 ─────────────────────────────────────────────────────────
    solo_mes = ("%d al %d de %s" % (d1, d2, MESES[m2 - 1])) if m1 == m2 else \
        ("%d de %s al %d de %s" % (d1, MESES[m1 - 1], d2, MESES[m2 - 1]))
    L['intro'] = ("Este es el cielo de la semana del %s, calculado para las 00:00 del "
                  "lunes y leído sobre su carta natal. Aquí va solo lo esencial: no son "
                  "predicciones absolutas, sino tendencias que nacen del tránsito de "
                  "los planetas en el cielo sobre su carta natal, y que le resultan "
                  "útiles para usarlas a su favor." % solo_mes)

    # texto bajo la barra (§6.4)
    partes = []
    grupos = {}
    for k in ('aJupiter', 'aSaturno', 'aUrano', 'aNeptuno', 'aPluton', 'aChiron'):
        if k in snap and k in fin and snap[k]['natal_house'] == fin[k]['natal_house']:
            grupos.setdefault(snap[k]['natal_house'], []).append(NOMBRE[k])
    if grupos:
        h, ns = max(grupos.items(), key=lambda kv: len(kv[1]))
        partes.append("Los planetas lentos casi no se mueven: %s %s toda la semana en "
                      "su %s, %s." % (_lista(ns), 'pasan' if len(ns) > 1 else 'pasa',
                                      _casa(h), CASA_DE[h - 1]))
    luna_casas = None
    if luna and 'aLuna' in fin:
        a, bb = luna['natal_house'], fin['aLuna']['natal_house']
        luna_casas = (a, bb, ((bb - a) % 12) + 1)
        if a != bb:
            partes.append("La Luna, en cambio, cruza de la %s a la %s: el lunes le "
                          "habla de %s y el domingo, de %s."
                          % (_casa(a), ROMAN[bb - 1], CASA_HABLA[a - 1], CASA_HABLA[bb - 1]))
    mov = []
    for k in RAPIDOS:
        if k in snap and k in fin and snap[k]['natal_house'] != fin[k]['natal_house']:
            mov.append("%s pasa de su %s a la %s" % (
                _pl(k, not mov), _casa(snap[k]['natal_house']),
                ROMAN[fin[k]['natal_house'] - 1]))
    if mov:
        partes.append(_lista(mov) + ".")
    L['barra_texto'] = ' '.join(partes)

    # fases de la Luna (hasta 3 tarjetas)
    L['fases'] = []
    luna_db = pih.get('aLuna', {})

    def fase_txt(idx, h):
        kw = _palabras_clave(interp, idx)
        t = ("Palabras clave: %s. " % kw) if kw else ""
        return (t + corta(luna_db.get(str(h), ''), 40, 120)).strip()
    for f in data['phases'][:3]:
        h = f['moon']['natal_house']
        L['fases'].append({'titulo': "%s en %s" % (f['name'], f['moon']['sign_es']),
                           'sign': SIGNOS_EN.index(f['moon']['sign']),
                           'fecha': "%s · %s" % (_cuando_corto(f), _casa(h)),
                           'texto': fase_txt(f['index'], h), 'elong': f['elong']})
    if not L['fases']:
        L['fases'].append({'titulo': "La semana transcurre en %s" % f0['name'],
                           'sign': None,
                           'fecha': "toda la semana · sin cambio de fase",
                           'texto': fase_txt(f0['index'], f0['moon']['natal_house']),
                           'elong': f0['elong']})

    # clima de la semana (≤ 380 por tarjeta)
    clima = []
    if sol:
        p1 = "Toda la semana el Sol le ilumina la %s: %s." % (_casa(hs), CASA_TEMA[hs - 1])
        p2 = resumen(sol_db, 120, max(140, 380 - len(p1)))
        clima.append({'key': 'aSol', 'kicker': 'TODA LA SEMANA',
                      'titulo': "El Sol en %s " % sol['sign_es'],
                      'sign': SIGNOS_EN.index(sol['sign']),
                      'titulo2': ", por su %s" % _casa(hs),
                      'paras': [p1, p2] if p2 else [p1]})
    if luna:
        hl = luna['natal_house']
        p1 = "El lunes la Luna está a %s, en su %s, en fase de %s" % (
            _pos(luna), _casa(hl), f0['name'])
        if luna_casas and luna_casas[0] != luna_casas[1]:
            p1 += "; en siete días cruza %d casas, hasta la %s." % (
                luna_casas[2], ROMAN[luna_casas[1] - 1])
        else:
            p1 += "."
        p2 = resumen(luna_db.get(str(hl), ''), 120, max(140, 380 - len(p1)))
        clima.append({'key': 'aLuna', 'kicker': 'LUNES 00:00',
                      'titulo': "La Luna arranca en %s " % luna['sign_es'],
                      'sign': SIGNOS_EN.index(luna['sign']), 'titulo2': "",
                      'paras': [p1, p2] if p2 else [p1]})
    L['clima'] = clima

    # ── Página 3: Sol / Luna / Ascendente ────────────────────────────────
    puntos = []
    rank = {k: i for i, k in enumerate(['aPluton', 'aNeptuno', 'aUrano', 'aSaturno',
                                        'aJupiter', 'aChiron', 'aNoduloNorte', 'aMarte',
                                        'aSol', 'aVenus', 'aMercurio'])}
    for nk in ('aSol', 'aLuna', 'aAsc'):
        if nk not in tg:
            continue
        t = tg[nk]
        item = {'nk': nk, 'nombre': "Su %s" % NOMBRE[nk],
                'pos': "%s " % _pos(t), 'sign': SIGNOS_EN.index(t['sign']),
                'pos2': (" · %s" % _casa(t['natal_house'])) if nk != 'aAsc' else ""}
        cands = [a for a in data['aspects'] if a['natal'] == nk]
        cands.sort(key=lambda a: (0 if a['exact'] else 1, rank.get(a['transit'], 99)))
        if not cands:
            cands = [a for a in data['moon_aspects'] if a['natal'] == nk]
        if cands:
            a = cands[0]
            cuando = _cuando_corto(a) if a['exact'] else "toda la semana"
            item['evento'] = {'tk': a['transit'], 'typ': a['type'],
                              'texto': "%s en %s · %s" % (NOMBRE[a['transit']],
                                                          ASP_ES[a['type']], cuando)}
            item['clave'] = ''
            item['db'] = (asp_db.get(a['transit'], {}).get(a['type'], {}).get(nk)
                          or fb.get(a['type'], ''))
        else:
            item['evento'] = None
            item['calma'] = "Semana tranquila para su %s" % NOMBRE[nk]
            item['clave'] = ''
            item['db'] = ("Ningún planeta forma un aspecto exacto con su %s natal "
                          "esta semana." % NOMBRE[nk])
        puntos.append(item)
    L['puntos'] = puntos

    # ── Tablero de retrógrados (hasta 7 filas) ───────────────────────────
    filas = []
    st = {s['key']: s for s in data['stations']}
    retro0 = set(data.get('retro_now', []))
    orden = [s['key'] for s in data['stations']] + \
        [k for k in ORDEN_RETRO if k in retro0 and k not in st]
    for k in orden[:7]:
        s = st.get(k)
        if s:
            estado = 'R' if s['kind'] == 'retrograde' else 'D'
            h = s['at']['natal_house']
            lab = "%s %s" % (DIAS_MIN[s['weekday']], s['time'])
            hrs = s.get('hours')
        else:
            estado = 'retro'
            h = snap[k]['natal_house'] if k in snap else 1
            lab = ''
            hrs = None
        filas.append({'key': k, 'name': NOMBRE[k], 'estado': estado,
                      'estado_txt': {'R': 'se vuelve R', 'D': 'queda directo',
                                     'retro': 'retrógrado'}[estado],
                      'hours': hrs, 'label': lab,
                      'casa': _casa(h), 'casa_corto': CASA_CORTO[h - 1],
                      'hacer': corta(pih.get(k, {}).get(str(h), ''), 24, 66)
                      or HACER[k][estado]})
    directos = [NOMBRE[k] for k in ORDEN_RETRO if k not in orden]
    if not filas:
        dtxt = "Todos los planetas avanzan directos esta semana"
    elif directos:
        dtxt = "%s %s toda la semana" % (_lista(directos), 'avanzan directos'
                                         if len(directos) > 1 else 'avanza directo')
    else:
        dtxt = ""
    L['tablero'] = {'filas': filas, 'directos': dtxt}

    # ── Tres claves ──────────────────────────────────────────────────────
    todos = [a for a in list(data['aspects']) + list(data.get('moon_all', []))
             if a.get('exact')]
    todos.sort(key=lambda a: (1 if a['transit'] == 'aLuna' else 0, a['jd']))

    def clave(tipos, vacio_t, vacio_x, benef=False):
        for a in todos:
            ok = a['type'] in tipos or (benef and a['type'] == 'Conjunction'
                                        and a['transit'] in ('aVenus', 'aJupiter'))
            if ok:
                tit = "%s %d" % (DIAS[a['weekday']].capitalize(), _fecha(a['date'])[2])
                db = asp_db.get(a['transit'], {}).get(a['type'], {}).get(a['natal'], '')
                tx = "%s en %s a su %s. %s" % (_pl(a['transit'], True), ASP_ES[a['type']],
                                               NOMBRE[a['natal']], corta(db, 30, 95))
                return tit, tx.strip()
        return vacio_t, vacio_x
    fav = clave(('Trine', 'Sextile'), "Sin día señalado",
                "Ningún trígono ni sextil es exacto con su Sol, su Luna o su "
                "Ascendente esta semana.", benef=True)
    cal = clave(('Square', 'Opposition'), "Sin día señalado",
                "Ninguna cuadratura ni oposición es exacta con su Sol, su Luna o su "
                "Ascendente esta semana.")
    c2 = corta(sol_db, 35, 110, skip=2)
    if c2 == frase:
        c2 = corta(sol_db, 35, 110, skip=5)
    cons = ("Sol en su %s" % _casa(hs), c2)
    L['claves'] = [("DÍA A FAVOR", fav[0], fav[1], '#93B096'),
                   ("DÍA PARA IR CON CALMA", cal[0], cal[1], '#C08A7B'),
                   ("CONSEJO DE LA SEMANA", cons[0], cons[1], '#B8863B')]
    return L
