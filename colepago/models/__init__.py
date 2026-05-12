from __future__ import annotations

import datetime
import enum
import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

load_dotenv()


class Base(DeclarativeBase):
    pass


class School(Base):
    __tablename__ = 'schools'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    source_year: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    sector: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    district_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    district_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    provincia: Mapped[str] = mapped_column(String, nullable=False)
    ciudad: Mapped[str] = mapped_column(String, nullable=False)
    comuna: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    low_grade: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    high_grade: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    locale_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    county_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class UserRole(enum.Enum):
    parent = 'parent'
    merchant = 'merchant'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    children: Mapped[list[Child]] = relationship('Child', back_populates='parent')
    temp_password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    temp_password_expires: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)


class Child(Base):
    __tablename__ = 'children'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    school_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    school_lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mobile_phone: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    school_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    school_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    shift: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    shift_start: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    shift_end: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    activities_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lives_with_parent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    home_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    home_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parent: Mapped[User] = relationship('User', back_populates='children')
    is_blocked: Mapped[int] = mapped_column(Integer, default=0)
    suspicious_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_merchants: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    wallet_buckets: Mapped[list[WalletBucket]] = relationship('WalletBucket', back_populates='child', cascade='all, delete-orphan')
    location_pings: Mapped[list[ChildLocationPing]] = relationship('ChildLocationPing', back_populates='child', cascade='all, delete-orphan', order_by='ChildLocationPing.recorded_at')
    route_waypoints: Mapped[list[ChildRouteWaypoint]] = relationship('ChildRouteWaypoint', back_populates='child', cascade='all, delete-orphan', order_by='ChildRouteWaypoint.seq')
    last_route_alert: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)


class ChildLocationPing(Base):
    __tablename__ = 'child_location_pings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey('children.id'), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    accel_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accel_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accel_z: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    child: Mapped[Child] = relationship('Child', back_populates='location_pings')


class ChildRouteWaypoint(Base):
    __tablename__ = 'child_route_waypoints'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey('children.id'), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    child: Mapped[Child] = relationship('Child', back_populates='route_waypoints')


class TransactionType(enum.Enum):
    fund = 'fund'
    spend = 'spend'
    settle = 'settle'
    transfer = 'transfer'


class LedgerOwnerType(enum.Enum):
    parent = 'parent'
    child = 'child'
    merchant = 'merchant'
    platform = 'platform'
    provider = 'provider'


class LedgerAccountType(enum.Enum):
    wallet = 'wallet'
    receivable = 'receivable'
    fee = 'fee'
    clearing = 'clearing'
    payout = 'payout'


class LedgerTransactionType(enum.Enum):
    deposit = 'deposit'
    child_purchase = 'child_purchase'
    merchant_payout = 'merchant_payout'
    refund = 'refund'
    adjustment = 'adjustment'


class LedgerTransactionStatus(enum.Enum):
    pending = 'pending'
    posted = 'posted'
    failed = 'failed'
    reversed = 'reversed'


class PaymentProvider(enum.Enum):
    mercadopago = 'mercadopago'
    stripe = 'stripe'
    bank_manual = 'bank_manual'


class ExternalPaymentStatus(enum.Enum):
    pending = 'pending'
    confirmed = 'confirmed'
    failed = 'failed'
    refunded = 'refunded'


class ExternalPayoutStatus(enum.Enum):
    pending = 'pending'
    processing = 'processing'
    paid = 'paid'
    failed = 'failed'


class WalletBucket(Base):
    __tablename__ = 'wallet_buckets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey('children.id'), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    allocated: Mapped[float] = mapped_column(Float, default=0.0)
    spent: Mapped[float] = mapped_column(Float, default=0.0)
    alert_threshold_pct: Mapped[int] = mapped_column(Integer, default=80)
    alert_sent: Mapped[int] = mapped_column(Integer, default=0)
    child: Mapped[Child] = relationship('Child', back_populates='wallet_buckets')

    @property
    def remaining(self) -> float:
        return max(self.allocated - self.spent, 0.0)

    @property
    def pct_used(self) -> int:
        if self.allocated <= 0:
            return 0
        return int(self.spent / self.allocated * 100)


class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    from_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    to_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    child_id: Mapped[Optional[int]] = mapped_column(ForeignKey('children.id'), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class LedgerAccount(Base):
    __tablename__ = 'ledger_accounts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_type: Mapped[LedgerOwnerType] = mapped_column(Enum(LedgerOwnerType), nullable=False)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    account_type: Mapped[LedgerAccountType] = mapped_column(Enum(LedgerAccountType), nullable=False)
    currency: Mapped[str] = mapped_column(String, default='ARS', nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    entries: Mapped[list[LedgerEntry]] = relationship('LedgerEntry', back_populates='account')


class LedgerTransaction(Base):
    __tablename__ = 'ledger_transactions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[LedgerTransactionType] = mapped_column(Enum(LedgerTransactionType), nullable=False)
    status: Mapped[LedgerTransactionStatus] = mapped_column(Enum(LedgerTransactionStatus), default=LedgerTransactionStatus.posted, nullable=False)
    external_reference: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    entries: Mapped[list[LedgerEntry]] = relationship('LedgerEntry', back_populates='transaction', cascade='all, delete-orphan')


class LedgerEntry(Base):
    __tablename__ = 'ledger_entries'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey('ledger_transactions.id'), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey('ledger_accounts.id'), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    transaction: Mapped[LedgerTransaction] = relationship('LedgerTransaction', back_populates='entries')
    account: Mapped[LedgerAccount] = relationship('LedgerAccount', back_populates='entries')


class MerchantPayoutMethod(Base):
    __tablename__ = 'merchant_payout_methods'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    provider: Mapped[PaymentProvider] = mapped_column(Enum(PaymentProvider), nullable=False)
    provider_account_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    label: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default='pending', nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    merchant: Mapped[User] = relationship('User')


class MerchantProfile(Base):
    __tablename__ = 'merchant_profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True, nullable=False)
    place_scope: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    business_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    personal_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mobile_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    transfer_account_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    transfer_account: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    transfer_account_alias: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    user: Mapped[User] = relationship('User', backref='merchant_profile', uselist=False)


class ExternalPayment(Base):
    __tablename__ = 'external_payments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    provider: Mapped[PaymentProvider] = mapped_column(Enum(PaymentProvider), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String, default='ARS', nullable=False)
    status: Mapped[ExternalPaymentStatus] = mapped_column(Enum(ExternalPaymentStatus), default=ExternalPaymentStatus.pending, nullable=False)
    ledger_transaction_id: Mapped[Optional[int]] = mapped_column(ForeignKey('ledger_transactions.id'), nullable=True)
    raw_response_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    confirmed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    parent: Mapped[User] = relationship('User', foreign_keys=[parent_id])
    ledger_transaction: Mapped[LedgerTransaction] = relationship('LedgerTransaction')


class ExternalPayout(Base):
    __tablename__ = 'external_payouts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    payout_method_id: Mapped[Optional[int]] = mapped_column(ForeignKey('merchant_payout_methods.id'), nullable=True)
    provider: Mapped[PaymentProvider] = mapped_column(Enum(PaymentProvider), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String, default='ARS', nullable=False)
    status: Mapped[ExternalPayoutStatus] = mapped_column(Enum(ExternalPayoutStatus), default=ExternalPayoutStatus.pending, nullable=False)
    ledger_transaction_id: Mapped[Optional[int]] = mapped_column(ForeignKey('ledger_transactions.id'), nullable=True)
    raw_response_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    paid_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    merchant: Mapped[User] = relationship('User', foreign_keys=[merchant_id])
    payout_method: Mapped[MerchantPayoutMethod] = relationship('MerchantPayoutMethod')
    ledger_transaction: Mapped[LedgerTransaction] = relationship('LedgerTransaction')


class ParentProfile(Base):
    __tablename__ = 'parent_profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True, nullable=False)
    relationship_to_child: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    children_using_colepago: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    home_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    home_floor: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    home_department: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    home_postal: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    home_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mobile_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_postal: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_shift: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_hours: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    workplace: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user: Mapped[User] = relationship('User', backref='parent_profile', uselist=False)
    trusted_contacts: Mapped[list[TrustedContact]] = relationship('TrustedContact', back_populates='parent_profile', cascade='all, delete-orphan')


class TrustedContact(Base):
    __tablename__ = 'emergency_contacts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parent_profile_id: Mapped[int] = mapped_column(ForeignKey('parent_profiles.id'), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    relation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    home_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parent_profile: Mapped[ParentProfile] = relationship('ParentProfile', back_populates='trusted_contacts')


UserType = UserRole
Parent = User
Merchant = User
Bucket = WalletBucket


_db_user = os.getenv('POSTGRES_USER', 'colepago')
_db_pass = os.getenv('POSTGRES_PASSWORD', 'colepago_pass')
_db_host = os.getenv('POSTGRES_HOST', 'localhost')
_db_port = os.getenv('POSTGRES_PORT', '5432')
_db_name = os.getenv('POSTGRES_DB', 'colepago')

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f'postgresql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}',
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
