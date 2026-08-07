"""Prueba contra la red cada enlace de Financiamiento y de Comunidades.

Los portales de postulación y los sitios de las comunidades cambian de
dirección seguido, así que conviene correrlo cada tanto y arreglar lo que
aparezca como FALLO o REDIRIGE.

Uso: python -m scripts.validar_directorios
"""
import httpx

from app.comunidades import COMUNIDADES
from app.directorio import ruta_logo
from app.financiamiento import INSTITUCIONES

FICHAS = INSTITUCIONES + COMUNIDADES

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def main():
    with httpx.Client(follow_redirects=True, timeout=25,
                      headers={"User-Agent": UA}, verify=False) as cliente:
        for inst in FICHAS:
            logo = "con logo" if ruta_logo(inst["slug"]) else "SIN LOGO"
            try:
                r = cliente.get(inst["url"])
            except Exception as e:
                print(f"FALLO    {inst['nombre']}: {type(e).__name__} ({logo})")
                continue
            destino = str(r.url).rstrip("/")
            if r.status_code != 200:
                estado = f"HTTP {r.status_code}"
            elif destino != inst["url"].rstrip("/"):
                estado = f"REDIRIGE a {destino}"
            else:
                estado = "OK"
            print(f"{estado:<9} {inst['nombre']} ({logo})")


if __name__ == "__main__":
    main()
