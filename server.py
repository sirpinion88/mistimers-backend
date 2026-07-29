from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Dict

app = FastAPI(title="MISTIMERS-MU API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado de bosses en memoria
server_state: Dict[str, Dict[str, str]] = {
    "Server 1": {},
    "Server 2": {},
    "Server 3": {},
    "Server 20": {}
}

# Base de datos de usuarios autorizados
USERS_DB = {
    "admin": "mudream123",
    "clan1": "clave123"
}

class LoginModel(BaseModel):
    username: str
    password: str

class BossReportModel(BaseModel):
    boss_id: str
    server: str

@app.post("/api/login")
def login(data: LoginModel):
    if data.username in USERS_DB and USERS_DB[data.username] == data.password:
        return {"access_token": f"token-{data.username}", "status": "authorized"}
    raise HTTPException(status_code=401, detail="Usuario o clave incorrecta")

@app.post("/api/boss/kill")
def report_kill(data: BossReportModel):
    if data.server not in server_state:
        raise HTTPException(status_code=400, detail="Servidor inexistente")
    
    server_state[data.server][data.boss_id] = datetime.now().isoformat()
    return {"status": "success", "updated": server_state[data.server]}

@app.get("/api/boss/state")
def get_state():
    return server_state