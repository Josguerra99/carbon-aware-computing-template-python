# Plantilla Python — pronóstico GHI

Misma idea que la plantilla TypeScript: el sitio del taller pide predicciones a **tu** servidor local.

## Dónde trabajar

| Archivo | Qué haces |
| --- | --- |
| `src/main.py` | Elige el modelo (`workshop_model`) e implementa `SimplePredictionModel`. |
| `src/workshop/` | (Opcional, no va a git) Copia aquí soluciones desde `examples/workshop/`. |
| `src/core/` | Infraestructura compartida — no hace falta tocarlo en el taller. |
| `src/server/index.py` | API HTTP — no hace falta tocarlo. |

## Arrancar

1. Arranca el sitio del taller (`carbon-aware-computing-website`) en el puerto **3915**.
2. Crea el entorno e instala dependencias:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Copia `.env.example` a `.env` y ajusta `MAIN_SERVER_URL` si hace falta.
4. Ejecuta el servidor del equipo:

```bash
python -m uvicorn src.server.index:app --reload --host 0.0.0.0 --port 3916
```

Ejemplo de petición (igual que la plantilla TS):

`GET /forecast/chiquimula?start=2026-08-03T00:00:00.000Z&end=2026-09-02T00:00:00.000Z`

## API

- `GET /` — comprobación rápida.
- `GET /forecast/{datasetid}?start=...&end=...` — franjas horarias UTC con `predWm2`.

Los históricos se cachean en `cache/` al descargarlos del sitio del taller.
