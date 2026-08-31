import os
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Spinning & Pilates Galaxy Room",
    description="Sistema de reservas para Spinning y Pilates"
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse(BASE_DIR / "templates" / "index.html")

@app.get("/clases")
async def obtener_clases():
    return [
        {"id": 1, "dia": "Lunes", "hora": "07:00 AM", "modalidad": "Just Ride", "coach": "Coquis"},
        {"id": 2, "dia": "Lunes", "hora": "05:15 PM", "modalidad": "Just Ride", "coach": "Principiantes"},
        {"id": 3, "dia": "Lunes", "hora": "06:15 PM", "modalidad": "Just Ride", "coach": "Mayra"},
        {"id": 4, "dia": "Lunes", "hora": "07:15 PM", "modalidad": "Montaña", "coach": "Omar"},
        {"id": 5, "dia": "Martes", "hora": "07:00 AM", "modalidad": "Montaña", "coach": "Coquis"},
        {"id": 6, "dia": "Martes", "hora": "06:15 PM", "modalidad": "Montaña", "coach": "Mario"},
        {"id": 7, "dia": "Martes", "hora": "07:15 PM", "modalidad": "Flow", "coach": "Coquis"},
        {"id": 8, "dia": "Miércoles", "hora": "05:15 PM", "modalidad": "Flow", "coach": "Principiantes"},
        {"id": 9, "dia": "Miércoles", "hora": "06:15 PM", "modalidad": "Power", "coach": "Mayra"},
        {"id": 10, "dia": "Miércoles", "hora": "07:15 PM", "modalidad": "Power", "coach": "Omar Loeza"},
        {"id": 11, "dia": "Jueves", "hora": "07:00 AM", "modalidad": "Power", "coach": "Coquis"},
        {"id": 12, "dia": "Jueves", "hora": "06:15 PM", "modalidad": "Power", "coach": "Coquis"},
        {"id": 13, "dia": "Jueves", "hora": "07:15 PM", "modalidad": "Power", "coach": "Mayra"},
        {"id": 14, "dia": "Viernes", "hora": "07:15 PM", "modalidad": "TEMATICA", "coach": "Especial"}
    ]

@app.get("/bicicletas")
async def obtener_bicicletas():
    return [
        {"id": 1, "numero": 1, "fila": "Frente"},
        {"id": 2, "numero": 2, "fila": "Frente"},
        {"id": 3, "numero": 3, "fila": "Centro"},
        {"id": 4, "numero": 4, "fila": "Centro"},
        {"id": 5, "numero": 5, "fila": "Centro"},
        {"id": 6, "numero": 6, "fila": "Centro"},
        {"id": 7, "numero": 7, "fila": "Atrás"},
        {"id": 8, "numero": 8, "fila": "Atrás"},
        {"id": 9, "numero": 9, "fila": "Atrás"},
        {"id": 10, "numero": 10, "fila": "Atrás"}
    ]

@app.post("/reservar")
async def reservar_spinning(datos: dict):
    print("Reserva Spinning:", datos)
    return {"status": "ok", "mensaje": "Reserva de Spinning confirmada"}

@app.post("/reservar/pilates")
async def reservar_pilates(datos: dict):
    print("Reserva Pilates:", datos)
    return {"status": "ok", "mensaje": "Reserva de Pilates registrada con éxito"}

# Bloque para producción en servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
