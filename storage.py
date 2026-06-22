"""
storage.py
ለ Multi-Tenant Telegram Shop Bot የተዘጋጀ ቀላል JSON-based data layer።

ለምን JSON ፋይል? ለ MVP/pilot ደረጅ ቀላል እና ፍጥነት ያለው ስለሆነ።
ነጋዴዎች ቁጥር ብዙ ሲሆን (ከ50+) ወደ SQLite ወይም PostgreSQL መቀየር ይመከራል።
"""

import json
import os
import threading
from typing import Optional

STORES_FILE = "stores.json"
ORDERS_FILE = "orders.json"

# ብዙ ጥያቄዎች በአንድ ጊዜ ፋይል ላይ ሲፅፉ እንዳይጋጭ የሚከላከል lock
_lock = threading.Lock()


def _read_json(path: str, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default


def _write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ====================== STORES ======================
def get_all_stores() -> dict:
    with _lock:
        return _read_json(STORES_FILE, {})


def get_store(store_id: str) -> Optional[dict]:
    return get_all_stores().get(store_id)


def get_store_by_owner(owner_id: int) -> Optional[tuple]:
    """ለ owner_id (የነጋዴው Telegram ID) ስቶር ካለ (store_id, store_data) ይመልሳል"""
    for sid, data in get_all_stores().items():
        if data.get("owner_id") == owner_id:
            return sid, data
    return None


def save_store(store_id: str, store_data: dict) -> None:
    with _lock:
        stores = _read_json(STORES_FILE, {})
        stores[store_id] = store_data
        _write_json(STORES_FILE, stores)


def add_product(store_id: str, key: str, name: str, price: int) -> None:
    with _lock:
        stores = _read_json(STORES_FILE, {})
        if store_id not in stores:
            return
        stores[store_id].setdefault("products", {})[key] = {"name": name, "price": price}
        _write_json(STORES_FILE, stores)


def remove_product(store_id: str, key: str) -> None:
    with _lock:
        stores = _read_json(STORES_FILE, {})
        if store_id in stores and key in stores[store_id].get("products", {}):
            del stores[store_id]["products"][key]
            _write_json(STORES_FILE, stores)


# ====================== ORDERS ======================
def save_order(order: dict) -> None:
    with _lock:
        orders = _read_json(ORDERS_FILE, [])
        orders.append(order)
        _write_json(ORDERS_FILE, orders)


def get_orders_for_store(store_id: str, limit: int = 10) -> list:
    orders = _read_json(ORDERS_FILE, [])
    store_orders = [o for o in orders if o.get("store_id") == store_id]
    return store_orders[-limit:]
