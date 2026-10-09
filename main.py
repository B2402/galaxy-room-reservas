import os
import uvicorn
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from supabase import create_client, Client

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

templates = Jinja2Templates(directory="templates")

# ==========================================
# PANEL DE ADMINISTRACIÓN - GESTIÓN DE CLASES Y RESERVAS
# ==========================================

@app.get("/admin/galaxy", response_class=HTMLResponse)
def ver_panel_admin(request: Request):
    try:
        # Obtener lista de clases dinámicas desde Supabase
        clases_res = supabase.table("clases").select("*").order("id").execute()
        lista_clases = clases_res.data if clases_res.data else []

        # Construir diccionario de mapeo para las reservas
        clases_mapping = {}
        for c in lista_clases:
            coach_str = f" ({c.get('coach')})" if c.get('coach') else ""
            clases_mapping[str(c.get("id"))] = f"{c.get('dia')} - {c.get('hora')} | {c.get('modalidad')}{coach_str}"

        # Consultar reservas de Spinning
        spinning_data = supabase.table("reservas_spinning").select("*").execute()
        reservas_spinning = spinning_data.data if spinning_data.data else []
        for r in reservas_spinning:
            c_id = str(r.get("clase_id", ""))
            r["clase_texto"] = clases_mapping.get(c_id, f"Clase ID: {c_id}" if c_id else "Sin asignar")

        # Consultar reservas de Pilates
        pilates_data = supabase.table("reservas_pilates").select("*").execute()
        reservas_pilates = pilates_data.data if pilates_data.data else []
        for r in reservas_pilates:
            c_id = str(r.get("clase_id", "")) if r.get("clase_id") else str(r.get("paquete", ""))
            r["clase_texto"] = clases_mapping.get(c_id, f"Paquete/Clase: {c_id}" if c_id else "Sin asignar")

        return templates.TemplateResponse(
            request, 
            "admin.html", 
            {
                "spinning": reservas_spinning,
                "pilates": reservas_pilates,
                "clases": lista_clases
            }
        )
        
    except Exception as e:
        return HTMLResponse(content=f"<h3>Ocurrió un error en el servidor:</h3><pre>{str(e)}</pre>", status_code=500)

@app.post("/admin/clases/agregar")
def agregar_clase(
    dia: str = Form(...),
    hora: str = Form(...),
    modalidad: str = Form(...),
    coach: Optional[str] = Form("")
):
    try:
        nueva_clase = {
            "dia": dia,
            "hora": hora,
            "modalidad": modalidad,
            "coach": coach
        }
        supabase.table("clases").insert(nueva_clase).execute()
        return RedirectResponse(url="/admin/galaxy", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al agregar clase: {str(e)}")

@app.post("/admin/clases/eliminar/{id}")
def eliminar_clase(id: int):
    try:
        supabase.table("clases").delete().eq("id", id).execute()
        return RedirectResponse(url="/admin/galaxy", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar clase: {str(e)}")

@app.post("/admin/eliminar/{tipo}/{id}")
def eliminar_reserva(tipo: str, id: int):
    tabla = "reservas_spinning" if tipo == "spinning" else "reservas_pilates"
    supabase.table(tabla).delete().eq("id", id).execute()
    return RedirectResponse(url="/admin/galaxy", status_code=303)

# --- MODELOS PYDANTIC ---
class ReservaSchema(BaseModel):
    clase_id: Optional[str] = "1"
    bicicleta: str
    nombre: str
    telefono: str
    modalidad: Optional[str] = ""

class CancelarReservaSchema(BaseModel):
    telefono: str
    tipo: str
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

# --- ENDPOINTS API SPINNING Y PILATES ---

@app.get("/api/reservas/{clase_id}")
async def obtener_reservas_por_clase(clase_id: str):
    try:
        response = supabase.table("reservas_spinning").select("*").eq("clase_id", clase_id).execute()
        bici_ocupadas = [int(row.get("bicicleta")) for row in response.data if row.get("bicicleta") and str(row.get("bicicleta")).isdigit()]
        return {"bicis_ocupadas": bici_ocupadas}
    except Exception as e:
        return {"bicis_ocupadas": []}

@app.get("/api/reservas")
async def obtener_reservas(clase_id: Optional[str] = None, fecha: Optional[str] = None):
    try:
        query = supabase.table("reservas_spinning").select("*")
        if clase_id:
            query = query.eq("clase_id", clase_id)
        response = query.execute()
        bici_ocupadas = [int(row.get("bicicleta")) for row in response.data if row.get("bicicleta") and str(row.get("bicicleta")).isdigit()]
        return {"bicis_ocupadas": bici_ocupadas}
    except Exception as e:
        return {"bicis_ocupadas": []}

@app.post("/api/reservar")
async def registrar_reserva(reserva: ReservaSchema):
    bici_id = str(reserva.bicicleta).strip()
    clase_id = str(reserva.clase_id).strip()
    try:
        existing = supabase.table("reservas_spinning").select("*").eq("clase_id", clase_id).eq("bicicleta", bici_id).execute()
        if existing.data and len(existing.data) > 0:
            raise HTTPException(status_code=400, detail=f"La bicicleta #{bici_id} ya se encuentra reservada para esta clase.")
        
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
        raise HTTPException(status_code=500, detail=f"Error al guardar la reserva: {str(e)}")

@app.post("/api/cancelar")
async def cancelar_reserva(data: CancelarReservaSchema):
    telefono = data.telefono.strip()
    tipo = data.tipo.lower()
    try:
        if tipo == "spinning":
            response = supabase.table("reservas_spinning").delete().eq("telefono", telefono).execute()
            if response.data and len(response.data) > 0:
                return {"status": "ok", "mensaje": "Reserva cancelada exitosamente."}
            raise HTTPException(status_code=404, detail="No se encontró reserva con este número.")
        elif tipo == "pilates":
            response = supabase.table("reservas_pilates").delete().eq("telefono", telefono).execute()
            if response.data and len(response.data) > 0:
                return {"status": "ok", "mensaje": "Reserva cancelada exitosamente."}
            raise HTTPException(status_code=404, detail="No se encontró reserva con este número.")
        raise HTTPException(status_code=400, detail="Tipo no válido.")
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cancelar: {str(e)}")

@app.get("/api/pilates/reservas")
@app.get("/api/reservas-pilates")
async def obtener_reservas_pilates(paquete: Optional[str] = None):
    try:
        query = supabase.table("reservas_pilates").select("*")
        if paquete:
            query = query.eq("paquete", paquete)
        response = query.execute()
        camas = [int(row.get("cama")) for row in response.data if row.get("cama") and str(row.get("cama")).isdigit()]
        return {"camas_ocupadas": camas, "ocupadas": camas}
    except Exception as e:
        return {"camas_ocupadas": [], "ocupadas": []}

@app.post("/api/pilates/reservar")
@app.post("/api/reservas-pilates")
async def registrar_reserva_pilates(reserva: ReservaPilatesSchema):
    cama_id = str(reserva.cama).strip() if reserva.cama else ""
    paquete_id = str(reserva.paquete).strip() if reserva.paquete else ""
    try:
        if cama_id and paquete_id:
            existing = supabase.table("reservas_pilates").select("*").eq("paquete", paquete_id).eq("cama", cama_id).execute()
            if existing.data and len(existing.data) > 0:
                raise HTTPException(status_code=400, detail=f"La cama #{cama_id} ya está reservada.")
        nueva_reserva = reserva.dict()
        supabase.table("reservas_pilates").insert(nueva_reserva).execute()
        return {"status": "ok", "mensaje": "Reserva de Pilates registrada exitosamente."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar pilates: {str(e)}")

@app.get("/bicicletas")
async def obtener_bicicletas():
    return [
        {"id": i, "numero": i, "fila": "Frente" if i <= 2 else ("Centro" if i <= 6 else "Atrás")} 
        for i in range(1, 11)
    ]

@app.get("/clases")
async def obtener_clases():
    """Devuelve las clases activas directamente desde Supabase para la app principal."""
    try:
        response = supabase.table("clases").select("*").order("id").execute()
        return response.data if response.data else []
    except Exception as e:
        return []

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
