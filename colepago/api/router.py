import os
from typing import Literal, Optional
import secrets
import string
import datetime

import bcrypt
import mercadopago
import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, SecretStr
from sqlalchemy.orm import Session

from models import Child, Merchant, Parent, ParentProfile, PaymentProvider, TrustedContact, User, UserType, get_db
from email_utils import send_temp_password_email, send_alert_email
from whatsapp_utils import send_whatsapp, make_voice_call
from geo_utils import is_payment_location_valid, is_rapid_spend, is_off_route
from models import Transaction, TransactionType, ChildLocationPing, ChildRouteWaypoint
from services.payment_gateway import (
    cents_to_pesos,
    create_merchant_payout_method,
    prepare_merchant_payout,
    record_child_purchase,
    record_parent_deposit,
)

router = APIRouter()

COIN_CONVERSION_RATE = 1.0


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

load_dotenv()
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
stripe.api_key = STRIPE_SECRET_KEY
MP_ACCESS_TOKEN = os.getenv('MP_ACCESS_TOKEN', '')
mp_client = mercadopago.SDK(MP_ACCESS_TOKEN) if MP_ACCESS_TOKEN else None


class StripeTestRequest(BaseModel):
    parent_id: int
    amount_pesos: float = 100.0


class SpendRequest(BaseModel):
    child_id: int
    merchant_id: int
    amount: float
    pay_lat: Optional[float] = None
    pay_lon: Optional[float] = None


class FundWalletRequest(BaseModel):
    parent_id: int
    amount_pesos: float
    payment_method: Literal['mercadopago', 'bank_transfer', 'stripe_card']
    mp_token: Optional[SecretStr] = None
    bank_account: Optional[SecretStr] = None
    stripe_payment_method_id: Optional[str] = None


class MerchantPayoutMethodRequest(BaseModel):
    provider: Literal['mercadopago', 'stripe', 'bank_manual']
    provider_account_id: Optional[str] = None
    label: Optional[str] = None
    metadata_json: Optional[str] = None


class MerchantPayoutRequest(BaseModel):
    payout_method_id: int
    amount_pesos: float


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal['parent', 'merchant']
    username: Optional[str] = None


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
    return {'msg': 'Registration successful', 'role': data.role}


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
        if not data.stripe_payment_method_id:
            raise HTTPException(status_code=400, detail='Stripe PaymentMethod ID required')
        provider = PaymentProvider.stripe
        external_id = data.stripe_payment_method_id
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
        'coins_added': cents_to_pesos(payment.amount_cents),
        'new_balance': parent.balance,
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

    ping = ChildLocationPing(child_id=child_id, lat=data.lat, lon=data.lon)
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
    relationship_to_child: Optional[str] = None
    home_address: Optional[str] = None
    home_floor: Optional[str] = None
    home_department: Optional[str] = None
    home_postal: Optional[str] = None
    home_phone: Optional[str] = None
    mobile_phone: Optional[str] = None
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
        'username': parent.username if parent else None,
        'relationship_to_child': profile.relationship_to_child,
        'home_address': profile.home_address,
        'home_floor': profile.home_floor,
        'home_department': profile.home_department,
        'home_postal': profile.home_postal,
        'home_phone': profile.home_phone,
        'mobile_phone': profile.mobile_phone,
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
    profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent_id).first()
    if not profile:
        profile = ParentProfile(user_id=parent_id)
        db.add(profile)
    for field, value in data.model_dump(exclude_unset=True).items():
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


# ── Escalation (parent unreachable → trusted contacts) ───────────────────────

class EscalateRequest(BaseModel):
    child_name: str
    message: str
    school_name: str = "the school"
    channels: list[str] = ["whatsapp", "call", "email"]  # which channels to use


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
