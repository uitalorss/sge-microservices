import uuid

from sqlalchemy import TIMESTAMP, Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.configs import settings


class User(settings.DBBaseModel):
    __tablename__ = "usuarios"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=False,
        index=True,
    )
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    cpf = Column(String(14), nullable=False, unique=True)
    senha = Column(String, nullable=False)
    telefone = Column(String(11), nullable=True)
    criado_em = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    perfil = relationship(
        "Profile", back_populates="usuario", cascade="all, delete-orphan"
    )