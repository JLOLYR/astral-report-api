# -*- coding: utf-8 -*-
"""
weekly_pdf.py — Reporte de Tránsitos Semanales, diseño v1: PDF A4 de 3 páginas
fijas dibujadas en lienzo (no flujo). Especificación:
DISENO_Reporte_Transitos_Semanales.md

Todas las medidas del diseño están en px CSS (96 dpi) con origen arriba a la
izquierda; aquí se convierten a puntos con K = 0,75.
"""
import io
import os

from reportlab.pdfgen import canvas as _canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

import report_chart as rc
import weekly_layout as wl
from weekly import resumen

_HERE = os.path.dirname(os.path.abspath(__file__))
_FONTS = os.path.join(_HERE, 'fonts')
_ASSETS = os.path.join(_HERE, 'assets')

K = 0.75
PW, PH = 794.0, 1123.0
ML = 40.0
CW = PW - 2 * ML            # 714

NAVY = '#0F1B3D'; INK = '#26304F'; MUTED = '#5A6178'
GOLD = '#B8863B'; GOLD_D = '#96682A'; GOLD_S = '#C9A063'
CREAM = '#F7F0D3'; TINT = '#FBF7EC'; HAIR = '#E2D3B4'; RETRO = '#C0392B'
SEP = '#E6D6AE'; WHITE = '#FFFFFF'
ELEM_COL = {'Fuego': '#C4796C', 'Tierra': '#7E9B78', 'Aire': '#B9A45E', 'Agua': '#93A3AE'}
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
DIAS_AB = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM']

# ── Fuentes (Montserrat; si faltan los archivos, Helvetica) ───────────────
_F = {}


def _fonts():
    if _F:
        return _F
    rc._reg()
    tabla = {'r': ('Mont', 'Montserrat-Regular.ttf', 'Helvetica'),
             'm': ('Mont-Md', 'Montserrat-Medium.ttf', 'Helvetica'),
             'sb': ('Mont-SB', 'Montserrat-SemiBold.ttf', 'Helvetica-Bold'),
             'b': ('Mont-B', 'Montserrat-Bold.ttf', 'Helvetica-Bold'),
             'i': ('Mont-It', 'Montserrat-Italic.ttf', 'Helvetica-Oblique'),
             'mi': ('Mont-MdIt', 'Montserrat-MediumItalic.ttf', 'Helvetica-Oblique')}
    for k, (name, fn, fb) in tabla.items():
        p = os.path.join(_FONTS, fn)
        try:
            if not os.path.exists(p):
                raise IOError(fn)
            pdfmetrics.registerFont(TTFont(name, p))
            _F[k] = name
        except Exception:
            _F[k] = fb
    try:
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        if _F['r'] == 'Mont':
            registerFontFamily('Mont', normal=_F['r'], bold=_F['sb'],
                               italic=_F['i'], boldItalic=_F['mi'])
    except Exception:
        pass
    _F['g'] = rc.GLYPHF()
    return _F


def X(x):
    return x * K


def Y(y):
    return (PH - y) * K


def esc(t):
    return (t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def G(ch, col, size=None):
    """Glifo en línea dentro de un Paragraph (fuente de glifos, nunca cursiva)."""
    f = _fonts()['g']
    if f == 'Helvetica':
        return ''
    s = (' size="%.2f"' % (size * K)) if size else ''
    return '<font name="%s" color="%s"%s>%s</font>' % (f, col, s, ch)


def sign_g(idx, size=None):
    return G(rc.SIGN_GLYPH[idx], rc.SIGN_COL[idx], size)


def asp_g(typ, size=None, col=None):
    c, g, _ = rc.ASPECTS[typ.lower()]
    return G(g, col or c, size)


class D(object):
    """Capa de dibujo en px con origen arriba-izquierda."""

    def __init__(self, c):
        self.c = c
        self.f = _fonts()

    # formas ---------------------------------------------------------------
    def rr(self, x, y, w, h, r=0, fill=None, stroke=None, lw=1, alpha=1.0):
        c = self.c
        c.saveState()
        if fill:
            c.setFillColor(HexColor(fill))
            if alpha < 1:
                c.setFillAlpha(alpha)
        if stroke:
            c.setStrokeColor(HexColor(stroke)); c.setLineWidth(lw * K)
        r = max(0, min(r, w / 2.0, h / 2.0))
        if r > 0:
            c.roundRect(X(x), Y(y + h), w * K, h * K, r * K,
                        stroke=1 if stroke else 0, fill=1 if fill else 0)
        else:
            c.rect(X(x), Y(y + h), w * K, h * K,
                   stroke=1 if stroke else 0, fill=1 if fill else 0)
        c.restoreState()

    def ln(self, x1, y1, x2, y2, col, lw=1, dash=None, alpha=1.0, cap=0):
        c = self.c
        c.saveState()
        c.setStrokeColor(HexColor(col)); c.setLineWidth(lw * K); c.setLineCap(cap)
        if alpha < 1:
            c.setStrokeAlpha(alpha)
        if dash:
            c.setDash([d * K for d in dash])
        c.line(X(x1), Y(y1), X(x2), Y(y2))
        c.restoreState()

    def poly(self, pts, col, lw=1, alpha=1.0):
        c = self.c
        c.saveState()
        c.setStrokeColor(HexColor(col)); c.setLineWidth(lw * K)
        c.setLineJoin(1); c.setLineCap(1)
        if alpha < 1:
            c.setStrokeAlpha(alpha)
        p = c.beginPath()
        p.moveTo(X(pts[0][0]), Y(pts[0][1]))
        for a, b in pts[1:]:
            p.lineTo(X(a), Y(b))
        c.drawPath(p, stroke=1, fill=0)
        c.restoreState()

    def shape(self, pts, fill=None, stroke=None, lw=1):
        c = self.c
        c.saveState()
        if fill:
            c.setFillColor(HexColor(fill))
        if stroke:
            c.setStrokeColor(HexColor(stroke)); c.setLineWidth(lw * K)
        p = c.beginPath()
        p.moveTo(X(pts[0][0]), Y(pts[0][1]))
        for a, b in pts[1:]:
            p.lineTo(X(a), Y(b))
        p.close()
        c.drawPath(p, stroke=1 if stroke else 0, fill=1 if fill else 0)
        c.restoreState()

    def circ(self, cx, cy, r, fill=None, stroke=None, lw=1):
        c = self.c
        c.saveState()
        if fill:
            c.setFillColor(HexColor(fill))
        if stroke:
            c.setStrokeColor(HexColor(stroke)); c.setLineWidth(lw * K)
        c.circle(X(cx), Y(cy), r * K, stroke=1 if stroke else 0, fill=1 if fill else 0)
        c.restoreState()

    def diamond(self, cx, cy, half, fill=None, stroke=None, lw=1):
        self.shape([(cx, cy - half), (cx + half, cy), (cx, cy + half), (cx - half, cy)],
                   fill, stroke, lw)

    # texto ----------------------------------------------------------------
    def tw(self, s, font, size, track=0):
        return pdfmetrics.stringWidth(s, self.f.get(font, font), size) + track * max(0, len(s) - 1)

    def tx(self, x, y, s, font='r', size=11, col=INK, align='l', track=0):
        """Texto de una línea; y = línea base (px)."""
        c = self.c
        fn = self.f.get(font, font)
        w = self.tw(s, font, size, track)
        if align == 'c':
            x -= w / 2.0
        elif align == 'r':
            x -= w
        c.setFillColor(HexColor(col)); c.setFont(fn, size * K)
        c.drawString(X(x), Y(y), s, charSpace=track * K)
        return w

    def fit(self, s, font, size, maxw, track=0, minsize=7.0):
        """Reduce el tamaño (y, si hace falta, recorta con …) hasta caber."""
        while size > minsize and self.tw(s, font, size, track) > maxw:
            size -= 0.25
        if self.tw(s, font, size, track) > maxw:
            while len(s) > 4 and self.tw(s + '…', font, size, track) > maxw:
                s = s[:-1]
            s = s.rstrip(' ,·') + '…'
        return s, size

    def _para(self, markup, w, font, size, col, lead, align):
        st = ParagraphStyle('p', fontName=self.f.get(font, font), fontSize=size * K,
                            leading=size * lead * K, textColor=HexColor(col),
                            alignment={'l': TA_LEFT, 'c': TA_CENTER, 'r': TA_RIGHT}[align])
        p = Paragraph(markup, st)
        _, h = p.wrap(w * K, 10000)
        return p, h / K

    def ph(self, markup, w, font='r', size=11.5, col=INK, lead=1.6, align='l'):
        return self._para(markup, w, font, size, col, lead, align)[1]

    def para(self, x, top, w, markup, font='r', size=11.5, col=INK, lead=1.6, align='l'):
        """Párrafo con ajuste de línea; devuelve el alto (px)."""
        p, h = self._para(markup, w, font, size, col, lead, align)
        p.drawOn(self.c, X(x), Y(top + h))
        return h

    # glifos ---------------------------------------------------------------
    def gch(self, ch, cx, cy, size, col):
        c = self.c
        if self.f['g'] == 'Helvetica':
            return
        c.setFillColor(HexColor(col)); c.setFont(self.f['g'], size * K)
        c.drawCentredString(X(cx), Y(cy) - size * K * 0.36, ch)

    def planet(self, key, cx, cy, size, col=None):
        g, pc, _ = rc.PLANETS.get(key, ('?', MUTED, ''))
        col = col or pc
        if key == 'aPluton':
            rc._draw_pluto(self.c, X(cx), Y(cy), size * 0.78 * K, HexColor(col))
        elif key == 'aTierra':
            rc._draw_earth(self.c, X(cx), Y(cy), size * 0.66 * K, HexColor(col))
        else:
            self.gch(g, cx, cy, size, col)

    def moon(self, cx, cy, r, elong, ring=0.8):
        """Fase lunar: disco NAVY con la parte iluminada en CREAM."""
        import math
        ang = elong % 360.0
        self.circ(cx, cy, r, fill=NAVY, stroke=GOLD, lw=ring)
        wan = ang > 180.0
        a = 360.0 - ang if wan else ang
        if a < 4:
            return
        sgn = -1.0 if wan else 1.0
        k = math.cos(math.radians(a))
        pts = []
        n = 28
        for i in range(n + 1):                      # limbo iluminado (arriba → abajo)
            t = math.pi * i / n
            pts.append((cx + sgn * r * math.sin(t), cy - r * math.cos(t)))
        for i in range(n + 1):                      # terminador (abajo → arriba)
            t = math.pi * (n - i) / n
            pts.append((cx + sgn * r * k * math.sin(t), cy - r * math.cos(t)))
        self.shape(pts, fill=CREAM)
        self.circ(cx, cy, r, stroke=GOLD, lw=ring)

    def elem_icon(self, elem, x, y, s=16):
        """Triángulos de los elementos (trazo 1,8)."""
        col = ELEM_COL[elem]
        up = elem in ('Fuego', 'Aire')
        pad = 2.5
        if up:
            pts = [(x + s / 2.0, y + pad), (x + s - pad, y + s - pad), (x + pad, y + s - pad)]
            ybar = y + s * 0.62
        else:
            pts = [(x + pad, y + pad), (x + s - pad, y + pad), (x + s / 2.0, y + s - pad)]
            ybar = y + s * 0.38
        self.poly(pts + [pts[0]], col, 1.8)
        if elem in ('Aire', 'Tierra'):
            self.ln(x + 1.5, ybar, x + s - 1.5, ybar, col, 1.8, cap=1)


# ════════════════════════════════════════════════════════════════════════
#  Elementos comunes
# ════════════════════════════════════════════════════════════════════════

def _footer(d, n, web):
    d.ln(ML, 1079, PW - ML, 1079, HAIR, 1)
    w = d.tx(ML, 1097, "REPORTE ASTRAL", 'b', 9, INK, track=1)
    d.tx(ML + w + 8, 1097, "·  Tránsitos Semanales  ·  Mauricio Puerta  ·  " + web,
         'r', 9, MUTED)
    cx, cy = PW - ML - 11, 1094
    d.diamond(cx, cy, 11.3, stroke=GOLD, lw=1)
    d.tx(cx, cy + 3.2, str(n), 'sb', 9, INK, 'c')


def _runhead(d, L):
    bits = ["REPORTE ASTRAL"]
    if L['name']:
        bits.append(L['name'].upper())
    quien = "%s, %s" % (L['nac_hora'], L['nac_fecha']) if L['nac_hora'] else L['nac_fecha']
    if L.get('natal_lugar'):
        quien += ", " + L['natal_lugar']
    bits.append(quien.upper())
    s = "  —  ".join(bits)
    track = 2.0
    while track > 0.4 and d.tw(s, 'r', 10, track) > CW:
        track -= 0.2
    s, size = d.fit(s, 'r', 10, CW, track)
    d.tx(PW / 2.0, 36, s, 'r', size, MUTED, 'c', track)
    y = 50
    d.ln(PW / 2.0 - 98, y, PW / 2.0 - 8, y, GOLD, 1)
    d.ln(PW / 2.0 + 8, y, PW / 2.0 + 98, y, GOLD, 1)
    d.diamond(PW / 2.0, y, 4.5, fill=GOLD)


def _titulo(d, kicker, h2, sub):
    d.tx(ML, 78, kicker, 'sb', 9, GOLD_D, track=3)
    d.tx(ML, 103, h2, 'sb', 22, NAVY, track=-0.2)
    d.tx(ML, 122, sub, 'mi', 12, GOLD_D)
    return 134


def _kicker(d, x, y, s, col=GOLD_D, size=9, align='l'):
    return d.tx(x, y, s, 'sb', size, col, align, track=3 if size >= 9 else 2.4)


# ════════════════════════════════════════════════════════════════════════
#  Página 1 — El cielo y la agenda
# ════════════════════════════════════════════════════════════════════════

def _page1(d, L, data, web):
    c = d.c
    # 3.1 Encabezado
    d.rr(0, 0, PW, 150, fill=NAVY)
    d.rr(10, 10, PW - 20, 130, stroke=GOLD_S, lw=1)
    c.saveState(); c.setStrokeAlpha(0.5)
    d.rr(14, 14, PW - 28, 122, stroke=GOLD_S, lw=0.75)
    c.restoreState()
    _kicker(d, ML, 54, "REPORTE ASTRAL · TRÁNSITOS SEMANALES", GOLD_S)
    d.tx(ML, 91, "El cielo en esta semana", 'b', 30, WHITE, track=-0.5)
    linea = ((L['name'] + " · ") if L['name'] else "") + "del " + L['rango']
    linea, sz = d.fit(linea, 'mi', 13, 400, 0, 10)
    d.tx(ML, 116, linea, 'mi', sz, GOLD_S)
    # columnas derechas
    xa, wa = 474, 132
    xb, wb = 628, 126
    c.saveState(); c.setStrokeAlpha(0.5)
    d.ln(616, 50, 616, 104, GOLD_S, 1)
    c.restoreState()
    _kicker(d, xa, 58, "NACIMIENTO", GOLD_S, 8.5)
    s, sz = d.fit("%s · %s h" % (L['nac_fecha'], L['nac_hora']), 'r', 11, wa, 0, 8.5)
    d.tx(xa, 79, s, 'r', sz, CREAM)
    s, sz = d.fit(L.get('natal_lugar') or '', 'r', 11, wa, 0, 8.5)
    d.tx(xa, 97, s, 'r', sz, CREAM)
    _kicker(d, xb, 58, "SEMANA", GOLD_S, 8.5)
    d.tx(xb, 79, "%s · 00:00 h" % L['sem_inicio'], 'r', 11, CREAM)
    s, sz = d.fit((L['lugar'] or '') + "*", 'r', 11, wb, 0, 8.5)
    d.tx(xb, 97, s, 'r', sz, CREAM)

    # 3.2 Rueda + columna derecha
    top, bh = 166, 485
    d.rr(ML, top, 400, bh, 14, fill=WHITE, stroke=HAIR, lw=1)
    _kicker(d, ML + 200, top + 24, "EL CIELO DEL LUNES SOBRE SU CARTA NATAL", align='c',
            size=8.5)
    wcy = top + 34 + 178
    size_px = 1000.0 * 178.0 / 524.0
    rc.draw_biwheel(c, data['natal'], data['transit'],
                    X(ML + 200) - size_px * K / 2.0, Y(wcy) - size_px * K / 2.0,
                    size_px * K)
    # leyenda compacta
    ly = top + 34 + 356 + 6
    d.ln(ML + 12, ly, ML + 388, ly, HAIR, 1)
    x0, x1 = ML + 14, ML + 388
    x, y = x0, ly + 16
    leg = [('aSol', 'Sol'), ('aLuna', 'Luna'), ('aMercurio', 'Mercurio'), ('aVenus', 'Venus'),
           ('aMarte', 'Marte'), ('aJupiter', 'Júpiter'), ('aSaturno', 'Saturno'),
           ('aUrano', 'Urano'), ('aNeptuno', 'Neptuno'), ('aPluton', 'Plutón'),
           ('aChiron', 'Quirón'), ('aNoduloNorte', 'Nodo Norte'),
           ('aLunaNegra', 'Luna Negra'), ('aRuedaFortuna', 'Fortuna')]
    for key, nm in leg:
        w = 14 + d.tw(nm, 'r', 8.5)
        if x + w > x1:
            x = x0; y += 14
        d.planet(key, x + 5, y - 3, 12)
        d.tx(x + 13, y, nm, 'r', 8.5, INK)
        x += w + 8
    x = x0; y += 16
    for typ in ('Conjunction', 'Opposition', 'Square', 'Trine', 'Sextile'):
        col, gl, nm = rc.ASPECTS[typ.lower()]
        w = 14 + 12 + d.tw(nm, 'r', 8.5)
        if x + w > x1:
            x = x0; y += 14
        d.rr(x, y - 4, 12, 2, fill=col)
        d.gch(gl, x + 19, y - 3, 10, col)
        d.tx(x + 26, y, nm, 'r', 8.5, INK)
        x += w + 8
    w = d.tw("00° 00′", 'sb', 8.5) + 4 + d.tw("retrógrado", 'r', 8.5)
    if x + w > x1:
        x = x0; y += 14
    w1 = d.tx(x, y, "00° 00′", 'sb', 8.5, RETRO)
    d.tx(x + w1 + 4, y, "retrógrado", 'r', 8.5, INK)

    # columna derecha
    rx, rw = 458, 296
    iw = rw - 36
    hp = d.ph(esc(L['frase']), iw, 'mi', 15, WHITE, 1.5)
    fh = 16 + 14 + 6 + hp + 16
    d.rr(rx, top, rw, fh, 14, fill=NAVY)
    _kicker(d, rx + 18, top + 27, "SU SEMANA EN UNA FRASE", GOLD_S, 8.5)
    d.para(rx + 18, top + 36, iw, esc(L['frase']), 'mi', 15, WHITE, 1.5)

    ey = top + fh + 14
    eh = top + bh - ey
    d.rr(rx, ey, rw, eh, 14, fill=WHITE, stroke=HAIR, lw=1)
    E = L['elementos']
    _kicker(d, rx + 18, ey + 27, "CÓMO ESTÁ REPARTIDO EL CIELO", size=8.5)
    nota_el = "Barra: el cielo del lunes · línea: sus planetas natales en ese elemento"
    nel_h = d.para(rx + 18, ey + 32, iw, nota_el, 'r', 8.5, MUTED, 1.4)
    mods_h = 58
    fr_h = d.ph(esc(E['frase']), iw, 'mi', 11.5, GOLD_D, 1.5)
    libre = eh - (40 + nel_h) - mods_h - fr_h - 16
    rowh = max(21.0, min(34.0, libre / 4.0))
    mx = float(max(5, max(E['trans'].values()), max(E['natal'].values())))
    bx = rx + 18 + 16 + 7 + 44 + 7
    bw = iw - 16 - 44 - 64 - 21
    yy = ey + 40 + nel_h
    for el in wl.ELEMENTOS:
        cy = yy + rowh / 2.0
        d.elem_icon(el, rx + 18, cy - 8, 16)
        d.tx(rx + 18 + 23, cy + 3.7, el, 'sb', 10.5, NAVY)
        d.rr(bx, cy - 4, bw, 8, 4, fill=WHITE, stroke=HAIR, lw=1)
        n = E['trans'][el]
        if n:
            d.rr(bx, cy - 4, max(8, bw * n / mx), 8, 4, fill=ELEM_COL[el])
        nx = bx + bw * E['natal'][el] / mx
        d.rr(min(max(nx - 1, bx), bx + bw - 2), cy - 7, 2, 14, fill=NAVY)
        ks = E['glifos'][el]
        if ks:
            step = min(13.0, 62.0 / len(ks))
            gx = bx + bw + 7 + 6
            for k in ks:
                d.planet(k, gx, cy, 13 if step >= 12 else 11)
                gx += step
        yy += rowh
    d.para(rx + 18, yy + 4, iw, esc(E['frase']), 'mi', 11.5, GOLD_D, 1.5)
    my = ey + eh - mods_h
    d.ln(rx + 18, my, rx + rw - 18, my, HAIR, 1)
    for i, lab in enumerate(('CARDINALES', 'FIJOS', 'MUTABLES')):
        cx = rx + 18 + iw * (i + 0.5) / 3.0
        d.tx(cx, my + 26, str(E['mods'][i]), 'b', 16, NAVY, 'c')
        d.tx(cx, my + 42, lab, 'r', 8.5, MUTED, 'c', track=1.2)

    # 3.3 Agenda
    ay = top + bh + 18
    d.tx(ML, ay + 15, "Agenda de la semana", 'sb', 17, NAVY, track=-0.2)
    d.tx(PW - ML, ay + 14, "cambios de signo, fases, aspectos y, en rojo, cambios de rumbo",
         'i', 10, MUTED, 'r')
    T = ay + 30
    gap = 6.0
    colw = (CW - 6 * gap) / 7.0
    cxs = [ML + colw / 2.0 + i * (colw + gap) for i in range(7)]
    ny = T + 31
    d.ln(cxs[0], ny, cxs[-1], ny, GOLD, 1)
    nota_h = d.ph(esc(L['nota']), CW, 'r', 8.5, MUTED, 1.45)
    limite = 1079 - 10 - nota_h - 10
    ev0 = ny + 15 + 12

    def markup(e):
        col = RETRO if e['red'] else INK
        out = []
        for j, p in enumerate(e['parts']):
            if isinstance(p, tuple):
                if p[0] == 'sign':
                    out.append(sign_g(p[1], 10))
                else:
                    out.append(asp_g(p[1], 10))
            else:
                t = esc(p)
                # el glifo nunca queda solo en otra línea
                if t.endswith(' ') and j + 1 < len(e['parts']) and \
                        isinstance(e['parts'][j + 1], tuple) and e['parts'][j + 1][0] == 'sign':
                    t = t[:-1] + '&nbsp;'
                out.append(t)
        return '<font color="%s">%s</font>' % (col, ''.join(out))

    for i in range(7):
        cx = cxs[i]
        d.tx(cx, T + 9, DIAS_AB[i], 'sb', 8.5, GOLD_D, 'c', track=2)
        evs = list(L['agenda'][i])
        if len(evs) > 3:
            keep = sorted(evs, key=lambda e: (e['prio'], e['jd']))[:3]
            evs = [e for e in evs if e in keep]

        def alto(e):
            return 28 + 4 + 11 + 3 + d.ph(markup(e), colw, 'r', 9.5, INK, 1.35, 'c')
        while evs and sum(alto(e) for e in evs) + 12 * (len(evs) - 1) > limite - ev0:
            peor = max(evs, key=lambda e: (e['prio'], e['jd']))
            evs.remove(peor)
        # línea punteada
        if evs:
            yb = ev0 + sum(alto(e) for e in evs[:-1]) + 12 * (len(evs) - 1) + 4
            d.ln(cx, ny + 15, cx, yb, GOLD, 1, dash=[3, 3], alpha=0.7)
        # nodo del día
        d.circ(cx, ny, 19, fill=WHITE)
        d.circ(cx, ny, 15, fill=NAVY)
        d.tx(cx, ny + 4.3, str(L['dias'][i]), 'b', 12, WHITE, 'c')
        y = ev0
        if not evs:
            d.para(cx - colw / 2.0, y, colw, "Sin eventos: avance con lo pendiente",
                   'i', 9, MUTED, 1.35, 'c')
        for e in evs:
            h = alto(e)
            col = RETRO if e['red'] else GOLD_D
            d.rr(cx - colw / 2.0, y - 2, colw, h + 4, fill=WHITE)
            d.circ(cx, y + 14, 14, fill=WHITE, stroke=RETRO if e['red'] else HAIR, lw=1.5)
            if e['icon'][0] == 'phase':
                d.moon(cx, y + 14, 8, e['icon'][1], ring=0.6)
            else:
                d.planet(e['icon'][1], cx, y + 14, 13)
            d.tx(cx, y + 28 + 4 + 8.5, e['time'], 'b', 8.5, col, 'c')
            d.para(cx - colw / 2.0, y + 28 + 4 + 11 + 1, colw, markup(e), 'r', 9.5, INK, 1.35, 'c')
            y += h + 12

    # nota + pie
    d.para(ML, 1079 - 10 - nota_h, CW, esc(L['nota']), 'r', 8.5, MUTED, 1.45)
    _footer(d, 1, web)


# ════════════════════════════════════════════════════════════════════════
#  Página 2 — Su semana de un vistazo
# ════════════════════════════════════════════════════════════════════════

def _barra(d, x0, y0, data):
    """Barra «El recorrido de la semana por sus casas» (714 × 170 px)."""
    W = CW
    cusps = [h['lon'] for h in data['natal']['houses']]
    cw = W / 12.0

    def xof(lon):
        for i in range(12):
            span = (cusps[(i + 1) % 12] - cusps[i]) % 360.0
            dd = (lon - cusps[i]) % 360.0
            if dd < span:
                return (i + dd / span) * cw
        return 0.0

    # franja de signos
    for s in range(12):
        a = xof(s * 30.0 + 0.0001)
        b = xof(s * 30.0 + 29.9999)
        segs = [(a, b)] if b >= a else [(a, W), (0.0, b)]
        col = rc.SIGN_COL[s]
        for (p, q) in segs:
            w = q - p - 3
            if w <= 1:
                continue
            d.rr(x0 + p + 1.5, y0, w, 22, 5, fill=col, alpha=0.18)
            if w > 14:
                d.gch(rc.SIGN_GLYPH[s], x0 + p + 1.5 + w / 2.0, y0 + 11, 13, col)
    # panel de planetas y casas
    for i in range(12):
        bx = x0 + i * cw + 1.5
        d.rr(bx, y0 + 25, cw - 3, 110, 5, fill=TINT)
        d.rr(bx, y0 + 138, cw - 3, 32, 5, fill=NAVY)
        cx = bx + (cw - 3) / 2.0
        ang = {0: 'AC', 3: 'IC', 6: 'DSC', 9: 'MC'}.get(i)
        if ang:
            w1 = d.tw(ang, 'b', 7.5, 0.6)
            w2 = d.tw(ROMAN[i], 'b', 13)
            sx = cx - (w1 + 5 + w2) / 2.0
            d.tx(sx, y0 + 138 + 20, ang, 'b', 7.5, GOLD_S, track=0.6)
            d.tx(sx + w1 + 5, y0 + 138 + 21, ROMAN[i], 'b', 13, GOLD_S)
        else:
            d.tx(cx, y0 + 138 + 20.5, ROMAN[i], 'm', 12, CREAM, 'c')

    snap = {p['key']: p for p in data['transit']['planets']}
    fin = data.get('transit_end', {})
    keys = [k for k in ['aSol', 'aLuna', 'aMercurio', 'aVenus', 'aMarte', 'aJupiter',
                        'aSaturno', 'aUrano', 'aNeptuno', 'aPluton', 'aChiron',
                        'aNoduloNorte'] if k in snap]
    xs = {k: xof(snap[k]['lon']) for k in keys}
    orden = sorted(keys, key=lambda k: xs[k])
    gx = [xs[k] for k in orden]
    for _ in range(200):
        mov = False
        for i in range(len(gx) - 1):
            dif = gx[i + 1] - gx[i]
            if dif < 24:
                ad = (24 - dif) / 2.0
                gx[i] -= ad; gx[i + 1] += ad; mov = True
        for i in range(len(gx)):
            gx[i] = min(max(gx[i], 11), W - 11)
        if not mov:
            break
    gpos = dict(zip(orden, gx))
    # recorrido semanal
    for j, k in enumerate(['aLuna', 'aSol', 'aMercurio', 'aVenus', 'aMarte']):
        if k not in snap or k not in fin:
            continue
        col = rc.PLANETS[k][1]
        a = xs[k]; b = xof(fin[k]['lon'])
        dlon = ((fin[k]['lon'] - snap[k]['lon'] + 180) % 360) - 180
        if dlon >= 0:
            segs = [(a, b)] if b >= a else [(a, W - 2), (2, b)]
        else:
            segs = [(a, b)] if b <= a else [(a, 2), (W - 2, b)]
        if sum(abs(q - p) for p, q in segs) <= 6:
            continue
        ly = y0 + 102 + 8 * j
        for p, q in segs:
            d.ln(x0 + p, ly, x0 + q, ly, col, 2, cap=1)
        d.circ(x0 + a, ly, 2, fill=col)
        p, q = segs[-1]
        s = 1 if dlon >= 0 else -1
        d.shape([(x0 + q + s * 3, ly), (x0 + q - s * 3, ly - 3.5), (x0 + q - s * 3, ly + 3.5)],
                fill=col)
        if k == 'aLuna':
            lab = "la Luna el domingo"
            lw_ = d.tw(lab, 'sb', 8)
            if s > 0 and q + 8 + lw_ < W - 4:
                d.tx(x0 + q + 8, ly + 2.8, lab, 'sb', 8, INK)
            else:
                d.tx(x0 + min(p, q) - 8, ly + 2.8, lab, 'sb', 8, INK, 'r')
    # guías, puntos y glifos
    for k in keys:
        col = rc.PLANETS[k][1]
        x = xs[k]; g = gpos[k]
        d.poly([(x0 + g, y0 + 54), (x0 + g, y0 + 60), (x0 + x, y0 + 74), (x0 + x, y0 + 86)],
               col, 1.2, alpha=0.8)
        d.circ(x0 + x, y0 + 89, 4, fill=col, stroke=WHITE, lw=1.5)
        d.planet(k, x0 + g, y0 + 42, 17)
        if snap[k].get('retrograde') and k != 'aNoduloNorte':
            d.tx(x0 + g + 7, y0 + 35, "R", 'b', 8, RETRO)


def _page2(d, L, data, web):
    _runhead(d, L)
    y = _titulo(d, "PÁGINA 2", "Su semana de un vistazo",
                "Lo esencial, para que sepa con qué viento cuenta.")
    # medidas
    intro_h = d.ph(esc(L['intro']), CW - 16, 'r', 12, INK, 1.65)
    bt_h = d.ph(esc(L['barra_texto']), CW, 'r', 10.5, INK, 1.55) if L['barra_texto'] else 0
    nf = len(L['fases'])
    fw = (CW - 12 * (nf - 1)) / float(nf)
    ftw = fw - 32 - 42 - 12
    f_h = max(max(42, 18 + 15 + d.ph(esc(f['texto']), ftw, 'r', 11, INK, 1.55))
              for f in L['fases']) + 28
    nc = max(1, len(L['clima']))
    cw_ = (CW - 12 * (nc - 1)) / float(nc)
    ctw = cw_ - 36

    def clima_h(cl):
        return 32 + 44 + sum(d.ph(esc(p), ctw, 'r', 11.5, INK, 1.6) + 7 for p in cl['paras'])
    c_h = max([clima_h(cl) for cl in L['clima']] or [0])
    total = intro_h + (24 + 170 + 10 + bt_h) + (18 + f_h) + (18 + c_h)
    libre = (1079 - 16) - (y + 4) - total
    gap = max(12.0, min(46.0, libre / 3.0))

    # 4.2 introducción
    y += 4
    d.rr(ML, y + 3, 2, intro_h - 2, fill=GOLD)
    d.para(ML + 16, y, CW - 16, esc(L['intro']), 'r', 12, INK, 1.65)
    y += intro_h + gap
    # 4.3 barra
    d.tx(ML, y + 13, "El recorrido de la semana por sus casas", 'sb', 16, NAVY, track=-0.2)
    d.tx(PW - ML, y + 12, "punto: lunes 00:00 · flecha: hasta el domingo", 'i', 10, MUTED, 'r')
    y += 24
    _barra(d, ML, y, data)
    y += 170 + 10
    if L['barra_texto']:
        d.para(ML, y, CW, esc(L['barra_texto']), 'r', 10.5, INK, 1.55)
    y += bt_h + gap
    # 4.4 fases
    _kicker(d, ML, y + 9, "LA LUNA Y SUS FASES")
    y += 18
    for i, f in enumerate(L['fases']):
        fx = ML + i * (fw + 12)
        d.rr(fx, y, fw, f_h, 12, fill=WHITE, stroke=HAIR, lw=1)
        d.moon(fx + 16 + 21, y + 14 + 21, 21, f['elong'])
        tx_ = fx + 16 + 42 + 12
        tit = esc(f['titulo']) + ((' ' + sign_g(f['sign'], 13)) if f['sign'] is not None else '')
        d.para(tx_, y + 12, ftw, '<font color="%s">%s</font>' % (NAVY, tit), 'sb', 13, NAVY, 1.25)
        d.tx(tx_, y + 14 + 28, f['fecha'], 'r', 9.5, MUTED)
        d.para(tx_, y + 14 + 34, ftw, esc(f['texto']), 'r', 11, INK, 1.55)
    y += f_h + gap
    # 4.5 clima
    _kicker(d, ML, y + 9, "EL CLIMA DE LA SEMANA")
    y += 18
    for i, cl in enumerate(L['clima']):
        cx = ML + i * (cw_ + 12)
        d.rr(cx, y, cw_, c_h, 12, fill=WHITE, stroke=HAIR, lw=1)
        d.circ(cx + 18 + 17, y + 16 + 17, 17, fill=TINT)
        d.planet(cl['key'], cx + 18 + 17, y + 16 + 17, 18)
        _kicker(d, cx + 18 + 44, y + 16 + 11, cl['kicker'], size=8.5)
        tit = esc(cl['titulo']) + sign_g(cl['sign'], 13) + esc(cl['titulo2'])
        s_ = 13.5
        while s_ > 10.5 and d.ph(tit, ctw - 44, 'sb', s_, NAVY, 1.2) > s_ * 1.5:
            s_ -= 0.5
        d.para(cx + 18 + 44, y + 16 + 15, ctw - 44, tit, 'sb', s_, NAVY, 1.2)
        py = y + 16 + 44
        for p in cl['paras']:
            py += d.para(cx + 18, py, ctw, esc(p), 'r', 11.5, INK, 1.6) + 7
    _footer(d, 2, web)


# ════════════════════════════════════════════════════════════════════════
#  Página 3 — Lo que el cielo le hace a usted
# ════════════════════════════════════════════════════════════════════════

def _page3(d, L, data, web, brand):
    c = d.c
    _runhead(d, L)
    y0 = _titulo(d, "PÁGINA 3", "Lo que el cielo le hace a usted",
                 "Su Sol, su Luna y su Ascendente, uno por uno.") + 4
    RX, RW = ML + 150 + 18, CW - 150 - 18

    def textos(m):
        out = []
        for p in L['puntos']:
            if p['evento']:
                t = resumen(p['db'], 90, m)
            else:
                t = wl.recorta(p['db'], m)
            out.append(t)
        return out

    filas = L['tablero']['filas']
    nrows = max(1, len(filas))
    LW = 186.0
    W4 = CW - 36 - (162 + LW + 12 + 162)
    fila_h = [max(31.0, d.ph(esc(f['hacer']), W4, 'r', 10, INK, 1.25) + 10) for f in filas] or [31.0]
    tab_h = 14 + 22 + 18 + sum(fila_h) + 24 + 12
    cl_h = 12 + 14 + 22 + max(d.ph(esc(k[2]), (CW - 20) / 3.0 - 28, 'r', 11, INK, 1.5)
                              for k in L['claves']) + 14
    web_cta = web
    cta_txt = ('Este reporte es un resumen. Para ver con calma lo que estos tránsitos '
               'significan en su vida, solicite su estudio en '
               '<font color="%s"><b>%s</b></font> o en la app '
               '<font color="%s"><b>Diario Astral</b></font>, su brújula cósmica personal.'
               % (GOLD_S, web_cta, GOLD_S))
    ctw = CW - 44 - 84 - 150 - 40
    cta_h = max(84, 14 + 24 + d.ph(cta_txt, ctw, 'r', 11, CREAM, 1.55)) + 36
    legal = ("La astrología orienta, no predice: use su sentido común y su propio juicio. "
             "Interpretaciones con fines de orientación y entretenimiento · © Mauricio Puerta®")
    lg_h = d.ph(esc(legal), CW, 'r', 8.5, MUTED, 1.45, 'c')
    fijo = tab_h + cl_h + cta_h + lg_h + 10
    disp = (1079 - 10) - y0

    txts, rows_h = [], []
    for m in (300, 270, 240, 210, 180, 150, 120):
        txts = textos(m)
        rows_h = [20 + max(40, 20 + d.ph(esc(t), RW, 'r', 11.5, INK, 1.6)) for t in txts]
        if sum(rows_h) + fijo + 3 * 12 <= disp:
            break
    libre = disp - sum(rows_h) - fijo
    gap = max(10.0, min(40.0, libre / 3.0))

    # 5.2 Sol / Luna / Ascendente
    y = y0
    for p, t, h in zip(L['puntos'], txts, rows_h):
        d.ln(ML, y, PW - ML, y, HAIR, 1)
        d.circ(ML + 18, y + 10 + 18, 18, fill=TINT)
        if p['nk'] == 'aAsc':
            d.tx(ML + 18, y + 10 + 22.3, "Ac", 'b', 12, NAVY, 'c')
        else:
            d.planet(p['nk'], ML + 18, y + 10 + 18, 20)
        d.tx(ML + 46, y + 10 + 15, p['nombre'], 'b', 13, NAVY)
        d.para(ML + 46, y + 10 + 19, 104,
               esc(p['pos']).replace(' ', '&nbsp;') + sign_g(p['sign'], 9.5)
               + esc(p['pos2']).replace('Casa ', 'Casa&nbsp;'), 'r', 9, MUTED, 1.3)
        if p['evento']:
            e = p['evento']
            pc = rc.PLANETS[e['tk']][1]
            d.planet(e['tk'], RX + 7, y + 10 + 8, 14)
            d.gch(rc.ASPECTS[e['typ'].lower()][1], RX + 24, y + 10 + 8, 12,
                  rc.ASPECTS[e['typ'].lower()][0])
            d.tx(RX + 36, y + 10 + 12.5, e['texto'], 'sb', 12, GOLD_D)
        else:
            d.tx(RX, y + 10 + 12.5, p['calma'], 'sb', 12, MUTED)
        d.para(RX, y + 10 + 18, RW, esc(t), 'r', 11.5, INK, 1.6)
        y += h
    d.ln(ML, y, PW - ML, y, HAIR, 1)
    y += gap

    # 5.3 Tablero de retrógrados
    d.rr(ML, y, CW, tab_h, 14, fill=CREAM)
    ix = ML + 18
    wt = d.tx(ix, y + 14 + 14, "Tablero de retrógrados", 'sb', 16, NAVY, track=-0.2)
    if L['tablero']['directos']:
        s, sz = d.fit(L['tablero']['directos'], 'i', 9.5, CW - 36 - wt - 16, 0, 7.5)
        d.tx(PW - ML - 18, y + 14 + 13, s, 'i', sz, MUTED, 'r')
    c1, c2, c3, c4 = ix, ix + 162, ix + 162 + LW + 12, ix + 162 + LW + 12 + 162
    w4 = (ML + CW - 18) - c4
    hy = y + 14 + 22 + 12
    d.tx(c1, hy, "PLANETA", 'sb', 8, GOLD_D, track=1.2)
    for k, ch in enumerate("LMMJVSD"):
        d.tx(c2 + LW * (k + 0.5) / 7.0, hy, ch, 'sb', 8, GOLD_D, 'c')
    d.tx(c3, hy, "EN SU CARTA", 'sb', 8, GOLD_D, track=1.2)
    d.tx(c4, hy, "QUÉ HACER", 'sb', 8, GOLD_D, track=1.2)
    ry = hy + 6
    if not filas:
        d.ln(ix, ry, PW - ML - 18, ry, SEP, 1)
        d.tx(ix, ry + 20, "Ningún planeta está retrógrado ni cambia de rumbo esta semana: "
             "vía libre para avanzar.", 'r', 10.5, INK)
    for f, fh_ in zip(filas, fila_h):
        d.ln(ix, ry, PW - ML - 18, ry, SEP, 1)
        cy = ry + fh_ / 2.0
        d.planet(f['key'], c1 + 8, cy, 15)
        wn = d.tx(c1 + 22, cy + 4, f['name'], 'sb', 11, NAVY)
        d.tx(c1 + 22 + wn + 6, cy + 3.5, f['estado_txt'], 'sb', 8.5,
             GOLD_D if f['estado'] == 'D' else RETRO)
        # línea de la semana
        for k in range(1, 7):
            d.rr(c2 + LW * k / 7.0 - 0.5, cy - 4, 1, 8, fill=HAIR)
        if f['hours'] is None:
            d.ln(c2, cy, c2 + LW, cy, RETRO, 2, dash=[5, 3])
        else:
            xh = c2 + LW * max(0.0, min(1.0, f['hours'] / 168.0))
            if f['estado'] == 'R':
                d.ln(c2, cy, xh, cy, GOLD, 2)
                d.ln(xh, cy, c2 + LW, cy, RETRO, 2, dash=[5, 3])
                dc = RETRO
            else:
                d.ln(c2, cy, xh, cy, RETRO, 2, dash=[5, 3])
                d.ln(xh, cy, c2 + LW, cy, GOLD, 2)
                dc = GOLD_D
            lw_ = d.tw(f['label'], 'b', 8)
            if xh + 9 + lw_ + 3 <= c2 + LW:
                lx = xh + 9
            else:
                lx = xh - 9 - lw_
            d.rr(lx - 2, cy - 6, lw_ + 4, 12, fill=CREAM)
            d.tx(lx, cy + 2.9, f['label'], 'b', 8, dc)
            d.diamond(xh, cy, 5, fill=dc)
        d.para(c3, cy - 9.5, 156, '<font color="%s"><b>%s</b></font> · %s'
               % (NAVY, f['casa'], esc(f['casa_corto'])), 'r', 10.5, INK, 1.25)
        hh = d.ph(esc(f['hacer']), w4, 'r', 10, INK, 1.25)
        d.para(c4, cy - hh / 2.0 - 1, w4, esc(f['hacer']), 'r', 10, INK, 1.25)
        ry += fh_
    # leyenda del tablero
    ly = y + tab_h - 14
    d.ln(ix, ly - 16, PW - ML - 18, ly - 16, SEP, 1)
    x = ix
    d.ln(x, ly - 3, x + 22, ly - 3, RETRO, 2, dash=[5, 3])
    x += 28 + d.tx(x + 28, ly, "retrógrado: revisar y terminar", 'r', 8.5, MUTED) + 18
    d.ln(x, ly - 3, x + 22, ly - 3, GOLD, 2)
    x += 28 + d.tx(x + 28, ly, "directo: avanzar", 'r', 8.5, MUTED) + 18
    d.diamond(x + 5, ly - 3, 4.5, fill=GOLD_D)
    d.tx(x + 15, ly, "día y hora del cambio de rumbo", 'r', 8.5, MUTED)
    y += tab_h + gap

    # 5.4 Tres claves
    kw = (CW - 20) / 3.0
    for i, (kick, tit, txt, col) in enumerate(L['claves']):
        kx = ML + i * (kw + 10)
        c.saveState()
        p = c.beginPath()
        p.roundRect(X(kx), Y(y + cl_h), kw * K, cl_h * K, 12 * K)
        c.clipPath(p, stroke=0, fill=0)
        c.setFillColor(HexColor(WHITE)); c.rect(X(kx), Y(y + cl_h), kw * K, cl_h * K, stroke=0, fill=1)
        c.setFillColor(HexColor(col)); c.rect(X(kx), Y(y + 3), kw * K, 3 * K, stroke=0, fill=1)
        c.restoreState()
        d.rr(kx, y, kw, cl_h, 12, stroke=HAIR, lw=1)
        _kicker(d, kx + 14, y + 12 + 11, kick, size=8)
        s, sz = d.fit(tit, 'b', 14, kw - 28, 0, 10.5)
        d.tx(kx + 14, y + 12 + 31, s, 'b', sz, NAVY)
        d.para(kx + 14, y + 12 + 38, kw - 28, esc(txt), 'r', 11, INK, 1.5)
    y += cl_h + gap

    # 5.5 Llamado a la acción + app
    d.rr(ML, y, CW, cta_h, 16, fill=NAVY)
    lx, ly2 = ML + 22, y + (cta_h - 84) / 2.0
    d.rr(lx, ly2, 84, 84, 20, fill=CREAM)
    logo = os.path.join(_ASSETS, 'diario_astral_logo.png')
    if os.path.exists(logo):
        try:
            c.drawImage(ImageReader(logo), X(lx + 11), Y(ly2 + 8 + 68), 62 * K, 68 * K,
                        mask='auto', preserveAspectRatio=True)
        except Exception:
            pass
    tx_ = lx + 84 + 20
    th = 14 + 24 + d.ph(cta_txt, ctw, 'r', 11, CREAM, 1.55)
    ty = y + (cta_h - th) / 2.0
    _kicker(d, tx_, ty + 9, "¿QUIERE IR MÁS A FONDO?", GOLD_S, 8.5)
    d.tx(tx_, ty + 14 + 17, "Pida su estudio completo de tránsitos", 'b', 16, WHITE)
    d.para(tx_, ty + 14 + 24, ctw, cta_txt, 'r', 11, CREAM, 1.55)
    bx = ML + CW - 22 - 150
    by = y + (cta_h - 78) / 2.0
    for j, (ic, lab, key) in enumerate((('▶', 'Google Play', 'app_android'),
                                        ('▯', 'App Store', 'app_ios'))):
        yy = by + j * 44
        badge = os.path.join(_ASSETS, 'badge_google_play.png' if j == 0
                             else 'badge_app_store.png')
        if os.path.exists(badge):
            # insignia oficial de la tienda (archivo descargado por el usuario)
            try:
                c.drawImage(ImageReader(badge), X(bx), Y(yy + 36), 150 * K, 38 * K,
                            mask='auto', preserveAspectRatio=True, anchor='c')
            except Exception:
                pass
        else:
            d.rr(bx, yy, 150, 34, 17, stroke=GOLD_S, lw=1)
            wl_ = d.tw(lab, 'sb', 10.5)
            sx = bx + 75 - (wl_ + 16) / 2.0
            d.gch(ic, sx + 5, yy + 17, 10, GOLD_S)
            d.tx(sx + 16, yy + 20.7, lab, 'sb', 10.5, WHITE)
        url = (brand or {}).get(key)
        if url:
            c.linkURL(url, (X(bx), Y(yy + 34), X(bx + 150), Y(yy)), relative=0)
    wurl = (brand or {}).get('web_url')
    if wurl:
        c.linkURL(wurl, (X(tx_), Y(ty + th), X(tx_ + ctw), Y(ty)), relative=0)

    # 5.6 aviso legal + pie
    d.para(ML, 1079 - 10 - lg_h, CW, esc(legal), 'r', 8.5, MUTED, 1.45, 'c')
    _footer(d, 3, web)


# ════════════════════════════════════════════════════════════════════════

def render(data, interp, name='', city='', natal_city='', brand=None):
    """Devuelve los bytes del PDF (3 páginas A4)."""
    brand = brand or {}
    L = wl.build_layout(data, interp, name=name, city=city)
    L['natal_lugar'] = (natal_city or city or '').strip()
    web = 'www.mauriciopuerta.tv'
    for r in brand.get('redes', []):
        if r.get('icon') == 'web' and r.get('texto'):
            web = r['texto']
            brand = dict(brand, web_url=r.get('url'))
            break
    buf = io.BytesIO()
    c = _canvas.Canvas(buf, pagesize=(PW * K, PH * K))
    c.setTitle("Reporte Astral · Tránsitos Semanales" + ((" · " + L['name']) if L['name'] else ""))
    c.setAuthor("Mauricio Puerta")
    d = D(c)
    _page1(d, L, data, web); c.showPage()
    _page2(d, L, data, web); c.showPage()
    _page3(d, L, data, web, brand); c.showPage()
    c.save()
    return buf.getvalue()
