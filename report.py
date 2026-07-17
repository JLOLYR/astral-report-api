# -*- coding: utf-8 -*-
"""
report.py — Genera el reporte astral interpretativo en PDF y DOCX.

Toma el resultado de astro.compute_chart(...) + los textos de
interpretations_es.json y arma un documento con:
  - portada (azul medianoche + oro)
  - la rueda de la carta (imagen PNG enviada por la web)
  - planetas en signo y casa
  - cúspides de las casas
  - aspectos

Todo con librerías puras de Python (reportlab, python-docx), sin dependencias
del sistema, para que funcione en Render.
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

# ── Íconos propios (logos convertidos a PNG en ./icons) ─────────────────
_ICONS_DIR = os.path.join(_BASE, 'icons')

# (nombre en el texto, archivo de ícono) — los nombres largos van primero
_NAME_ICON = [
    ("Luna Negra", "aLunaNegra"), ("Nodo Norte", "aNoduloNorte"),
    ("Nodo Sur", "aNoduloSur"), ("Rueda de la Fortuna", "aRuedaFortuna"),
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
    """Divide el texto en [(texto, icono_o_None), ...] insertando el ícono
    después de cada nombre de planeta o signo (como en el reporte modelo)."""
    out = []
    last = 0
    for m in _NAME_RE.finditer(text):
        out.append((text[last:m.end()], _icon_path(m.group(1))))
        last = m.end()
    out.append((text[last:], None))
    return out

_INTERP = None
_PREAMBLE = None


def _interp():
    global _INTERP
    if _INTERP is None:
        with open(os.path.join(_BASE, 'interpretations_es.json'), encoding='utf-8') as f:
            _INTERP = json.load(f)
    return _INTERP


def _preamble():
    global _PREAMBLE
    if _PREAMBLE is None:
        try:
            with open(os.path.join(_BASE, 'preamble_es.json'), encoding='utf-8') as f:
                _PREAMBLE = json.load(f)
        except Exception:
            _PREAMBLE = {}
    return _PREAMBLE


# Regente de cada signo (sistema de la app), cruz y elemento
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


def build_preamble(chart):
    """Bloques del preámbulo, con resaltados según la carta:
       [("h2",t) | ("p",t) | ("item", nombre, texto, resaltado_bool)]"""
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
    sun_house = "Casa " + ROMAN[sun.get('house', 1) - 1]
    moon_house = "Casa " + ROMAN[moon.get('house', 1) - 1]
    regente = _REGENTE.get(sun_sign_en, 'Sol')
    hl_signos = {sun_sign, moon_sign, asc_sign}
    hl_casas = {sun_house, moon_house, "Casa I"}
    hl_planetas = {"Sol", "Luna", regente}

    b = []
    b.append(("h2", pre.get('intro_titulo', 'Qué es una carta astral natal')))
    for p in pre.get('intro', []):
        b.append(("p", p))
    b.append(("h2", "Los mandamientos zodiacales"))
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

    # Cruz según el signo solar
    cz = pre.get('cruces', {}).get(_CRUZ.get(sun_sign_en, 'fija'), {})
    if cz:
        otros = [s for s in cz.get('signos', []) if s != sun_sign]
        b.append(("h2", cz.get('titulo', 'Tu cruz zodiacal')))
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

    # Elemento según el signo solar
    el = pre.get('elementos', {}).get(_ELEM.get(sun_sign_en, 'tierra'), {})
    if el:
        otros2 = [s for s in el.get('signos', []) if s != sun_sign]
        b.append(("h2", el.get('titulo', 'Tu elemento')))
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


_LEGEND_PLANETS = [("aSol", "Sol"), ("aLuna", "Luna"), ("aMercurio", "Mercurio"),
    ("aVenus", "Venus"), ("aTierra", "Tierra"), ("aMarte", "Marte"),
    ("aJupiter", "Júpiter"), ("aSaturno", "Saturno"), ("aQuiron_", "—"),
    ("aChiron", "Quirón"), ("aUrano", "Urano"), ("aNeptuno", "Neptuno"),
    ("aPluton", "Plutón"), ("aNoduloNorte", "Nodo Norte"),
    ("aNoduloSur", "Nodo Sur"), ("aLunaNegra", "Luna Negra"),
    ("aRuedaFortuna", "R. Fortuna")]
_LEGEND_SIGNS = [("Aries", "Aries"), ("Taurus", "Tauro"), ("Gemini", "Géminis"),
    ("Cancer", "Cáncer"), ("Leo", "Leo"), ("Virgo", "Virgo"), ("Libra", "Libra"),
    ("Scorpio", "Escorpio"), ("Sagittarius", "Sagitario"),
    ("Capricorn", "Capricornio"), ("Aquarius", "Acuario"), ("Pisces", "Piscis")]


def build_legend():
    """[(título_grupo, [(ruta_icono, etiqueta), ...]), ...]"""
    out = []
    for gname, entries in (("Planetas y puntos", _LEGEND_PLANETS),
                           ("Signos", _LEGEND_SIGNS)):
        rows = []
        for key, label in entries:
            if label == "—":
                continue
            p = os.path.join(_ICONS_DIR, key + '.png')
            if os.path.exists(p):
                rows.append((p, label))
        out.append((gname, rows))
    return out


def build_sections(chart):
    """Arma (intro, secciones) para una carta natal usando interpretations_es.json."""
    interp = _interp()
    nat = interp.get('natal', {})
    fb = interp.get('aspect_fallback', {}).get('natal', {})
    intro = interp.get('by_chart_type', {}).get('natal', {}).get('intro', '')

    sections = []

    # Planetas en signo + casa
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
        sections.append(("Los planetas en tu carta", items))

    # Cúspides de casas
    cusp_items = []
    for h in chart['houses']:
        t = nat.get('cusp_in_sign', {}).get(str(h['num']), {}).get(h['sign'])
        if t:
            cusp_items.append(("Casa %s en %s" % (h['roman'], h.get('sign_es', h['sign'])), [t]))
    if cusp_items:
        sections.append(("Las cúspides de las casas", cusp_items))

    # Aspectos
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
        sections.append(("Los aspectos", asp_items))

    return intro, sections


def _png_from_dataurl(chart_png):
    """Convierte 'data:image/png;base64,...' (o base64 puro) a bytes."""
    if not chart_png:
        return None
    try:
        if ',' in chart_png:
            chart_png = chart_png.split(',', 1)[1]
        return base64.b64decode(chart_png)
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════
#  PDF (reportlab)
# ════════════════════════════════════════════════════════════════════════

def render_pdf(title, intro, sections, chart_png_bytes, user_line,
               pre_blocks=None, legend=None):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors as C
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame,
                                    NextPageTemplate, Paragraph, Spacer,
                                    PageBreak, Image, KeepTogether, Table,
                                    TableStyle)

    buf = io.BytesIO()
    page_w, page_h = A4
    lm = rm = 2.6 * cm
    tm = bm = 2.4 * cm
    bf, bd, it = 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'

    def esc(t):
        return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def with_icons(t, size=8):
        """Texto escapado con los íconos propios tras cada nombre."""
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
    st_intro = ParagraphStyle('i', fontName=it, fontSize=12, leading=19,
                              textColor=C.HexColor('#EDEFF7'), alignment=TA_JUSTIFY)
    st_h2 = ParagraphStyle('h2', fontName=bd, fontSize=16, leading=21,
                           textColor=C.HexColor(NAVY), spaceBefore=16, spaceAfter=6,
                           keepWithNext=1)
    st_h3 = ParagraphStyle('h3', fontName=bd, fontSize=12, leading=15,
                           textColor=C.HexColor(BLUE), spaceBefore=9, spaceAfter=2,
                           keepWithNext=1)
    st_body = ParagraphStyle('b', fontName=bf, fontSize=10.3, leading=15,
                             textColor=C.HexColor(INK), alignment=TA_JUSTIFY, spaceAfter=4)

    def on_cover(cv, doc):
        """Portada minimalista: azul noche plano, doble filete dorado y un
        pequeño rombo como único ornamento."""
        cv.saveState()
        cv.setFillColorRGB(0x0E / 255., 0x13 / 255., 0x32 / 255.)
        cv.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        # doble filete dorado
        cv.setStrokeColor(C.HexColor(GOLD))
        cv.setLineWidth(1.0)
        cv.rect(36, 36, page_w - 72, page_h - 72, fill=0, stroke=1)
        cv.setLineWidth(0.4)
        cv.rect(44, 44, page_w - 88, page_h - 88, fill=0, stroke=1)
        # rombo dorado sobre el título
        cx, cy, r = page_w / 2, page_h * 0.70, 9
        p = cv.beginPath()
        p.moveTo(cx, cy + r); p.lineTo(cx + r, cy); p.lineTo(cx, cy - r)
        p.lineTo(cx - r, cy); p.close()
        cv.setLineWidth(0.9)
        cv.drawPath(p, fill=0, stroke=1)
        cv.circle(cx, cy, 1.6, fill=1, stroke=0)
        # filetes cortos a los lados del rombo
        cv.setLineWidth(0.5)
        cv.line(cx - 110, cy, cx - r - 12, cy)
        cv.line(cx + r + 12, cy, cx + 110, cy)
        # marca inferior
        cv.setFont(bf, 9)
        cv.setFillColor(C.HexColor(GOLD))
        cv.drawCentredString(page_w / 2, 58, 'R E P O R T E   A S T R A L')
        cv.restoreState()

    def on_body(cv, doc):
        cv.saveState()
        # página blanca
        cv.setFillColor(C.HexColor(PAPER_BG)); cv.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        # cabecera sutil: filete dorado corto centrado
        cv.setStrokeColor(C.HexColor(GOLD)); cv.setLineWidth(0.6)
        cv.line(page_w / 2 - 40, page_h - tm * 0.55, page_w / 2 + 40, page_h - tm * 0.55)
        # pie de página: filete + marca a la izquierda, página en rombo a la derecha
        cv.setLineWidth(0.7)
        cv.line(lm, bm * 0.72, page_w - rm, bm * 0.72)
        cv.setFont(bf, 7.5); cv.setFillColor(C.HexColor(NAVY))
        marca = 'REPORTE ASTRAL'
        cv.drawString(lm, bm * 0.42, marca)
        cv.setFont(it, 7.5); cv.setFillColor(C.HexColor(SLATE))
        sub = '  ·  Carta Natal' + (('  ·  ' + user_line) if user_line else '')
        cv.drawString(lm + cv.stringWidth(marca, bf, 7.5), bm * 0.42, sub)
        # número de página con rombo dorado
        num = str(doc.page)
        cx = page_w - rm - 8
        cy = bm * 0.46
        r = 8.5
        p = cv.beginPath()
        p.moveTo(cx, cy + r); p.lineTo(cx + r, cy); p.lineTo(cx, cy - r); p.lineTo(cx - r, cy); p.close()
        cv.setStrokeColor(C.HexColor(GOLD)); cv.setLineWidth(0.7)
        cv.drawPath(p, fill=0, stroke=1)
        cv.setFont(bf, 7.5); cv.setFillColor(C.HexColor(NAVY))
        cv.drawCentredString(cx, cy - 2.6, num)
        cv.restoreState()

    frame = Frame(lm, bm, page_w - lm - rm, page_h - tm - bm)
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=lm, rightMargin=rm,
                          topMargin=tm, bottomMargin=bm)
    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=[Frame(lm, bm, page_w - lm - rm, page_h - tm - bm)], onPage=on_cover),
        PageTemplate(id='Body', frames=[frame], onPage=on_body),
    ])

    st_item = ParagraphStyle('li', fontName=bf, fontSize=10.3, leading=16,
                             textColor=C.HexColor(INK), leftIndent=14)

    flow = [NextPageTemplate('Body'), Spacer(1, page_h * 0.30),
            Paragraph(esc(title), st_title), Spacer(1, 14)]
    if user_line:
        flow.append(Paragraph(esc(user_line), st_sub))
    flow.append(PageBreak())

    # ── Preámbulo (Qué es una carta natal, mandamientos, cruz, elemento) ──
    if pre_blocks:
        for blk in pre_blocks:
            if blk[0] == "h2":
                flow.append(Paragraph(esc(blk[1]), st_h2))
            elif blk[0] == "p":
                flow.append(Paragraph(with_icons(blk[1], 8), st_body))
            elif blk[0] == "item":
                _, nm, tx, hl = blk
                nm_markup = with_icons(nm, 8)
                if hl:
                    nm_markup = '<font color="%s"><b>%s</b></font>' % (RED, nm_markup)
                else:
                    nm_markup = '<b>%s</b>' % nm_markup
                flow.append(Paragraph(nm_markup + ' — ' + esc(tx), st_item))
        flow.append(PageBreak())
    elif intro:
        flow.append(Paragraph(esc(intro), ParagraphStyle(
            'iB', fontName=it, fontSize=11.5, leading=18,
            textColor=C.HexColor(NAVY), alignment=TA_JUSTIFY, spaceAfter=14)))

    if chart_png_bytes:
        try:
            from PIL import Image as PILImage
            im = PILImage.open(io.BytesIO(chart_png_bytes))
            iw, ih = im.size
            disp_w = min(page_w - lm - rm, 15 * cm)
            disp_h = disp_w * ih / iw
            flow.append(Paragraph("La carta", st_h2))
            flow.append(Spacer(1, 6))
            flow.append(Image(io.BytesIO(chart_png_bytes), width=disp_w, height=disp_h))
        except Exception:
            pass

    # ── Leyenda de símbolos ─────────────────────────────────────────────
    if legend:
        flow.append(Paragraph("Leyenda de símbolos", st_h2))
        st_leg = ParagraphStyle('lg', fontName=bf, fontSize=9,
                                textColor=C.HexColor(INK))
        for gname, rows in legend:
            flow.append(Paragraph('<b>%s</b>' % esc(gname), st_h3))
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
            flow.append(t)
        flow.append(PageBreak())

    for sec_title, items in sections:
        flow.append(Paragraph(esc(sec_title), st_h2))
        for it_title, paras in items:
            flow.append(Paragraph(with_icons(it_title, 9), st_h3))
            for p in paras:
                flow.append(Paragraph(with_icons(p, 8), st_body))
    doc.build(flow)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════
#  DOCX (python-docx)
# ════════════════════════════════════════════════════════════════════════

def render_docx(title, intro, sections, chart_png_bytes, user_line,
                pre_blocks=None, legend=None):
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    def add_text_with_icons(par, text, bold=False, size=None, color=None):
        """Escribe el texto insertando el ícono propio tras cada nombre."""
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

    doc = Document()
    for s in doc.sections:
        s.top_margin = Inches(1); s.bottom_margin = Inches(1)
        s.left_margin = Inches(1); s.right_margin = Inches(1)

    h = doc.add_paragraph(); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = h.add_run(title); r.bold = True; r.font.size = Pt(24)
    r.font.color.rgb = RGBColor(0x30, 0x3A, 0x78)
    if user_line:
        sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rr = sp.add_run(user_line); rr.italic = True; rr.font.size = Pt(12)
        rr.font.color.rgb = RGBColor(0x8A, 0x93, 0xB5)
    if pre_blocks:
        for blk in pre_blocks:
            if blk[0] == "h2":
                hp = doc.add_heading(level=1)
                hr = hp.add_run(blk[1]); hr.font.color.rgb = RGBColor(0x1E, 0x24, 0x50)
            elif blk[0] == "p":
                bp = doc.add_paragraph(); bp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                add_text_with_icons(bp, blk[1])
            elif blk[0] == "item":
                _, nm, tx, hl = blk
                ip = doc.add_paragraph()
                ip.paragraph_format.left_indent = Inches(0.2)
                col = RGBColor(0xB0, 0x20, 0x20) if hl else RGBColor(0x22, 0x28, 0x4A)
                add_text_with_icons(ip, nm, bold=True, color=col)
                ip.add_run(" — " + tx)
    elif intro:
        pi = doc.add_paragraph(); pi.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        ri = pi.add_run(intro); ri.italic = True; ri.font.size = Pt(11.5)

    if chart_png_bytes:
        try:
            doc.add_paragraph()
            pic = doc.add_paragraph(); pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pic.add_run().add_picture(io.BytesIO(chart_png_bytes), width=Inches(5.6))
        except Exception:
            pass

    if legend:
        hp = doc.add_heading(level=1)
        hr = hp.add_run("Leyenda de símbolos")
        hr.font.color.rgb = RGBColor(0x1E, 0x24, 0x50)
        for gname, rows in legend:
            gp = doc.add_paragraph()
            gr = gp.add_run(gname); gr.bold = True
            gr.font.color.rgb = RGBColor(0x3A, 0x44, 0x88)
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

    for sec_title, items in sections:
        hp = doc.add_heading(level=1)
        hr = hp.add_run(sec_title); hr.font.color.rgb = RGBColor(0x1E, 0x24, 0x50)
        for it_title, paras in items:
            sp = doc.add_paragraph()
            add_text_with_icons(sp, it_title, bold=True, size=Pt(12),
                                color=RGBColor(0x3A, 0x44, 0x88))
            for p in paras:
                bp = doc.add_paragraph()
                bp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                add_text_with_icons(bp, p)

    buf = io.BytesIO(); doc.save(buf); return buf.getvalue()


def generate(chart, name, fmt, chart_png):
    """Punto de entrada. Devuelve (bytes, filename, mimetype)."""
    intro, sections = build_sections(chart)
    pre_blocks = build_preamble(chart)
    legend = build_legend()
    title = "Carta Natal"
    person = (name or '').strip()
    user_line = person if person else None
    png = _png_from_dataurl(chart_png)
    safe = "Reporte_Astral" + (("_" + person.replace(' ', '_')) if person else "")
    if fmt == 'docx':
        data = render_docx(title, intro, sections, png, user_line,
                           pre_blocks=pre_blocks, legend=legend)
        return data, safe + '.docx', \
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    data = render_pdf(title, intro, sections, png, user_line,
                      pre_blocks=pre_blocks, legend=legend)
    return data, safe + '.pdf', 'application/pdf'
