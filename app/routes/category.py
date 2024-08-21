from typing import List

from fastapi import APIRouter, status, Request, Depends, Response
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Category
from schemas import Category as schemaCategory
from utils import get_db_conn

router = APIRouter(
    prefix="/category",
    tags=['Category']
)


@router.get("", status_code=status.HTTP_200_OK, response_model=List[schemaCategory])
async def get_categories(db_conn: AsyncSession = Depends(get_db_conn)):
    """Возвращает все категории."""

    db_categories = await db_conn.execute(select(Category))
    db_categories = db_categories.scalars().all()

    if db_categories is None:
        return Response(status.HTTP_204_NO_CONTENT)

    return db_categories
