from pydantic import BaseModel, Field, field_validator, EmailStr
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Dict, List

# ==================== USER SCHEMAS ====================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# ==================== EXPENSE SCHEMAS ====================

class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    category: str = Field(..., min_length=1, max_length=50)
    note: Optional[str] = Field(None, max_length=255)
    date: date

    @field_validator('category', 'note', mode='before')
    def strip_whitespace(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator('category')
    def category_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Category cannot be empty or only spaces')
        return v


class ExpenseResponse(ExpenseCreate):
    id: int
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    month: str
    total_spend: Decimal
    spend_by_category: Dict[str, Decimal]
    previous_month_total: Decimal
    month_over_month_change_percentage: Optional[float]
    insights: List[str]