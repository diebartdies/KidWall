from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship, declarative_base, Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import enum
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

_DB_USER = os.getenv('POSTGRES_USER', 'colepago')
_DB_PASS = os.getenv('POSTGRES_PASSWORD', 'colepago_pass')
_DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
_DB_PORT = os.getenv('POSTGRES_PORT', '5432')
_DB_NAME = os.getenv('POSTGRES_DB', 'colepago')

DATABASE_URL = f"postgresql://{_DB_USER}:{_DB_PASS}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
    temp_password_hash = Column(String, nullable=True)
    temp_password_expires = Column(DateTime, nullable=True)

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


# --- ParentProfile and EmergencyContact models ---

class ParentProfile(Base):
    __tablename__ = "parent_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    role = Column(String, nullable=True)
    home_address = Column(String, nullable=True)
    home_postal = Column(String, nullable=True)
    home_phone = Column(String, nullable=True)
    mobile_phone = Column(String, nullable=True)
    country_code = Column(String, nullable=True)
    work_name = Column(String, nullable=True)
    work_address = Column(String, nullable=True)
    work_phone = Column(String, nullable=True)
    workplace = Column(String, nullable=True)
    email = Column(String, nullable=True)
    # Relationship
    user = relationship("User", backref="parent_profile", uselist=False)
    emergency_contacts = relationship("EmergencyContact", back_populates="parent_profile", cascade="all, delete-orphan")

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    id = Column(Integer, primary_key=True, index=True)
    parent_profile_id = Column(Integer, ForeignKey("parent_profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=True)
    relation = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    country_code = Column(String, nullable=True)
    home_phone = Column(String, nullable=True)
    work_phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    email = Column(String, nullable=True)
    # Relationship
    parent_profile = relationship("ParentProfile", back_populates="emergency_contacts")


# Aliases for router compatibility
UserType = UserRole
Parent = User
Merchant = User
