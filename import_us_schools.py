import csv
import struct
from pathlib import Path

from models import School, SessionLocal


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "schools"
PUBLIC_CCD = DATA_DIR / "ccd_public_2024_25_prelim" / "ccd_sch_029_2425_w_0a_051425.csv"
PUBLIC_EDGE = DATA_DIR / "edge_public_2024_25" / "EDGE_GEOCODE_PUBLICSCH_2425.TXT"
PRIVATE_EDGE_DBF = DATA_DIR / "edge_private_2023_24" / "EDGE_GEOCODE_PRIVATESCH_2324.dbf"


PUBLIC_EDGE_COLUMNS = [
    "NCESSCH",
    "LEAID",
    "NAME",
    "OPSTFIPS",
    "STREET",
    "CITY",
    "STATE",
    "ZIP",
    "STFIP",
    "CNTY",
    "NMCNTY",
    "LOCALE",
    "LAT",
    "LON",
    "CBSA",
    "NMCBSA",
    "CBSATYPE",
    "CSA",
    "NMCSA",
    "CD",
    "SLDL",
    "SLDU",
    "SCHOOLYEAR",
]


def _clean(value):
    if value is None:
        return None
    value = str(value).strip()
    if value in {"", "-1", "-2", "N", "M"}:
        return None
    return value


def _float_or_none(value):
    value = _clean(value)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _load_public_edge():
    geocodes = {}
    if not PUBLIC_EDGE.exists():
        return geocodes
    with PUBLIC_EDGE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, delimiter="|")
        for row in reader:
            if len(row) < len(PUBLIC_EDGE_COLUMNS):
                continue
            item = dict(zip(PUBLIC_EDGE_COLUMNS, row))
            geocodes[item["NCESSCH"]] = item
    return geocodes


def _read_dbf(path: Path):
    data = path.read_bytes()
    record_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]

    fields = []
    offset = 32
    while data[offset] != 13:
        raw = data[offset : offset + 32]
        name = raw[:11].split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        field_type = chr(raw[11])
        length = raw[16]
        decimals = raw[17]
        fields.append((name, field_type, length, decimals))
        offset += 32

    for index in range(record_count):
        record_start = header_len + index * record_len
        record = data[record_start : record_start + record_len]
        if not record or record[:1] == b"*":
            continue
        position = 1
        row = {}
        for name, field_type, length, _decimals in fields:
            raw_value = record[position : position + length]
            position += length
            text = raw_value.decode("utf-8", errors="ignore").strip()
            if field_type in {"N", "F"}:
                row[name] = _float_or_none(text) if "." in text else _clean(text)
            else:
                row[name] = _clean(text)
        yield row


def _existing_by_source(db, source: str):
    rows = db.query(School).filter(School.source == source).all()
    return {row.external_id: row for row in rows if row.external_id}


def import_public_schools(db):
    edge = _load_public_edge()
    existing = _existing_by_source(db, "nces_ccd_public")
    imported = 0
    updated = 0

    with PUBLIC_CCD.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            external_id = _clean(row.get("NCESSCH"))
            if not external_id:
                continue
            geo = edge.get(external_id, {})
            school = existing.get(external_id)
            if not school:
                school = School(
                    source="nces_ccd_public",
                    external_id=external_id,
                    sector="public",
                    provincia=_clean(row.get("LSTATE")) or _clean(row.get("MSTATE")) or _clean(row.get("ST")) or "US",
                    ciudad=_clean(row.get("LCITY")) or _clean(row.get("MCITY")) or "Unknown",
                    name=_clean(row.get("SCH_NAME")) or "Unknown school",
                )
                db.add(school)
                existing[external_id] = school
                imported += 1
            else:
                updated += 1

            school.source_year = _clean(row.get("SCHOOL_YEAR")) or "2024-2025"
            school.district_id = _clean(row.get("LEAID"))
            school.district_name = _clean(row.get("LEA_NAME"))
            school.name = _clean(row.get("SCH_NAME")) or school.name
            school.provincia = _clean(row.get("LSTATE")) or _clean(row.get("MSTATE")) or _clean(row.get("ST")) or school.provincia
            school.ciudad = _clean(row.get("LCITY")) or _clean(row.get("MCITY")) or school.ciudad
            school.address = _clean(row.get("LSTREET1")) or _clean(row.get("MSTREET1")) or school.address
            school.postal_code = _clean(row.get("LZIP")) or _clean(row.get("MZIP"))
            school.phone = _clean(row.get("PHONE"))
            school.website = _clean(row.get("WEBSITE"))
            school.level = _clean(row.get("LEVEL"))
            school.low_grade = _clean(row.get("GSLO"))
            school.high_grade = _clean(row.get("GSHI"))
            school.locale_code = _clean(geo.get("LOCALE"))
            school.county_name = _clean(geo.get("NMCNTY"))
            school.latitude = _float_or_none(geo.get("LAT"))
            school.longitude = _float_or_none(geo.get("LON"))

            if (imported + updated) % 5000 == 0:
                db.commit()

    db.commit()
    return imported, updated


def import_private_schools(db):
    existing = _existing_by_source(db, "nces_edge_private")
    imported = 0
    updated = 0

    for row in _read_dbf(PRIVATE_EDGE_DBF):
        external_id = _clean(row.get("PPIN"))
        if not external_id:
            continue
        school = existing.get(external_id)
        if not school:
            school = School(
                source="nces_edge_private",
                external_id=external_id,
                sector="private",
                provincia=_clean(row.get("STATE")) or "US",
                ciudad=_clean(row.get("CITY")) or "Unknown",
                name=_clean(row.get("NAME")) or "Unknown school",
            )
            db.add(school)
            existing[external_id] = school
            imported += 1
        else:
            updated += 1

        school.source_year = _clean(row.get("SCHOOLYEAR")) or "2023-2024"
        school.name = _clean(row.get("NAME")) or school.name
        school.provincia = _clean(row.get("STATE")) or school.provincia
        school.ciudad = _clean(row.get("CITY")) or school.ciudad
        school.address = _clean(row.get("STREET"))
        school.postal_code = _clean(row.get("ZIP"))
        school.locale_code = _clean(row.get("LOCALE"))
        school.county_name = _clean(row.get("NAMELSAD"))
        school.latitude = _float_or_none(row.get("LAT"))
        school.longitude = _float_or_none(row.get("LON"))

        if (imported + updated) % 5000 == 0:
            db.commit()

    db.commit()
    return imported, updated


def main():
    for required in [PUBLIC_CCD, PUBLIC_EDGE, PRIVATE_EDGE_DBF]:
        if not required.exists():
            raise FileNotFoundError(required)

    db = SessionLocal()
    try:
        public_imported, public_updated = import_public_schools(db)
        private_imported, private_updated = import_private_schools(db)
        public_total = db.query(School).filter(School.source == "nces_ccd_public").count()
        private_total = db.query(School).filter(School.source == "nces_edge_private").count()
        print(f"public_imported={public_imported}")
        print(f"public_updated={public_updated}")
        print(f"public_total={public_total}")
        print(f"private_imported={private_imported}")
        print(f"private_updated={private_updated}")
        print(f"private_total={private_total}")
        print(f"combined_total={public_total + private_total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
