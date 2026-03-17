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
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def get(self, record_id: Any) -> ModelT | None:
        return self.query().filter_by(id=record_id).first()

    def list(self, **filters: Any) -> list[ModelT]:
        query = self.query()
        if filters:
            query = query.filter_by(**filters)
        return list(query.all())

    def update(self, record_id: Any, **values: Any) -> ModelT | None:
        instance = self.get(record_id)
        if instance is None:
            return None
        for key, value in values.items():
            setattr(instance, key, value)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, record_id: Any) -> bool:
        instance = self.get(record_id)
        if instance is None:
            return False
        self.db.delete(instance)
        self.db.commit()
        return True

    def count_by(self, **filters: object) -> int:
        return self.query().filter_by(**filters).count()
