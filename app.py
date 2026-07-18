# -*- coding: utf-8 -*-
"""
app.py — API FastAPI del Diario Astral (motor Swiss Ephemeris).

Endpoints:
  GET  /                → info y estado
  GET  /health         → {"status": "ok"}
  POST /api/natal      → carta natal (planetas, casas, aspectos, Lilith)
  POST /api/transits   → carta natal + tránsitos + aspectos tránsito→natal
  GET  /api/interpretations → (opcional) sirve interpretations_es.json si está

Pensado para desplegarse en Render y consumirse desde una web en GitHub Pages.
CORS habilitado (configurable con la variable de entorno ALLOW_ORIGINS).
"""
import os
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional

import astro
import report

app = FastAPI(title="Reporte Astral API", version="1.1.0",
              description="Cálculo de cartas astrológicas con Swiss Ephemeris.")

# ── CORS ────────────────────────────────────────────────────────────────
# Por defecto permite cualquier origen (GitHub Pages). Podés restringirlo
# con ALLOW_ORIGINS="https://usuario.github.io,https://midominio.com"
_origins_env = os.environ.get("ALLOW_ORIGINS", "*").strip()
_origins = ["*"] if _origins_env == "*" else [o.strip() for o in _origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modelos de entrada ──────────────────────────────────────────────────
class BirthData(BaseModel):
    date: str = Field(..., examples=["1988-09-28"], description="AAAA-MM-DD")
    time: str = Field("12:00", examples=["04:20"], description="HH:MM (24h)")
    lat: float = Field(..., examples=[-38.7333], description="Latitud decimal (sur negativo)")
    lon: float = Field(..., examples=[-72.6], description="Longitud decimal (oeste negativo)")
    tz: str = Field("", examples=["America/Santiago"],
                    description="Zona horaria IANA (con horario de verano) u offset fijo '-04:00'")
    hsys: str = Field("P", description="Sistema de casas (P=Placidus)")


class TransitRequest(BaseModel):
    natal: BirthData
    transit: BirthData


class ReportRequest(BirthData):
    name: str = Field("", description="Nombre de la persona (opcional)")
    format: str = Field("pdf", description="pdf | docx")
    chart_png: Optional[str] = Field(None, description="Imagen de la rueda (data URL base64)")
    city: str = Field("", description="Ciudad y país de nacimiento (texto libre)")
    astrologer: str = Field("", description="Nombre del astrólogo (opcional)")


# ── Rutas ───────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "service": "Diario Astral API",
        "engine": "Swiss Ephemeris (pyswisseph)",
        "endpoints": ["/health", "POST /api/natal", "POST /api/transits",
                      "/api/interpretations"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/natal")
def natal(data: BirthData):
    try:
        return astro.compute_chart(data.date, data.time, data.lat, data.lon,
                                   data.tz, data.hsys)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo calcular: {e}")


@app.post("/api/transits")
def transits(req: TransitRequest):
    try:
        n = req.natal
        t = req.transit
        return astro.compute_transits(
            {"date": n.date, "time": n.time, "lat": n.lat, "lon": n.lon,
             "tz": n.tz, "hsys": n.hsys},
            {"date": t.date, "time": t.time, "lat": t.lat, "lon": t.lon,
             "tz": t.tz, "hsys": t.hsys},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo calcular: {e}")


@app.post("/api/report")
def make_report(req: ReportRequest):
    """Genera el reporte natal interpretativo y lo devuelve como archivo
    descargable (PDF o DOCX). La web envía la imagen de la rueda en chart_png."""
    try:
        chart = astro.compute_chart(req.date, req.time, req.lat, req.lon,
                                    req.tz, req.hsys)
        fmt = (req.format or "pdf").lower()
        data, filename, mime = report.generate(chart, req.name, fmt, req.chart_png,
                                               city=req.city,
                                               astrologer=req.astrologer)
        return Response(content=data, media_type=mime, headers={
            "Content-Disposition": 'attachment; filename="%s"' % filename})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo generar el reporte: {e}")


@app.get("/api/interpretations")
def interpretations():
    """Sirve interpretations_es.json si está junto al backend (opcional).
    Así el frontend puede pedir los textos al mismo origen."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "interpretations_es.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404,
                            detail="interpretations_es.json no incluido en el backend.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
