# -*- coding: utf-8 -*-
"""
report_chart.py — Lámina de carta astral estética (solo para los REPORTES PDF).
Dibujo 100% vectorial en reportlab (sin cairo, sin tocar la app web).
Se alimenta de los datos que ya calcula el backend (astro.compute_*).
"""
import os, math
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

_HERE = os.path.dirname(os.path.abspath(__file__))
_FONTS = os.path.join(_HERE, 'fonts')
_ASSETS = os.path.join(_HERE, 'assets')

# ── Fuentes ───────────────────────────────────────────────────────────────
GLYPH = 'AstroGlyph'          # DejaVu Sans: cubre todos los glifos astrológicos
_registered = {}
def _reg():
    if _registered:
        return
    dj = os.path.join(_FONTS, 'DejaVuSans.ttf')
    if os.path.exists(dj):
        pdfmetrics.registerFont(TTFont(GLYPH, dj))
        _registered['glyph'] = GLYPH
    else:
        _registered['glyph'] = 'Helvetica'
    # Serif premium (Cormorant Garamond) si está; si no, Times integrado.
    def _try(name, fname):
        p = os.path.join(_FONTS, fname)
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont(name, p)); return name
            except Exception:
                return None
        return None
    _registered['serif']   = _try('Cormorant',    'CormorantGaramond-Regular.ttf')  or 'Times-Roman'
    _registered['serif_m'] = _try('Cormorant-Md', 'CormorantGaramond-Medium.ttf')   or _registered['serif']
    _registered['serif_sb']= _try('Cormorant-Sb', 'CormorantGaramond-SemiBold.ttf') or _registered['serif']
    _registered['serif_i'] = _try('Cormorant-It', 'CormorantGaramond-Italic.ttf')   or 'Times-Italic'

def SERIF():    _reg(); return _registered['serif']
def SERIF_M():  _reg(); return _registered['serif_m']
def SERIF_SB(): _reg(); return _registered['serif_sb']
def SERIF_I():  _reg(); return _registered['serif_i']
def GLYPHF():   _reg(); return _registered['glyph']

# ── Paletas ─────────────────────────────────────────────────────────────────
INK   = HexColor('#26304F')
INK2  = HexColor('#3A3A46')
GOLD  = HexColor('#B8863B')
def _shift(hexc, d):
    c = HexColor(hexc)
    return Color(max(0, min(1, c.red + d/255.0)),
                 max(0, min(1, c.green + d/255.0)),
                 max(0, min(1, c.blue + d/255.0)))
GOLD_D = _shift('#B8863B', -34)
GOLD_F = _shift('#B8863B',  62)
SILVER = HexColor('#9AA2AC')

# key de la app -> (glifo, color, nombre)
PLANETS = {
    'aSol':        ('☉', '#C79A4E', 'Sol'),
    'aLuna':       ('☽', '#9BA3C0', 'Luna'),
    'aMercurio':   ('☿', '#79A794', 'Mercurio'),
    'aVenus':      ('♀', '#CF92AB', 'Venus'),
    'aMarte':      ('♂', '#C4796C', 'Marte'),
    'aJupiter':    ('♃', '#C77BA0', 'Júpiter'),   # rosado
    'aSaturno':    ('♄', '#918CA8', 'Saturno'),
    'aUrano':      ('♅', '#6BB3D8', 'Urano'),     # celeste
    'aNeptuno':    ('♆', '#3F529A', 'Neptuno'),   # azul oscuro
    'aPluton':     ('♇', '#A481BB', 'Plutón'),    # glifo antiguo (vector)
    'aChiron':     ('⚷', '#8A5FA6', 'Quirón'),    # púrpura
    'aNoduloNorte':('☊', '#8D9CB4', 'Nodo Norte'),
    'aNoduloSur':  ('☋', '#A29AAE', 'Nodo Sur'),
    'aLunaNegra':  ('⚸', '#83769B', 'Luna Negra'),
    'aRuedaFortuna':('⊗','#BC9A5A', 'Parte de la Fortuna'),
}
SIGN_GLYPH = ['♈','♉','♊','♋','♌','♍',
              '♎','♏','♐','♑','♒','♓']
SIGN_NAME = ['Aries','Tauro','Géminis','Cáncer','Leo','Virgo',
             'Libra','Escorpio','Sagitario','Capricornio','Acuario','Piscis']
SIGN_COL = ['#C4796C','#7E9B78','#B9A45E','#93A3AE','#C89163','#A88CA8',
            '#8FA97F','#A57080','#B27FA8','#8A8578','#79AFB4','#8290BB']
# Regentes de decanato (glifos), Aries->Piscis (copiado de DECAN_RULERS)
DECANS = [
    ['♂','☉','♃'], ['♀','⚷','♄'], ['☿','♀','♅'],
    ['☽','♇','♆'], ['☉','♃','♂'], ['⚷','♄','♀'],
    ['♀','♅','☿'], ['♇','♆','☽'], ['♃','♂','☉'],
    ['♄','♀','⚷'], ['♅','☿','♀'], ['♆','☽','♇'],
]
ASPECTS = {  # tipo -> (color, glifo, nombre)
    'conjunction':('#B8863B','☌','Conjunción'),
    'opposition': ('#C08A7B','☍','Oposición'),
    'square':     ('#C2A05C','□','Cuadratura'),
    'trine':      ('#8FA0C0','△','Trígono'),
    'sextile':    ('#93B096','✦','Sextil'),
}
# tipos en inglés y español (el backend entrega inglés en 'type')
_ASP_ES = {'Conjunction':'conjunction','Opposition':'opposition','Square':'square',
           'Trine':'trine','Sextile':'sextile'}

def _hx(s): return HexColor(s)

# ── Anti-solape que preserva el orden (igual criterio que la app) ───────────
def spread(lons, min_sep=10.0):
    n = len(lons)
    if n <= 1: return list(lons)
    idx = sorted(range(n), key=lambda i: lons[i])
    s = [lons[i] for i in idx]
    maxg, cut = -1, 0
    for k in range(n):
        g = (s[k+1]-s[k]) if k < n-1 else (s[0]+360-s[n-1])
        if g > maxg: maxg, cut = g, (k+1) % n
    seq = [(cut+k) % n for k in range(n)]
    orig = [0]*n; orig[0] = s[seq[0]]
    for k in range(1, n):
        v = s[seq[k]]
        while v < orig[k-1]: v += 360
        orig[k] = v
    P = orig[:]
    for k in range(1, n):
        if P[k] < P[k-1]+min_sep: P[k] = P[k-1]+min_sep
    if n*min_sep > 360:
        step = 360.0/n
        for k in range(n): P[k] = orig[0]+k*step
    sh = (sum(orig)-sum(P))/n
    out = [0]*n
    for k in range(n): out[idx[seq[k]]] = (P[k]+sh) % 360
    return out


# Glifo de Plutón según el SVG del usuario (círculo en copa sobre la cruz).
# Geometría original (viewBox centrado, y hacia abajo):
#   círculo  centro (0,-9.771) r 9.313
#   copa     semicírculo inferior r 13.938 centrado en (0,-9.771)  → abre arriba
#   tallo    (0,4.167)–(0,19.083)      barra (-7.089,11.625)–(7.536,11.625)
# Alto natural ≈ 38.16 u. Aquí y va hacia ARRIBA (reportlab), por eso se niega.
def _draw_pluto(c, x, y, px, col):
    u = px/38.16
    c.saveState(); c.setStrokeColor(col); c.setFillColor(col)
    c.setLineWidth(max(0.7, 1.8*u))
    cyc = y + 9.771*u                     # centro del círculo/copa
    R = 13.938*u                          # radio de la copa
    rC = 9.313*u                          # radio del círculo
    c.arc(x-R, cyc-R, x+R, cyc+R, 180, 180)   # copa: semicírculo inferior
    c.circle(x, cyc, rC, stroke=1, fill=0)    # círculo
    c.line(x, y-4.167*u, x, y-19.083*u)       # tallo
    c.line(x-7.089*u, y-11.625*u, x+7.536*u, y-11.625*u)  # barra
    c.restoreState()


# ── LA RUEDA ────────────────────────────────────────────────────────────────
def draw_wheel(c, data, ox, oy, size, center_art='sun', aspect_lines=True,
               show_decans=True):
    """Dibuja la rueda (viewBox 1000) dentro del cuadro (ox,oy,size) en puntos.
    ox,oy = esquina inferior-izquierda; size = lado en puntos."""
    _reg()
    S = 1000.0
    sc = size/S
    asc = data['angles']['asc']['lon'] if 'angles' in data else data['asc']
    mc  = data['angles']['mc']['lon']  if 'angles' in data else data['mc']
    cx = cy = 500.0

    def pt(lon, r):
        th = math.radians(180 + asc - lon)
        vx = cx + r*math.cos(th)
        vy = cy + r*math.sin(th)
        return (ox + vx*sc, oy + (S-vy)*sc)   # flip y (viewBox y-down -> page y-up)

    def ring(r, col, w):
        c.setStrokeColor(col); c.setLineWidth(w*sc)
        c.circle(ox+cx*sc, oy+(S-cy)*sc, r*sc, stroke=1, fill=0)

    def gtext(lon, r, glyph, col, px):
        x, y = pt(lon, r)
        c.setFillColor(col); c.setFont(GLYPHF(), px*sc)
        c.drawCentredString(x, y - px*sc*0.36, glyph)

    def line(l1, r1, l2, r2, col, w, alpha=1):
        x1, y1 = pt(l1, r1); x2, y2 = pt(l2, r2)
        c.setStrokeColor(col); c.setLineWidth(w*sc)
        if alpha < 1: c.setStrokeAlpha(alpha)
        c.line(x1, y1, x2, y2)
        if alpha < 1: c.setStrokeAlpha(1)

    # aros exteriores
    ring(452, GOLD, 1.3)
    ring(446, GOLD_F, 0.7)
    ring(392, GOLD, 0.9)
    ring(356, GOLD, 1.0)
    # marcas de grado (1/5/10) hacia dentro desde 446
    for d in range(360):
        r0 = 446
        r1 = 441 if d % 5 else (438 if d % 10 else 434)
        line(d, r0, d, r1, GOLD_F, 0.5 if d % 5 else 0.7, 0.9 if d % 5 else 1)
    # banda de signos: glifo + divisor cada 30° + decanatos
    for i in range(12):
        l0 = i*30
        line(l0, 356, l0, 452, GOLD, 1.0)
        gtext(l0+15, 418, SIGN_GLYPH[i], _hx(SIGN_COL[i]), 36)
        if show_decans:
            for d in (10, 20):
                line(l0+d, 356, l0+d, 392, GOLD_F, 0.5, 0.9)
            for k, g in enumerate(DECANS[i]):
                gtext(l0+5+k*10, 374, g, GOLD, 15)

    # casas: cúspides de 150 a 356
    houses = [h['lon'] for h in data['houses']] if isinstance(data['houses'][0], dict) else data['houses']
    for hi, hl in enumerate(houses):
        axis = hi in (0, 3, 6, 9)
        line(hl, 150, hl, 356, GOLD_D if axis else GOLD, 1.4 if axis else 0.7,
             1 if axis else 0.8)
        # número de casa centrado en el sector
        nxt = houses[(hi+1) % 12]
        arc = (nxt - hl) % 360
        mid = (hl + arc/2.0) % 360
        x, y = pt(mid, 168)
        c.setFillColor(GOLD_D); c.setFont(SERIF_SB(), 15*sc)
        c.drawCentredString(x, y-15*sc*0.34, _ROMAN[hi])
    ring(150, GOLD_F, 0.8)

    # arte central: sol dibujado = 48 triángulos rellenos que nacen del borde
    # de un disco r32 (base = arco del disco, vértice a distancia rr). Todo el
    # grupo a opacity .3 para que sea marca de agua. Detrás de aspectos/planetas.
    if center_art == 'sun':
        ccx, ccy = ox+cx*sc, oy+(S-cy)*sc
        gds = HexColor('#96682A')            # oro oscuro base −34 por canal

        def _P(r, ang):
            return (ccx + r*math.cos(ang)*sc, ccy - r*math.sin(ang)*sc)

        c.saveState()
        # OJO: en reportlab setFillColor/​setStrokeColor resetean el alpha, así que
        # el alpha se fija DESPUÉS de cada color. Grupo a opacity .3 (marca de agua).
        _AL = 0.3
        c.setFillColor(gds); c.setFillAlpha(_AL); c.setStrokeAlpha(_AL)
        for i in range(48):
            a0 = math.radians(i*7.5)
            rr = 128 if i % 4 == 0 else (100 if i % 2 == 0 else 78)
            w = 5.0 if i % 4 == 0 else 3.2
            aw = math.radians(w)
            xt, yt = _P(rr, a0)
            xa, ya = _P(32, a0-aw)
            xb, yb = _P(32, a0+aw)
            pth = c.beginPath(); pth.moveTo(xa, ya); pth.lineTo(xt, yt)
            pth.lineTo(xb, yb); pth.close()
            c.drawPath(pth, stroke=0, fill=1)
        # disco central del color del papel con aro fino encima
        c.setFillColor(HexColor('#FFFFFF')); c.setStrokeColor(gds); c.setLineWidth(1.4*sc)
        c.setFillAlpha(_AL); c.setStrokeAlpha(_AL)   # re-fijar (el color lo reseteó)
        c.circle(ccx, ccy, 32*sc, stroke=1, fill=1)
        c.restoreState()

    # planetas
    plist = data['planets']
    lons = [p['lon'] for p in plist]
    shown = spread(lons, 6.5)   # más compacto (stellium tipo AstroGold)
    # líneas de aspecto (sobre el aro 150), en longitud real
    if aspect_lines:
        pos = {p['key']: p['lon'] for p in plist}
        for a in data.get('aspects', []):
            t = _ASP_ES.get(a['type'], a['type'])
            if t == 'conjunction': continue
            if a['a'] not in pos or a['b'] not in pos: continue
            col, _, _ = ASPECTS.get(t, ('#999', '', ''))
            line(pos[a['a']], 150, pos[a['b']], 150, _hx(col), 0.9, 0.65)
    for i, p in enumerate(plist):
        col = _hx(PLANETS.get(p['key'], ('', '#8890B0', ''))[1])
        gl  = PLANETS.get(p['key'], ('?',))[0]
        a = shown[i]; real = p['lon']
        # punto en la longitud REAL (sin línea guía)
        xr, yr = pt(real, 356)
        c.setFillColor(col); c.circle(xr, yr, 3*sc, stroke=0, fill=1)
        if p['key'] == 'aPluton':
            gx, gy = pt(a, 320); _draw_pluto(c, gx, gy, 27*sc, col)
        else:
            gtext(a, 320, gl, col, 36)
        # grado / signo / minutos
        deg = int(real % 30); mn = int(round((real % 1)*60))
        if mn == 60: mn = 0; deg += 1
        sidx = int(real // 30) % 12
        x, y = pt(a, 281); c.setFillColor(INK2); c.setFont(SERIF_M(), 21*sc)
        c.drawCentredString(x, y-21*sc*0.34, u"%d°" % deg)
        gtext(a, 256, SIGN_GLYPH[sidx], _hx(SIGN_COL[sidx]), 18)
        x, y = pt(a, 232); c.setFillColor(INK2); c.setFont(SERIF_M(), 18*sc)
        c.drawCentredString(x, y-18*sc*0.34, u"%02d'" % mn)

    # ejes Ac / Mc con punta de flecha
    def axis_arrow(lon, col, label):
        x1, y1 = pt(lon, 356); x2, y2 = pt(lon, 482)
        c.setStrokeColor(col); c.setLineWidth(1.4*sc); c.line(x1, y1, x2, y2)
        tipx, tipy = pt(lon, 497)
        b1 = pt(lon-0.85, 482); b2 = pt(lon+0.85, 482)
        path = c.beginPath(); path.moveTo(tipx, tipy)
        path.lineTo(*b1); path.lineTo(*b2); path.close()
        c.setFillColor(col); c.drawPath(path, stroke=0, fill=1)
        lx, ly = pt(lon+2.6, 494); c.setFillColor(col); c.setFont(SERIF_SB(), 17*sc)
        c.drawCentredString(lx, ly-17*sc*0.34, label)
    axis_arrow(asc, GOLD_D, 'Ac')
    axis_arrow(mc, SILVER, 'Mc')

_ROMAN = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']


# ── Textos por tipo ──────────────────────────────────────────────────────────
TEXTS = {
 'natal': ("El mapa de tu cielo al nacer — Carta natal",
           "El instante exacto en que el cosmos escribió tu libreto.",
           ("Naciste con un mapa completo entre las manos.",
            "Aprender a leerlo es el trabajo de toda una vida.")),
 'solar_return': ("El mapa de tu nuevo año personal — Retorno solar",
           "Un viaje por las oportunidades, desafíos y propósito de este ciclo.",
           ("Cada cumpleaños marca un nuevo comienzo.",
            "Conoce tu tiempo para vivirlo con conciencia y plenitud.")),
 'progressed': ("El mapa de tu evolución interior — Progresada",
           "Cómo ha ido madurando tu carta natal con el paso de los años.",
           ("El cielo con el que naciste nunca dejó de moverse.",
            "Esta es la forma que tiene hoy.")),
 'combined': ("El mapa del encuentro entre dos cielos — Combinada",
           "Lo que dos cartas construyen cuando se miran de frente.",
           ("Ningún vínculo llega por casualidad.",
            "Dos cartas que se cruzan escriben una tercera historia.")),
 'akashic': ("El mapa de la memoria de tu alma — Registros akáshicos",
           "Aquello que traes de antes y que este cielo todavía recuerda.",
           ("Tu alma guarda registro de cada camino recorrido.",
            "Aquí comienza su lectura.")),
}
ADORNO = {'natal':'sun-sq.png','solar_return':'sun-sq.png','progressed':'moon-sq.png',
          'combined':'hands-heart.png','akashic':'akashic-hands.png'}


# ── Helpers de dibujo de la página ───────────────────────────────────────────
def _tracked(c, cx, y, text, font, size, tracking, color, align='center'):
    """Dibuja texto con letter-spacing. cx = centro si align='center'."""
    c.setFont(font, size); c.setFillColor(color)
    widths = [pdfmetrics.stringWidth(ch, font, size) for ch in text]
    total = sum(widths) + tracking*(len(text)-1 if text else 0)
    x = cx - total/2.0 if align == 'center' else cx
    for ch, w in zip(text, widths):
        c.drawString(x, y, ch); x += w + tracking

def _chamfer(c, x, y, w, h, ch, col, lw, alpha=1):
    p = c.beginPath()
    p.moveTo(x+ch, y); p.lineTo(x+w-ch, y); p.lineTo(x+w, y+ch)
    p.lineTo(x+w, y+h-ch); p.lineTo(x+w-ch, y+h); p.lineTo(x+ch, y+h)
    p.lineTo(x, y+h-ch); p.lineTo(x, y+ch); p.close()
    c.setStrokeColor(col); c.setLineWidth(lw)
    if alpha < 1: c.setStrokeAlpha(alpha)
    c.drawPath(p, stroke=1, fill=0)
    if alpha < 1: c.setStrokeAlpha(1)

def _icon(c, kind, x, y, s, col):
    """Icono de línea de tamaño s con esquina inf-izq en (x,y)."""
    c.setStrokeColor(col); c.setFillColor(col); c.setLineWidth(1.5)
    m = s
    if kind == 'cal':
        c.roundRect(x, y, m, m*0.86, 1.5, stroke=1, fill=0)
        c.line(x, y+m*0.63, x+m, y+m*0.63)
        c.line(x+m*0.28, y+m*0.86, x+m*0.28, y+m); c.line(x+m*0.72, y+m*0.86, x+m*0.72, y+m)
    elif kind == 'clock':
        c.circle(x+m/2, y+m/2, m/2, stroke=1, fill=0)
        c.line(x+m/2, y+m/2, x+m/2, y+m*0.82); c.line(x+m/2, y+m/2, x+m*0.72, y+m/2)
    elif kind == 'pin':
        c.circle(x+m/2, y+m*0.62, m*0.32, stroke=1, fill=0)
        p = c.beginPath(); p.moveTo(x+m*0.5, y); p.lineTo(x+m*0.22, y+m*0.55)
        p.lineTo(x+m*0.78, y+m*0.55); p.close(); c.drawPath(p, stroke=1, fill=0)
        c.circle(x+m/2, y+m*0.62, m*0.10, stroke=0, fill=1)
    elif kind == 'up':
        c.line(x+m/2, y, x+m/2, y+m)
        p = c.beginPath(); p.moveTo(x+m/2, y+m); p.lineTo(x+m*0.24, y+m*0.66)
        p.lineTo(x+m*0.76, y+m*0.66); p.close(); c.drawPath(p, stroke=0, fill=1)
    elif kind == 'globe':
        c.circle(x+m/2, y+m/2, m/2, stroke=1, fill=0)
        c.line(x, y+m/2, x+m, y+m/2)
        c.ellipse(x+m*0.30, y, x+m*0.70, y+m, stroke=1, fill=0)

def _diamond_rule(c, cx, y, half, col):
    c.setStrokeColor(col); c.setLineWidth(0.8)
    c.line(cx-half, y, cx-7, y); c.line(cx+7, y, cx+half, y)
    p = c.beginPath(); p.moveTo(cx, y+3.4); p.lineTo(cx+3.4, y); p.lineTo(cx, y-3.4)
    p.lineTo(cx-3.4, y); p.close(); c.setFillColor(col); c.drawPath(p, stroke=0, fill=1)

def _stars(c, cx, cy, spread, col, seed=7):
    import random; rnd = random.Random(seed)
    c.setFillColor(col)
    for _ in range(9):
        ang = rnd.uniform(0, 6.28); rad = rnd.uniform(spread*0.5, spread)
        x = cx + rad*math.cos(ang); y = cy + rad*math.sin(ang)
        sz = rnd.uniform(2.2, 3.6); c.setFillAlpha(rnd.uniform(0.45, 0.6))
        p = c.beginPath()
        for k in range(4):
            a = k*math.pi/2
            p.moveTo(x, y)
        # estrella de 4 puntas
        pth = c.beginPath()
        pts = [(0,-sz),(sz*0.28,-sz*0.28),(sz,0),(sz*0.28,sz*0.28),
               (0,sz),(-sz*0.28,sz*0.28),(-sz,0),(-sz*0.28,-sz*0.28)]
        pth.moveTo(x+pts[0][0], y+pts[0][1])
        for dx, dy in pts[1:]:
            pth.lineTo(x+dx, y+dy)
        pth.close(); c.drawPath(pth, stroke=0, fill=1)
    c.setFillAlpha(1)


def _draw_watermark(c, page_w, page_h, alpha=0.5):
    """Marca de agua de constelaciones cubriendo TODA la página (escala cover)."""
    wm = os.path.join(_ASSETS, 'constellations-faint.png')
    if not os.path.exists(wm):
        return
    nw, nh = 4278.0, 2480.0
    scale = max(page_w/nw, page_h/nh)      # cover: llena ancho y alto
    iw, ih = nw*scale, nh*scale
    try:
        c.saveState(); c.setFillAlpha(alpha)
        c.drawImage(ImageReader(wm), page_w/2-iw/2, page_h/2-ih/2, iw, ih,
                    mask='auto', preserveAspectRatio=False)
        c.restoreState()
    except Exception:
        pass


def draw_lamina(c, page_w, page_h, chart_type, meta, data,
                center_art='sun', aspect_lines=True, show_decans=True):
    """Dibuja una lámina de carta completa en la página actual (fondo blanco)."""
    _reg()
    ct = chart_type if chart_type in TEXTS else 'natal'
    ante, sub, close = TEXTS[ct]
    cx = page_w/2.0

    # fondo blanco + marca de agua de constelaciones (cubre toda la página)
    c.setFillColor(HexColor('#FFFFFF')); c.rect(0, 0, page_w, page_h, stroke=0, fill=1)
    _draw_watermark(c, page_w, page_h)

    y = page_h - 42
    # antetítulo (versalitas, tracking)
    _tracked(c, cx, y, ante.upper(), SERIF_SB(), 13.5, 1.6, INK)
    y -= 22
    c.setFont(SERIF_I(), 17); c.setFillColor(HexColor('#A07127'))
    c.drawCentredString(cx, y, sub)
    y -= 42
    # nombre (armónico, no invasivo)
    nombre = meta.get('lamina_name') or meta.get('name') or ''
    nsize = 30 if ct == 'combined' else 38
    c.setFont(SERIF_M(), nsize); c.setFillColor(INK)
    c.drawCentredString(cx, y, nombre or ' ')
    y -= 16
    _diamond_rule(c, cx, y, 150, GOLD)
    y -= 10

    # rueda
    wsize = min(page_w-70, 442)
    wx = cx - wsize/2; wy = y - wsize
    _stars(c, cx, wy+wsize*0.5, wsize*0.62, HexColor('#C08B33'))
    draw_wheel(c, data, wx, wy, wsize, center_art, aspect_lines, show_decans)

    # ── bloques de datos (con título, filas alineadas) ──
    raw = meta.get('boxes') or [_default_box(meta, data)]
    norm = []
    for b in raw:
        if isinstance(b, dict):
            norm.append((b.get('title'), b.get('rows', [])))
        else:
            norm.append((None, b))
    twobox = len(norm) > 1
    bw = 206 if twobox else 234
    chf = 12
    pad_top, rowh, pad_bot = 14, 19, 13
    has_title = any(t for t, _ in norm)
    title_h = 18 if has_title else 0
    maxrows = max((len(r) for _, r in norm), default=1)
    bh = pad_top + title_h + maxrows*rowh + pad_bot
    gap = 74
    total_w = len(norm)*bw + (len(norm)-1)*gap
    bx0 = cx - total_w/2
    by = wy - bh - 2
    rfs = 11.5 if twobox else 12.5
    for bi, (title, rows) in enumerate(norm):
        bx = bx0 + bi*(bw+gap)
        _chamfer(c, bx, by, bw, bh, chf, GOLD, 1.2)
        _chamfer(c, bx+6, by+6, bw-12, bh-12, chf-5, GOLD, 0.6, alpha=0.55)
        ty = by + bh - pad_top
        if title:
            _tracked(c, bx+bw/2, ty-9, title.upper(), SERIF_SB(), 10, 1.7, GOLD_D)
            ty -= title_h
        ry = ty - rowh/2
        for icon, txt in rows:
            _icon(c, icon, bx+22, ry-6, 11, GOLD)
            c.setFont(SERIF_M(), rfs); c.setFillColor(INK)
            c.drawString(bx+42, ry-4, txt)
            ry -= rowh
    # adorno (sin solaparse con las cajas)
    ad = ADORNO.get(ct)
    if ad and os.path.exists(os.path.join(_ASSETS, ad)):
        adp = ImageReader(os.path.join(_ASSETS, ad)); asz = 58
        cyb = by + bh/2
        try:
            if len(norm) == 1:
                c.drawImage(adp, bx0-asz-22, cyb-asz/2, asz, asz, mask='auto', preserveAspectRatio=True)
                c.drawImage(adp, bx0+bw+22, cyb-asz/2, asz, asz, mask='auto', preserveAspectRatio=True)
            else:
                c.drawImage(adp, cx-asz/2, cyb-asz/2, asz, asz, mask='auto', preserveAspectRatio=True)
        except Exception:
            pass

    # frase de cierre (dos líneas, itálica)
    fy = by - 24
    c.setFont(SERIF_I(), 15.5); c.setFillColor(INK)
    c.drawCentredString(cx, fy, close[0]); c.drawCentredString(cx, fy-19, close[1])


def draw_dual_wheels(c, page_w, page_h, meta, natal, der, ntitle, dtitle,
                     center_art='sun', aspect_lines=True, show_decans=True):
    """Página apaisada con las DOS ruedas (natal + derivada) en el estilo nuevo."""
    _reg()
    cx = page_w/2.0
    c.setFillColor(HexColor('#FFFFFF')); c.rect(0, 0, page_w, page_h, stroke=0, fill=1)
    _draw_watermark(c, page_w, page_h)
    # título general + rombo
    title = (meta.get('dual_title') or 'Tus dos cartas')
    _tracked(c, cx, page_h-32, title.upper(), SERIF_SB(), 13, 1.6, INK)
    _diamond_rule(c, cx, page_h-46, 150, GOLD)
    # dos ruedas con su rótulo y su línea de datos
    subs = meta.get('dual_subs') or ['', '']
    top = page_h - 108
    bot = 24
    wsize = min(page_w/2 - 78, top - bot)
    cap_y = page_h - 72
    for k, (chart, cap) in enumerate(((natal, ntitle), (der, dtitle))):
        halfcx = page_w*(0.25 if k == 0 else 0.75)
        c.setFont(SERIF_SB(), 15); c.setFillColor(HexColor('#A07127'))
        c.drawCentredString(halfcx, cap_y, cap or '')
        sub = subs[k] if k < len(subs) else ''
        if sub:
            c.setFont(SERIF_I(), 11.5); c.setFillColor(INK)
            c.drawCentredString(halfcx, cap_y-17, sub)
        wy = bot + ((top-bot) - wsize)/2.0
        wx = halfcx - wsize/2.0
        draw_wheel(c, chart, wx, wy, wsize, center_art, aspect_lines, show_decans)


def _default_box(meta, data):
    rows = []
    if meta.get('date_fmt'): rows.append(('cal', meta['date_fmt']))
    if meta.get('time'):     rows.append(('clock', meta['time']))
    if meta.get('city'):     rows.append(('pin', meta['city']))
    asc = data.get('asc', data.get('angles', {}).get('asc', {}).get('lon'))
    if asc is not None:
        si = int(asc // 30) % 12
        rows.append(('up', 'Asc %s %d°' % (SIGN_NAME[si], int(asc % 30))))
    if meta.get('coords'):   rows.append(('globe', meta['coords']))
    return rows[:5]


def draw_legend(c, page_w, page_h):
    """Página de leyenda independiente (fondo blanco)."""
    _reg()
    cx = page_w/2.0
    c.setFillColor(HexColor('#FFFFFF')); c.rect(0, 0, page_w, page_h, stroke=0, fill=1)
    y = page_h - 46
    _tracked(c, cx, y, "LEYENDA DE SÍMBOLOS", SERIF_SB(), 13.5, 1.6, INK); y -= 22
    c.setFont(SERIF_I(), 17); c.setFillColor(HexColor('#A07127'))
    c.drawCentredString(cx, y, "Las claves para leer cada carta de este reporte."); y -= 16
    _diamond_rule(c, cx, y, 150, GOLD); y -= 40

    margin = 62; cw = page_w - 2*margin; left = margin
    def block_head(title, yy):
        _tracked(c, left, yy, title.upper(), SERIF_SB(), 11.5, 1.8, INK, align='left')
        tw = sum(pdfmetrics.stringWidth(ch, SERIF_SB(), 11.5) for ch in title.upper()) + 1.8*(len(title)-1)
        # regla degradé oro -> transparente (aprox con segmentos)
        x0 = left+tw+12; x1 = left+cw
        n = 40
        for k in range(n):
            xa = x0+(x1-x0)*k/n; xb = x0+(x1-x0)*(k+1)/n
            c.setStrokeColor(GOLD); c.setStrokeAlpha(0.9*(1-k/n)); c.setLineWidth(1.0)
            c.line(xa, yy+3, xb, yy+3)
        c.setStrokeAlpha(1)

    def grid(entries, yy, cols, rowh):
        colw = cw/cols
        for i, (glyph, gcol, name) in enumerate(entries):
            r = i//cols; cc = i % cols
            gx = left + cc*colw; gy = yy - r*rowh
            if glyph == '♇':
                _draw_pluto(c, gx+13, gy-4, 17, _hx(gcol))
            else:
                c.setFont(GLYPHF(), 20); c.setFillColor(_hx(gcol))
                c.drawCentredString(gx+13, gy-7, glyph)
            c.setFont(SERIF_M(), 14.5); c.setFillColor(INK)
            c.drawString(gx+30, gy-6, name)
        rows = (len(entries)+cols-1)//cols
        return yy - rows*rowh

    # Planetas y puntos (15)
    block_head("Planetas y puntos", y); y -= 24
    order = ['aSol','aLuna','aMercurio','aVenus','aMarte','aJupiter','aSaturno',
             'aUrano','aNeptuno','aPluton','aChiron','aNoduloNorte','aNoduloSur',
             'aLunaNegra','aRuedaFortuna']
    pe = [(PLANETS[k][0], PLANETS[k][1], PLANETS[k][2]) for k in order]
    y = grid(pe, y, 3, 26) - 16

    # Signos (12)
    block_head("Signos", y); y -= 24
    se = [(SIGN_GLYPH[i], SIGN_COL[i], SIGN_NAME[i]) for i in range(12)]
    y = grid(se, y, 3, 26) - 16

    # Aspectos (5)
    block_head("Aspectos", y); y -= 24
    aspe = [('conjunction','Conjunción'),('opposition','Oposición'),
            ('square','Cuadratura'),('trine','Trígono'),('sextile','Sextil')]
    colw = cw/2
    for i, (t, name) in enumerate(aspe):
        col, glyph, _ = ASPECTS[t]
        r = i//2; cc = i % 2; gx = left+cc*colw; gy = y - r*26
        c.setStrokeColor(_hx(col)); c.setLineWidth(1.5)
        if t == 'conjunction':
            c.setFillColor(_hx(col)); c.circle(gx+17, gy-5, 3.5, stroke=0, fill=1)
        else:
            c.line(gx, gy-5, gx+34, gy-5)
        c.setFont(GLYPHF(), 15); c.setFillColor(_hx(col))
        c.drawCentredString(gx+48, gy-10, glyph)
        c.setFont(SERIF_M(), 14.5); c.setFillColor(INK)
        c.drawString(gx+64, gy-9, name)
