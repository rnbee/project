from typing import List, Literal, Annotated
from decimal import Decimal

from pydantic import Field, BaseModel, model_serializer


class ParcelCreate(BaseModel):
    parcel_name: Annotated[str, Field(examples=['example_parcel'])]
    weight: Annotated[int, Field(gt=0)]
    parcel_category: Literal['clothes', 'electronics', 'other']
    cost: Annotated[Decimal, Field(gt=0,
                                   decimal_places=2,
                                   description='content value in dollars',
                                   examples=['23.34']
                                   )]

    @model_serializer()
    def serialize_model(self):
        return {'parcel_name': self.parcel_name,
                'weight': self.weight,
                'cost': float(self.cost)
                }


class Parcel(BaseModel):
    parcel_name: str
    weight: int
    parcel_category: str | int
    cost: float
    delivery_cost: float | None

    class Config:
        from_attribute = True


class ParcelId(BaseModel):
    """Схема для возврата id зарегистрированной посылки."""

    id: int

    class Config:
        from_attributes = True


class ParcelInfo(ParcelId):
    """Схема для возврата полной информации о загеристрированных посылках."""

    parcel_name: str
    weight: int
    parcel_category: int
    cost: float
    delivery_cost: float | None


class Category(BaseModel):
    id: int
    category_name: str

    class Config:
        from_attributes = True


class CategoryFilter(BaseModel):
    category_names: List[Literal['clothes', 'electronics', 'other']]
