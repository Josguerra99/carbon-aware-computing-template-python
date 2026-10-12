from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from src.config.env import MAIN_SERVER_URL, PORT
from src.core.debug_logs import Logger
from src.core.historic_store import historic_store
from src.core.load_data import LoadTrainingData, map_pool
from src.main import workshop_model

HOUR_MS = 3_600_000
MAX_HOURS = 24 * 100
FORECAST_CONCURRENCY = 16


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _hourly_utc_range(start: datetime, end: datetime) -> list[datetime]:
    first = datetime(
        start.year,
        start.month,
        start.day,
        start.hour,
        0,
        0,
        tzinfo=timezone.utc,
    )
    times: list[datetime] = []
    stamp_ms = int(first.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)
    while stamp_ms < end_ms:
        times.append(datetime.fromtimestamp(stamp_ms / 1000, tz=timezone.utc))
        stamp_ms += HOUR_MS
    return times


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Training prediction model...")
    datasets = await LoadTrainingData.load()
    await workshop_model.train(datasets)
    print("Prediction model trained")
    _print_startup_banner()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        "<title>Hello world</title></head><body><h1>Hello world</h1></body></html>"
    )


@app.get("/forecast/{dataset_id}")
async def forecast(
    dataset_id: str,
    start: str | None = Query(None),
    end: str | None = Query(None),
):
    start_dt = _parse_utc(start)
    end_dt = _parse_utc(end)
    if start_dt is None or end_dt is None or end_dt.timestamp() <= start_dt.timestamp():
        return JSONResponse(
            {"error": "start and end are required and end must be after start"},
            status_code=400,
        )
    hours = _hourly_utc_range(start_dt, end_dt)
    if len(hours) > MAX_HOURS:
        return JSONResponse({"error": "range too long"}, status_code=400)
    try:
        place = await historic_store.get_meta(dataset_id)
        latitude = float(place["latitude"])
        longitude = float(place["longitude"])
    except Exception:
        return JSONResponse(
            {"error": f"No se pudo leer el histórico de {dataset_id}"},
            status_code=502,
        )
    Logger.allow_debug_logs = True
    slots: list[dict[str, object]] = []
    try:

        async def predict_one(timestamp: datetime) -> dict[str, object]:
            value = await workshop_model.forecast(timestamp, latitude, longitude)
            return {"time": timestamp.isoformat().replace("+00:00", "Z"), "predWm2": float(value) or 0.0}

        slots = await map_pool(hours, FORECAST_CONCURRENCY, predict_one)
    finally:
        Logger.allow_debug_logs = False
    return {"datasetId": dataset_id, "slots": slots}


def _print_startup_banner() -> None:
    print(f"Template forecast en http://localhost:{PORT}")
    print(f"Inicio: http://localhost:{PORT}/")
    print(
        f"Ejemplo: http://localhost:{PORT}/forecast/chiquimula?"
        "start=2026-08-03T00:00:00.000Z&end=2026-09-02T00:00:00.000Z"
    )
    print(f"Histórico: {MAIN_SERVER_URL}/api/historic/ghi/:datasetid")


if __name__ == "__main__":
    import uvicorn

    _print_startup_banner()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
