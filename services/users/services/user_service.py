from uuid import UUID

from fastapi import HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from core.auth.auth import create_access_token
from core.auth.security import generate_hashed_password, verify_password
from models.profile_model import PerfilEnum, Profile
from models.user_model import User
from schemas.user_schema import (
    CreateUserSchema,
    LoginUserSchema,
    ProfileResponseSchema,
    UserUpdateSchema,
)


async def create_user(user: CreateUserSchema, db: AsyncSession):
    new_user: User = User(
        nome=user.nome,
        email=user.email,
        cpf=user.cpf,
        senha=generate_hashed_password(user.senha),
        telefone=user.telefone,
    )
    async with db as session:
        try:
            session.add(new_user)
            await session.flush()
            for perfil_item in user.perfil:
                new_perfil: Profile = Profile(
                    usuario_id=new_user.id, tipo_perfil=perfil_item
                )
                session.add(new_perfil)

            await session.commit()

            return {"message": "Usuário criado com sucesso."}
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Favor verificar dados.",
            )

        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dados informados são inválidos.",
            )


async def login_user(user_data: LoginUserSchema, db: AsyncSession):
    async with db as session:
        query = (
            select(User)
            .options(selectinload(User.perfil))
            .filter(User.email == user_data.email)
        )
        result = await session.execute(query)
        user = result.scalars().unique().one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário e/ou senha incorretos.",
            )

        if not verify_password(user_data.senha, user.senha):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário e/ou senha incorretos.",
            )

        profile_priority = {
            "ADMIN": 0,
            "ORGANIZADOR": 1,
            "PARTICIPANTE": 2,
        }

        active_profiles = [
            perfil for perfil in user.perfil if perfil.is_active
        ]
        if active_profiles:
            high_access_profile = min(
                active_profiles,
                key=lambda profile: profile_priority.get(
                    profile.tipo_perfil, float("inf")
                ),
            )
        else:
            high_access_profile = min(
                user.perfil,
                key=lambda profile: profile_priority.get(
                    profile.tipo_perfil, float("inf")
                ),
            )

        token_data = {
            "sub": str(user.id),
            "data_type": high_access_profile.tipo_perfil,
            "is_active": high_access_profile.is_active,
        }
        return create_access_token(**token_data)


async def get_user_data(user_id: UUID, db: AsyncSession, profile: PerfilEnum):
    async with db as session:
        result = await session.execute(
            select(User)
            .options(selectinload(User.perfil))
            .filter(User.id == user_id)
        )

        user_db = result.scalars().unique().one_or_none()

        if user_db is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )

        perfil_atual = next(
            (
                ProfileResponseSchema.model_validate(perfil)
                for perfil in user_db.perfil
                if perfil.tipo_perfil == profile
            ),
            None,
        )
        outros_perfis = [
            ProfileResponseSchema.model_validate(perfil)
            for perfil in user_db.perfil
            if perfil.tipo_perfil != profile
        ]

        user = {
            "nome": user_db.nome,
            "email": user_db.email,
            "telefone": user_db.telefone,
            "perfil_atual": perfil_atual,
            "outro_perfis": outros_perfis
        }

        return user


async def update_user(
    user_data: UserUpdateSchema, user_id: UUID, db: AsyncSession
):
    async with db as session:
        result = await session.execute(select(User).filter(User.id == user_id))
        user_update = result.scalars().first()

        if user_update is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )

        for field, value in user_data.model_dump(exclude_unset=True).items():
            if field == "senha":
                value = generate_hashed_password(value)
            setattr(user_update, field, value)

        await session.commit()

        return {"message": "Usuário atualizado com sucesso."}


async def update_profile(
    user_id: User, profile_to_update: PerfilEnum, db: AsyncSession
):
    async with db as session:
        query = (
            select(User)
            .options(joinedload(User.perfil))
            .filter(User.id == user_id)
        )
        result = await session.execute(query)
        user = result.scalars().unique().one_or_none()

        if not user or not user.perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário ou perfil não encontrado.",
            )

        available_profile = next(
            (
                perfil
                for perfil in user.perfil
                if perfil.tipo_perfil == profile_to_update.value
            ),
            None,
        )
        if available_profile is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Perfil não disponível para o usuário.",
            )

        token_data = {
            "sub": str(user.id),
            "data_type": available_profile.tipo_perfil,
            "is_active": available_profile.is_active,
        }

        access_token = create_access_token(**token_data)

        return {
            "message": f"Perfil alterado para {available_profile.tipo_perfil.value}.",
            "access_token": access_token,
        }


async def add_profile(
    user_id: UUID, profile_to_add: PerfilEnum, db: AsyncSession
):
    async with db as session:
        query = (
            select(User)
            .options(selectinload(User.perfil))
            .filter(User.id == UUID(user_id))
        )
        result = await session.execute(query)
        user = result.scalars().unique().one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário ou perfil não encontrado.",
            )

        for perfil in user.perfil:
            if perfil.tipo_perfil == profile_to_add.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Perfil já adicionado ao usuário.",
                )

        new_profile = Profile(usuario_id=user.id, tipo_perfil=profile_to_add)
        session.add(new_profile)

        await session.commit()

        return {"message": "Perfil adicionado ao usuário com sucesso."}


async def change_status_profile(
    user_id: str, profile: PerfilEnum, db: AsyncSession
):
    async with db as session:
        query = (
            select(User)
            .options(selectinload(User.perfil))
            .filter(User.id == UUID(user_id))
        )
        result = await session.execute(query)
        user = result.scalars().unique().one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )

        profile_to_change = next(
            (
                perfil
                for perfil in user.perfil
                if perfil.tipo_perfil == profile.value
            ),
            None,
        )
        if profile_to_change is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado.",
            )

        profile_to_change.is_active = not profile_to_change.is_active
        await session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)