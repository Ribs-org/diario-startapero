"""Web de Copper Valley Diario: solo lee de SQLite."""
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import db

BASE = Path(__file__).parent
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
