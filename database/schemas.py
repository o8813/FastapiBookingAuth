from pydantic import BaseModel, Field, EmailStr
from enum import Enum
from typing import Optional
from datetime import date

class StatusChoices(str, Enum):
    USER = 'User'
    OWNER = 'Owner'

class UserLoginSchema(BaseModel):
    username: str
    password: str

class LogoutSchema(BaseModel):
    refresh_token: str

class UserOutSchema(BaseModel):
    id: int
    username: str = Field(min_length=3, max_length=30)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[StatusChoices] = Field(default=StatusChoices.USER)
    registered_date: date
class UserInputSchema(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(min_length=6, max_length=100)
    status: Optional[StatusChoices] = Field(default=StatusChoices.USER)