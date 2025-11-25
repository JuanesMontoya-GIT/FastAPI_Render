# routes.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from models import Order, OrderCreate, OrderRead
import httpx

router = APIRouter()

AUTH_URL = "http://127.0.0.1:8000/me"
PRODUCTS_URL = "http://127.0.0.1:8002/products"


async def get_current_user(authorization: str = Header(None)):
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
            raise HTTPException(
                status_code=503,
                detail="No se pudo conectar con el servicio de autenticación"
            )
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return response.json()


async def cliente_required(user=Depends(get_current_user)):
    if user.get("role") not in ["admin", "cliente"]:
        raise HTTPException(
            status_code=403,
            detail="Solo los clientes pueden realizar pedidos"
        )
    return user


async def get_product_info(product_id: int, authorization: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{PRODUCTS_URL}/{product_id}",
                headers={"Authorization": authorization},
                timeout=5.0
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="No se pudo conectar con el servicio de productos"
            )

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    elif response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Error al obtener información del producto"
        )
    return response.json()


@router.get("/orders", response_model=list[OrderRead])
async def list_orders(
        user=Depends(cliente_required),
        db: Session = Depends(get_db)
):
    orders = db.query(Order).all()
    return orders

@router.post("/orders", response_model=OrderRead, status_code=201)
async def create_order(
        order_data: OrderCreate,
        authorization: str = Header(None),
        user=Depends(cliente_required),
        db: Session = Depends(get_db)
):
    product = await get_product_info(order_data.producto_id, authorization)


    total = product["precio"] * order_data.cantidad

    new_order = Order(
        producto=product["nombre"],
        precio=product["precio"],
        cantidad=order_data.cantidad,
        total=total
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order

@router.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(
        order_id: int,
        user=Depends(cliente_required),
        db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    return order