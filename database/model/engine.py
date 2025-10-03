from sqlalchemy.orm import DeclarativeBase 
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import DBConfig


class BaseSQLAlchemyModel(DeclarativeBase):
    pass


db = DBConfig()
engine = create_async_engine(db.db_url, echo=False)

SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


