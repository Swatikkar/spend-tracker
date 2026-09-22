from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional
from pathlib import Path

from app.database import engine, Base, get_db
from app.models import User
from app.schemas import (
    ExpenseCreate, ExpenseResponse, SummaryResponse,
    UserRegister, UserLogin, UserResponse, Token
)
from app.crud import (
    create_expense, get_expenses, create_user, get_user_by_email
)
from app.services import calculate_summary
from app.auth import (
    get_current_user, create_access_token, verify_password
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Spend Tracker API")

# ==================== AUTH ENDPOINTS ====================

@app.post("/auth/register", response_model=UserResponse, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = create_user(db, user_data.email, user_data.password)
    return user


@app.post("/auth/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login and get JWT token"""
    user = get_user_by_email(db, user_data.email)
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==================== EXPENSE ENDPOINTS ====================

@app.post("/expenses", response_model=ExpenseResponse, status_code=201)
def add_expense(
    expense: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new expense for the logged-in user"""
    db_expense = create_expense(db, expense, current_user.id)
    return db_expense


@app.get("/expenses", response_model=list[ExpenseResponse])
def list_expenses(
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List expenses for the logged-in user with optional filters.
    
    Query parameters:
    - category: Filter by category
    - start_date: Filter from this date (inclusive)
    - end_date: Filter until this date (inclusive)
    """
    
    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be later than end_date"
        )
    
    expenses = get_expenses(
        db,
        user_id=current_user.id,
        category=category,
        start_date=start_date,
        end_date=end_date
    )
    return expenses


@app.get("/summary", response_model=SummaryResponse)
def get_summary(
    month: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get spending summary for the logged-in user.
    
    Query parameters:
    - month: YYYY-MM format (e.g., 2026-09). Defaults to current month.
    """
    
    try:
        summary = calculate_summary(db, current_user.id, month)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== STATIC FILES ====================

static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")