import bcrypt

from models import ParentProfile, SessionLocal, User, UserRole


PARENT_EMAIL = "dcarloni@drsrv.net.ar"
TEMP_PASSWORD = "ChangeMe123!"


def main() -> None:
    db = SessionLocal()
    try:
        parent = db.query(User).filter(User.email == PARENT_EMAIL).first()
        if not parent:
            parent = db.query(User).filter(User.email == "test.parent@example.com").first()

        if not parent:
            parent = User(
                password_hash=bcrypt.hashpw(
                    TEMP_PASSWORD.encode("utf-8"),
                    bcrypt.gensalt(),
                ).decode("utf-8"),
                role=UserRole.parent,
                balance=0.0,
            )
            db.add(parent)

        parent.name = "Diego R Carloni"
        parent.username = "DrCarlo"
        parent.email = PARENT_EMAIL
        parent.role = UserRole.parent
        db.commit()
        db.refresh(parent)

        profile = db.query(ParentProfile).filter(ParentProfile.user_id == parent.id).first()
        if not profile:
            profile = ParentProfile(user_id=parent.id)
            db.add(profile)

        profile.relationship_to_child = "parent"
        profile.home_address = "Nahuel Huapi 5050"
        profile.home_floor = "8"
        profile.home_department = "A"
        profile.mobile_phone = "91134679434"
        profile.country_code = "54"
        profile.work_name = "Prisma Medios de Pago"
        profile.work_address = "La pindonga 234"
        profile.work_postal = "1156"
        profile.work_phone = "1143902127"
        profile.work_shift = "dia"
        profile.work_hours = "9:00 to 18:00"
        profile.workplace = "Prisma Medios de Pago"
        profile.email = PARENT_EMAIL

        db.commit()
        db.refresh(profile)

        print(f"parent_id={parent.id}")
        print(f"username={parent.username}")
        print(f"parent_name={parent.name}")
        print(f"parent_email={parent.email}")
        print(f"profile_id={profile.id}")
        print(f"mobile=+{profile.country_code}{profile.mobile_phone}")
        print(f"home_address={profile.home_address}")
        print(f"home_floor={profile.home_floor}")
        print(f"home_department={profile.home_department}")
        print(f"work_name={profile.work_name}")
        print(f"work_address={profile.work_address}")
        print(f"work_postal={profile.work_postal}")
        print(f"work_phone={profile.work_phone}")
        print(f"work_shift={profile.work_shift}")
        print(f"work_hours={profile.work_hours}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
