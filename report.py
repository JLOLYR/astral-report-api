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

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']

_INTERP = None


def _interp():
    global _INTERP
    if _INTERP is None:
        with open(os.path.join(_BASE, 'interpretations_es.json'), encoding='utf-8') as f:
            _INTERP = json.load(f)
    return _INTERP


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

def render_pdf(title, intro, sections, chart_png_bytes, user_line):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors as C
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame,
                                    NextPageTemplate, Paragraph, Spacer,
                                    PageBreak, Image, KeepTogether)

    buf = io.BytesIO()
    page_w, page_h = A4
    lm = rm = 2.6 * cm
    tm = bm = 2.4 * cm
    bf, bd, it = 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'

    def esc(t):
        return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

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
        cv.saveState()
        ct = (0x0B, 0x10, 0x30); cb = (0xEC, 0xEF, 0xF7); n = 150
        for i in range(n):
            yc = (i + 0.5) / n
            col = tuple(cb[k] + (ct[k] - cb[k]) * yc for k in range(3))
            cv.setFillColorRGB(col[0] / 255., col[1] / 255., col[2] / 255.)
            cv.rect(0, i * page_h / n, page_w + 1, page_h / n + 1.2, fill=1, stroke=0)
        cv.setFillColor(C.HexColor(BLUE)); cv.circle(page_w / 2, page_h * 0.80, 74, fill=1, stroke=0)
        cv.setFillColorRGB(ct[0] / 255., ct[1] / 255., ct[2] / 255.)
        cv.circle(page_w / 2, page_h * 0.80, 63, fill=1, stroke=0)
        cv.setStrokeColor(C.HexColor(GOLD)); cv.setLineWidth(0.8)
        cv.line(page_w * 0.32, page_h * 0.12, page_w * 0.68, page_h * 0.12)
        cv.restoreState()

    def on_body(cv, doc):
        cv.saveState()
        cv.setFillColor(C.HexColor('#FBFAF6')); cv.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        cv.setStrokeColor(C.HexColor(GOLD)); cv.setLineWidth(0.7)
        cv.line(lm, bm * 0.7, page_w - rm, bm * 0.7)
        cv.setFont(it, 8); cv.setFillColor(C.HexColor(SLATE))
        cv.drawCentredString(page_w / 2, bm * 0.5, 'Reporte Astral')
        cv.drawRightString(page_w - rm, bm * 0.5, str(doc.page))
        cv.restoreState()

    frame = Frame(lm, bm, page_w - lm - rm, page_h - tm - bm)
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=lm, rightMargin=rm,
                          topMargin=tm, bottomMargin=bm)
    doc.addPageTemplates([
        PageTemplate(id='Cover', frames=[Frame(lm, bm, page_w - lm - rm, page_h - tm - bm)], onPage=on_cover),
        PageTemplate(id='Body', frames=[frame], onPage=on_body),
    ])

    flow = [NextPageTemplate('Body'), Spacer(1, page_h * 0.17),
            Paragraph(esc(title), st_title), Spacer(1, 10)]
    if user_line:
        flow.append(Paragraph(esc(user_line), st_sub))
    flow.append(Spacer(1, 24))
    if intro:
        flow.append(Paragraph(esc(intro), st_intro))
    flow.append(PageBreak())

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
            flow.append(PageBreak())
        except Exception:
            pass

    for sec_title, items in sections:
        flow.append(Paragraph(esc(sec_title), st_h2))
        for it_title, paras in items:
            flow.append(Paragraph(esc(it_title), st_h3))
            for p in paras:
                flow.append(Paragraph(esc(p), st_body))
    doc.build(flow)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════
#  DOCX (python-docx)
# ════════════════════════════════════════════════════════════════════════

def render_docx(title, intro, sections, chart_png_bytes, user_line):
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH

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
    if intro:
        pi = doc.add_paragraph(); pi.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        ri = pi.add_run(intro); ri.italic = True; ri.font.size = Pt(11.5)

    if chart_png_bytes:
        try:
            doc.add_paragraph()
            pic = doc.add_paragraph(); pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pic.add_run().add_picture(io.BytesIO(chart_png_bytes), width=Inches(5.6))
        except Exception:
            pass

    for sec_title, items in sections:
        hp = doc.add_heading(level=1)
        hr = hp.add_run(sec_title); hr.font.color.rgb = RGBColor(0x1E, 0x24, 0x50)
        for it_title, paras in items:
            sp = doc.add_paragraph()
            sr = sp.add_run(it_title); sr.bold = True; sr.font.size = Pt(12)
            sr.font.color.rgb = RGBColor(0x3A, 0x44, 0x88)
            for p in paras:
                bp = doc.add_paragraph(p); bp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    buf = io.BytesIO(); doc.save(buf); return buf.getvalue()


def generate(chart, name, fmt, chart_png):
    """Punto de entrada. Devuelve (bytes, filename, mimetype)."""
    intro, sections = build_sections(chart)
    title = "Carta Natal"
    person = (name or '').strip()
    user_line = person if person else None
    png = _png_from_dataurl(chart_png)
    safe = "Reporte_Astral" + (("_" + person.replace(' ', '_')) if person else "")
    if fmt == 'docx':
        data = render_docx(title, intro, sections, png, user_line)
        return data, safe + '.docx', \
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    data = render_pdf(title, intro, sections, png, user_line)
    return data, safe + '.pdf', 'application/pdf'
