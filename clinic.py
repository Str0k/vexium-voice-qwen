"""Vexium Dental — clinic business logic (transport-independent).

Single source of truth for the demo receptionist: clinic profile, service catalog
with prices, opening hours, availability checking, and booking. Imported by both
`agent_config.py` (to build the system prompt) and `dev_client.py` (to handle the
client-side function calls), and reused by the Twilio bridge in Phase 3.

For the MVP/demo this is all in-memory. Phase 4 will persist bookings to
`appointments.json`. Prices/services are invented but realistic — tune freely.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

# ── Clinic profile (override via .env if you like) ──────────────────────────
CLINIC = {
    "name": os.getenv("BUSINESS_NAME", "Vexium Dental"),
    "address": os.getenv("BUSINESS_ADDRESS", "1820 Westheimer Road, Houston, Texas"),
    "phone": os.getenv("BUSINESS_PHONE", "(713) 555-0182"),
    "hours_human": os.getenv(
        "BUSINESS_HOURS_HUMAN",
        "lunes a viernes de 9 de la mañana a 6 de la tarde, "
        "sábados de 9 a 2, domingos cerrado",
    ),
}

# ── Service catalog (name, approximate price, optional note) ────────────────
# Final price is always "confirmed after the dentist's evaluation".
SERVICES = [
    ("Consulta y evaluación inicial", "gratis la primera visita (después $75)"),
    ("Limpieza dental", "$89"),
    ("Limpieza profunda", "$220 por cuadrante"),
    ("Blanqueamiento", "$349"),
    ("Resina o empaste", "desde $160"),
    ("Extracción simple", "$145"),
    ("Extracción de muela del juicio", "desde $350"),
    ("Corona dental", "desde $999"),
    ("Endodoncia (tratamiento de nervio)", "desde $850"),
    ("Ortodoncia / brackets", "consulta $49, tratamiento desde $3,200"),
    ("Emergencia dental", "evaluación $99"),
]


def services_text() -> str:
    """Bulleted price list for the system prompt."""
    return "\n".join(f"  - {name}: {price}" for name, price in SERVICES)


# ── Schedule rules ──────────────────────────────────────────────────────────
# Opening hours per weekday (Monday=0 … Sunday=6). (open_hour, close_hour) where
# close_hour is the last hour an appointment can START (1-hour slots).
BUSINESS_HOURS = {
    0: (9, 18), 1: (9, 18), 2: (9, 18), 3: (9, 18), 4: (9, 18),  # Mon–Fri
    5: (9, 14),                                                    # Sat
    # Sunday (6) closed — absent from the map.
}

# Demo fixtures: recurring "already booked" hours per weekday, so the
# availability flow is reproducible no matter what date you record on.
# Ask for one of THESE slots to demo the "offer alternatives" path; ask for any
# other open time to demo the smooth path.
#   Monday mornings full · Wednesday afternoons · Friday late · Saturday midday
BUSY_WEEKLY = {
    0: {9, 10, 11},
    2: {15, 16},
    4: {16, 17},
    5: {12, 13},
}


def _parse(dt_str: str) -> datetime | None:
    s = (dt_str or "").strip().replace(" ", "T")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _is_open(dt: datetime) -> bool:
    hours = BUSINESS_HOURS.get(dt.weekday())
    return bool(hours) and hours[0] <= dt.hour < hours[1]


def _is_busy(dt: datetime) -> bool:
    return dt.hour in BUSY_WEEKLY.get(dt.weekday(), set())


def _slot_free(dt: datetime) -> bool:
    return _is_open(dt) and not _is_busy(dt)


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M")


def _free_slots_from(start: datetime, n: int = 3) -> list[str]:
    """Next `n` free hourly slots at/after `start` (searches up to 14 days)."""
    out: list[str] = []
    cur = start.replace(minute=0, second=0, microsecond=0)
    limit = start + timedelta(days=14)
    while len(out) < n and cur < limit:
        cur += timedelta(hours=1)
        if _slot_free(cur):
            out.append(_fmt(cur))
    return out


def check_availability(requested_datetime: str = "", **_) -> dict:
    """Is the requested slot free? If not, return concrete alternatives."""
    dt = _parse(requested_datetime)
    if dt is None:
        return {
            "available": False,
            "reason": "unparseable_datetime",
            "message": "No pude interpretar la fecha y hora.",
            "alternatives": [],
        }
    base = {"requested": _fmt(dt)}
    if dt.weekday() not in BUSINESS_HOURS:
        return {**base, "available": False, "reason": "closed_day",
                "message": "La clínica está cerrada ese día.",
                "alternatives": _free_slots_from(dt)}
    if not _is_open(dt):
        oh = BUSINESS_HOURS[dt.weekday()]
        return {**base, "available": False, "reason": "outside_hours",
                "message": f"Ese horario está fuera del horario de atención "
                           f"({oh[0]}:00–{oh[1]}:00).",
                "alternatives": _free_slots_from(dt)}
    if _is_busy(dt):
        return {**base, "available": False, "reason": "slot_taken",
                "message": "Ese horario ya está reservado.",
                "alternatives": _free_slots_from(dt)}
    return {**base, "available": True, "message": "Disponible."}


def _confirmation_code(seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:4].upper()
    return f"VX-{digest}"


def book_appointment(caller_name: str = "", phone: str = "", service: str = "",
                     preferred_datetime: str = "", language: str = "es", **_) -> dict:
    """Record a booking. Phase 4 will persist this to appointments.json."""
    booking = {
        "caller_name": caller_name,
        "phone": phone,
        "service": service,
        "preferred_datetime": preferred_datetime,
        "language": language,
    }
    code = _confirmation_code(f"{caller_name}|{phone}|{preferred_datetime}")
    return {"status": "confirmed", "confirmation_code": code, "booking": booking}
