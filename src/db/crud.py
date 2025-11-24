import uuid
from sqlalchemy import select
from typing import Union, Iterable, Type
from src.db.database import connection, Base


@connection(commit=False)
async def get(model: Type[Base], _id: uuid.UUID, session):
    async with session.begin():
        result = await session.execute(select(model).filter_by(id=_id))
        _object = result.scalars().first()
        return _object


@connection(commit=False)
async def get_by_param(model: Type[Base], session, **kwargs):
    async with session.begin():
        result = await session.execute(select(model).filter_by(**kwargs))
        _object = result.scalars().first()
        return _object


@connection(commit=False)
async def get_all(model: Type[Base], session):
    async with session.begin():
        result = await session.execute(select(model))
        objects = result.scalars().all()
        return objects


@connection()
async def create(new_object: Union[Base, Iterable[Base]], session):
    async with session.begin():
        if isinstance(new_object, Iterable) and not isinstance(new_object, Base):
            session.add_all(new_object)
        else:
            session.add(new_object)
        await session.flush()
        return new_object


@connection()
async def update(updated_object: Base, session):
    async with session.begin():
        await session.merge(updated_object)
        await session.flush()


@connection()
async def delete(model: Type[Base], _id: uuid.UUID, session):
    async with session.begin():
        _object = await get(model, _id)
        await session.delete(_object)
