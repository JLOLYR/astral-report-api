# Guía paso a paso — Subir la API a GitHub y Render

Esta guía es para publicar la carpeta **`astral-web-api`** como un servicio web nuevo
en Render (aparte del que ya tenés), usando un repositorio de GitHub.

Carpeta a subir:
`E:\JLO\Cosass\Apps\ReporteAstral_Master_App\astral-web-api`

Archivos que DEBEN quedar en el repo (11 en total):

```
app.py
astro.py
requirements.txt
render.yaml
Procfile
runtime.txt
README.md
.gitignore
ephe/seas_12.se1      ← archivos de Quirón (NO borrar)
ephe/seas_18.se1
ephe/seas_24.se1
```

> ⚠️ La carpeta `ephe/` con los 3 archivos `.se1` es obligatoria para que Quirón
> se calcule. Asegurate de que se suban.

---

## PARTE 1 — Subir a GitHub

Tenés dos caminos. El **A (por la web)** es el más simple y no requiere instalar nada.

### Camino A — Por la página de GitHub (recomendado)

1. Entrá a **https://github.com/new** (logueada con tu cuenta `JLOLYR`).
2. En **Repository name** escribí: `diario-astral-web-api`
3. Elegí **Public** (o Private, las dos funcionan con Render).
4. **NO** marques “Add a README file” (ya tenemos uno).
5. Click en **Create repository**.
6. En la página del repo vacío, buscá el link **“uploading an existing file”**
   (o entrá a `https://github.com/JLOLYR/diario-astral-web-api/upload/main`).
7. Abrí el Explorador de Windows en la carpeta `astral-web-api`, **seleccioná
   todos los archivos y la carpeta `ephe`**, y **arrastralos** a la zona de GitHub
   que dice “Drag files here”.
   - GitHub sube también las carpetas: se va a ver `ephe/` con los 3 `.se1`.
8. Abajo, en **Commit changes**, escribí un mensaje (ej: `Backend Diario Astral Web API`).
9. Click **Commit changes**.
10. Verificá que en el repo aparezcan los 11 archivos, incluida la carpeta
    `ephe/` con `seas_12.se1`, `seas_18.se1`, `seas_24.se1`.

Listo, tu código ya está en GitHub.

### Camino B — Por línea de comandos (si tenés Git instalado)

Abrí una terminal (PowerShell o CMD) y ejecutá:

```bash
cd "E:\JLO\Cosass\Apps\ReporteAstral_Master_App\astral-web-api"
git init
git add .
git commit -m "Backend Diario Astral Web API (Swiss Ephemeris)"
git branch -M main
git remote add origin https://github.com/JLOLYR/diario-astral-web-api.git
git push -u origin main
```

- Si no tenés Git: instalalo desde https://git-scm.com/download/win
- La primera vez te va a pedir loguearte en GitHub (se abre el navegador).
- Antes del `git remote add`, creá el repo vacío en https://github.com/new
  (nombre `diario-astral-web-api`, sin README).

---

## PARTE 2 — Desplegar en Render

1. Entrá a **https://dashboard.render.com** (con tu cuenta).
2. Arriba a la derecha: **New +** → **Web Service**.
3. En **Source Code**, elegí **Build and deploy from a Git repository** → **Next**.
4. Buscá y seleccioná el repo **`diario-astral-web-api`** → **Connect**.
   - Si no aparece, click en **“Configure account”** / **“Edit permissions”** en
     GitHub para darle acceso de Render a ese repositorio nuevo, y volvé.
5. Completá la configuración:

   | Campo | Valor |
   |-------|-------|
   | **Name** | `diario-astral-web-api` |
   | **Region** | la más cercana (ej: Oregon) |
   | **Branch** | `main` |
   | **Root Directory** | *(dejar vacío)* |
   | **Runtime / Language** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
   | **Instance Type** | `Free` |

6. Click en **Advanced** y agregá:
   - **Health Check Path**: `/health`
   - *(opcional)* **Environment Variable**: `ALLOW_ORIGINS` con el valor de tu
     página, ej. `https://jlolyr.github.io` (para que solo tu web pueda usar la API).
     Si lo dejás sin poner, cualquiera puede llamarla (valor por defecto `*`).
7. Click en **Create Web Service**.
8. Render empieza a construir (tarda 2–5 min). Cuando el estado sea **Live**,
   tu API estará en una URL tipo:
   `https://diario-astral-web-api.onrender.com`

> Alternativa automática: como el repo incluye `render.yaml`, también podés usar
> **New + → Blueprint**, elegir el repo y Render lee la configuración solo.

---

## PARTE 3 — Verificar que funciona

Abrí en el navegador (reemplazá por tu URL real):

- `https://diario-astral-web-api.onrender.com/health` → debe mostrar `{"status":"ok"}`
- `https://diario-astral-web-api.onrender.com/docs` → documentación interactiva.
  Ahí podés probar `POST /api/natal` con el botón **“Try it out”** y este ejemplo:

```json
{
  "date": "1988-09-28",
  "time": "04:20",
  "lat": -38.7333,
  "lon": -72.6,
  "tz": "America/Santiago"
}
```

Debe devolver 15 cuerpos (incluido Quirón), casas, ángulos y aspectos.

> **Plan Free:** el servicio “se duerme” tras ~15 min sin uso. La primera petición
> después de dormir puede tardar ~50 segundos en responder (después va rápido).

---

## PARTE 4 — Actualizar la API a futuro

Cada vez que cambies el código:

- **Camino A (web):** subí los archivos nuevos al repo (el botón *Add file → Upload files*),
  o editá directamente en GitHub. Render redepliega solo.
- **Camino B (git):**
  ```bash
  git add .
  git commit -m "cambios"
  git push
  ```
  Render detecta el push y redepliega automáticamente.

---

## Problemas comunes

- **Quirón no aparece / error de archivo:** faltan los `ephe/seas_*.se1` en el repo.
  Verificá que la carpeta `ephe/` esté subida con sus 3 archivos.
- **El frontend no puede llamar la API (error CORS):** poné en `ALLOW_ORIGINS`
  la URL exacta de tu GitHub Pages, o dejá `*` mientras probás.
- **Build falla:** revisá que `requirements.txt` esté en la raíz del repo y que el
  **Root Directory** esté vacío (o apunte a la carpeta correcta si usaste subcarpeta).
- **Tarda mucho la primera vez:** es el “despertar” del plan Free, es normal.
```
