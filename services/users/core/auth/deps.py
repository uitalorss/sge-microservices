from typing import AsyncGenerator
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Session
from models.user_model import User

from ..configs import settings
from .auth import oauth2_schema


async def get_session() -> AsyncGenerator:
    session: AsyncSession = Session()

    try:
        yield session
    finally:
        await session.close()


async def get_current_user_main(
    security_scopes: SecurityScopes,
    check_active: bool,
    db: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_schema),
):
    credential_exception: HTTPException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de acesso inválido ou expirado.",
        headers={"WWW-authenticate": "Bearer"},
    )

    if token is None or not token.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso não fornecido ou não autorizado.",
            headers={"WWW-authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token.credentials,
            settings.JWT_KEY,
            algorithms=settings.ALGORITHM,
            options={"verify_aud": False},
        )
        user_id = payload.get("sub")
        token_scopes = payload.get("scopes", [])
        is_active = payload.get("is_active")
        if user_id is None:
            raise credential_exception

        if security_scopes.scopes:
            is_valid_scope = False
            for scope in security_scopes.scopes:
                if scope in token_scopes:
                    is_valid_scope = True
                    break

            if not is_valid_scope:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Ação não permitida para o perfil informado.",
                )
        if check_active:
            if not is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Ação não permitida para usuários inativos.",
                )

    except PyJWTError:
        raise credential_exception

    async with db as session:
        query = select(User).filter(User.id == UUID(user_id))
        result = await session.execute(query)
        usuario = result.scalars().unique().one_or_none()

        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não Autenticado",
            )
        return usuario


async def get_current_user_without_profile_check(
    security_scopes: SecurityScopes,
    db: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_schema),
):
    return await get_current_user_main(
        security_scopes=security_scopes, db=db, token=token, check_active=False
    )


async def get_current_user(
    security_scopes: SecurityScopes,
    db: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_schema),
):
    return await get_current_user_main(
        security_scopes=security_scopes, db=db, token=token, check_active=True
    )


async def get_current_profile(
    token: str = Depends(oauth2_schema),
):
    try:
        payload = jwt.decode(
            token.credentials,
            settings.JWT_KEY,
            algorithms=[settings.ALGORITHM],
        )

        scopes = payload.get("scopes", [])
        if not scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou perfil ausente",
            )

        return scopes
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido ou expirado.",
            headers={"WWW-authenticate": "Bearer"},
        )