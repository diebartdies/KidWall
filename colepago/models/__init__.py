import enum
import os

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


Base = declarative_base()


class UserType(str, enum.Enum):
	parent = 'parent'
	merchant = 'merchant'


class Parent(Base):
	__tablename__ = 'parents'

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, nullable=False)
	email = Column(String, unique=True, index=True, nullable=False)
	password_hash = Column(String, nullable=False)
	balance = Column(Float, default=0.0)
	children = relationship('Child', back_populates='parent', cascade='all, delete-orphan')


class Merchant(Base):
	__tablename__ = 'merchants'

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, nullable=False)
	email = Column(String, unique=True, index=True, nullable=False)
	password_hash = Column(String, nullable=False)
	balance = Column(Float, default=0.0)


class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, nullable=False)
	email = Column(String, unique=True, index=True, nullable=False)
	password_hash = Column(String, nullable=False)
	role = Column(Enum(UserType), nullable=False)
	balance = Column(Float, default=0.0)


class Child(Base):
	__tablename__ = 'children'

	id = Column(Integer, primary_key=True, index=True)
	name = Column(String, nullable=False)
	parent_id = Column(Integer, ForeignKey('parents.id'), nullable=False)
	balance = Column(Float, default=0.0)
	parent = relationship('Parent', back_populates='children')


DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
	postgres_user = os.getenv('POSTGRES_USER', 'postgres')
	postgres_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
	postgres_host = os.getenv('POSTGRES_HOST', 'db')
	postgres_port = os.getenv('POSTGRES_PORT', '5432')
	postgres_db = os.getenv('POSTGRES_DB', 'kidwall')
	DATABASE_URL = (
		f'postgresql+psycopg2://{postgres_user}:{postgres_password}'
		f'@{postgres_host}:{postgres_port}/{postgres_db}'
	)

engine = create_engine(
	DATABASE_URL,
	pool_pre_ping=True,
	connect_args={'timeout': 5, 'check_same_thread': False},
	pool_recycle=3600,
	echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
