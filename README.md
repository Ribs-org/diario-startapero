# Copper Valley Diario

Diario web de noticias de startups y emprendimiento, con dos secciones:
**Startups Chile** y **Startups Mundo**. Un scraper diario lee fuentes RSS,
filtra y clasifica cada noticia con Claude y publica un titular y resumen
propios que citan y enlazan la fuente original.

## Cómo correr

```powershell
# 1. Instalar
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. Scraper (requiere ANTHROPIC_API_KEY en el entorno)
.venv\Scripts\python.exe -m scraper.run

# 3. Web
.venv\Scripts\uvicorn.exe app.main:app --port 8000
```

## Agendar la corrida diaria

La corrida diaria todavía no está agendada. Para agendarla a las 7:00 AM con
el Programador de tareas de Windows, guardar la API key como variable de
usuario persistente y crear la tarea:

```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $env:ANTHROPIC_API_KEY, "User")
schtasks /Create /SC DAILY /ST 07:00 /TN "CopperValleyDiario" /TR "cmd /c cd /d C:\Users\vpareja\Desktop\Ribs\diario-startapero && .venv\Scripts\python.exe -m scraper.run"
```

Verificar con `schtasks /Query /TN "CopperValleyDiario"`.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```

## Operación

- Despublicar una nota: `UPDATE articles SET estado = 'hidden' WHERE url_original = '...'`
- Validar fuentes RSS: `.venv\Scripts\python.exe -m scripts.validar_fuentes`
- Base de datos: `diario.db` (SQLite) en la raíz del repo.
