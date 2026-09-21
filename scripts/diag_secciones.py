"""Diagnóstico temporal: conteos por sección y fuente en la BD activa."""
import db

conn = db.get_connection()
print("Por sección:", conn.execute(
    "SELECT seccion, COUNT(1) FROM articles GROUP BY seccion", ()).fetchall())
print("Por fuente:", conn.execute(
    "SELECT fuente, seccion, COUNT(1) FROM articles GROUP BY fuente, seccion "
    "ORDER BY fuente", ()).fetchall())
print("Últimas 5:", conn.execute(
    "SELECT fecha_publicacion, seccion, fuente, titulo FROM articles "
    "ORDER BY id DESC LIMIT 5", ()).fetchall())
