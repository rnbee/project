from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from .category import get_categories

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/page",
    tags=['Pages'],
    default_response_class=HTMLResponse
)


@router.get("/")
async def get_home_page(request: Request):
    """Показывает основную страницу."""

    return templates.TemplateResponse(request=request, name="home.html", context={})


@router.get("/parcel")
async def get_page_register_parcel(request: Request):
    """Рендерит страниу регистрации посылки."""

    return templates.TemplateResponse(request=request, name="register_parcel.html", context={})


@router.get("/category")
async def get_page_categories(request: Request, db_categories=Depends(get_categories)):
    """Возвращает страницу со всеми категориями."""

    return templates.TemplateResponse(request=request, name="categories.html", context={"categories": db_categories})


@router.get("/parcels")
async def get_page_parcels(request: Request):
    """Возвращает страницу на которой осуществляется поиск посылок принадлежащих пользователю,
     с возможностью задать определенные фильтры, результат поиска рендериться на той же странице."""

    return templates.TemplateResponse(request=request, name="parcels.html", context={})


@router.get("/parcel_id")
async def get_page_parcel_id(request: Request):
    """Возвращает страницу c данными определенного ID."""

    return templates.TemplateResponse(request=request, name="parcel_details.html", context={})
