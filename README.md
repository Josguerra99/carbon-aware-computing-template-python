# Template del equipo (Python)

Servidor de pronóstico del taller (puerto **3916**). El sitio del taller lo opera el facilitador; tú solo levantas este repo.

## Setup

Desde la raíz del repo:

**Windows**

```bat
scripts\windows\setup.cmd
```

Si la regla de firewall falla, abre **Símbolo del sistema como administrador** y vuelve a ejecutar setup, o:

```bat
scripts\windows\open-lan-firewall.cmd 3916
```

**Ubuntu**

```bash
bash scripts/ubuntu/setup.sh
```

Luego edita `.env` y pon **`MAIN_SERVER_URL`** con la URL del facilitador. Regístrate en el taller (`/register`) con la IP de tu PC. En Windows, usa Wi‑Fi **Privada**.

## Run

**Windows**

```bat
scripts\windows\run.cmd
```

**Ubuntu**

```bash
bash scripts/ubuntu/run.sh
```

## Setup manual

El script de setup hace: crear `.env` si no existe, crear `.venv`, instalar `requirements.txt`, y en Windows la regla de firewall para el puerto **3916** (red privada, solo LAN).

Si lo haces a mano:

| Requisito | Windows | Ubuntu |
| --- | --- | --- |
| **Python 3.10+** (3.11+ recomendado) | [python.org](https://www.python.org/downloads/) o `winget install Python.Python.3.12` | `sudo apt install python3 python3-venv python3-pip` |
| **Dependencias** | venv + `pip install -r requirements.txt` | Igual |
| **Config** | Copia `.env.example` → `.env` y ajusta `MAIN_SERVER_URL` | Igual |
| **Firewall (LAN)** | `scripts\windows\open-lan-firewall.cmd 3916` (admin si hace falta) | Abre el puerto en `ufw` si usas firewall |

Arranque manual:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn src.server.index:app --host 0.0.0.0 --port 3916
```
