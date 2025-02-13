from fastapi import APIRouter
from .endpoints import teste

api_router = APIRouter()

api_router.include_router(teste.router, prefix="/teste", tags=["Testes"])