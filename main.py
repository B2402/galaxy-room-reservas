import os
import uvicorn
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from supabase import create_client, Client
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# ==========================================
# NUEVAS RUTAS PARA EL PANEL DE ADMINISTRACIÓN
# ==========================================

templates = Jinja2Templates(directory="templates")

@app.get("/admin/galaxy", response_class=HTMLResponse)
def ver_panel_admin(request: Request):
    # Consultar reservas de Spinning
    spinning_data = supabase.table("reservas_spinning").select("*").execute()
    reservas_spinning = spinning_data.data if spinning_data.data else []

    # Consultar reservas de Pilates
    pilates_data = supabase.table("reservas_pilates").select("*").execute()
    reservas_pilates = pilates_data.data if pilates_data.data else []

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "spinning": reservas_spinning,
        "pilates": reservas_pilates
    })

@app.post("/admin/eliminar/{tipo}/{id}")
def eliminar_reserva(tipo: str, id: int):
    tabla = "reservas_spinning" if tipo == "spinning" else "reservas_pilates"
    supabase.table(tabla).delete().eq("id", id).execute()
    return RedirectResponse(url="/admin/galaxy", status_code=303)


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Spinning & Pilates Galaxy Room",
    description="Sistema de reservas para Spinning y Pilates"
)
# Servir archivos estáticos
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# --- CONFIGURACIÓN DE SUPABASE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://pjatimqcgmnsnkmjspqi.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_KqE4UPVn2JYKnAudq6RV2w_GwhJj_vu")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class ReservaSchema(BaseModel):
    clase_id: Optional[str] = "1"
    bicicleta: str
    nombre: str
    telefono: str
    modalidad: Optional[str] = ""

class CancelarReservaSchema(BaseModel):
    telefono: str
    tipo: str  # "spinning" o "pilates"
    bicicleta: Optional[str] = None

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

@app.get("/api/reservas/{clase_id}")
async def obtener_reservas_por_clase(clase_id: str):
    """Devuelve la lista de bicicletas reservadas para una clase específica desde Supabase."""
    try:
        response = supabase.table("reservas_spinning").select("*").eq("clase_id", clase_id).execute()
        bici_ocupadas = []
        for row in response.data:
            bici_num = row.get("bicicleta")
            if bici_num and str(bici_num).isdigit():
                bici_ocupadas.append(int(bici_num))
        return {"bicis_ocupadas": bici_ocupadas}
    except Exception as e:
        print(f"Error al obtener reservas de spinning: {e}")
        return {"bicis_ocupadas": []}

@app.get("/api/reservas")
async def obtener_reservas(clase_id: Optional[str] = None, fecha: Optional[str] = None):
    try:
        query = supabase.table("reservas_spinning").select("*")
        if clase_id:
            query = query.eq("clase_id", clase_id)
        response = query.execute()
        
        bici_ocupadas = []
        for row in response.data:
            bici_num = row.get("bicicleta")
            if bici_num and str(bici_num).isdigit():
                bici_ocupadas.append(int(bici_num))
        return {"bicis_ocupadas": bici_ocupadas}
    except Exception as e:
        print(f"Error al obtener todas las reservas: {e}")
        return {"bicis_ocupadas": []}

@app.post("/api/reservar")
async def registrar_reserva(reserva: ReservaSchema):
    """Registra una nueva reserva de bicicleta en Supabase."""
    bici_id = str(reserva.bicicleta).strip()
    clase_id = str(reserva.clase_id).strip()
    
    try:
        # Validar si ya está ocupada en esa clase en Supabase
        existing = supabase.table("reservas_spinning")\
            .select("*")\
            .eq("clase_id", clase_id)\
            .eq("bicicleta", bici_id)\
            .execute()
            
        if existing.data and len(existing.data) > 0:
            raise HTTPException(status_code=400, detail=f"La bicicleta #{bici_id} ya se encuentra reservada para esta clase.")
        
        # Insertar registro
        data_to_insert = {
            "clase_id": clase_id,
            "bicicleta": bici_id,
            "nombre": reserva.nombre,
            "telefono": reserva.telefono,
            "modalidad": reserva.modalidad
        }
        
        supabase.table("reservas_spinning").insert(data_to_insert).execute()
        return {"status": "ok", "mensaje": f"Bicicleta #{bici_id} reservada exitosamente."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar la reserva en la base de datos: {str(e)}")

@app.post("/api/cancelar")
async def cancelar_reserva(data: CancelarReservaSchema):
    """Cancela una reserva mediante el número de teléfono en Supabase."""
    telefono = data.telefono.strip()
    tipo = data.tipo.lower()

    try:
        if tipo == "spinning":
            response = supabase.table("reservas_spinning").delete().eq("telefono", telefono).execute()
            if response.data and len(response.data) > 0:
                return {"status": "ok", "mensaje": "Reserva(s) de Spinning cancelada(s) exitosamente."}
            raise HTTPException(status_code=404, detail="No se encontró ninguna reserva de Spinning con este número de teléfono.")
        
        elif tipo == "pilates":
            response = supabase.table("reservas_pilates").delete().eq("telefono", telefono).execute()
            if response.data and len(response.data) > 0:
                return {"status": "ok", "mensaje": "Reserva(s) de Pilates cancelada(s) exitosamente."}
            raise HTTPException(status_code=404, detail="No se encontró ninguna reserva de Pilates con este número de teléfono.")
        
        raise HTTPException(status_code=400, detail="Tipo de experiencia no válido.")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cancelar la reserva: {str(e)}")

@app.post("/api/reset-db")
async def reset_db():
    """Limpia las tablas de Supabase para pruebas."""
    try:
        # Nota: Esto requiere que las tablas permitan el borrado masivo o se limpien por filas
        supabase.table("reservas_spinning").delete().neq("id", 0).execute()
        supabase.table("reservas_pilates").delete().neq("id", 0).execute()
        return {"status": "ok", "mensaje": "Base de datos en Supabase reiniciada."}
    except Exception as e:
        # Método alternativo por si no usan columna id numérica
        try:
            supabase.table("reservas_spinning").delete().gte("bicicleta", "0").execute()
            supabase.table("reservas_pilates").delete().gte("telefono", "0").execute()
            return {"status": "ok", "mensaje": "Base de datos en Supabase reiniciada."}
        except Exception as err:
            raise HTTPException(status_code=500, detail=f"No se pudo vaciar la base de datos: {str(err)}")

# --- ENDPOINTS PILATES ---

@app.get("/api/pilates/reservas")
@app.get("/api/reservas-pilates")
async def obtener_reservas_pilates(paquete: Optional[str] = None):
    """Devuelve las camas ocupadas para Pilates desde Supabase."""
    try:
        query = supabase.table("reservas_pilates").select("*")
        if paquete:
            query = query.eq("paquete", paquete)
        response = query.execute()
        
        camas = []
        for row in response.data:
            cama_val = row.get("cama")
            if cama_val and str(cama_val).isdigit():
                camas.append(int(cama_val))
                
        return {"camas_ocupadas": camas, "ocupadas": camas}
    except Exception as e:
        print(f"Error al obtener reservas de pilates: {e}")
        return {"camas_ocupadas": [], "ocupadas": []}

@app.post("/api/pilates/reservar")
@app.post("/api/reservas-pilates")
async def registrar_reserva_pilates(reserva: ReservaPilatesSchema):
    """Registra la reserva de Pilates validando disponibilidad en Supabase."""
    cama_id = str(reserva.cama).strip() if reserva.cama else ""
    paquete_id = str(reserva.paquete).strip() if reserva.paquete else ""

    try:
        if cama_id and paquete_id:
            existing = supabase.table("reservas_pilates")\
                .select("*")\
                .eq("paquete", paquete_id)\
                .eq("cama", cama_id)\
                .execute()
                
            if existing.data and len(existing.data) > 0:
                raise HTTPException(status_code=400, detail=f"La cama #{cama_id} ya se encuentra reservada para este paquete/horario.")

        nueva_reserva = reserva.dict()
        supabase.table("reservas_pilates").insert(nueva_reserva).execute()
        return {"status": "ok", "mensaje": "Reserva de Pilates registrada exitosamente."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar la reserva de pilates: {str(e)}")

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
        {"id": 1, "dia": "Lunes", "hora": "07:00 AM", "modalidad": "FLOW", "coach": "Coquis"},
        {"id": 2, "dia": "Lunes", "hora": "05:15 PM", "modalidad": "Principiantes"},
        {"id": 3, "dia": "Lunes", "hora": "06:15 PM", "modalidad": "FLOW", "coach": "Mayra"},
        {"id": 4, "dia": "Lunes", "hora": "07:15 PM", "modalidad": "FLOW", "coach": "Mario"},
        {"id": 5, "dia": "Martes", "hora": "07:00 AM", "modalidad": "Montaña", "coach": "Coquis"},
        {"id": 6, "dia": "Martes", "hora": "05:15 PM", "modalidad": "Principiantes"},
        {"id": 7, "dia": "Martes", "hora": "06:15 PM", "modalidad": "Montaña", "coach": "Tere Vega"},
        {"id": 8, "dia": "Martes", "hora": "07:15 PM", "modalidad": "Montaña", "coach": "Mayra"},
        {"id": 9, "dia": "Miércoles", "hora": "06:15 PM", "modalidad": "Gruperas", "coach": "Mayra"},
        {"id": 10, "dia": "Miércoles", "hora": "07:15 PM", "modalidad": "Gruperas", "coach": "Omar Loeza"},
        {"id": 11, "dia": "Jueves", "hora": "07:00 AM", "modalidad": "Just Ride", "coach": "Coquis"},
        {"id": 12, "dia": "Jueves", "hora": "05:15 PM", "modalidad": "Principiantes"},
        {"id": 13, "dia": "Jueves", "hora": "06:15 PM", "modalidad": "Just Ride", "coach": "Coquis"},
        {"id": 14, "dia": "Jueves", "hora": "07:15 PM", "modalidad": "Just Ride", "coach": "Mayra"},
        {"id": 15, "dia": "Viernes", "hora": "06:15 PM", "modalidad": "2'000", "coach": "Mayra"}
    ]
   
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
