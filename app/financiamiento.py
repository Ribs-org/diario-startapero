"""Directorio curado de fondos, aceleradoras y programas de financiamiento.

Datos estáticos: no dependen del scraper ni de la base de datos. Cada entrada
apunta al portal de postulación cuando existe uno público, y si no, al sitio
oficial de la institución.

Al agregar una institución: elegir un `slug` único, dejar `dominio` sin `www.`
y correr `python -m scripts.descargar_logos` para bajar el logo nuevo. Si el
sitio no publica un ícono decente, fijar `logo_url` a mano.
"""
from app.directorio import por_categoria as _por_categoria

INSTITUCIONES = [
    # --- Chile ---------------------------------------------------------
    {
        "slug": "platanus",
        "nombre": "Platanus Ventures",
        "dominio": "platan.us",
        "url": "https://platan.us/apply",
        "categoria": "chile",
        "tipo": "Aceleradora",
        "detalle": "Pre-seed",
        "descripcion": "Invierte US$200.000 por 7% y acelera durante tres meses "
                       "a fundadores técnicos de habla hispana.",
        "monograma": "PV",
    },
    {
        "slug": "corfo",
        "nombre": "Corfo",
        "dominio": "corfo.gob.cl",
        "url": "https://www.corfo.gob.cl/sites/cpp/programasyconvocatorias",
        "categoria": "chile",
        "tipo": "Fondo público",
        "detalle": "Idea a escalamiento",
        "descripcion": "Subsidios no reembolsables y convocatorias permanentes: "
                       "Semilla Inicia, Semilla Expande y escalamiento.",
        "monograma": "CO",
    },
    {
        "slug": "startup-chile",
        "nombre": "Start-Up Chile",
        "dominio": "startupchile.org",
        "url": "https://startupchile.org/en/apply/",
        "categoria": "chile",
        "tipo": "Aceleradora pública",
        "detalle": "Pre-seed / Seed",
        "descripcion": "Aceleradora de Corfo con capital sin dilución y visa de "
                       "trabajo para equipos que se instalan en Chile.",
        "monograma": "SC",
    },
    {
        "slug": "chile-global-ventures",
        "nombre": "Chile Global Ventures",
        "dominio": "chileglobalventures.cl",
        "url": "https://chileglobalventures.cl/",
        # su favicon.ico viene vacío; usamos el logo del encabezado
        "logo_url": "https://chileglobalventures.cl/wp-content/uploads/2025/03/"
                    "Logo-CGV-Hor-Color-1.webp",
        "categoria": "chile",
        "tipo": "Venture Capital",
        "detalle": "Seed / Serie A",
        "descripcion": "El brazo de venture capital de Fundación Chile, con "
                       "varios fondos activos en el ecosistema local.",
        "monograma": "CG",
    },
    {
        "slug": "magma-partners",
        "nombre": "Magma Partners",
        "dominio": "magmapartners.com",
        "url": "https://magmapartners.com/",
        "categoria": "chile",
        "tipo": "Venture Capital",
        "detalle": "Pre-seed / Seed",
        "descripcion": "Uno de los fondos más activos de Chile, con foco en "
                       "fintech e insurtech y puente hacia Estados Unidos.",
        "monograma": "MP",
    },
    {
        "slug": "fen-ventures",
        "nombre": "Fen Ventures",
        "dominio": "fenventures.com",
        "url": "https://fenventures.com/",
        "categoria": "chile",
        "tipo": "Venture Capital",
        "detalle": "Pre-seed / Seed",
        "descripcion": "Fondo chileno de etapa temprana que invierte en "
                       "software y marketplaces de toda la región.",
        "monograma": "FV",
    },
    {
        "slug": "manutara-ventures",
        "nombre": "Manutara Ventures",
        "dominio": "manutaraventures.com",
        "url": "https://manutaraventures.com/",
        "categoria": "chile",
        "tipo": "Venture Capital",
        "detalle": "Seed",
        "descripcion": "Invierte en startups latinoamericanas con vocación "
                       "global y las acompaña en su salto a nuevos mercados.",
        "monograma": "MV",
    },
    {
        "slug": "impacta-vc",
        "nombre": "Impacta VC",
        "dominio": "impacta.vc",
        "url": "https://www.impacta.vc/",
        "categoria": "chile",
        "tipo": "Venture Capital de impacto",
        "detalle": "Seed / Serie A",
        "descripcion": "Financia startups de impacto en América Latina que "
                       "miden resultados sociales y ambientales.",
        "monograma": "IV",
    },
    # --- Internacional -------------------------------------------------
    {
        "slug": "y-combinator",
        "nombre": "Y Combinator",
        "dominio": "ycombinator.com",
        "url": "https://www.ycombinator.com/apply",
        "categoria": "internacional",
        "tipo": "Aceleradora",
        "detalle": "Pre-seed",
        "descripcion": "La aceleradora de referencia en Silicon Valley: dos "
                       "batches al año y postulación abierta a cualquiera.",
        "monograma": "YC",
    },
    {
        "slug": "techstars",
        "nombre": "Techstars",
        "dominio": "techstars.com",
        "url": "https://apply.techstars.com/",
        # el favicon de techstars.com es un placeholder de 111 bytes
        "logo_url": "https://apply.techstars.com/favicon.svg",
        "categoria": "internacional",
        "tipo": "Aceleradora",
        "detalle": "Pre-seed / Seed",
        "descripcion": "Red global de programas de tres meses por ciudad y por "
                       "industria, con inversión y mentoría.",
        "monograma": "TS",
    },
    {
        "slug": "500-global",
        "nombre": "500 Global",
        "dominio": "500.co",
        "url": "https://500.co/founders",
        "categoria": "internacional",
        "tipo": "Aceleradora / VC",
        "detalle": "Pre-seed / Seed",
        "descripcion": "Programas para fundadores en varios continentes y una "
                       "de las carteras más amplias de mercados emergentes.",
        "monograma": "500",
    },
    {
        "slug": "antler",
        "nombre": "Antler",
        "dominio": "antler.co",
        "url": "https://www.antler.co/pitch",
        "categoria": "internacional",
        "tipo": "Venture Capital día cero",
        "detalle": "Pre-seed",
        "descripcion": "Invierte desde el día cero, incluso antes de que exista "
                       "equipo fundador o producto.",
        "monograma": "AN",
    },
    {
        "slug": "a16z-speedrun",
        "nombre": "a16z Speedrun",
        "dominio": "a16z.com",
        "url": "https://speedrun.a16z.com/",
        "categoria": "internacional",
        "tipo": "Programa de VC",
        "detalle": "Pre-seed / Seed",
        "descripcion": "El programa de etapa temprana de Andreessen Horowitz "
                       "para startups de tecnología, juegos e inteligencia artificial.",
        "monograma": "A16",
    },
    {
        "slug": "sequoia-arc",
        "nombre": "Sequoia Arc",
        "dominio": "sequoiacap.com",
        "url": "https://www.sequoiacap.com/arc/",
        "categoria": "internacional",
        "tipo": "Programa de VC",
        "detalle": "Pre-seed / Seed",
        "descripcion": "El programa de arranque de Sequoia Capital para "
                       "fundadores en la primera etapa de su empresa.",
        "monograma": "SQ",
    },
    {
        "slug": "kaszek",
        "nombre": "Kaszek",
        "dominio": "kaszek.com",
        "url": "https://kaszek.com/",
        # su favicon es el de WordPress por defecto: el logotipo está puesto a
        # mano en static/logos/kaszek.svg y descargar_logos no lo toca
        "logo_manual": True,
        "categoria": "internacional",
        "tipo": "Venture Capital",
        "detalle": "Seed a Serie C",
        "descripcion": "El fondo más grande de América Latina, detrás de varios "
                       "de los unicornios de la región.",
        "monograma": "KA",
    },
    {
        "slug": "monashees",
        "nombre": "monashees",
        "dominio": "monashees.com",
        "url": "https://www.monashees.com/",
        "categoria": "internacional",
        "tipo": "Venture Capital",
        "detalle": "Seed / Serie A",
        "descripcion": "Fondo brasileño de etapa temprana con inversiones en "
                       "toda América Latina.",
        "monograma": "MO",
    },
]


def por_categoria(categoria):
    return _por_categoria(INSTITUCIONES, categoria)
