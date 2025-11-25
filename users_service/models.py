
from sqlalchemy import Column, Integer, String
from pydantic import BaseModel, EmailStr
from database import Base
import re

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, default="cliente", nullable=False)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    email: str
    password: str
    role: str
    def validar_correo(cls, v):
        if not v:
            return v
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, v):
            raise ValueError("El correo electrónico no tiene un formato válido (ejemplo: usuario@dominio.com)")
        return v

    def validar_role(cls, v):
        if v not in (None, "admin", "cliente"):
            raise ValueError("El rol debe ser 'admin' o 'cliente'")
        return v
    class Config:
        orm_mode = True
