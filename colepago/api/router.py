import os
import json
from typing import Any, Literal, Optional, cast
import secrets
import string
import datetime

import bcrypt
import mercadopago
import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr, SecretStr
from sqlalchemy.orm import Session

from models import Child, ExternalPayment, ExternalPaymentStatus, Merchant, MerchantPayoutMethod, MerchantProfile, Parent, ParentProfile, PaymentProvider, School, TrustedContact, User, UserType, WalletBucket, get_db, Transaction, TransactionType, ChildLocationPing, ChildRouteWaypoint
from email_utils import send_temp_password_email, send_alert_email
from whatsapp_utils import send_sms, send_whatsapp, send_whatsapp_template, make_voice_call
from geo_utils import is_payment_location_valid, is_rapid_spend, is_off_route
from services.payment_gateway import (
    cents_to_pesos,
    confirm_parent_deposit,
    create_pending_parent_deposit,
    create_merchant_payout_method,
    prepare_merchant_payout,
    pesos_to_cents,
    record_child_purchase,
    record_parent_deposit,
)
import services.admin_config

router = APIRouter()

COIN_CONVERSION_RATE = 1.0


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

load_dotenv()
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
stripe.api_key = STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
STRIPE_CURRENCY = os.getenv('STRIPE_CURRENCY', 'ars').lower()
MP_ACCESS_TOKEN = os.getenv('MP_ACCESS_TOKEN', '')
mp_client = mercadopago.SDK(MP_ACCESS_TOKEN) if MP_ACCESS_TOKEN else None
DEFAULT_ADMIN_EMAIL = 'diego.r.carloni@gmail.com'
ADMIN_EMAILS = {
    email.strip().lower()
    for email in os.getenv('ADMIN_EMAILS', DEFAULT_ADMIN_EMAIL).split(',')
    if email.strip()
}
ADMIN_USER_IDS = {
    user_id.strip()
    for user_id in os.getenv('ADMIN_USER_IDS', '').split(',')
    if user_id.strip()
}


def _is_admin_user(user: User | None) -> bool:
    if not user:
        return False
    return (
        str(user.id) in ADMIN_USER_IDS
        or (user.email or '').strip().lower() in ADMIN_EMAILS
    )


def _require_admin_user(user_id: Optional[int], db: Session) -> User:
    if not user_id:
        raise HTTPException(status_code=401, detail='Admin user id required')
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail='Admin user not found')
    if not _is_admin_user(user):
        raise HTTPException(status_code=403, detail='Admin access required')
    return cast(User, user)


class StripeTestRequest(BaseModel):
    parent_id: int
    amount_pesos: float = 100.0


class StripePaymentIntentRequest(BaseModel):
    parent_id: int
    amount_pesos: float


class AdminSettingsRequest(BaseModel):
    fee_percent: Optional[float] = None
    fee_payer: Optional[Literal['merchant', 'parent', 'split', 'school']] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    society_profile: Optional[str] = None
    religion_context: Optional[str] = None
    local_policy_notes: Optional[str] = None
    merchant_fee_disclosure: Optional[str] = None


class SpendRequest(BaseModel):
    child_id: int
    merchant_id: int
    amount: float
    pay_lat: Optional[float] = None
    pay_lon: Optional[float] = None


class SaleItemRequest(BaseModel):
    description: str
    quantity: float
    unit_price: float
    bucket_name: Optional[str] = None


class MerchantSaleRequest(BaseModel):
    merchant_id: int
    items: list[SaleItemRequest]
    note: Optional[str] = None


class ChildSalePaymentRequest(BaseModel):
    child_id: int
    bucket_name: str
    sale_payload: str
    pay_lat: Optional[float] = None
    pay_lon: Optional[float] = None


class ChildCreateRequest(BaseModel):
    parent_id: int
    full_name: str
    mobile_phone: str
    school_id: Optional[str] = None
    school_name: str
    shift: str
    shift_start: str
    shift_end: str
    activities: list[dict] = []
    lives_with_parent: bool = True
    home_address: Optional[str] = None
    home_phone: Optional[str] = None


class FundWalletRequest(BaseModel):
    parent_id: int
    amount_pesos: float
    payment_method: Literal['mercadopago', 'bank_transfer', 'stripe_card']
    mp_token: Optional[SecretStr] = None
    bank_account: Optional[SecretStr] = None
    stripe_payment_method_id: Optional[str] = None


class BucketAllocationRequest(BaseModel):
    name: str
    amount: float
    alert_threshold_pct: Optional[int] = None


class WalletAllocationRequest(BaseModel):
    parent_id: int
    child_id: int
    amount_pesos: float
    buckets: list[BucketAllocationRequest] = []


class BucketThresholdRequest(BaseModel):
    name: str
    alert_threshold_pct: int


class WalletThresholdRequest(BaseModel):
    parent_id: int
    default_threshold_pct: Optional[int] = None
    buckets: list[BucketThresholdRequest] = []


class MerchantPayoutMethodRequest(BaseModel):
    provider: Literal['mercadopago', 'stripe', 'bank_manual']
    provider_account_id: Optional[str] = None
    label: Optional[str] = None
    metadata_json: Optional[str] = None


class MerchantPayoutRequest(BaseModel):
    payout_method_id: int
    amount_pesos: float


class MerchantProfileRequest(BaseModel):
    place_scope: Optional[Literal['inside_school', 'outside_school']] = None
    business_name: Optional[str] = None
    address: Optional[str] = None
    personal_name: Optional[str] = None
    mobile_phone: Optional[str] = None
    country_code: Optional[str] = None
    transfer_account_type: Optional[Literal['CVU', 'CBU']] = None
    transfer_account: Optional[str] = None
    transfer_account_alias: Optional[str] = None


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal['parent', 'merchant']
    username: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class KidLoginRequest(BaseModel):
    parent_email: EmailStr
    parent_password: str
    child_mobile_phone: str


def _auth_payload(user: User) -> dict:
    token = secrets.token_urlsafe(32)
    role = user.role.value if hasattr(user.role, 'value') else user.role
    return {
        'access_token': token,
        'token': token,
        'token_type': 'bearer',
        'id': user.id,
        'user_id': user.id,
        # Kept for the current Flutter app, which still names the id parent_id.
        'parent_id': user.id,
        'role': role,
        'name': user.name,
        'email': user.email,
        'is_admin': _is_admin_user(user),
    }


@router.get('/ping')
async def ping():
    return {'msg': 'pong'}


@router.get('/')
async def api_root():
    return {
        'service': 'ColePago API',
        'status': 'ok',
        'ping': '/api/ping',
        'docs': '/docs',
    }


@router.post('/auth/register')
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    username = data.username.strip() if data.username else None
    if username and db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail='Username already registered')

    if data.role == 'parent':
        if db.query(Parent).filter(Parent.email == data.email).first():
            raise HTTPException(status_code=400, detail='Email already registered')
        user = Parent(
            name=data.name,
            username=username,
            email=data.email,
            password_hash=hash_password(data.password),
            role=UserType.parent,
        )
    else:
        if db.query(Merchant).filter(Merchant.email == data.email).first():
            raise HTTPException(status_code=400, detail='Email already registered')
        user = Merchant(
            name=data.name,
            username=username,
            email=data.email,
            password_hash=hash_password(data.password),
            role=UserType.merchant,
        )

    db.add(user)
    db.commit()
    db.refresh(user)
    payload = _auth_payload(user)
    payload['msg'] = 'Registration successful'
    return payload


@router.post('/auth/login')
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, cast(str, user.password_hash)):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    return _auth_payload(user)


@router.post('/auth/kid-login')
def kid_login(data: KidLoginRequest, db: Session = Depends(get_db)):
    parent = (
        db.query(Parent)
        .filter(Parent.email == data.parent_email, Parent.role == UserType.parent)
        .first()
    )
    if not parent or not verify_password(data.parent_password, cast(str, parent.password_hash)):
        raise HTTPException(status_code=401, detail='Invalid parent credentials')

    normalized_mobile_phone = ''.join(
        ch for ch in data.child_mobile_phone.strip() if ch.isdigit() or ch == '+'
    )
    child = (
        db.query(Child)
        .filter(Child.parent_id == parent.id, Child.mobile_phone == normalized_mobile_phone)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail='Child phone not found for parent')

    token = secrets.token_urlsafe(32)
    return {
        'access_token': token,
        'token': token,
        'token_type': 'bearer',
        'role': 'kid',
        'kid_id': child.id,
        'child_id': child.id,
        'parent_id': parent.id,
        'name': child.name,
        'mobile_phone': child.mobile_phone,
    }


@router.post('/wallet/fund')
def fund_wallet(data: FundWalletRequest, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.id == data.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')
    if data.amount_pesos <= 0:
        raise HTTPException(status_code=400, detail='Amount must be positive')

    provider = PaymentProvider.bank_manual
    external_id = None
    if data.payment_method == 'mercadopago':
        if mp_client is None:
            raise HTTPException(status_code=500, detail='Mercado Pago not configured')
        if not data.mp_token:
            raise HTTPException(status_code=400, detail='Mercado Pago token required')
        provider = PaymentProvider.mercadopago
        external_id = 'mercadopago_pending'
    elif data.payment_method == 'stripe_card':
        if not STRIPE_SECRET_KEY:
            raise HTTPException(status_code=500, detail='Stripe not configured')
        raise HTTPException(
            status_code=400,
            detail='Use /wallet/stripe/create-payment-intent for Stripe card deposits',
        )
    elif data.payment_method == 'bank_transfer' and not data.bank_account:
        raise HTTPException(status_code=400, detail='Bank transfer details required')

    try:
        payment = record_parent_deposit(
            db,
            parent=parent,
            amount_pesos=data.amount_pesos * COIN_CONVERSION_RATE,
            provider=provider,
            external_id=external_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    db.refresh(parent)
    return {
        'msg': 'Wallet funded successfully',
        'external_payment_id': payment.id,
        'ledger_transaction_id': payment.ledger_transaction_id,
        'coins_added': cents_to_pesos(cast(int, payment.amount_cents)),
        'new_balance': parent.balance,
    }


@router.get('/payments/stripe/config')
def stripe_payment_config():
    if not STRIPE_PUBLISHABLE_KEY:
        raise HTTPException(status_code=500, detail='Stripe publishable key not configured')
    return {
        'publishable_key': STRIPE_PUBLISHABLE_KEY,
        'currency': STRIPE_CURRENCY,
    }


@router.post('/wallet/stripe/create-payment-intent')
def create_stripe_wallet_payment_intent(data: StripePaymentIntentRequest, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.id == data.parent_id, Parent.role == UserType.parent).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')
    if data.amount_pesos <= 0:
        raise HTTPException(status_code=400, detail='Amount must be positive')
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail='Stripe not configured')

    amount_cents = pesos_to_cents(data.amount_pesos * COIN_CONVERSION_RATE)
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=STRIPE_CURRENCY,
            automatic_payment_methods={'enabled': True},
            metadata={
                'parent_id': str(parent.id),
                'purpose': 'parent_wallet_deposit',
            },
        )
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        raw_response = json.dumps(cast(dict[str, Any], intent.to_dict()))
    except Exception:
        raw_response = json.dumps({'id': intent.id, 'status': intent.status})

    payment = create_pending_parent_deposit(
        db,
        parent=parent,
        amount_pesos=data.amount_pesos * COIN_CONVERSION_RATE,
        provider=PaymentProvider.stripe,
        external_id=intent.id,
        raw_response_json=raw_response,
    )
    db.commit()
    return {
        'payment_id': payment.id,
        'payment_intent_id': intent.id,
        'client_secret': intent.client_secret,
        'amount_cents': amount_cents,
        'currency': STRIPE_CURRENCY,
        'status': intent.status,
    }


@router.post('/webhooks/stripe')
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get('stripe-signature')

    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=STRIPE_WEBHOOK_SECRET,
            )
        else:
            event = json.loads(payload.decode('utf-8'))
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid Stripe payload')
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail='Invalid Stripe signature')

    if isinstance(event, dict):
        raw_event = event
    else:
        raw_event = cast(dict[str, Any], event.to_dict())

    event_type = raw_event.get('type')
    data_object = cast(dict[str, Any], raw_event.get('data', {}).get('object', {}))
    intent_id = data_object.get('id')
    raw_response = json.dumps(raw_event)

    if event_type == 'payment_intent.succeeded':
        payment = (
            db.query(ExternalPayment)
            .filter(
                ExternalPayment.provider == PaymentProvider.stripe,
                ExternalPayment.external_id == intent_id,
            )
            .first()
        )
        if not payment:
            raise HTTPException(status_code=404, detail='Stripe payment not found')
        try:
            payment = confirm_parent_deposit(db, payment, raw_response_json=raw_response)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        db.commit()
        return {
            'received': True,
            'event': event_type,
            'payment_id': payment.id,
            'status': payment.status.value,
            'ledger_transaction_id': payment.ledger_transaction_id,
        }

    if event_type == 'payment_intent.payment_failed':
        payment = (
            db.query(ExternalPayment)
            .filter(
                ExternalPayment.provider == PaymentProvider.stripe,
                ExternalPayment.external_id == intent_id,
            )
            .first()
        )
        if payment and payment.status == ExternalPaymentStatus.pending:
            payment.status = ExternalPaymentStatus.failed
            payment.raw_response_json = raw_response
            db.commit()
        return {'received': True, 'event': event_type}

    return {'received': True, 'event': event_type, 'ignored': True}


@router.get('/payments/{payment_id}')
def get_external_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(ExternalPayment).filter(ExternalPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail='Payment not found')
    return {
        'id': payment.id,
        'parent_id': payment.parent_id,
        'provider': payment.provider.value,
        'external_id': payment.external_id,
        'amount': cents_to_pesos(cast(int, payment.amount_cents)),
        'currency': payment.currency,
        'status': payment.status.value,
        'ledger_transaction_id': payment.ledger_transaction_id,
        'confirmed_at': payment.confirmed_at.isoformat() if payment.confirmed_at else None,
    }


@router.get('/admin/settings')
def get_admin_settings(
    x_user_id: Optional[int] = Header(None, alias='X-User-Id'),
    db: Session = Depends(get_db),
):
    _require_admin_user(x_user_id, db)
    return services.admin_config.load_admin_settings()


@router.put('/admin/settings')
def update_admin_settings(
    data: AdminSettingsRequest,
    x_user_id: Optional[int] = Header(None, alias='X-User-Id'),
    db: Session = Depends(get_db),
):
    admin = _require_admin_user(x_user_id, db)
    payload = data.model_dump(exclude_unset=True)
    if 'fee_percent' in payload:
        fee_percent = payload['fee_percent']
        if fee_percent is None or fee_percent < 0 or fee_percent > 25:
            raise HTTPException(status_code=400, detail='Fee percent must be between 0 and 25')
    if 'currency' in payload and payload['currency']:
        payload['currency'] = payload['currency'].upper()
    settings = services.admin_config.save_admin_settings(payload, updated_by=admin.email)
    return {'msg': 'Admin settings saved', 'settings': settings}


@router.post('/wallet/allocate')
def allocate_wallet_to_child(data: WalletAllocationRequest, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.id == data.parent_id, Parent.role == UserType.parent).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')
    child = db.query(Child).filter(Child.id == data.child_id, Child.parent_id == parent.id).first()
    if not child:
        raise HTTPException(status_code=404, detail='Child not found for parent')
    if data.amount_pesos <= 0:
        raise HTTPException(status_code=400, detail='Amount must be positive')
    if (parent.balance or 0) < data.amount_pesos:
        raise HTTPException(status_code=400, detail='Insufficient parent wallet balance')

    buckets = data.buckets or [BucketAllocationRequest(name='General', amount=data.amount_pesos)]
    clean_buckets: list[BucketAllocationRequest] = []
    for bucket in buckets:
        name = bucket.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail='Bucket name is required')
        if bucket.amount <= 0:
            continue
        clean_buckets.append(BucketAllocationRequest(name=name, amount=bucket.amount))

    allocated_total = round(sum(bucket.amount for bucket in clean_buckets), 2)
    requested_total = round(data.amount_pesos, 2)
    if allocated_total != requested_total:
        raise HTTPException(
            status_code=400,
            detail='Bucket amounts must equal the amount being applied to the child',
        )

    parent.balance = (parent.balance or 0) - allocated_total
    child.balance = (child.balance or 0) + allocated_total

    for bucket_data in clean_buckets:
        bucket = (
            db.query(WalletBucket)
            .filter(WalletBucket.child_id == child.id, WalletBucket.name == bucket_data.name)
            .first()
        )
        if not bucket:
            bucket = WalletBucket(child_id=child.id, name=bucket_data.name)
            db.add(bucket)
        bucket.allocated = (bucket.allocated or 0) + bucket_data.amount
        if bucket_data.alert_threshold_pct is not None:
            if bucket_data.alert_threshold_pct < 1 or bucket_data.alert_threshold_pct > 100:
                raise HTTPException(status_code=400, detail='Alert threshold must be between 1 and 100')
            bucket.alert_threshold_pct = bucket_data.alert_threshold_pct
        bucket.alert_sent = 0

    db.add(
        Transaction(
            from_id=parent.id,
            to_id=child.id,
            child_id=child.id,
            amount=allocated_total,
            type=TransactionType.transfer,
            description='Parent wallet allocation to child buckets',
        )
    )
    db.commit()
    db.refresh(parent)
    db.refresh(child)
    return {
        'msg': 'Money applied to child buckets',
        'parent_balance': parent.balance,
        'child_balance': child.balance,
        'allocated': allocated_total,
    }


@router.put('/child/{child_id}/wallet_buckets/thresholds')
def update_child_wallet_thresholds(
    child_id: int,
    data: WalletThresholdRequest,
    db: Session = Depends(get_db),
):
    parent = db.query(Parent).filter(Parent.id == data.parent_id, Parent.role == UserType.parent).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')
    child = db.query(Child).filter(Child.id == child_id, Child.parent_id == parent.id).first()
    if not child:
        raise HTTPException(status_code=404, detail='Child not found for parent')

    def validate_threshold(value: int) -> int:
        if value < 1 or value > 100:
            raise HTTPException(status_code=400, detail='Alert threshold must be between 1 and 100')
        return value

    default_threshold = (
        validate_threshold(data.default_threshold_pct)
        if data.default_threshold_pct is not None
        else None
    )
    named_thresholds = {
        item.name.strip(): validate_threshold(item.alert_threshold_pct)
        for item in data.buckets
        if item.name.strip()
    }

    updated = []
    for bucket in child.wallet_buckets:
        next_threshold = named_thresholds.get(bucket.name, default_threshold)
        if next_threshold is None:
            continue
        bucket.alert_threshold_pct = next_threshold
        bucket.alert_sent = 0
        updated.append({
            'id': bucket.id,
            'name': bucket.name,
            'alert_threshold_pct': bucket.alert_threshold_pct,
        })

    db.commit()
    return {
        'msg': 'Bucket thresholds saved',
        'updated': updated,
    }


@router.get('/parent/{parent_id}/wallet_summary')
def parent_wallet_summary(parent_id: int, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.id == parent_id, Parent.role == UserType.parent).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')
    children = db.query(Child).filter(Child.parent_id == parent.id).all()
    return {
        'parent_balance': parent.balance or 0,
        'children_balance': sum(child.balance or 0 for child in children),
        'children_count': len(children),
    }


@router.get('/parent/{parent_id}/dashboard_economy')
def parent_dashboard_economy(parent_id: int, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.id == parent_id, Parent.role == UserType.parent).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')

    now = datetime.datetime.utcnow()
    since_7 = now - datetime.timedelta(days=7)
    since_30 = now - datetime.timedelta(days=30)
    children = db.query(Child).filter(Child.parent_id == parent.id).order_by(Child.id).all()
    child_rows = []

    for child in children:
        buckets = []
        total_remaining = 0.0
        affected_buckets = []
        for bucket in child.wallet_buckets:
            remaining = round(bucket.remaining, 2)
            allocated = round(bucket.allocated or 0, 2)
            spent = round(bucket.spent or 0, 2)
            threshold = bucket.alert_threshold_pct or 80
            pct_used = bucket.pct_used
            total_remaining += remaining
            if allocated > 0 and pct_used >= threshold:
                affected_buckets.append(bucket.name)
            buckets.append({
                'id': bucket.id,
                'name': bucket.name,
                'allocated': allocated,
                'spent': spent,
                'remaining': remaining,
                'pct_used': pct_used,
                'alert_threshold_pct': threshold,
                'status': 'warning' if allocated > 0 and pct_used >= threshold else 'ok',
            })

        spend_7 = (
            db.query(Transaction)
            .filter(
                Transaction.child_id == child.id,
                Transaction.type == TransactionType.spend,
                Transaction.timestamp >= since_7,
            )
            .all()
        )
        spend_30 = (
            db.query(Transaction)
            .filter(
                Transaction.child_id == child.id,
                Transaction.type == TransactionType.spend,
                Transaction.timestamp >= since_30,
            )
            .all()
        )
        spend_7_total = round(sum(txn.amount or 0 for txn in spend_7), 2)
        spend_30_total = round(sum(txn.amount or 0 for txn in spend_30), 2)
        daily_spend_rate = round(spend_7_total / 7, 2)
        days_left = None
        if daily_spend_rate > 0:
            days_left = round(total_remaining / daily_spend_rate, 1)

        child_rows.append({
            'id': child.id,
            'name': child.name,
            'balance': round(child.balance or 0, 2),
            'total_remaining': round(total_remaining, 2),
            'spend_7_days': spend_7_total,
            'spend_30_days': spend_30_total,
            'daily_spend_rate': daily_spend_rate,
            'estimated_days_left': days_left,
            'affected_buckets': affected_buckets,
            'buckets': buckets,
        })

    return {
        'parent_balance': round(parent.balance or 0, 2),
        'children_balance': round(sum(child.balance or 0 for child in children), 2),
        'children': child_rows,
    }


@router.get('/parent/{parent_id}/children')
def get_parent_children(parent_id: int, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.id == parent_id, Parent.role == UserType.parent).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')
    children = db.query(Child).filter(Child.parent_id == parent.id).order_by(Child.id).all()
    return [
        {
            'id': child.id,
            'name': child.name,
            'mobile_phone': child.mobile_phone,
            'school_id': child.school_id,
            'school_name': child.school_name,
            'shift': child.shift,
            'shift_start': child.shift_start,
            'shift_end': child.shift_end,
            'activities': json.loads(child.activities_json or '[]'),
            'balance': child.balance or 0,
            'lives_with_parent': child.lives_with_parent,
            'home_address': child.home_address,
            'home_phone': child.home_phone,
        }
        for child in children
    ]


@router.get('/parent/{parent_id}/wallet_buckets')
def get_parent_wallet_buckets(parent_id: int, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.id == parent_id, Parent.role == UserType.parent).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')
    totals: dict[str, float] = {}
    children = db.query(Child).filter(Child.parent_id == parent.id).all()
    for child in children:
        for bucket in child.wallet_buckets:
            totals[bucket.name] = totals.get(bucket.name, 0) + (bucket.remaining or 0)
    return totals


@router.get('/child/{child_id}/wallet_buckets')
def get_child_wallet_buckets(child_id: int, db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail='Child not found')
    return [
        {
            'id': bucket.id,
            'name': bucket.name,
            'allocated': bucket.allocated or 0,
            'spent': bucket.spent or 0,
            'remaining': bucket.remaining,
            'alert_threshold_pct': bucket.alert_threshold_pct,
        }
        for bucket in child.wallet_buckets
    ]


@router.get('/child/{child_id}/transactions')
def get_child_transactions(child_id: int, db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail='Child not found')
    transactions = (
        db.query(Transaction)
        .filter(Transaction.child_id == child.id)
        .order_by(Transaction.timestamp.desc())
        .limit(50)
        .all()
    )
    return [
        {
            'id': txn.id,
            'childId': child.id,
            'amount': txn.amount,
            'type': txn.type.value if hasattr(txn.type, 'value') else str(txn.type),
            'desc': txn.description or '',
            'date': txn.timestamp.isoformat() if txn.timestamp else '',
        }
        for txn in transactions
    ]


@router.get('/geo/provinces')
def get_school_provinces(db: Session = Depends(get_db)):
    rows = (
        db.query(School.provincia)
        .filter(School.provincia.isnot(None), School.provincia != '')
        .distinct()
        .order_by(School.provincia)
        .all()
    )
    return {'provinces': [row[0] for row in rows]}


@router.get('/geo/cities')
def get_school_cities(province: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(School.ciudad).filter(School.ciudad.isnot(None), School.ciudad != '')
    if province:
        query = query.filter(School.provincia == province)
    rows = query.distinct().order_by(School.ciudad).limit(1000).all()
    return {'cities': [row[0] for row in rows]}


@router.get('/geo/neighborhoods')
def get_school_neighborhoods(
    city: str,
    province: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(School.comuna)
        .filter(School.ciudad == city, School.comuna.isnot(None), School.comuna != '')
    )
    if province:
        query = query.filter(School.provincia == province)
    rows = query.distinct().order_by(School.comuna).limit(1000).all()
    return {'neighborhoods': [row[0] for row in rows]}


@router.get('/geo/schools')
def get_schools(
    city: str,
    province: Optional[str] = None,
    neighborhood: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(School).filter(School.ciudad == city)
    if province:
        query = query.filter(School.provincia == province)
    if neighborhood:
        query = query.filter(School.comuna == neighborhood)
    schools = query.order_by(School.name).limit(200).all()
    return {
        'schools': [
            {
                'id': str(school.id),
                'name': school.name,
                'province': school.provincia,
                'city': school.ciudad,
                'neighborhood': school.comuna,
                'address': school.address,
                'phone': school.phone,
                'email': '',
            }
            for school in schools
        ]
    }


@router.post('/wallet/test-stripe')
def test_stripe_payment(data: StripeTestRequest, db: Session = Depends(get_db)):
    if os.getenv('ENV', 'development').lower() == 'production':
        raise HTTPException(status_code=403, detail='This endpoint is disabled in production')
    parent = db.query(Parent).filter(Parent.id == data.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail='Stripe not configured')
    return {'msg': 'Stripe configured', 'amount': data.amount_pesos}


@router.post('/parent/add-child')
def add_child(data: ChildCreateRequest, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.id == data.parent_id, Parent.role == UserType.parent).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')

    name = data.full_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail='Child name is required')

    mobile_phone = data.mobile_phone.strip()
    normalized_mobile_phone = ''.join(
        ch for ch in mobile_phone if ch.isdigit() or ch == '+'
    )
    if not normalized_mobile_phone:
        raise HTTPException(status_code=400, detail='Child phone number is required')
    existing_child_phone = (
        db.query(Child)
        .filter(Child.mobile_phone == normalized_mobile_phone)
        .first()
    )
    if existing_child_phone:
        raise HTTPException(status_code=400, detail='Child phone number is already used')

    school_name = data.school_name.strip()
    if not school_name:
        raise HTTPException(status_code=400, detail='School attending is required')
    shift = data.shift.strip()
    if not shift:
        raise HTTPException(status_code=400, detail='Shift is required')
    shift_start = data.shift_start.strip()
    shift_end = data.shift_end.strip()
    if not shift_start or not shift_end:
        raise HTTPException(status_code=400, detail='Shift hours are required')

    activities = []
    for activity in data.activities:
        if not isinstance(activity, dict):
            continue
        name = str(activity.get('name') or '').strip()
        activity_type = str(activity.get('type') or '').strip()
        period = str(activity.get('period') or '').strip()
        if not name and not activity_type:
            continue
        activities.append({
            'period': period,
            'type': activity_type,
            'name': name,
            'start': str(activity.get('start') or '').strip(),
            'end': str(activity.get('end') or '').strip(),
            'address': str(activity.get('address') or '').strip(),
            'institution': str(activity.get('institution') or '').strip(),
            'phone': str(activity.get('phone') or '').strip(),
            'professor': str(activity.get('professor') or '').strip(),
        })

    home_address = data.home_address
    home_phone = data.home_phone
    if data.lives_with_parent:
        profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent.id).first()
        if profile:
            home_address = profile.home_address
            home_phone = profile.home_phone
    elif not home_address:
        raise HTTPException(status_code=400, detail='Child home address is required')

    child = Child(
        name=name,
        parent_id=parent.id,
        mobile_phone=normalized_mobile_phone,
        school_id=data.school_id,
        school_name=school_name,
        shift=shift,
        shift_start=shift_start,
        shift_end=shift_end,
        activities_json=json.dumps(activities),
        lives_with_parent=data.lives_with_parent,
        home_address=home_address,
        home_phone=home_phone,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return {
        'msg': 'Child added',
        'child_id': child.id,
        'name': child.name,
        'mobile_phone': child.mobile_phone,
        'school_id': child.school_id,
        'school_name': child.school_name,
        'shift': child.shift,
        'shift_start': child.shift_start,
        'shift_end': child.shift_end,
        'activities': activities,
        'lives_with_parent': child.lives_with_parent,
        'home_address': child.home_address,
        'home_phone': child.home_phone,
    }


@router.post('/child/spend')
def child_spend(data: SpendRequest, db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == data.child_id).first()
    merchant = (
        db.query(Merchant)
        .filter(Merchant.id == data.merchant_id, Merchant.role == UserType.merchant)
        .first()
    )
    if not child or not merchant:
        raise HTTPException(status_code=404, detail='Child or merchant not found')
    parent = child.parent
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')
    if child.is_blocked:
        raise HTTPException(status_code=403, detail='Account blocked')
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail='Amount must be positive')

    # ── Geo-fence check ──────────────────────────────────────────────
    # If the child has a school location set, payment must originate
    # within ~3 blocks (0.4 km) of the school OR at the merchant.
    # If no location is sent and a school is configured, deny the payment.
    has_school = child.school_lat is not None and child.school_lon is not None
    if has_school:
        if data.pay_lat is None or data.pay_lon is None:
            raise HTTPException(
                status_code=403,
                detail='Location required: payment must be made at or near school'
            )
        if not is_payment_location_valid(child, merchant, data.pay_lat, data.pay_lon, db):
            raise HTTPException(
                status_code=403,
                detail='Payment declined: too far from school (allowed within ~3 blocks)'
            )

    # ── Anti-theft: rapid-spend detection ────────────────────────────
    # If >= 3 purchases happen within 5 minutes, block the account and
    # immediately alert the parent (possible phone theft).
    if is_rapid_spend(child, db):
        child.is_blocked = 1
        child.suspicious_reason = 'Auto-blocked: rapid consecutive purchases (possible theft)'
        db.commit()
        # Fire alert in background (non-blocking)
        _fire_theft_alert(child, db)
        raise HTTPException(
            status_code=403,
            detail='Account auto-blocked: too many purchases in a short time. Parent has been alerted.'
        )

    try:
        ledger_txn = record_child_purchase(
            db,
            parent=parent,
            merchant=merchant,
            child_id=child.id,
            amount_pesos=data.amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Record transaction for future rapid-spend queries
    txn = Transaction(
        from_id=parent.id,
        to_id=merchant.id,
        child_id=child.id,
        amount=data.amount,
        type=TransactionType.spend,
        description=f'Child {child.id} purchase confirmed by merchant {merchant.id}',
    )
    db.add(txn)
    db.commit()
    db.refresh(parent)
    db.refresh(merchant)
    return {
        'msg': 'Payment successful',
        'ledger_transaction_id': ledger_txn.id,
        'parent_balance': parent.balance,
        'merchant_balance': merchant.balance,
    }


def _notify_parent_bucket_status(
    db: Session,
    parent: User,
    child: Child,
    affected_buckets: list[WalletBucket],
    borrowed_parts: list[dict],
) -> dict:
    unique_buckets = []
    seen_names = set()
    for bucket in affected_buckets:
        if bucket.name in seen_names:
            continue
        seen_names.add(bucket.name)
        unique_buckets.append(bucket)

    threshold_buckets = [
        bucket
        for bucket in unique_buckets
        if bucket.allocated and bucket.pct_used >= (bucket.alert_threshold_pct or 80)
        and not bucket.alert_sent
    ]
    should_notify = bool(borrowed_parts or threshold_buckets)
    if not should_notify:
        return {'sent': False, 'reason': 'not_needed'}

    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent.id).first()
    if not profile or not profile.mobile_phone:
        return {'sent': False, 'reason': 'parent_mobile_missing'}

    bucket_lines = [
        f"{bucket.name}: remaining {bucket.remaining:.2f}, used {bucket.pct_used}% "
        f"(threshold {bucket.alert_threshold_pct or 80}%)"
        for bucket in unique_buckets
    ]
    borrowed_lines = [
        f"{part['amount']:.2f} borrowed from {part['from_bucket']} for {part['for_bucket']}"
        for part in borrowed_parts
    ]
    message = (
        f"ColePago alert: {child.name} completed a purchase and one or more buckets "
        f"need attention.\nAffected buckets:\n- " + "\n- ".join(bucket_lines)
    )
    if borrowed_lines:
        message += "\nBorrowing used:\n- " + "\n- ".join(borrowed_lines)

    try:
        sid = send_whatsapp(profile.mobile_phone, profile.country_code or '', message)
        for bucket in threshold_buckets:
            bucket.alert_sent = 1
        return {'sent': True, 'sid': sid, 'affected_buckets': [bucket.name for bucket in unique_buckets]}
    except Exception as exc:
        return {'sent': False, 'reason': str(exc), 'affected_buckets': [bucket.name for bucket in unique_buckets]}


@router.post('/merchant/sales/qr')
def create_merchant_sale_qr(data: MerchantSaleRequest, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == data.merchant_id, Merchant.role == UserType.merchant).first()
    if not merchant:
        raise HTTPException(status_code=404, detail='Merchant not found')
    clean_items = []
    total = 0.0
    for item in data.items:
        description = item.description.strip()
        if not description:
            raise HTTPException(status_code=400, detail='Item description is required')
        if item.quantity <= 0 or item.unit_price <= 0:
            raise HTTPException(status_code=400, detail='Item quantity and price must be positive')
        line_total = round(item.quantity * item.unit_price, 2)
        total += line_total
        clean_items.append({
            'description': description,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'line_total': line_total,
            'bucket_name': item.bucket_name.strip() if item.bucket_name else None,
        })
    if not clean_items:
        raise HTTPException(status_code=400, detail='At least one item is required')
    sale = {
        'type': 'colepago_merchant_sale',
        'merchant_id': merchant.id,
        'merchant_name': merchant.name,
        'merchant_address': merchant.address,
        'items': clean_items,
        'total': round(total, 2),
        'note': data.note,
        'created_at': datetime.datetime.utcnow().isoformat(),
    }
    payload = json.dumps(sale, separators=(',', ':'))
    return {
        'msg': 'Sale QR payload created',
        'sale': sale,
        'qr_payload': payload,
    }


@router.post('/child/pay-sale')
def child_pay_sale(data: ChildSalePaymentRequest, db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == data.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail='Child not found')
    try:
        sale = json.loads(data.sale_payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid sale QR payload')
    if sale.get('type') != 'colepago_merchant_sale':
        raise HTTPException(status_code=400, detail='QR is not a ColePago sale')
    merchant_id = int(sale.get('merchant_id') or 0)
    total = float(sale.get('total') or 0)
    if total <= 0:
        raise HTTPException(status_code=400, detail='Sale total must be positive')
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id, Merchant.role == UserType.merchant).first()
    if not merchant:
        raise HTTPException(status_code=404, detail='Merchant not found')
    parent = child.parent
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')

    selected_bucket_name = data.bucket_name.strip()
    if not selected_bucket_name:
        raise HTTPException(status_code=400, detail='Selected bucket is required')

    bucket_map = {bucket.name: bucket for bucket in child.wallet_buckets}
    if selected_bucket_name not in bucket_map:
        raise HTTPException(status_code=404, detail='Selected bucket not found')

    items = sale.get('items') or []
    if not isinstance(items, list) or not items:
        raise HTTPException(status_code=400, detail='Sale must include item details')
    if sum(bucket.remaining for bucket in bucket_map.values()) < total:
        raise HTTPException(status_code=400, detail='Not enough money across child buckets')

    payment_parts = []
    borrowed_parts = []
    affected_buckets: list[WalletBucket] = []
    planned_spend: dict[int, float] = {}

    def available(bucket: WalletBucket) -> float:
        return max(bucket.remaining - planned_spend.get(bucket.id, 0), 0)

    def add_part(bucket: WalletBucket, amount: float, target_name: str, borrowed: bool):
        clean_amount = round(amount, 2)
        if clean_amount <= 0:
            return
        planned_spend[bucket.id] = planned_spend.get(bucket.id, 0) + clean_amount
        payment_parts.append({'bucket': bucket, 'amount': clean_amount})
        affected_buckets.append(bucket)
        if borrowed:
            borrowed_parts.append({
                'from_bucket': bucket.name,
                'for_bucket': target_name,
                'amount': clean_amount,
            })

    calculated_total = 0.0
    for item in items:
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail='Sale item format is invalid')
        item_amount = float(item.get('line_total') or 0)
        if item_amount <= 0:
            item_amount = float(item.get('quantity') or 0) * float(item.get('unit_price') or 0)
        item_amount = round(item_amount, 2)
        if item_amount <= 0:
            raise HTTPException(status_code=400, detail='Sale item total must be positive')
        calculated_total = round(calculated_total + item_amount, 2)

        target_name = str(item.get('bucket_name') or selected_bucket_name).strip() or selected_bucket_name
        target_bucket = bucket_map.get(target_name)
        if not target_bucket:
            raise HTTPException(status_code=404, detail=f'Bucket not found for item: {target_name}')

        remaining = item_amount
        direct_amount = min(available(target_bucket), remaining)
        add_part(target_bucket, direct_amount, target_name, borrowed=False)
        remaining = round(remaining - direct_amount, 2)

        if remaining > 0:
            candidates = sorted(
                [bucket for bucket in bucket_map.values() if bucket.name != target_bucket.name and available(bucket) > 0],
                key=available,
                reverse=True,
            )
            for candidate in candidates:
                borrowed_amount = min(available(candidate), remaining)
                add_part(candidate, borrowed_amount, target_name, borrowed=True)
                remaining = round(remaining - borrowed_amount, 2)
                if remaining <= 0:
                    break

        if remaining > 0:
            raise HTTPException(status_code=400, detail=f'Not enough money for item bucket: {target_name}')

    if abs(calculated_total - total) > 0.01:
        raise HTTPException(status_code=400, detail='Sale item total does not match QR total')

    try:
        ledger_txn = record_child_purchase(
            db,
            parent=parent,
            merchant=merchant,
            child_id=child.id,
            amount_pesos=total,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    for part in payment_parts:
        part['bucket'].spent = (part['bucket'].spent or 0) + part['amount']

    notification = _notify_parent_bucket_status(
        db,
        parent=parent,
        child=child,
        affected_buckets=affected_buckets,
        borrowed_parts=borrowed_parts,
    )

    txn = Transaction(
        from_id=parent.id,
        to_id=merchant.id,
        child_id=child.id,
        amount=total,
        type=TransactionType.spend,
        description=(
            f"QR sale paid from buckets: "
            f"{json.dumps([{'bucket': part['bucket'].name, 'amount': part['amount']} for part in payment_parts])}; "
            f"items: {json.dumps(items)}"
        ),
    )
    db.add(txn)
    db.commit()
    db.refresh(parent)
    db.refresh(merchant)
    return {
        'msg': 'Payment successful',
        'ledger_transaction_id': ledger_txn.id,
        'bucket_remaining': bucket_map[selected_bucket_name].remaining,
        'bucket_debits': [
            {'bucket_name': part['bucket'].name, 'amount': part['amount'], 'remaining': part['bucket'].remaining}
            for part in payment_parts
        ],
        'borrowed_from_buckets': borrowed_parts,
        'parent_notification': notification,
        'parent_balance': parent.balance,
        'merchant_balance': merchant.balance,
        'sale': sale,
    }


def _merchant_profile_response(merchant: User, profile: MerchantProfile | None) -> dict:
    if not profile:
        return {
            'merchant_id': merchant.id,
            'business_name': None,
            'personal_name': merchant.name,
            'place_scope': None,
            'address': merchant.address,
            'mobile_phone': None,
            'country_code': None,
            'transfer_account_type': None,
            'transfer_account': None,
            'transfer_account_alias': None,
        }
    return {
        'id': profile.id,
        'merchant_id': merchant.id,
        'business_name': profile.business_name,
        'personal_name': profile.personal_name,
        'place_scope': profile.place_scope,
        'address': profile.address,
        'mobile_phone': profile.mobile_phone,
        'country_code': profile.country_code,
        'transfer_account_type': profile.transfer_account_type,
        'transfer_account': profile.transfer_account,
        'transfer_account_alias': profile.transfer_account_alias,
    }


@router.get('/merchant/{merchant_id}/profile')
def get_merchant_profile(merchant_id: int, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id, Merchant.role == UserType.merchant).first()
    if not merchant:
        raise HTTPException(status_code=404, detail='Merchant not found')
    profile = db.query(MerchantProfile).filter(MerchantProfile.user_id == merchant_id).first()
    return _merchant_profile_response(merchant, profile)


@router.put('/merchant/{merchant_id}/profile')
def upsert_merchant_profile(
    merchant_id: int,
    data: MerchantProfileRequest,
    db: Session = Depends(get_db),
):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id, Merchant.role == UserType.merchant).first()
    if not merchant:
        raise HTTPException(status_code=404, detail='Merchant not found')

    payload = data.model_dump(exclude_unset=True)
    profile = db.query(MerchantProfile).filter(MerchantProfile.user_id == merchant_id).first()
    if not profile:
        profile = MerchantProfile(user_id=merchant_id)
        db.add(profile)

    place_scope = payload.get('place_scope', profile.place_scope)
    address = payload.get('address', profile.address or merchant.address)
    if place_scope == 'outside_school' and not address:
        raise HTTPException(status_code=400, detail='Address is required for merchants outside school')

    for field, value in payload.items():
        setattr(profile, field, value)

    if 'address' in payload:
        merchant.address = payload['address']

    db.commit()
    db.refresh(profile)
    db.refresh(merchant)
    return {
        'msg': 'Merchant profile saved',
        'profile': _merchant_profile_response(merchant, profile),
    }


@router.post('/merchant/{merchant_id}/payout-methods')
def add_merchant_payout_method(
    merchant_id: int,
    data: MerchantPayoutMethodRequest,
    db: Session = Depends(get_db),
):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id, Merchant.role == UserType.merchant).first()
    if not merchant:
        raise HTTPException(status_code=404, detail='Merchant not found')
    try:
        payout_method = create_merchant_payout_method(
            db,
            merchant=merchant,
            provider=PaymentProvider(data.provider),
            provider_account_id=data.provider_account_id,
            label=data.label,
            metadata_json=data.metadata_json,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(payout_method)
    return {
        'msg': 'Payout method saved',
        'payout_method_id': payout_method.id,
        'provider': payout_method.provider.value,
        'status': payout_method.status,
    }


@router.post('/merchant/{merchant_id}/payouts')
def create_merchant_payout(
    merchant_id: int,
    data: MerchantPayoutRequest,
    db: Session = Depends(get_db),
):
    from models import MerchantPayoutMethod

    merchant = db.query(Merchant).filter(Merchant.id == merchant_id, Merchant.role == UserType.merchant).first()
    if not merchant:
        raise HTTPException(status_code=404, detail='Merchant not found')
    payout_method = (
        db.query(MerchantPayoutMethod)
        .filter(MerchantPayoutMethod.id == data.payout_method_id, MerchantPayoutMethod.merchant_id == merchant_id)
        .first()
    )
    if not payout_method:
        raise HTTPException(status_code=404, detail='Payout method not found')
    try:
        payout = prepare_merchant_payout(
            db,
            merchant=merchant,
            payout_method=payout_method,
            amount_pesos=data.amount_pesos,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()
    db.refresh(merchant)
    db.refresh(payout)
    return {
        'msg': 'Payout prepared',
        'payout_id': payout.id,
        'ledger_transaction_id': payout.ledger_transaction_id,
        'status': payout.status.value,
        'merchant_balance': merchant.balance,
    }


def _notification_recipients(parent_user, profile):
    """Return parent and trusted contacts with email addresses, without duplicates."""
    recipients = []
    seen = set()

    def add(label: str, email: str | None):
        if not email:
            return
        normalized = email.strip().lower()
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        recipients.append((label, email.strip()))

    if parent_user:
        add(parent_user.name or 'Parent', getattr(parent_user, 'email', None))
    if profile:
        add('Parent', profile.email)
        for contact in profile.trusted_contacts:
            label = f"{contact.name} {contact.surname or ''}".strip() or 'Trusted contact'
            add(label, contact.email)

    return recipients


def _email_child_alert(parent_user, profile, child_name: str, message: str, school_name: str = 'ColePago'):
    for recipient_name, to_email in _notification_recipients(parent_user, profile):
        try:
            send_alert_email(
                to_email=to_email,
                recipient_name=recipient_name,
                child_name=child_name,
                message=message,
                school_name=school_name,
            )
        except Exception:
            pass


def _fire_theft_alert(child, db):
    """Send WhatsApp + email alerts when rapid-spend triggers an auto-block."""
    try:
        parent_user = child.parent
        profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_user.id).first()
        msg = (
            f"🚨 *ColePago Security Alert*\n\n"
            f"Your child *{child.name}*'s account has been *automatically blocked* because "
            f"3 or more purchases were made within 5 minutes.\n\n"
            f"This may indicate phone theft. Please check and unblock via the app if safe."
        )
        if profile and profile.mobile_phone:
            try:
                send_whatsapp(profile.mobile_phone, profile.country_code or '', msg)
            except Exception:
                pass
        _email_child_alert(
            parent_user,
            profile,
            child.name,
            (
                f"{child.name}'s account was auto-blocked after 3 purchases in under 5 minutes. "
                "This may indicate phone theft. Log in to review and unblock."
            ),
        )
    except Exception:
        pass  # alert failure must never prevent the HTTP response


# ── Child location tracking ───────────────────────────────────────────────

class LocationPingRequest(BaseModel):
    lat: float
    lon: float
    accel_x: Optional[float] = None
    accel_y: Optional[float] = None
    accel_z: Optional[float] = None


class RouteWaypointIn(BaseModel):
    seq: int
    lat: float
    lon: float


@router.post('/child/{child_id}/location')
def post_location_ping(child_id: int, data: LocationPingRequest, db: Session = Depends(get_db)):
    """Child device sends its current GPS position."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail='Child not found')

    ping = ChildLocationPing(
        child_id=child_id,
        lat=data.lat,
        lon=data.lon,
        accel_x=data.accel_x,
        accel_y=data.accel_y,
        accel_z=data.accel_z,
    )
    db.add(ping)
    db.commit()

    # Check if the child is off their normal route and alert parent
    off_route = is_off_route(child, data.lat, data.lon, db)
    if off_route:
        now = datetime.datetime.utcnow()
        # Throttle: only alert once every 10 minutes
        if (
            child.last_route_alert is None
            or (now - child.last_route_alert).total_seconds() > 600
        ):
            child.last_route_alert = now
            db.commit()
            _fire_route_alert(child, data.lat, data.lon, db)

    return {'recorded': True, 'off_route': off_route}


@router.get('/child/{child_id}/location/latest')
def get_latest_location(child_id: int, db: Session = Depends(get_db)):
    """Return the child's most recent GPS ping."""
    ping = (
        db.query(ChildLocationPing)
        .filter(ChildLocationPing.child_id == child_id)
        .order_by(ChildLocationPing.recorded_at.desc())
        .first()
    )
    if not ping:
        raise HTTPException(status_code=404, detail='No location data yet')
    return {'lat': ping.lat, 'lon': ping.lon, 'recorded_at': ping.recorded_at}


@router.get('/child/{child_id}/accelerometer')
def get_child_accelerometer(child_id: int, limit: int = 60, db: Session = Depends(get_db)):
    """Return accelerometer samples prepared for dashboard graphing."""
    limit = min(max(limit, 5), 240)
    pings = (
        db.query(ChildLocationPing)
        .filter(
            ChildLocationPing.child_id == child_id,
            ChildLocationPing.accel_x.isnot(None),
            ChildLocationPing.accel_y.isnot(None),
            ChildLocationPing.accel_z.isnot(None),
        )
        .order_by(ChildLocationPing.recorded_at.desc())
        .limit(limit)
        .all()
    )
    samples = []
    for ping in reversed(pings):
        x = float(ping.accel_x or 0)
        y = float(ping.accel_y or 0)
        z = float(ping.accel_z or 0)
        samples.append({
            'recorded_at': ping.recorded_at.isoformat() if ping.recorded_at else None,
            'magnitude': round((x * x + y * y + z * z) ** 0.5, 3),
        })
    return {'child_id': child_id, 'samples': samples}


@router.put('/child/{child_id}/route')
def set_route(child_id: int, waypoints: list[RouteWaypointIn], db: Session = Depends(get_db)):
    """Replace the child's standard route (array of ordered lat/lon waypoints)."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail='Child not found')
    db.query(ChildRouteWaypoint).filter(ChildRouteWaypoint.child_id == child_id).delete()
    for wp in waypoints:
        db.add(ChildRouteWaypoint(child_id=child_id, seq=wp.seq, lat=wp.lat, lon=wp.lon))
    db.commit()
    return {'msg': f'{len(waypoints)} waypoints saved'}


@router.get('/child/{child_id}/route')
def get_route(child_id: int, db: Session = Depends(get_db)):
    """Return the child's configured route waypoints."""
    wps = (
        db.query(ChildRouteWaypoint)
        .filter(ChildRouteWaypoint.child_id == child_id)
        .order_by(ChildRouteWaypoint.seq)
        .all()
    )
    return [{'seq': w.seq, 'lat': w.lat, 'lon': w.lon} for w in wps]


def _fire_route_alert(child, lat: float, lon: float, db):
    """Alert the parent and trusted contacts when the child strays from their standard route."""
    try:
        parent_user = child.parent
        profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_user.id).first()
        msg = (
            f"📍 *ColePago Route Alert*\n\n"
            f"*{child.name}* appears to be off their normal route.\n"
            f"Last known position: lat {lat:.5f}, lon {lon:.5f}\n\n"
            f"Please check on them."
        )
        if profile and profile.mobile_phone:
            try:
                send_whatsapp(profile.mobile_phone, profile.country_code or '', msg)
            except Exception:
                pass
        _email_child_alert(
            parent_user,
            profile,
            child.name,
            (
                f"{child.name} appears to be off their normal route. "
                f"Last position: {lat:.5f}, {lon:.5f}. Please check on them."
            ),
        )
    except Exception:
        pass


# ── Password reset ────────────────────────────────────────────────

def _generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    temp_password: str
    new_password: str


@router.post('/auth/forgot-password')
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    # Always return success to prevent email enumeration
    if not user:
        return {'msg': 'If that email is registered you will receive a reset link.'}

    temp_pw = _generate_temp_password()
    user.temp_password_hash = hash_password(temp_pw)
    user.temp_password_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    db.commit()

    try:
        send_temp_password_email(user.email, user.name, temp_pw)
    except Exception as exc:
        # Roll back temp password if email fails so user is not locked out
        user.temp_password_hash = None
        user.temp_password_expires = None
        db.commit()
        raise HTTPException(status_code=500, detail=f'Failed to send email: {exc}')

    return {'msg': 'If that email is registered you will receive a reset link.'}


@router.post('/auth/reset-password')
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.temp_password_hash:
        raise HTTPException(status_code=400, detail='Invalid or expired reset request.')

    if user.temp_password_expires is None or datetime.datetime.utcnow() > user.temp_password_expires:
        user.temp_password_hash = None
        user.temp_password_expires = None
        db.commit()
        raise HTTPException(status_code=400, detail='Temporary password has expired. Please request a new one.')

    if not verify_password(data.temp_password, user.temp_password_hash):
        raise HTTPException(status_code=400, detail='Invalid temporary password.')

    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail='New password must be at least 8 characters.')

    user.password_hash = hash_password(data.new_password)
    user.temp_password_hash = None
    user.temp_password_expires = None
    db.commit()
    return {'msg': 'Password updated successfully.'}


# ── Parent Profile ────────────────────────────────────────────────

class ParentProfileRequest(BaseModel):
    name: Optional[str] = None
    relationship_to_child: Optional[str] = None
    children_using_colepago: Optional[int] = None
    home_address: Optional[str] = None
    home_floor: Optional[str] = None
    home_department: Optional[str] = None
    home_postal: Optional[str] = None
    home_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    work_name: Optional[str] = None
    work_address: Optional[str] = None
    work_postal: Optional[str] = None
    work_phone: Optional[str] = None
    work_shift: Optional[str] = None
    work_hours: Optional[str] = None
    workplace: Optional[str] = None
    email: Optional[str] = None


@router.get('/parent/{parent_id}/profile')
def get_parent_profile(parent_id: int, db: Session = Depends(get_db)):
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        return {}
    parent = db.query(User).filter(User.id == parent_id).first()
    return {
        'id': profile.id,
        'name': parent.name if parent else None,
        'username': parent.username if parent else None,
        'relationship_to_child': profile.relationship_to_child,
        'children_using_colepago': profile.children_using_colepago,
        'home_address': profile.home_address,
        'home_floor': profile.home_floor,
        'home_department': profile.home_department,
        'home_postal': profile.home_postal,
        'home_phone': profile.home_phone,
        'mobile_phone': profile.mobile_phone,
        'country': profile.country,
        'country_code': profile.country_code,
        'work_name': profile.work_name,
        'work_address': profile.work_address,
        'work_postal': profile.work_postal,
        'work_phone': profile.work_phone,
        'work_shift': profile.work_shift,
        'work_hours': profile.work_hours,
        'workplace': profile.workplace,
        'email': profile.email,
    }


@router.put('/parent/{parent_id}/profile')
def upsert_parent_profile(parent_id: int, data: ParentProfileRequest, db: Session = Depends(get_db)):
    parent = db.query(User).filter(User.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail='Parent not found')
    if (
        data.children_using_colepago is not None
        and data.children_using_colepago < 1
    ):
        raise HTTPException(status_code=400, detail='At least one child is required')
    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail='Parent name is required')
        parent.name = name
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        profile = ParentProfile(user_id=parent_id)
        db.add(profile)
    for field, value in data.model_dump(exclude_unset=True, exclude={'name'}).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return {'msg': 'Profile saved', 'profile_id': profile.id}


# ── Trusted Contacts ─────────────────────────────────────────────

class TrustedContactRequest(BaseModel):
    name: str
    surname: Optional[str] = None
    relation: Optional[str] = None
    mobile: Optional[str] = None
    country_code: Optional[str] = None
    home_phone: Optional[str] = None
    work_phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None


@router.get('/parent/{parent_id}/trusted-contacts')
def get_trusted_contacts(parent_id: int, db: Session = Depends(get_db)):
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        return []
    return [
        {
            'id': c.id,
            'name': c.name,
            'surname': c.surname,
            'relation': c.relation,
            'mobile': c.mobile,
            'country_code': c.country_code,
            'home_phone': c.home_phone,
            'work_phone': c.work_phone,
            'address': c.address,
            'email': c.email,
        }
        for c in profile.trusted_contacts
    ]


@router.post('/parent/{parent_id}/trusted-contacts')
def add_trusted_contact(parent_id: int, data: TrustedContactRequest, db: Session = Depends(get_db)):
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        # Auto-create profile if it doesn't exist yet
        profile = ParentProfile(user_id=parent_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    contact = TrustedContact(parent_profile_id=profile.id, **data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return {'msg': 'Trusted contact added', 'contact_id': contact.id}


@router.delete('/parent/{parent_id}/trusted-contacts/{contact_id}')
def delete_trusted_contact(parent_id: int, contact_id: int, db: Session = Depends(get_db)):
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail='Profile not found')
    contact = db.query(TrustedContact).filter(
        TrustedContact.id == contact_id,
        TrustedContact.parent_profile_id == profile.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail='Contact not found')
    db.delete(contact)
    db.commit()
    return {'msg': 'Contact deleted'}


class WhatsAppRequest(BaseModel):
    message: str
    include_trusted_contacts: bool = False
    content_sid: Optional[str] = None
    content_variables: Optional[dict] = None


@router.post('/parent/{parent_id}/whatsapp')
def send_whatsapp_to_parent(parent_id: int, data: WhatsAppRequest, db: Session = Depends(get_db)):
    """
    Send a WhatsApp message to a parent and optionally all their trusted contacts.
    Requires TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN in .env.
    """
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail='Parent profile not found')

    results = []
    errors = []

    # Send to parent
    if profile.mobile_phone:
        try:
            if data.content_sid:
                sid = send_whatsapp_template(
                    to_number=profile.mobile_phone,
                    country_code=profile.country_code or '',
                    content_sid=data.content_sid,
                    content_variables=data.content_variables or {},
                )
            else:
                sid = send_whatsapp(
                    to_number=profile.mobile_phone,
                    country_code=profile.country_code or '',
                    body=data.message,
                )
            results.append({'target': 'parent', 'sid': sid})
        except Exception as e:
            errors.append({'target': 'parent', 'error': str(e)})
    else:
        errors.append({'target': 'parent', 'error': 'No mobile number on profile'})

    # Send to trusted contacts if requested
    if data.include_trusted_contacts:
        for contact in profile.trusted_contacts:
            if contact.mobile:
                try:
                    if data.content_sid:
                        sid = send_whatsapp_template(
                            to_number=contact.mobile,
                            country_code=contact.country_code or '',
                            content_sid=data.content_sid,
                            content_variables=data.content_variables or {},
                        )
                    else:
                        sid = send_whatsapp(
                            to_number=contact.mobile,
                            country_code=contact.country_code or '',
                            body=data.message,
                        )
                    results.append({
                        'target': f'{contact.name} {contact.surname or ""}'.strip(),
                        'sid': sid,
                    })
                except Exception as e:
                    errors.append({
                        'target': f'{contact.name} {contact.surname or ""}'.strip(),
                        'error': str(e),
                    })

    if not results and errors:
        raise HTTPException(status_code=502, detail={'sent': results, 'errors': errors})

    return {'sent': results, 'errors': errors}


class SmsRequest(BaseModel):
    message: str
    include_trusted_contacts: bool = False


class ParentMessageRequest(BaseModel):
    message: str
    channels: list[str] = ["whatsapp", "sms"]
    include_trusted_contacts: bool = False
    content_sid: Optional[str] = None
    content_variables: Optional[dict] = None


class ParentCallRequest(BaseModel):
    message: Optional[str] = None
    include_trusted_contacts: bool = False


@router.post('/parent/{parent_id}/sms')
def send_sms_to_parent(parent_id: int, data: SmsRequest, db: Session = Depends(get_db)):
    """
    Send an SMS message to a parent and optionally all trusted contacts.
    Requires TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN and either TWILIO_SMS_FROM
    or TWILIO_MESSAGING_SERVICE_SID in .env.
    """
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail='Parent profile not found')

    results = []
    errors = []

    if profile.mobile_phone:
        try:
            sid = send_sms(
                to_number=profile.mobile_phone,
                country_code=profile.country_code or '',
                body=data.message,
            )
            results.append({'target': 'parent', 'sid': sid})
        except Exception as e:
            errors.append({'target': 'parent', 'error': str(e)})
    else:
        errors.append({'target': 'parent', 'error': 'No mobile number on profile'})

    if data.include_trusted_contacts:
        for contact in profile.trusted_contacts:
            if contact.mobile:
                try:
                    sid = send_sms(
                        to_number=contact.mobile,
                        country_code=contact.country_code or '',
                        body=data.message,
                    )
                    results.append({
                        'target': f'{contact.name} {contact.surname or ""}'.strip(),
                        'sid': sid,
                    })
                except Exception as e:
                    errors.append({
                        'target': f'{contact.name} {contact.surname or ""}'.strip(),
                        'error': str(e),
                    })

    if not results and errors:
        raise HTTPException(status_code=502, detail={'sent': results, 'errors': errors})

    return {'sent': results, 'errors': errors}


@router.post('/parent/{parent_id}/message')
def send_message_to_parent(parent_id: int, data: ParentMessageRequest, db: Session = Depends(get_db)):
    """
    Send message-only alerts to a parent. No voice calls are attempted here.
    Supported channels: whatsapp, sms.
    """
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail='Parent profile not found')

    recipients = [('parent', profile.mobile_phone or '', profile.country_code or '')]
    if data.include_trusted_contacts:
        for contact in profile.trusted_contacts:
            recipients.append((
                f'{contact.name} {contact.surname or ""}'.strip(),
                contact.mobile or '',
                contact.country_code or '',
            ))

    results = []
    for target_label, number, cc in recipients:
        if not number:
            results.append({
                'target': target_label,
                'channel': 'message',
                'status': 'failed',
                'error': 'No mobile number on profile',
            })
            continue

        if 'whatsapp' in data.channels:
            try:
                if data.content_sid:
                    sid = send_whatsapp_template(
                        to_number=number,
                        country_code=cc,
                        content_sid=data.content_sid,
                        content_variables=data.content_variables or {},
                    )
                else:
                    sid = send_whatsapp(number, cc, data.message)
                results.append({'target': target_label, 'channel': 'whatsapp', 'status': 'sent', 'sid': sid})
            except Exception as e:
                results.append({'target': target_label, 'channel': 'whatsapp', 'status': 'failed', 'error': str(e)})

        if 'sms' in data.channels:
            try:
                sid = send_sms(number, cc, data.message)
                results.append({'target': target_label, 'channel': 'sms', 'status': 'sent', 'sid': sid})
            except Exception as e:
                results.append({'target': target_label, 'channel': 'sms', 'status': 'failed', 'error': str(e)})

    sent = [result for result in results if result['status'] == 'sent']
    if not sent:
        raise HTTPException(status_code=502, detail={'msg': 'All message channels failed', 'log': results})

    return {'log': results, 'sent_count': len(sent)}


@router.post('/parent/{parent_id}/call')
def call_parent_phone(parent_id: int, data: ParentCallRequest, db: Session = Depends(get_db)):
    """
    Place a voice call to the parent phone number.
    This is an explicit call-only endpoint; message endpoints never call.
    """
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail='Parent profile not found')

    parent_user = db.query(User).filter(User.id == parent_id).first()
    spoken = data.message or 'ColePago alert. Please check your parent dashboard.'
    results = []
    errors = []

    recipients = [(
        parent_user.name if parent_user else 'Parent',
        profile.mobile_phone or '',
        profile.country_code or '',
    )]
    if data.include_trusted_contacts:
        for contact in profile.trusted_contacts:
            recipients.append((
                f'{contact.name} {contact.surname or ""}'.strip(),
                contact.mobile or '',
                contact.country_code or '',
            ))

    for target_label, number, cc in recipients:
        if not number:
            errors.append({'target': target_label, 'error': 'No mobile number on profile'})
            continue
        try:
            sid = make_voice_call(number, cc, spoken)
            results.append({'target': target_label, 'channel': 'call', 'status': 'sent', 'sid': sid})
        except Exception as e:
            errors.append({'target': target_label, 'channel': 'call', 'status': 'failed', 'error': str(e)})

    if not results and errors:
        raise HTTPException(status_code=502, detail={'sent': results, 'errors': errors})

    return {'sent': results, 'errors': errors}


# ── Escalation (parent unreachable → trusted contacts) ───────────────────────

class EscalateRequest(BaseModel):
    child_name: str
    message: str
    school_name: str = "the school"
    channels: list[str] = ["whatsapp", "sms", "email"]  # call only if explicitly requested


@router.post('/parent/{parent_id}/escalate')
def escalate_to_contacts(
    parent_id: int,
    data: EscalateRequest,
    db: Session = Depends(get_db),
):
    """
    Try to reach the parent via all requested channels.
    If the parent has no mobile/email, or as a parallel fallback,
    also send to all emergency contacts.
    Returns a per-recipient, per-channel result log.
    """
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail='Parent profile not found')

    parent_user = db.query(User).filter(User.id == parent_id).first()
    parent_name = parent_user.name if parent_user else 'Parent'

    spoken = (
        f"Hello, this is an urgent message from {data.school_name} regarding "
        f"{data.child_name}. {data.message} Please contact the school immediately."
    )

    results = []

    def _try(target_label: str, number: str, cc: str, email: str | None):
        """Attempt all requested channels for one recipient. Appends to results."""
        if 'whatsapp' in data.channels and number:
            try:
                sid = send_whatsapp(number, cc, f"🚨 *{data.school_name}* – Urgent\n\n{data.message}")
                results.append({'target': target_label, 'channel': 'whatsapp', 'status': 'sent', 'sid': sid})
            except Exception as e:
                results.append({'target': target_label, 'channel': 'whatsapp', 'status': 'failed', 'error': str(e)})

        if 'sms' in data.channels and number:
            try:
                sid = send_sms(number, cc, f"{data.school_name} urgent: {data.message}")
                results.append({'target': target_label, 'channel': 'sms', 'status': 'sent', 'sid': sid})
            except Exception as e:
                results.append({'target': target_label, 'channel': 'sms', 'status': 'failed', 'error': str(e)})

        if 'call' in data.channels and number:
            try:
                sid = make_voice_call(number, cc, spoken)
                results.append({'target': target_label, 'channel': 'call', 'status': 'sent', 'sid': sid})
            except Exception as e:
                results.append({'target': target_label, 'channel': 'call', 'status': 'failed', 'error': str(e)})

        if 'email' in data.channels and email:
            try:
                send_alert_email(
                    to_email=email,
                    recipient_name=target_label,
                    child_name=data.child_name,
                    message=data.message,
                    school_name=data.school_name,
                )
                results.append({'target': target_label, 'channel': 'email', 'status': 'sent'})
            except Exception as e:
                results.append({'target': target_label, 'channel': 'email', 'status': 'failed', 'error': str(e)})

    # 1. Try the parent
    _try(
        target_label=parent_name,
        number=profile.mobile_phone or '',
        cc=profile.country_code or '',
        email=profile.email or (parent_user.email if parent_user else None),
    )

    # 2. Always also try all trusted contacts as parallel escalation
    for contact in profile.trusted_contacts:
        label = f"{contact.name} {contact.surname or ''}".strip()
        _try(
            target_label=label,
            number=contact.mobile or '',
            cc=contact.country_code or '',
            email=contact.email,
        )

    sent = [r for r in results if r['status'] == 'sent']
    if not sent:
        raise HTTPException(
            status_code=502,
            detail={'msg': 'All channels failed', 'log': results},
        )

    return {'log': results, 'sent_count': len(sent)}


app = FastAPI(title='Colepago API')
app.include_router(router)
