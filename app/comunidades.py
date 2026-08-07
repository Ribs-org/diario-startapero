"""Directorio curado de comunidades de emprendimiento del Copper Valley.

Mismo formato y mismas reglas que `app.financiamiento`: datos estáticos, logo
descargado al repo con `python -m scripts.descargar_logos` y enlace al sitio
oficial de la comunidad.

Acá entran comunidades, redes y gremios donde un emprendedor se junta con
otros. Los fondos y las convocatorias van en `app.financiamiento`.

Quedó fuera iTera (la incubadora de Ingeniería UC): su sitio se cayó y no
publica ningún logotipo utilizable. Vale la pena reintentarlo más adelante.
"""
from app.directorio import por_categoria as _por_categoria

COMUNIDADES = [
    # --- Universitarias -------------------------------------------------
    {
        "slug": "jump-chile",
        "nombre": "Jump Chile",
        "dominio": "jumpchile.com",
        "url": "https://jumpchile.com/",
        # su favicon es de 32px; el logotipo bueno venia embebido en un SVG
        # del tema y quedo extraido a mano en static/logos/jump-chile.png
        "logo_manual": True,
        "categoria": "universitaria",
        "tipo": "Comunidad universitaria",
        "detalle": "UC · Nacional",
        "descripcion": "El programa de emprendimiento universitario más grande "
                       "del país: postulan equipos de todas las universidades.",
        "monograma": "JC",
    },
    {
        "slug": "brain-chile",
        "nombre": "Brain Chile",
        "dominio": "brainchile.cl",
        "url": "https://brainchile.cl/",
        "categoria": "universitaria",
        "tipo": "Concurso y comunidad",
        "detalle": "Base científico-tecnológica",
        "descripcion": "Concurso del Centro de Innovación UC y El Mercurio para "
                       "emprendimientos que nacen de la ciencia y la tecnología.",
        "monograma": "BC",
    },
    {
        "slug": "centro-innovacion-uc",
        "nombre": "Centro de Innovación UC",
        "dominio": "centrodeinnovacion.uc.cl",
        "url": "https://centrodeinnovacion.uc.cl/",
        "categoria": "universitaria",
        "tipo": "Centro de innovación",
        "detalle": "UC · Anacleto Angelini",
        "descripcion": "Punto de encuentro entre la universidad, las empresas y "
                       "los emprendedores, con programas abiertos todo el año.",
        "monograma": "CI",
    },
    {
        "slug": "openbeauchef",
        "nombre": "OpenBeauchef",
        "dominio": "openbeauchef.cl",
        "url": "https://openbeauchef.cl/",
        "categoria": "universitaria",
        "tipo": "Comunidad universitaria",
        "detalle": "FCFM · U. de Chile",
        "descripcion": "La comunidad de innovación y emprendimiento de Beauchef, "
                       "en la Facultad de Ingeniería de la U. de Chile.",
        "monograma": "OB",
    },
    {
        "slug": "3ie-usm",
        "nombre": "3IE",
        "dominio": "3ie.usm.cl",
        "url": "https://3ie.usm.cl/",
        "categoria": "universitaria",
        "tipo": "Incubadora universitaria",
        "detalle": "USM · Valparaíso",
        "descripcion": "El instituto de innovación empresarial de la Santa María, "
                       "uno de los polos de emprendimiento de la Quinta Región.",
        "monograma": "3IE",
    },
    # --- Redes y gremios ------------------------------------------------
    {
        "slug": "asech",
        "nombre": "Asech",
        "dominio": "asech.cl",
        "url": "https://asech.cl/",
        "categoria": "red",
        "tipo": "Gremio de emprendedores",
        "detalle": "Nacional",
        "descripcion": "La Asociación de Emprendedores de Chile: gremio, red de "
                       "beneficios y voz del sector frente a la política pública.",
        "monograma": "AS",
    },
    {
        "slug": "endeavor-chile",
        "nombre": "Endeavor Chile",
        "dominio": "endeavor.cl",
        "url": "https://endeavor.cl/",
        "categoria": "red",
        "tipo": "Red de founders",
        "detalle": "Scaleups",
        "descripcion": "Selecciona emprendedores de alto impacto y los conecta "
                       "con mentores y con la red global de Endeavor.",
        "monograma": "EN",
    },
    {
        "slug": "fintechile",
        "nombre": "FinteChile",
        "dominio": "fintechile.org",
        "url": "https://fintechile.org/",
        "categoria": "red",
        "tipo": "Gremio sectorial",
        "detalle": "Fintech",
        "descripcion": "El gremio de las fintech chilenas, muy activo en la "
                       "discusión regulatoria del sector.",
        "monograma": "FC",
    },
    {
        "slug": "chiletec",
        "nombre": "Chiletec",
        "dominio": "chiletec.org",
        "url": "https://chiletec.org/",
        "categoria": "red",
        "tipo": "Gremio sectorial",
        "detalle": "Tecnología y software",
        "descripcion": "Reúne a las empresas de tecnología del país y tiene un "
                       "brazo dedicado al emprendimiento.",
        "monograma": "CT",
    },
    {
        "slug": "sofofa-hub",
        "nombre": "SOFOFA Hub",
        "dominio": "sofofahub.cl",
        "url": "https://sofofahub.cl/",
        "categoria": "red",
        "tipo": "Hub de innovación",
        "detalle": "Industria · Corporate",
        "descripcion": "Conecta startups con la industria: el puente de la Sofofa "
                       "entre grandes empresas y emprendedores.",
        "monograma": "SH",
    },
    {
        "slug": "socialab",
        "nombre": "Socialab",
        "dominio": "socialab.com",
        "url": "https://socialab.com/",
        "categoria": "red",
        "tipo": "Comunidad de impacto",
        "detalle": "Triple impacto",
        "descripcion": "Comunidad y desafíos abiertos para emprendimientos que "
                       "resuelven problemas sociales y ambientales.",
        "monograma": "SL",
    },
    {
        "slug": "startup-grind-santiago",
        "nombre": "Startup Grind Santiago",
        "dominio": "startupgrind.com",
        "url": "https://www.startupgrind.com/santiago/",
        "categoria": "red",
        "tipo": "Comunidad de eventos",
        "detalle": "Santiago",
        "descripcion": "El capítulo santiaguino de la red global: charlas y "
                       "encuentros periódicos entre fundadores.",
        "monograma": "SG",
    },
    {
        "slug": "mujeres-empresarias",
        "nombre": "Mujeres Empresarias",
        "dominio": "me.cl",
        "url": "https://me.cl/",
        "categoria": "red",
        "tipo": "Red de mujeres",
        "detalle": "Nacional",
        "descripcion": "La red más grande de mujeres que emprenden y lideran "
                       "empresas en Chile, con programas y encuentros propios.",
        "monograma": "ME",
    },
]


def por_categoria(categoria):
    return _por_categoria(COMUNIDADES, categoria)
