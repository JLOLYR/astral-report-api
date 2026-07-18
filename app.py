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


class Reloc(BaseModel):
    lat: float
    lon: float
    tz: str = ""


class TransitRequest(BaseModel):
    natal: BirthData
    transit: BirthData


class SolarReturnRequest(BaseModel):
    natal: BirthData
    year: int
    reloc: Optional[Reloc] = None


class ProgressedRequest(BaseModel):
    natal: BirthData
    target_date: str = Field(..., examples=["2026-01-01"], description="Fecha objetivo AAAA-MM-DD")


class CombinedRequest(BaseModel):
    person_a: BirthData
    person_b: BirthData


class ReportRequest(BaseModel):
    chart_type: str = Field("natal",
        description="natal | transit | solar_return | progressed | combined")
    format: str = Field("pdf", description="pdf | docx")
    chart_png: Optional[str] = Field(None, description="Imagen de la rueda (data URL base64)")
    name: str = Field("", description="Nombre de la persona (opcional)")
    city: str = Field("", description="Ciudad y país de nacimiento (texto libre)")
    astrologer: str = Field("", description="Nombre del astrólogo (opcional)")
    # Cargas útiles según el tipo (todas opcionales)
    natal: Optional[BirthData] = None
    transit: Optional[BirthData] = None
    year: Optional[int] = None
    reloc: Optional[Reloc] = None
    target_date: Optional[str] = None
    person_a: Optional[BirthData] = None
    person_b: Optional[BirthData] = None


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


def _bd(b):
    return {"date": b.date, "time": b.time, "lat": b.lat, "lon": b.lon,
            "tz": b.tz, "hsys": b.hsys}


@app.post("/api/solar_return")
def solar_return(req: SolarReturnRequest):
    try:
        reloc = None
        if req.reloc:
            reloc = {"lat": req.reloc.lat, "lon": req.reloc.lon, "tz": req.reloc.tz}
        return astro.compute_solar_return(_bd(req.natal), req.year, reloc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo calcular: {e}")


@app.post("/api/progressed")
def progressed(req: ProgressedRequest):
    try:
        return astro.compute_progressed(_bd(req.natal), req.target_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo calcular: {e}")


@app.post("/api/combined")
def combined(req: CombinedRequest):
    try:
        return astro.compute_combined(_bd(req.person_a), _bd(req.person_b))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo calcular: {e}")


@app.post("/api/report")
def make_report(req: ReportRequest):
    """Genera el reporte interpretativo (natal, tránsitos, retorno solar,
    progresada o combinada) y lo devuelve como archivo descargable (PDF o DOCX).
    La web envía la imagen de la rueda ya compuesta en chart_png."""
    try:
        ct = (req.chart_type or "natal").lower()
        if ct == "natal":
            if not req.natal:
                raise ValueError("Faltan los datos natales.")
            data = astro.compute_chart(**_bd(req.natal))
        elif ct == "transit":
            if not (req.natal and req.transit):
                raise ValueError("Faltan datos natales o de tránsito.")
            data = astro.compute_transits(_bd(req.natal), _bd(req.transit))
        elif ct == "solar_return":
            if not req.natal or req.year is None:
                raise ValueError("Faltan datos natales o el año del retorno.")
            reloc = None
            if req.reloc:
                reloc = {"lat": req.reloc.lat, "lon": req.reloc.lon, "tz": req.reloc.tz}
            data = astro.compute_solar_return(_bd(req.natal), req.year, reloc)
        elif ct == "progressed":
            if not (req.natal and req.target_date):
                raise ValueError("Faltan datos natales o la fecha objetivo.")
            data = astro.compute_progressed(_bd(req.natal), req.target_date)
        elif ct == "combined":
            if not (req.person_a and req.person_b):
                raise ValueError("Faltan los datos de una de las personas.")
            data = astro.compute_combined(_bd(req.person_a), _bd(req.person_b))
        else:
            raise ValueError("Tipo de carta no reconocido: %s" % ct)

        fmt = (req.format or "pdf").lower()
        out, filename, mime = report.generate(
            data, req.name, fmt, req.chart_png,
            city=req.city, astrologer=req.astrologer, chart_type=ct)
        return Response(content=out, media_type=mime, headers={
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
