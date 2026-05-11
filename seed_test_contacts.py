import bcrypt

from models import Child, ParentProfile, SessionLocal, TrustedContact, User, UserRole


TEST_PARENT_EMAIL = "test.parent@example.com"
TEST_PARENT_PASSWORD = "TestParent123!"


def main() -> None:
    db = SessionLocal()
    try:
        parent = db.query(User).filter(User.email == TEST_PARENT_EMAIL).first()
        if not parent:
            parent = User(
                name="Test Parent",
                email=TEST_PARENT_EMAIL,
                password_hash=bcrypt.hashpw(
                    TEST_PARENT_PASSWORD.encode("utf-8"),
                    bcrypt.gensalt(),
                ).decode("utf-8"),
                role=UserRole.parent,
                balance=0.0,
            )
            db.add(parent)
            db.commit()
            db.refresh(parent)

        profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent.id).first()
        if not profile:
            profile = ParentProfile(user_id=parent.id)
            db.add(profile)

        profile.relationship_to_child = "parent"
        profile.mobile_phone = "5550101"
        profile.country_code = "1"
        profile.email = "test.parent.profile@example.com"
        db.commit()
        db.refresh(profile)

        child = (
            db.query(Child)
            .filter(Child.parent_id == parent.id, Child.name == "Test Child")
            .first()
        )
        if not child:
            child = Child(name="Test Child", parent_id=parent.id, balance=100.0)
            db.add(child)

        contacts = [
            {
                "name": "Test Alternate",
                "surname": "One",
                "relation": "aunt",
                "mobile": "5550102",
                "country_code": "1",
                "email": "test.alternate.one@example.com",
            },
            {
                "name": "Test Alternate",
                "surname": "Two",
                "relation": "uncle",
                "mobile": "5550103",
                "country_code": "1",
                "email": "test.alternate.two@example.com",
            },
        ]
        existing = {(c.name, c.surname, c.email) for c in profile.trusted_contacts}
        for contact in contacts:
            key = (contact["name"], contact["surname"], contact["email"])
            if key not in existing:
                db.add(TrustedContact(parent_profile_id=profile.id, **contact))

        db.commit()
        db.refresh(child)
        db.refresh(profile)

        print(f"parent_id={parent.id}")
        print(f"parent_email={parent.email}")
        print(f"profile_id={profile.id}")
        print(f"child_id={child.id}")
        print(f"trusted_contacts={len(profile.trusted_contacts)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
