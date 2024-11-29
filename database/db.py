from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, JSON, select

DATABASE_URL = "postgresql+asyncpg://Postgres:postgres_pw@localhost:5432/fin_db"

Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class UserBudget(Base):
    __tablename__ = "user_budgets"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    monthly_income = Column(Integer, nullable=False)
    savings_percent = Column(Integer, nullable=False)
    credit_payment = Column(Integer, nullable=True)
    expenses = Column(JSON, default=dict)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with SessionLocal() as session:
        yield session

async def get_user_budget(telegram_id: str):
    async with SessionLocal() as session:
        result = await session.execute(
            select(UserBudget).filter(UserBudget.telegram_id == telegram_id)
        )
        user_budget = result.scalar_one_or_none()
        return user_budget
