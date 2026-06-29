"""Vexium Cocina — restaurant business logic (transport-independent).

Second demo vertical (alongside `clinic.py`). Single source of truth for the
restaurant host: profile, menu with prices, specials, dietary info, reservation
policy, table-availability checking, and reservation booking. Same shape as the
dental vertical so the bridge can route to either by name.

In-memory for the demo. Prices/menu are invented but realistic for an upscale
modern Mexican restaurant — tune freely.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

# ── Restaurant profile (override via .env if you like) ──────────────────────
RESTAURANT = {
    "name": os.getenv("REST_NAME", "Vexium Cocina"),
    "address": os.getenv("REST_ADDRESS", "2200 Post Oak Boulevard, Houston, Texas"),
    "phone": os.getenv("REST_PHONE", "(713) 555-0147"),
    "hours_human": os.getenv(
        "REST_HOURS_HUMAN",
        "martes a jueves de 5 a 10 de la noche, viernes y sábado de 5 a 11 de la noche, "
        "domingo de 1 de la tarde a 9 de la noche; lunes cerrado",
    ),
}

# ── Menu (category -> [(dish, price, optional note)]) ───────────────────────
MENU = {
    "Entradas": [
        ("Guacamole hecho en la mesa", "$16"),
        ("Esquites con trufa", "$14"),
        ("Ceviche de pescado del día", "$19"),
        ("Queso fundido con chorizo", "$15"),
        ("Sopa de tortilla", "$12"),
    ],
    "Platos fuertes": [
        ("Mole poblano con pollo de rancho", "$32"),
        ("Carne asada (rib-eye 12 oz)", "$46"),
        ("Pescado a la talla", "$38"),
        ("Cochinita pibil", "$29"),
        ("Enchiladas de mole", "$26"),
    ],
    "Especialidades de la casa": [
        ("Pulpo al pastor", "$42"),
        ("Short rib en adobo (cocción lenta)", "$48"),
        ("Chiles en nogada (de temporada)", "$34"),
    ],
    "Vegano / vegetariano": [
        ("Tacos de hongos al ajillo", "$22"),
        ("Coliflor rostizada con pipián", "$20"),
    ],
    "Postres": [
        ("Pastel de elote tibio", "$11"),
        ("Flan de cajeta", "$10"),
        ("Churros con chocolate de Oaxaca", "$9"),
    ],
    "Bebidas": [
        ("Margarita de la casa", "$14"),
        ("Flight de mezcal (3 destilados)", "$24"),
        ("Aguas frescas", "$6"),
        ("Vinos por copa", "desde $12"),
    ],
}

# Rotating specials — fixed for the demo so it's reproducible on any recording.
SPECIALS = os.getenv(
    "REST_SPECIALS",
    "la pesca del día es robalo a la veracruzana, y el chef recomienda el flight "
    "de mezcal oaxaqueño; los chiles en nogada están de temporada",
)

# Dietary / allergen note (spoken when asked).
DIETARY = (
    "tenemos opciones veganas y vegetarianas (tacos de hongos, coliflor rostizada); "
    "las tortillas son de maíz, naturalmente sin gluten, y la cocina puede adaptar "
    "varios platillos para alergias — siempre conviene avisarnos al reservar"
)

# Reservation / house policy (spoken when relevant).
POLICY = (
    "las reservaciones son recomendadas; para grupos de 8 o más pedimos una tarjeta "
    "para garantizar la mesa y ofrecemos un salón privado para eventos de hasta 30 "
    "personas; el código de vestimenta es smart casual; contamos con valet parking; "
    "los niños son bienvenidos hasta las 8 de la noche y las mascotas solo en la terraza"
)

LARGE_PARTY = 8     # 8+ = card on file to hold the table
PRIVATE_EVENT = 12  # 13+ = route to private events, not a normal table


def menu_text() -> str:
    """Grouped menu for the system prompt."""
    lines = []
    for category, items in MENU.items():
        lines.append(f"  {category}:")
        for dish, price in items:
            lines.append(f"    - {dish}: {price}")
    return "\n".join(lines)


# ── Schedule rules (dinner-focused) ─────────────────────────────────────────
# (open_hour, close_hour) where close_hour is the last hour a seating can START.
BUSINESS_HOURS = {
    1: (17, 22), 2: (17, 22), 3: (17, 22),  # Tue–Thu 5pm–10pm
    4: (17, 23), 5: (17, 23),               # Fri–Sat 5pm–11pm
    6: (13, 21),                            # Sun 1pm–9pm
    # Monday (0) closed — absent from the map.
}

# Demo fixtures: recurring "fully committed" prime times so the "offer
# alternatives" flow is reproducible. Ask for one of THESE to demo alternatives;
# any other open time demos the smooth path.
#   Friday & Saturday prime dinner (7–9pm) booked out · Sunday early evening
BUSY_WEEKLY = {
    4: {19, 20, 21},
    5: {19, 20, 21},
    6: {18, 19},
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
    """Next `n` free hourly seatings at/after `start` (searches up to 14 days)."""
    out: list[str] = []
    cur = start.replace(minute=0, second=0, microsecond=0)
    limit = start + timedelta(days=14)
    while len(out) < n and cur < limit:
        cur += timedelta(hours=1)
        if _slot_free(cur):
            out.append(_fmt(cur))
    return out


def check_table_availability(requested_datetime: str = "", party_size: int = 0, **_) -> dict:
    """Is the requested seating free for this party size? If not, return concrete
    alternatives. Flags large parties (deposit) and oversize ones (private events)."""
    try:
        party = int(party_size or 0)
    except (TypeError, ValueError):
        party = 0

    if party and party > PRIVATE_EVENT:
        return {
            "available": False,
            "reason": "private_event",
            "party_size": party,
            "message": (f"Un grupo de {party} se maneja como evento privado / "
                        "salón privado, no como mesa regular."),
            "alternatives": [],
        }

    dt = _parse(requested_datetime)
    if dt is None:
        return {
            "available": False,
            "reason": "unparseable_datetime",
            "message": "No pude interpretar la fecha y hora.",
            "alternatives": [],
        }

    base = {"requested": _fmt(dt), "party_size": party}
    large = bool(party >= LARGE_PARTY)

    if dt.weekday() not in BUSINESS_HOURS:
        return {**base, "available": False, "reason": "closed_day",
                "message": "El restaurante está cerrado ese día (lunes cerramos).",
                "alternatives": _free_slots_from(dt)}
    if not _is_open(dt):
        oh = BUSINESS_HOURS[dt.weekday()]
        return {**base, "available": False, "reason": "outside_hours",
                "message": f"Ese horario está fuera del servicio ({oh[0]}:00–{oh[1]}:00).",
                "alternatives": _free_slots_from(dt)}
    if _is_busy(dt):
        return {**base, "available": False, "reason": "fully_booked",
                "message": "Esa hora ya está completa.",
                "alternatives": _free_slots_from(dt)}
    return {**base, "available": True, "large_party": large,
            "message": ("Disponible." + (" Grupo grande: se pide tarjeta para garantizar."
                                          if large else ""))}


def _confirmation_code(seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:4].upper()
    return f"VX-{digest}"


def book_reservation(caller_name: str = "", phone: str = "", party_size: int = 0,
                     reservation_datetime: str = "", occasion: str = "",
                     seating_preference: str = "", language: str = "es", **_) -> dict:
    """Record a reservation. (Demo: in-memory; persist later.)"""
    reservation = {
        "caller_name": caller_name,
        "phone": phone,
        "party_size": party_size,
        "reservation_datetime": reservation_datetime,
        "occasion": occasion,
        "seating_preference": seating_preference,
        "language": language,
    }
    code = _confirmation_code(f"{caller_name}|{phone}|{reservation_datetime}|{party_size}")
    return {"status": "confirmed", "confirmation_code": code, "reservation": reservation}
