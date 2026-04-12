
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship, declarative_base
import enum
import datetime

Base = declarative_base()

class School(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    provincia = Column(String, nullable=False)
    ciudad = Column(String, nullable=False)
    comuna = Column(String, nullable=True)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

class UserRole(enum.Enum):
    parent = "parent"
    merchant = "merchant"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    role = Column(Enum(UserRole), nullable=False)
    address = Column(String, nullable=True)  # Only for merchants
    latitude = Column(Float, nullable=True)  # Only for merchants
    longitude = Column(Float, nullable=True) # Only for merchants
    children = relationship("Child", back_populates="parent")

class Child(Base):
    __tablename__ = "children"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    balance = Column(Float, default=0.0)
    school_lat = Column(Float, nullable=True)
    school_lon = Column(Float, nullable=True)
    parent = relationship("User", back_populates="children")
    is_blocked = Column(Integer, default=0)  # 0 = active, 1 = blocked
    suspicious_reason = Column(String, nullable=True)
    last_merchants = Column(String, nullable=True)  # Comma-separated merchant IDs for quick pattern check


class TransactionType(enum.Enum):
    fund = "fund"
    spend = "spend"
    settle = "settle"
    transfer = "transfer"


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, nullable=True)  # User or child
    to_id = Column(Integer, nullable=True)    # User or child
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String, nullable=True)
