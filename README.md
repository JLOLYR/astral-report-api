# Diario Astral — Web API (Swiss Ephemeris)

API en **FastAPI** que calcula cartas astrológicas con **Swiss Ephemeris** (`pyswisseph`).
Pensada para desplegarse en **Render** y consumirse desde una web estática en **GitHub Pages**
(o cualquier frontend). Devuelve JSON con planetas, casas, ángulos, Luna Negra y aspectos —
el frontend dibuja la rueda y muestra las interpretaciones.

## Qué calcula

- Planetas Sol–Plutón (efemérides Moshier, sin archivos externos).
- Nodos lunares (medio) y **Luna Negra** (apogeo lunar medio, `MEAN_APOG`).
- **Quirón** (usa los archivos `ephe/seas_*.se1` incluidos en el repo).
- Casas **Placidus**, Ascendente y Medio Cielo.
- Parte de la Fortuna (fórmula diurna/nocturna).
- Aspectos mayores (conjunción, sextil, cuadratura, trígono, oposición).
- **Horario de verano correcto**: si mandás la zona como nombre IANA
  (`America/Santiago`), aplica el DST de la fecha de nacimiento.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | estado |
| POST | `/api/natal` | carta natal |
| POST | `/api/transits` | natal + tránsitos + aspectos al natal |
| GET | `/api/interpretations` | sirve `interpretations_es.json` si lo copiás junto al backend (opcional) |

### Ejemplo de petición

```bash
curl -X POST https://TU-SERVICIO.onrender.com/api/natal \
  -H "Content-Type: application/json" \
  -d '{"date":"1988-09-28","time":"04:20","lat":-38.7333,"lon":-72.6,"tz":"America/Santiago"}'
```

`lat`/`lon` en grados decimales (sur y oeste negativos). `tz` puede ser un nombre IANA
(recomendado, aplica DST) o un offset fijo `"-04:00"`.

## Probar localmente

```bash
pip install -r requirements.txt
uvicorn app:app --reload
# abrir http://127.0.0.1:8000/docs  (documentación interactiva)
```

## Desplegar en Render (nuevo Web Service)

1. Subí esta carpeta a un **repositorio de GitHub nuevo** (por ejemplo `diario-astral-web-api`).
   *(Si preferís reusar un repo existente, ponelo en una subcarpeta y en Render seteá
   «Root Directory» a esa subcarpeta.)*
2. En Render → **New +** → **Web Service** → conectá ese repo.
3. Configuración:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`
   - **Plan:** Free
   - (opcional) Variable de entorno `ALLOW_ORIGINS` = `https://TU-USUARIO.github.io`
     para restringir el CORS solo a tu página. Por defecto es `*` (cualquiera).
4. Deploy. Cuando quede **Live**, tu API estará en `https://TU-SERVICIO.onrender.com`.

> El `render.yaml` incluido permite también crear el servicio como *Blueprint* automáticamente.

**Nota (plan Free):** el servicio “se duerme” tras un rato de inactividad; la primera
petición puede tardar ~50 s en despertar. Es normal.

## Consumir desde GitHub Pages

```javascript
const API = "https://TU-SERVICIO.onrender.com";

async function carta(datos) {
  const r = await fetch(`${API}/api/natal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();  // { planets, houses, angles, aspects, ... }
}

carta({ date:"1988-09-28", time:"04:20", lat:-38.7333, lon:-72.6, tz:"America/Santiago" })
  .then(data => console.log(data));
```

Con ese JSON, el frontend puede dibujar la rueda (SVG) y buscar los textos en
`interpretations_es.json` (que podés servir desde la propia web o desde
`/api/interpretations`).

## Estructura

```
astral-web-api/
├── app.py             # API FastAPI (endpoints + CORS)
├── astro.py           # motor de cálculo (Swiss Ephemeris)
├── ephe/              # archivos de efemérides de Quirón (seas_*.se1)
├── requirements.txt
├── render.yaml        # blueprint opcional de Render
├── Procfile           # comando de arranque alternativo
├── runtime.txt        # versión de Python
└── README.md
```
