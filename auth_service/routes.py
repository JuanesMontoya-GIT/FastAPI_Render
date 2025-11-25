# routes.py
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserCreate, UserLogin, UserPublic
from utils import hash_password, verify_password, create_access_token, verify_token
import httpx
router = APIRouter()

USERS_URL = "http://127.0.0.1:8001/sync_user"

@router.post("/register")
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    user_existe = db.query(User).filter(User.email == user.email).first()
    if user_existe:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    hashed_pw = hash_password(user.password)
    new_user = User(email=user.email, password=hashed_pw, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                USERS_URL,
                json={
                    "email": new_user.email,
                    "role": new_user.role,
                    "id": new_user.id
                },
                timeout=5.0
            )
        except httpx.RequestError:
            print("⚠No se pudo conectar con el microservicio de Users")

    return {
        "message": "Usuario creado exitosamente",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "role": new_user.role
        }
    }

@router.post("/login")
def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    email = credentials.email
    password = credentials.password
    if not email or not password:
        raise HTTPException(status_code=400, detail="Faltan campos obligatorios (email o password)")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_access_token({
        "sub": user.email,
        "role": user.role,
        "id": user.id
    })
    return {"access_token": token, "token_type": "bearer"}



@router.get("/me", response_model=UserPublic)
def get_current_user(
    request: Request,
    authorization: str = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
):
    # Mostrar todos los headers para depuración
    print("HEADERS RECIBIDOS:", dict(request.headers))
    if not authorization:
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de token inválido. Debe comenzar con 'Bearer '")
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user
