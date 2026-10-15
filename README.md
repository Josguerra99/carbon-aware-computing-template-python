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

## TensorFlow en WSL (GPU) + proxy LAN

Igual que la plantilla TypeScript: el servidor del equipo corre en **WSL**; Windows publica **:3916** con `scripts/win-team-proxy.py` hacia WSL **:3917** cuando usas `npm run start:wsl`.

| Paso | Comando |
| --- | --- |
| Activar WSL en Windows (primera vez) | `npm run setup:wsl:host` o `scripts\windows\setup-wsl-features.cmd` |
| Setup en WSL (venv + TensorFlow GPU si hay NVIDIA) | `npm run setup:wsl` o `scripts\windows\setup-wsl-tf.cmd` |
| Solo reinstalar GPU wheel | `npm run setup:wsl:gpu` o `scripts\windows\setup-wsl-gpu.cmd` |
| Sitio :3915 + proxy + uvicorn en WSL | `npm run start:wsl:stack` |
| Solo proxy + WSL | `npm run start:wsl` |

Requisitos: driver NVIDIA con soporte WSL; en Ubuntu `nvidia-smi` debe funcionar. No instales TensorFlow en Windows si entrenas en WSL — usa solo `.venv` de Linux.

Variables en `.env`: `MAIN_SERVER_URL` (sitio :3915), `PORT` (3916 en LAN), `TF_BACKEND=gpu|cpu`.
