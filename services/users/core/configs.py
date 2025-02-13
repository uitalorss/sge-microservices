from typing import ClassVar
from pydantic_settings import BaseSettings
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
import os
import dotenv

dotenv.load_dotenv()

tipo_ambiente: str = os.getenv("TIPO_AMBIENTE")

class Settings(BaseSettings):
    DB_HOST: ClassVar[str] = os.getenv("DB_HOST")
    DB_PORT: ClassVar[str] = os.getenv("DB_PORT")
    DB_USER: ClassVar[str] = os.getenv("DB_USER")
    DB_PASS: ClassVar[str] = os.getenv("DB_PASS")
    DB_NAME: ClassVar[str] = os.getenv("DB_NAME")
    DB_BANCO: ClassVar[str] = "postgresql+asyncpg"
    DB_URL: ClassVar[str]

    if not all([DB_NAME, DB_USER, DB_PASS, DB_HOST, DB_PORT]):
        raise ValueError(
            "Missing one or more environment variables for production database "
            "connection."
        )

    API_V1_STR: ClassVar[str] = "/api/v1"
    if tipo_ambiente == "dev":
        DB_URL = f"{DB_BANCO}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    elif tipo_ambiente == "initial":
        DB_URL = "sqlite+aiosqlite:///./dev.db"
    else:
        raise ValueError("Tipo de ambiente informado é inválido.")

    DBBaseModel: ClassVar[DeclarativeMeta] = declarative_base()

    JWT_KEY: str = os.getenv("JWT_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    class Config:
        case_sensitive: True

settings: Settings = Settings()