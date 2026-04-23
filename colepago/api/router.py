
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Optional, Literal
from pydantic import SecretStr, BaseModel, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
import stripe
import mercadopago
# from geo_utils import is_payment_location_valid  # Uncomment if geo_utils.py exists
from models import Parent, Merchant, Base, UserType, get_db, User, Child  # adjust import as needed

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Stripe Test Endpoint ---
class StripeTestRequest(BaseModel):
    parent_id: int
    amount_pesos: float = 100.0

@router.post("/wallet/test-stripe")
def test_stripe_payment(data: StripeTestRequest, db: Session = Depends(get_db)):
    """
    Test Stripe payment with test PaymentMethod ID (pm_card_visa).
    Only available in non-production environments.
    """
    if os.getenv("ENV", "development").lower() == "production":
        raise HTTPException(status_code=403, detail="This endpoint is disabled in production.")
    parent = db.query(Parent).filter(Parent.id == data.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(data.amount_pesos * 100),
            currency="mxn",
            payment_method="pm_card_visa",
            confirmation_method="automatic",
            confirm=True,
        )
        if intent.status == "succeeded":
            return {"msg": "Stripe test payment succeeded", "intent_id": intent.id}
        else:
            raise HTTPException(status_code=402, detail="Stripe test payment failed: " + intent.status)
    except stripe.error.CardError as e:
        raise HTTPException(status_code=402, detail=f"Stripe card error: {e.user_message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

# --- Spend Endpoint ---
class SpendRequest(BaseModel):
    child_id: int
    merchant_id: int
    amount: float
    pay_lat: float
    pay_lon: float

@router.post("/child/spend")
def child_spend(data: SpendRequest, db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == data.child_id).first()
    merchant = db.query(User).filter(User.id == data.merchant_id, User.role == 'merchant').first()
    if not child or not merchant:
        raise HTTPException(status_code=404, detail="Child or merchant not found")
    if child.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    # Validate payment location
    # if not is_payment_location_valid(child, merchant, data.pay_lat, data.pay_lon, db):
    #     raise HTTPException(status_code=400, detail="Payment location not allowed. Must be near merchant or school.")
    try:
        with db.begin():
            child.balance -= data.amount
            merchant.balance += data.amount
            db.flush()
        return {"msg": "Payment successful"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Payment failed")
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Optional, Literal
from pydantic import SecretStr, BaseModel, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
import stripe
import mercadopago
from models import Parent, Merchant, Base, UserType, get_db  # adjust import as needed

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Wallet Funding ---
class FundWalletRequest(BaseModel):
    parent_id: int
    amount_pesos: float
    payment_method: Literal["mercadopago", "bank_transfer", "stripe_card"]
    mp_token: Optional[SecretStr] = None
    bank_account: Optional[SecretStr] = None
    stripe_payment_method_id: Optional[str] = None

COIN_CONVERSION_RATE = 1.0

load_dotenv()
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
stripe.api_key = STRIPE_SECRET_KEY
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "TEST-...")
mp_client = mercadopago.SDK(MP_ACCESS_TOKEN)

@router.post("/wallet/fund")
def fund_wallet(data: FundWalletRequest, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.id == data.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    if data.amount_pesos <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    payment_success = False
    if data.payment_method == "mercadopago":
        if not data.mp_token:
            raise HTTPException(status_code=400, detail="Mercado Pago token required")
        try:
            payment_data = {
                "transaction_amount": float(data.amount_pesos),
                "token": data.mp_token.get_secret_value(),
                "description": "Colepago wallet funding",
                "installments": 1,
                "payment_method_id": "visa",
                "payer": {"email": parent.email}
            }
            mp_response = mp_client.payment().create(payment_data)
            mp_status = mp_response["response"].get("status")
            if mp_status == "approved":
                payment_success = True
            else:
                raise HTTPException(status_code=402, detail=f"Mercado Pago payment failed: {mp_status}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Mercado Pago error: {str(e)}")
    elif data.payment_method == "bank_transfer":
        if not data.bank_account:
            raise HTTPException(status_code=400, detail="Bank transfer details required")
        payment_success = True
    elif data.payment_method == "stripe_card":
        if not data.stripe_payment_method_id:
            raise HTTPException(status_code=400, detail="Stripe PaymentMethod ID required. Create it on the client using publishable key.")
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(data.amount_pesos * 100),
                currency="mxn",
                payment_method=data.stripe_payment_method_id,
                confirmation_method="automatic",
                confirm=True,
            )
            if intent.status == "succeeded":
                payment_success = True
            else:
                raise HTTPException(status_code=402, detail="Stripe payment failed: " + intent.status)
        except stripe.error.CardError as e:
            raise HTTPException(status_code=402, detail=f"Stripe card error: {e.user_message}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    if not payment_success:
        raise HTTPException(status_code=402, detail="Payment failed")

    coins = data.amount_pesos * COIN_CONVERSION_RATE
    try:
        with db.begin():
            parent.balance = (parent.balance or 0) + coins
            db.flush()
        db.refresh(parent)
        return {"msg": "Wallet funded successfully", "coins_added": coins, "new_balance": parent.balance}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Funding failed")

# --- Ping Endpoint ---
@router.get("/ping")
async def ping():
    return {"msg": "pong"}

# --- Registration ---
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str  # "parent" or "merchant"

@router.post("/auth/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if data.role == "parent":
        if db.query(Parent).filter(Parent.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = pwd_context.hash(data.password)
        user = Parent(name=data.name, email=data.email, password_hash=hashed_password)
        try:
            with db.begin():
                db.add(user)
                db.flush()
            db.refresh(user)
            return {"msg": "Registration successful", "role": "parent"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Registration failed")
    elif data.role == "merchant":
        if db.query(Merchant).filter(Merchant.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = pwd_context.hash(data.password)
        user = Merchant(name=data.name, email=data.email, password_hash=hashed_password)
        try:
            with db.begin():
                db.add(user)
                db.flush()
            db.refresh(user)
            return {"msg": "Registration successful", "role": "merchant"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Registration failed")
    else:
        raise HTTPException(status_code=400, detail="Invalid role")
