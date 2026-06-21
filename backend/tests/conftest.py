import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db import Base  # Garanta que o caminho aponta para seu db.py customizado

# 1. Redefine o escopo do loop de eventos para toda a sessão de testes
@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

# 2. Exemplo de Fixture do Banco de dados assíncrono isolado para os testes (Opcional/Recomendado)
@pytest.fixture(scope="session")
async def test_engine():
    # Usando uma URL de teste sqlite ou postgres assíncrona isolada
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()