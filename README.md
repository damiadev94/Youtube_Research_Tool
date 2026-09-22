# YouTube Research Tool

Aplicación local de Python que abre búsquedas de YouTube en Chromium y guarda los primeros resultados de vídeo en CSV. No usa la API de YouTube ni incluye mecanismos de evasión de CAPTCHA, límites o protecciones anti-bot.

## Instalación

Requiere Python 3.10+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
playwright install chromium
```

## Uso

El CSV de entrada debe tener la columna `query`; `category` y `url` son opcionales. Si `url` está vacía, se genera a partir de la consulta. Los archivos se leen como UTF-8 (también UTF-8 con BOM).

```powershell
python -m src.main --input input/searches.csv --limit 10 --queries 5
```

Por defecto Chromium se abre visible. Para ejecución sin ventana:

```powershell
python -m src.main --input input/searches.csv --headless
```

Para continuar un trabajo interrumpido, usa el mismo directorio de salida y `--resume`:

```powershell
python -m src.main --input input/searches.csv --output output --limit 10 --resume
```

Opciones: `--delay-min`, `--delay-max` (2 y 5 segundos por defecto), `--retries` (2 por defecto), `--queries` para prueba limitada y `--output`.

## Salida

`output/results.csv` se escribe después de cada consulta exitosa. `output/checkpoints.json` registra las consultas completadas para reanudación; `output/errors.csv` conserva fallos agotados; `output/run_summary.json` resume la última ejecución. Los eventos detallados se guardan en `logs/run.log`.

## Pruebas

```powershell
pytest
```
