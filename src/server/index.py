from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

load_dotenv()

from src.core import debug_logs  # noqa: E402
from src.core.data_downloader import load_historic  # noqa: E402
from src.load_data import load_training_data  # noqa: E402
from src.main import workshop_model  # noqa: E402

PORT = int(os.getenv("PORT", "3916"))
MAIN_SERVER_URL = os.getenv("MAIN_SERVER_URL", "http://192.168.0.232:3915").rstrip("/")
HOUR = timedelta(hours=1)
MAX_HOURS = 24 * 100

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def hello() -> str:
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        "<title>Hello world</title></head><body><h1>Hello world</h1></body></html>"
    )


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def hourly_utc_range(start: datetime, end: datetime) -> list[datetime]:
    first = start.replace(minute=0, second=0, microsecond=0)
    times: list[datetime] = []
    stamp = first
    while stamp < end:
        times.append(stamp)
        stamp += HOUR
    return times


def format_utc_iso(moment: datetime) -> str:
    utc = moment.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")


print("Training prediction model...")
_training = load_training_data()
workshop_model.train(_training)
print("Prediction model trained")


@app.get("/forecast/{datasetid}")
def forecast_dataset(datasetid: str, start: str | None = None, end: str | None = None):
    start_dt = parse_utc(start)
    end_dt = parse_utc(end)
    if start_dt is None or end_dt is None or end_dt <= start_dt:
        return JSONResponse(
            {"error": "start and end are required and end must be after start"},
            status_code=400,
        )

    hours = hourly_utc_range(start_dt, end_dt)
    if len(hours) > MAX_HOURS:
        return JSONResponse({"error": "range too long"}, status_code=400)

    try:
        with httpx.Client(timeout=60.0) as client:
            place = load_historic(datasetid, client)
    except (httpx.HTTPError, ValueError):
        return JSONResponse(
            {"error": f"No se pudo leer el histórico de {datasetid}"},
            status_code=502,
        )

    slots = []
    for timestamp in hours:
        try:
            debug_logs.allow_debug_logs = True
            pred_wm2 = workshop_model.forecast(timestamp, place.latitude, place.longitude)
        finally:
            debug_logs.allow_debug_logs = False
        slots.append(
            {
                "time": format_utc_iso(timestamp),
                "predWm2": float(pred_wm2) or 0.0,
            }
        )

    return {"datasetId": datasetid, "slots": slots}


if __name__ == "__main__":
    import uvicorn

    print(f"Template forecast en http://localhost:{PORT}")
    print(f"Inicio: http://localhost:{PORT}/")
    print(
        "Ejemplo: "
        f"http://localhost:{PORT}/forecast/chiquimula"
        "?start=2026-08-03T00:00:00.000Z&end=2026-09-02T00:00:00.000Z"
    )
    print(f"Histórico: {MAIN_SERVER_URL}/api/historic/ghi/:datasetid")
    uvicorn.run("src.server.index:app", host="0.0.0.0", port=PORT, reload=True)
