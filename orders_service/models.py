from sqlalchemy import Column, Integer, String, Float
from pydantic import BaseModel, Field
from database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    producto = Column(String, nullable=False)
    precio = Column(Float, nullable=False)
    cantidad = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)


# Pydantic schemas
class OrderCreate(BaseModel):
    producto_id: int = Field(..., gt=0, description="ID del producto a comprar")
    cantidad: int = Field(..., gt=0, le=100, description="Cantidad solicitada")


class OrderRead(BaseModel):
    id: int
    producto: str
    precio: float
    cantidad: int
    total: float

    class Config:
        orm_mode = True
