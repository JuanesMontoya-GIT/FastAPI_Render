# routes.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from models import Product, ProductCreate, ProductUpdate, ProductRead
import httpx

router = APIRouter()


AUTH_URL = "https://fastapi-render-f2yz.onrender.com/me"

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
            raise HTTPException(status_code=503, detail="No se pudo conectar con el servicio de autenticación")
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return response.json()

async def admin_required(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden realizar esta acción")
    return user

async def cliente_o_admin(user=Depends(get_current_user)):
    if user.get("role") not in ["admin", "cliente"]:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")
    return user

@router.get("/products", response_model=list[ProductRead], dependencies=[Depends(cliente_o_admin)])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products


@router.post("/products", response_model=ProductRead, dependencies=[Depends(admin_required)])
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    product_exist = db.query(Product).filter(Product.nombre == product.nombre).first()
    if product_exist:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un producto con el nombre '{product.nombre}'."
        )
    db_product = Product(
        nombre=product.nombre,
        precio=product.precio,
        descripcion=product.descripcion
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product


@router.put(
    "/products/{product_id}",
    response_model=ProductRead,
    dependencies=[Depends(admin_required)]
)
def update_product(
        product_id: int,
        product_update: ProductUpdate,
        db: Session = Depends(get_db)
):
    # Buscar el producto a actualizar
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Convertir el modelo a dict excluyendo los valores no enviados
    update_data = product_update.dict(exclude_unset=True)

    # Validar si se intenta actualizar el nombre y si ya existe otro producto con ese nombre
    if "nombre" in update_data:
        nombre_nuevo = update_data["nombre"].strip()
        if nombre_nuevo != "":
            # Verificar si otro producto ya tiene ese nombre
            existente = db.query(Product).filter(
                Product.nombre == nombre_nuevo,
                Product.id != product_id
            ).first()
            if existente:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe un producto con el nombre '{nombre_nuevo}'"
                )

    # Actualizar solo los campos que se enviaron
    for key, value in update_data.items():
        if value is not None:
            if isinstance(value, str) and value.strip() == "":
                continue
            setattr(product, key, value)

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", dependencies=[Depends(admin_required)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(db_product)
    db.commit()
    return {"Message": "Producto eliminado"}

@router.get("/products/{product_id}", response_model=ProductRead, dependencies=[Depends(cliente_o_admin)])
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product