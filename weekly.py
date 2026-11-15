# -*- coding: utf-8 -*-
"""
weekly.py — Textos y armado del Reporte de Tránsitos Semanales (resumido).

Recibe el dict de astro.compute_weekly() y la base de interpretaciones
(interpretations_es.json) y devuelve los bloques que report.render_pdf /
render_docx ya saben dibujar:

    pre_blocks → "Su semana de un vistazo" + agenda día por día
    sections   → clima de la semana, Sol / Luna / Ascendente natales,
                 planetas que cambian de rumbo y fases de la Luna
    closing    → palabras finales

Los textos de los aspectos y del Sol por casa salen de la base de tránsitos
de Mauricio Puerta (bloque "transit"), resumidos. El resto está escrito en su
mismo tono: directo, práctico y de usted.
"""
import re

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
DIAS_AB = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

NOMBRE = {
    'aSol': 'Sol', 'aLuna': 'Luna', 'aMercurio': 'Mercurio', 'aVenus': 'Venus',
    'aMarte': 'Marte', 'aJupiter': 'Júpiter', 'aSaturno': 'Saturno',
    'aUrano': 'Urano', 'aNeptuno': 'Neptuno', 'aPluton': 'Plutón',
    'aChiron': 'Quirón', 'aNoduloNorte': 'Nodo Norte', 'aAsc': 'Ascendente',
}
ART = {'aSol': 'El', 'aLuna': 'La', 'aNoduloNorte': 'El'}      # resto sin artículo
LENTOS = ('aJupiter', 'aSaturno', 'aUrano', 'aNeptuno', 'aPluton', 'aChiron',
          'aNoduloNorte')

ASP_ES = {'Conjunction': 'conjunción', 'Sextile': 'sextil', 'Square': 'cuadratura',
          'Trine': 'trígono', 'Opposition': 'oposición'}
# cómo se dice el aspecto dentro de una frase
ASP_FRASE = {'Conjunction': 'en conjunción con', 'Sextile': 'en sextil a',
             'Square': 'en cuadratura a', 'Trine': 'en trígono a',
             'Opposition': 'en oposición a'}
ASP_CLAVE = {
    'Conjunction': "La conjunción es el aspecto más fuerte de todos: el planeta se "
                   "le monta encima y lo que él representa se vuelve el tema de la semana.",
    'Sextile': "El sextil es una puerta entreabierta: la oportunidad está, pero hay "
               "que empujarla; si usted no se mueve, pasa de largo.",
    'Square': "La cuadratura aprieta y es para eso: incomoda con el fin de que usted "
              "haga algo. No es castigo, es el empujón que le estaba faltando.",
    'Trine': "El trígono es viento a favor: las cosas salen sin tanto esfuerzo. El "
             "único riesgo es dormirse en la comodidad y no aprovecharlo.",
    'Opposition': "La oposición le pone el asunto de frente, casi siempre a través "
                  "de otra persona que hace de espejo. Toca negociar, no imponerse.",
}

OBJETIVO = {
    'aSol': ("su Sol natal", "su identidad, su vitalidad y aquello que vino a ser"),
    'aLuna': ("su Luna natal", "sus emociones, su hogar y lo que necesita para sentirse seguro"),
    'aAsc': ("su Ascendente", "su cuerpo, su imagen y la manera como enfrenta la vida"),
}
SEC_TITULO = {
    'aSol': "Lo que el cielo le hace a su Sol",
    'aLuna': "Lo que el cielo le hace a su Luna",
    'aAsc': "Lo que el cielo le hace a su Ascendente",
}
CALMA = {
    'aSol': "Ningún planeta le hace un aspecto exacto a su Sol natal en estos siete "
            "días. No es que no pase nada: es que el cielo no le está exigiendo nada "
            "nuevo a su identidad ni a sus metas. Semana para sostener el rumbo que ya "
            "trae, sin inventarse crisis que no existen.",
    'aLuna': "Su Luna natal no recibe aspectos exactos de los planetas esta semana. "
             "En lo emocional y lo familiar el cielo le da un respiro: aprovéchelo para "
             "descansar, ordenar la casa y atender a los suyos sin dramas agregados.",
    'aAsc': "Su Ascendente pasa la semana sin aspectos exactos. Ni su cuerpo ni su "
            "imagen están bajo presión: buena semana para mantener sus rutinas y "
            "cuidarse sin andar a las carreras.",
}

# De qué se ocupa cada casa, con los nombres que usa Mauricio Puerta
# (rueda «Carta_info»: I Personalidad, II Dinero, III Mente inferior, IV Hogar,
#  V Hijos, VI Salud y trabajo, VII Matrimonio, VIII Transformación,
#  IX Mente superior, X Misión, XI Amigos, XII Karmas).
CASA_TEMA = [
    "su personalidad, su carácter y la forma de su cuerpo",
    "el dinero, la libertad que da el dinero y la seguridad material",
    "la mente inferior: la enseñanza, la literatura, los hermanos y los viajes cortos",
    "los padres, la intimidad, el hogar, la casa, las tierras y el país natal",
    "los hijos, todo lo creado por usted mismo, la diversión y el amor",
    "la salud, el trabajo y los servidores",
    "el matrimonio, la compañía, los socios y la armonía",
    "la transformación, las herencias, el sexo, los poderes ocultos latentes y las ganancias y pérdidas",
    "la mente superior: la religión, la filosofía y los viajes largos",
    "la misión, su lugar en la sociedad, la profesión y la ambición",
    "los amigos, las esperanzas, los deseos y la fraternidad",
    "los karmas, las deudas del destino, las limitaciones y lo inevitable",
]

# El tono que le pone cada signo a la Luna
LUNA_SIGNO = {
    'Aries': "impaciente, valiente y con ganas de empezar algo ya",
    'Taurus': "tranquila, sensual y terca, que pide comodidad y cosas concretas",
    'Gemini': "curiosa, conversadora e inquieta, con la cabeza en diez asuntos",
    'Cancer': "sensible y hogareña, que pide nido, familia y memoria",
    'Leo': "orgullosa, generosa y dramática, que pide aplauso y corazón",
    'Virgo': "ordenada, crítica y servicial, que pide método y detalle",
    'Libra': "diplomática y sociable, que pide armonía, pareja y acuerdos",
    'Scorpio': "intensa y reservada, que no acepta medias tintas",
    'Sagittarius': "optimista y andariega, que pide horizonte y franqueza",
    'Capricorn': "seria y responsable, que pide resultados y poca queja",
    'Aquarius': "desapegada y original, que pide libertad, amigos e ideas nuevas",
    'Pisces': "soñadora y compasiva, que pide silencio, fe y descanso",
}

# ── Las ocho fases de la Luna ───────────────────────────────────────────
FASE_CLAVE_DB = ['Fase De Luna Nueva', 'Fase De Luna Creciente', 'Fase Cuarto Creciente',
                 'Fase Lunar Gibosa', 'Fase De Luna Llena', 'Fase Lunar Menguante',
                 'Fase Lunar Cuarto Menguante', 'Fase Lunar Balsámica']
FASE_TXT = [
    "La Luna Nueva es la semilla: la Luna está pegada al Sol y no se ve, de modo que "
    "nadie ve tampoco lo que usted está por comenzar. Es el momento de sembrar una "
    "intención, no de mostrar resultados. Empiece algo, aunque sea pequeño, y no se "
    "lo cuente a todo el mundo todavía.",
    "La Luna Creciente es el brote que rompe la tierra. Lo que se sembró en la Luna "
    "Nueva pide ahora el primer empujón y aparecen las primeras resistencias, sobre "
    "todo las de sus viejas costumbres. Enfóquese, junte sus recursos y siga "
    "adelante sin mirar atrás.",
    "El Cuarto Creciente es la primera crisis del ciclo: media Luna iluminada y media "
    "a oscuras. Es crisis de acción, no de pensamiento. Lo que usted venía planeando "
    "exige una decisión y un acto concreto; si se queda quieto, pierde el impulso.",
    "La Luna Gibosa es la víspera de la Luna Llena: ya casi está redonda, pero le "
    "falta. Es tiempo de pulir, corregir y perfeccionar lo que tiene entre manos. "
    "No empiece nada nuevo; mejore lo que ya empezó y pregúntese para qué lo hace.",
    "La Luna Llena es la fase más importante de todas: el Sol y la Luna se miran de "
    "frente y todo queda a la vista. Se recoge lo sembrado, las emociones se "
    "desbordan y las relaciones muestran lo que de verdad son. Mire con claridad "
    "antes de reaccionar, y no tome decisiones con la marea alta.",
    "La Luna Menguante —o diseminante— es la del maestro: ya vio lo que había que "
    "ver y ahora le corresponde compartirlo. Semana para comunicar, enseñar, "
    "difundir y entregar a otros lo que aprendió, en vez de guardárselo.",
    "El Cuarto Menguante es la segunda crisis del ciclo, pero esta es de conciencia. "
    "Lo que ya no sirve se nota y pesa. Revise, reevalúe y suelte: cierre lo que deba "
    "cerrar y bote lo que deba botar, sin sentimentalismos.",
    "La Luna Balsámica es el último suspiro del ciclo, la oscuridad antes de la "
    "nueva semilla. No es momento de comenzar sino de terminar, perdonar, descansar "
    "y quedarse callado. Lo que usted deje atrás ahora le hace espacio a lo que viene.",
]
FASE_ACCION = [
    "sembrar una intención nueva", "dar el primer empujón", "decidir y actuar",
    "pulir y ajustar", "ver con claridad y recoger lo sembrado",
    "compartir lo aprendido", "revisar y soltar", "cerrar el ciclo y descansar",
]

# ── Planetas que se detienen: inicio (R) y fin (D) de la retrogradación ─
ESTACION = {
    'aMercurio': {
        'retrograde': "Mercurio se devuelve y con él se devuelven las palabras, los "
            "papeles y los aparatos. Durante unas tres semanas no es que todo salga "
            "mal: es que todo pide ser revisado. Relea antes de firmar, confirme las "
            "citas, guarde copia de lo importante y no compre a la carrera nada "
            "eléctrico ni de comunicaciones. Excelente época, en cambio, para "
            "retomar, corregir, reencontrarse y terminar lo que dejó a medias.",
        'direct': "Mercurio vuelve a andar hacia adelante y los enredos de las "
            "últimas semanas empiezan a soltarse. Lo que estaba demorado —una "
            "respuesta, un papel, un viaje— se destraba. Dele unos días antes de "
            "firmar o lanzar algo grande, pero ya puede decidir con lo que aprendió "
            "revisando.",
    },
    'aVenus': {
        'retrograde': "Venus se devuelve y pone en revisión lo que usted quiere y lo "
            "que usted vale: los afectos y el dinero. Suelen reaparecer amores del "
            "pasado y cuentas pendientes. No es el mejor momento para casarse, "
            "empezar una relación, hacerse cambios de imagen ni gastar en lujos; sí "
            "lo es para preguntarse con honestidad a quién quiere y qué aprecia de verdad.",
        'direct': "Venus retoma su marcha y el corazón y el bolsillo se aclaran. Lo "
            "que estuvo en duda en sus afectos o en sus finanzas empieza a definirse: "
            "ya sabe qué quiere conservar y qué no. Ahora sí puede comprometerse, "
            "comprar o arreglarse con la seguridad de no arrepentirse.",
    },
    'aMarte': {
        'retrograde': "Marte se devuelve y la fuerza se le mete para adentro. Durante "
            "más de dos meses lo que usted empuje de frente tiende a devolverse: las "
            "peleas, las prisas y las imprudencias salen caras. No inicie guerras ni "
            "proyectos que exijan mucho arranque; revise su manera de actuar, cuide "
            "el cuerpo y aprenda a medir la rabia antes de soltarla.",
        'direct': "Marte vuelve a avanzar y usted recupera el impulso. La energía que "
            "andaba contenida —o mal dirigida— encuentra otra vez por dónde salir. "
            "Retome lo que frenó, pero hágalo con la estrategia que aprendió en estos "
            "meses y no con la misma terquedad de antes.",
    },
    'aJupiter': {
        'retrograde': "Júpiter se devuelve y el crecimiento deja de ser hacia afuera "
            "para volverse hacia adentro. Durante unos cuatro meses la suerte no "
            "desaparece, pero deja de regalarse: revise sus creencias, sus planes "
            "de expansión y aquello en lo que ha exagerado. Más vale consolidar lo "
            "que tiene que prometer lo que no puede cumplir.",
        'direct': "Júpiter retoma el camino y las puertas que parecían entornadas "
            "vuelven a abrirse. Lo que usted revisó por dentro ya puede crecer por "
            "fuera: estudios, viajes, proyectos y trámites legales encuentran mejor "
            "viento. Confíe, pero sin pasarse de optimista.",
    },
    'aSaturno': {
        'retrograde': "Saturno se devuelve y el maestro severo le revisa la tarea. "
            "Durante más de cuatro meses las responsabilidades que usted ha "
            "esquivado vuelven a tocarle la puerta. No es tiempo de levantar "
            "estructuras nuevas sino de reforzar los cimientos de las que ya tiene: "
            "termine lo pendiente, ordene sus compromisos y hágase cargo.",
        'direct': "Saturno vuelve a avanzar y el peso se hace más llevadero. Lo que "
            "usted ordenó y asumió en estos meses empieza a mostrar resultados "
            "concretos. Ya puede construir con paso firme: los plazos se cumplen y "
            "el esfuerzo serio por fin se nota.",
    },
    'aUrano': {
        'retrograde': "Urano se devuelve y la rebeldía se le va por dentro. Durante "
            "cinco meses los cambios dejan de caerle de sorpresa desde afuera y "
            "usted empieza a notar dónde es que de verdad necesita liberarse. No "
            "rompa nada por impulso; madure primero el cambio que quiere hacer.",
        'direct': "Urano retoma su marcha y lo que usted venía cocinando por dentro "
            "quiere salir. Los cambios que aplazó se precipitan y aparecen "
            "novedades y sorpresas. Si ya sabe de qué quiere liberarse, es el "
            "momento de dar el salto.",
    },
    'aNeptuno': {
        'retrograde': "Neptuno se devuelve y la niebla se levanta un poco. Durante "
            "cinco meses se le hace más fácil ver dónde se ha estado engañando o "
            "dejando engañar. Las ilusiones se desinflan, y aunque eso duele, es "
            "sano. Buena época para la vida interior, la oración, el arte y para "
            "dejar las evasiones.",
        'direct': "Neptuno vuelve a avanzar y los sueños recobran fuerza. La "
            "inspiración y la fe regresan, pero también la tentación de ver solo lo "
            "que le conviene. Sueñe, por supuesto, pero con lo que aprendió en estos "
            "meses acerca de sus propios espejismos.",
    },
    'aPluton': {
        'retrograde': "Plutón se devuelve y la transformación se vuelve trabajo de "
            "sótano. Durante cinco meses lo que usted ha escondido, controlado o "
            "callado sube a que lo mire. No luche por poder afuera; revise adentro "
            "sus apegos, sus miedos y sus obsesiones, y deje morir lo que ya murió.",
        'direct': "Plutón retoma su marcha y lo que se removió por dentro empieza a "
            "cambiar las cosas por fuera. Lo que usted soltó ya no vuelve, y está "
            "bien que así sea. Use la fuerza recuperada para reconstruir, no para "
            "desquitarse.",
    },
    'aChiron': {
        'retrograde': "Quirón se devuelve y la vieja herida vuelve a sentirse. No es "
            "retroceso: es que el dolor que usted creía superado pide ser atendido "
            "con más honestidad. Durante cinco meses conviene dejar de curar a todo "
            "el mundo y ocuparse por fin de lo suyo.",
        'direct': "Quirón vuelve a avanzar y la herida, mejor comprendida, se "
            "convierte en maestra. Lo que usted sanó por dentro en estos meses ya "
            "puede ponerlo al servicio de otros. Enseñe desde lo que aprendió "
            "sufriendo, sin hacerse la víctima.",
    },
}
ESTACION_GEN = {
    'retrograde': "se detiene y comienza a retrogradar: lo que este planeta gobierna "
                  "pasa a revisión.",
    'direct': "termina su retrogradación y vuelve a avanzar: lo que estaba en "
              "revisión retoma su curso.",
}
RETRO_TEMA = {
    'aMercurio': "las ideas, los papeles y las conversaciones",
    'aVenus': "los afectos y los gastos", 'aMarte': "los impulsos y las peleas",
    'aJupiter': "las creencias y los planes de crecimiento",
    'aSaturno': "las responsabilidades y las estructuras",
    'aUrano': "las ansias de libertad", 'aNeptuno': "los sueños y las ilusiones",
    'aPluton': "el manejo del poder", 'aChiron': "las viejas heridas",
}


# ── Utilidades ──────────────────────────────────────────────────────────

def _fecha(iso):
    y, m, d = [int(x) for x in iso.split('-')[:3]]
    return y, m, d


def rango_semana(start, end):
    """'2026-11-16','2026-11-22' → '16 al 22 de noviembre de 2026'."""
    y1, m1, d1 = _fecha(start); y2, m2, d2 = _fecha(end)
    if y1 != y2:
        return "%d de %s de %d al %d de %s de %d" % (d1, MESES[m1 - 1], y1, d2, MESES[m2 - 1], y2)
    if m1 != m2:
        return "%d de %s al %d de %s de %d" % (d1, MESES[m1 - 1], d2, MESES[m2 - 1], y2)
    return "%d al %d de %s de %d" % (d1, d2, MESES[m2 - 1], y2)


def _cuando(ev):
    """'el domingo 22 a las 10:39'"""
    return "el %s %d a las %s" % (DIAS[ev['weekday']], _fecha(ev['date'])[2], ev['time'])


def _cuando_corto(ev):
    """'domingo 22, 10:39'"""
    return "%s %d, %s" % (DIAS[ev['weekday']], _fecha(ev['date'])[2], ev['time'])


def _etiqueta(ev):
    """'Dom 22 · 10:39' (columna izquierda de la agenda)"""
    return "%s %d · %s" % (DIAS_AB[ev['weekday']], _fecha(ev['date'])[2], ev['time'])


def _pl(key, inicio=False):
    """Nombre del planeta con artículo cuando corresponde ('el Sol', 'Mercurio')."""
    a = ART.get(key)
    n = NOMBRE.get(key, key)
    if not a:
        return n
    return "%s %s" % (a if inicio else a.lower(), n)


def _num(x):
    return ("%.1f" % x).replace('.', ',')


def resumen(texto, minimo=300, maximo=560):
    """Resume un texto largo de la base: primeras frases completas hasta
    `maximo` caracteres (corta en punto; si no hay, en punto y coma)."""
    if not texto:
        return ''
    t = ' '.join(texto.split('\n\n')[0].split())
    if len(t) <= maximo:
        return t
    frases = re.split(r'(?<=[.!?])\s+', t)
    out = ''
    for f in frases:
        if out and len(out) + 1 + len(f) > maximo:
            break
        if not out and len(f) > maximo:
            # primera frase demasiado larga: cortar en ; o , antes del límite
            cut = max(f.rfind(';', 0, maximo), f.rfind(':', 0, maximo))
            if cut < minimo // 2:
                cut = f.rfind(',', 0, maximo)
            if cut < minimo // 2:
                cut = f.rfind(' ', 0, maximo)
            return f[:cut].rstrip(' ,;:') + '.'
        out = (out + ' ' + f).strip()
        if len(out) >= minimo:
            break
    return out


def _palabras_clave(interp, idx):
    """Palabras clave de la fase, tomadas de la base de Mauricio."""
    t = (interp.get('combined', {}).get('lunar_phases', {}) or {}).get(FASE_CLAVE_DB[idx], '')
    m = re.search(r'Palabras claves?:\s*([^\n.]+)', t)
    return m.group(1).strip().rstrip('.') if m else ''


def _pos(w):
    """'5° de Libra'"""
    return "%d° de %s" % (w['deg'], w['sign_es'])


def _casa(n):
    return "Casa %s" % ROMAN[n - 1]


# ── Armado del reporte ──────────────────────────────────────────────────

def build_weekly(data, interp, place=''):
    """Devuelve (pre_blocks, sections, closing)."""
    tr = interp.get('transit', {})
    asp_db = tr.get('aspects', {})
    fb = interp.get('aspect_fallback', {}).get('transit', {})
    wk = data['week']
    snap = {p['key']: p for p in data['transit']['planets']}
    tg = data['targets']
    rango = rango_semana(wk['start'], wk['end'])
    lugar = (place or '').strip()

    sol, luna = snap.get('aSol'), snap.get('aLuna')
    f0 = data['phase_start']

    # ═══ Su semana de un vistazo ═════════════════════════════════════════
    pre = [("h2", "Su semana de un vistazo")]
    intro = ("Este es el cielo de la semana del %s, calculado para las 00:00 horas "
             "del lunes%s y leído sobre su carta natal. Aquí va únicamente lo "
             "esencial: lo que los planetas le hacen a su Sol, a su Luna y a su "
             "Ascendente; los planetas que se detienen para cambiar de rumbo, y "
             "las fases de la Luna que marcan el ritmo de estos siete días. No es "
             "para que se asuste ni para que se siente a esperar: es para que sepa "
             "con qué viento cuenta y lo use a su favor."
             % (rango, (" en %s" % lugar) if lugar else ""))
    pre.append(("p", intro))
    pre.append(("h3", "Agenda de la semana"))

    ag = []     # (jd, etiqueta, frase, resaltado)
    if sol and luna:
        ag.append((-1, "Lun %d · 00:00" % _fecha(wk['start'])[2],
                   "Comienza la semana con el Sol en %s y la Luna en %s, en fase de %s."
                   % (sol['sign_es'], luna['sign_es'], f0['name']), False))
    for a in data['aspects']:
        frase = "%s %s %s" % (_pl(a['transit'], True), ASP_FRASE[a['type']],
                              OBJETIVO[a['natal']][0])
        if a['exact']:
            ag.append((a['jd'], _etiqueta(a), frase + ".", False))
        else:
            ag.append((1e9, "Toda la semana", "%s (a %s° de ser exacto)."
                       % (frase, _num(a['orb'])), False))
    for a in data['moon_aspects']:
        ag.append((a['jd'], _etiqueta(a), "La Luna %s %s." % (
            'pasa sobre' if a['type'] == 'Conjunction' else 'se opone a',
            OBJETIVO[a['natal']][0]), False))
    for s in data['stations']:
        ag.append((s['jd'], _etiqueta(s), "%s %s, a %s." % (
            s['name'], 'inicia su retrogradación' if s['kind'] == 'retrograde'
            else 'termina su retrogradación y queda directo', _pos(s['at'])), True))
    for f in data['phases']:
        ag.append((f['jd'], _etiqueta(f), "%s en %s, en su %s." % (
            f['name'], f['moon']['sign_es'], _casa(f['moon']['natal_house'])), False))
    for _, lab, frase, hl in sorted(ag, key=lambda x: x[0]):
        pre.append(("mand", lab, frase, hl))

    sections = []

    # ═══ El clima de la semana ═══════════════════════════════════════════
    clima = []
    if sol:
        h = sol.get('natal_house', sol.get('house', 1))
        paras = ["Toda la semana el Sol camina por %s y le ilumina la %s: el sector "
                 "de %s. Ahí es donde están puestos el foco y la energía de estos días."
                 % (sol['sign_es'], _casa(h), CASA_TEMA[h - 1])]
        t = resumen(tr.get('planet_in_house', {}).get('aSol', {}).get(str(h)))
        if t:
            paras.append(t)
        clima.append(("El Sol en %s, por su %s" % (sol['sign_es'], _casa(h)), paras))
    if luna:
        h = luna.get('natal_house', luna.get('house', 1))
        clima.append(("La Luna arranca la semana en %s" % luna['sign_es'], [
            "El lunes a las 00:00 la Luna está a %s, en su %s, y viene en fase de %s. "
            "Es una Luna %s; ese es el ánimo con el que usted y quienes lo rodean "
            "empiezan la semana. En siete días ella recorre algo más de tres signos, "
            "de modo que el ánimo cambia cada dos días y medio: no tome por "
            "definitivo lo que sienta el lunes."
            % (_pos(luna), _casa(h), f0['name'],
               LUNA_SIGNO.get(luna['sign'], ''))]))
    if clima:
        sections.append(("El clima de la semana", clima))

    # ═══ Sol, Luna y Ascendente natales ══════════════════════════════════
    for nk in ('aSol', 'aLuna', 'aAsc'):
        if nk not in tg:
            continue
        nombre, tema = OBJETIVO[nk]
        donde = "%s, en la %s" % (_pos(tg[nk]), _casa(tg[nk]['natal_house'])) \
            if nk != 'aAsc' else _pos(tg[nk])
        items = []
        for a in [x for x in data['aspects'] if x['natal'] == nk]:
            tk, typ = a['transit'], a['type']
            lento = tk in LENTOS
            if a['exact']:
                titulo = "%s %s %s · %s" % (_pl(tk, True), ASP_FRASE[typ], nombre,
                                            _cuando_corto(a))
                tiempo = ("El aspecto es exacto %s, con %s a %s. %s"
                          % (_cuando(a), _pl(tk), _pos(a['at']),
                             "Como es un planeta lento, usted lo viene sintiendo desde "
                             "hace semanas y lo seguirá sintiendo después."
                             if lento else
                             "Se siente desde un par de días antes y se va apagando "
                             "un par de días después."))
            else:
                titulo = "%s %s %s · toda la semana" % (_pl(tk, True), ASP_FRASE[typ], nombre)
                tiempo = ("No llega a ser exacto esta semana, pero está a apenas %s° y "
                          "%s: lo acompaña los siete días."
                          % (_num(a['orb']),
                             "acercándose, de modo que va cobrando fuerza" if a['applying']
                             else "alejándose, de modo que va perdiendo fuerza"))
            p1 = ("%s le hace %s a %s, que usted tiene a %s, y que habla de %s. %s %s"
                  % (_pl(tk, True), ASP_ES[typ], nombre, donde, tema,
                     ASP_CLAVE[typ], tiempo))
            paras = [p1]
            t = resumen(asp_db.get(tk, {}).get(typ, {}).get(nk)) or fb.get(typ, '')
            if t:
                paras.append(t)
            items.append((titulo, paras))
        for a in [x for x in data['moon_aspects'] if x['natal'] == nk]:
            typ = a['type']
            titulo = "La Luna %s %s · %s" % (ASP_FRASE[typ], nombre, _cuando_corto(a))
            p1 = ("La Luna %s %s %s. Es un tránsito de pocas horas, pero se nota: "
                  "%s" % ('pasa sobre' if typ == 'Conjunction' else 'queda justo al frente de',
                          nombre, _cuando(a),
                          "le sube el volumen a lo emocional y lo vuelve más "
                          "receptivo a todo lo que ocurra ese día."
                          if typ == 'Conjunction' else
                          "ese día lo que usted quiere y lo que sienten los demás "
                          "tiran para lados distintos; no lo tome como algo personal."))
            paras = [p1]
            t = resumen(asp_db.get('aLuna', {}).get(typ, {}).get(nk), 180, 360)
            if t:
                paras.append(t)
            items.append((titulo, paras))
        if not items:
            items.append(("Semana tranquila para %s" % nombre,
                          [CALMA[nk] + " Recuerde que usted %s tiene a %s."
                           % ('la' if nk == 'aLuna' else 'lo', donde)]))
        sections.append((SEC_TITULO[nk], items))

    # ═══ Planetas que cambian de rumbo ═══════════════════════════════════
    items = []
    for s in data['stations']:
        k, kind = s['key'], s['kind']
        titulo = "%s %s · %s" % (s['name'],
                                 'inicia su retrogradación' if kind == 'retrograde'
                                 else 'termina su retrogradación', _cuando_corto(s))
        gen = ESTACION.get(k, {}).get(kind) or ("%s %s" % (s['name'], ESTACION_GEN[kind]))
        h = s['at']['natal_house']
        cerca = []
        for nk in ('aSol', 'aLuna', 'aAsc'):
            if nk in tg:
                d = abs(((s['at']['lon'] - tg[nk]['lon'] + 180) % 360) - 180)
                if d <= 4:
                    cerca.append(OBJETIVO[nk][0])
        p2 = ("En su carta, %s se detiene %s a %s, dentro de su %s: el sector de %s. "
              "Ahí es donde usted más va a notar %s."
              % (s['name'], _cuando(s), _pos(s['at']), _casa(h), CASA_TEMA[h - 1],
                 "el freno y la necesidad de revisar" if kind == 'retrograde'
                 else "que las cosas vuelven a moverse"))
        if cerca:
            p2 += (" Y ponga atención, porque lo hace prácticamente encima de %s: "
                   "le toca de manera muy directa." % ' y de '.join(cerca))
        items.append((titulo, [gen, p2]))
    retro = [k for k in data.get('retro_now', [])
             if not any(s['key'] == k and s['kind'] == 'direct' for s in data['stations'])]
    if not data['stations']:
        items.append(("Ningún planeta cambia de dirección esta semana", [
            "En estos siete días ningún planeta se detiene para devolverse ni para "
            "retomar su marcha. Es una buena noticia: el cielo no cambia las reglas "
            "a mitad de semana y lo que usted planee puede seguir su curso normal."]))
    if retro:
        lista = '; '.join("%s (%s)" % (NOMBRE[k], RETRO_TEMA.get(k, '')) for k in retro)
        items.append(("Los que siguen retrógrados", [
            "Durante toda la semana continúan retrógrados: %s. Un planeta retrógrado "
            "no es una desgracia; es un planeta que pide revisar antes de avanzar. En "
            "esos asuntos, mejor corregir y terminar que estrenar." % lista]))
    sections.append(("Planetas que cambian de rumbo", items))

    # ═══ La Luna y sus fases ═════════════════════════════════════════════
    items = []
    for f in data['phases']:
        i = f['index']; m = f['moon']; h = m['natal_house']
        titulo = "%s en %s · %s" % (f['name'], m['sign_es'], _cuando_corto(f))
        p1 = FASE_TXT[i]
        kw = _palabras_clave(interp, i)
        if kw:
            p1 += " Palabras clave: %s." % kw
        p2 = ("Esta fase comienza %s, con la Luna a %s —una Luna %s— y el Sol en %s. "
              "En su carta cae en la %s, el sector de %s: es ahí donde le conviene %s."
              % (_cuando(f), _pos(m), LUNA_SIGNO.get(m['sign'], ''), f['sun']['sign_es'],
                 _casa(h), CASA_TEMA[h - 1], FASE_ACCION[i]))
        cerca = []
        for nk in ('aSol', 'aLuna', 'aAsc'):
            if nk in tg:
                d = abs(((m['lon'] - tg[nk]['lon'] + 180) % 360) - 180)
                if d <= 5:
                    cerca.append(OBJETIVO[nk][0])
        if cerca:
            p2 += (" Además se produce casi encima de %s, de modo que esta fase le "
                   "habla a usted de forma muy personal." % ' y de '.join(cerca))
        items.append((titulo, [p1, p2]))
    if not items:
        items.append(("La semana transcurre en fase de %s" % f0['name'],
                      [FASE_TXT[f0['index']]]))
    sections.append(("La Luna y sus fases", items))

    closing = [
        ("h2", "Palabras finales"),
        ("pc", "Hasta aquí el cielo de su semana. Recuerde que los planetas inclinan "
               "pero no obligan: ellos ponen el clima y usted decide si sale con "
               "paraguas o se queda mirando llover. Use lo que le sirva, ponga "
               "atención en los días señalados y vuelva el próximo lunes por el "
               "cielo de la semana siguiente."),
        ("pc", "Este es un resumen; si desea profundizar en lo que estos tránsitos "
               "significan para su vida, solicite su consulta en nuestra página web."),
    ]
    return pre, sections, closing
