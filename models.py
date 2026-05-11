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
    source = Column(String, nullable=True, index=True)
    source_year = Column(String, nullable=True)
    external_id = Column(String, nullable=True, index=True)
    sector = Column(String, nullable=True)  # public/private
    district_id = Column(String, nullable=True)
    district_name = Column(String, nullable=True)
    provincia = Column(String, nullable=False)
    ciudad = Column(String, nullable=False)
    comuna = Column(String, nullable=True)
    address = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    level = Column(String, nullable=True)
    low_grade = Column(String, nullable=True)
    high_grade = Column(String, nullable=True)
    locale_code = Column(String, nullable=True)
    county_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

class UserRole(enum.Enum):
    parent = "parent"
    merchant = "merchant"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
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
    wallet_buckets = relationship("WalletBucket", back_populates="child", cascade="all, delete-orphan")
    location_pings = relationship("ChildLocationPing", back_populates="child", cascade="all, delete-orphan", order_by="ChildLocationPing.recorded_at")
    route_waypoints = relationship("ChildRouteWaypoint", back_populates="child", cascade="all, delete-orphan", order_by="ChildRouteWaypoint.seq")
    last_route_alert = Column(DateTime, nullable=True)  # last time a route-deviation alert was sent


class ChildLocationPing(Base):
    """Single GPS ping sent by the child's device."""
    __tablename__ = "child_location_pings"
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)
    child = relationship("Child", back_populates="location_pings")


class ChildRouteWaypoint(Base):
    """One point in the child's standard home↔school route (set by parent)."""
    __tablename__ = "child_route_waypoints"
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    seq = Column(Integer, nullable=False)   # 0-based order along the route
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    child = relationship("Child", back_populates="route_waypoints")


class TransactionType(enum.Enum):
    fund = "fund"
    spend = "spend"
    settle = "settle"
    transfer = "transfer"


class LedgerOwnerType(enum.Enum):
    parent = "parent"
    child = "child"
    merchant = "merchant"
    platform = "platform"
    provider = "provider"


class LedgerAccountType(enum.Enum):
    wallet = "wallet"
    receivable = "receivable"
    fee = "fee"
    clearing = "clearing"
    payout = "payout"


class LedgerTransactionType(enum.Enum):
    deposit = "deposit"
    child_purchase = "child_purchase"
    merchant_payout = "merchant_payout"
    refund = "refund"
    adjustment = "adjustment"


class LedgerTransactionStatus(enum.Enum):
    pending = "pending"
    posted = "posted"
    failed = "failed"
    reversed = "reversed"


class PaymentProvider(enum.Enum):
    mercadopago = "mercadopago"
    stripe = "stripe"
    bank_manual = "bank_manual"


class ExternalPaymentStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"
    refunded = "refunded"


class ExternalPayoutStatus(enum.Enum):
    pending = "pending"
    processing = "processing"
    paid = "paid"
    failed = "failed"


class WalletBucket(Base):
    """
    A named spending envelope for a child.
    Parent allocates coins and sets an alert threshold (%).
    When spent/allocated >= alert_threshold_pct the parent gets notified.
    """
    __tablename__ = "wallet_buckets"
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    name = Column(String, nullable=False)               # e.g. "Lunch", "Bus", "Snacks"
    allocated = Column(Float, default=0.0)              # coins assigned to this bucket
    spent = Column(Float, default=0.0)                  # coins consumed so far
    alert_threshold_pct = Column(Integer, default=80)   # 0-100, alert when spent/allocated >= this
    alert_sent = Column(Integer, default=0)             # 1 = notification already sent this cycle
    child = relationship("Child", back_populates="wallet_buckets")

    @property
    def remaining(self) -> float:
        return max(self.allocated - self.spent, 0.0)

    @property
    def pct_used(self) -> int:
        if self.allocated <= 0:
            return 0
        return int(self.spent / self.allocated * 100)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, nullable=True)   # User or child ID
    to_id = Column(Integer, nullable=True)     # User or child ID
    child_id = Column(Integer, ForeignKey("children.id"), nullable=True)  # for rapid-spend detection
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String, nullable=True)


class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"
    id = Column(Integer, primary_key=True, index=True)
    owner_type = Column(Enum(LedgerOwnerType), nullable=False)
    owner_id = Column(Integer, nullable=True)
    account_type = Column(Enum(LedgerAccountType), nullable=False)
    currency = Column(String, default="ARS", nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    entries = relationship("LedgerEntry", back_populates="account")


class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(LedgerTransactionType), nullable=False)
    status = Column(Enum(LedgerTransactionStatus), default=LedgerTransactionStatus.posted, nullable=False)
    external_reference = Column(String, nullable=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    entries = relationship("LedgerEntry", back_populates="transaction", cascade="all, delete-orphan")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("ledger_transactions.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("ledger_accounts.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    transaction = relationship("LedgerTransaction", back_populates="entries")
    account = relationship("LedgerAccount", back_populates="entries")


class MerchantPayoutMethod(Base):
    __tablename__ = "merchant_payout_methods"
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(Enum(PaymentProvider), nullable=False)
    provider_account_id = Column(String, nullable=True)
    label = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    merchant = relationship("User")


class ExternalPayment(Base):
    __tablename__ = "external_payments"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(Enum(PaymentProvider), nullable=False)
    external_id = Column(String, nullable=True, index=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, default="ARS", nullable=False)
    status = Column(Enum(ExternalPaymentStatus), default=ExternalPaymentStatus.pending, nullable=False)
    ledger_transaction_id = Column(Integer, ForeignKey("ledger_transactions.id"), nullable=True)
    raw_response_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    parent = relationship("User", foreign_keys=[parent_id])
    ledger_transaction = relationship("LedgerTransaction")


class ExternalPayout(Base):
    __tablename__ = "external_payouts"
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payout_method_id = Column(Integer, ForeignKey("merchant_payout_methods.id"), nullable=True)
    provider = Column(Enum(PaymentProvider), nullable=False)
    external_id = Column(String, nullable=True, index=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, default="ARS", nullable=False)
    status = Column(Enum(ExternalPayoutStatus), default=ExternalPayoutStatus.pending, nullable=False)
    ledger_transaction_id = Column(Integer, ForeignKey("ledger_transactions.id"), nullable=True)
    raw_response_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    merchant = relationship("User", foreign_keys=[merchant_id])
    payout_method = relationship("MerchantPayoutMethod")
    ledger_transaction = relationship("LedgerTransaction")


# --- ParentProfile and TrustedContact models ---

class ParentProfile(Base):
    __tablename__ = "parent_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    relationship_to_child = Column(String, nullable=True)  # father, mother, uncle, aunt, other
    home_address = Column(String, nullable=True)
    home_floor = Column(String, nullable=True)
    home_department = Column(String, nullable=True)
    home_postal = Column(String, nullable=True)
    home_phone = Column(String, nullable=True)
    mobile_phone = Column(String, nullable=True)
    country_code = Column(String, nullable=True)
    work_name = Column(String, nullable=True)
    work_address = Column(String, nullable=True)
    work_postal = Column(String, nullable=True)
    work_phone = Column(String, nullable=True)
    work_shift = Column(String, nullable=True)   # morning, afternoon, night, rotating
    work_hours = Column(String, nullable=True)   # e.g. "08:00-16:00"
    workplace = Column(String, nullable=True)
    email = Column(String, nullable=True)
    # Relationship
    user = relationship("User", backref="parent_profile", uselist=False)
    trusted_contacts = relationship("TrustedContact", back_populates="parent_profile", cascade="all, delete-orphan")

class TrustedContact(Base):
    __tablename__ = "emergency_contacts"  # DB table kept for backward compat
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
    parent_profile = relationship("ParentProfile", back_populates="trusted_contacts")


# Aliases for router compatibility
UserType = UserRole
Parent = User
Merchant = User
Bucket = WalletBucket
