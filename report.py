# -*- coding: utf-8 -*-
"""
report.py — Genera el reporte astral interpretativo en PDF y DOCX.

Estructura del documento:
  Portada (azul noche, minimalista)
  Índice de contenidos (con enlaces internos)
  1. Qué es una carta astral natal (+ mandamientos, cruz, elemento)
  2. Carta natal: el libreto de tu vida (rueda + leyenda de símbolos)
  3. Los planetas en tu carta natal
  4. Las cúspides de las casas
  5. Aspectos astrales
  6. Glosario (signos, planetas y luminarias, casas)
  Comentarios finales

Textos: interpretations_es.json + preamble_es.json + glossary_es.json.
Íconos propios (./icons) junto a cada nombre de planeta o signo.
"""
import os
import io
import json
import base64

_BASE = os.path.dirname(os.path.abspath(__file__))

# Paleta "Cielo Nocturno"
GOLD = '#C9A24B'
NAVY = '#1E2450'
BLUE = '#3A4488'
SLATE = '#8A93B5'
INK = '#22284A'
RED = '#B02020'
PAPER_BG = '#FFFFFF'

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']

# ── Íconos propios ──────────────────────────────────────────────────────
_ICONS_DIR = os.path.join(_BASE, 'icons')

_NAME_ICON = [
    ("Luna Negra", "aLunaNegra"), ("Nodo Norte", "aNoduloNorte"),
    ("Nodo Sur", "aNoduloSur"), ("Nódulo Lunar Norte", "aNoduloNorte"),
    ("Nódulo Lunar Sur", "aNoduloSur"), ("Nódulo Norte", "aNoduloNorte"),
    ("Nódulo Sur", "aNoduloSur"), ("Rueda de la Fortuna", "aRuedaFortuna"),
    ("Parte de la Fortuna", "aRuedaFortuna"),
    ("Sol", "aSol"), ("Luna", "aLuna"), ("Mercurio", "aMercurio"),
    ("Venus", "aVenus"), ("Marte", "aMarte"), ("Júpiter", "aJupiter"),
    ("Jupiter", "aJupiter"), ("Saturno", "aSaturno"), ("Urano", "aUrano"),
    ("Neptuno", "aNeptuno"), ("Plutón", "aPluton"), ("Pluton", "aPluton"),
    ("Quirón", "aChiron"), ("Quiron", "aChiron"), ("Tierra", "aTierra"),
    ("Aries", "Aries"), ("Tauro", "Taurus"), ("Géminis", "Gemini"),
    ("Geminis", "Gemini"), ("Cáncer", "Cancer"), ("Cancer", "Cancer"),
    ("Leo", "Leo"), ("Virgo", "Virgo"), ("Libra", "Libra"),
    ("Escorpión", "Scorpio"), ("Escorpio", "Scorpio"),
    ("Sagitario", "Sagittarius"), ("Capricornio", "Capricorn"),
    ("Acuario", "Aquarius"), ("Piscis", "Pisces"),
]

import re as _re
_NAME_RE = _re.compile(
    r'\b(' + '|'.join(_re.escape(n) for n, _ in _NAME_ICON) + r')\b')
_NAME2FILE = {n: k for n, k in _NAME_ICON}


def _icon_path(name):
    p = os.path.join(_ICONS_DIR, _NAME2FILE.get(name, '') + '.png')
    return p if os.path.exists(p) else None


def _segments(text):
    out = []
    last = 0
    for m in _NAME_RE.finditer(text):
        out.append((text[last:m.end()], _icon_path(m.group(1))))
        last = m.end()
    out.append((text[last:], None))
    return out


# ── Datos ───────────────────────────────────────────────────────────────
_INTERP = None
_PREAMBLE = None
_GLOSSARY = None


def _load_json(fname):
    try:
        with open(os.path.join(_BASE, fname), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _interp():
    global _INTERP
    if _INTERP is None:
        _INTERP = _load_json('interpretations_es.json')
    return _INTERP


def _preamble():
    global _PREAMBLE
    if _PREAMBLE is None:
        _PREAMBLE = _load_json('preamble_es.json')
    return _PREAMBLE


def _glossary():
    global _GLOSSARY
    if _GLOSSARY is None:
        _GLOSSARY = _load_json('glossary_es.json')
    return _GLOSSARY


_REGENTE = {"Aries": "Marte", "Taurus": "Venus", "Gemini": "Mercurio",
            "Cancer": "Luna", "Leo": "Sol", "Virgo": "Quirón", "Libra": "Venus",
            "Scorpio": "Plutón", "Sagittarius": "Júpiter", "Capricorn": "Saturno",
            "Aquarius": "Urano", "Pisces": "Neptuno"}
_CRUZ = {"Aries": "cardinal", "Cancer": "cardinal", "Libra": "cardinal",
         "Capricorn": "cardinal", "Taurus": "fija", "Leo": "fija",
         "Scorpio": "fija", "Aquarius": "fija", "Gemini": "mutable",
         "Virgo": "mutable", "Sagittarius": "mutable", "Pisces": "mutable"}
_ELEM = {"Aries": "fuego", "Leo": "fuego", "Sagittarius": "fuego",
         "Taurus": "tierra", "Virgo": "tierra", "Capricorn": "tierra",
         "Gemini": "aire", "Libra": "aire", "Aquarius": "aire",
         "Cancer": "agua", "Scorpio": "agua", "Pisces": "agua"}


# ── Secciones interpretativas ───────────────────────────────────────────

def build_sections(chart):
    interp = _interp()
    nat = interp.get('natal', {})
    fb = interp.get('aspect_fallback', {}).get('natal', {})
    intro = interp.get('by_chart_type', {}).get('natal', {}).get('intro', '')

    sections = []
    items = []
    for p in chart['planets']:
        key, sign_en, house = p['key'], p['sign'], p['house']
        title = "%s en %s · Casa %s" % (p['name'], p.get('sign_es', sign_en), ROMAN[house - 1])
        paras = []
        t_sign = nat.get('planet_in_sign', {}).get(key, {}).get(sign_en)
        if t_sign:
            paras.append(t_sign)
        t_house = nat.get('planet_in_house', {}).get(key, {}).get(str(house))
        if t_house:
            paras.append(t_house)
        if paras:
            items.append((title, paras))
    if items:
        sections.append(("Los planetas en tu carta natal", items))

    cusp_items = []
    for h in chart['houses']:
        t = nat.get('cusp_in_sign', {}).get(str(h['num']), {}).get(h['sign'])
        if t:
            cusp_items.append(("Casa %s en %s" % (h['roman'], h.get('sign_es', h['sign'])), [t]))
    if cusp_items:
        sections.append(("Las cúspides de las casas", cusp_items))

    asp = nat.get('aspects', {})
    name_es = {p['key']: p['name'] for p in chart['planets']}
    asp_es = {'Conjunction': 'conjunción', 'Opposition': 'oposición', 'Trine': 'trígono',
              'Square': 'cuadratura', 'Sextile': 'sextil'}
    asp_items = []
    for a in chart['aspects']:
        ka, kb, typ = a['a'], a['b'], a['type']
        txt = (asp.get(ka, {}).get(typ, {}).get(kb)
               or asp.get(kb, {}).get(typ, {}).get(ka)
               or fb.get(typ))
        if not txt:
            continue
        title = "%s %s %s  (orbe %.1f°)" % (
            name_es.get(ka, ka), asp_es.get(typ, typ.lower()),
            name_es.get(kb, kb), a.get('orb', 0))
        asp_items.append((title, [txt]))
    if asp_items:
        sections.append(("Aspectos astrales", asp_items))

    return intro, sections


# ── Preámbulo ───────────────────────────────────────────────────────────

def build_preamble(chart):
    pre = _preamble()
    if not pre:
        return []
    planets = {p['key']: p for p in chart['planets']}
    sun = planets.get('aSol', {})
    moon = planets.get('aLuna', {})
    sun_sign_en = sun.get('sign', 'Aries')
    sun_sign = sun.get('sign_es', sun_sign_en)
    moon_sign = moon.get('sign_es', '')
    asc_sign = chart['angles']['asc'].get('sign_es', '')
    sun_roman = ROMAN[sun.get('house', 1) - 1]
    moon_roman = ROMAN[moon.get('house', 1) - 1]
    sun_house = "Casa " + sun_roman
    moon_house = "Casa " + moon_roman
    regente = _REGENTE.get(sun_sign_en, 'Sol')
    hl_signos = {sun_sign, moon_sign, asc_sign}
    hl_casas = {sun_house, moon_house, "Casa I"}
    hl_planetas = {"Sol", "Luna", regente}

    b = []
    b.append(("h2", pre.get('intro_titulo', 'Qué es una carta astral natal')))
    for p in pre.get('intro', []):
        # Parametrización con los datos reales de la carta
        if p.startswith('1.'):
            p += " En tu caso, tu Sol está en %s, en la Casa %s." % (sun_sign, sun_roman)
        elif p.startswith('2.'):
            p += " En tu caso, tu Ascendente es %s." % asc_sign
        elif p.startswith('3.'):
            p += " En tu caso, tu Luna está en %s, en la Casa %s." % (moon_sign, moon_roman)
        b.append(("p", p))
    b.append(("h3", "Los mandamientos zodiacales"))
    b.append(("p", pre.get('mand_signos_intro', '')))
    for k, v in pre.get('mand_signos', {}).items():
        b.append(("item", k, v, k in hl_signos))
    b.append(("p", pre.get('mand_casas_intro', '')))
    for k, v in pre.get('mand_casas', {}).items():
        b.append(("item", k, v, k in hl_casas))
    b.append(("p", pre.get('mand_planetas_intro', '')))
    for k, v in pre.get('mand_planetas', {}).items():
        b.append(("item", k, v, k in hl_planetas))
    b.append(("p", pre.get('mand_cierre', '')))
    b.append(("p", pre.get('puente_cruz', '')))

    cz = pre.get('cruces', {}).get(_CRUZ.get(sun_sign_en, 'fija'), {})
    if cz:
        otros = [s for s in cz.get('signos', []) if s != sun_sign]
        b.append(("h3", cz.get('titulo', 'Tu cruz zodiacal')))
        b.append(("p", "Inicio tu carta por decirte que, al ser %s, perteneces a una "
                        "cruz conocida como %s, la cual decidiste antes de nacer que "
                        "la tienes que formar en esta vida con las personas de los "
                        "signos %s. Primero te digo qué es esta cruz zodiacal y luego "
                        "vamos a tu caso particular."
                  % (sun_sign, cz.get('titulo', '').upper(),
                     ", ".join(otros[:-1]) + " y " + otros[-1] if len(otros) > 1 else "".join(otros))))
        if cz.get('mision'):
            b.append(("p", cz['mision']))
        rep = cz.get('representacion', {})
        if rep:
            b.append(("p", "Representación particular: recuerda que tienes que formar "
                            "esta cruz con personas de los siguientes signos."))
            for sname, stext in rep.items():
                b.append(("p", stext))
        if cz.get('cierre'):
            b.append(("p", cz['cierre']))

    el = pre.get('elementos', {}).get(_ELEM.get(sun_sign_en, 'tierra'), {})
    if el:
        otros2 = [s for s in el.get('signos', []) if s != sun_sign]
        b.append(("h3", el.get('titulo', 'Tu elemento')))
        b.append(("p", "Como pudiste apreciar, %s pertenece al elemento %s de esa "
                        "cruz y, por lo tanto, también decidiste antes de nacer que "
                        "tienes que formar tu triángulo con los signos %s. Observa, "
                        "entonces, qué significa el elemento al cual perteneces."
                  % (sun_sign, el.get('titulo', '').replace('Elemento ', ''),
                     " y ".join(otros2))))
        for fld in ('mision', 'personaje', 'frase', 'descripcion'):
            if el.get(fld):
                b.append(("p", el[fld]))
        for sname, stext in el.get('representacion', {}).items():
            b.append(("p", stext))

    if pre.get('cierre_preambulo'):
        b.append(("p", pre['cierre_preambulo']))
    if pre.get('puente_interpretacion'):
        b.append(("p", pre['puente_interpretacion']))
    return [x for x in b if not (x[0] == "p" and not x[1])]


# ── Glosario ────────────────────────────────────────────────────────────

def build_glossary():
    g = _glossary()
    if not g:
        return []
    b = [("h2", "Glosario")]
    b.append(("h3", "Signos zodiacales"))
    if g.get('signos_intro'):
        b.append(("p", g['signos_intro']))
    for s in g.get('signos', []):
        b.append(("item", s['nombre'],
                  "%s · %s. %s" % (s.get('lema', ''), s.get('elemento', ''), s.get('desc', '')),
                  False))
    b.append(("h3", "Luminarias y planetas"))
    if g.get('planetas_intro'):
        b.append(("p", g['planetas_intro']))
    for s in g.get('planetas', []):
        b.append(("item", s['nombre'], s.get('desc', ''), False))
    b.append(("h3", "Casas astrales"))
    if g.get('casas_intro'):
        b.append(("p", g['casas_intro']))
    for s in g.get('casas', []):
        b.append(("item", s['nombre'], s.get('desc', ''), False))
    if g.get('comentarios_finales'):
        b.append(("h3", "Comentarios finales"))
        b.append(("p", g['comentarios_finales']))
    return b


_LEGEND_PLANETS = [("aSol", "Sol"), ("aLuna", "Luna"), ("aMercurio", "Mercurio"),
    ("aVenus", "Venus"), ("aTierra", "Tierra"), ("aMarte", "Marte"),
    ("aJupiter", "Júpiter"), ("aSaturno", "Saturno"),
    ("aChiron", "Quirón"), ("aUrano", "Urano"), ("aNeptuno", "Neptuno"),
    ("aPluton", "Plutón"), ("aNoduloNorte", "Nodo Norte"),
    ("aNoduloSur", "Nodo Sur"), ("aLunaNegra", "Luna Negra"),
    ("aRuedaFortuna", "R. Fortuna")]
_LEGEND_SIGNS = [("Aries", "Aries"), ("Taurus", "Tauro"), ("Gemini", "Géminis"),
    ("Cancer", "Cáncer"), ("Leo", "Leo"), ("Virgo", "Virgo"), ("Libra", "Libra"),
    ("Scorpio", "Escorpio"), ("Sagittarius", "Sagitario"),
    ("Capricorn", "Capricornio"), ("Aquarius", "Acuario"), ("Pisces", "Piscis")]


def build_legend():
    out = []
    for gname, entries in (("Planetas y puntos", _LEGEND_PLANETS),
                           ("Signos", _LEGEND_SIGNS)):
        rows = []
        for key, label in entries:
            p = os.path.join(_ICONS_DIR, key + '.png')
            if os.path.exists(p):
                rows.append((p, label))
        out.append((gname, rows))
    return out


def _png_from_dataurl(chart_png):
    if not chart_png:
        return None
    try:
        if ',' in chart_png:
            chart_png = chart_png.split(',', 1)[1]
        return base64.b64decode(chart_png)
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════
#  PDF
# ════════════════════════════════════════════════════════════════════════

def render_pdf(title, sections, chart_png_bytes, user_line,
               pre_blocks=None, legend=None, glossary=None):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors as C
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame,
                                    NextPageTemplate, Paragraph, Spacer,
                                    PageBreak, Image, Table, TableStyle)

    buf = io.BytesIO()
    page_w, page_h = A4
    lm = rm = 2.6 * cm
    tm = bm = 2.4 * cm
    bf, bd, it = 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'

    def esc(t):
        return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def with_icons(t, size=8):
        parts = []
        for seg, icon in _segments(t):
            parts.append(esc(seg))
            if icon:
                parts.append(' <img src="%s" width="%d" height="%d" valign="-1"/>'
                             % (icon, size, size))
        return ''.join(parts)

    st_title = ParagraphStyle('t', fontName=bd, fontSize=28, leading=34,
                              textColor=C.HexColor(GOLD), alignment=TA_CENTER)
    st_sub = ParagraphStyle('s', fontName=it, fontSize=13, leading=18,
                            textColor=C.HexColor(SLATE), alignment=TA_CENTER)
    st_h2 = ParagraphStyle('h2', fontName=bd, fontSize=16, leading=21,
                           textColor=C.HexColor(NAVY), spaceBefore=18, spaceAfter=8,
                           keepWithNext=1)
    st_h3 = ParagraphStyle('h3', fontName=bd, fontSize=12, leading=15,
                           textColor=C.HexColor(BLUE), spaceBefore=10, spaceAfter=6,
                           keepWithNext=1)
    st_body = ParagraphStyle('b', fontName=bf, fontSize=10.3, leading=15,
                             textColor=C.HexColor(INK), alignment=TA_JUSTIFY,
                             spaceAfter=5, firstLineIndent=14)
    st_item = ParagraphStyle('li', fontName=bf, fontSize=10.3, leading=16,
                             textColor=C.HexColor(INK), leftIndent=14)
    st_tocc = ParagraphStyle('tc', fontName=bd, fontSize=11.5, leading=19,
                             textColor=C.HexColor(NAVY))
    st_tocs = ParagraphStyle('ts', fontName=bf, fontSize=9.5, leading=15,
                             textColor=C.HexColor(BLUE), leftIndent=20)

    def on_cover(cv, doc):
        cv.saveState()
        cv.setFillColorRGB(0x0E / 255., 0x13 / 255., 0x32 / 255.)
        cv.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        cv.setStrokeColor(C.HexColor(GOLD))
        cv.setLineWidth(1.0)
        cv.rect(36, 36, page_w - 72, page_h - 72, fill=0, stroke=1)
        cv.setLineWidth(0.4)
        cv.rect(44, 44, page_w - 88, page_h - 88, fill=0, stroke=1)
        cx, cy, r = page_w / 2, page_h * 0.70, 9
        p = cv.beginPath()
        p.moveTo(cx, cy + r); p.lineTo(cx + r, cy); p.lineTo(cx, cy - r)
        p.lineTo(cx - r, cy); p.close()
        cv.setLineWidth(0.9)
        cv.drawPath(p, fill=0, stroke=1)
        cv.circle(cx, cy, 1.6, fill=1, stroke=0)
        cv.setLineWidth(0.5)
        cv.line(cx - 110, cy, cx - r - 12, cy)
        cv.line(cx + r + 12, cy, cx + 110, cy)
        cv.setFont(bf, 9)
        cv.setFillColor(C.HexColor(GOLD))
        cv.drawCentredString(page_w / 2, 58, 'R E P O R T E   A S T R A L')
        cv.restoreState()

    def _diamond(cv, cx, cy, r, C):
        p = cv.beginPath()
        p.moveTo(cx, cy + r); p.lineTo(cx + r, cy); p.lineTo(cx, cy - r)
        p.lineTo(cx - r, cy); p.close()
        cv.drawPath(p, fill=0, stroke=1)

    def on_body(cv, doc):
        cv.saveState()
        cv.setFillColor(C.HexColor(PAPER_BG)); cv.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        # ornamento superior: filete — rombo — filete
        ty = page_h - tm * 0.52
        cv.setStrokeColor(C.HexColor(GOLD)); cv.setLineWidth(0.6)
        cv.line(page_w / 2 - 90, ty, page_w / 2 - 14, ty)
        cv.line(page_w / 2 + 14, ty, page_w / 2 + 90, ty)
        cv.setLineWidth(0.7)
        _diamond(cv, page_w / 2, ty, 4.5, C)
        cv.setFillColor(C.HexColor(GOLD))
        cv.circle(page_w / 2, ty, 1.0, fill=1, stroke=0)
        # pie de página
        cv.setLineWidth(0.7)
        cv.line(lm, bm * 0.72, page_w - rm, bm * 0.72)
        cv.setFont(bf, 7.5); cv.setFillColor(C.HexColor(NAVY))
        marca = 'REPORTE ASTRAL'
        cv.drawString(lm, bm * 0.42, marca)
        cv.setFont(it, 7.5); cv.setFillColor(C.HexColor(SLATE))
        sub = '  ·  Carta Natal' + (('  ·  ' + user_line) if user_line else '')
        cv.drawString(lm + cv.stringWidth(marca, bf, 7.5), bm * 0.42, sub)
        num = str(doc.page)
        cx2 = page_w - rm - 8
        cy2 = bm * 0.46
        cv.setStrokeColor(C.HexColor(GOLD)); cv.setLineWidth(0.7)
        _diamond(cv, cx2, cy2, 8.5, C)
        cv.setFont(bf, 7.5); cv.setFillColor(C.HexColor(NAVY))
        cv.drawCentredString(cx2, cy2 - 2.6, num)
        cv.restoreState()

    frame = Frame(lm, bm, page_w - lm - rm, page_h - tm - bm)
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=lm, rightMargin=rm,
                          topMargin=tm, bottomMargin=bm)
    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=[Frame(lm, bm, page_w - lm - rm, page_h - tm - bm)], onPage=on_cover),
        PageTemplate(id='Body', frames=[frame], onPage=on_body),
    ])

    # ── Contenido con anclas para el índice ──────────────────────────────
    toc = []          # (nivel, texto, clave)
    content = []

    def H2(text):
        key = "sec%d" % len(toc)
        toc.append((1, text, key))
        content.append(Paragraph('<a name="%s"/>' % key + with_icons(text, 10), st_h2))

    def H3(text):
        key = "sec%d" % len(toc)
        toc.append((2, text, key))
        content.append(Paragraph('<a name="%s"/>' % key + with_icons(text, 9), st_h3))

    # 1) Preámbulo
    if pre_blocks:
        for blk in pre_blocks:
            if blk[0] == "h2":
                H2(blk[1])
            elif blk[0] == "h3":
                H3(blk[1])
            elif blk[0] == "p":
                content.append(Paragraph(with_icons(blk[1], 8), st_body))
            elif blk[0] == "item":
                _, nm, tx, hl = blk
                nm_markup = with_icons(nm, 8)
                nm_markup = ('<font color="%s"><b>%s</b></font>' % (RED, nm_markup)) if hl \
                    else ('<b>%s</b>' % nm_markup)
                content.append(Paragraph(nm_markup + ' — ' + esc(tx), st_item))
        content.append(PageBreak())

    # 2) La carta + leyenda
    if chart_png_bytes:
        try:
            from PIL import Image as PILImage
            im = PILImage.open(io.BytesIO(chart_png_bytes))
            iw, ih = im.size
            disp_w = min(page_w - lm - rm, 15 * cm)
            disp_h = disp_w * ih / iw
            H2("Carta natal: el libreto de tu vida")
            content.append(Spacer(1, 6))
            content.append(Image(io.BytesIO(chart_png_bytes), width=disp_w, height=disp_h))
        except Exception:
            pass

    if legend:
        H3("Leyenda de símbolos")
        st_leg = ParagraphStyle('lg', fontName=bf, fontSize=9,
                                textColor=C.HexColor(INK))
        for gname, rows in legend:
            content.append(Paragraph('<b>%s</b>' % esc(gname), ParagraphStyle(
                'lgt', fontName=bd, fontSize=10, textColor=C.HexColor(BLUE),
                spaceBefore=6, spaceAfter=3)))
            cells, row = [], []
            for icon, label in rows:
                row.append(Paragraph(
                    '<img src="%s" width="10" height="10" valign="-2"/> %s'
                    % (icon, esc(label)), st_leg))
                if len(row) == 4:
                    cells.append(row); row = []
            if row:
                row += [Paragraph('', st_leg)] * (4 - len(row))
                cells.append(row)
            t = Table(cells, colWidths=[(page_w - lm - rm) / 4.0] * 4)
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            content.append(t)
        content.append(PageBreak())

    # 3-5) Secciones interpretativas
    for sec_title, items in sections:
        H2(sec_title)
        for it_title, paras in items:
            H3(it_title)
            for p in paras:
                content.append(Paragraph(with_icons(p, 8), st_body))

    # 6) Glosario
    if glossary:
        content.append(PageBreak())
        for blk in glossary:
            if blk[0] == "h2":
                H2(blk[1])
            elif blk[0] == "h3":
                H3(blk[1])
            elif blk[0] == "p":
                content.append(Paragraph(with_icons(blk[1], 8), st_body))
            elif blk[0] == "item":
                _, nm, tx, _hl = blk
                content.append(Paragraph('<b>%s</b> — %s' % (with_icons(nm, 8), esc(tx)),
                                         st_item))

    # ── Índice ───────────────────────────────────────────────────────────
    toc_flow = [Paragraph('Índice de contenidos', st_h2)]
    for lvl, text, key in toc:
        style = st_tocc if lvl == 1 else st_tocs
        toc_flow.append(Paragraph(
            '<a href="#%s" color="%s">%s</a>' % (key, NAVY if lvl == 1 else BLUE, esc(text)),
            style))
    toc_flow.append(PageBreak())

    flow = [NextPageTemplate('Body'), Spacer(1, page_h * 0.30),
            Paragraph(esc(title), st_title), Spacer(1, 14)]
    if user_line:
        flow.append(Paragraph(esc(user_line), st_sub))
    flow.append(PageBreak())
    flow += toc_flow
    flow += content
    doc.build(flow)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════
#  DOCX
# ════════════════════════════════════════════════════════════════════════

def render_docx(title, sections, chart_png_bytes, user_line,
                pre_blocks=None, legend=None, glossary=None):
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    NAVY_RGB = RGBColor(0x1E, 0x24, 0x50)
    BLUE_RGB = RGBColor(0x3A, 0x44, 0x88)
    RED_RGB = RGBColor(0xB0, 0x20, 0x20)
    INK_RGB = RGBColor(0x22, 0x28, 0x4A)
    SLATE_RGB = RGBColor(0x8A, 0x93, 0xB5)

    def add_text_with_icons(par, text, bold=False, size=None, color=None):
        for seg, icon in _segments(text):
            if seg:
                r = par.add_run(seg)
                r.bold = bold
                if size:
                    r.font.size = size
                if color:
                    r.font.color.rgb = color
            if icon:
                try:
                    par.add_run(' ')
                    par.add_run().add_picture(icon, height=Inches(0.12))
                except Exception:
                    pass

    def bookmark(par, name, bid):
        s = OxmlElement('w:bookmarkStart')
        s.set(qn('w:id'), str(bid)); s.set(qn('w:name'), name)
        e = OxmlElement('w:bookmarkEnd')
        e.set(qn('w:id'), str(bid))
        par._p.insert(0, s); par._p.append(e)

    def toc_link(par, anchor, text, color='1E2450', bold=False, italic=False):
        h = OxmlElement('w:hyperlink')
        h.set(qn('w:anchor'), anchor)
        r = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')
        c = OxmlElement('w:color'); c.set(qn('w:val'), color); rPr.append(c)
        if bold:
            rPr.append(OxmlElement('w:b'))
        r.append(rPr)
        t = OxmlElement('w:t'); t.text = text
        r.append(t); h.append(r); par._p.append(h)

    doc = Document()
    for s in doc.sections:
        s.top_margin = Inches(1); s.bottom_margin = Inches(1)
        s.left_margin = Inches(1); s.right_margin = Inches(1)

    # Portada simple
    h = doc.add_paragraph(); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = h.add_run(title); r.bold = True; r.font.size = Pt(26)
    r.font.color.rgb = BLUE_RGB
    if user_line:
        sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rr = sp.add_run(user_line); rr.italic = True; rr.font.size = Pt(12)
        rr.font.color.rgb = SLATE_RGB
    mk = doc.add_paragraph(); mk.alignment = WD_ALIGN_PARAGRAPH.CENTER
    mr = mk.add_run('R E P O R T E   A S T R A L'); mr.font.size = Pt(9)
    mr.font.color.rgb = RGBColor(0xC9, 0xA2, 0x4B)
    doc.add_page_break()

    # ── Contenido (recolectando anclas) ──────────────────────────────────
    toc = []      # (nivel, texto, ancla)
    bodyq = []    # cola de operaciones: se materializa tras armar el índice

    def q_h2(text):
        toc.append((1, text, "sec%d" % len(toc)))
        bodyq.append(("h2", text, toc[-1][2]))

    def q_h3(text):
        toc.append((2, text, "sec%d" % len(toc)))
        bodyq.append(("h3", text, toc[-1][2]))

    def q(other, *args):
        bodyq.append((other,) + args)

    if pre_blocks:
        for blk in pre_blocks:
            if blk[0] == "h2":
                q_h2(blk[1])
            elif blk[0] == "h3":
                q_h3(blk[1])
            elif blk[0] == "p":
                q("p", blk[1])
            elif blk[0] == "item":
                q("item", blk[1], blk[2], blk[3])
    if chart_png_bytes:
        q_h2("Carta natal: el libreto de tu vida")
        q("img", chart_png_bytes)
    if legend:
        q_h3("Leyenda de símbolos")
        q("legend", legend)
    for sec_title, items in sections:
        q_h2(sec_title)
        for it_title, paras in items:
            q_h3(it_title)
            for p in paras:
                q("p", p)
    if glossary:
        for blk in glossary:
            if blk[0] == "h2":
                q_h2(blk[1])
            elif blk[0] == "h3":
                q_h3(blk[1])
            elif blk[0] == "p":
                q("p", blk[1])
            elif blk[0] == "item":
                q("gitem", blk[1], blk[2])

    # ── Índice ───────────────────────────────────────────────────────────
    hp = doc.add_heading(level=1)
    hr = hp.add_run("Índice de contenidos"); hr.font.color.rgb = NAVY_RGB
    for lvl, text, anchor in toc:
        p = doc.add_paragraph()
        if lvl == 2:
            p.paragraph_format.left_indent = Inches(0.3)
        toc_link(p, anchor, text, color='1E2450' if lvl == 1 else '3A4488',
                 bold=(lvl == 1))
    doc.add_page_break()

    # ── Materializar el contenido ────────────────────────────────────────
    bid = [100]
    for op in bodyq:
        kind = op[0]
        if kind == "h2":
            hp = doc.add_heading(level=1)
            add_text_with_icons(hp, op[1], color=NAVY_RGB)
            bookmark(hp, op[2], bid[0]); bid[0] += 1
        elif kind == "h3":
            sp = doc.add_paragraph()
            sp.paragraph_format.space_before = Pt(8)
            sp.paragraph_format.space_after = Pt(4)
            add_text_with_icons(sp, op[1], bold=True, size=Pt(12), color=BLUE_RGB)
            bookmark(sp, op[2], bid[0]); bid[0] += 1
        elif kind == "p":
            bp = doc.add_paragraph()
            bp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            bp.paragraph_format.first_line_indent = Inches(0.18)
            add_text_with_icons(bp, op[1])
        elif kind == "item":
            _, nm, tx, hl = op
            ip = doc.add_paragraph()
            ip.paragraph_format.left_indent = Inches(0.2)
            add_text_with_icons(ip, nm, bold=True,
                                color=RED_RGB if hl else INK_RGB)
            ip.add_run(" — " + tx)
        elif kind == "gitem":
            _, nm, tx = op
            ip = doc.add_paragraph()
            ip.paragraph_format.left_indent = Inches(0.2)
            add_text_with_icons(ip, nm, bold=True, color=INK_RGB)
            ip.add_run(" — " + tx)
        elif kind == "img":
            doc.add_paragraph()
            pic = doc.add_paragraph(); pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
            try:
                pic.add_run().add_picture(io.BytesIO(op[1]), width=Inches(5.6))
            except Exception:
                pass
        elif kind == "legend":
            for gname, rows in op[1]:
                gp = doc.add_paragraph()
                gr = gp.add_run(gname); gr.bold = True
                gr.font.color.rgb = BLUE_RGB
                ncols = 4
                nrows = (len(rows) + ncols - 1) // ncols
                tbl = doc.add_table(rows=nrows, cols=ncols)
                for i, (icon, label) in enumerate(rows):
                    cell = tbl.cell(i // ncols, i % ncols)
                    cp = cell.paragraphs[0]
                    try:
                        cp.add_run().add_picture(icon, height=Inches(0.14))
                    except Exception:
                        pass
                    cp.add_run("  " + label).font.size = Pt(9.5)

    buf = io.BytesIO(); doc.save(buf); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════
#  ORQUESTACIÓN
# ════════════════════════════════════════════════════════════════════════

def generate(chart, name, fmt, chart_png):
    """Punto de entrada. Devuelve (bytes, filename, mimetype)."""
    _intro, sections = build_sections(chart)
    pre_blocks = build_preamble(chart)
    legend = build_legend()
    glossary = build_glossary()
    title = "Carta Natal"
    person = (name or '').strip()
    user_line = person if person else None
    png = _png_from_dataurl(chart_png)
    safe = "Reporte_Astral" + (("_" + person.replace(' ', '_')) if person else "")
    if fmt == 'docx':
        data = render_docx(title, sections, png, user_line,
                           pre_blocks=pre_blocks, legend=legend, glossary=glossary)
        return data, safe + '.docx', \
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    data = render_pdf(title, sections, png, user_line,
                      pre_blocks=pre_blocks, legend=legend, glossary=glossary)
    return data, safe + '.pdf', 'application/pdf'
