from sqlalchemy.future import select

from db_init import AsyncSession
from models import Category, Parcel


async def get_category_id_by_name(db_conn: AsyncSession, category_name: str) -> Category:
    """Получаем id категории из базы данных."""

    query = select(Category).filter(Category.category_name == category_name if category_name else True)
    db_category = await db_conn.execute(query)

    db_category = db_category.scalars().first()
    return db_category


async def get_parcel_by_id(db_conn: AsyncSession, parcel_id: int, session_id: str) -> Parcel:
    """ """

    query = select(Parcel).filter(Parcel.session_id == session_id and Parcel.id == parcel_id)
    db_parcel = await db_conn.execute(query)

    db_parcel = db_parcel.scalars().first()
    return db_parcel
