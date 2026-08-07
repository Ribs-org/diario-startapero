"""Descarga a app/static/logos/ el logo de cada ficha de los directorios.

Cubre las dos secciones estáticas del diario: Financiamiento y Comunidades.

Prueba, en orden: el `logo_url` fijado a mano en la ficha, los íconos
declarados en el HTML del sitio (apple-touch-icon y los de mayor tamaño),
/favicon.ico y por último los servicios de favicons de Google y DuckDuckGo.
Los archivos quedan versionados en el repo: el sitio nunca le pide imágenes a
un tercero en tiempo de carga.

Cada logo se guarda como `<slug>.<extensión>`; la web resuelve la extensión
sola (ver `app.directorio.ruta_logo`). Las fichas marcadas con
`logo_manual` se saltan, porque su logotipo está puesto a mano en el repo. Si
no se consigue ninguna imagen, la tarjeta muestra el monograma y el sitio
igual funciona.

Uso: python -m scripts.descargar_logos
"""
import hashlib
import re
import struct
from urllib.parse import urljoin

import httpx

from app.comunidades import COMUNIDADES
from app.directorio import DIR_LOGOS
from app.financiamiento import INSTITUCIONES

FICHAS = INSTITUCIONES + COMUNIDADES

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
MINIMO_BYTES = 400        # descarta favicons placeholder de 1x1
MINIMO_BYTES_SVG = 150    # un SVG legítimo pesa mucho menos que un PNG
MINIMO_LADO = 64          # abajo de esto el logo se ve borroso en la ficha

# Muchos sitios en WordPress no configuran favicon y sirven el de la propia
# plataforma. Es una imagen válida, pero no es el logo de nadie. Van los dos
# que aparecen en la practica: el original del sitio y el que devuelven los
# servicios de favicons despues de reescalarlo.
FAVICONS_GENERICOS = {
    "000bf649cc8f6bf27cfb04d1bcdcd3c7",
    "6ff1009e1215a17f2ac9420bed6a164d",
}
EXTENSIONES = {
    "image/png": ".png", "image/x-icon": ".ico", "image/vnd.microsoft.icon": ".ico",
    "image/jpeg": ".jpg", "image/webp": ".webp", "image/svg+xml": ".svg",
    "image/gif": ".gif",
}
RE_LINK_ICON = re.compile(r'<link[^>]+rel="[^"]*icon[^"]*"[^>]*>', re.I)
RE_HREF = re.compile(r'href="([^"]+)"', re.I)
RE_SIZES = re.compile(r'sizes="(\d+)x\d+"', re.I)


def iconos_del_html(cliente, dominio):
    """Íconos declarados en el <head> del sitio, del más grande al más chico."""
    for base in (f"https://{dominio}/", f"https://www.{dominio}/"):
        try:
            r = cliente.get(base)
        except Exception:
            continue
        if r.status_code != 200:
            continue
        encontrados = []
        for etiqueta in RE_LINK_ICON.findall(r.text[:300_000]):
            href = RE_HREF.search(etiqueta)
            if not href:
                continue
            tamano = RE_SIZES.search(etiqueta)
            # apple-touch-icon suele ser de 180px aunque no declare `sizes`
            peso = int(tamano.group(1)) if tamano else (
                180 if "apple-touch" in etiqueta.lower() else 0)
            encontrados.append((peso, urljoin(str(r.url), href.group(1))))
        encontrados.sort(key=lambda par: par[0], reverse=True)
        return [url for _, url in encontrados]
    return []


def candidatos(cliente, inst):
    dominio = inst["dominio"]
    urls = []
    if inst.get("logo_url"):
        urls.append(inst["logo_url"])
    urls += iconos_del_html(cliente, dominio)
    urls += [
        f"https://{dominio}/favicon.ico",
        f"https://www.google.com/s2/favicons?domain={dominio}&sz=128",
        f"https://icons.duckduckgo.com/ip3/{dominio}.ico",
    ]
    return urls


def lado_menor(contenido):
    """Lado más corto de la imagen, o None si el formato no se puede medir.

    Solo mide PNG e ICO, que son la mayoría; SVG y WebP pasan derecho porque
    el SVG escala solo y el WebP siempre vino de un logo grande.
    """
    if contenido[:8] == b"\x89PNG\r\n\x1a\n":
        ancho, alto = struct.unpack(">II", contenido[16:24])
        return min(ancho, alto)
    if contenido[:4] == b"\x00\x00\x01\x00":  # ICO: 0 en la cabecera son 256px
        cuantos = struct.unpack("<H", contenido[4:6])[0]
        lados = [min(contenido[6 + i * 16] or 256, contenido[7 + i * 16] or 256)
                 for i in range(cuantos)]
        return max(lados) if lados else None
    return None


def extension_por_contenido(contenido):
    """Reconoce el formato por los bytes, para servidores sin content-type."""
    if contenido[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if contenido[:4] == b"\x00\x00\x01\x00":
        return ".ico"
    if contenido[:2] == b"\xff\xd8":
        return ".jpg"
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return ".webp"
    if contenido[:4] == b"GIF8":
        return ".gif"
    if b"<svg" in contenido[:300].lower():
        return ".svg"
    return None


def descargar(cliente, url, exigir_tamano=True):
    """Devuelve (bytes, extensión) si la respuesta es una imagen útil."""
    r = cliente.get(url)
    if r.status_code != 200:
        return None
    tipo = r.headers.get("content-type", "").split(";")[0].strip()
    # Hay servidores que no declaran content-type (o mandan octet-stream);
    # si los bytes son los de una imagen, vale igual.
    extension = EXTENSIONES.get(tipo) or extension_por_contenido(r.content)
    if extension is None:
        return None
    minimo = MINIMO_BYTES_SVG if extension == ".svg" else MINIMO_BYTES
    if len(r.content) < minimo:
        return None
    if hashlib.md5(r.content).hexdigest() in FAVICONS_GENERICOS:
        return None
    lado = lado_menor(r.content)
    if exigir_tamano and lado is not None and lado < MINIMO_LADO:
        return None
    return r.content, extension


def main():
    DIR_LOGOS.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=25,
                      headers={"User-Agent": UA}, verify=False) as cliente:
        for inst in FICHAS:
            if inst.get("logo_manual"):
                print(f"SALTO {inst['slug']}: logo puesto a mano en el repo")
                continue
            urls = candidatos(cliente, inst)
            # Primera vuelta exigiendo resolución decente; si ningún candidato
            # la cumple, segunda vuelta aceptando lo que haya antes de
            # resignarse al monograma.
            for exigir in (True, False):
                elegido = None
                for url in urls:
                    try:
                        elegido = descargar(cliente, url, exigir_tamano=exigir)
                    except Exception:
                        elegido = None
                    if elegido:
                        break
                if elegido:
                    contenido, extension = elegido
                    for viejo in DIR_LOGOS.glob(f"{inst['slug']}.*"):
                        viejo.unlink()
                    (DIR_LOGOS / f"{inst['slug']}{extension}").write_bytes(contenido)
                    aviso = "" if exigir else " (chico, no habia mejor)"
                    print(f"OK    {inst['slug']}{extension}: "
                          f"{len(contenido)} bytes{aviso} ({url})")
                    break
            else:
                print(f"FALLO {inst['slug']}: sin logo, usará el monograma")


if __name__ == "__main__":
    main()
