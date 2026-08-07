"""Validación de las altas al newsletter."""
import re

MAX_NOMBRE = 80
MAX_EMAIL = 254
ORIGENES = {"modal", "pagina"}

# Deliberadamente laxa: solo descarta lo que claramente no es un correo. Validar
# RFC 5322 completo acá no aporta nada — quien se equivoca de dirección igual
# escribe algo con forma de email.
EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")

MENSAJE_NOMBRE = f"Escribí tu nombre (hasta {MAX_NOMBRE} caracteres)."
MENSAJE_EMAIL = "Ese correo no parece válido. Revisalo y probá de nuevo."


class DatosInvalidos(ValueError):
    """El formulario llegó con datos que no se pueden guardar."""


def limpiar(nombre, email):
    """Devuelve (nombre, email) normalizados o levanta DatosInvalidos."""
    nombre = nombre.strip()
    email = email.strip().lower()
    if not 1 <= len(nombre) <= MAX_NOMBRE:
        raise DatosInvalidos(MENSAJE_NOMBRE)
    if len(email) > MAX_EMAIL or not EMAIL.match(email):
        raise DatosInvalidos(MENSAJE_EMAIL)
    return nombre, email


def normalizar_origen(origen):
    return origen if origen in ORIGENES else "pagina"
