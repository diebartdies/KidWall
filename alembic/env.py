from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env so DATABASE_URL picks up local credentials
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from models import Base

config = context.config
fileConfig(config.config_file_name)

# Build URL from env vars (overrides alembic.ini sqlalchemy.url)
_db_user = os.getenv('POSTGRES_USER', 'colepago')
_db_pass = os.getenv('POSTGRES_PASSWORD', 'Palo1010')
_db_host = os.getenv('POSTGRES_HOST', 'localhost')
if _db_host == 'db':   # Docker service name → use host-mapped address
    _db_host = 'localhost'
_db_port = os.getenv('POSTGRES_PORT', '5433')
_db_name = os.getenv('POSTGRES_DB', 'colepago')
config.set_main_option(
    'sqlalchemy.url',
    f'postgresql+psycopg2://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}'
)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
