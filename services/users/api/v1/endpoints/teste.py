from fastapi import APIRouter, status

router = APIRouter()

# Define uma rota básica
@router.get("/", status_code=status.HTTP_200_OK)
def read_root():
    return {"message": "Olá, mundo!"}

# Rota com parâmetro
@router.get("/ola/{nome}", status_code=status.HTTP_200_OK)
def cumprimentar(nome: str):
    return {"message": f"Olá, {nome}!"}