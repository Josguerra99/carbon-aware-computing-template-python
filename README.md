# Template del equipo (Python)

Servidor de pronóstico del taller (puerto **3916**). El sitio del taller lo opera el facilitador; tú solo levantas este repo.

## Setup

Desde la raíz del repo. Crea `.env` si no existe, crea `.venv` e instala `requirements.txt`. En Windows, setup también intenta abrir el puerto **3916** en la red **privada** (solo LAN).

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

Después de setup, edita `.env` y pon **`MAIN_SERVER_URL`** con la URL que te dé el facilitador. Regístrate en el sitio del taller (`/register`) con la IP de tu PC y el puerto **3916**. Marca la Wi‑Fi como red **Privada** en Windows.

## Run

Carga `.env`, usa el venv y arranca uvicorn en `0.0.0.0:PORT` (sin recarga automática).

**Windows**

```bat
scripts\windows\run.cmd
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
| **Firewall (LAN)** | `scripts\windows\open-lan-firewall.cmd 3916` (admin si hace falta) | Abre el puerto en `ufw` si usas firewall |

Arranque manual:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn src.server.index:app --host 0.0.0.0 --port 3916
```
