# models.py
from sqlalchemy import Column, Integer, String
from pydantic import BaseModel
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="cliente")


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "cliente"

class UserLogin(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        orm_mode = True
