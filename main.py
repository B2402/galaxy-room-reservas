import os
import uvicorn
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from supabase import create_client, Client

BASE_DIR = Path(__file__).resolve().parent

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://pjatimqcgmnsnkmjspqi.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_KqE4UPVn2JYKnAudq6RV2w_GwhJj_vu")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Spinning & Pilates Galaxy Room")

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# --- ESQUEMAS DE DATOS ---

class ReservaSchema(BaseModel):
    clase_id: Optional[str] = "1"
    bicicleta: str
    nombre: str
    telefono: str
    modalidad: Optional[str] = ""

class ReservaPilatesSchema(BaseModel):
    nombre: str
    telefono: str
    fecha_nacimiento: str
    paquete: Optional[str] = ""
    cama: Optional[str] = ""
    fruta: Optional[str] = ""
    bebida: Optional[str] = ""
    personaje: Optional[str] = ""

class CancelarSchema(BaseModel):
    telefono: str
    tipo: str  # "spinning" o "pilates"

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse(BASE_DIR / "templates" / "index.html")

# --- ENDPOINTS SPINNING ---

@app.get("/api/reservas/{clase_id}")
async def obtener_reservas_por_clase(clase_id: str):
    res = supabase.table("reservas_spinning").select("bicicleta").eq("clase_id", clase_id).execute()
    ocupadas = [int(row["bicicleta"]) for row in res.data if str(row.get("bicicleta")).isdigit()]
    return {"bicis_ocupadas": ocupadas}

@app.get("/api/reservas")
async def obtener_reservas(clase_id: Optional[str] = None, fecha: Optional[str] = None):
    query = supabase.table("reservas_spinning").select("bicicleta")
    if clase_id:
        query = query.eq("clase_id", clase_id)
    res = query.execute()
    ocupadas = [int(row["bicicleta"]) for row in res.data if str(row.get("bicicleta")).isdigit()]
    return {"bicis_ocupadas": ocupadas}

@app.post("/api/reservar")
async def registrar_reserva(reserva: ReservaSchema):
    bici_id = str(reserva.bicicleta).strip()
    clase_id = str(reserva.clase_id).strip()
    
    check = supabase.table("reservas_spinning").select("bicicleta").eq("clase_id", clase_id).eq("bicicleta", bici_id).execute()
    if check.data:
        raise HTTPException(status_code=400, detail=f"La bicicleta #{bici_id} ya se encuentra reservada para esta clase.")
    
    supabase.table("reservas_spinning").insert({
        "clase_id": clase_id,
        "bicicleta": bici_id,
        "nombre": reserva.nombre,
        "telefono": reserva.telefono,
        "modalidad": reserva.modalidad
    }).execute()
    
    return {"status": "ok", "mensaje": f"Bicicleta #{bici_id} reservada exitosamente."}

# --- ENDPOINTS PILATES ---

@app.get("/api/pilates/reservas")
@app.get("/api/reservas-pilates")
async def obtener_reservas_pilates(paquete: Optional[str] = None):
    res = supabase.table("reservas_pilates").select("cama").execute()
    camas = []
    for r in res.data:
        cama_val = r.get("cama")
        if cama_val is not None and str(cama_val).isdigit():
            camas.append(int(cama_val))
            
    return {"camas_ocupadas": camas, "ocupadas": camas}

@app.post("/api/pilates/reservar")
@app.post("/api/reservas-pilates")
async def registrar_reserva_pilates(reserva: ReservaPilatesSchema):
    cama_id = str(reserva.cama).strip() if reserva.cama else ""

    if cama_id:
        check = supabase.table("reservas_pilates").select("id").eq("cama", cama_id).execute()
        if check.data:
            raise HTTPException(status_code=400, detail=f"La cama #{cama_id} ya se encuentra reservada.")

    nueva_reserva = reserva.dict()
    supabase.table("reservas_pilates").insert(nueva_reserva).execute()
    return {"status": "ok", "mensaje": "Reserva de Pilates registrada exitosamente."}

# --- ENDPOINT DE CANCELACIÓN POR WHATSAPP ---

@app.post("/api/cancelar")
async def cancelar_reserva(datos: CancelarSchema):
    telefono = datos.telefono.strip()
    tipo = datos.tipo.strip().lower()

    if not telefono:
        raise HTTPException(status_code=400, detail="Debe ingresar un número de teléfono.")

    if tipo == "spinning":
        res = supabase.table("reservas_spinning").delete().eq("telefono", telefono).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="No se encontró ninguna reserva de Spinning con este número de WhatsApp.")
        return {"status": "ok", "mensaje": "Reserva de Spinning cancelada exitosamente."}
    
    elif tipo == "pilates":
        res = supabase.table("reservas_pilates").delete().eq("telefono", telefono).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="No se encontró ninguna reserva de Pilates con este número de WhatsApp.")
        return {"status": "ok", "mensaje": "Reserva de Pilates cancelada exitosamente."}
    
    else:
        raise HTTPException(status_code=400, detail="Tipo de reserva inválido.")

# --- ENDPOINT DE LIMPIEZA MANUAL ---

@app.post("/api/admin/limpiar")
async def limpiar_todo(tipo: str = "todas"):
    if tipo in ["spinning", "todas"]:
        supabase.table("reservas_spinning").delete().neq("bicicleta", "0").execute()
    if tipo in ["pilates", "todas"]:
        supabase.table("reservas_pilates").delete().neq("id", 0).execute()
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
        {"id": 14, "dia": "Viernes", "hora": "07:15 PM", "modalidad": "Libre", "coach": "TEMATICA"}
    ]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
