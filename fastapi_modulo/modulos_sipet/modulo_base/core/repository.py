from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db


class SQLAlchemyRepository(BaseRepository, Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT]) -> None:
        super().__init__(db)
        self.model = model

    def query(self):
        return self.db.query(self.model)

    def create(self, **values: Any) -> ModelT:
        instance = self.model(**values)
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def create_and_commit(self, **values: Any) -> ModelT:
        instance = self.create(**values)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def get(self, record_id: Any) -> ModelT | None:
        return self.query().filter_by(id=record_id).first()

    def get_or_raise(self, record_id: Any, detail: str = "Registro no encontrado.") -> ModelT:
        instance = self.get(record_id)
        if instance is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=detail)
        return instance

    def list(self, **filters: Any) -> list[ModelT]:
        query = self.query()
        if filters:
            query = query.filter_by(**filters)
        return list(query.all())

    def list_paginated(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        **filters: Any,
    ) -> tuple[list[ModelT], int]:
        query = self.query()
        if filters:
            query = query.filter_by(**filters)
        total = query.count()
        items = list(query.offset(max(0, skip)).limit(max(1, min(limit, 500))).all())
        return items, total

    def update(self, record_id: Any, **values: Any) -> ModelT | None:
        instance = self.get(record_id)
        if instance is None:
            return None
        for key, value in values.items():
            setattr(instance, key, value)
        self.db.flush()
        self.db.refresh(instance)
        return instance

    def update_and_commit(self, record_id: Any, **values: Any) -> ModelT | None:
        instance = self.update(record_id, **values)
        if instance is None:
            return None
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, record_id: Any) -> bool:
        instance = self.get(record_id)
        if instance is None:
            return False
        self.db.delete(instance)
        self.db.flush()
        return True

    def delete_and_commit(self, record_id: Any) -> bool:
        deleted = self.delete(record_id)
        if deleted:
            self.db.commit()
        return deleted

    def count_by(self, **filters: object) -> int:
        return self.query().filter_by(**filters).count()

    def exists(self, **filters: Any) -> bool:
        return self.query().filter_by(**filters).limit(1).count() > 0

    def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelT]:
        instances = [self.model(**values) for values in items]
        self.db.add_all(instances)
        self.db.flush()
        for instance in instances:
            self.db.refresh(instance)
        return instances

    def bulk_create_and_commit(self, items: list[dict[str, Any]]) -> list[ModelT]:
        instances = self.bulk_create(items)
        self.db.commit()
        for instance in instances:
            self.db.refresh(instance)
        return instances


__all__ = [
    "BaseRepository",
    "SQLAlchemyRepository",
]
