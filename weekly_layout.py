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

# Temas de las casas según Mauricio Puerta (rueda «Carta_info»)
CASA_CORTO = ["personalidad", "dinero", "mente inferior", "hogar y padres",
              "hijos y amor", "salud y trabajo", "matrimonio y socios",
              "transformación", "mente superior", "misión y profesión",
              "amigos y esperanzas", "karmas"]
CASA_DE = ["la de la personalidad y el carácter",
           "la del dinero y la seguridad material",
           "la de la mente inferior, los hermanos y los viajes cortos",
           "la del hogar, los padres y la intimidad",
           "la de los hijos, la diversión y el amor",
           "la de la salud y el trabajo",
           "la del matrimonio y los socios",
           "la de la transformación, las herencias y el sexo",
           "la de la mente superior, la filosofía y los viajes largos",
           "la de la misión y la profesión",
           "la de los amigos y las esperanzas",
           "la de los karmas y las deudas del destino"]
CASA_HABLA = ["su personalidad", "su dinero", "su mente y sus hermanos",
              "su hogar y sus padres", "sus hijos y sus amores",
              "su salud y su trabajo", "su matrimonio y sus socios",
              "sus transformaciones", "su mente superior y sus viajes largos",
              "su misión y su profesión", "sus amigos y sus esperanzas",
              "sus karmas"]

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


# Verbos en imperativo (de usted) que usa Mauricio Puerta al aconsejar.
_IMPER = set("""sea busque sepa trate desarrolle controle cuídese observe deje salga vigile
procure revise interésese aprenda haga cuide piense mire mejore tenga aumente estudie
recuerde esté canalice saque conozca calme siéntase dedíquese vea sienta ponga aproveche
refuerce cambie abra comparta póngale acérquese viaje libérese prepárese espere acepte
conózcase tome evite expanda analice dé realice goce estimule trabaje comprenda déle
invierta hágase renueve asesórese diviértase mírese aclare comience ensaye transforme
armonice confíe descargue dése medite eleve fortalezca arregle ayúdese reflexione reúnase
bucee asegúrese esfuércese termine atrévase adquiera use relájese organice incremente lleve
ayude viva utilice conéctese ordene despierte fíjese escuche invite resuelva elimine encare
modernice cultive escriba compréndase préstele maneje construya intente crea muéstrese venza
colabore compre planifique déjese exprese refresque vaya obsérvese continúe actúe encuentre
respete establezca active asegure eche comprométase ábrale visualícese relaciónese coopere
hable concrete decida concéntrese converse visualice cumpla atienda recapacite posponga
agilice dirija muévase enfrente promueva tómese defina acéptese amplíe pida regenere
aprovéchelo baje profundice comuníquele acentúe embellezca obre infórmese demuestre
enriquezca respire ábrase entienda mantenga hágalo estabilice oiga descubra planee
solucione pruebe descarte dialogue equilibre suelte evalúe contémplese sépase domínese
brille enfóquese evalúese ocúpese aléjese olvídese apóyese apóyele dele empiece
inviértale ahorre gaste cuente exija perdone prevéngase protéjase sincérese ubíquese""".split())
_PRONOM = re.compile(r'^(no (se |le |lo |la |les |los |me )?[a-záéíóúñ]+|'
                     r'(buen|excelente|magnífico) momento para|es (el )?momento (de|para)|'
                     r'es (buena )?época (de|para))\b', re.I)
_ENCL = re.compile(r'^[a-záéíóúñ]*[áéíó][a-zñ]*(se|le|lo|la|les|los|me|selo|sela)$')


def _imper(f):
    """¿La oración es un consejo (imperativo de usted)?"""
    g = f.lstrip('¿¡"«(').strip()
    if _PRONOM.match(g):
        return True
    w = re.split(r'[\s,;:]', g, 1)[0].lower()
    return w in _IMPER or bool(_ENCL.match(w))


def _ok(f):
    """Descarta oraciones con restos de OCR o referencias técnicas."""
    return not re.search(r'[|()\[\]]|\.\.\.|Nodo|Nódulo|Más o menos cada', f)


def corta(texto, lo=30, hi=90, skip=0, n=12):
    """Consejo breve tomado TAL CUAL de la base de Mauricio Puerta: la primera
    oración en imperativo que quepa entre lo y hi caracteres (o su primera
    cláusula, cortada en punto y coma). Nunca inventa texto: si no encuentra
    un consejo claro, devuelve ''."""
    t = ' '.join((texto or '').split())
    if not t:
        return ''
    fr = [f.strip() for f in re.split(r'(?<=[.!?])\s+', t) if len(f.strip()) > 12]
    cand = [f for f in (fr[skip:skip + n] or fr[:n]) if _ok(f) and _imper(f)]
    for f in cand:                                   # oración completa
        if lo <= len(f) <= hi:
            return f[0].upper() + f[1:]
    for f in cand:                                   # primera cláusula (;)
        parts = [p.strip() for p in f.split(';')]
        if len(parts) > 1 and lo <= len(parts[0]) <= hi:
            return parts[0][0].upper() + parts[0][1:] + '.'
    for f in cand:                                   # algo más largo
        if lo <= len(f) <= int(hi * 1.35):
            return f[0].upper() + f[1:]
    return ''


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
    frase = corta(sol_db, 45, 125) or corta(sol_db, 30, 125, skip=0, n=40) \
        or ("El Sol ilumina esta semana su %s." % _casa(hs))
    L['frase_fuente'] = "Según el tránsito del Sol por su %s" % _casa(hs)
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

    # ── Los tránsitos más importantes de la semana ──────────────────────
    # Peso = planeta en tránsito × punto natal × aspecto × cercanía.
    PESO_T = {'aPluton': 10, 'aNeptuno': 9, 'aUrano': 9, 'aSaturno': 8,
              'aJupiter': 7, 'aChiron': 6, 'aNoduloNorte': 5, 'aMarte': 5,
              'aSol': 4, 'aVenus': 3, 'aMercurio': 3}
    rk_ = (data.get('ruler') or {}).get('key')
    PESO_N = {'aSol': 3, 'aLuna': 3, 'aAsc': 3, 'aMc': 2.5}
    PESO_A = {'Conjunction': 1.0, 'Opposition': 0.9, 'Square': 0.9,
              'Trine': 0.7, 'Sextile': 0.55}
    NOMBRE_N = dict(NOMBRE, aMc='Medio Cielo')

    def peso(a):
        pn = PESO_N.get(a['natal'], 2.5 if a['natal'] == rk_ else
                        (2.0 if a['natal'] in ('aMercurio', 'aVenus', 'aMarte') else 1.5))
        cerca = 1.0 if a.get('exact') else max(0.25, 0.75 - a.get('orb', 0) / 3.0)
        return PESO_T.get(a['transit'], 1) * pn * PESO_A.get(a['type'], 0.5) * cerca

    cands = [a for a in data.get('all_aspects', []) if a['transit'] != 'aLuna']
    cands.sort(key=peso, reverse=True)
    top = []
    for a in cands:
        db = asp_db.get(a['transit'], {}).get(a['type'], {}).get(a['natal'], '')
        if not db and a['natal'] == 'aMc':
            db = asp_db.get(a['transit'], {}).get(a['type'], {}).get('aMc', '')
        if not db:
            continue
        cuando = ("exacto el " + _cuando_corto(a)) if a.get('exact') else \
            ("toda la semana, %s" % ("acercándose" if a.get('applying') else "separándose"))
        top.append({'key': a['transit'], 'typ': a['type'],
                    'linea': "Tránsito: %s en %s a su %s natal · %s" % (
                        NOMBRE[a['transit']], ASP_ES[a['type']], NOMBRE_N[a['natal']], cuando),
                    'texto': corta(db, 50, 170) or resumen(db, 80, 170)})
        if len(top) == 3:
            break
    # Planetas lentos (y Marte) que transitan su Casa I: se agregan al final
    # si queda espacio en la página.
    for k in ('aPluton', 'aNeptuno', 'aUrano', 'aSaturno', 'aJupiter', 'aChiron', 'aMarte'):
        p_ = snap.get(k)
        if p_ and p_['natal_house'] == 1:
            db = pih.get(k, {}).get('1', '')
            top.append({'key': k, 'typ': None,
                        'linea': "Tránsito: %s en %s por su Casa I, la de la personalidad" % (
                            NOMBRE[k], p_['sign_es']),
                        'texto': corta(db, 50, 170) or resumen(db, 80, 170)})
    L['casa1'] = top[:5]

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
                              'texto': "Tránsito: %s en %s · %s" % (
                                  NOMBRE[a['transit']], ASP_ES[a['type']], cuando)}
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

    # ── Regente de la carta ──────────────────────────────────────────────
    r = data.get('ruler')
    if not r:
        # respaldo (si astro.py no entregó el bloque 'ruler')
        _REG = {'Aries': 'aMarte', 'Taurus': 'aVenus', 'Gemini': 'aMercurio',
                'Cancer': 'aLuna', 'Leo': 'aSol', 'Virgo': 'aChiron', 'Libra': 'aVenus',
                'Scorpio': 'aPluton', 'Sagittarius': 'aJupiter', 'Capricorn': 'aSaturno',
                'Aquarius': 'aUrano', 'Pisces': 'aNeptuno'}
        asc = data['natal']['angles']['asc']
        rk = _REG.get(asc['sign'])
        sp = snap.get(rk)
        if sp:
            r = {'key': rk, 'name': NOMBRE[rk], 'asc_sign_es': asc['sign_es'],
                 'sign': sp['sign'], 'sign_es': sp['sign_es'], 'deg': sp['deg'],
                 'natal_house': sp['natal_house'], 'retrograde': sp['retrograde'],
                 'end_house': fin.get(rk, {}).get('natal_house'),
                 'stations': [x for x in data['stations'] if x['key'] == rk],
                 'ingresses': [x for x in data.get('ingresses', []) if x['key'] == rk],
                 'aspects': [a for a in data['aspects'] if a['transit'] == rk]}
    L['regente'] = None
    if r:
        k = r['key']
        h = r['natal_house']
        estado = 'retrógrado' if r['retrograde'] else 'directo'
        movs = []
        for s_ in r['stations']:
            movs.append("%s %s" % ('se vuelve retrógrado' if s_['kind'] == 'retrograde'
                                   else 'queda directo', _cuando_corto(s_)))
            estado = 'retrógrado' if s_['kind'] == 'retrograde' else 'directo'
            if not r['retrograde'] and s_['kind'] == 'retrograde':
                estado = 'directo'
        for g in r['ingresses']:
            movs.append("entra a %s el %s" % (g['sign_es'], _cuando_corto(g)))
        if r.get('end_house') and r['end_house'] != h:
            movs.append("pasa a su %s" % _casa(r['end_house']))
        asps = []
        for a in r['aspects'][:3]:
            asps.append({'typ': a['type'],
                         'txt': "%s a su %s natal%s" % (
                             ASP_ES[a['type']], NOMBRE.get(a['natal'], 'Medio Cielo')
                             if a['natal'] != 'aMc' else 'Medio Cielo',
                             (" · " + _cuando_corto(a)) if a.get('exact') else "")})
        txt = resumen(pih.get(k, {}).get(str(h), ''), 80, 230)
        L['regente'] = {
            'key': k, 'name': r['name'],
            'pos': "Rige su Ascendente en %s" % r['asc_sign_es'],
            'linea': "Tránsito: %s en %d° de %s · %s · %s" % (
                r['name'], r['deg'], r['sign_es'], _casa(h), estado),
            'sign': SIGNOS_EN.index(r['sign']),
            'movs': movs, 'aspectos': asps, 'texto': txt}

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
        sp_ = snap.get(k, {})
        sub = "en %s" % sp_.get('sign_es', '') if sp_ else ""
        re_ = (data.get('retro_end') or {}).get(k)
        if re_ and estado in ('retro', 'R'):
            y_, m_, d_ = _fecha(re_['date'])
            anio = "" if y_ == y1 else " %d" % y_
            sub += " · directo el %d %s%s" % (d_, MESES_AB[m_ - 1], anio)
        sidx = SIGNOS_EN.index(sp_['sign']) if sp_ else None
        filas.append({'key': k, 'name': NOMBRE[k], 'estado': estado, 'sub': sub,
                      'sub_sign': sidx,
                      'estado_txt': {'R': 'se vuelve R', 'D': 'queda directo',
                                     'retro': 'retrógrado'}[estado],
                      'hours': hrs, 'label': lab,
                      'casa': _casa(h), 'casa_corto': CASA_CORTO[h - 1],
                      'hacer': corta(pih.get(k, {}).get(str(h), ''), 20, 70)
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
                tx = ("Tránsito de %s en %s a su %s natal." % (
                    _pl(a['transit']), ASP_ES[a['type']], NOMBRE[a['natal']])
                      ).replace(" de el ", " del ")
                c_ = corta(db, 25, 95)
                return tit, (tx + (" " + c_ if c_ else "")).strip()
        return vacio_t, vacio_x
    fav = clave(('Trine', 'Sextile'), "Sin día señalado",
                "Ningún trígono ni sextil es exacto con su Sol, su Luna o su "
                "Ascendente esta semana.", benef=True)
    cal = clave(('Square', 'Opposition'), "Sin día señalado",
                "Ninguna cuadratura ni oposición es exacta con su Sol, su Luna o su "
                "Ascendente esta semana.")
    c2 = ''
    for sk in (1, 2, 3, 5, 8):
        c2 = corta(sol_db, 30, 110, skip=sk)
        if c2 and c2 != frase:
            break
    cons = ("Tránsito del Sol por su %s" % _casa(hs),
            c2 or "El foco de la semana está en %s." % CASA_TEMA[hs - 1])
    L['claves'] = [("DÍA A FAVOR", fav[0], fav[1], '#93B096'),
                   ("DÍA PARA IR CON CALMA", cal[0], cal[1], '#C08A7B'),
                   ("CONSEJO DE LA SEMANA", cons[0], cons[1], '#B8863B')]
    return L
