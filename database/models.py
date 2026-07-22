from sqlalchemy import String, Date, ForeignKey, Enum
from sqlalchemy.orm import mapped_column, Mapped, relationship
from .connection import Base
from typing import Optional
from datetime import date
from enum import Enum as PyEnum

class StatusChoices(str, PyEnum):
    USER = 'User'
    OWNER = 'Owner'

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(unique=True)
    phone: Mapped[Optional[str]] = mapped_column()
    password: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[StatusChoices] = mapped_column(Enum(StatusChoices), default=StatusChoices.USER)
    registered_date: Mapped[date] = mapped_column(Date, default=date.today)

    user_refresh: Mapped['UserRefresh'] = relationship(back_populates='refresh_user',
                                                       cascade='all, delete-orphan')

    def __repr__(self):
        return f'User(id={self.id!r}, username={self.username!r})'

class UserRefresh(Base):
    __tablename__ = 'refresh'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    token: Mapped[str] = mapped_column(unique=True)

    refresh_user: Mapped[User] = relationship(back_populates='user_refresh')

    def __repr__(self):
        return f'UserRefresh(id={self.id!r}, user_id={self.user_id!r})'