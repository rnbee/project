from typing import List, Literal, Optional, Annotated
from datetime import timedelta
import json

from fastapi import Query, status, Depends, Request, Response, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select

from utils import get_db_conn, get_rpc_client, validate_categorys, RegistrationParcelRPClient
from schemas import ParcelId, ParcelInfo, ParcelCreate, CategoryFilter
from models import Parcel, Category
from crud import get_parcel_by_id, get_category_id_by_name
from redis_conn import get_redis_conn


routes = APIRouter(
    prefix="/parcel",
    tags=['Parcel']
)


@routes.post("", status_code=status.HTTP_201_CREATED, response_model=ParcelId)
async def register_parcel(request: Request,
                          parcel: ParcelCreate,
                          db_conn: AsyncSession = Depends(get_db_conn),
                          rpc_client: RegistrationParcelRPClient = Depends(get_rpc_client),
                          redis_client: AsyncSession = Depends(get_redis_conn)) -> int:
    """
    Регистрация посылки

    - **parcel_name**: каждая посылка должна содержать имя
    - **weight**: вес в кг.
    - **category**: любая из иеющихся категория ['clothes', 'electronics', 'other']
    - **cost**: стоимость посылки в долларах

    """

    try:
        db_category = await get_category_id_by_name(db_conn=db_conn, category_name=parcel.parcel_category)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"This category: {parcel.category} does not exist")

    # Cоздаем модель посылки с заменой строки категории на id
    parcel_model = parcel.model_dump()
    parcel_model['parcel_category'] = db_category.id

    # Извлекаем session_id пользователя из cookie и сохраняем в parcel_model
    session_id = request.session.get('session_id')
    parcel_model['session_id'] = session_id

    try:
        # Публикация данных в rabbitmq, consumer принимает данные,
        # вычесляет стоимость доставки и сохраняет данные в db
        # consumer возвращает id зарегистрированной посылки
        parcel_info = await rpc_client.call(parcel_model)

        async with redis_client.pipeline() as pipe:
            pipe.hset(f"session_id:{session_id}", f"parcel:{parcel_info['id']}", json.dumps(parcel_info).encode())
            pipe.expire(f"session_id:{session_id}", timedelta(hours=1))
            await pipe.execute()
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return {'id': parcel_info['id']}


@routes.get("", status_code=status.HTTP_200_OK, response_model=List[ParcelInfo])
async def get_user_parcels(request: Request,
                           category_names: Optional[List[Literal['clothes', 'electronics', 'other']]] = Query(None),
                           db_conn: AsyncSession = Depends(get_db_conn),
                           redis_client: AsyncSession = Depends(get_redis_conn),
                           has_delivery_cost: Annotated[bool,
                                                        Query(description="Filter by delivery cost presence")] = None,
                           skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
                           limit: Annotated[int, Query(gt=0, description="Number of items to return")] = 10):
    """
    Возвращает все посылки пользователя по заданным фильтрам.

    - **category_names**: филльтрация по категории
    - **has_delivery_cost**: фильтрация по наличию расчитанной суммы доставки
    - **param skip**:
    - **param limit**:
    """

    filters = []

    session_id = request.session.get('session_id')
    filters.append(Parcel.session_id == session_id)

    # Фильтрация по категориям, если указаны
    if category_names:
        filters.append(Parcel.category.has(Category.category_name.in_(category_names)))

    # Фильтрация по стоимости доставки
    if has_delivery_cost is not None:
        delivery_cost_fiter = Parcel.delivery_cost.isnot(None) if has_delivery_cost else Parcel.delivery_cost.is_(None)
        filters.append(delivery_cost_fiter)

    # Формирование зароса
    query = select(Parcel)\
        .options(joinedload(Parcel.category))\
        .filter(*filters)\
        .offset(skip)\
        .limit(limit)
    result = await db_conn.execute(query)
    parcels = result.scalars().all()

    if not parcels:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return parcels


@routes.get("/{parcel_id}", response_model=ParcelInfo)
async def get_parcel_details(parcel_id: int,
                             request: Request,
                             db_conn: AsyncSession = Depends(get_db_conn),
                             redis_client: AsyncSession = Depends(get_redis_conn)):

    """Выводит информацию о зарегистрированной посылки."""

    session_id = request.session.get('session_id')
    # Нужно сделать так, чтобы выводилось название категории а не ее id

    async with redis_client.pipeline() as pipe:
        pipe.hget(f'session_id:{session_id}', f'parcel:{parcel_id}')
        db_parcel = await pipe.execute()

    if db_parcel is not None:
        return json.loads((db_parcel[0].decode('utf-8')))

    db_parcel = get_parcel_by_id(db_conn, parcel_id, session_id)

    if db_parcel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Parcel with id: {parcel_id} does not exist")

    return db_parcel


