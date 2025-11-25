# routes.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import httpx
from database import get_db
from models import User, UserRead, UserUpdate

router = APIRouter()

AUTH_URL = "http://127.0.0.1:8000/me"

async def admin_required(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                AUTH_URL,
                headers={"Authorization": authorization},
                timeout=5.0
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="No se pudo conectar con el servicio de autenticación")
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user = response.json()
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return user

@router.get("/users", response_model=list[UserRead], dependencies=[Depends(admin_required)])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.get("/users/{user_id}", response_model=UserRead, dependencies=[Depends(admin_required)])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.put("/users/{user_id}", response_model=UserRead, dependencies=[Depends(admin_required)])
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user_update.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="El email ya está en uso por otro usuario")
        user.email = user_update.email
    if user_update.password:
        user.password = user_update.password
    if user_update.role:
        user.role = user_update.role
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}", dependencies=[Depends(admin_required)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    return {"message": "Usuario eliminado correctamente"}

@router.post("/sync_user")
def sync_user(user_data: dict, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data["email"]).first()
    if existing_user:
        return {"message": "Usuario ya sincronizado"}

    new_user = User(
        id=user_data["id"],
        email=user_data["email"],
        role=user_data["role"]
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": f"Usuario {new_user.email} sincronizado correctamente"}
