from sqlalchemy.orm import Session
from sqlalchemy import desc
from decimal import Decimal
from datetime import date
from typing import Optional, List
from app.models import Expense, User
from app.schemas import ExpenseCreate
from app.auth import hash_password

def create_user(db: Session, email: str, password: str) -> User:
    """Create a new user"""
    db_user = User(
        email=email,
        hashed_password=hash_password(password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_expense(db: Session, expense: ExpenseCreate, user_id: int) -> Expense:
    """Create a new expense for a user"""
    db_expense = Expense(
        amount=expense.amount,
        category=expense.category,
        note=expense.note,
        date=expense.date,
        user_id=user_id
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def get_expenses(
    db: Session,
    user_id: int,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Expense]:
    """Get expenses for a user with optional filters"""
    query = db.query(Expense).filter(Expense.user_id == user_id)
    
    if category:
        query = query.filter(Expense.category == category)
    
    if start_date:
        query = query.filter(Expense.date >= start_date)
    
    if end_date:
        query = query.filter(Expense.date <= end_date)
    
    return query.order_by(desc(Expense.date)).all()


def get_expenses_by_month(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date
) -> List[Expense]:
    """Get expenses for a user within a month range (exclusive upper bound)"""
    return db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date < end_date
    ).all()