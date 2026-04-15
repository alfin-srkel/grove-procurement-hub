import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import hashlib, secrets, time, json
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
CACHE_TTL = 300

def get_client():
    if "gs_client" not in st.session_state:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        st.session_state["gs_client"] = gspread.authorize(creds)
    return st.session_state["gs_client"]

def get_sheet(name):
    client = get_client()
    spreadsheet_id = st.secrets["spreadsheet"]["id"]
    sh = client.open_by_key(spreadsheet_id)
    return sh.worksheet(name)

def _cache_get(key):
    cache = st.session_state.setdefault("_db_cache", {})
    entry = cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None

def _cache_set(key, data):
    cache = st.session_state.setdefault("_db_cache", {})
    cache[key] = {"data": data, "ts": time.time()}

def _cache_clear(prefix=None):
    cache = st.session_state.get("_db_cache", {})
    if prefix:
        keys = [k for k in cache if k.startswith(prefix)]
        for k in keys:
            del cache[k]
    else:
        cache.clear()

# ── Auth ──────────────────────────────────────────────
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return h, salt

def get_user(email):
    cached = _cache_get(f"user:{email}")
    if cached is not None:
        return cached
    ws = get_sheet("Users")
    rows = ws.get_all_records()
    user = next((r for r in rows if r.get("email", "").lower() == email.lower()), None)
    _cache_set(f"user:{email}", user)
    return user

def verify_password(email, password):
    user = get_user(email)
    if not user:
        return None
    h, _ = hash_password(password, user.get("salt", ""))
    if h == user.get("password_hash", ""):
        return user
    return None

def create_user(email, name, role, password):
    h, salt = hash_password(password)
    ws = get_sheet("Users")
    ws.append_row([email, name, role, h, salt, datetime.now().strftime("%Y-%m-%d %H:%M")])
    _cache_clear("user:")
    _cache_clear("all_users")

def get_all_users():
    cached = _cache_get("all_users")
    if cached is not None:
        return cached
    ws = get_sheet("Users")
    rows = ws.get_all_records()
    _cache_set("all_users", rows)
    return rows

def has_users():
    cached = _cache_get("has_users")
    if cached is not None:
        return cached
    ws = get_sheet("Users")
    vals = ws.col_values(1)
    result = len(vals) > 1
    _cache_set("has_users", result)
    return result

# ── Vendors ───────────────────────────────────────────
def get_vendors():
    cached = _cache_get("vendors")
    if cached is not None:
        return cached
    ws = get_sheet("Vendors")
    rows = ws.get_all_records()
    _cache_set("vendors", rows)
    return rows

def add_vendor(data):
    ws = get_sheet("Vendors")
    existing = get_vendors()
    next_id = f"V{len(existing)+1:03d}"
    row = [
        next_id,
        data["vendor_name"],
        data["category"],
        data.get("subcategory", ""),
        data.get("contact_person", ""),
        data.get("phone", ""),
        data.get("email", ""),
        data.get("address", ""),
        data.get("rating", 0),
        data.get("notes", ""),
        datetime.now().strftime("%Y-%m-%d"),
        "Active",
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")
    _cache_clear("vendors")
    return next_id

def update_vendor(vendor_id, data):
    ws = get_sheet("Vendors")
    cell = ws.find(vendor_id, in_column=1)
    if not cell:
        return False
    row = cell.row
    for col_name, col_idx in [
        ("vendor_name", 2), ("category", 3), ("subcategory", 4),
        ("contact_person", 5), ("phone", 6), ("email", 7),
        ("address", 8), ("rating", 9), ("notes", 10), ("status", 12),
    ]:
        if col_name in data:
            ws.update_cell(row, col_idx, data[col_name])
    _cache_clear("vendors")
    return True

# ── Items ─────────────────────────────────────────────
def get_items():
    cached = _cache_get("items")
    if cached is not None:
        return cached
    ws = get_sheet("Items")
    rows = ws.get_all_records()
    _cache_set("items", rows)
    return rows

def add_item(data):
    ws = get_sheet("Items")
    existing = get_items()
    next_id = f"ITM{len(existing)+1:03d}"
    row = [
        next_id,
        data["vendor_id"],
        data["category"],
        data["item_name"],
        data.get("description", ""),
        data.get("unit", "pcs"),
        data.get("unit_price", 0),
        data.get("min_order", 1),
        data.get("lead_time_days", 0),
        datetime.now().strftime("%Y-%m-%d"),
        data.get("source", "Manual"),
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")
    _cache_clear("items")
    return next_id

def update_item(item_id, data):
    ws = get_sheet("Items")
    cell = ws.find(item_id, in_column=1)
    if not cell:
        return False
    row = cell.row
    for col_name, col_idx in [
        ("vendor_id", 2), ("category", 3), ("item_name", 4),
        ("description", 5), ("unit", 6), ("unit_price", 7),
        ("min_order", 8), ("lead_time_days", 9),
    ]:
        if col_name in data:
            ws.update_cell(row, col_idx, data[col_name])
    ws.update_cell(row, 10, datetime.now().strftime("%Y-%m-%d"))
    _cache_clear("items")
    return True

# ── Procurement Cart ──────────────────────────────────
def save_cart(cart_items, created_by, purpose):
    ws = get_sheet("ProcurementCart")
    cart_id = f"CART-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []
    for item in cart_items:
        rows.append([
            cart_id, created_by, ts,
            item.get("item_id", ""),
            item.get("vendor_id", ""),
            item["item_name"],
            item["qty"],
            item["unit_price"],
            item["qty"] * item["unit_price"],
            purpose,
            "Draft",
        ])
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
    return cart_id

# ── Search Log ────────────────────────────────────────
def log_search(email, query, source, results_count):
    try:
        ws = get_sheet("SearchLog")
        ws.append_row([
            f"SRC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            email,
            query,
            source,
            results_count,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ], value_input_option="USER_ENTERED")
    except Exception:
        pass

# ── Stats ─────────────────────────────────────────────
def get_dashboard_stats():
    cached = _cache_get("dashboard_stats")
    if cached is not None:
        return cached
    vendors = get_vendors()
    items = get_items()
    active_vendors = len([v for v in vendors if v.get("status") == "Active"])
    categories = list(set(v.get("category", "") for v in vendors if v.get("category")))
    stats = {
        "total_vendors": len(vendors),
        "active_vendors": active_vendors,
        "total_items": len(items),
        "categories": categories,
        "category_count": len(categories),
    }
    _cache_set("dashboard_stats", stats)
    return stats
