import uuid
from enum import Enum

from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.configs import settings


class PerfilEnum(str, Enum):
    ORGANIZADOR = "Organizador"
    PARTICIPANTE = "Participante"
    ADMIN = "Admin"


class Profile(settings.DBBaseModel):
    __tablename__ = "perfis"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    )
    usuario_id = Column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="cascade")
    )
    tipo_perfil = Column(SQLAlchemyEnum(PerfilEnum), nullable=False)
    is_active = Column(Boolean, default=True)

    usuario = relationship("User", back_populates="perfil")