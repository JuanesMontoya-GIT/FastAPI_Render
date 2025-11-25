from sqlalchemy import Column, Integer, String, Float
from pydantic import BaseModel, Field, validator
from database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    precio = Column(Float, nullable=False)
    descripcion = Column(String(255), nullable=True)

class ProductCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre del producto (entre 3 y 100 caracteres)")
    precio: float = Field(..., gt=0, description="Precio del producto (debe ser mayor que 0)")
    descripcion: str | None = Field(None, max_length=255)

    @validator("nombre")
    def validate_nombre(cls, value):
        if not value.replace(" ", "").isalpha():
            raise ValueError("El nombre del producto solo puede contener letras y espacios")
        return value.title()

    class Config:
        orm_mode = True


class ProductUpdate(BaseModel):

    nombre: str | None = Field(None, min_length=3, max_length=100)
    precio: float | None = Field(None, gt=0)
    descripcion: str | None = Field(None, max_length=255)

    @validator("nombre")
    def validate_nombre(cls, value):
        if value and not value.replace(" ", "").isalpha():
            raise ValueError("El nombre del producto solo puede contener letras y espacios")
        return value.title() if value else value

    class Config:
        orm_mode = True

class ProductRead(BaseModel):
    id: int
    nombre: str
    precio: float
    descripcion: str

    class Config:
        orm_mode = True
