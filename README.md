# Template del equipo (Python)

Servidor de pronóstico del taller (puerto **3916**). El sitio del taller lo opera el facilitador; tú solo levantas este repo.

## Setup

Desde la raíz del repo:

**Windows**

```bat
scripts\windows\setup.cmd
```

**Ubuntu**

```bash
bash scripts/ubuntu/setup.sh
```

Luego edita `.env` y pon **`MAIN_SERVER_URL`** con la URL del facilitador. Regístrate en el taller (`/register`) con la IP de tu PC.

## Run

**Windows**

```bat
scripts\windows\run.cmd
```

**Ubuntu**

```bash
bash scripts/ubuntu/run.sh
```

## Windows y la LAN del taller

**`run.cmd`** arranca el servidor. Si la LAN falla: **`run.cmd --fix-permissions`** (UAC) corrige **python.exe** en red privada y arranca.

## Setup manual

El script de setup hace: crear `.env` si no existe, crear `.venv` e instalar `requirements.txt`.

Si lo haces a mano:

| Requisito | Windows | Ubuntu |
| --- | --- | --- |
| **Python 3.10+** (3.11+ recomendado) | [python.org](https://www.python.org/downloads/) o `winget install Python.Python.3.12` | `sudo apt install python3 python3-venv python3-pip` |
| **Dependencias** | venv + `pip install -r requirements.txt` | Igual |
| **Config** | Copia `.env.example` → `.env` y ajusta `MAIN_SERVER_URL` | Igual |

Arranque manual:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn src.server.index:app --host 0.0.0.0 --port 3916 --reload
```
