import pandas as pd
from sqlalchemy import create_engine
from models import School, Base
import os
from geocode_utils import geocode_with_retry

# Update these as needed for your environment
DB_USER = os.getenv('POSTGRES_USER', 'colepago')
DB_PASS = os.getenv('POSTGRES_PASSWORD', 'colepago_pass')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'colepago')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Path to your Excel file
EXCEL_PATH = "d:/kidwall/2026.01.12_padron_oficial_establecimientos_educativos_die.xlsx"
print("Reading Excel file...")
df = pd.read_excel(EXCEL_PATH, sheet_name="padron", header=12)

# Normalize source headers once so lookups are stable across accent/case variants.
df.columns = [str(col).strip() for col in df.columns]

# Rename columns for consistency
df = df.rename(columns={
    'Jurisdicción': 'provincia',
    'Localidad': 'ciudad',
    'Nombre': 'name',
    'Domicilio': 'address',
    'Teléfono': 'phone',
})

GEOCODE_MISSING_COORDS = os.getenv("GEOCODE_MISSING_COORDS", "false").lower() == "true"

# Fill missing columns if not present
def get_col(col):
    return col if col in df.columns else None

# Create DB engine
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

# Insert schools
def insert_schools():
    with engine.begin() as conn:
        # Truncate the schools table before import
        conn.execute(School.__table__.delete())
        for _, row in df.iterrows():
            name = row.get('name', '')
            provincia = row.get('provincia', '')
            ciudad = row.get('ciudad', '')
            comuna = row.get('comuna', None)
            address = row.get('address', None)
            phone = row.get('phone', None)
            latitude = row.get('latitud', None)
            longitude = row.get('longitud', None)
            if pd.isna(phone):
                phone = None
            # If lat/lon missing, geocode
            if GEOCODE_MISSING_COORDS and ((latitude is None or pd.isna(latitude)) or (longitude is None or pd.isna(longitude))):
                if address:
                    latitude, longitude = geocode_with_retry(address, ciudad, provincia)
            school = School(
                name=name,
                provincia=provincia,
                ciudad=ciudad,
                comuna=comuna,
                address=address,
                phone=phone,
                latitude=latitude,
                longitude=longitude
            )
            conn.execute(
                School.__table__.insert().values(
                    name=school.name,
                    provincia=school.provincia,
                    ciudad=school.ciudad,
                    comuna=school.comuna,
                    address=school.address,
                    phone=school.phone,
                    latitude=school.latitude,
                    longitude=school.longitude
                )
            )
    print("Schools loaded successfully.")

if __name__ == "__main__":
    insert_schools()
