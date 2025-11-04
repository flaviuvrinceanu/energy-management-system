import enum, uuid
from sqlalchemy import String, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column



class Base(DeclarativeBase): pass

class Role(str, enum.Enum):
    admin = "admin"
    client = "client"

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.client)
