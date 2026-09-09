
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import re
import hashlib
import json
import io
import zipfile
import uuid
from pathlib import Path
from datetime import datetime, date, timedelta

# ============================================================
# PERFUME OS
# Sistema operativo integral para negocio de perfumería
# Un solo archivo Streamlit + Google Sheets como única persistencia
# ============================================================

APP_NAME = "PERFUME OS"
APP_VERSION = "2.2.0-SHEETS-STABLE"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# UI / THEME
# -----------------------------
st.markdown(
    """
    <style>
    :root{
        --bg:#f6f7f9;
        --card:#ffffff;
        --ink:#17191c;
        --muted:#737983;
        --line:#e7e9ee;
        --accent:#22252a;
        --soft:#eef0f3;
        --good:#177a52;
        --warn:#9b6a00;
        --bad:#b23a3a;
    }
    .stApp { background: var(--bg); color: var(--ink); }
    section[data-testid="stSidebar"] {
        background: #fbfbfc;
        border-right: 1px solid var(--line);
    }
    section[data-testid="stSidebar"] > div { padding-top: 1.0rem; }
    .block-container { padding-top: 1.1rem; padding-bottom: 4rem; max-width: 1600px; }
    h1,h2,h3 { letter-spacing:-0.025em; }
    [data-testid="stMetric"]{
        background:var(--card);
        border:1px solid var(--line);
        border-radius:18px;
        padding:15px 17px;
        box-shadow:0 6px 24px rgba(10,18,30,.035);
    }
    [data-testid="stMetricLabel"] { color:var(--muted); }
    div[data-testid="stDataFrame"]{
        background:var(--card);
        border:1px solid var(--line);
        border-radius:16px;
        overflow:hidden;
    }
    .hero{
        background:linear-gradient(135deg,#17191c,#343941);
        color:white;border-radius:24px;padding:26px 28px;
        box-shadow:0 18px 50px rgba(0,0,0,.12);
        margin-bottom:18px;
    }
    .hero .eyebrow{opacity:.66;font-size:.8rem;text-transform:uppercase;letter-spacing:.12em;}
    .hero h1{margin:.2rem 0 .3rem 0;font-size:2.1rem;}
    .hero p{margin:0;opacity:.78;max-width:1000px;}
    .section{
        background:var(--card); border:1px solid var(--line);
        border-radius:20px;padding:18px 20px;margin:8px 0 16px 0;
    }
    .pill{
        display:inline-block;padding:4px 9px;border-radius:999px;background:#eef0f3;
        margin-right:5px;font-size:.78rem;color:#4a4f57;
    }
    .status-good{color:var(--good);font-weight:700}
    .status-warn{color:var(--warn);font-weight:700}
    .status-bad{color:var(--bad);font-weight:700}
    .mini{font-size:.83rem;color:var(--muted)}
    .big-number{font-size:1.9rem;font-weight:800;letter-spacing:-.04em}
    .product-card{
        background:white;border:1px solid var(--line);border-radius:18px;
        padding:16px;height:100%;
    }
    .product-title{font-size:1.02rem;font-weight:800;}
    .product-sub{color:var(--muted);font-size:.84rem}
    .brand{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:#666}
    .stButton button, .stDownloadButton button{
        border-radius:12px!important;border:1px solid #dfe2e7!important;
        min-height:2.55rem;
    }
    .stButton button[kind="primary"]{
        background:#1f2227!important;color:white!important;border-color:#1f2227!important;
    }
    hr{border-color:var(--line);}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# HELPERS
# -----------------------------
def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def today_iso():
    return date.today().isoformat()

def money(v):
    try:
        return f"$ {float(v):,.0f}".replace(",", ".")
    except Exception:
        return "$ 0"

def pct(v):
    try:
        return f"{float(v):.1f}%"
    except Exception:
        return "0.0%"

def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default

def safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def uid(prefix=""):
    return f"{prefix}{uuid.uuid4().hex[:10].upper()}"

# ============================================================
# GOOGLE SHEETS BACKEND
# Google Sheets is the single persistent source of truth.
# SQLite is used ONLY as an in-memory query/cache engine while
# the Streamlit process is running. No .db file is created.
# ============================================================
SPREADSHEET_NAME = "Parfum"
CREDENTIALS_FILE = Path(__file__).with_name("service_account.json")

SHEET_NAMES = {
    "settings": "configuracion",
    "users": "usuarios",
    "suppliers": "proveedores",
    "vendors": "vendedores",
    "customers": "clientes",
    "products": "productos",
    "inventory_moves": "movimientos_stock",
    "purchases": "compras",
    "purchase_items": "items_compras",
    "sales": "ventas",
    "sale_items": "items_ventas",
    "cash_moves": "caja",
    "expenses": "gastos",
    "reservations": "reservas",
    "account_ledger": "cuentas_corrientes",
    "promotions": "promociones",
    "decant_pools": "decants_pool",
    "campaign_log": "campanas",
}
TABLE_ORDER = list(SHEET_NAMES.keys())

SCHEMA_SQL = r"""
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'Admin',
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS suppliers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT,
            phone TEXT,
            email TEXT,
            country TEXT,
            tax_id TEXT,
            notes TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS vendors(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            commission_pct REAL DEFAULT 0,
            notes TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS customers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            instagram TEXT,
            email TEXT,
            birthday TEXT,
            gender TEXT,
            preferred_families TEXT,
            notes TEXT,
            vip INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            barcode TEXT,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            line TEXT,
            gender TEXT,
            concentration TEXT,
            size_ml REAL DEFAULT 0,
            origin_country TEXT,
            category TEXT,
            product_type TEXT DEFAULT 'PERFUME',
            parent_product_id INTEGER,
            olfactory_family TEXT,
            top_notes TEXT,
            heart_notes TEXT,
            base_notes TEXT,
            season TEXT,
            use_time TEXT,
            batch_code TEXT,
            supplier_id INTEGER,
            avg_cost REAL DEFAULT 0,
            sale_price REAL DEFAULT 0,
            wholesale_price REAL DEFAULT 0,
            reseller_price REAL DEFAULT 0,
            promo_price REAL DEFAULT 0,
            min_stock REAL DEFAULT 0,
            location TEXT,
            sellable INTEGER DEFAULT 1,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY(parent_product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS inventory_moves(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            move_type TEXT NOT NULL,
            qty REAL NOT NULL,
            unit_cost REAL DEFAULT 0,
            reference_type TEXT,
            reference_id INTEGER,
            notes TEXT,
            user_name TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS purchases(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            supplier_id INTEGER,
            invoice TEXT,
            payment_method TEXT,
            shipping REAL DEFAULT 0,
            fees REAL DEFAULT 0,
            taxes REAL DEFAULT 0,
            items_subtotal REAL DEFAULT 0,
            total REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            status TEXT DEFAULT 'Recibida',
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        );

        CREATE TABLE IF NOT EXISTS purchase_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            qty REAL NOT NULL,
            unit_price REAL NOT NULL,
            landed_unit_cost REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY(purchase_id) REFERENCES purchases(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS sales(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            customer_id INTEGER,
            vendor_id INTEGER,
            channel TEXT,
            payment_method TEXT,
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            shipping REAL DEFAULT 0,
            total REAL DEFAULT 0,
            cost REAL DEFAULT 0,
            profit REAL DEFAULT 0,
            margin REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            status TEXT DEFAULT 'Completada',
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS sale_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            qty REAL NOT NULL,
            unit_price REAL NOT NULL,
            unit_cost REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY(sale_id) REFERENCES sales(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS cash_moves(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            direction TEXT NOT NULL,
            category TEXT NOT NULL,
            method TEXT,
            amount REAL NOT NULL,
            reference_type TEXT,
            reference_id INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT,
            supplier TEXT,
            method TEXT,
            amount REAL NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reservations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            customer_id INTEGER,
            product_id INTEGER,
            qty REAL DEFAULT 1,
            deposit REAL DEFAULT 0,
            total REAL DEFAULT 0,
            due_date TEXT,
            status TEXT DEFAULT 'Consulta',
            vendor_id INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(product_id) REFERENCES products(id),
            FOREIGN KEY(vendor_id) REFERENCES vendors(id)
        );

        CREATE TABLE IF NOT EXISTS account_ledger(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            concept TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            reference_type TEXT,
            reference_id INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS promotions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            promo_type TEXT,
            value REAL DEFAULT 0,
            start_date TEXT,
            end_date TEXT,
            min_qty REAL DEFAULT 1,
            scope TEXT DEFAULT 'Todos',
            active INTEGER DEFAULT 1,
            notes TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS decant_pools(
            product_id INTEGER PRIMARY KEY,
            available_ml REAL DEFAULT 0,
            updated_at TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS campaign_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            name TEXT NOT NULL,
            channel TEXT,
            spend REAL DEFAULT 0,
            attributed_sales REAL DEFAULT 0,
            attributed_profit REAL DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        """


def _safe_secret_keys():
    """Devuelve solamente nombres de secrets; nunca valores."""
    try:
        return sorted([str(k) for k in st.secrets.keys()])
    except Exception:
        return []


def _mapping_to_dict(obj):
    try:
        return {str(k): obj[k] for k in obj.keys()}
    except Exception:
        try:
            return dict(obj)
        except Exception:
            return None


def _looks_like_service_account(d):
    if not isinstance(d, dict):
        return False
    required = {"project_id", "private_key", "client_email", "token_uri"}
    return required.issubset(set(d.keys()))


def _normalize_private_key(d):
    if not isinstance(d, dict):
        return d
    out = dict(d)
    pk = out.get("private_key")
    if isinstance(pk, str):
        # Soporta secretos pegados con \n literales o saltos reales.
        out["private_key"] = pk.replace("\\n", "\n")
    return out


def _diagnostic_sheet_id():
    """Busca el ID del Sheet en todas las formas admitidas y acepta también una URL completa."""
    raw = None
    source = None
    try:
        for key in ["GOOGLE_SHEET_ID", "google_sheet_id", "SHEET_ID", "GSHEET_ID", "SPREADSHEET_ID"]:
            if key in st.secrets and str(st.secrets[key]).strip():
                raw = str(st.secrets[key]).strip()
                source = key
                break

        if not raw:
            for section in ["sheets", "google_sheets"]:
                if section in st.secrets:
                    sec = _mapping_to_dict(st.secrets[section]) or {}
                    for key in ["sheet_id", "spreadsheet_id", "id"]:
                        if key in sec and str(sec[key]).strip():
                            raw = str(sec[key]).strip()
                            source = f"{section}.{key}"
                            break
                    if raw:
                        break
    except Exception:
        pass

    if not raw:
        return None, None, None

    m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", raw)
    normalized = m.group(1) if m else raw.strip()
    return normalized, source, raw


def _diagnostic_credentials_candidate():
    """Lee credenciales sin ocultar errores."""
    try:
        if "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
            raw = str(st.secrets["GCP_SERVICE_ACCOUNT_JSON"]).strip()
            if not raw:
                return None, "GCP_SERVICE_ACCOUNT_JSON", "El Secret existe pero está vacío."
            try:
                candidate = json.loads(raw)
            except json.JSONDecodeError as e:
                return None, "GCP_SERVICE_ACCOUNT_JSON", (
                    f"JSON inválido: línea {e.lineno}, columna {e.colno}: {e.msg}"
                )
            return _normalize_private_key(candidate), "GCP_SERVICE_ACCOUNT_JSON", None
    except Exception as e:
        return None, "GCP_SERVICE_ACCOUNT_JSON", f"No pude leer el Secret: {type(e).__name__}: {e}"

    for section in ["gcp_service_account", "google_service_account", "service_account", "google", "gcp"]:
        try:
            if section in st.secrets:
                candidate = _mapping_to_dict(st.secrets[section])
                if not candidate:
                    return None, f"[{section}]", "La sección existe pero está vacía o no es legible."
                return _normalize_private_key(candidate), f"[{section}]", None
        except Exception as e:
            return None, f"[{section}]", f"No pude leer la sección: {type(e).__name__}: {e}"

    if CREDENTIALS_FILE.exists():
        try:
            candidate = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
            return _normalize_private_key(candidate), str(CREDENTIALS_FILE.name), None
        except Exception as e:
            return None, str(CREDENTIALS_FILE.name), f"No pude leer el JSON local: {type(e).__name__}: {e}"

    return None, None, "No encontré ninguna fuente de credenciales."


def _diagnostic_hint_for_exception(exc):
    msg = str(exc)
    low = msg.lower()
    tname = type(exc).__name__.lower()

    if "spreadsheetnotfound" in tname:
        return (
            "Google no encuentra una planilla accesible con ese ID. Revisá GOOGLE_SHEET_ID y "
            "compartí Parfum con el client_email de la cuenta de servicio."
        )
    if "api has not been used" in low or "has not been used in project" in low or "disabled" in low:
        return "La API mencionada en el error está deshabilitada en Google Cloud. Activala y esperá 1–2 minutos."
    if "permission_denied" in low or "insufficient permission" in low or "forbidden" in low or "403" in low:
        return (
            "Google rechazó el permiso. Si la lectura funciona pero la escritura falla, "
            "la cuenta de servicio no tiene permiso Editor. Si falla al abrir, compartí la planilla "
            "con el client_email correcto y verificá que Sheets API esté habilitada."
        )
    if "invalid_grant" in low:
        return (
            "Google rechazó la cuenta de servicio/clave. Suele ocurrir con una private_key incorrecta "
            "o una clave eliminada."
        )
    if "invalid_scope" in low:
        return "Los scopes OAuth son inválidos. La app debe usar Sheets + Drive."
    if "invalid jwt" in low or "jwt" in low:
        return "La private_key o los datos de la cuenta de servicio no corresponden entre sí."
    if "could not deserialize key data" in low or "deserialize" in low:
        return (
            "La private_key quedó mal copiada. Debe conservar BEGIN PRIVATE KEY, END PRIVATE KEY "
            "y los saltos de línea."
        )
    if "quota" in low or "429" in low:
        return (
            "Google alcanzó temporalmente la cuota de lecturas. Esta versión reduce las llamadas "
            "y cachea las pestañas; esperá aproximadamente un minuto y reiniciá la app."
        )
    if "already exists" in low and "sheet" in low:
        return (
            "La pestaña ya existe. La versión estable ya no intentará recrearla cuando Google "
            "devuelva otro error transitorio."
        )
    return "El detector ya aisló la etapa exacta. Revisá el detalle técnico de este paso."


def run_google_sheets_diagnostic(deep_write_test=True):
    """Diagnóstico profundo sin exponer la private_key."""
    results = []

    def add(step, status, detail, action=""):
        results.append({
            "Paso": step,
            "Estado": status,
            "Detalle": str(detail),
            "Qué hacer": action,
        })

    try:
        import gspread
        from google.oauth2.service_account import Credentials
        from google.auth.transport.requests import Request
        add("1. Dependencias Python", "OK", "gspread y google-auth disponibles.")
    except Exception as e:
        add(
            "1. Dependencias Python", "ERROR",
            f"{type(e).__name__}: {e}",
            "Revisá requirements.txt: streamlit, pandas, numpy, gspread y google-auth."
        )
        return results

    keys = _safe_secret_keys()
    if keys:
        add("2. Streamlit Secrets", "OK", "Secrets raíz detectados: " + ", ".join(keys))
    else:
        add(
            "2. Streamlit Secrets", "ERROR", "No se detectó ningún Secret.",
            "Entrá a Manage app → Settings → Secrets, cargalos y presioná Save."
        )
        return results

    sheet_id, sheet_source, raw_sheet = _diagnostic_sheet_id()
    if not sheet_id:
        add(
            "3. Google Sheet ID", "ERROR", "No encontré GOOGLE_SHEET_ID ni alias compatibles.",
            'Agregá GOOGLE_SHEET_ID = "ID_DE_PARFUM" en Secrets.'
        )
        return results

    if not re.fullmatch(r"[A-Za-z0-9_-]{20,}", sheet_id):
        add(
            "3. Google Sheet ID", "ERROR",
            f"Valor detectado en {sheet_source}, pero no tiene formato de ID válido. Longitud: {len(sheet_id)}.",
            "Copiá únicamente lo que aparece entre /d/ y /edit en la URL de Parfum."
        )
        return results
    add(
        "3. Google Sheet ID", "OK",
        f"Detectado desde {sheet_source}. Formato válido · longitud {len(sheet_id)}."
    )

    cred_info, cred_source, cred_error = _diagnostic_credentials_candidate()
    if cred_error:
        add(
            "4. Lectura de credenciales", "ERROR",
            f"Fuente: {cred_source or 'ninguna'} · {cred_error}",
            "Recomendado: pegá el JSON COMPLETO en GCP_SERVICE_ACCOUNT_JSON."
        )
        return results
    add("4. Lectura de credenciales", "OK", f"Credenciales detectadas desde {cred_source}.")

    required = [
        "type", "project_id", "private_key_id", "private_key",
        "client_email", "client_id", "token_uri"
    ]
    missing = [k for k in required if not str(cred_info.get(k, "")).strip()]
    if missing:
        add(
            "5. Campos del JSON", "ERROR",
            "Faltan: " + ", ".join(missing),
            "Volvé a copiar el JSON original completo descargado de Google Cloud."
        )
        return results

    client_email = str(cred_info.get("client_email", ""))
    project_id = str(cred_info.get("project_id", ""))
    account_type = str(cred_info.get("type", ""))

    if account_type != "service_account":
        add(
            "5. Campos del JSON", "ERROR",
            f"type = {account_type!r}; esperaba 'service_account'.",
            "Usá una clave JSON de una Cuenta de Servicio."
        )
        return results

    if "@" not in client_email or ".iam.gserviceaccount.com" not in client_email:
        add(
            "5. Campos del JSON", "ERROR",
            f"client_email tiene formato inesperado: {client_email}",
            "Usá el JSON generado desde IAM → Cuentas de servicio → Claves."
        )
        return results

    add(
        "5. Campos del JSON", "OK",
        f"project_id={project_id} · client_email={client_email}"
    )

    pk = str(cred_info.get("private_key", ""))
    begins = pk.strip().startswith("-----BEGIN PRIVATE KEY-----")
    ends = pk.strip().endswith("-----END PRIVATE KEY-----")
    newline_count = pk.count("\n")
    if not (begins and ends):
        add(
            "6. Private key", "ERROR",
            f"Encabezado válido={begins} · cierre válido={ends} · saltos de línea={newline_count}.",
            "La clave debe copiarse completa desde BEGIN PRIVATE KEY hasta END PRIVATE KEY."
        )
        return results
    add(
        "6. Private key", "OK",
        f"Estructura PEM válida por formato · {newline_count} saltos de línea. Contenido oculto."
    )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds = Credentials.from_service_account_info(cred_info, scopes=scopes)
        add("7. Construcción de credenciales", "OK", "google-auth pudo interpretar la cuenta y la clave privada.")
    except Exception as e:
        add(
            "7. Construcción de credenciales", "ERROR",
            f"{type(e).__name__}: {e}",
            _diagnostic_hint_for_exception(e)
        )
        return results

    try:
        creds.refresh(Request())
        expiry = getattr(creds, "expiry", None)
        add(
            "8. Autenticación con Google", "OK",
            f"Google emitió un token para {client_email}" + (f" · vence {expiry}" if expiry else "")
        )
    except Exception as e:
        add(
            "8. Autenticación con Google", "ERROR",
            f"{type(e).__name__}: {e}",
            _diagnostic_hint_for_exception(e)
        )
        return results

    try:
        gc = gspread.authorize(creds)
        add("9. Cliente Google Sheets", "OK", "gspread autorizado correctamente.")
    except Exception as e:
        add(
            "9. Cliente Google Sheets", "ERROR",
            f"{type(e).__name__}: {e}",
            _diagnostic_hint_for_exception(e)
        )
        return results

    try:
        ss = gc.open_by_key(sheet_id)
        add(
            "10. Apertura de Parfum", "OK",
            f"Google abrió el spreadsheet · título real: {ss.title!r}"
        )
        if ss.title.strip().lower() != SPREADSHEET_NAME.lower():
            add(
                "10b. Nombre de planilla", "AVISO",
                f"El ID apunta a {ss.title!r}, no a {SPREADSHEET_NAME!r}.",
                "No impide funcionar porque la app usa el ID, pero verificá que sea la planilla correcta."
            )
    except Exception as e:
        add(
            "10. Apertura de Parfum", "ERROR",
            f"{type(e).__name__}: {e}",
            _diagnostic_hint_for_exception(e)
        )
        return results

    try:
        worksheets = ss.worksheets()
        titles = [w.title for w in worksheets]
        add(
            "11. Lectura de pestañas", "OK",
            f"{len(titles)} pestaña(s) accesibles: " + (", ".join(titles[:12]) if titles else "(ninguna)")
        )
    except Exception as e:
        add(
            "11. Lectura de pestañas", "ERROR",
            f"{type(e).__name__}: {e}",
            _diagnostic_hint_for_exception(e)
        )
        return results

    try:
        if worksheets:
            probe_ws = worksheets[0]
            a1 = probe_ws.acell("A1").value
            add(
                "12. Lectura de celdas", "OK",
                f"Lectura A1 de {probe_ws.title!r} correcta · valor: {repr(a1)[:120]}"
            )
        else:
            add(
                "12. Lectura de celdas", "AVISO",
                "No hay pestañas para probar lectura.",
                "La app intentará crear su estructura si tiene permiso Editor."
            )
    except Exception as e:
        add(
            "12. Lectura de celdas", "ERROR",
            f"{type(e).__name__}: {e}",
            _diagnostic_hint_for_exception(e)
        )
        return results

    if deep_write_test:
        temp_ws = None
        temp_title = f"__PERFUME_OS_DIAG_{uuid.uuid4().hex[:6]}"
        token = f"OK-{uuid.uuid4().hex[:8]}"
        try:
            temp_ws = ss.add_worksheet(title=temp_title, rows=2, cols=2)
            try:
                temp_ws.update_acell("A1", token)
            except Exception:
                temp_ws.update("A1", [[token]])
            readback = temp_ws.acell("A1").value
            if readback != token:
                raise RuntimeError(f"Escribí {token!r} pero Google devolvió {readback!r}.")
            add(
                "13. Permiso de escritura", "OK",
                "Se creó una pestaña temporal, se escribió y se leyó correctamente. La cuenta tiene permiso Editor."
            )
        except Exception as e:
            add(
                "13. Permiso de escritura", "ERROR",
                f"{type(e).__name__}: {e}",
                "La lectura funciona, pero la escritura no. Compartí Parfum con el client_email como EDITOR."
            )
            return results
        finally:
            if temp_ws is not None:
                try:
                    ss.del_worksheet(temp_ws)
                except Exception as cleanup_error:
                    add(
                        "14. Limpieza diagnóstico", "AVISO",
                        f"No pude borrar la pestaña temporal {temp_title}: {type(cleanup_error).__name__}: {cleanup_error}",
                        f"Borrá manualmente la pestaña {temp_title}."
                    )

    add(
        "RESULTADO", "OK",
        "Conexión Google Sheets completamente operativa: Secrets, credenciales, autenticación, apertura, lectura y escritura funcionan."
    )
    return results


def render_google_sheets_diagnostic(original_error=None):
    """Pantalla automática de diagnóstico cuando el backend no inicia."""
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">DIAGNÓSTICO AUTOMÁTICO</div>
          <h1>Google Sheets · Detector de conexión</h1>
          <p>PERFUME OS prueba cada capa por separado para identificar el punto exacto de falla.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if original_error is not None:
        st.error(f"Error que detuvo el inicio: {type(original_error).__name__}: {original_error}")

    with st.spinner("Ejecutando diagnóstico profundo de Google Sheets..."):
        results = run_google_sheets_diagnostic(deep_write_test=True)

    df = pd.DataFrame(results)
    first_error = next((r for r in results if r["Estado"] == "ERROR"), None)

    if first_error:
        st.error(f"FALLA EXACTA: {first_error['Paso']}")
        st.markdown(f"**Detalle:** {first_error['Detalle']}")
        if first_error.get("Qué hacer"):
            st.warning(first_error["Qué hacer"])
    else:
        st.success("Todas las pruebas de Google Sheets pasaron correctamente.")

    status_icon = {"OK": "✅", "ERROR": "❌", "AVISO": "⚠️", "INFO": "ℹ️"}
    if not df.empty:
        df.insert(0, "", df["Estado"].map(status_icon).fillna("•"))
        st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("Información segura para enviarme"):
        safe_summary = {
            "fecha": now_iso(),
            "secrets_detectados": _safe_secret_keys(),
            "primer_error": first_error,
            "pasos": results,
        }
        st.code(json.dumps(safe_summary, ensure_ascii=False, indent=2))
        st.caption("Este resumen NO incluye la private_key ni los valores de tus Secrets.")

    st.markdown("### Configuración mínima recomendada")
    minimal_config = (
        'GOOGLE_SHEET_ID = "ID_DEL_SHEET"\n\n'
        'GCP_SERVICE_ACCOUNT_JSON = "PEGAR_EL_JSON_COMPLETO_DE_GOOGLE_CLOUD_COMO_UN_SOLO_SECRET"\n'
    )
    st.code(minimal_config, language="toml")

    if st.button("↻ Volver a probar ahora", type="primary", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()


def _get_google_credentials_source():
    """
    Método recomendado en Streamlit Cloud:
      GOOGLE_SHEET_ID
      GCP_SERVICE_ACCOUNT_JSON = '''{...JSON completo...}'''
    """
    # 1) Método SIMPLE recomendado: JSON completo en un solo Secret.
    try:
        if "GCP_SERVICE_ACCOUNT_JSON" in st.secrets:
            raw = str(st.secrets["GCP_SERVICE_ACCOUNT_JSON"]).strip()
            if raw:
                candidate = json.loads(raw)
                candidate = _normalize_private_key(candidate)
                if _looks_like_service_account(candidate):
                    return "streamlit_json:GCP_SERVICE_ACCOUNT_JSON", candidate
                raise RuntimeError(
                    "GCP_SERVICE_ACCOUNT_JSON existe, pero no parece ser un JSON válido "
                    "de una Cuenta de Servicio de Google."
                )
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "GCP_SERVICE_ACCOUNT_JSON está cargado, pero el JSON quedó mal pegado o incompleto. "
            f"Detalle: {e}"
        )

    # 2) Compatibilidad con secciones previas.
    section_names = [
        "gcp_service_account",
        "google_service_account",
        "service_account",
        "google",
        "gcp",
    ]
    try:
        for section in section_names:
            if section in st.secrets:
                candidate = _mapping_to_dict(st.secrets[section])
                candidate = _normalize_private_key(candidate)
                if _looks_like_service_account(candidate):
                    return f"streamlit_section:{section}", candidate
    except Exception:
        pass

    # 3) Desarrollo local.
    if CREDENTIALS_FILE.exists():
        return "local_json", str(CREDENTIALS_FILE)

    visible = ", ".join(_safe_secret_keys()) or "(ninguno)"
    raise RuntimeError(
        "No encontré credenciales de Google. "
        f"Secrets detectados: {visible}. "
        "En Streamlit Cloud cargá GCP_SERVICE_ACCOUNT_JSON con el JSON COMPLETO "
        "de la cuenta de servicio."
    )


@st.cache_resource
def get_backend():
    import gspread
    import threading
    from google.oauth2.service_account import Credentials

    source, credentials_data = _get_google_credentials_source()

    try:
        if source.startswith("streamlit_"):
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_info(
                credentials_data,
                scopes=scopes,
            )
            gc = gspread.authorize(creds)
        else:
            gc = gspread.service_account(filename=credentials_data)

        # En Streamlit Cloud preferimos el ID exacto del Sheet.
        sheet_id = None
        try:
            for key in ["GOOGLE_SHEET_ID", "google_sheet_id", "SHEET_ID", "GSHEET_ID", "SPREADSHEET_ID"]:
                if key in st.secrets and str(st.secrets[key]).strip():
                    sheet_id = str(st.secrets[key]).strip()
                    break

            # También acepta secciones [sheets] o [google_sheets].
            if not sheet_id:
                for section in ["sheets", "google_sheets"]:
                    if section in st.secrets:
                        sec = _mapping_to_dict(st.secrets[section]) or {}
                        for key in ["sheet_id", "spreadsheet_id", "id"]:
                            if key in sec and str(sec[key]).strip():
                                sheet_id = str(sec[key]).strip()
                                break
                        if sheet_id:
                            break
        except Exception:
            sheet_id = None

        if sheet_id:
            spreadsheet = gc.open_by_key(sheet_id)
        else:
            # Fallback por nombre para uso local.
            spreadsheet = gc.open(SPREADSHEET_NAME)

    except Exception as e:
        email_hint = ""
        if source.startswith("streamlit_"):
            email_hint = credentials_data.get("client_email", "")
        keys_seen = ", ".join(_safe_secret_keys()) or "(ninguno)"
        raise RuntimeError(
            "No pude conectar PERFUME OS con Google Sheets. "
            f"Secrets raíz detectados: {keys_seen}. "
            "Verificá el Sheet ID y compartí la planilla como Editor con el client_email "
            f"de la Cuenta de Servicio{f' ({email_hint})' if email_hint else ''}. "
            f"Detalle técnico: {type(e).__name__}: {e}"
        )

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return {
        "conn": conn,
        "spreadsheet": spreadsheet,
        "lock": threading.RLock(),
        "loaded": False,
        "sync_enabled": False,
        "structure_ready": False,
        "worksheet_cache": {},
    }


def get_conn():
    return get_backend()["conn"]


def _refresh_worksheet_cache():
    """
    Obtiene la lista de pestañas UNA sola vez y la conserva en memoria.
    Evita hacer ss.worksheet(...) para cada tabla y cada rerun.
    """
    backend = get_backend()
    worksheets = backend["spreadsheet"].worksheets()
    backend["worksheet_cache"] = {ws.title: ws for ws in worksheets}
    return backend["worksheet_cache"]


def _worksheet_for_table(table):
    """
    Devuelve la pestaña asociada a una tabla.
    IMPORTANTE: ya no interpreta cualquier APIError como 'no existe'.
    Solo crea la pestaña si realmente no está en el cache de títulos.
    """
    backend = get_backend()
    title = SHEET_NAMES[table]
    cache = backend.setdefault("worksheet_cache", {})

    if not cache:
        cache = _refresh_worksheet_cache()

    if title in cache:
        return cache[title]

    cols = table_columns(table)
    ss = backend["spreadsheet"]

    try:
        ws = ss.add_worksheet(
            title=title,
            rows=max(100, 20),
            cols=max(20, len(cols) + 3),
        )
    except Exception as e:
        # Puede ocurrir si dos instancias arrancan al mismo tiempo.
        # Si Google dice que ya existe, refrescamos el cache y usamos esa pestaña.
        msg = str(e).lower()
        if "already exists" in msg or "ya existe" in msg:
            cache = _refresh_worksheet_cache()
            if title in cache:
                return cache[title]
        # Cualquier otro error (429, 403, etc.) ES un error real y debe propagarse.
        raise

    backend["worksheet_cache"][title] = ws
    return ws


def ensure_sheet_structure():
    """
    Crea únicamente las pestañas faltantes.
    No vuelve a leer las 18 pestañas en cada rerun de Streamlit.
    """
    backend = get_backend()
    with backend["lock"]:
        if backend.get("structure_ready", False):
            return

        cache = _refresh_worksheet_cache()

        for table in TABLE_ORDER:
            title = SHEET_NAMES[table]
            if title in cache:
                continue

            cols = table_columns(table)
            ws = _worksheet_for_table(table)

            # La pestaña acaba de ser creada: escribimos el encabezado una sola vez.
            _gspread_update(ws, [cols])

        backend["structure_ready"] = True


def _gspread_update(ws, values):
    ws.clear()
    try:
        ws.update(values=values, range_name="A1", value_input_option="RAW")
    except TypeError:
        try:
            ws.update("A1", values, value_input_option="RAW")
        except TypeError:
            ws.update("A1", values)


def _clean_sheet_value(v):
    if v is None:
        return ""
    if isinstance(v, float) and pd.isna(v):
        return ""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def table_columns(table):
    return [r[1] for r in get_conn().execute(f"PRAGMA table_info({table})").fetchall()]


def _load_table_from_sheet(table):
    conn = get_conn()
    ws = _worksheet_for_table(table)
    values = ws.get_all_values()
    cols = table_columns(table)
    conn.execute(f"DELETE FROM {table}")
    if len(values) <= 1:
        return
    header = values[0]
    col_positions = {c: i for i, c in enumerate(header)}
    insert_cols = [c for c in cols if c in col_positions]
    if not insert_cols:
        return
    placeholders = ",".join(["?"] * len(insert_cols))
    sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"
    rows = []
    for raw in values[1:]:
        if not any(str(x).strip() for x in raw):
            continue
        row = []
        for c in insert_cols:
            idx = col_positions[c]
            val = raw[idx] if idx < len(raw) else ""
            row.append(None if val == "" else val)
        rows.append(tuple(row))
    if rows:
        conn.executemany(sql, rows)


def reload_from_sheets():
    backend = get_backend()
    conn = get_conn()
    with backend["lock"]:
        backend["sync_enabled"] = False
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            for table in reversed(TABLE_ORDER):
                conn.execute(f"DELETE FROM {table}")
            for table in TABLE_ORDER:
                _load_table_from_sheet(table)
            conn.commit()
        finally:
            conn.execute("PRAGMA foreign_keys = ON")

        # Seed solo si las hojas correspondientes no tenían datos.
        settings_was_empty = conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0] == 0
        users_was_empty = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0

        defaults = {
            "business_name": "Mi Perfumería",
            "currency": "ARS",
            "login_enabled": "0",
            "monthly_goal": "0",
            "target_margin": "35",
            "default_low_stock_days": "14",
        }
        for k, v in defaults.items():
            conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
        conn.execute(
            "INSERT OR IGNORE INTO users(username,password_hash,full_name,role,active,created_at) VALUES(?,?,?,?,?,?)",
            ("admin", hash_password("admin"), "Administrador", "Admin", 1, now_iso()),
        )
        conn.commit()

        backend["sync_enabled"] = True
        backend["loaded"] = True

        # Evita reescribir settings/usuarios en cada arranque si ya estaban en Sheets.
        if settings_was_empty:
            sync_table_to_sheet("settings")
        if users_was_empty:
            sync_table_to_sheet("users")


def sync_table_to_sheet(table):
    backend = get_backend()
    if not backend.get("sync_enabled", False):
        return
    if table not in SHEET_NAMES:
        return
    with backend["lock"]:
        cols = table_columns(table)
        df = pd.read_sql_query(f"SELECT {','.join(cols)} FROM {table}", get_conn())
        values = [cols]
        if not df.empty:
            for row in df.itertuples(index=False, name=None):
                values.append([_clean_sheet_value(v) for v in row])
        ws = _worksheet_for_table(table)
        _gspread_update(ws, values)


def sync_tables(tables):
    for t in dict.fromkeys(tables):
        sync_table_to_sheet(t)


def _mutated_table(sql):
    s = " ".join(sql.strip().split())
    patterns = [
        r"^INSERT(?: OR IGNORE)? INTO ([A-Za-z_][A-Za-z0-9_]*)",
        r"^UPDATE ([A-Za-z_][A-Za-z0-9_]*)",
        r"^DELETE FROM ([A-Za-z_][A-Za-z0-9_]*)",
        r"^REPLACE INTO ([A-Za-z_][A-Za-z0-9_]*)",
    ]
    for p in patterns:
        m = re.search(p, s, flags=re.I)
        if m:
            return m.group(1)
    return None


def execute(sql, params=(), commit=True):
    backend = get_backend()
    with backend["lock"]:
        cur = get_conn().execute(sql, params)
        if commit:
            get_conn().commit()
            table = _mutated_table(sql)
            if table:
                sync_table_to_sheet(table)
        return cur


def executemany(sql, seq, commit=True):
    backend = get_backend()
    with backend["lock"]:
        cur = get_conn().executemany(sql, seq)
        if commit:
            get_conn().commit()
            table = _mutated_table(sql)
            if table:
                sync_table_to_sheet(table)
        return cur


def qdf(sql, params=()):
    return pd.read_sql_query(sql, get_conn(), params=params)


def scalar(sql, params=(), default=0):
    row = get_conn().execute(sql, params).fetchone()
    if not row:
        return default
    val = row[0]
    return default if val is None else val


def init_db():
    backend = get_backend()

    # Streamlit ejecuta el script completo en cada interacción.
    # Si esta instancia ya cargó Sheets, NO volvemos a consultar Google.
    if backend.get("loaded", False):
        return

    ensure_sheet_structure()
    reload_from_sheets()


try:
    init_db()
except Exception as _google_error:
    render_google_sheets_diagnostic(_google_error)
    st.stop()

def get_setting(key, default=""):
    row = execute("SELECT value FROM settings WHERE key=?", (key,), commit=False).fetchone()
    return row["value"] if row else default

def set_setting(key, value):
    execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))

def current_user():
    return st.session_state.get("user", {"username":"local","full_name":"Operador local","role":"Admin"})

def stock_df(active_only=True):
    where = "WHERE p.active=1" if active_only else ""
    return qdf(
        f"""
        SELECT p.*,
               COALESCE(SUM(im.qty),0) AS stock
        FROM products p
        LEFT JOIN inventory_moves im ON im.product_id=p.id
        {where}
        GROUP BY p.id
        ORDER BY p.brand, p.name, p.size_ml
        """
    )

def current_stock(product_id):
    return safe_float(scalar("SELECT COALESCE(SUM(qty),0) FROM inventory_moves WHERE product_id=?", (product_id,), 0))

def product_label(row):
    typ = " · DECANT" if row.get("product_type","PERFUME") == "DECANT" else ""
    return f"{row['brand']} {row['name']} · {row['size_ml']:g} ml{typ} · {row['sku']}"

def ensure_cart():
    if "cart" not in st.session_state:
        st.session_state.cart = []

def add_inventory_move(product_id, move_type, qty, unit_cost=0, reference_type=None, reference_id=None, notes=""):
    execute(
        """INSERT INTO inventory_moves(date,product_id,move_type,qty,unit_cost,reference_type,reference_id,notes,user_name,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (
            today_iso(), product_id, move_type, qty, unit_cost, reference_type,
            reference_id, notes, current_user().get("username","local"), now_iso()
        )
    )

def add_cash_move(direction, category, method, amount, reference_type=None, reference_id=None, notes="", move_date=None):
    execute(
        """INSERT INTO cash_moves(date,direction,category,method,amount,reference_type,reference_id,notes,created_at)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (move_date or today_iso(), direction, category, method, amount, reference_type, reference_id, notes, now_iso())
    )

def recalc_customer_vip(customer_id):
    if not customer_id:
        return
    spent = safe_float(scalar("SELECT COALESCE(SUM(total),0) FROM sales WHERE customer_id=? AND status='Completada'", (customer_id,), 0))
    count = safe_int(scalar("SELECT COUNT(*) FROM sales WHERE customer_id=? AND status='Completada'", (customer_id,), 0))
    vip = 1 if (spent >= 500000 or count >= 5) else 0
    execute("UPDATE customers SET vip=? WHERE id=?", (vip, customer_id))

def save_sale(cart, customer_id, vendor_id, channel, payment_method, discount, shipping, paid, notes):
    if not cart:
        raise ValueError("El carrito está vacío.")
    conn = get_conn()
    try:
        cur = conn.cursor()
        for item in cart:
            available = current_stock(item["product_id"])
            if item["qty"] > available + 1e-9:
                raise ValueError(f"Stock insuficiente para {item['label']}. Disponible: {available:g}")
        subtotal = sum(i["qty"] * i["unit_price"] for i in cart)
        cost = sum(i["qty"] * i["unit_cost"] for i in cart)
        total = max(0, subtotal - discount + shipping)
        profit = total - cost
        margin = (profit / total * 100) if total else 0
        cur.execute(
            """INSERT INTO sales(date,customer_id,vendor_id,channel,payment_method,subtotal,discount,shipping,total,cost,profit,margin,paid,status,notes,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (today_iso(), customer_id, vendor_id, channel, payment_method, subtotal, discount, shipping, total, cost, profit, margin, paid, "Completada", notes, now_iso())
        )
        sale_id = cur.lastrowid
        for item in cart:
            cur.execute(
                """INSERT INTO sale_items(sale_id,product_id,qty,unit_price,unit_cost,subtotal)
                   VALUES(?,?,?,?,?,?)""",
                (sale_id, item["product_id"], item["qty"], item["unit_price"], item["unit_cost"], item["qty"] * item["unit_price"])
            )
            cur.execute(
                """INSERT INTO inventory_moves(date,product_id,move_type,qty,unit_cost,reference_type,reference_id,notes,user_name,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (today_iso(), item["product_id"], "VENTA", -item["qty"], item["unit_cost"], "SALE", sale_id, "", current_user().get("username","local"), now_iso())
            )
        if paid > 0:
            cur.execute(
                """INSERT INTO cash_moves(date,direction,category,method,amount,reference_type,reference_id,notes,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (today_iso(), "INGRESO", "Venta", payment_method, paid, "SALE", sale_id, notes, now_iso())
            )
        if customer_id and paid < total:
            cur.execute(
                """INSERT INTO account_ledger(date,entity_type,entity_id,concept,debit,credit,reference_type,reference_id,notes,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (today_iso(), "CUSTOMER", customer_id, f"Venta #{sale_id}", total-paid, 0, "SALE", sale_id, notes, now_iso())
            )
        conn.commit()
        sync_tables(["sales","sale_items","inventory_moves","cash_moves","account_ledger"])
        if customer_id:
            recalc_customer_vip(customer_id)
        return sale_id
    except Exception:
        conn.rollback()
        raise

def save_purchase(items, supplier_id, invoice, payment_method, shipping, fees, taxes, paid, status, notes):
    if not items:
        raise ValueError("No hay productos en la compra.")
    conn = get_conn()
    try:
        cur = conn.cursor()
        items_subtotal = sum(i["qty"] * i["unit_price"] for i in items)
        extra = shipping + fees + taxes
        total = items_subtotal + extra
        cur.execute(
            """INSERT INTO purchases(date,supplier_id,invoice,payment_method,shipping,fees,taxes,items_subtotal,total,paid,status,notes,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (today_iso(), supplier_id, invoice, payment_method, shipping, fees, taxes, items_subtotal, total, paid, status, notes, now_iso())
        )
        purchase_id = cur.lastrowid

        for i in items:
            alloc = (i["qty"] * i["unit_price"] / items_subtotal) if items_subtotal else (1/len(items))
            allocated_extra = extra * alloc
            landed_unit = (i["qty"] * i["unit_price"] + allocated_extra) / i["qty"] if i["qty"] else i["unit_price"]
            old_stock = max(0.0, current_stock(i["product_id"]))
            old_cost = safe_float(scalar("SELECT avg_cost FROM products WHERE id=?", (i["product_id"],), 0))
            new_qty = i["qty"]
            weighted = ((old_stock * old_cost) + (new_qty * landed_unit)) / (old_stock + new_qty) if (old_stock + new_qty) else landed_unit

            cur.execute(
                """INSERT INTO purchase_items(purchase_id,product_id,qty,unit_price,landed_unit_cost,subtotal)
                   VALUES(?,?,?,?,?,?)""",
                (purchase_id, i["product_id"], i["qty"], i["unit_price"], landed_unit, i["qty"]*i["unit_price"])
            )
            cur.execute("UPDATE products SET avg_cost=?, supplier_id=COALESCE(?,supplier_id) WHERE id=?", (weighted, supplier_id, i["product_id"]))
            cur.execute(
                """INSERT INTO inventory_moves(date,product_id,move_type,qty,unit_cost,reference_type,reference_id,notes,user_name,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (today_iso(), i["product_id"], "COMPRA", i["qty"], landed_unit, "PURCHASE", purchase_id, invoice, current_user().get("username","local"), now_iso())
            )

        if paid > 0:
            cur.execute(
                """INSERT INTO cash_moves(date,direction,category,method,amount,reference_type,reference_id,notes,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (today_iso(), "EGRESO", "Compra mercadería", payment_method, paid, "PURCHASE", purchase_id, notes, now_iso())
            )
        if supplier_id and paid < total:
            cur.execute(
                """INSERT INTO account_ledger(date,entity_type,entity_id,concept,debit,credit,reference_type,reference_id,notes,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (today_iso(), "SUPPLIER", supplier_id, f"Compra #{purchase_id}", 0, total-paid, "PURCHASE", purchase_id, notes, now_iso())
            )
        conn.commit()
        sync_tables(["purchases","purchase_items","products","inventory_moves","cash_moves","account_ledger"])
        return purchase_id
    except Exception:
        conn.rollback()
        raise

def refund_sale(sale_id):
    sale = execute("SELECT * FROM sales WHERE id=?", (sale_id,), commit=False).fetchone()
    if not sale or sale["status"] != "Completada":
        raise ValueError("La venta no existe o ya fue anulada.")
    items = qdf("SELECT * FROM sale_items WHERE sale_id=?", (sale_id,))
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE sales SET status='Anulada' WHERE id=?", (sale_id,))
        for _, i in items.iterrows():
            cur.execute(
                """INSERT INTO inventory_moves(date,product_id,move_type,qty,unit_cost,reference_type,reference_id,notes,user_name,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (today_iso(), int(i.product_id), "ANULACION_VENTA", float(i.qty), float(i.unit_cost), "SALE", sale_id, "", current_user().get("username","local"), now_iso())
            )
        if safe_float(sale["paid"]) > 0:
            cur.execute(
                """INSERT INTO cash_moves(date,direction,category,method,amount,reference_type,reference_id,notes,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (today_iso(), "EGRESO", "Anulación venta", sale["payment_method"], safe_float(sale["paid"]), "SALE", sale_id, "", now_iso())
            )
        conn.commit()
        sync_tables(["sales","inventory_moves","cash_moves"])
    except Exception:
        conn.rollback()
        raise

def create_decants(parent_id, decant_ml, qty, packaging_cost, sale_price, location="Decants"):
    parent = execute("SELECT * FROM products WHERE id=?", (parent_id,), commit=False).fetchone()
    if not parent:
        raise ValueError("Producto madre inexistente.")
    if parent["product_type"] == "DECANT":
        raise ValueError("Un decant no puede ser botella madre.")
    needed_ml = decant_ml * qty
    conn = get_conn()
    try:
        cur = conn.cursor()
        pool = safe_float(scalar("SELECT available_ml FROM decant_pools WHERE product_id=?", (parent_id,), 0))
        bottle_ml = safe_float(parent["size_ml"])
        while pool + 1e-9 < needed_ml:
            available_units = current_stock(parent_id)
            if available_units < 1:
                raise ValueError("No hay botellas completas suficientes para alimentar el pool de decants.")
            cur.execute(
                """INSERT INTO inventory_moves(date,product_id,move_type,qty,unit_cost,reference_type,reference_id,notes,user_name,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (today_iso(), parent_id, "APERTURA_DECANT", -1, parent["avg_cost"], "DECANT_POOL", parent_id, f"Apertura botella {bottle_ml:g} ml", current_user().get("username","local"), now_iso())
            )
            pool += bottle_ml

        pool -= needed_ml
        cur.execute(
            """INSERT INTO decant_pools(product_id,available_ml,updated_at) VALUES(?,?,?)
               ON CONFLICT(product_id) DO UPDATE SET available_ml=excluded.available_ml, updated_at=excluded.updated_at""",
            (parent_id, pool, now_iso())
        )

        existing = cur.execute(
            "SELECT * FROM products WHERE product_type='DECANT' AND parent_product_id=? AND ABS(size_ml-?)<0.0001",
            (parent_id, decant_ml)
        ).fetchone()
        cost_ml = safe_float(parent["avg_cost"]) / bottle_ml if bottle_ml else 0
        unit_cost = cost_ml * decant_ml + packaging_cost
        if existing:
            decant_id = existing["id"]
            cur.execute("UPDATE products SET avg_cost=?, sale_price=?, location=?, active=1, sellable=1 WHERE id=?", (unit_cost, sale_price, location, decant_id))
        else:
            sku = f"D-{parent['sku']}-{int(decant_ml)}ML"
            cur.execute(
                """INSERT INTO products(sku,brand,name,line,gender,concentration,size_ml,origin_country,category,product_type,parent_product_id,
                   olfactory_family,top_notes,heart_notes,base_notes,season,use_time,supplier_id,avg_cost,sale_price,wholesale_price,reseller_price,promo_price,
                   min_stock,location,sellable,active,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    sku, parent["brand"], parent["name"], parent["line"], parent["gender"], parent["concentration"], decant_ml,
                    parent["origin_country"], "Decant", "DECANT", parent_id, parent["olfactory_family"], parent["top_notes"],
                    parent["heart_notes"], parent["base_notes"], parent["season"], parent["use_time"], parent["supplier_id"],
                    unit_cost, sale_price, 0, 0, 0, 0, location, 1, 1, now_iso()
                )
            )
            decant_id = cur.lastrowid
        cur.execute(
            """INSERT INTO inventory_moves(date,product_id,move_type,qty,unit_cost,reference_type,reference_id,notes,user_name,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (today_iso(), decant_id, "PRODUCCION_DECANT", qty, unit_cost, "DECANT_POOL", parent_id, f"{needed_ml:g} ml consumidos", current_user().get("username","local"), now_iso())
        )
        conn.commit()
        sync_tables(["products","inventory_moves","decant_pools"])
        return decant_id, pool
    except Exception:
        conn.rollback()
        raise

def export_backup_zip():
    tables = [
        "settings","users","suppliers","vendors","customers","products","inventory_moves",
        "purchases","purchase_items","sales","sale_items","cash_moves","expenses",
        "reservations","account_ledger","promotions","decant_pools","campaign_log"
    ]
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        for t in tables:
            df = qdf(f"SELECT * FROM {t}")
            z.writestr(f"{t}.csv", df.to_csv(index=False).encode("utf-8-sig"))
        z.writestr(
            "README.txt",
            (
                f"{APP_NAME} {APP_VERSION}\n"
                f"Backup generado: {now_iso()}\n"
                "Cada tabla está exportada en CSV UTF-8.\n"
                "Google Sheets (Parfum) es la base persistente principal. Este ZIP es una copia de seguridad adicional."
            ).encode("utf-8")
        )
    bio.seek(0)
    return bio.getvalue()

# -----------------------------
# AUTH
# -----------------------------
def login_gate():
    enabled = get_setting("login_enabled","0") == "1"
    if not enabled:
        st.session_state.user = {"username":"local","full_name":"Operador local","role":"Admin"}
        return True
    if st.session_state.get("user"):
        return True

    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">ACCESO SEGURO</div>
          <h1>PERFUME OS</h1>
          <p>Ingresá con tu usuario para acceder al sistema.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        go = st.form_submit_button("Ingresar", type="primary", use_container_width=True)
    if go:
        row = execute("SELECT * FROM users WHERE username=? AND active=1", (user.strip(),), commit=False).fetchone()
        if row and row["password_hash"] == hash_password(pw):
            st.session_state.user = dict(row)
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    return False

if not login_gate():
    st.stop()

# -----------------------------
# SHARED FILTERS / DATA
# -----------------------------
BUSINESS_NAME = get_setting("business_name", "Mi Perfumería")
TARGET_MARGIN = safe_float(get_setting("target_margin","35"))
MONTHLY_GOAL = safe_float(get_setting("monthly_goal","0"))

def date_range_for_month(d):
    start = date(d.year, d.month, 1)
    if d.month == 12:
        nxt = date(d.year + 1, 1, 1)
    else:
        nxt = date(d.year, d.month + 1, 1)
    return start, nxt

def period_sales(start, end):
    return qdf(
        """SELECT s.*, c.name customer_name, v.name vendor_name
           FROM sales s
           LEFT JOIN customers c ON c.id=s.customer_id
           LEFT JOIN vendors v ON v.id=s.vendor_id
           WHERE s.date>=? AND s.date<? AND s.status='Completada'
           ORDER BY s.id DESC""",
        (str(start), str(end))
    )

def inventory_value():
    df = stock_df()
    if df.empty:
        return 0,0,0
    sellable = df[df.stock > 0].copy()
    cost = float((sellable.stock * sellable.avg_cost).sum()) if not sellable.empty else 0
    retail = float((sellable.stock * sellable.sale_price).sum()) if not sellable.empty else 0
    return cost, retail, retail-cost

def last_sale_by_product():
    return qdf(
        """SELECT si.product_id, MAX(s.date) last_sale_date, SUM(si.qty) units_sold
           FROM sale_items si JOIN sales s ON s.id=si.sale_id
           WHERE s.status='Completada'
           GROUP BY si.product_id"""
    )

def section_header(title, subtitle=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)

def hero(title, subtitle, eyebrow="PERFUME OS"):
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.markdown(f"### ✦ {APP_NAME}")
    st.caption(BUSINESS_NAME)
    st.divider()
    pages = [
        "◎ Centro Ejecutivo",
        "▣ Venta rápida",
        "◈ Catálogo",
        "▤ Inventario",
        "◆ Compras",
        "♙ Clientes",
        "♜ Vendedores",
        "◫ Reservas y pedidos",
        "↔ Cuentas corrientes",
        "$ Caja y finanzas",
        "◌ Decants y testers",
        "◇ Promociones y marketing",
        "↻ Reposición",
        "✦ Centro inteligente",
        "▥ Reportes",
        "⚙ Configuración",
    ]
    page = st.radio("Navegación", pages, label_visibility="collapsed")
    st.divider()
    u = current_user()
    st.caption(f"{u.get('full_name','')} · {u.get('role','')}")
    try:
        _sheet_ref = st.secrets.get("GOOGLE_SHEET_ID", st.secrets.get("google_sheet_id", SPREADSHEET_NAME))
    except Exception:
        _sheet_ref = SPREADSHEET_NAME
    st.caption(f"☁ Google Sheets · {_sheet_ref}")
    if st.button("↻ Actualizar desde Sheets", use_container_width=True):
        reload_from_sheets()
        st.rerun()
    if get_setting("login_enabled","0") == "1":
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.pop("user", None)
            st.rerun()

# ============================================================
# PAGE: EXECUTIVE DASHBOARD
# ============================================================
if page == "◎ Centro Ejecutivo":
    hero(
        "Centro Ejecutivo",
        "Ventas, rentabilidad, inventario, caja y señales de gestión en una única vista.",
        BUSINESS_NAME.upper(),
    )

    month = st.date_input("Mes a analizar", value=date.today().replace(day=1), key="dash_month")
    start, end = date_range_for_month(month)
    sales = period_sales(start, end)
    prev_month_end = start
    prev_month_start = (start - timedelta(days=1)).replace(day=1)
    prev_sales = period_sales(prev_month_start, prev_month_end)

    revenue = safe_float(sales.total.sum()) if not sales.empty else 0
    profit = safe_float(sales.profit.sum()) if not sales.empty else 0
    units = safe_float(qdf(
        """SELECT COALESCE(SUM(si.qty),0) q FROM sale_items si JOIN sales s ON s.id=si.sale_id
           WHERE s.date>=? AND s.date<? AND s.status='Completada'""",
        (str(start), str(end))
    ).iloc[0,0])
    tickets = len(sales)
    avg_ticket = revenue / tickets if tickets else 0
    margin = profit/revenue*100 if revenue else 0
    prev_revenue = safe_float(prev_sales.total.sum()) if not prev_sales.empty else 0
    growth = ((revenue-prev_revenue)/prev_revenue*100) if prev_revenue else 0
    stock_cost, stock_retail, stock_potential = inventory_value()
    cash_balance = safe_float(scalar(
        "SELECT COALESCE(SUM(CASE WHEN direction='INGRESO' THEN amount ELSE -amount END),0) FROM cash_moves", default=0
    ))
    receivables = safe_float(scalar(
        "SELECT COALESCE(SUM(debit-credit),0) FROM account_ledger WHERE entity_type='CUSTOMER'", default=0
    ))
    payables = safe_float(scalar(
        "SELECT COALESCE(SUM(credit-debit),0) FROM account_ledger WHERE entity_type='SUPPLIER'", default=0
    ))

    cols = st.columns(6)
    cols[0].metric("Facturación", money(revenue), f"{growth:+.1f}% vs mes ant.")
    cols[1].metric("Ganancia bruta", money(profit))
    cols[2].metric("Margen real", pct(margin), f"Meta {TARGET_MARGIN:.0f}%")
    cols[3].metric("Unidades", f"{units:g}")
    cols[4].metric("Ticket promedio", money(avg_ticket))
    cols[5].metric("Caja teórica", money(cash_balance))

    cols2 = st.columns(5)
    cols2[0].metric("Stock a costo", money(stock_cost))
    cols2[1].metric("Stock a venta", money(stock_retail))
    cols2[2].metric("Ganancia potencial", money(stock_potential))
    cols2[3].metric("Por cobrar", money(receivables))
    cols2[4].metric("Por pagar", money(payables))

    if MONTHLY_GOAL > 0:
        progress = min(1.0, revenue / MONTHLY_GOAL)
        st.markdown("### Objetivo mensual")
        st.progress(progress)
        st.caption(f"{money(revenue)} de {money(MONTHLY_GOAL)} · {progress*100:.1f}%")

    c1, c2 = st.columns([1.35,1])
    with c1:
        section_header("Evolución de ventas")
        if sales.empty:
            st.info("Todavía no hay ventas para este período.")
        else:
            daily = sales.groupby("date", as_index=False).agg(Facturación=("total","sum"), Ganancia=("profit","sum"))
            st.line_chart(daily.set_index("date")[["Facturación","Ganancia"]], use_container_width=True)
    with c2:
        section_header("Canales")
        if not sales.empty:
            ch = sales.groupby("channel", as_index=False).total.sum().sort_values("total", ascending=False)
            st.bar_chart(ch.set_index("channel")["total"], use_container_width=True)
        else:
            st.info("Sin datos.")

    c1, c2 = st.columns(2)
    with c1:
        section_header("Productos líderes")
        top = qdf(
            """SELECT p.brand || ' ' || p.name || ' ' || CAST(p.size_ml AS INT) || 'ml' producto,
                      SUM(si.qty) unidades, SUM(si.subtotal) facturacion,
                      SUM((si.unit_price-si.unit_cost)*si.qty) ganancia
               FROM sale_items si JOIN sales s ON s.id=si.sale_id JOIN products p ON p.id=si.product_id
               WHERE s.date>=? AND s.date<? AND s.status='Completada'
               GROUP BY p.id ORDER BY ganancia DESC LIMIT 10""",
            (str(start), str(end))
        )
        if top.empty:
            st.info("Sin ventas.")
        else:
            st.dataframe(top, use_container_width=True, hide_index=True)
    with c2:
        section_header("Alertas")
        inv = stock_df()
        low = inv[(inv.stock <= inv.min_stock) & (inv.active==1)] if not inv.empty else pd.DataFrame()
        no_stock = inv[(inv.stock <= 0) & (inv.active==1) & (inv.sellable==1)] if not inv.empty else pd.DataFrame()
        if not low.empty:
            st.warning(f"{len(low)} productos están en stock mínimo o crítico.")
        if not no_stock.empty:
            st.error(f"{len(no_stock)} productos están agotados.")
        if margin and margin < TARGET_MARGIN:
            st.warning(f"El margen del período ({margin:.1f}%) está debajo de la meta ({TARGET_MARGIN:.1f}%).")
        if receivables > 0:
            st.info(f"Tenés {money(receivables)} pendientes de cobrar.")
        if low.empty and no_stock.empty and (margin >= TARGET_MARGIN or revenue == 0) and receivables <= 0:
            st.success("No hay alertas críticas activas.")

# ============================================================
# PAGE: POS
# ============================================================
elif page == "▣ Venta rápida":
    hero("Venta rápida", "Punto de venta con stock, margen, cliente, vendedor, canal, cobro y cuenta corriente.")
    ensure_cart()

    inv = stock_df()
    inv = inv[(inv.stock > 0) & (inv.sellable==1) & (inv.active==1)].copy() if not inv.empty else inv
    search = st.text_input("Buscar por marca, perfume, SKU o código de barras", placeholder="Ej.: 9PM, Hawas, SKU...")

    if not inv.empty:
        if search:
            mask = (
                inv["brand"].fillna("").str.contains(search, case=False, regex=False)
                | inv["name"].fillna("").str.contains(search, case=False, regex=False)
                | inv["sku"].fillna("").str.contains(search, case=False, regex=False)
                | inv["barcode"].fillna("").str.contains(search, case=False, regex=False)
            )
            choices = inv[mask]
        else:
            choices = inv.head(40)
        if choices.empty:
            st.warning("No se encontraron productos disponibles.")
        else:
            labels = {product_label(r): int(r["id"]) for _, r in choices.iterrows()}
            c1, c2, c3, c4 = st.columns([3,1,1.2,1])
            selected_label = c1.selectbox("Producto", list(labels.keys()))
            pid = labels[selected_label]
            prow = inv[inv.id==pid].iloc[0]
            qty = c2.number_input("Cantidad", min_value=0.1, max_value=float(prow.stock), value=1.0, step=1.0)
            default_price = float(prow.promo_price if prow.promo_price and prow.promo_price > 0 else prow.sale_price)
            price = c3.number_input("Precio unitario", min_value=0.0, value=default_price, step=100.0)
            add = c4.button("Agregar", type="primary", use_container_width=True)
            if add:
                existing = next((x for x in st.session_state.cart if x["product_id"]==pid and abs(x["unit_price"]-price)<1e-9), None)
                if existing:
                    existing["qty"] += qty
                else:
                    st.session_state.cart.append({
                        "product_id": pid, "label": selected_label, "qty": qty,
                        "unit_price": price, "unit_cost": float(prow.avg_cost)
                    })
                st.rerun()
    else:
        st.info("No hay stock vendible. Cargá productos y compras primero.")

    st.markdown("### Carrito")
    if not st.session_state.cart:
        st.caption("Todavía no agregaste productos.")
    else:
        cart_df = pd.DataFrame(st.session_state.cart)
        cart_df["Subtotal"] = cart_df.qty * cart_df.unit_price
        cart_df["Costo"] = cart_df.qty * cart_df.unit_cost
        st.dataframe(
            cart_df[["label","qty","unit_price","Subtotal","Costo"]],
            use_container_width=True, hide_index=True,
            column_config={
                "label":"Producto",
                "qty":"Cant.",
                "unit_price":st.column_config.NumberColumn("Precio", format="$ %.0f"),
                "Subtotal":st.column_config.NumberColumn("Subtotal", format="$ %.0f"),
                "Costo":st.column_config.NumberColumn("Costo", format="$ %.0f"),
            }
        )
        rem_cols = st.columns(len(st.session_state.cart))
        for idx, item in enumerate(list(st.session_state.cart)):
            if rem_cols[idx].button(f"Quitar {idx+1}", key=f"rm_{idx}"):
                st.session_state.cart.pop(idx)
                st.rerun()

        customers = qdf("SELECT id,name,phone,vip FROM customers WHERE active=1 ORDER BY name")
        vendors = qdf("SELECT id,name,commission_pct FROM vendors WHERE active=1 ORDER BY name")
        customer_opts = {"Consumidor final":None}
        if not customers.empty:
            customer_opts.update({f"{r['name']} · {r['phone'] or ''}":int(r["id"]) for _,r in customers.iterrows()})
        vendor_opts = {"Sin vendedor":None}
        if not vendors.empty:
            vendor_opts.update({r["name"]:int(r["id"]) for _,r in vendors.iterrows()})

        st.divider()
        a,b,c,d = st.columns(4)
        customer_label = a.selectbox("Cliente", list(customer_opts.keys()))
        vendor_label = b.selectbox("Vendedor", list(vendor_opts.keys()))
        channel = c.selectbox("Canal", ["Particular","Instagram","WhatsApp","Local","Marketplace","Mayorista","Revendedor","Consignación","Otro"])
        payment = d.selectbox("Forma de pago", ["Efectivo","Transferencia","Mercado Pago","Tarjeta","Cuenta corriente","Otro"])

        subtotal = sum(x["qty"]*x["unit_price"] for x in st.session_state.cart)
        cost = sum(x["qty"]*x["unit_cost"] for x in st.session_state.cart)
        e,f,g,h = st.columns(4)
        discount = e.number_input("Descuento total", min_value=0.0, max_value=float(subtotal), value=0.0, step=100.0)
        shipping = f.number_input("Envío cobrado", min_value=0.0, value=0.0, step=100.0)
        total = max(0.0, subtotal-discount+shipping)
        default_paid = 0.0 if payment=="Cuenta corriente" else total
        paid = g.number_input("Cobrado ahora", min_value=0.0, max_value=float(total), value=float(default_paid), step=100.0)
        notes = h.text_input("Observaciones")

        profit = total-cost
        margin = profit/total*100 if total else 0
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Total", money(total))
        m2.metric("Costo", money(cost))
        m3.metric("Ganancia", money(profit))
        m4.metric("Margen", pct(margin), "OK" if margin>=TARGET_MARGIN else "Debajo de meta")

        if st.button("CONFIRMAR VENTA", type="primary", use_container_width=True):
            try:
                sale_id = save_sale(
                    st.session_state.cart,
                    customer_opts[customer_label],
                    vendor_opts[vendor_label],
                    channel, payment, discount, shipping, paid, notes
                )
                st.session_state.cart = []
                st.success(f"Venta #{sale_id} registrada correctamente.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.divider()
    with st.expander("Últimas ventas / anulaciones"):
        recent = qdf(
            """SELECT s.id,s.date,c.name cliente,v.name vendedor,s.channel,s.payment_method,s.total,s.profit,s.margin,s.paid,s.status
               FROM sales s LEFT JOIN customers c ON c.id=s.customer_id LEFT JOIN vendors v ON v.id=s.vendor_id
               ORDER BY s.id DESC LIMIT 30"""
        )
        if recent.empty:
            st.caption("Sin ventas.")
        else:
            st.dataframe(recent, use_container_width=True, hide_index=True)
            sale_to_void = st.number_input("ID de venta a anular", min_value=0, value=0, step=1)
            if st.button("Anular venta seleccionada"):
                try:
                    refund_sale(int(sale_to_void))
                    st.success("Venta anulada y stock reintegrado.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

# ============================================================
# PAGE: CATALOG
# ============================================================
elif page == "◈ Catálogo":
    hero("Catálogo maestro", "Ficha comercial y olfativa completa de cada perfume, tester y decant.")
    tab1, tab2, tab3 = st.tabs(["Catálogo", "Nuevo producto", "Editar / desactivar"])

    with tab1:
        inv = stock_df(active_only=False)
        c1,c2,c3,c4 = st.columns(4)
        search = c1.text_input("Buscar", key="catalog_search")
        gender = c2.multiselect("Género", sorted([x for x in inv.gender.dropna().unique() if x])) if not inv.empty else []
        ptype = c3.multiselect("Tipo", sorted([x for x in inv.product_type.dropna().unique() if x])) if not inv.empty else []
        active_filter = c4.selectbox("Estado", ["Activos","Todos","Inactivos"])
        view = inv.copy()
        if search and not view.empty:
            mask = (
                view.brand.fillna("").str.contains(search,case=False,regex=False)
                | view.name.fillna("").str.contains(search,case=False,regex=False)
                | view.sku.fillna("").str.contains(search,case=False,regex=False)
            )
            view = view[mask]
        if gender:
            view = view[view.gender.isin(gender)]
        if ptype:
            view = view[view.product_type.isin(ptype)]
        if active_filter=="Activos":
            view = view[view.active==1]
        elif active_filter=="Inactivos":
            view = view[view.active==0]
        if view.empty:
            st.info("No hay productos con esos filtros.")
        else:
            show = view[
                ["id","sku","brand","name","gender","concentration","size_ml","product_type","avg_cost","sale_price","stock","min_stock","location","active"]
            ].copy()
            st.dataframe(
                show, use_container_width=True, hide_index=True,
                column_config={
                    "avg_cost": st.column_config.NumberColumn("Costo", format="$ %.0f"),
                    "sale_price": st.column_config.NumberColumn("Venta", format="$ %.0f"),
                    "stock": st.column_config.NumberColumn("Stock", format="%.1f"),
                }
            )

            st.markdown("#### Ficha")
            id_map = {product_label(r):int(r["id"]) for _,r in view.iterrows()}
            sel = st.selectbox("Abrir producto", list(id_map.keys()))
            r = view[view.id==id_map[sel]].iloc[0]
            a,b,c,d = st.columns(4)
            a.metric("Stock", f"{r.stock:g}")
            b.metric("Costo promedio", money(r.avg_cost))
            c.metric("Precio venta", money(r.sale_price))
            bmargin = (r.sale_price-r.avg_cost)/r.sale_price*100 if r.sale_price else 0
            d.metric("Margen", pct(bmargin))
            st.markdown(
                f"""
                <div class="section">
                <span class="pill">{r.gender or 'Sin género'}</span>
                <span class="pill">{r.concentration or 'Sin concentración'}</span>
                <span class="pill">{r.olfactory_family or 'Familia no definida'}</span>
                <span class="pill">{r.season or 'Temporada no definida'}</span>
                <br><br>
                <b>Salida:</b> {r.top_notes or '—'}<br>
                <b>Corazón:</b> {r.heart_notes or '—'}<br>
                <b>Fondo:</b> {r.base_notes or '—'}<br><br>
                <b>Origen:</b> {r.origin_country or '—'} · <b>Ubicación:</b> {r.location or '—'} · <b>Batch:</b> {r.batch_code or '—'}
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab2:
        suppliers = qdf("SELECT id,name FROM suppliers WHERE active=1 ORDER BY name")
        sup_opts = {"Sin proveedor":None}
        if not suppliers.empty:
            sup_opts.update({r["name"]:int(r["id"]) for _,r in suppliers.iterrows()})
        with st.form("new_product_form", clear_on_submit=True):
            c1,c2,c3,c4 = st.columns(4)
            sku = c1.text_input("SKU*", value=uid("PF-"))
            barcode = c2.text_input("Código de barras")
            brand = c3.text_input("Marca*")
            name = c4.text_input("Nombre*")
            c1,c2,c3,c4 = st.columns(4)
            line = c1.text_input("Línea")
            gender = c2.selectbox("Género", ["Hombre","Mujer","Unisex","Otro"])
            concentration = c3.selectbox("Concentración", ["EDT","EDP","Parfum","Extrait","Cologne","Body Spray","Otro"])
            size_ml = c4.number_input("Tamaño ml", min_value=0.0, value=100.0, step=5.0)
            c1,c2,c3,c4 = st.columns(4)
            origin = c1.text_input("País de fabricación")
            category = c2.selectbox("Categoría", ["Árabe","Diseñador","Nicho","Clásico","Otro"])
            family = c3.text_input("Familia olfativa")
            season = c4.multiselect("Temporada", ["Primavera","Verano","Otoño","Invierno"])
            c1,c2,c3 = st.columns(3)
            top_notes = c1.text_area("Notas de salida")
            heart_notes = c2.text_area("Notas de corazón")
            base_notes = c3.text_area("Notas de fondo")
            c1,c2,c3,c4 = st.columns(4)
            use_time = c1.multiselect("Uso", ["Día","Noche","Oficina","Cita","Fiesta","Formal","Casual"])
            batch = c2.text_input("Batch code")
            supplier_label = c3.selectbox("Proveedor", list(sup_opts.keys()))
            location = c4.text_input("Ubicación física", placeholder="A-2-4")
            c1,c2,c3,c4,c5 = st.columns(5)
            avg_cost = c1.number_input("Costo inicial", min_value=0.0, value=0.0, step=100.0)
            sale_price = c2.number_input("Precio venta", min_value=0.0, value=0.0, step=100.0)
            wholesale = c3.number_input("Mayorista", min_value=0.0, value=0.0, step=100.0)
            reseller = c4.number_input("Revendedor", min_value=0.0, value=0.0, step=100.0)
            promo = c5.number_input("Promocional", min_value=0.0, value=0.0, step=100.0)
            c1,c2 = st.columns(2)
            min_stock = c1.number_input("Stock mínimo", min_value=0.0, value=1.0, step=1.0)
            initial_stock = c2.number_input("Stock inicial", min_value=0.0, value=0.0, step=1.0)
            submitted = st.form_submit_button("Crear producto", type="primary", use_container_width=True)
        if submitted:
            if not brand.strip() or not name.strip() or not sku.strip():
                st.error("SKU, marca y nombre son obligatorios.")
            else:
                try:
                    cur = execute(
                        """INSERT INTO products(sku,barcode,brand,name,line,gender,concentration,size_ml,origin_country,category,product_type,
                           olfactory_family,top_notes,heart_notes,base_notes,season,use_time,batch_code,supplier_id,avg_cost,sale_price,
                           wholesale_price,reseller_price,promo_price,min_stock,location,sellable,active,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            sku.strip(), barcode.strip(), brand.strip(), name.strip(), line.strip(), gender, concentration, size_ml,
                            origin.strip(), category, "PERFUME", family.strip(), top_notes.strip(), heart_notes.strip(), base_notes.strip(),
                            ",".join(season), ",".join(use_time), batch.strip(), sup_opts[supplier_label], avg_cost, sale_price,
                            wholesale, reseller, promo, min_stock, location.strip(), 1, 1, now_iso()
                        )
                    )
                    pid = cur.lastrowid
                    if initial_stock > 0:
                        add_inventory_move(pid, "STOCK_INICIAL", initial_stock, avg_cost, "SETUP", None, "Carga inicial")
                    st.success("Producto creado.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Ese SKU ya existe.")

    with tab3:
        inv = stock_df(active_only=False)
        if inv.empty:
            st.info("No hay productos.")
        else:
            labels = {product_label(r):int(r["id"]) for _,r in inv.iterrows()}
            sel = st.selectbox("Producto a editar", list(labels.keys()), key="edit_product_select")
            pid = labels[sel]
            r = inv[inv.id==pid].iloc[0]
            with st.form("edit_product_form"):
                c1,c2,c3,c4 = st.columns(4)
                e_brand = c1.text_input("Marca", value=r.brand or "")
                e_name = c2.text_input("Nombre", value=r["name"] or "")
                e_gender = c3.selectbox("Género", ["Hombre","Mujer","Unisex","Otro"], index=(["Hombre","Mujer","Unisex","Otro"].index(r.gender) if r.gender in ["Hombre","Mujer","Unisex","Otro"] else 0))
                e_conc = c4.text_input("Concentración", value=r.concentration or "")
                c1,c2,c3,c4 = st.columns(4)
                e_cost = c1.number_input("Costo promedio", min_value=0.0, value=float(r.avg_cost), step=100.0)
                e_sale = c2.number_input("Precio venta", min_value=0.0, value=float(r.sale_price), step=100.0)
                e_min = c3.number_input("Stock mínimo", min_value=0.0, value=float(r.min_stock), step=1.0)
                e_loc = c4.text_input("Ubicación", value=r.location or "")
                c1,c2,c3 = st.columns(3)
                e_wh = c1.number_input("Mayorista", min_value=0.0, value=float(r.wholesale_price), step=100.0)
                e_res = c2.number_input("Revendedor", min_value=0.0, value=float(r.reseller_price), step=100.0)
                e_promo = c3.number_input("Promo", min_value=0.0, value=float(r.promo_price), step=100.0)
                e_active = st.checkbox("Producto activo", value=bool(r.active))
                e_sellable = st.checkbox("Vendible", value=bool(r.sellable))
                save = st.form_submit_button("Guardar cambios", type="primary", use_container_width=True)
            if save:
                execute(
                    """UPDATE products SET brand=?,name=?,gender=?,concentration=?,avg_cost=?,sale_price=?,min_stock=?,location=?,
                       wholesale_price=?,reseller_price=?,promo_price=?,active=?,sellable=? WHERE id=?""",
                    (e_brand,e_name,e_gender,e_conc,e_cost,e_sale,e_min,e_loc,e_wh,e_res,e_promo,int(e_active),int(e_sellable),pid)
                )
                st.success("Producto actualizado.")
                st.rerun()

# ============================================================
# PAGE: INVENTORY
# ============================================================
elif page == "▤ Inventario":
    hero("Inventario PRO", "Stock real, comprometido, antigüedad, movimientos, ajustes, pérdidas y trazabilidad.")
    inv = stock_df()
    last = last_sale_by_product()
    if not inv.empty:
        inv = inv.merge(last, how="left", left_on="id", right_on="product_id")
        inv["stock_value"] = inv["stock"].clip(lower=0) * inv["avg_cost"]
        inv["retail_value"] = inv["stock"].clip(lower=0) * inv["sale_price"]
        inv["last_sale_date"] = pd.to_datetime(inv["last_sale_date"], errors="coerce")
        inv["days_without_sale"] = (pd.Timestamp.today().normalize() - inv["last_sale_date"]).dt.days
        inv.loc[inv["last_sale_date"].isna(), "days_without_sale"] = 9999

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("SKUs activos", len(inv) if not inv.empty else 0)
    c2.metric("Unidades", f"{inv.stock.clip(lower=0).sum():g}" if not inv.empty else "0")
    c3.metric("Capital inmovilizado", money(inv.stock_value.sum() if not inv.empty else 0))
    c4.metric("Valor a venta", money(inv.retail_value.sum() if not inv.empty else 0))

    tabs = st.tabs(["Stock", "Movimientos", "Ajuste", "Stock envejecido", "Ubicaciones"])
    with tabs[0]:
        if inv.empty:
            st.info("Sin productos.")
        else:
            filter_stock = st.selectbox("Estado de stock", ["Todos","Con stock","Crítico","Agotado"])
            v = inv.copy()
            if filter_stock=="Con stock":
                v=v[v.stock>0]
            elif filter_stock=="Crítico":
                v=v[(v.stock>0)&(v.stock<=v.min_stock)]
            elif filter_stock=="Agotado":
                v=v[v.stock<=0]
            show=v[["sku","brand","name","size_ml","product_type","stock","min_stock","avg_cost","sale_price","stock_value","location"]]
            st.dataframe(show,use_container_width=True,hide_index=True)

    with tabs[1]:
        moves = qdf(
            """SELECT im.id,im.date,p.sku,p.brand,p.name,im.move_type,im.qty,im.unit_cost,im.reference_type,im.reference_id,im.notes,im.user_name
               FROM inventory_moves im JOIN products p ON p.id=im.product_id ORDER BY im.id DESC LIMIT 500"""
        )
        st.dataframe(moves,use_container_width=True,hide_index=True)

    with tabs[2]:
        if inv.empty:
            st.info("Creá productos primero.")
        else:
            labels={product_label(r):int(r["id"]) for _,r in inv.iterrows()}
            with st.form("adjust_stock"):
                sel=st.selectbox("Producto",list(labels.keys()))
                kind=st.selectbox("Tipo",["AJUSTE_POSITIVO","AJUSTE_NEGATIVO","ROTURA","PERDIDA","REGALO","MUESTRA","USO_PERSONAL","DEVOLUCION"])
                qty=st.number_input("Cantidad",min_value=0.01,value=1.0,step=1.0)
                note=st.text_input("Motivo / observación")
                submit=st.form_submit_button("Registrar movimiento",type="primary")
            if submit:
                sign = 1 if kind in ["AJUSTE_POSITIVO","DEVOLUCION"] else -1
                pid=labels[sel]
                if sign<0 and current_stock(pid)<qty:
                    st.error("No hay stock suficiente.")
                else:
                    cost=safe_float(scalar("SELECT avg_cost FROM products WHERE id=?",(pid,),0))
                    add_inventory_move(pid,kind,sign*qty,cost,"MANUAL",None,note)
                    st.success("Movimiento registrado.")
                    st.rerun()

    with tabs[3]:
        if inv.empty:
            st.info("Sin inventario.")
        else:
            age=inv[(inv.stock>0)&(inv.days_without_sale>=60)].copy()
            age["days_without_sale"]=age["days_without_sale"].replace(9999,np.nan)
            if age.empty:
                st.success("No hay stock con más de 60 días sin venta.")
            else:
                st.warning(f"{money(age.stock_value.sum())} están inmovilizados en productos con baja o nula rotación.")
                st.dataframe(age[["brand","name","stock","stock_value","last_sale_date","days_without_sale","sale_price"]],use_container_width=True,hide_index=True)

    with tabs[4]:
        if inv.empty:
            st.info("Sin datos.")
        else:
            loc=inv.groupby(inv.location.fillna("Sin ubicación"),as_index=False).agg(SKUs=("id","count"),Unidades=("stock","sum"),Capital=("stock_value","sum"))
            st.dataframe(loc,use_container_width=True,hide_index=True)

# ============================================================
# PAGE: PURCHASES
# ============================================================
elif page == "◆ Compras":
    hero("Compras y proveedores", "Costo aterrizado real, deuda con proveedor, ingreso de stock y actualización automática del costo promedio.")
    t1,t2,t3 = st.tabs(["Nueva compra","Historial","Proveedores"])

    with t3:
        with st.form("new_supplier", clear_on_submit=True):
            a,b,c = st.columns(3)
            name=a.text_input("Proveedor*")
            contact=b.text_input("Contacto")
            phone=c.text_input("Teléfono")
            a,b,c = st.columns(3)
            email=a.text_input("Email")
            country=b.text_input("País")
            taxid=c.text_input("CUIT / ID fiscal")
            notes=st.text_area("Notas")
            sub=st.form_submit_button("Crear proveedor",type="primary")
        if sub and name.strip():
            execute("INSERT INTO suppliers(name,contact,phone,email,country,tax_id,notes,active,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                    (name.strip(),contact,phone,email,country,taxid,notes,1,now_iso()))
            st.success("Proveedor creado.")
            st.rerun()
        suppliers=qdf("SELECT * FROM suppliers ORDER BY id DESC")
        st.dataframe(suppliers,use_container_width=True,hide_index=True)

    with t1:
        suppliers=qdf("SELECT id,name FROM suppliers WHERE active=1 ORDER BY name")
        products=qdf("SELECT id,sku,brand,name,size_ml,avg_cost FROM products WHERE active=1 AND product_type!='DECANT' ORDER BY brand,name")
        if suppliers.empty:
            st.warning("Primero creá al menos un proveedor.")
        elif products.empty:
            st.warning("Primero creá productos en Catálogo.")
        else:
            if "purchase_cart" not in st.session_state:
                st.session_state.purchase_cart=[]
            sup_map={r["name"]:int(r["id"]) for _,r in suppliers.iterrows()}
            prod_map={f"{r['brand']} {r['name']} {r['size_ml']:g}ml · {r['sku']}":int(r["id"]) for _,r in products.iterrows()}
            a,b,c = st.columns([3,1,1.2])
            pl=a.selectbox("Producto",list(prod_map.keys()),key="purch_prod")
            q=b.number_input("Cantidad",min_value=0.1,value=1.0,step=1.0,key="purch_qty")
            up=c.number_input("Costo unitario proveedor",min_value=0.0,value=float(products[products.id==prod_map[pl]].iloc[0].avg_cost),step=100.0,key="purch_cost")
            if st.button("Agregar a compra",type="primary"):
                st.session_state.purchase_cart.append({"product_id":prod_map[pl],"label":pl,"qty":q,"unit_price":up})
                st.rerun()
            if st.session_state.purchase_cart:
                pdf=pd.DataFrame(st.session_state.purchase_cart)
                pdf["subtotal"]=pdf.qty*pdf.unit_price
                st.dataframe(pdf[["label","qty","unit_price","subtotal"]],use_container_width=True,hide_index=True)
                if st.button("Vaciar compra"):
                    st.session_state.purchase_cart=[]
                    st.rerun()
                with st.form("purchase_final"):
                    a,b,c,d=st.columns(4)
                    supplier_label=a.selectbox("Proveedor",list(sup_map.keys()))
                    invoice=b.text_input("Factura / referencia")
                    payment=c.selectbox("Forma de pago",["Efectivo","Transferencia","Mercado Pago","Tarjeta","Cuenta corriente","Otro"])
                    status=d.selectbox("Estado",["Recibida","Parcial","Pendiente"])
                    a,b,c=st.columns(3)
                    shipping=a.number_input("Envío",min_value=0.0,value=0.0,step=100.0)
                    fees=b.number_input("Comisiones",min_value=0.0,value=0.0,step=100.0)
                    taxes=c.number_input("Impuestos",min_value=0.0,value=0.0,step=100.0)
                    items_sub=sum(i["qty"]*i["unit_price"] for i in st.session_state.purchase_cart)
                    grand=items_sub+shipping+fees+taxes
                    paid=st.number_input("Pagado ahora",min_value=0.0,max_value=float(grand),value=float(grand),step=100.0)
                    notes=st.text_area("Notas")
                    done=st.form_submit_button("CONFIRMAR COMPRA",type="primary",use_container_width=True)
                if done:
                    try:
                        pid=save_purchase(st.session_state.purchase_cart,sup_map[supplier_label],invoice,payment,shipping,fees,taxes,paid,status,notes)
                        st.session_state.purchase_cart=[]
                        st.success(f"Compra #{pid} registrada.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            else:
                st.caption("Agregá productos para armar la compra.")

    with t2:
        hist=qdf(
            """SELECT p.id,p.date,s.name proveedor,p.invoice,p.payment_method,p.items_subtotal,p.shipping,p.fees,p.taxes,p.total,p.paid,
                      (p.total-p.paid) pendiente,p.status
               FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id ORDER BY p.id DESC"""
        )
        st.dataframe(hist,use_container_width=True,hide_index=True)

# ============================================================
# PAGE: CUSTOMERS
# ============================================================
elif page == "♙ Clientes":
    hero("CRM de clientes", "Historial, preferencias, ticket, recurrencia, valor de vida y oportunidades de recompra.")
    t1,t2,t3=st.tabs(["Base de clientes","Nuevo cliente","Oportunidades"])
    with t2:
        with st.form("new_customer",clear_on_submit=True):
            a,b,c=st.columns(3)
            name=a.text_input("Nombre*")
            phone=b.text_input("WhatsApp")
            instagram=c.text_input("Instagram")
            a,b,c=st.columns(3)
            email=a.text_input("Email")
            birthday=b.date_input("Cumpleaños",value=None)
            gender=c.selectbox("Perfil",["","Hombre","Mujer","Unisex"])
            families=st.text_input("Familias preferidas",placeholder="Amaderado, dulce, oriental...")
            notes=st.text_area("Notas comerciales")
            vip=st.checkbox("Marcar VIP")
            done=st.form_submit_button("Crear cliente",type="primary")
        if done and name.strip():
            execute("""INSERT INTO customers(name,phone,instagram,email,birthday,gender,preferred_families,notes,vip,active,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (name.strip(),phone,instagram,email,str(birthday) if birthday else None,gender,families,notes,int(vip),1,now_iso()))
            st.success("Cliente creado.")
            st.rerun()

    with t1:
        crm=qdf(
            """SELECT c.id,c.name,c.phone,c.instagram,c.vip,
                      COUNT(DISTINCT s.id) compras,
                      COALESCE(SUM(CASE WHEN s.status='Completada' THEN s.total ELSE 0 END),0) total_gastado,
                      COALESCE(AVG(CASE WHEN s.status='Completada' THEN s.total END),0) ticket_promedio,
                      MAX(CASE WHEN s.status='Completada' THEN s.date END) ultima_compra
               FROM customers c LEFT JOIN sales s ON s.customer_id=c.id
               WHERE c.active=1 GROUP BY c.id ORDER BY total_gastado DESC"""
        )
        if crm.empty:
            st.info("Todavía no hay clientes.")
        else:
            st.dataframe(crm,use_container_width=True,hide_index=True)
            cmap={f"{r['name']} · {r['phone'] or ''}":int(r["id"]) for _,r in crm.iterrows()}
            sel=st.selectbox("Abrir cliente",list(cmap.keys()))
            cid=cmap[sel]
            r=crm[crm.id==cid].iloc[0]
            a,b,c,d=st.columns(4)
            a.metric("Compras",int(r.compras))
            b.metric("Total gastado",money(r.total_gastado))
            c.metric("Ticket promedio",money(r.ticket_promedio))
            d.metric("Última compra",r.ultima_compra or "—")
            bought=qdf(
                """SELECT s.date,p.brand,p.name,p.size_ml,si.qty,si.unit_price
                   FROM sale_items si JOIN sales s ON s.id=si.sale_id JOIN products p ON p.id=si.product_id
                   WHERE s.customer_id=? AND s.status='Completada' ORDER BY s.id DESC""",(cid,)
            )
            st.dataframe(bought,use_container_width=True,hide_index=True)

    with t3:
        opp=qdf(
            """SELECT c.id,c.name,c.phone,c.instagram,MAX(s.date) ultima_compra,SUM(s.total) total_gastado,COUNT(s.id) compras
               FROM customers c JOIN sales s ON s.customer_id=c.id
               WHERE s.status='Completada'
               GROUP BY c.id"""
        )
        if opp.empty:
            st.info("Necesitás historial de ventas para detectar oportunidades.")
        else:
            opp["ultima_compra"]=pd.to_datetime(opp.ultima_compra)
            opp["dias_sin_comprar"]=(pd.Timestamp.today().normalize()-opp.ultima_compra).dt.days
            opp=opp[opp.dias_sin_comprar>=45].sort_values(["total_gastado","dias_sin_comprar"],ascending=[False,False])
            st.info("Clientes con 45+ días sin comprar, priorizados por valor histórico.")
            st.dataframe(opp,use_container_width=True,hide_index=True)

# ============================================================
# PAGE: VENDORS
# ============================================================
elif page == "♜ Vendedores":
    hero("Vendedores y socios comerciales", "Facturación, margen, comisión, cobranza y desempeño individual.")
    t1,t2=st.tabs(["Desempeño","Nuevo vendedor"])
    with t2:
        with st.form("new_vendor",clear_on_submit=True):
            a,b,c=st.columns(3)
            name=a.text_input("Nombre*")
            phone=b.text_input("Teléfono")
            email=c.text_input("Email")
            commission=st.number_input("Comisión %",min_value=0.0,max_value=100.0,value=0.0,step=0.5)
            notes=st.text_area("Notas")
            done=st.form_submit_button("Crear vendedor",type="primary")
        if done and name.strip():
            execute("INSERT INTO vendors(name,phone,email,commission_pct,notes,active,created_at) VALUES(?,?,?,?,?,?,?)",
                    (name.strip(),phone,email,commission,notes,1,now_iso()))
            st.success("Vendedor creado.")
            st.rerun()
    with t1:
        perf=qdf(
            """SELECT v.id,v.name,v.commission_pct,
                      COUNT(s.id) ventas,COALESCE(SUM(s.total),0) facturacion,COALESCE(SUM(s.profit),0) ganancia,
                      COALESCE(AVG(s.total),0) ticket_promedio
               FROM vendors v LEFT JOIN sales s ON s.vendor_id=v.id AND s.status='Completada'
               WHERE v.active=1 GROUP BY v.id ORDER BY facturacion DESC"""
        )
        if perf.empty:
            st.info("No hay vendedores.")
        else:
            perf["comision_estimada"]=perf.facturacion*perf.commission_pct/100
            st.dataframe(perf,use_container_width=True,hide_index=True)
            st.bar_chart(perf.set_index("name")["facturacion"])

# ============================================================
# PAGE: RESERVATIONS
# ============================================================
elif page == "◫ Reservas y pedidos":
    hero("Reservas y pedidos", "Seguimiento desde la consulta hasta la entrega y el cobro.")
    t1,t2=st.tabs(["Pipeline","Nueva reserva"])
    with t2:
        customers=qdf("SELECT id,name FROM customers WHERE active=1 ORDER BY name")
        inv=stock_df()
        inv=inv[(inv.active==1)&(inv.sellable==1)] if not inv.empty else inv
        vendors=qdf("SELECT id,name FROM vendors WHERE active=1 ORDER BY name")
        if customers.empty or inv.empty:
            st.info("Necesitás al menos un cliente y un producto.")
        else:
            cm={r["name"]:int(r["id"]) for _,r in customers.iterrows()}
            pm={product_label(r):int(r["id"]) for _,r in inv.iterrows()}
            vm={"Sin vendedor":None}
            vm.update({r["name"]:int(r["id"]) for _,r in vendors.iterrows()})
            with st.form("new_reservation"):
                a,b,c=st.columns(3)
                cl=a.selectbox("Cliente",list(cm.keys()))
                pr=b.selectbox("Producto",list(pm.keys()))
                qty=c.number_input("Cantidad",min_value=1.0,value=1.0,step=1.0)
                a,b,c=st.columns(3)
                total=a.number_input("Total acordado",min_value=0.0,value=float(inv[inv.id==pm[pr]].iloc[0].sale_price),step=100.0)
                dep=b.number_input("Seña",min_value=0.0,max_value=float(total),value=0.0,step=100.0)
                due=c.date_input("Fecha prometida",value=date.today()+timedelta(days=7))
                a,b=st.columns(2)
                status=a.selectbox("Estado",["Consulta","Reservado","Seña","Preparado","Entregado","Cobrado","Cancelado"])
                vend=b.selectbox("Vendedor",list(vm.keys()))
                notes=st.text_area("Notas")
                done=st.form_submit_button("Guardar reserva",type="primary")
            if done:
                cur=execute("""INSERT INTO reservations(date,customer_id,product_id,qty,deposit,total,due_date,status,vendor_id,notes,created_at)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                            (today_iso(),cm[cl],pm[pr],qty,dep,total,str(due),status,vm[vend],notes,now_iso()))
                if dep>0:
                    add_cash_move("INGRESO","Seña reserva","Efectivo",dep,"RESERVATION",cur.lastrowid,notes)
                st.success("Reserva creada.")
                st.rerun()
    with t1:
        pipe=qdf(
            """SELECT r.id,r.date,c.name cliente,p.brand||' '||p.name producto,r.qty,r.deposit,r.total,(r.total-r.deposit) saldo,
                      r.due_date,r.status,v.name vendedor,r.notes
               FROM reservations r JOIN customers c ON c.id=r.customer_id JOIN products p ON p.id=r.product_id
               LEFT JOIN vendors v ON v.id=r.vendor_id ORDER BY r.id DESC"""
        )
        if pipe.empty:
            st.info("No hay reservas.")
        else:
            st.dataframe(pipe,use_container_width=True,hide_index=True)
            rid=st.number_input("ID a actualizar",min_value=0,value=0,step=1)
            new_status=st.selectbox("Nuevo estado",["Consulta","Reservado","Seña","Preparado","Entregado","Cobrado","Cancelado"])
            if st.button("Actualizar estado"):
                execute("UPDATE reservations SET status=? WHERE id=?",(new_status,int(rid)))
                st.success("Estado actualizado.")
                st.rerun()

# ============================================================
# PAGE: CURRENT ACCOUNTS
# ============================================================
elif page == "↔ Cuentas corrientes":
    hero("Cuentas corrientes", "Saldos de clientes y proveedores con movimientos y cobranzas.")
    tabc,tabs=st.tabs(["Clientes","Proveedores"])
    with tabc:
        balances=qdf(
            """SELECT c.id,c.name,c.phone,COALESCE(SUM(l.debit-l.credit),0) saldo
               FROM customers c LEFT JOIN account_ledger l ON l.entity_type='CUSTOMER' AND l.entity_id=c.id
               WHERE c.active=1 GROUP BY c.id HAVING ABS(saldo)>0.001 ORDER BY saldo DESC"""
        )
        st.dataframe(balances,use_container_width=True,hide_index=True)
        customers=qdf("SELECT id,name FROM customers WHERE active=1 ORDER BY name")
        if not customers.empty:
            cm={r["name"]:int(r["id"]) for _,r in customers.iterrows()}
            with st.form("customer_payment"):
                cl=st.selectbox("Cliente",list(cm.keys()))
                amount=st.number_input("Cobro",min_value=0.0,value=0.0,step=100.0)
                method=st.selectbox("Medio",["Efectivo","Transferencia","Mercado Pago","Tarjeta","Otro"])
                note=st.text_input("Nota")
                done=st.form_submit_button("Registrar cobro",type="primary")
            if done and amount>0:
                execute("""INSERT INTO account_ledger(date,entity_type,entity_id,concept,debit,credit,reference_type,reference_id,notes,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?)""",
                        (today_iso(),"CUSTOMER",cm[cl],"Cobro",0,amount,"PAYMENT",None,note,now_iso()))
                add_cash_move("INGRESO","Cobranza cliente",method,amount,"CUSTOMER",cm[cl],note)
                st.success("Cobro registrado.")
                st.rerun()
    with tabs:
        balances=qdf(
            """SELECT s.id,s.name,COALESCE(SUM(l.credit-l.debit),0) saldo
               FROM suppliers s LEFT JOIN account_ledger l ON l.entity_type='SUPPLIER' AND l.entity_id=s.id
               WHERE s.active=1 GROUP BY s.id HAVING ABS(saldo)>0.001 ORDER BY saldo DESC"""
        )
        st.dataframe(balances,use_container_width=True,hide_index=True)
        suppliers=qdf("SELECT id,name FROM suppliers WHERE active=1 ORDER BY name")
        if not suppliers.empty:
            sm={r["name"]:int(r["id"]) for _,r in suppliers.iterrows()}
            with st.form("supplier_payment"):
                sl=st.selectbox("Proveedor",list(sm.keys()))
                amount=st.number_input("Pago",min_value=0.0,value=0.0,step=100.0)
                method=st.selectbox("Medio",["Efectivo","Transferencia","Mercado Pago","Tarjeta","Otro"],key="supp_method")
                note=st.text_input("Nota",key="supp_note")
                done=st.form_submit_button("Registrar pago",type="primary")
            if done and amount>0:
                execute("""INSERT INTO account_ledger(date,entity_type,entity_id,concept,debit,credit,reference_type,reference_id,notes,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?)""",
                        (today_iso(),"SUPPLIER",sm[sl],"Pago",amount,0,"PAYMENT",None,note,now_iso()))
                add_cash_move("EGRESO","Pago proveedor",method,amount,"SUPPLIER",sm[sl],note)
                st.success("Pago registrado.")
                st.rerun()

# ============================================================
# PAGE: CASH & FINANCE
# ============================================================
elif page == "$ Caja y finanzas":
    hero("Caja y finanzas", "Ingresos, egresos, gastos, resultado operativo y posición de caja.")
    tab1,tab2,tab3=st.tabs(["Resumen","Registrar gasto / movimiento","Movimientos"])

    with tab1:
        month=st.date_input("Mes",value=date.today().replace(day=1),key="finance_month")
        start,end=date_range_for_month(month)
        s=period_sales(start,end)
        rev=s.total.sum() if not s.empty else 0
        gross=s.profit.sum() if not s.empty else 0
        exp=safe_float(scalar("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date>=? AND date<?",(str(start),str(end)),0))
        net=gross-exp
        a,b,c,d=st.columns(4)
        a.metric("Ventas",money(rev))
        b.metric("Margen bruto",money(gross))
        c.metric("Gastos operativos",money(exp))
        d.metric("Resultado operativo",money(net))
        cash=qdf(
            """SELECT method,
                      SUM(CASE WHEN direction='INGRESO' THEN amount ELSE -amount END) saldo
               FROM cash_moves GROUP BY method ORDER BY saldo DESC"""
        )
        st.markdown("### Caja por medio")
        st.dataframe(cash,use_container_width=True,hide_index=True)

    with tab2:
        mode=st.radio("Tipo",["Gasto operativo","Movimiento de caja"],horizontal=True)
        if mode=="Gasto operativo":
            with st.form("expense_form",clear_on_submit=True):
                a,b,c=st.columns(3)
                cat=a.selectbox("Categoría",["Publicidad","Envíos","Packaging","Servicios","Impuestos","Comisiones","Movilidad","Alquiler","Sueldos","Otros"])
                supplier=b.text_input("Proveedor / destinatario")
                method=c.selectbox("Medio",["Efectivo","Transferencia","Mercado Pago","Tarjeta","Otro"])
                amount=st.number_input("Importe",min_value=0.0,value=0.0,step=100.0)
                notes=st.text_area("Notas")
                done=st.form_submit_button("Registrar gasto",type="primary")
            if done and amount>0:
                cur=execute("INSERT INTO expenses(date,category,supplier,method,amount,notes,created_at) VALUES(?,?,?,?,?,?,?)",
                            (today_iso(),cat,supplier,method,amount,notes,now_iso()))
                add_cash_move("EGRESO",cat,method,amount,"EXPENSE",cur.lastrowid,notes)
                st.success("Gasto registrado.")
                st.rerun()
        else:
            with st.form("cash_manual",clear_on_submit=True):
                a,b,c=st.columns(3)
                direction=a.selectbox("Dirección",["INGRESO","EGRESO"])
                category=b.text_input("Categoría")
                method=c.selectbox("Medio",["Efectivo","Transferencia","Mercado Pago","Tarjeta","Otro"])
                amount=st.number_input("Importe",min_value=0.0,value=0.0,step=100.0,key="cash_amt")
                notes=st.text_area("Notas",key="cash_notes")
                done=st.form_submit_button("Registrar",type="primary")
            if done and amount>0:
                add_cash_move(direction,category,method,amount,"MANUAL",None,notes)
                st.success("Movimiento registrado.")
                st.rerun()

    with tab3:
        cash=qdf("SELECT * FROM cash_moves ORDER BY id DESC LIMIT 500")
        st.dataframe(cash,use_container_width=True,hide_index=True)

# ============================================================
# PAGE: DECANTS & TESTERS
# ============================================================
elif page == "◌ Decants y testers":
    hero("Decants y testers", "Apertura controlada de botellas, pool de mililitros y producción de decants con costo real.")
    tab1,tab2=st.tabs(["Producir decants","Pools y testers"])
    with tab1:
        inv=stock_df()
        parents=inv[(inv.product_type=="PERFUME")&(inv.active==1)&(inv.size_ml>0)] if not inv.empty else inv
        if parents.empty:
            st.info("Necesitás perfumes completos para producir decants.")
        else:
            pm={product_label(r):int(r["id"]) for _,r in parents.iterrows()}
            with st.form("decant_form"):
                pl=st.selectbox("Botella madre",list(pm.keys()))
                a,b,c,d=st.columns(4)
                ml=a.selectbox("Tamaño decant",[2.0,3.0,5.0,10.0,15.0])
                qty=b.number_input("Cantidad a producir",min_value=1,value=1,step=1)
                packaging=c.number_input("Costo envase + etiqueta por unidad",min_value=0.0,value=0.0,step=50.0)
                sale_price=d.number_input("Precio de venta por decant",min_value=0.0,value=0.0,step=100.0)
                location=st.text_input("Ubicación",value="Decants")
                done=st.form_submit_button("Producir decants",type="primary")
            if done:
                try:
                    did,pool=create_decants(pm[pl],float(ml),int(qty),packaging,sale_price,location)
                    st.success(f"Decants producidos. Producto #{did}. Pool restante: {pool:g} ml.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
    with tab2:
        pools=qdf(
            """SELECT p.brand,p.name,p.size_ml botella_ml,d.available_ml,d.updated_at
               FROM decant_pools d JOIN products p ON p.id=d.product_id ORDER BY d.updated_at DESC"""
        )
        st.markdown("#### Pools de ml")
        st.dataframe(pools,use_container_width=True,hide_index=True)
        testers=qdf(
            """SELECT p.id,p.sku,p.brand,p.name,p.size_ml,p.sellable,COALESCE(SUM(im.qty),0) stock
               FROM products p LEFT JOIN inventory_moves im ON im.product_id=p.id
               WHERE p.sellable=0 OR p.category='Tester'
               GROUP BY p.id"""
        )
        st.markdown("#### Testers / no vendibles")
        st.dataframe(testers,use_container_width=True,hide_index=True)

# ============================================================
# PAGE: PROMOS & MARKETING
# ============================================================
elif page == "◇ Promociones y marketing":
    hero("Promociones y marketing", "Campañas, promociones, inversión publicitaria, ventas atribuidas y ROAS.")
    t1,t2,t3=st.tabs(["Promociones","Campañas","Análisis"])
    with t1:
        with st.form("promo_form",clear_on_submit=True):
            a,b,c=st.columns(3)
            name=a.text_input("Nombre de promoción*")
            ptype=b.selectbox("Tipo",["% descuento","Monto descuento","Precio especial","Combo"])
            value=c.number_input("Valor",min_value=0.0,value=0.0,step=1.0)
            a,b,c=st.columns(3)
            start=a.date_input("Desde",value=date.today())
            end=b.date_input("Hasta",value=date.today()+timedelta(days=7))
            qty=c.number_input("Cantidad mínima",min_value=1.0,value=1.0,step=1.0)
            scope=st.text_input("Alcance",value="Todos",placeholder="Todos / Marca / SKU / Categoría")
            notes=st.text_area("Condiciones")
            done=st.form_submit_button("Crear promoción",type="primary")
        if done and name.strip():
            execute("""INSERT INTO promotions(name,promo_type,value,start_date,end_date,min_qty,scope,active,notes,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (name,ptype,value,str(start),str(end),qty,scope,1,notes,now_iso()))
            st.success("Promoción creada.")
            st.rerun()
        promos=qdf("SELECT * FROM promotions ORDER BY id DESC")
        st.dataframe(promos,use_container_width=True,hide_index=True)
    with t2:
        with st.form("campaign_form",clear_on_submit=True):
            a,b,c=st.columns(3)
            name=a.text_input("Campaña*")
            channel=b.selectbox("Canal",["Instagram Ads","Instagram orgánico","WhatsApp","Influencer","Sorteo","Marketplace","Otro"])
            spend=c.number_input("Inversión",min_value=0.0,value=0.0,step=100.0)
            a,b=st.columns(2)
            sales=a.number_input("Ventas atribuidas",min_value=0.0,value=0.0,step=100.0)
            profit=b.number_input("Ganancia atribuida",min_value=0.0,value=0.0,step=100.0)
            notes=st.text_area("Notas")
            done=st.form_submit_button("Guardar campaña",type="primary")
        if done and name.strip():
            execute("INSERT INTO campaign_log(date,name,channel,spend,attributed_sales,attributed_profit,notes,created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (today_iso(),name,channel,spend,sales,profit,notes,now_iso()))
            st.success("Campaña guardada.")
            st.rerun()
    with t3:
        camp=qdf("SELECT * FROM campaign_log ORDER BY id DESC")
        if camp.empty:
            st.info("Sin campañas.")
        else:
            camp["ROAS"]=camp.apply(lambda r:r.attributed_sales/r.spend if r.spend else 0,axis=1)
            camp["ROI_marketing_%"]=camp.apply(lambda r:(r.attributed_profit-r.spend)/r.spend*100 if r.spend else 0,axis=1)
            st.dataframe(camp,use_container_width=True,hide_index=True)

# ============================================================
# PAGE: REPLENISHMENT
# ============================================================
elif page == "↻ Reposición":
    hero("Centro de reposición", "Qué comprar, cuánto comprar y cuánto capital requiere, usando ventas recientes y cobertura estimada.")
    inv=stock_df()
    if inv.empty:
        st.info("Sin inventario.")
    else:
        days=st.slider("Ventana de demanda (días)",30,180,60,10)
        cover_days=st.slider("Cobertura objetivo (días)",7,90,30,1)
        cutoff=(date.today()-timedelta(days=days)).isoformat()
        demand=qdf(
            """SELECT si.product_id,SUM(si.qty) units
               FROM sale_items si JOIN sales s ON s.id=si.sale_id
               WHERE s.status='Completada' AND s.date>=?
               GROUP BY si.product_id""",(cutoff,)
        )
        inv=inv.merge(demand,how="left",left_on="id",right_on="product_id")
        inv["units"]=inv["units"].fillna(0)
        inv["daily_velocity"]=inv["units"]/days
        inv["target_stock"]=np.ceil(inv["daily_velocity"]*cover_days)
        inv["suggested_qty"]=np.maximum(0,np.ceil(inv["target_stock"]-inv["stock"]))
        inv.loc[(inv["daily_velocity"]==0)&(inv["stock"]<=inv["min_stock"]),"suggested_qty"]=np.maximum(
            0,inv["min_stock"]-inv["stock"]+1
        )
        inv["capital_needed"]=inv["suggested_qty"]*inv["avg_cost"]
        rec=inv[(inv.suggested_qty>0)&(inv.product_type=="PERFUME")].sort_values(["daily_velocity","capital_needed"],ascending=[False,False])
        a,b,c=st.columns(3)
        a.metric("SKUs a reponer",len(rec))
        b.metric("Capital sugerido",money(rec.capital_needed.sum() if not rec.empty else 0))
        c.metric("Cobertura objetivo",f"{cover_days} días")
        if rec.empty:
            st.success("No hay reposiciones sugeridas con los parámetros actuales.")
        else:
            st.dataframe(rec[["sku","brand","name","stock","units","daily_velocity","target_stock","suggested_qty","avg_cost","capital_needed"]],use_container_width=True,hide_index=True)

# ============================================================
# PAGE: INTELLIGENCE
# ============================================================
elif page == "✦ Centro inteligente":
    hero("Centro inteligente", "Reglas automáticas para detectar estrellas, capital inmovilizado, margen, cobranza y próximas acciones.")
    inv=stock_df()
    days90=(date.today()-timedelta(days=90)).isoformat()
    perf=qdf(
        """SELECT p.id,p.brand,p.name,p.size_ml,
                  SUM(si.qty) units90,
                  SUM(si.subtotal) revenue90,
                  SUM((si.unit_price-si.unit_cost)*si.qty) profit90
           FROM products p
           LEFT JOIN sale_items si ON si.product_id=p.id
           LEFT JOIN sales s ON s.id=si.sale_id AND s.status='Completada' AND s.date>=?
           GROUP BY p.id""",(days90,)
    )
    if not inv.empty:
        perf=perf.merge(inv[["id","stock","avg_cost","sale_price","min_stock","product_type"]],on="id",how="left")
        perf["margin_pct"]=np.where(perf["revenue90"]>0,perf["profit90"]/perf["revenue90"]*100,0)
        median_vel=perf.units90.median() if not perf.empty else 0
        median_margin=perf.margin_pct[perf.revenue90>0].median() if (perf.revenue90>0).any() else TARGET_MARGIN
        perf["class"]=np.select(
            [
                (perf.units90>=median_vel)&(perf.margin_pct>=median_margin),
                (perf.units90>=median_vel)&(perf.margin_pct<median_margin),
                (perf.units90<median_vel)&(perf.margin_pct>=median_margin)&(perf.units90>0),
            ],
            ["ESTRELLA","VOLUMEN","NICHO"],
            default="LIQUIDAR / REVISAR"
        )

    st.markdown("### Qué hacer hoy")
    actions=[]
    if not inv.empty:
        low=inv[(inv.stock<=inv.min_stock)&(inv.active==1)&(inv.sellable==1)]
        for _,r in low.head(8).iterrows():
            actions.append(("REPOSICIÓN",f"{r.brand} {r['name']}: stock {r.stock:g}, mínimo {r.min_stock:g}."))
        dead_ids=set(perf[(perf.units90<=0)&(perf.stock>0)].id.tolist()) if not perf.empty else set()
        for _,r in inv[inv.id.isin(dead_ids)].sort_values("avg_cost",ascending=False).head(5).iterrows():
            actions.append(("CAPITAL INMOVILIZADO",f"{r.brand} {r['name']}: {r.stock:g} unidades sin ventas en 90 días, {money(r.stock*r.avg_cost)} a costo."))
    recv=safe_float(scalar("SELECT COALESCE(SUM(debit-credit),0) FROM account_ledger WHERE entity_type='CUSTOMER'",default=0))
    if recv>0:
        actions.append(("COBRANZA",f"Hay {money(recv)} pendientes de cobrar."))
    month_start=date.today().replace(day=1)
    month_end=date.today()+timedelta(days=1)
    ms=period_sales(month_start,month_end)
    mm=(ms.profit.sum()/ms.total.sum()*100) if (not ms.empty and ms.total.sum()) else 0
    if mm and mm<TARGET_MARGIN:
        actions.append(("MARGEN",f"El margen mensual está en {mm:.1f}%, por debajo de la meta de {TARGET_MARGIN:.1f}%."))

    if not actions:
        st.success("No detecté alertas operativas críticas. Podés concentrarte en crecimiento y adquisición.")
    else:
        for kind,text in actions[:15]:
            st.markdown(f"**{kind}** — {text}")

    st.divider()
    st.markdown("### Matriz de portafolio")
    if inv.empty:
        st.info("Sin datos.")
    else:
        st.dataframe(perf[["brand","name","stock","units90","revenue90","profit90","margin_pct","class"]].sort_values(["class","profit90"],ascending=[True,False]),use_container_width=True,hide_index=True)

    st.divider()
    st.markdown("### Preguntale al analista local")
    question=st.text_input("Pregunta",placeholder="Ej.: qué stock tengo clavado / qué productos venden más / cuánto tengo por cobrar")
    if question:
        q=question.lower()
        if "clavad" in q or "inmov" in q or "sin venta" in q:
            dead=perf[(perf.units90<=0)&(perf.stock>0)].copy() if not perf.empty else pd.DataFrame()
            if dead.empty:
                st.success("No encontré stock sin ventas en los últimos 90 días.")
            else:
                dead["capital"]=dead.stock*dead.avg_cost
                st.write(f"Hay {money(dead.capital.sum())} a costo en productos sin ventas en 90 días.")
                st.dataframe(dead[["brand","name","stock","capital"]].sort_values("capital",ascending=False),use_container_width=True,hide_index=True)
        elif "por cobrar" in q or "deben" in q:
            st.write(f"Saldo total pendiente de clientes: **{money(recv)}**.")
        elif "vende" in q or "top" in q or "mejor" in q:
            top=perf.sort_values("profit90",ascending=False).head(10)
            st.dataframe(top[["brand","name","units90","revenue90","profit90","margin_pct"]],use_container_width=True,hide_index=True)
        elif "reponer" in q or "comprar" in q:
            low=inv[(inv.stock<=inv.min_stock)&(inv.active==1)]
            if low.empty:
                st.success("No hay productos por debajo del mínimo configurado.")
            else:
                st.dataframe(low[["brand","name","stock","min_stock","avg_cost"]],use_container_width=True,hide_index=True)
        elif "margen" in q:
            st.write(f"Margen del mes actual: **{mm:.1f}%**. Meta configurada: **{TARGET_MARGIN:.1f}%**.")
        else:
            st.info("Puedo resolver consultas sobre ventas, productos top, reposición, margen, stock inmovilizado y cuentas por cobrar. Para análisis libres, usá los módulos de Reportes y Centro Ejecutivo.")

# ============================================================
# PAGE: REPORTS
# ============================================================
elif page == "▥ Reportes":
    hero("Reportes", "Análisis comercial, rentabilidad, marcas, canales, clientes, vendedores y exportación.")
    start=st.date_input("Desde",value=date.today().replace(day=1),key="rep_start")
    end=st.date_input("Hasta",value=date.today(),key="rep_end")
    end_ex=end+timedelta(days=1)
    sales=period_sales(start,end_ex)
    if sales.empty:
        st.info("Sin ventas en el rango.")
    else:
        a,b,c,d=st.columns(4)
        a.metric("Ventas",money(sales.total.sum()))
        b.metric("Ganancia",money(sales.profit.sum()))
        c.metric("Margen",pct(sales.profit.sum()/sales.total.sum()*100 if sales.total.sum() else 0))
        d.metric("Tickets",len(sales))
        tabs=st.tabs(["Productos","Marcas","Canales","Clientes","Vendedores","Detalle"])
        items=qdf(
            """SELECT s.date,s.id sale_id,p.brand,p.name,p.size_ml,p.gender,p.category,p.product_type,
                      si.qty,si.unit_price,si.unit_cost,si.subtotal,
                      (si.unit_price-si.unit_cost)*si.qty item_profit,
                      s.channel,s.payment_method,s.customer_id,s.vendor_id
               FROM sale_items si JOIN sales s ON s.id=si.sale_id JOIN products p ON p.id=si.product_id
               WHERE s.date>=? AND s.date<? AND s.status='Completada'""",(str(start),str(end_ex))
        )
        with tabs[0]:
            x=items.groupby(["brand","name","size_ml"],as_index=False).agg(unidades=("qty","sum"),facturacion=("subtotal","sum"),ganancia=("item_profit","sum"))
            st.dataframe(x.sort_values("ganancia",ascending=False),use_container_width=True,hide_index=True)
        with tabs[1]:
            x=items.groupby("brand",as_index=False).agg(unidades=("qty","sum"),facturacion=("subtotal","sum"),ganancia=("item_profit","sum"))
            st.dataframe(x.sort_values("ganancia",ascending=False),use_container_width=True,hide_index=True)
        with tabs[2]:
            x=sales.groupby("channel",as_index=False).agg(ventas=("id","count"),facturacion=("total","sum"),ganancia=("profit","sum"))
            st.dataframe(x.sort_values("facturacion",ascending=False),use_container_width=True,hide_index=True)
        with tabs[3]:
            x=sales.groupby(sales.customer_name.fillna("Consumidor final"),as_index=False).agg(ventas=("id","count"),facturacion=("total","sum"),ganancia=("profit","sum"))
            st.dataframe(x.sort_values("facturacion",ascending=False),use_container_width=True,hide_index=True)
        with tabs[4]:
            x=sales.groupby(sales.vendor_name.fillna("Sin vendedor"),as_index=False).agg(ventas=("id","count"),facturacion=("total","sum"),ganancia=("profit","sum"))
            st.dataframe(x.sort_values("facturacion",ascending=False),use_container_width=True,hide_index=True)
        with tabs[5]:
            st.dataframe(sales,use_container_width=True,hide_index=True)

# ============================================================
# PAGE: SETTINGS
# ============================================================
elif page == "⚙ Configuración":
    hero("Configuración", "Negocio, márgenes, seguridad, usuarios, backup y herramientas administrativas.")
    t1,t2,t3,t4=st.tabs(["Negocio","Usuarios","Backup","Diagnóstico"])

    with t1:
        with st.form("settings_form"):
            business=st.text_input("Nombre del negocio",value=get_setting("business_name","Mi Perfumería"))
            goal=st.number_input("Objetivo mensual",min_value=0.0,value=safe_float(get_setting("monthly_goal","0")),step=1000.0)
            margin=st.number_input("Margen objetivo %",min_value=0.0,max_value=100.0,value=safe_float(get_setting("target_margin","35")),step=0.5)
            login=st.checkbox("Activar login",value=get_setting("login_enabled","0")=="1")
            save=st.form_submit_button("Guardar configuración",type="primary")
        if save:
            set_setting("business_name",business)
            set_setting("monthly_goal",goal)
            set_setting("target_margin",margin)
            set_setting("login_enabled","1" if login else "0")
            st.success("Configuración guardada.")
            st.rerun()

        st.markdown("### Motor de precios")
        cost=st.number_input("Costo real",min_value=0.0,value=25000.0,step=100.0)
        desired=st.number_input("Margen deseado %",min_value=0.0,max_value=95.0,value=TARGET_MARGIN,step=0.5)
        price=cost/(1-desired/100) if desired<100 else 0
        st.metric("Precio mínimo sugerido",money(price))
        variants=pd.DataFrame({"Precio":[price*.9,price,price*1.1]})
        variants["Ganancia"]=variants.Precio-cost
        variants["Margen %"]=np.where(variants.Precio>0,variants.Ganancia/variants.Precio*100,0)
        st.dataframe(variants,use_container_width=True,hide_index=True)

    with t2:
        users=qdf("SELECT id,username,full_name,role,active,created_at FROM users ORDER BY id")
        st.dataframe(users,use_container_width=True,hide_index=True)
        with st.form("new_user",clear_on_submit=True):
            a,b,c=st.columns(3)
            username=a.text_input("Usuario")
            fullname=b.text_input("Nombre")
            role=c.selectbox("Rol",["Admin","Encargado","Vendedor","Consulta"])
            password=st.text_input("Contraseña",type="password")
            done=st.form_submit_button("Crear usuario",type="primary")
        if done and username and password:
            try:
                execute("INSERT INTO users(username,password_hash,full_name,role,active,created_at) VALUES(?,?,?,?,?,?)",
                        (username,hash_password(password),fullname,role,1,now_iso()))
                st.success("Usuario creado.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("El usuario ya existe.")
        st.caption("Usuario inicial: admin / admin. Si activás el login, cambiá esa contraseña creando un usuario propio y luego desactivando el inicial.")

    with t3:
        backup=export_backup_zip()
        st.download_button(
            "Descargar backup completo CSV (.zip)",
            data=backup,
            file_name=f"perfume_os_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
            use_container_width=True,
        )
        st.info("Google Sheets es la única base persistente. El archivo Parfum contiene toda la información; el .py no crea ninguna base de datos local.")

    with t4:
        tables=["products","inventory_moves","sales","sale_items","purchases","customers","suppliers","vendors","cash_moves","expenses"]
        rows=[]
        for t in tables:
            rows.append({"Tabla":t,"Registros":safe_int(scalar(f"SELECT COUNT(*) FROM {t}",default=0))})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        try:
            _diag_sheet = st.secrets.get("GOOGLE_SHEET_ID", st.secrets.get("google_sheet_id", SPREADSHEET_NAME))
        except Exception:
            _diag_sheet = SPREADSHEET_NAME
        st.code(f"Google Sheet: {_diag_sheet}\nVersión: {APP_VERSION}\nPersistencia: Google Sheets\nFecha: {now_iso()}")
        if st.button("Sincronizar ahora desde Google Sheets"):
            reload_from_sheets()
            st.success("Datos recargados desde Parfum.")
            st.rerun()

# -----------------------------
# FOOTER
# -----------------------------
st.divider()
try:
    _footer_sheet = st.secrets.get("GOOGLE_SHEET_ID", st.secrets.get("google_sheet_id", SPREADSHEET_NAME))
except Exception:
    _footer_sheet = SPREADSHEET_NAME
st.caption(f"{APP_NAME} · v{APP_VERSION} · {BUSINESS_NAME} · Google Sheets · caché anti-cuota activa")
