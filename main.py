import os
import uvicorn
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Spinning & Pilates Galaxy Room",
    description="Sistema de reservas para Spinning y Pilates"
)

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Estructura de datos temporal en memoria
reservas_db: Dict[str, Dict[str, str]] = {}
reservas_pilates_db: List[Dict[str, Any]] = []

class ReservaSchema(BaseModel):
    bicicleta: str
    nombre: str
    telefono: str

class CancelarReservaSchema(BaseModel):
    bicicleta: str

class ReservaPilatesSchema(BaseModel):
    nombre: str
    telefono: str
    fecha_nacimiento: str
    paquete: Optional[str] = ""
    cama: Optional[str] = ""
    fruta: Optional[str] = ""
    bebida: Optional[str] = ""
    personaje: Optional[str] = ""

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse(BASE_DIR / "templates" / "index.html")

# --- ENDPOINTS SPINNING ---

@app.get("/api/reservas")
async def obtener_reservas(clase_id: Optional[str] = None, fecha: Optional[str] = None):
    """Devuelve la lista de bicicletas reservadas."""
    return {"bicis_ocupadas": [int(k) for k in reservas_db.keys() if k.isdigit()]}

@app.post("/api/reservar")
async def registrar_reserva(reserva: ReservaSchema):
    """Registra una nueva reserva de bicicleta."""
    bici_id = str(reserva.bicicleta).strip()
    if bici_id in reservas_db:
        raise HTTPException(status_code=400, detail=f"La bicicleta #{bici_id} ya se encuentra reservada.")
    
    reservas_db[bici_id] = {
        "nombre": reserva.nombre,
        "telefono": reserva.telefono
    }
    return {"status": "ok", "mensaje": f"Bicicleta #{bici_id} reservada exitosamente."}

@app.post("/api/cancelar")
async def cancelar_reserva(data: CancelarReservaSchema):
    """Cancela una reserva de bicicleta."""
    bici_id = str(data.bicicleta).strip()
    if bici_id in reservas_db:
        del reservas_db[bici_id]
        return {"status": "ok", "mensaje": f"Bicicleta #{bici_id} liberada exitosamente."}
    return {"status": "ok", "mensaje": "La bicicleta no estaba registrada en el servidor."}

# --- ENDPOINTS PILATES ---

@app.get("/api/pilates/reservas")
@app.get("/api/reservas-pilates")
async def obtener_reservas_pilates(paquete: Optional[str] = None):
    """Devuelve las camas ocupadas para Pilates."""
    if paquete:
        camas = [
            int(r.get("cama")) for r in reservas_pilates_db 
            if str(r.get("paquete")) == str(paquete) and str(r.get("cama")).isdigit()
        ]
        return {"camas_ocupadas": camas, "ocupadas": camas}
    
    camas = [int(r.get("cama")) for r in reservas_pilates_db if str(r.get("cama")).isdigit()]
    return {"camas_ocupadas": camas, "ocupadas": camas}

@app.post("/api/pilates/reservar")
@app.post("/api/reservas-pilates")
async def registrar_reserva_pilates(reserva: ReservaPilatesSchema):
    """Registra la reserva de Pilates validando disponibilidad."""
    cama_id = str(reserva.cama).strip() if reserva.cama else ""
    paquete_id = str(reserva.paquete).strip() if reserva.paquete else ""

    if cama_id and paquete_id:
        cama_ocupada = any(
            str(r.get("cama")) == cama_id and str(r.get("paquete")) == paquete_id 
            for r in reservas_pilates_db
        )
        if cama_ocupada:
            raise HTTPException(status_code=400, detail=f"La cama #{cama_id} ya se encuentra reservada para este paquete/horario.")

    nueva_reserva = reserva.dict()
    reservas_pilates_db.append(nueva_reserva)
    return {"status": "ok", "mensaje": "Reserva de Pilates registrada exitosamente."}

# --- ENDPOINTS AUXILIARES ---

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

@app.get("/clases")
async def obtener_clases():
    return [
        {"id": 1, "dia": "Lunes", "hora": "07:00 AM", "modalidad": "Just Ride", "coach": "Coquis"},
        {"id": 2, "dia": "Lunes", "hora": "05:15 PM", "modalidad": "Just Ride", "coach": "Principiantes"},
        {"id": 3, "dia": "Lunes", "hora": "06:15 PM", "modalidad": "Just Ride", "coach": "Omar"},
        {"id": 4, "dia": "Lunes", "hora": "07:15 PM", "modalidad": "Montaña", "coach": "Mayra"},
        {"id": 5, "dia": "Martes", "hora": "07:00 AM", "modalidad": "Montaña", "coach": "Coquis"},
        {"id": 6, "dia": "Martes", "hora": "06:15 PM", "modalidad": "Montaña", "coach": "Mario"},
        {"id": 7, "dia": "Martes", "hora": "07:15 PM", "modalidad": "Flow", "coach": "Mayra"},
        {"id": 8, "dia": "Miércoles", "hora": "05:15 PM", "modalidad": "Flow", "coach": "Principiantes"},
        {"id": 9, "dia": "Miércoles", "hora": "06:15 PM", "modalidad": "Power", "coach": "Mayra"},
        {"id": 10, "dia": "Miércoles", "hora": "07:15 PM", "modalidad": "Power", "coach": "Omar Loeza"},
        {"id": 11, "dia": "Jueves", "hora": "07:00 AM", "modalidad": "Power", "coach": "Coquis"},
        {"id": 12, "dia": "Jueves", "hora": "06:15 PM", "modalidad": "Power", "coach": "Coquis"},
        {"id": 13, "dia": "Jueves", "hora": "07:15 PM", "modalidad": "Power", "coach": "Mayra"},
        {"id": 14, "dia": "Viernes", "hora": "07:15 PM", "modalidad": "Power", "coach": "TEMATICA"}
    ]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
