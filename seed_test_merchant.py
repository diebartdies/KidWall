import bcrypt

from models import SessionLocal, User, UserRole


MERCHANT_EMAIL = "test.merchant@example.com"
MERCHANT_PASSWORD = "TestMerchant123!"


def main() -> None:
    db = SessionLocal()
    try:
        merchant = db.query(User).filter(User.email == MERCHANT_EMAIL).first()
        if not merchant:
            merchant = User(
                name="Test School Merchant",
                username="TestMerchant",
                email=MERCHANT_EMAIL,
                password_hash=bcrypt.hashpw(
                    MERCHANT_PASSWORD.encode("utf-8"),
                    bcrypt.gensalt(),
                ).decode("utf-8"),
                role=UserRole.merchant,
                balance=0.0,
            )
            db.add(merchant)
        else:
            merchant.name = "Test School Merchant"
            merchant.username = "TestMerchant"
            merchant.role = UserRole.merchant

        parent = db.query(User).filter(User.email == "dcarloni@drsrv.net.ar").first()
        if parent and (parent.balance or 0) < 100.0:
            parent.balance = 100.0

        db.commit()
        db.refresh(merchant)
        if parent:
            db.refresh(parent)

        print(f"merchant_id={merchant.id}")
        print(f"merchant_name={merchant.name}")
        print(f"merchant_email={merchant.email}")
        print(f"merchant_balance={merchant.balance}")
        if parent:
            print(f"parent_id={parent.id}")
            print(f"parent_balance={parent.balance}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
