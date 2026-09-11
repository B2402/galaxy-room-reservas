import os
import json
import uvicorn
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent

SPINNING_FILE = BASE_DIR / "reservas_spinning.json"
PILATES_FILE = BASE_DIR / "reservas_pilates.json"

app = FastAPI(title="Spinning & Pilates Galaxy Room")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# --- LECTURA Y ESCRITURA EN DISCO DURA ---

def cargar_reservas_spinning() -> Dict[str, Dict[str, str]]:
    if SPINNING_FILE.exists():
        try:
            with open(SPINNING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_reservas_spinning(data: Dict[str, Dict[str, str]]):
    with open(SPINNING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cargar_reservas_pilates() -> List[Dict[str, Any]]:
    if PILATES_FILE.exists():
        try:
            with open(PILATES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_reservas_pilates(data: List[Dict[str, Any]]):
    with open(PILATES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class ReservaSchema(BaseModel):
    bicicleta: str
    nombre: str
    telefono: str

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
    # Lee directo del archivo para asegurar sincronización
    reservas = cargar_reservas_spinning()
    ocupadas = [int(k) for k in reservas.keys() if str(k).isdigit()]
    return {"bicis_ocupadas": ocupadas}

@app.post("/api/reservar")
async def registrar_reserva(reserva: ReservaSchema):
    reservas = cargar_reservas_spinning()
    bici_id = str(reserva.bicicleta).strip()
    
    if bici_id in reservas:
        raise HTTPException(status_code=400, detail=f"La bicicleta #{bici_id} ya se encuentra reservada.")
    
    reservas[bici_id] = {
        "nombre": reserva.nombre,
        "telefono": reserva.telefono
    }
    guardar_reservas_spinning(reservas)
    return {"status": "ok", "mensaje": f"Bicicleta #{bici_id} reservada exitosamente."}

# --- ENDPOINTS PILATES ---

@app.get("/api/pilates/reservas")
@app.get("/api/reservas-pilates")
async def obtener_reservas_pilates(paquete: Optional[str] = None):
    # Lee directo del archivo para asegurar sincronización en tiempo real
    reservas = cargar_reservas_pilates()
    
    camas = []
    for r in reservas:
        cama_val = r.get("cama")
        if cama_val is not None and str(cama_val).isdigit():
            # Devuelve como entero para evitar fallos de coincidencia en JS
            camas.append(int(cama_val))
            
    return {"camas_ocupadas": camas, "ocupadas": camas}

@app.post("/api/pilates/reservar")
@app.post("/api/reservas-pilates")
async def registrar_reserva_pilates(reserva: ReservaPilatesSchema):
    reservas = cargar_reservas_pilates()
    cama_id = str(reserva.cama).strip() if reserva.cama else ""

    if cama_id:
        cama_ocupada = any(str(r.get("cama")).strip() == cama_id for r in reservas)
        if cama_ocupada:
            raise HTTPException(status_code=400, detail=f"La cama #{cama_id} ya se encuentra reservada.")

    nueva_reserva = reserva.dict()
    reservas.append(nueva_reserva)
    guardar_reservas_pilates(reservas)
    return {"status": "ok", "mensaje": "Reserva de Pilates registrada exitosamente."}

# --- ENDPOINT DE LIMPIEZA MANUAL (TU OPCION Y LA DE TU TIA) ---

@app.post("/api/admin/limpiar")
async def limpiar_todo(tipo: str = "todas"):
    if tipo in ["spinning", "todas"]:
        guardar_reservas_spinning({})
    if tipo in ["pilates", "todas"]:
        guardar_reservas_pilates([])
    return {"status": "ok", "mensaje": f"Registros limpiados ({tipo}) correctamente."}

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
        {"id": 1, "dia": "Lunes", "hora": "07:00 AM", "modalidad": "Speed", "coach": "Coquis"},
        {"id": 2, "dia": "Lunes", "hora": "05:15 PM", "modalidad": "Just Ride", "coach": "Principiantes"},
        {"id": 3, "dia": "Lunes", "hora": "06:15 PM", "modalidad": "Speed", "coach": "Mayra"},
        {"id": 4, "dia": "Lunes", "hora": "07:15 PM", "modalidad": "Speed", "coach": "Omar"},
        {"id": 5, "dia": "Martes", "hora": "07:00 AM", "modalidad": "Flow", "coach": "Coquis"},
        {"id": 6, "dia": "Martes", "hora": "06:15 PM", "modalidad": "Flow", "coach": "Coquis"},
        {"id": 7, "dia": "Martes", "hora": "07:15 PM", "modalidad": "Flow", "coach": "Mario"},
        {"id": 8, "dia": "Miércoles", "hora": "05:15 PM", "modalidad": "Flow", "coach": "Principiantes"},
        {"id": 9, "dia": "Miércoles", "hora": "06:15 PM", "modalidad": "Montaña", "coach": "Omar Loeza"},
        {"id": 10, "dia": "Miércoles", "hora": "07:15 PM", "modalidad": "Montaña", "coach": "Mayra"},
        {"id": 11, "dia": "Jueves", "hora": "07:00 AM", "modalidad": "Just Ride", "coach": "Coquis"},
        {"id": 12, "dia": "Jueves", "hora": "06:15 PM", "modalidad": "Just Ride", "coach": "Mayra"},
        {"id": 13, "dia": "Jueves", "hora": "07:15 PM", "modalidad": "Just Ride", "coach": "Coquis"},
        {"id": 14, "dia": "Viernes", "hora": "07:15 PM", "coach": "TEMATICA"}
    ]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
