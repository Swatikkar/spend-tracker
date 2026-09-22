from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
from typing import Optional, Tuple, Dict
from app.crud import get_expenses_by_month


def validate_month_format(month: str) -> bool:
    """Validate YYYY-MM format"""
    if not month or len(month) != 7:
        return False
    try:
        parts = month.split('-')
        if len(parts) != 2:
            return False
        year, month_num = int(parts[0]), int(parts[1])
        if month_num < 1 or month_num > 12:
            return False
        return True
    except ValueError:
        return False


def get_month_boundaries(month: str) -> Tuple[date, date]:
    """
    Returns (start_date, end_date) for YYYY-MM
    Range is [start_date, end_date) - inclusive start, exclusive end
    Example: 2026-09 -> (2026-09-01, 2026-10-01)
    """
    year, month_num = map(int, month.split('-'))
    
    start_date = date(year, month_num, 1)
    
    if month_num == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month_num + 1, 1)
    
    return start_date, end_date


def get_previous_month(month: str) -> str:
    """Get previous month in YYYY-MM format"""
    year, month_num = map(int, month.split('-'))
    
    if month_num == 1:
        return f"{year - 1}-12"
    else:
        return f"{year}-{month_num - 1:02d}"


def calculate_summary(db: Session, user_id: int, month: Optional[str] = None) -> dict:
    """Calculate spending summary for a user's month"""
    
    if month is None:
        today = date.today()
        month = today.strftime("%Y-%m")
    
    if not validate_month_format(month):
        raise ValueError("Invalid month format. Use YYYY-MM (e.g., 2026-09)")
    
    # Current month
    current_start, current_end = get_month_boundaries(month)
    current_expenses = get_expenses_by_month(db, user_id, current_start, current_end)
    
    current_total = Decimal('0.00')
    current_by_category = {}
    
    for expense in current_expenses:
        current_total += expense.amount
        if expense.category not in current_by_category:
            current_by_category[expense.category] = Decimal('0.00')
        current_by_category[expense.category] += expense.amount
    
    # Previous month
    previous_month_str = get_previous_month(month)
    previous_start, previous_end = get_month_boundaries(previous_month_str)
    previous_expenses = get_expenses_by_month(db, user_id, previous_start, previous_end)
    
    previous_total = Decimal('0.00')
    previous_by_category = {}
    
    for expense in previous_expenses:
        previous_total += expense.amount
        if expense.category not in previous_by_category:
            previous_by_category[expense.category] = Decimal('0.00')
        previous_by_category[expense.category] += expense.amount
    
    # Calculate percentage change
    if previous_total == 0 and current_total == 0:
        percentage_change = Decimal('0')
    elif previous_total == 0 and current_total > 0:
        percentage_change = None  # Cannot calculate from zero
    else:
        percentage_change = ((current_total - previous_total) / previous_total * 100)
    
    # Generate insights
    insights = []
    for category, current_amount in current_by_category.items():
        previous_amount = previous_by_category.get(category, Decimal('0.00'))
        
        if previous_amount == 0:
            continue
        
        change_percent = ((current_amount - previous_amount) / previous_amount * 100)
        
        if change_percent > 20:
            insights.append(
                f"{category} spending increased by {change_percent:.2f}% compared with the previous month."
            )
    
    return {
        "month": month,
        "total_spend": current_total,
        "spend_by_category": current_by_category,
        "previous_month_total": previous_total,
        "month_over_month_change_percentage": float(percentage_change) if percentage_change is not None else None,
        "insights": insights
    }