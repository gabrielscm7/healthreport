from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import get_settings

settings = get_settings()

# 1. Criação do Engine Assíncrono com pool para evitar quedas no Railway
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True
)

# 2. Configuração correta do Sessionmaker para o modo Assíncrono
# Removemos o scoped_session completamente daqui
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# 3. Gerenciador de dependência injetado corretamente por requisição (Event Loop isolado)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Tipagem corrigida para remover o erro do VS Code (AsyncGenerator)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
