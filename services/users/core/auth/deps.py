from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..configs import settings
from sqlalchemy import select
import jwt
from jwt import PyJWTError
from core.database import Session
from .auth import oauth2_schema
from models.user_model import UserModel
from uuid import UUID

async def get_session() -> AsyncGenerator:
    session: AsyncSession = Session()

    try:
        yield session
    finally:
        await session.close()

async def get_current_user(db: AsyncSession = Depends(get_session), token: str = Depends(oauth2_schema)):

    credential_exception: HTTPException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de acesso inválido ou expirado.",
        headers={"WWW-authenticate": "Bearer"}
    )

    if token is None or not token.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token de acesso não fornecido ou não autorizado.",
            headers={"WWW-authenticate": "Bearer"}
        )
    

    try:
        payload = jwt.decode(token.credentials, settings.JWT_KEY, algorithms=settings.ALGORITHM,options={"verify_aud": False})
        user_id = payload.get("sub")
        if user_id is None:
            raise credential_exception
    
    except PyJWTError:
        raise credential_exception
    
    async with db as session:
        query = select(UserModel).filter(UserModel.id == UUID(user_id))
        result = await session.execute(query)
        usuario: UserModel = result.scalars().unique().one_or_none()

        if usuario is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        return usuario