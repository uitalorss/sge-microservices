from fastapi import APIRouter
from .endpoints import teste, user

api_router = APIRouter()

api_router.include_router(teste.router, prefix="/teste", tags=["Testes"])
api_router.include_router(user.router, prefix="/user", tags=["Usuários"])