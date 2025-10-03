import asyncio
from database.model.engine import engine, BaseSQLAlchemyModel
from database.model import models


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(BaseSQLAlchemyModel.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_db())