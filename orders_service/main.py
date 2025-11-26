from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette import status
from database import Base, engine
from routes import router
from fastapi.openapi.utils import get_openapi

app = FastAPI(title="Orders Microservice")

Base.metadata.create_all(bind=engine)
app.include_router(router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": exc.errors(),
            "body": exc.body  # opcional, para depuración
        },
    )
@app.get("/")
def root():
    return {"Message": "This is the DiDi API"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Orders Microservice",
        version="0.1.0",
        description="API para la gestion de ordenes",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/ping")
def ping():
    return {"status": "ok"}