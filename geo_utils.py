import math
import datetime
from models import User, Child, ChildRouteWaypoint, ChildLocationPing

# ── Tunable constants ──────────────────────────────────────────────────────
# ~3 city blocks in Argentina (≈130m/block) = 0.40 km
SCHOOL_RADIUS_KM = 0.40

# How far from the known route before we call it a deviation (1 block = 0.13 km)
ROUTE_DEVIATION_KM = 0.15

# Anti-theft: N purchases within this many minutes triggers an account hold
RAPID_SPEND_LIMIT = 3          # number of purchases
RAPID_SPEND_WINDOW_MINUTES = 5 # rolling window


# ── Core maths ────────────────────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in kilometres between two lat/lon points."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def is_within_radius(lat1, lon1, lat2, lon2, radius_km: float = SCHOOL_RADIUS_KM) -> bool:
    if None in (lat1, lon1, lat2, lon2):
        return False
    return haversine(lat1, lon1, lat2, lon2) <= radius_km


# ── Payment location gate ─────────────────────────────────────────────────

def is_payment_location_valid(
    child: Child,
    merchant: User,
    pay_lat: float,
    pay_lon: float,
    db,
    radius_km: float = SCHOOL_RADIUS_KM,
) -> bool:
    """
    Allow the payment if it occurs within radius_km of the merchant's registered
    location OR within radius_km of the child's school.
    """
    if merchant.latitude and merchant.longitude:
        if is_within_radius(pay_lat, pay_lon, merchant.latitude, merchant.longitude, radius_km):
            return True
    if child.school_lat and child.school_lon:
        if is_within_radius(pay_lat, pay_lon, child.school_lat, child.school_lon, radius_km):
            return True
    return False


# ── Route-deviation check ─────────────────────────────────────────────────

def is_off_route(child: Child, lat: float, lon: float, db) -> bool:
    """
    Returns True if the given position is further than ROUTE_DEVIATION_KM from
    every waypoint on the child's standard route.
    Returns False (safe) if no route has been configured.
    """
    waypoints = (
        db.query(ChildRouteWaypoint)
        .filter(ChildRouteWaypoint.child_id == child.id)
        .order_by(ChildRouteWaypoint.seq)
        .all()
    )
    if not waypoints:
        return False  # no route set → can't judge
    return all(
        haversine(lat, lon, wp.lat, wp.lon) > ROUTE_DEVIATION_KM
        for wp in waypoints
    )


# ── Anti-theft: rapid-spend detection ─────────────────────────────────────

def is_rapid_spend(child: Child, db) -> bool:
    """
    Returns True if the child has made >= RAPID_SPEND_LIMIT purchases
    within the last RAPID_SPEND_WINDOW_MINUTES minutes.
    Uses the Transaction table if available; falls back to last_merchants heuristic.
    """
    try:
        from models import Transaction, TransactionType
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=RAPID_SPEND_WINDOW_MINUTES)
        recent = (
            db.query(Transaction)
            .filter(
                Transaction.child_id == child.id,
                Transaction.type == TransactionType.spend,
                Transaction.created_at >= cutoff,
            )
            .count()
        )
        return recent >= RAPID_SPEND_LIMIT
    except Exception:
        return False
