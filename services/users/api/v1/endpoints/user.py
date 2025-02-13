from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.deps import (
    get_current_profile,
    get_current_user,
    get_current_user_without_profile_check,
    get_session,
)
from models.profile_model import PerfilEnum
from models.user_model import User
from schemas.user_schema import (
    CreateUserSchema,
    LoginUserSchema,
    UserUpdateSchema,
)
from services.user_service import (
    add_profile,
    change_status_profile,
    create_user,
    get_user_data,
    login_user,
    update_profile,
    update_user,
)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def post_user(
    user: CreateUserSchema, db: AsyncSession = Depends(get_session)
):
    return await create_user(user, db)


@router.post("/login", status_code=status.HTTP_200_OK)
async def post_login_user(
    user_data: LoginUserSchema, db: AsyncSession = Depends(get_session)
):
    token = await login_user(user_data, db)

    return JSONResponse(
        content={"access_token": token, "token-type": "bearer"},
        status_code=status.HTTP_202_ACCEPTED,
    )


@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(
    profile: PerfilEnum = Depends(get_current_profile),
    user: User = Depends(get_current_user_without_profile_check),
    db: AsyncSession = Depends(get_session),
):
    return await get_user_data(user_id=user.id, db=db, profile=profile)


@router.patch("/", status_code=status.HTTP_202_ACCEPTED)
async def patch_user(
    user_data: UserUpdateSchema,
    user: User = Depends(get_current_user_without_profile_check),
    db: AsyncSession = Depends(get_session),
):
    return await update_user(user_data=user_data, user_id=user.id, db=db)


@router.patch("/update-profile", status_code=status.HTTP_200_OK)
async def patch_current_profile(
    profile_to_update: PerfilEnum,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await update_profile(
        user_id=user.id, profile_to_update=profile_to_update, db=db
    )


@router.post("/create-profile/{user_id}", status_code=status.HTTP_201_CREATED)
async def post_add_profile(
    user_id: str,
    profile_to_add: PerfilEnum,
    db: AsyncSession = Depends(get_session),
    _user: User = Security(get_current_user, scopes=[PerfilEnum.ADMIN.value]),
):
    if _user.id == UUID(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é permitido adicionar um perfil ao usuário admin.",
        )

    return await add_profile(
        user_id=user_id, profile_to_add=profile_to_add, db=db
    )


@router.patch(
    "/status-profile/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def patch_change_status_profile(
    user_id: str,
    profile: PerfilEnum,
    db: AsyncSession = Depends(get_session),
    _user: User = Security(get_current_user, scopes=[PerfilEnum.ADMIN.value]),
):
    if _user.id == UUID(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é permitido alterar o status de um usuário admin.",
        )

    return await change_status_profile(user_id=user_id, profile=profile, db=db)
