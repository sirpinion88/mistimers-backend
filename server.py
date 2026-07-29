import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

app = FastAPI(title="MISTIMERS-MU API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "Mistermagu2022*"  # Cambia esto por una frase aleatoria larga
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Base de datos en memoria (Para producción persistente se recomienda integrar SQLite/PostgreSQL)
# Estructura: "username": {"password_hash": "...", "is_approved": True/False, "is_admin": True/False}
users_db: Dict[str, dict] = {
    "admin": {
        "password_hash": pwd_context.hash("tu_clave_admin_aqui"),
        "is_approved": True,
        "is_admin": True
    }
}

server_state: Dict[str, Dict[str, str]] = {
    "Server 1": {}, "Server 2": {}, "Server 3": {}, "Server 20": {}
}

# --- MODELOS DE DATOS ---
class UserRegisterModel(BaseModel):
    username: str
    password: str

class UserLoginModel(BaseModel):
    username: str
    password: str

class ApprovalModel(BaseModel):
    admin_username: str
    admin_password: str
    target_username: str

class BossReportModel(BaseModel):
    boss_id: str
    server: str

# --- FUNCIONES DE SEGURIDAD ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- ENDPOINTS ---

# 1. Registro público de usuarios
@app.post("/api/register")
def register(data: UserRegisterModel):
    user = data.username.strip().lower()
    if user in users_db:
        raise HTTPException(status_code=400, detail="El usuario ya existe.")
    
    users_db[user] = {
        "password_hash": pwd_context.hash(data.password),
        "is_approved": False,  # Queda pendiente hasta que tú lo apruebes
        "is_admin": False
    }
    return {"message": "Usuario registrado exitosamente. Pendiente de aprobación por el administrador."}

# 2. Login para Web y para el Ejecutable
@app.post("/api/login")
def login(data: UserLoginModel):
    user = data.username.strip().lower()
    if user not in users_db or not pwd_context.verify(data.password, users_db[user]["password_hash"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    
    if not users_db[user]["is_approved"]:
        raise HTTPException(status_code=403, detail="Tu cuenta aún no ha sido aprobada por el administrador.")
    
    token = create_access_token({"sub": user, "is_admin": users_db[user]["is_admin"]})
    return {"access_token": token, "token_type": "bearer", "username": user}

# 3. Endpoint para que tú apruebes usuarios registrados
@app.post("/api/admin/approve")
def approve_user(data: ApprovalModel):
    admin = data.admin_username.strip().lower()
    if admin not in users_db or not pwd_context.verify(data.admin_password, users_db[admin]["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales de admin inválidas.")
    
    if not users_db[admin]["is_admin"]:
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador.")
    
    target = data.target_username.strip().lower()
    if target not in users_db:
        raise HTTPException(status_code=404, detail="Usuario objetivo no encontrado.")
    
    users_db[target]["is_approved"] = True
    return {"message": f"Usuario {target} aprobado exitosamente."}

# 4. Reporte de Bosses (Sincronización)
@app.post("/api/boss/kill")
def report_kill(data: BossReportModel):
    if data.server not in server_state:
        raise HTTPException(status_code=400, detail="Servidor no válido")
    server_state[data.server][data.boss_id] = datetime.now().isoformat()
    return {"status": "success", "updated": server_state[data.server]}

# 5. Obtener el estado actual para la Web
@app.get("/api/boss/state")
def get_state():
    return server_state