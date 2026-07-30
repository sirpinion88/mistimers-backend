from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict

app = FastAPI(title="MISTIMERS-MU API")

# Configuración de CORS para permitir peticiones desde Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

server_state: Dict[str, Dict[str, str]] = {
    "Server 1": {},
    "Server 2": {},
    "Server 3": {},
    "Server 20": {}
}

# Guarda la última señal de vida (heartbeat) de cada scanner por servidor
ocr_active_status: Dict[str, str] = {}

class BossReportModel(BaseModel):
    boss_id: str
    server: str

class HeartbeatModel(BaseModel):
    server: str

@app.post("/api/boss/kill")
def report_kill(data: BossReportModel):
    if data.server not in server_state:
        raise HTTPException(status_code=400, detail="Servidor inexistente")
    
    server_state[data.server][data.boss_id] = datetime.now().isoformat()
    return {"status": "success", "updated": server_state[data.server]}

@app.post("/api/bot/heartbeat")
def bot_heartbeat(data: HeartbeatModel):
    ocr_active_status[data.server] = datetime.now().isoformat()
    return {"status": "ok"}

@app.get("/api/boss/state")
def get_state():
    return {
        "timers": server_state,
        "active_scanners": ocr_active_status
    }
