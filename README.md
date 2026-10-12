# Template del equipo (Python)

Servidor de pronóstico del taller (puerto **3916**). El sitio del taller lo opera el facilitador; tú solo levantas este repo.

## Setup

Desde la raíz del repo. Crea `.env` si no existe, crea `.venv` e instala `requirements.txt`.

**Windows**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/setup.ps1
```

**Ubuntu**

```bash
bash scripts/ubuntu/setup.sh
```

Después de setup, edita `.env` y pon **`MAIN_SERVER_URL`** con la URL que te dé el facilitador. Regístrate en el sitio del taller (`/register`) con la IP de tu PC y el puerto **3916**.

## Run

Carga `.env`, usa el venv y arranca uvicorn en `0.0.0.0:PORT` (sin recarga automática).

**Windows**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/run.ps1
```

**Ubuntu**

```bash
bash scripts/ubuntu/run.sh
```

## Setup manual

| Requisito | Windows | Ubuntu |
| --- | --- | --- |
| **Python 3.10+** (3.11+ recomendado) | [python.org](https://www.python.org/downloads/) o `winget install Python.Python.3.12` | `sudo apt install python3 python3-venv python3-pip` |
| **Dependencias** | venv + `pip install -r requirements.txt` | Igual |
| **Config** | Copia `.env.example` → `.env` y ajusta `MAIN_SERVER_URL` | Igual |

Arranque manual:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Ubuntu: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn src.server.index:app --host 0.0.0.0 --port 3916
```
