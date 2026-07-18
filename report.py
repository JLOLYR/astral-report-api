# -*- coding: utf-8 -*-
"""
report.py — Genera el reporte astral interpretativo en PDF y DOCX.

Estructura del documento:
  Portada (azul noche · tipografía serif · datos completos de la carta)
  Índice de contenidos (con números de página y enlaces internos)
  1. Qué es una carta astral natal (+ mandamientos, cruz, elemento)
  2. Carta natal: el libreto de tu vida (rueda + leyenda de símbolos)
  3. Los planetas en tu carta natal
  4. Las cúspides de las casas
  5. Aspectos astrales
  6. Glosario · Comentarios finales
  Redes sociales del astrólogo

Textos: interpretations_es.json + preamble_es.json + glossary_es.json + brand_es.json.
"""
import os
import io
import json
import base64
from datetime import date as _date

_BASE = os.path.dirname(os.path.abspath(__file__))

GOLD = '#C9A24B'
NAVY = '#1E2450'
BLUE = '#3A4488'
SLATE = '#8A93B5'
INK = '#22284A'
RED = '#B02020'
PAPER_BG = '#FFFFFF'
LIGHT = '#E8ECF8'

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']

_NAME_BY_KEY = {
    'aSol': 'Sol', 'aLuna': 'Luna', 'aMercurio': 'Mercurio', 'aVenus': 'Venus',
    'aMarte': 'Marte', 'aJupiter': 'Júpiter', 'aSaturno': 'Saturno',
    'aUrano': 'Urano', 'aNeptuno': 'Neptuno', 'aPluton': 'Plutón',
    'aChiron': 'Quirón', 'aNoduloNorte': 'Nodo Norte', 'aNoduloSur': 'Nodo Sur',
    'aLunaNegra': 'Luna Negra', 'aRuedaFortuna': 'Parte de la Fortuna',
}
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def fecha_es(iso):
    """'1988-09-28' → '28 de septiembre de 1988'."""
    try:
        p = iso.replace('/', '-').split('-')
        return "%d de %s de %s" % (int(p[2]), MESES[int(p[1]) - 1], p[0])
    except Exception:
        return iso


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
_CACHE = {}


def _load_json(fname):
    if fname not in _CACHE:
        try:
            with open(os.path.join(_BASE, fname), encoding='utf-8') as f:
                _CACHE[fname] = json.load(f)
        except Exception:
            _CACHE[fname] = {}
    return _CACHE[fname]


def _interp():
    return _load_json('interpretations_es.json')


def _preamble():
    return _load_json('preamble_es.json')


def _glossary():
    return _load_json('glossary_es.json')


def _brand():
    return _load_json('brand_es.json')


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

def build_sections(chart, chart_type='natal', house_key='house', aspects=None):
    """Construye las secciones interpretativas de una carta.
    chart_type: elige la introducción por tipo (natal/transit/solar_return/…).
    house_key: 'house' (casas propias) o 'natal_house' (para tránsitos).
    aspects: lista de aspectos a interpretar; por defecto los de la carta."""
    interp = _interp()
    nat = interp.get('natal', {})
    fb = interp.get('aspect_fallback', {}).get('natal', {})
    bct = interp.get('by_chart_type', {})
    intro = bct.get(chart_type, {}).get('intro', '') or bct.get('natal', {}).get('intro', '')

    # Encabezados por tipo de carta
    PL_HEAD = {'natal': "Los planetas en tu carta natal",
               'transit': "Los planetas en tránsito",
               'solar_return': "Los planetas de tu retorno solar",
               'progressed': "Los planetas de tu carta progresada",
               'combined': "Los planetas de la carta combinada"}
    ASP_HEAD = {'transit': "Aspectos del tránsito a tu carta natal"}

    sections = []
    items = []
    for p in chart['planets']:
        key, sign_en = p['key'], p['sign']
        house = p.get(house_key, p.get('house', 1))
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
        sections.append((PL_HEAD.get(chart_type, PL_HEAD['natal']), items))

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
    asp_source = aspects if aspects is not None else chart['aspects']
    for a in asp_source:
        ka, kb, typ = a['a'], a['b'], a['type']
        txt = (asp.get(ka, {}).get(typ, {}).get(kb)
               or asp.get(kb, {}).get(typ, {}).get(ka)
               or fb.get(typ))
        if not txt:
            continue
        na = name_es.get(ka) or _NAME_BY_KEY.get(ka, ka)
        nb = name_es.get(kb) or _NAME_BY_KEY.get(kb, kb)
        if chart_type == 'transit':
            title = "%s (tránsito) %s %s (natal)  (orbe %.1f°)" % (
                na, asp_es.get(typ, typ.lower()), nb, a.get('orb', 0))
        else:
            title = "%s %s %s  (orbe %.1f°)" % (
                na, asp_es.get(typ, typ.lower()), nb, a.get('orb', 0))
        asp_items.append((title, [txt]))
    if asp_items:
        sections.append((ASP_HEAD.get(chart_type, "Aspectos astrales"), asp_items))

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


def _png_from_dataurl(chart_png, max_side=900):
    """Decodifica la imagen y la reduce si viene muy grande. Acotar el tamaño
    mantiene bajo el uso de memoria y el tiempo de generación en el servidor."""
    if not chart_png:
        return None
    try:
        if ',' in chart_png:
            chart_png = chart_png.split(',', 1)[1]
        raw = base64.b64decode(chart_png)
    except Exception:
        return None
    try:
        from PIL import Image as PILImage
        im = PILImage.open(io.BytesIO(raw))
        if max(im.size) > max_side:
            ratio = max_side / float(max(im.size))
            im = im.convert('RGB').resize(
                (max(1, int(im.size[0] * ratio)), max(1, int(im.size[1] * ratio))),
                PILImage.LANCZOS)
            b = io.BytesIO()
            im.save(b, 'PNG', optimize=True)
            raw = b.getvalue()
        im.close()
    except Exception:
        pass
    return raw


# ════════════════════════════════════════════════════════════════════════
#  PDF
# ════════════════════════════════════════════════════════════════════════

def render_pdf(sections, chart_png_bytes, meta,
               pre_blocks=None, legend=None, glossary=None, chart_png2_bytes=None):
    """meta: dict(name, city, astrologer, date, time)"""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors as C
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame,
                                    NextPageTemplate, Paragraph, Spacer,
                                    PageBreak, Image, Table, TableStyle)
    from reportlab.platypus.tableofcontents import TableOfContents

    buf = io.BytesIO()
    page_w, page_h = A4
    lm = rm = 2.6 * cm
    tm = bm = 2.4 * cm
    bf, bd, it = 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'
    # Serif elegante para la portada (siempre disponible en PDF)
    sf, sb, si = 'Times-Roman', 'Times-Bold', 'Times-Italic'

    person = meta.get('name') or ''
    astrologer = meta.get('astrologer') or _brand().get('astrologo_default', '')
    hoy = fecha_es(_date.today().isoformat())

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

    # Estilos (capítulos centrados)
    st_h2 = ParagraphStyle('h2', fontName=bd, fontSize=16, leading=21,
                           textColor=C.HexColor(NAVY), spaceBefore=18, spaceAfter=10,
                           keepWithNext=1, alignment=TA_CENTER)
    st_h3 = ParagraphStyle('h3', fontName=bd, fontSize=12, leading=15,
                           textColor=C.HexColor(BLUE), spaceBefore=10, spaceAfter=6,
                           keepWithNext=1)
    st_body = ParagraphStyle('b', fontName=bf, fontSize=10.3, leading=15,
                             textColor=C.HexColor(INK), alignment=TA_JUSTIFY,
                             spaceAfter=5, firstLineIndent=14)
    st_item = ParagraphStyle('li', fontName=bf, fontSize=10.3, leading=16,
                             textColor=C.HexColor(INK), leftIndent=14)

    _WM_SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
                 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

    def _watermark_signs(cv):
        """Los 12 signos, sutiles y dorados, repartidos alrededor del margen."""
        import math
        sz = 24
        # Los signos van holgadamente por dentro del marco dorado (que está a
        # 44 pt del borde) y por encima del pie de portada, para que ninguno
        # quede sobre una línea ni sobre un texto.
        inset = 44 + sz / 2 + 12
        top_y = page_h - inset          # justo dentro del marco superior
        bot_y = 145                     # por encima de astrólogo/fecha/marca
        cx = page_w / 2
        cy = (top_y + bot_y) / 2.0
        rx = page_w / 2 - inset
        ry = (top_y - bot_y) / 2.0
        for i, sg in enumerate(_WM_SIGNS):
            fp = os.path.join(_ICONS_DIR, 'wm_' + sg + '.png')
            if not os.path.exists(fp):
                continue
            ang = math.pi / 2 - i * (2 * math.pi / 12)  # arranca arriba, en sentido horario
            x = cx + rx * math.cos(ang)
            y = cy + ry * math.sin(ang)
            try:
                cv.drawImage(fp, x - sz / 2, y - sz / 2, width=sz, height=sz, mask='auto')
            except Exception:
                pass

    def on_cover(cv, doc):
        cv.saveState()
        cv.setFillColorRGB(0x0E / 255., 0x13 / 255., 0x32 / 255.)
        cv.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        _watermark_signs(cv)
        cv.setStrokeColor(C.HexColor(GOLD))
        cv.setLineWidth(1.0)
        cv.rect(36, 36, page_w - 72, page_h - 72, fill=0, stroke=1)
        cv.setLineWidth(0.4)
        cv.rect(44, 44, page_w - 88, page_h - 88, fill=0, stroke=1)
        # ornamento
        cx, cy, r = page_w / 2, page_h * 0.76, 9
        p = cv.beginPath()
        p.moveTo(cx, cy + r); p.lineTo(cx + r, cy); p.lineTo(cx, cy - r)
        p.lineTo(cx - r, cy); p.close()
        cv.setLineWidth(0.9)
        cv.drawPath(p, fill=0, stroke=1)
        cv.circle(cx, cy, 1.6, fill=1, stroke=0)
        cv.setLineWidth(0.5)
        cv.line(cx - 110, cy, cx - r - 12, cy)
        cv.line(cx + r + 12, cy, cx + 110, cy)
        # astrólogo y fecha de generación
        if astrologer:
            cv.setFont(si, 11.5)
            cv.setFillColor(C.HexColor(LIGHT))
            cv.drawCentredString(page_w / 2, 118, 'Astrólogo: %s' % astrologer)
        cv.setFont(sf, 9.5)
        cv.setFillColor(C.HexColor(SLATE))
        cv.drawCentredString(page_w / 2, 100, hoy)
        cv.setFont(bf, 9)
        cv.setFillColor(C.HexColor(GOLD))
        cv.drawCentredString(page_w / 2, 58, 'R E P O R T E   A S T R A L')
        cv.restoreState()

    def _diamond(cv, cx, cy, r):
        p = cv.beginPath()
        p.moveTo(cx, cy + r); p.lineTo(cx + r, cy); p.lineTo(cx, cy - r)
        p.lineTo(cx - r, cy); p.close()
        cv.drawPath(p, fill=0, stroke=1)

    def on_body(cv, doc):
        cv.saveState()
        cv.setFillColor(C.HexColor(PAPER_BG)); cv.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        ty = page_h - tm * 0.52
        cv.setStrokeColor(C.HexColor(GOLD)); cv.setLineWidth(0.6)
        cv.line(page_w / 2 - 90, ty, page_w / 2 - 14, ty)
        cv.line(page_w / 2 + 14, ty, page_w / 2 + 90, ty)
        cv.setLineWidth(0.7)
        _diamond(cv, page_w / 2, ty, 4.5)
        cv.setFillColor(C.HexColor(GOLD))
        cv.circle(page_w / 2, ty, 1.0, fill=1, stroke=0)
        cv.setLineWidth(0.7)
        cv.line(lm, bm * 0.72, page_w - rm, bm * 0.72)
        cv.setFont(bf, 7.5); cv.setFillColor(C.HexColor(NAVY))
        marca = 'REPORTE ASTRAL'
        cv.drawString(lm, bm * 0.42, marca)
        cv.setFont(it, 7.5); cv.setFillColor(C.HexColor(SLATE))
        _tipo = meta.get('subtitle', 'de Carta Natal')
        if _tipo.lower().startswith('de '):
            _tipo = _tipo[3:]
        sub = '  ·  ' + _tipo + (('  ·  ' + person) if person else '')
        cv.drawString(lm + cv.stringWidth(marca, bf, 7.5), bm * 0.42, sub)
        num = str(doc.page)
        cx2 = page_w - rm - 8
        cy2 = bm * 0.46
        cv.setStrokeColor(C.HexColor(GOLD)); cv.setLineWidth(0.7)
        _diamond(cv, cx2, cy2, 8.5)
        cv.setFont(bf, 7.5); cv.setFillColor(C.HexColor(NAVY))
        cv.drawCentredString(cx2, cy2 - 2.6, num)
        cv.restoreState()

    # Página apaisada (para comparar las dos ruedas lado a lado, grandes)
    land_w, land_h = landscape(A4)

    def on_wheels(cv, doc):
        cv.saveState()
        cv.setFillColor(C.HexColor(PAPER_BG)); cv.rect(0, 0, land_w, land_h, fill=1, stroke=0)
        cv.setStrokeColor(C.HexColor(GOLD)); cv.setLineWidth(0.7)
        cv.line(lm, bm * 0.72, land_w - rm, bm * 0.72)
        cv.setFont(bf, 7.5); cv.setFillColor(C.HexColor(NAVY))
        marca = 'REPORTE ASTRAL'
        cv.drawString(lm, bm * 0.42, marca)
        cv.setFont(it, 7.5); cv.setFillColor(C.HexColor(SLATE))
        _tipo = meta.get('subtitle', 'de Carta Natal')
        if _tipo.lower().startswith('de '):
            _tipo = _tipo[3:]
        sub = '  ·  ' + _tipo + (('  ·  ' + person) if person else '')
        cv.drawString(lm + cv.stringWidth(marca, bf, 7.5), bm * 0.42, sub)
        cx2 = land_w - rm - 8
        cv.setStrokeColor(C.HexColor(GOLD)); cv.setLineWidth(0.7)
        _diamond(cv, cx2, bm * 0.46, 8.5)
        cv.setFont(bf, 7.5); cv.setFillColor(C.HexColor(NAVY))
        cv.drawCentredString(cx2, bm * 0.46 - 2.6, str(doc.page))
        cv.restoreState()

    class _Doc(BaseDocTemplate):
        def afterFlowable(self, f):
            key = getattr(f, '_tocKey', None)
            if key:
                lvl = 0 if f.style.name == 'h2' else 1
                self.notify('TOCEntry', (lvl, f.getPlainText(), self.page, key))

    frame = Frame(lm, bm, page_w - lm - rm, page_h - tm - bm)
    frame_land = Frame(lm, bm, land_w - lm - rm, land_h - tm * 0.7 - bm)
    doc = _Doc(buf, pagesize=A4, leftMargin=lm, rightMargin=rm,
               topMargin=tm, bottomMargin=bm)
    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=[Frame(lm, bm, page_w - lm - rm, page_h - tm - bm)], onPage=on_cover),
        PageTemplate(id='Body', frames=[frame], onPage=on_body),
        PageTemplate(id='Wheels', frames=[frame_land], onPage=on_wheels, pagesize=landscape(A4)),
    ])

    nkey = [0]
    content = []

    def H2(text):
        key = "sec%d" % nkey[0]; nkey[0] += 1
        p = Paragraph('<a name="%s"/>' % key + with_icons(text, 10), st_h2)
        p._tocKey = key
        content.append(p)

    def H3(text):
        key = "sec%d" % nkey[0]; nkey[0] += 1
        p = Paragraph('<a name="%s"/>' % key + with_icons(text, 9), st_h3)
        p._tocKey = key
        content.append(p)

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

    legend_done = [False]

    def add_legend(ncols=4, total_w=None, fs=9, ic_sz=10):
        """Leyenda de símbolos. En la página apaisada se usa con más columnas."""
        if not legend:
            return
        tw = total_w if total_w else (page_w - lm - rm)
        H3("Leyenda de símbolos")
        st_leg = ParagraphStyle('lg%d' % ncols, fontName=bf, fontSize=fs,
                                textColor=C.HexColor(INK))
        for gname, rows in legend:
            content.append(Paragraph('<b>%s</b>' % esc(gname), ParagraphStyle(
                'lgt%d' % ncols, fontName=bd, fontSize=fs + 1,
                textColor=C.HexColor(BLUE), spaceBefore=3, spaceAfter=1)))
            cells, row = [], []
            for icon, label in rows:
                row.append(Paragraph(
                    '<img src="%s" width="%d" height="%d" valign="-2"/> %s'
                    % (icon, ic_sz, ic_sz, esc(label)), st_leg))
                if len(row) == ncols:
                    cells.append(row); row = []
            if row:
                row += [Paragraph('', st_leg)] * (ncols - len(row))
                cells.append(row)
            t = Table(cells, colWidths=[tw / float(ncols)] * ncols)
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            content.append(t)

    if chart_png_bytes:
        try:
            from PIL import Image as PILImage
            caps = meta.get('img_captions')
            if chart_png2_bytes and caps:
                # Ambas ruedas en UNA página apaisada, lado a lado, grandes,
                # para poder compararlas.
                # Evita una página en blanco si ya venía un salto de página
                if content and isinstance(content[-1], PageBreak):
                    content.insert(len(content) - 1, NextPageTemplate('Wheels'))
                else:
                    content.append(NextPageTemplate('Wheels'))
                    content.append(PageBreak())
                H2(meta.get('chart_heading', 'Tus dos cartas'))
                content.append(Spacer(1, 4))
                colw = (land_w - lm - rm) / 2.0
                # Deja sitio para la leyenda en la misma página
                each = min(colw - 0.5 * cm, 9.5 * cm)
                st_wcap = ParagraphStyle('wcap', fontName=bd, fontSize=12, leading=15,
                                         textColor=C.HexColor(BLUE), alignment=TA_CENTER,
                                         spaceAfter=5)
                row = []
                for img_bytes, cap in ((chart_png_bytes, caps[0]),
                                       (chart_png2_bytes, caps[1])):
                    im = PILImage.open(io.BytesIO(img_bytes))
                    iw, ih = im.size
                    w = each; h = w * ih / iw
                    row.append([Paragraph(cap, st_wcap),
                                Image(io.BytesIO(img_bytes), width=w, height=h)])
                tw = Table([row], colWidths=[colw, colw])
                tw.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                        ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
                content.append(tw)
                # La leyenda entra en la misma página apaisada
                add_legend(ncols=8, total_w=land_w - lm - rm, fs=8, ic_sz=9)
                legend_done[0] = True
                content.append(NextPageTemplate('Body'))
                content.append(PageBreak())
            else:
                im = PILImage.open(io.BytesIO(chart_png_bytes))
                iw, ih = im.size
                disp_w = min(page_w - lm - rm, 15 * cm)
                disp_h = disp_w * ih / iw
                H2(meta.get('chart_heading', 'Carta natal: el libreto de tu vida'))
                content.append(Spacer(1, 6))
                content.append(Image(io.BytesIO(chart_png_bytes), width=disp_w, height=disp_h))
        except Exception:
            pass

    if legend and not legend_done[0]:
        add_legend()
        content.append(PageBreak())

    for sec_title, items in sections:
        H2(sec_title)
        for it_title, paras in items:
            H3(it_title)
            for p in paras:
                content.append(Paragraph(with_icons(p, 8), st_body))

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

    # ── Redes sociales del astrólogo ─────────────────────────────────────
    brand = _brand()
    redes = brand.get('redes', [])
    if redes:
        content.append(PageBreak())
        H2(brand.get('redes_titulo', 'Encuéntrame en'))
        st_red = ParagraphStyle('rd', fontName=bf, fontSize=11, leading=22,
                                textColor=C.HexColor(INK), alignment=TA_CENTER)
        if astrologer:
            content.append(Paragraph('<font name="%s" size="13" color="%s"><i>%s</i></font>'
                                     % (si, BLUE, esc(astrologer)), ParagraphStyle(
                                         'rda', alignment=TA_CENTER, spaceAfter=12,
                                         fontName=si, fontSize=13,
                                         textColor=C.HexColor(BLUE))))
        for r in redes:
            ic = os.path.join(_ICONS_DIR, 'soc_' + r.get('icon', '') + '.png')
            ic_markup = ('<img src="%s" width="13" height="13" valign="-2"/> ' % ic) \
                if os.path.exists(ic) else ''
            content.append(Paragraph(
                ic_markup + '<b>%s</b> — <a href="%s" color="%s"><u>%s</u></a>'
                % (esc(r.get('nombre', '')), r.get('url', '#'), BLUE,
                   esc(r.get('texto', r.get('url', '')))), st_red))

    # ── Índice con números de página ─────────────────────────────────────
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle('tocc', fontName=bd, fontSize=11.5, leading=18,
                       textColor=C.HexColor(NAVY)),
        ParagraphStyle('tocs', fontName=bf, fontSize=9.5, leading=14.5,
                       textColor=C.HexColor(BLUE), leftIndent=20),
    ]
    toc.dotsMinLevel = 0

    # ── Portada (serif elegante) ─────────────────────────────────────────
    st_cv1 = ParagraphStyle('cv1', fontName=sb, fontSize=30, leading=36,
                            textColor=C.HexColor(GOLD), alignment=TA_CENTER)
    st_cv2 = ParagraphStyle('cv2', fontName=si, fontSize=17, leading=22,
                            textColor=C.HexColor(SLATE), alignment=TA_CENTER)
    st_cv3 = ParagraphStyle('cv3', fontName=sb, fontSize=19, leading=25,
                            textColor=C.HexColor(LIGHT), alignment=TA_CENTER)
    st_cv4 = ParagraphStyle('cv4', fontName=sf, fontSize=12.5, leading=19,
                            textColor=C.HexColor(SLATE), alignment=TA_CENTER)

    flow = [NextPageTemplate('Body'), Spacer(1, page_h * 0.24),
            Paragraph('Reporte Astrológico', st_cv1),
            Spacer(1, 4),
            Paragraph(esc(meta.get('subtitle', 'de Carta Natal')), st_cv2),
            Spacer(1, 34)]
    if person:
        flow.append(Paragraph(esc(person), st_cv3))
        flow.append(Spacer(1, 10))
    linea_fecha = meta.get('time', '')
    if linea_fecha:
        linea_fecha += '  —  '
    linea_fecha += fecha_es(meta.get('date', ''))
    flow.append(Paragraph(esc(linea_fecha), st_cv4))
    if meta.get('city'):
        flow.append(Paragraph(esc(meta['city']), st_cv4))

    st_cv5 = ParagraphStyle('cv5', fontName=si, fontSize=11, leading=16,
                            textColor=C.HexColor(GOLD), alignment=TA_CENTER)
    st_cv6 = ParagraphStyle('cv6', fontName=sf, fontSize=11.5, leading=17,
                            textColor=C.HexColor(SLATE), alignment=TA_CENTER)

    # Retorno solar: lugar y momento exacto del retorno (no es la hora de nacimiento)
    if meta.get('chart_type') == 'solar_return' and meta.get('return_moment'):
        flow.append(Spacer(1, 16))
        if meta.get('relocated') and meta.get('return_place'):
            flow.append(Paragraph('Relocalizado en: ' + esc(meta['return_place']), st_cv5))
        rmoment = esc(meta['return_moment'])
        if meta.get('return_tz'):
            rmoment += '  (' + esc(meta['return_tz']) + ')'
        flow.append(Paragraph('El retorno solar exacto ocurre el', st_cv6))
        flow.append(Paragraph(rmoment, st_cv5))
        if meta.get('return_ut'):
            flow.append(Paragraph(esc(meta['return_ut']) + ' UT', st_cv6))

    # Combinada: segunda persona con sus datos
    pb = meta.get('person_b')
    if meta.get('chart_type') == 'combined' and pb:
        flow.append(Spacer(1, 14))
        flow.append(Paragraph('en vínculo con', st_cv6))
        if pb.get('name'):
            flow.append(Paragraph(esc(pb['name']), st_cv3))
        lb = pb.get('time', '')
        if lb:
            lb += '  —  '
        lb += fecha_es(pb.get('date', ''))
        flow.append(Paragraph(esc(lb), st_cv4))
        if pb.get('city'):
            flow.append(Paragraph(esc(pb['city']), st_cv4))

    flow.append(PageBreak())

    flow.append(Paragraph('Índice de contenidos', st_h2))
    flow.append(toc)
    flow.append(PageBreak())
    flow += content
    doc.multiBuild(flow)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════
#  DOCX
# ════════════════════════════════════════════════════════════════════════

def render_docx(sections, chart_png_bytes, meta,
                pre_blocks=None, legend=None, glossary=None, chart_png2_bytes=None):
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
    GOLD_RGB = RGBColor(0xC9, 0xA2, 0x4B)

    person = meta.get('name') or ''
    astrologer = meta.get('astrologer') or _brand().get('astrologo_default', '')
    hoy = fecha_es(_date.today().isoformat())

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

    def ext_link(par, url, text, color='3A4488'):
        part = par.part
        r_id = part.relate_to(url,
            'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
            is_external=True)
        h = OxmlElement('w:hyperlink')
        h.set(qn('r:id'), r_id)
        r = OxmlElement('w:r')
        rPr = OxmlElement('w:rPr')
        c = OxmlElement('w:color'); c.set(qn('w:val'), color); rPr.append(c)
        u = OxmlElement('w:u'); u.set(qn('w:val'), 'single'); rPr.append(u)
        r.append(rPr)
        t = OxmlElement('w:t'); t.text = text
        r.append(t); h.append(r); par._p.append(h)

    def toc_field(par):
        """Campo TOC de Word: muestra títulos con números de página
        (clic derecho → Actualizar campos)."""
        fld = OxmlElement('w:fldSimple')
        fld.set(qn('w:instr'), 'TOC \\o "1-2" \\h \\z \\u')
        r = OxmlElement('w:r')
        t = OxmlElement('w:t')
        t.text = "Índice — haz clic derecho y elige «Actualizar campos» para ver las páginas."
        r.append(t); fld.append(r)
        par._p.append(fld)

    doc = Document()
    for s in doc.sections:
        s.top_margin = Inches(1); s.bottom_margin = Inches(1)
        s.left_margin = Inches(1); s.right_margin = Inches(1)

    def cover_line(text, size, color, bold=False, italic=False, font='Georgia',
                   space_after=6):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(space_after)
        r = p.add_run(text)
        r.bold = bold; r.italic = italic
        r.font.size = Pt(size); r.font.color.rgb = color; r.font.name = font
        return p

    # Portada
    for _ in range(4):
        doc.add_paragraph()
    cover_line('Reporte Astrológico', 28, GOLD_RGB, bold=True)
    cover_line(meta.get('subtitle', 'de Carta Natal'), 15, SLATE_RGB, italic=True, space_after=22)
    if person:
        cover_line(person, 17, NAVY_RGB, bold=True, space_after=10)
    linea = (meta.get('time', '') + '  —  ' if meta.get('time') else '') + fecha_es(meta.get('date', ''))
    cover_line(linea, 12, INK_RGB)
    if meta.get('city'):
        cover_line(meta['city'], 12, INK_RGB, space_after=8)

    # Retorno solar: lugar y momento exacto del retorno
    if meta.get('chart_type') == 'solar_return' and meta.get('return_moment'):
        if meta.get('relocated') and meta.get('return_place'):
            cover_line('Relocalizado en: ' + meta['return_place'], 11, GOLD_RGB, italic=True)
        rmoment = meta['return_moment'] + (('  (' + meta['return_tz'] + ')') if meta.get('return_tz') else '')
        cover_line('El retorno solar exacto ocurre el', 10.5, SLATE_RGB)
        cover_line(rmoment, 12, GOLD_RGB, bold=True)
        if meta.get('return_ut'):
            cover_line(meta['return_ut'] + ' UT', 10, SLATE_RGB, space_after=20)

    # Combinada: segunda persona con sus datos
    pb = meta.get('person_b')
    if meta.get('chart_type') == 'combined' and pb:
        cover_line('en vínculo con', 10.5, SLATE_RGB, italic=True)
        if pb.get('name'):
            cover_line(pb['name'], 15, NAVY_RGB, bold=True)
        lb = (pb.get('time', '') + '  —  ' if pb.get('time') else '') + fecha_es(pb.get('date', ''))
        cover_line(lb, 12, INK_RGB)
        if pb.get('city'):
            cover_line(pb['city'], 12, INK_RGB, space_after=20)

    if astrologer:
        cover_line('Astrólogo: %s' % astrologer, 11.5, BLUE_RGB, italic=True)
    cover_line(hoy, 9.5, SLATE_RGB)
    cover_line('R E P O R T E   A S T R A L', 9, GOLD_RGB, space_after=0)
    doc.add_page_break()

    # Índice (campo de Word con números de página)
    hp = doc.add_heading(level=1)
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hr = hp.add_run("Índice de contenidos"); hr.font.color.rgb = NAVY_RGB
    toc_field(doc.add_paragraph())
    doc.add_page_break()

    def H2(text):
        hp = doc.add_heading(level=1)
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_text_with_icons(hp, text, color=NAVY_RGB)

    def H3(text):
        hp = doc.add_heading(level=2)
        add_text_with_icons(hp, text, color=BLUE_RGB)

    def body_p(text):
        bp = doc.add_paragraph()
        bp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        bp.paragraph_format.first_line_indent = Inches(0.18)
        add_text_with_icons(bp, text)

    def item_p(nm, tx, hl=False):
        ip = doc.add_paragraph()
        ip.paragraph_format.left_indent = Inches(0.2)
        add_text_with_icons(ip, nm, bold=True, color=RED_RGB if hl else INK_RGB)
        ip.add_run(" — " + tx)

    if pre_blocks:
        for blk in pre_blocks:
            if blk[0] == "h2":
                H2(blk[1])
            elif blk[0] == "h3":
                H3(blk[1])
            elif blk[0] == "p":
                body_p(blk[1])
            elif blk[0] == "item":
                item_p(blk[1], blk[2], blk[3])

    if chart_png_bytes:
        caps = meta.get('img_captions')
        if chart_png2_bytes and caps:
            # Ambas ruedas en una página apaisada, lado a lado, para compararlas.
            from docx.enum.section import WD_ORIENT, WD_SECTION
            sec = doc.add_section(WD_SECTION.NEW_PAGE)
            sec.orientation = WD_ORIENT.LANDSCAPE
            if sec.page_width < sec.page_height:
                sec.page_width, sec.page_height = sec.page_height, sec.page_width
            sec.left_margin = sec.right_margin = Inches(0.6)
            sec.top_margin = sec.bottom_margin = Inches(0.7)
            H2(meta.get('chart_heading', 'Tus dos cartas'))
            tbl = doc.add_table(rows=1, cols=2)
            for j, (img_bytes, cap) in enumerate(((chart_png_bytes, caps[0]),
                                                  (chart_png2_bytes, caps[1]))):
                cell = tbl.cell(0, j)
                cp = cell.paragraphs[0]; cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cr = cp.add_run(cap); cr.bold = True; cr.font.color.rgb = BLUE_RGB
                ip = cell.add_paragraph(); ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
                try:
                    ip.add_run().add_picture(io.BytesIO(img_bytes), width=Inches(4.7))
                except Exception:
                    pass
            sec2 = doc.add_section(WD_SECTION.NEW_PAGE)
            sec2.orientation = WD_ORIENT.PORTRAIT
            if sec2.page_width > sec2.page_height:
                sec2.page_width, sec2.page_height = sec2.page_height, sec2.page_width
            sec2.left_margin = sec2.right_margin = Inches(1)
            sec2.top_margin = sec2.bottom_margin = Inches(1)
        else:
            H2(meta.get('chart_heading', 'Carta natal: el libreto de tu vida'))
            pic = doc.add_paragraph(); pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
            try:
                pic.add_run().add_picture(io.BytesIO(chart_png_bytes), width=Inches(5.6))
            except Exception:
                pass

    if legend:
        H3("Leyenda de símbolos")
        for gname, rows in legend:
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

    for sec_title, items in sections:
        H2(sec_title)
        for it_title, paras in items:
            H3(it_title)
            for p in paras:
                body_p(p)

    if glossary:
        for blk in glossary:
            if blk[0] == "h2":
                H2(blk[1])
            elif blk[0] == "h3":
                H3(blk[1])
            elif blk[0] == "p":
                body_p(blk[1])
            elif blk[0] == "item":
                item_p(blk[1], blk[2], False)

    brand = _brand()
    redes = brand.get('redes', [])
    if redes:
        doc.add_page_break()
        H2(brand.get('redes_titulo', 'Encuéntrame en'))
        if astrologer:
            cover_line(astrologer, 13, BLUE_RGB, italic=True)
        for r in redes:
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            ic = os.path.join(_ICONS_DIR, 'soc_' + r.get('icon', '') + '.png')
            if os.path.exists(ic):
                try:
                    p.add_run().add_picture(ic, height=Inches(0.15))
                    p.add_run('  ')
                except Exception:
                    pass
            rr = p.add_run(r.get('nombre', '') + ' — '); rr.bold = True
            rr.font.color.rgb = INK_RGB
            ext_link(p, r.get('url', '#'), r.get('texto', r.get('url', '')))

    buf = io.BytesIO(); doc.save(buf); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════
#  ORQUESTACIÓN
# ════════════════════════════════════════════════════════════════════════

_SUBTITLE = {
    'natal': 'de Carta Natal', 'transit': 'de Tránsitos',
    'solar_return': 'de Retorno Solar', 'progressed': 'de Carta Progresada',
    'combined': 'de Carta Combinada',
}
_CHART_HEADING = {
    'natal': 'Carta natal: el libreto de tu vida',
    'transit': 'Bi-rueda: tu carta natal (interior) y los tránsitos (exterior)',
    'solar_return': 'Tus dos cartas: natal y retorno solar',
    'progressed': 'Tus dos cartas: natal y progresada',
    'combined': 'La carta combinada del vínculo',
}
_INTRO_TITLE = {
    'transit': 'Qué son los tránsitos',
    'solar_return': 'Qué es el retorno solar',
    'progressed': 'Qué es la carta progresada',
    'combined': 'Qué es la carta combinada',
}


def generate(data, name, fmt, chart_png, city="", astrologer="", chart_type="natal",
             chart_png2=None, name_b="", city_b=""):
    """Punto de entrada. Devuelve (bytes, filename, mimetype).

    `data` es el dict que devuelve astro para el tipo pedido:
      natal        → la carta natal
      transit      → {natal, transit, cross_aspects}
      solar_return → {natal, solar_return, year}
      progressed   → {natal, progressed, years}
      combined     → {a, b, combined}
    """
    ct = chart_type or "natal"

    if ct == "transit":
        chart = data['transit']
        base_meta = data.get('natal', chart)
        xa = [{'a': x['transit'], 'b': x['natal'], 'type': x['type'], 'orb': x['orb']}
              for x in data.get('cross_aspects', [])]
        _intro, sections = build_sections(chart, 'transit',
                                          house_key='natal_house', aspects=xa)
    elif ct == "solar_return":
        chart = data['solar_return']
        base_meta = data.get('natal', chart)
        _intro, sections = build_sections(chart, 'solar_return')
    elif ct == "progressed":
        chart = data['progressed']
        base_meta = data.get('natal', chart)
        _intro, sections = build_sections(chart, 'progressed')
    elif ct == "combined":
        chart = data['combined']
        base_meta = data.get('a', chart)
        _intro, sections = build_sections(chart, 'combined')
    else:
        ct = "natal"
        chart = data
        base_meta = data
        _intro, sections = build_sections(chart, 'natal')

    if ct == "natal":
        pre_blocks = build_preamble(chart)
    else:
        pre_blocks = []
        if _INTRO_TITLE.get(ct):
            pre_blocks.append(("h2", _INTRO_TITLE[ct]))
        if _intro:
            pre_blocks.append(("p", _intro))

    subtitle = _SUBTITLE.get(ct, 'de Carta Natal')
    if ct == 'solar_return' and data.get('year'):
        subtitle += ' %s' % data['year']

    legend = build_legend()
    glossary = build_glossary()
    person = (name or '').strip()
    meta = {
        'name': person,
        'city': (city or '').strip(),
        'astrologer': (astrologer or '').strip(),
        'date': base_meta.get('input', {}).get('date', ''),
        'time': base_meta.get('input', {}).get('time', ''),
        'subtitle': subtitle,
        'chart_heading': _CHART_HEADING.get(ct, 'Carta natal'),
        'chart_type': ct,
    }

    # Datos específicos por tipo para la portada
    if ct == 'solar_return':
        si = data.get('solar_return', {}).get('input', {})
        rl = si.get('return_local', '')          # 'YYYY-MM-DD HH:MM'
        if rl:
            parts = rl.split(' ')
            dp = parts[0]; tp = parts[1] if len(parts) > 1 else ''
            meta['return_moment'] = fecha_es(dp) + ((', ' + tp) if tp else '')
        else:
            meta['return_moment'] = ''
        meta['return_tz'] = si.get('return_tz', '')
        meta['return_ut'] = si.get('return_ut', '')
        meta['return_place'] = (data.get('reloc_city') or city or '').strip()
        meta['relocated'] = si.get('relocated', False)
        meta['img_captions'] = ['Carta natal', 'Retorno solar']
    elif ct == 'progressed':
        meta['img_captions'] = ['Carta natal', 'Carta progresada']
    elif ct == 'combined':
        bi = data.get('b', {}).get('input', {})
        meta['person_b'] = {
            'name': (name_b or '').strip(),
            'date': bi.get('date', ''), 'time': bi.get('time', ''),
            'city': (city_b or '').strip(),
        }

    png = _png_from_dataurl(chart_png)
    png2 = _png_from_dataurl(chart_png2)
    tsuf = '' if ct == 'natal' else ('_' + ct)
    safe = "Reporte_Astral" + (("_" + person.replace(' ', '_')) if person else "") + tsuf
    if fmt == 'docx':
        out = render_docx(sections, png, meta,
                          pre_blocks=pre_blocks, legend=legend, glossary=glossary,
                          chart_png2_bytes=png2)
        return out, safe + '.docx', \
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    out = render_pdf(sections, png, meta,
                     pre_blocks=pre_blocks, legend=legend, glossary=glossary,
                     chart_png2_bytes=png2)
    return out, safe + '.pdf', 'application/pdf'
