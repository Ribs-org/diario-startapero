"""Web de Copper Valley Diario: solo lee de SQLite."""
import mimetypes
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import db
from app import comunidades, financiamiento

BASE = Path(__file__).parent

# El runtime de Vercel no trae el mapeo de .webp y sirve esos logos como
# application/octet-stream; hoy el navegador los adivina, pero se romperian
# el dia que la respuesta lleve X-Content-Type-Options: nosniff.
mimetypes.add_type("image/webp", ".webp")

app = FastAPI(title="Copper Valley Diario")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_hoy():
    hoy = date.today()
    return f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"


def get_db():
    conn = db.get_connection()
    try:
        yield conn
    finally:
        conn.close()


@app.get("/favicon.ico")
def favicon():
    """Las páginas declaran el favicon, pero varios bots lo piden en la raíz."""
    return FileResponse(BASE / "static" / "favicon.png", media_type="image/png")


@app.get("/")
def portada(request: Request, conn=Depends(get_db)):
    return templates.TemplateResponse(request, "home.html", {
        "chile": db.list_articles(conn, "chile", limit=10),
        "mundo": db.list_articles(conn, "mundo", limit=10),
        "fecha_hoy": fecha_hoy(),
    })


@app.get("/chile")
def seccion_chile(request: Request, conn=Depends(get_db)):
    return templates.TemplateResponse(request, "section.html", {
        "titulo_seccion": "Startups Chile",
        "articulos": db.list_articles(conn, "chile", limit=30),
    })


@app.get("/mundo")
def seccion_mundo(request: Request, conn=Depends(get_db)):
    return templates.TemplateResponse(request, "section.html", {
        "titulo_seccion": "Startups Mundo",
        "articulos": db.list_articles(conn, "mundo", limit=30),
    })


@app.get("/financiamiento")
def seccion_financiamiento(request: Request):
    """Directorio estático: no toca la base de datos."""
    return templates.TemplateResponse(request, "financiamiento.html", {
        "chile": financiamiento.por_categoria("chile"),
        "internacional": financiamiento.por_categoria("internacional"),
    })


@app.get("/comunidades")
def seccion_comunidades(request: Request):
    """Directorio estático: no toca la base de datos."""
    return templates.TemplateResponse(request, "comunidades.html", {
        "universitarias": comunidades.por_categoria("universitaria"),
        "redes": comunidades.por_categoria("red"),
        "encuentros": comunidades.por_categoria("encuentro"),
    })
