import os
from typing import Literal, Optional

import mercadopago
import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, SecretStr
from sqlalchemy.orm import Session

from models import Child, Merchant, Parent, User, UserType, get_db

router = APIRouter()

COIN_CONVERSION_RATE = 1.0
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

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
    pay_lat: float
    pay_lon: float


class FundWalletRequest(BaseModel):
    parent_id: int
    amount_pesos: float
    payment_method: Literal['mercadopago', 'bank_transfer', 'stripe_card']
    mp_token: Optional[SecretStr] = None
    bank_account: Optional[SecretStr] = None
    stripe_payment_method_id: Optional[str] = None


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal['parent', 'merchant']


@router.get('/ping')
async def ping():
    return {'msg': 'pong'}


@router.post('/auth/register')
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if data.role == 'parent':
        if db.query(Parent).filter(Parent.email == data.email).first():
            raise HTTPException(status_code=400, detail='Email already registered')
        user = Parent(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
        )
    else:
        if db.query(Merchant).filter(Merchant.email == data.email).first():
            raise HTTPException(status_code=400, detail='Email already registered')
        user = Merchant(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
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

    if data.payment_method == 'mercadopago':
        if mp_client is None:
            raise HTTPException(status_code=500, detail='Mercado Pago not configured')
        if not data.mp_token:
            raise HTTPException(status_code=400, detail='Mercado Pago token required')
    elif data.payment_method == 'stripe_card':
        if not STRIPE_SECRET_KEY:
            raise HTTPException(status_code=500, detail='Stripe not configured')
        if not data.stripe_payment_method_id:
            raise HTTPException(status_code=400, detail='Stripe PaymentMethod ID required')
    elif data.payment_method == 'bank_transfer' and not data.bank_account:
        raise HTTPException(status_code=400, detail='Bank transfer details required')

    coins = data.amount_pesos * COIN_CONVERSION_RATE
    parent.balance = (parent.balance or 0) + coins
    db.commit()
    db.refresh(parent)
    return {'msg': 'Wallet funded successfully', 'coins_added': coins, 'new_balance': parent.balance}


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
    merchant = db.query(Merchant).filter(Merchant.id == data.merchant_id).first()
    if not child or not merchant:
        raise HTTPException(status_code=404, detail='Child or merchant not found')
    if child.balance < data.amount:
        raise HTTPException(status_code=400, detail='Insufficient balance')

    child.balance -= data.amount
    merchant.balance = (merchant.balance or 0) + data.amount
    db.commit()
    return {'msg': 'Payment successful'}


app = FastAPI(title='Colepago API')
app.include_router(router)
