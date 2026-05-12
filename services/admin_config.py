import datetime
import json
import os
from pathlib import Path
from typing import Any


CONFIG_PATH = Path(os.getenv("COLEPAGO_ADMIN_CONFIG", "config/admin_settings.json"))

DEFAULT_ADMIN_SETTINGS: dict[str, Any] = {
    "fee_percent": 2.0,
    "fee_payer": "merchant",
    "currency": "ARS",
    "country": "Argentina",
    "society_profile": "",
    "religion_context": "",
    "local_policy_notes": "",
    "merchant_fee_disclosure": "Merchant pays ColePago fee at payment time.",
    "updated_at": None,
    "updated_by": None,
}


def load_admin_settings() -> dict[str, Any]:
    settings = DEFAULT_ADMIN_SETTINGS.copy()
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                settings.update(loaded)
        except json.JSONDecodeError:
            pass
    return settings


def save_admin_settings(values: dict[str, Any], updated_by: str | None = None) -> dict[str, Any]:
    settings = load_admin_settings()
    settings.update(values)
    settings["updated_at"] = datetime.datetime.utcnow().isoformat()
    settings["updated_by"] = updated_by
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")
    return settings


def commission_percent() -> float:
    settings = load_admin_settings()
    try:
        return float(settings.get("fee_percent", DEFAULT_ADMIN_SETTINGS["fee_percent"]))
    except (TypeError, ValueError):
        return float(DEFAULT_ADMIN_SETTINGS["fee_percent"])
