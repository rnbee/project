from sqlalchemy import Column, String, Integer, \
    Float, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship

from db_init import Base


class Parcel(Base):
    __tablename__ = 'parcels'

    id = Column(Integer, primary_key=True, index=True)
    parcel_name = Column(String(20), unique=True, nullable=False)
    weight = Column(Float, nullable=False)
    cost = Column(Integer, nullable=False)
    parcel_category = Column(Integer, ForeignKey('categories.id'))
    delivery_cost = Column(Float, default=None)
    session_id = Column(String(36), index=True, nullable=False)

    category = relationship('Category', back_populates='parcels')


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    category_name = Column(String(20), unique=True, nullable=False)

    parcels = relationship('Parcel', back_populates='category')

    __table_args__ = (
        CheckConstraint(
            "parcel_category IN ('clothes', 'electronics', 'other')",
            name='check_category'
        ),
    )
