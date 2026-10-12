# Scripts (Python)

Ayudantes de **setup** y **run** en Windows y Ubuntu (sin WSL). Ejecuta los comandos desde la **raíz del repo**.

## Comandos

| OS | Setup | Run |
| --- | --- | --- |
| Windows | `powershell -ExecutionPolicy Bypass -File scripts/windows/setup.ps1` | `powershell -ExecutionPolicy Bypass -File scripts/windows/run.ps1` |
| Ubuntu | `bash scripts/ubuntu/setup.sh` | `bash scripts/ubuntu/run.sh` |

## Qué instala / hace `setup`

| Paso | Windows | Ubuntu |
| --- | --- | --- |
| Python | Usa `py -3`, `python` o `python3` (debe estar instalado) | `python3`; si falta, `apt install python3 python3-venv python3-pip` |
| Entorno | `python -m venv .venv` | Igual |
| Dependencias | `.venv\Scripts\pip install -r requirements.txt` | `.venv/bin/pip install -r requirements.txt` |
| Config | `scripts/ensure-env.*` → crea `.env` desde `.env.example` (o valores por defecto) | Igual |

## Qué hace `run`

1. Comprueba `.venv` (si no, llama a `setup`).
2. Carga `.env`.
3. `uvicorn src.server.index:app --host 0.0.0.0 --port PORT` (sin recarga automática).

## Requisitos previos (manual)

| Herramienta | Notas |
| --- | --- |
| **Python 3.10+** | En Windows: [python.org](https://www.python.org/downloads/) o `winget install Python.Python.3.12`. |
| **Sitio del taller** | Lo opera el facilitador. Pon su URL en `MAIN_SERVER_URL` (`.env`). |

## Archivos

```
scripts/
  README.md
  windows/
    setup.ps1
    run.ps1
  ubuntu/
    setup.sh
    run.sh
```
