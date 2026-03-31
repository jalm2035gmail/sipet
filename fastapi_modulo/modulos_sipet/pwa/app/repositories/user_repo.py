from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def create(self, data: UserCreate) -> User:
        user = User(
            email=data.email.lower(),
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, obj: User, data: UserUpdate) -> User:
        payload = data.model_dump(exclude_unset=True)
        if "email" in payload and payload["email"]:
            payload["email"] = payload["email"].lower()
        for field, value in payload.items():
            setattr(obj, field, value)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def exists_email(self, email: str) -> bool:
        return self.db.query(User.id).filter(User.email == email.lower()).first() is not None

    def exists_username(self, username: str) -> bool:
        return self.db.query(User.id).filter(User.username == username).first() is not None
