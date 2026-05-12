import datetime
import os
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from models import (
    ExternalPayment,
    ExternalPaymentStatus,
    ExternalPayout,
    ExternalPayoutStatus,
    LedgerAccount,
    LedgerAccountType,
    LedgerEntry,
    LedgerOwnerType,
    LedgerTransaction,
    LedgerTransactionStatus,
    LedgerTransactionType,
    MerchantPayoutMethod,
    PaymentProvider,
    User,
    UserType,
)
from services.admin_config import commission_percent


DEFAULT_CURRENCY = "ARS"


def pesos_to_cents(amount: float) -> int:
    decimal_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(decimal_amount * 100)


def cents_to_pesos(amount_cents: int) -> float:
    return float(Decimal(amount_cents) / Decimal(100))


def _commission_cents(amount_cents: int) -> int:
    percent = Decimal(str(commission_percent()))
    return int((Decimal(amount_cents) * percent / Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def get_or_create_ledger_account(
    db: Session,
    owner_type: LedgerOwnerType,
    owner_id: int | None,
    account_type: LedgerAccountType,
    currency: str = DEFAULT_CURRENCY,
    name: str | None = None,
) -> LedgerAccount:
    account = (
        db.query(LedgerAccount)
        .filter(
            LedgerAccount.owner_type == owner_type,
            LedgerAccount.owner_id == owner_id,
            LedgerAccount.account_type == account_type,
            LedgerAccount.currency == currency,
        )
        .first()
    )
    if account:
        return account

    account = LedgerAccount(
        owner_type=owner_type,
        owner_id=owner_id,
        account_type=account_type,
        currency=currency,
        name=name,
    )
    db.add(account)
    db.flush()
    return account


def _post_transaction(
    db: Session,
    transaction_type: LedgerTransactionType,
    entries: list[tuple[LedgerAccount, int]],
    external_reference: str | None = None,
    description: str | None = None,
) -> LedgerTransaction:
    total = sum(amount_cents for _, amount_cents in entries)
    if total != 0:
        raise ValueError(f"Ledger transaction is not balanced: {total} cents")

    transaction = LedgerTransaction(
        type=transaction_type,
        status=LedgerTransactionStatus.posted,
        external_reference=external_reference,
        description=description,
    )
    db.add(transaction)
    db.flush()

    for account, amount_cents in entries:
        db.add(
            LedgerEntry(
                transaction_id=transaction.id,
                account_id=account.id,
                amount_cents=amount_cents,
            )
        )

    return transaction


def record_parent_deposit(
    db: Session,
    parent: User,
    amount_pesos: float,
    provider: PaymentProvider,
    external_id: str | None = None,
    raw_response_json: str | None = None,
) -> ExternalPayment:
    amount_cents = pesos_to_cents(amount_pesos)
    if amount_cents <= 0:
        raise ValueError("Deposit amount must be positive")

    parent_wallet = get_or_create_ledger_account(
        db,
        LedgerOwnerType.parent,
        parent.id,
        LedgerAccountType.wallet,
        name=f"Parent wallet {parent.id}",
    )
    provider_clearing = get_or_create_ledger_account(
        db,
        LedgerOwnerType.provider,
        None,
        LedgerAccountType.clearing,
        name=f"{provider.value} clearing",
    )
    transaction = _post_transaction(
        db,
        LedgerTransactionType.deposit,
        [(parent_wallet, amount_cents), (provider_clearing, -amount_cents)],
        external_reference=external_id,
        description=f"Parent {parent.id} wallet deposit via {provider.value}",
    )

    parent.balance = (parent.balance or 0) + cents_to_pesos(amount_cents)
    payment = ExternalPayment(
        parent_id=parent.id,
        provider=provider,
        external_id=external_id,
        amount_cents=amount_cents,
        status=ExternalPaymentStatus.confirmed,
        ledger_transaction_id=transaction.id,
        raw_response_json=raw_response_json,
        confirmed_at=datetime.datetime.utcnow(),
    )
    db.add(payment)
    db.flush()
    return payment


def create_pending_parent_deposit(
    db: Session,
    parent: User,
    amount_pesos: float,
    provider: PaymentProvider,
    external_id: str | None = None,
    raw_response_json: str | None = None,
) -> ExternalPayment:
    amount_cents = pesos_to_cents(amount_pesos)
    if amount_cents <= 0:
        raise ValueError("Deposit amount must be positive")

    payment = ExternalPayment(
        parent_id=parent.id,
        provider=provider,
        external_id=external_id,
        amount_cents=amount_cents,
        status=ExternalPaymentStatus.pending,
        raw_response_json=raw_response_json,
    )
    db.add(payment)
    db.flush()
    return payment


def confirm_parent_deposit(
    db: Session,
    payment: ExternalPayment,
    raw_response_json: str | None = None,
) -> ExternalPayment:
    if payment.status == ExternalPaymentStatus.confirmed:
        return payment
    if payment.status != ExternalPaymentStatus.pending:
        raise ValueError(f"Cannot confirm payment with status {payment.status.value}")

    parent = db.query(User).filter(User.id == payment.parent_id).first()
    if not parent:
        raise ValueError("Parent not found for external payment")

    parent_wallet = get_or_create_ledger_account(
        db,
        LedgerOwnerType.parent,
        parent.id,
        LedgerAccountType.wallet,
        name=f"Parent wallet {parent.id}",
    )
    provider_clearing = get_or_create_ledger_account(
        db,
        LedgerOwnerType.provider,
        None,
        LedgerAccountType.clearing,
        name=f"{payment.provider.value} clearing",
    )
    transaction = _post_transaction(
        db,
        LedgerTransactionType.deposit,
        [(parent_wallet, payment.amount_cents), (provider_clearing, -payment.amount_cents)],
        external_reference=payment.external_id,
        description=f"Parent {parent.id} wallet deposit via {payment.provider.value}",
    )

    parent.balance = (parent.balance or 0) + cents_to_pesos(payment.amount_cents)
    payment.status = ExternalPaymentStatus.confirmed
    payment.ledger_transaction_id = transaction.id
    payment.confirmed_at = datetime.datetime.utcnow()
    if raw_response_json:
        payment.raw_response_json = raw_response_json
    db.flush()
    return payment


def record_child_purchase(
    db: Session,
    parent: User,
    merchant: User,
    child_id: int,
    amount_pesos: float,
    external_reference: str | None = None,
) -> LedgerTransaction:
    amount_cents = pesos_to_cents(amount_pesos)
    if amount_cents <= 0:
        raise ValueError("Purchase amount must be positive")
    if pesos_to_cents(parent.balance or 0) < amount_cents:
        raise ValueError("Insufficient parent wallet balance")

    fee_cents = _commission_cents(amount_cents)
    merchant_net_cents = amount_cents - fee_cents

    parent_wallet = get_or_create_ledger_account(
        db,
        LedgerOwnerType.parent,
        parent.id,
        LedgerAccountType.wallet,
        name=f"Parent wallet {parent.id}",
    )
    merchant_receivable = get_or_create_ledger_account(
        db,
        LedgerOwnerType.merchant,
        merchant.id,
        LedgerAccountType.receivable,
        name=f"Merchant receivable {merchant.id}",
    )
    platform_fee = get_or_create_ledger_account(
        db,
        LedgerOwnerType.platform,
        None,
        LedgerAccountType.fee,
        name="ColePago fee revenue",
    )

    transaction = _post_transaction(
        db,
        LedgerTransactionType.child_purchase,
        [
            (parent_wallet, -amount_cents),
            (merchant_receivable, merchant_net_cents),
            (platform_fee, fee_cents),
        ],
        external_reference=external_reference,
        description=f"Child {child_id} purchase confirmed by merchant {merchant.id}",
    )

    parent.balance = (parent.balance or 0) - cents_to_pesos(amount_cents)
    merchant.balance = (merchant.balance or 0) + cents_to_pesos(merchant_net_cents)
    db.flush()
    return transaction


def create_merchant_payout_method(
    db: Session,
    merchant: User,
    provider: PaymentProvider,
    provider_account_id: str | None = None,
    label: str | None = None,
    metadata_json: str | None = None,
) -> MerchantPayoutMethod:
    if merchant.role != UserType.merchant:
        raise ValueError("Payout methods can only be added to merchant users")

    payout_method = MerchantPayoutMethod(
        merchant_id=merchant.id,
        provider=provider,
        provider_account_id=provider_account_id,
        label=label,
        status="pending" if provider == PaymentProvider.bank_manual else "active",
        metadata_json=metadata_json,
    )
    db.add(payout_method)
    db.flush()
    return payout_method


def prepare_merchant_payout(
    db: Session,
    merchant: User,
    payout_method: MerchantPayoutMethod,
    amount_pesos: float,
) -> ExternalPayout:
    amount_cents = pesos_to_cents(amount_pesos)
    if amount_cents <= 0:
        raise ValueError("Payout amount must be positive")
    if pesos_to_cents(merchant.balance or 0) < amount_cents:
        raise ValueError("Insufficient merchant receivable balance")

    merchant_receivable = get_or_create_ledger_account(
        db,
        LedgerOwnerType.merchant,
        merchant.id,
        LedgerAccountType.receivable,
        name=f"Merchant receivable {merchant.id}",
    )
    provider_payout = get_or_create_ledger_account(
        db,
        LedgerOwnerType.provider,
        None,
        LedgerAccountType.payout,
        name=f"{payout_method.provider.value} payout",
    )
    transaction = _post_transaction(
        db,
        LedgerTransactionType.merchant_payout,
        [(merchant_receivable, -amount_cents), (provider_payout, amount_cents)],
        description=f"Merchant {merchant.id} payout via {payout_method.provider.value}",
    )

    merchant.balance = (merchant.balance or 0) - cents_to_pesos(amount_cents)
    payout = ExternalPayout(
        merchant_id=merchant.id,
        payout_method_id=payout_method.id,
        provider=payout_method.provider,
        amount_cents=amount_cents,
        status=ExternalPayoutStatus.pending,
        ledger_transaction_id=transaction.id,
    )
    db.add(payout)
    db.flush()
    return payout
