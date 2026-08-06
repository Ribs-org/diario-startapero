"""Descarga a app/static/logos/ el logo de cada institución de financiamiento.

Prueba, en orden: el `logo_url` fijado a mano en la institución, los íconos
declarados en el HTML del sitio (apple-touch-icon y los de mayor tamaño),
/favicon.ico y por último los servicios de favicons de Google y DuckDuckGo.
Los archivos quedan versionados en el repo: el sitio nunca le pide imágenes a
un tercero en tiempo de carga.

Cada logo se guarda como `<slug>.<extensión>`; la web resuelve la extensión
sola (ver `app.financiamiento.ruta_logo`). Las instituciones marcadas con
`logo_manual` se saltan, porque su logotipo está puesto a mano en el repo. Si
no se consigue ninguna imagen, la tarjeta muestra el monograma y el sitio
igual funciona.

Uso: python -m scripts.descargar_logos
"""
import re
from urllib.parse import urljoin

import httpx

from app.financiamiento import DIR_LOGOS, INSTITUCIONES

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
MINIMO_BYTES = 400        # descarta favicons placeholder de 1x1
MINIMO_BYTES_SVG = 150    # un SVG legítimo pesa mucho menos que un PNG
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


def descargar(cliente, url):
    """Devuelve (bytes, extensión) si la respuesta es una imagen útil."""
    r = cliente.get(url)
    tipo = r.headers.get("content-type", "").split(";")[0].strip()
    if r.status_code != 200 or tipo not in EXTENSIONES:
        return None
    minimo = MINIMO_BYTES_SVG if tipo == "image/svg+xml" else MINIMO_BYTES
    if len(r.content) < minimo:
        return None
    return r.content, EXTENSIONES[tipo]


def main():
    DIR_LOGOS.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=25,
                      headers={"User-Agent": UA}, verify=False) as cliente:
        for inst in INSTITUCIONES:
            if inst.get("logo_manual"):
                print(f"SALTO {inst['slug']}: logo puesto a mano en el repo")
                continue
            for url in candidatos(cliente, inst):
                try:
                    resultado = descargar(cliente, url)
                except Exception:
                    resultado = None
                if resultado:
                    contenido, extension = resultado
                    for viejo in DIR_LOGOS.glob(f"{inst['slug']}.*"):
                        viejo.unlink()
                    (DIR_LOGOS / f"{inst['slug']}{extension}").write_bytes(contenido)
                    print(f"OK    {inst['slug']}{extension}: "
                          f"{len(contenido)} bytes ({url})")
                    break
            else:
                print(f"FALLO {inst['slug']}: sin logo, usará el monograma")


if __name__ == "__main__":
    main()
