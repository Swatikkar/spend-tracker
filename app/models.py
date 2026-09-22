from sqlalchemy import Column, Integer, Numeric, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    expenses = relationship("Expense", back_populates="owner")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    note = Column(String(255), nullable=True)
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    owner = relationship("User", back_populates="expenses")