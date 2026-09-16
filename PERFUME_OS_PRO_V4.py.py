
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
import unicodedata
import math
import difflib
from collections import defaultdict, deque
from pathlib import Path
from datetime import datetime, date, timedelta

try:
    import plotly.express as px
    import plotly.graph_objects as go
except Exception:
    px = None
    go = None

try:
    import qrcode
    from PIL import Image
except Exception:
    qrcode = None
    Image = None

try:
    import cv2
except Exception:
    cv2 = None

try:
    from pyzbar.pyzbar import decode as zbar_decode
except Exception:
    zbar_decode = None

try:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
except Exception:
    rl_canvas = None
    A4 = None
    ImageReader = None

# ============================================================
# PERFUME OS
# Sistema operativo integral para negocio de perfumería
# Un solo archivo Streamlit + Google Sheets como única persistencia
# ============================================================

APP_NAME = "PERFUME 35 OS"
APP_VERSION = "8.1.0-FLEX-SHEETS"
FIXED_SIZE_ML = 35.0

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
# LUXURY UI OVERRIDES
# -----------------------------
st.markdown(
    """
    <style>
    :root{
        --lux-bg:#f5f1eb;
        --lux-card:#fffdf9;
        --lux-ink:#17151a;
        --lux-muted:#786f79;
        --lux-line:#e8dfd4;
        --lux-gold:#b88945;
        --lux-gold2:#d5b071;
        --lux-plum:#56354f;
        --lux-rose:#9b5365;
        --lux-green:#2f765a;
        --lux-red:#ad4a4a;
        --lux-blue:#486a8a;
    }
    .stApp{
        background:
          radial-gradient(circle at 92% 0%, rgba(184,137,69,.08), transparent 28rem),
          linear-gradient(180deg,#f8f5f0 0%,#f4f0ea 100%) !important;
    }
    .block-container{max-width:1680px!important;padding-top:1.4rem!important}
    section[data-testid="stSidebar"]{
        background:linear-gradient(180deg,#1d1920 0%,#262029 58%,#171419 100%)!important;
        border-right:1px solid rgba(255,255,255,.06)!important;
    }
    section[data-testid="stSidebar"] *{color:#f6f0e8!important}
    section[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.11)!important}
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{color:#bdb1bb!important}
    section[data-testid="stSidebar"] div[role="radiogroup"] label{
        border-radius:12px!important;padding:.36rem .55rem!important;margin:.08rem 0!important;
        transition:.15s ease!important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{
        background:rgba(213,176,113,.11)!important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
        background:linear-gradient(90deg,rgba(184,137,69,.25),rgba(155,83,101,.13))!important;
        box-shadow:inset 3px 0 0 #d5b071!important;
    }
    .hero{
        position:relative;overflow:hidden;
        background:
          radial-gradient(circle at 88% 15%,rgba(213,176,113,.28),transparent 22rem),
          linear-gradient(125deg,#17151a 0%,#352630 55%,#58384d 100%)!important;
        border:1px solid rgba(255,255,255,.08)!important;
        border-radius:28px!important;
        padding:30px 34px!important;
        box-shadow:0 22px 70px rgba(37,25,35,.18)!important;
    }
    .hero:after{
        content:"";position:absolute;width:190px;height:190px;border-radius:50%;
        border:1px solid rgba(213,176,113,.22);right:-40px;top:-70px;
    }
    .hero .eyebrow{color:#e6c68f!important;font-weight:700!important}
    .hero h1{font-size:2.25rem!important;line-height:1.05!important}
    [data-testid="stMetric"]{
        background:linear-gradient(145deg,#fffefb,#fbf6ef)!important;
        border:1px solid #e8ded2!important;border-radius:20px!important;
        box-shadow:0 10px 32px rgba(58,42,50,.065)!important;
        position:relative;overflow:hidden;
    }
    [data-testid="stMetric"]:before{
        content:"";position:absolute;left:0;top:0;width:100%;height:3px;
        background:linear-gradient(90deg,#b88945,#9b5365,#56354f);
    }
    [data-testid="stMetricValue"]{
        font-weight:800!important;
        letter-spacing:-.035em!important;
        font-size:1.52rem!important;
        line-height:1.08!important;
    }
    [data-testid="stMetricValue"] *{
        font-size:inherit!important;
        line-height:inherit!important;
    }
    @media (max-width:1200px){
        [data-testid="stMetricValue"]{font-size:1.38rem!important;}
    }
    div[data-testid="stDataFrame"]{
        border:1px solid #e7ddd1!important;border-radius:18px!important;
        box-shadow:0 8px 28px rgba(45,31,40,.045)!important;
    }
    .stTabs [data-baseweb="tab-list"]{
        gap:.45rem;background:#eee7df;padding:.35rem;border-radius:15px;
    }
    .stTabs [data-baseweb="tab"]{
        border-radius:11px;padding:.55rem .9rem!important;
    }
    .stTabs [aria-selected="true"]{
        background:#fffaf4!important;box-shadow:0 2px 10px rgba(58,42,50,.08)!important;
        color:#56354f!important;
    }
    .stButton button[kind="primary"]{
        background:linear-gradient(100deg,#5d354f,#8f5063)!important;
        border:0!important;box-shadow:0 7px 18px rgba(94,53,79,.22)!important;
    }
    .stButton button[kind="primary"]:hover{
        transform:translateY(-1px);filter:brightness(1.04);
    }
    .stDownloadButton button{
        background:#fffaf4!important;border:1px solid #dccdbd!important;
    }
    div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input,
    .stDateInput input, .stTextArea textarea{
        background:#fffdf9!important;border-color:#e4d9cc!important;
    }
    .pro-card{
        background:linear-gradient(145deg,#fffefb,#fbf6ef);
        border:1px solid #e8ded2;border-radius:20px;padding:18px 20px;
        box-shadow:0 9px 28px rgba(55,38,48,.055);height:100%;
    }
    .pro-card .label{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:#8b7c83;font-weight:700}
    .pro-card .value{font-size:1.55rem;font-weight:850;letter-spacing:-.035em;color:#211b22;margin:.15rem 0}
    .pro-card .sub{font-size:.82rem;color:#837780}
    /* Centro Ejecutivo: tarjetas legibles sin truncar en desktop y tablet */
    .pro-card .label{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;line-height:1.2!important;}
    .pro-card .value{white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;}
    @media (max-width:1250px){
        .pro-card{padding:15px 16px!important;}
        .pro-card .value{font-size:1.34rem!important;}
        .pro-card .label{font-size:.68rem!important;}
        .pro-card .sub{font-size:.77rem!important;}
    }
    .sale-ticket{
        background:linear-gradient(145deg,#fffdf9,#f7f0e8);
        border:1px solid #dfd2c3;border-radius:22px;padding:22px 24px;
        box-shadow:0 10px 32px rgba(57,40,49,.07);
    }
    .sale-ticket .ticket-id{font-size:.76rem;letter-spacing:.14em;color:#9b5365;font-weight:800}
    .sale-ticket .ticket-title{font-size:1.6rem;font-weight:850;color:#221b22;margin:.2rem 0}
    .sale-ticket .ticket-meta{color:#776d75;font-size:.88rem}
    .badge{
        display:inline-flex;align-items:center;padding:5px 10px;border-radius:999px;
        font-size:.74rem;font-weight:800;letter-spacing:.02em;margin-right:5px;
    }
    .badge-good{background:#e7f3ec;color:#2f765a}
    .badge-warn{background:#f7edda;color:#936a28}
    .badge-bad{background:#f6e5e5;color:#a74747}
    .badge-plum{background:#eee4eb;color:#6c405e}
    .insight{
        border-left:4px solid #b88945;background:#fff9f1;border-radius:0 16px 16px 0;
        padding:13px 16px;margin:.35rem 0;color:#463943;
    }
    .section-title{
        font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;
        color:#9b5365;font-weight:800;margin-bottom:.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# 35 ML POLISHED RESPONSIVE LAYER
# -----------------------------
st.markdown(
    """
    <style>
    /* Sidebar nativo: NO fijar ancho/min-width.
       Streamlit puede así devolver todo ese espacio al contenido al cerrarlo. */
    section[data-testid="stSidebar"]{
        transition: transform .22s ease, width .22s ease!important;
    }
    .block-container{
        width:100%!important;
        max-width:1680px!important;
        padding-left:2rem!important;
        padding-right:2rem!important;
        transition:padding .22s ease!important;
    }
    /* Tipografía y jerarquía más limpia */
    html, body, [class*="css"]{font-feature-settings:"tnum" 1,"ss01" 1;}
    .hero h1{font-weight:850!important;letter-spacing:-.04em!important;}
    .hero p{font-size:.98rem!important;line-height:1.55!important;}
    /* Métricas nativas: títulos y cifras nunca deben terminar en puntos suspensivos */
    [data-testid="stMetric"]{min-width:0!important;}
    [data-testid="stMetricLabel"] p{
        white-space:normal!important;overflow:visible!important;text-overflow:clip!important;
        line-height:1.15!important;
    }
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] *{
        white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;
    }
    /* Editores de datos con aspecto de aplicación de gestión */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"]{
        box-shadow:0 12px 38px rgba(49,34,44,.055)!important;
    }
    .edit-callout{
        background:linear-gradient(135deg,#fffdf9,#f7efe7);
        border:1px solid #e5d9cd;border-radius:18px;padding:14px 16px;
        color:#5c5058;margin:.4rem 0 1rem 0;
    }
    .edit-callout b{color:#342831;}
    .soft-title{
        font-size:.78rem;text-transform:uppercase;letter-spacing:.12em;
        color:#8b596d;font-weight:850;margin:.2rem 0 .55rem;
    }
    .command-banner{
        border:1px solid #e6d9ce;border-radius:24px;padding:18px 20px;margin:.4rem 0 1rem;
        background:
          radial-gradient(circle at 92% 12%,rgba(184,137,69,.12),transparent 30%),
          linear-gradient(135deg,#fffdf9,#f7f0ea);
        box-shadow:0 14px 45px rgba(54,36,46,.055);
    }
    .command-banner .status{font-size:.72rem;text-transform:uppercase;letter-spacing:.13em;font-weight:900;color:#8b596d}
    .command-banner .headline{font-size:1.45rem;font-weight:900;color:#241d23;margin:.15rem 0}
    .command-banner .detail{font-size:.88rem;color:#746a72;line-height:1.5}
    .health-ring{
        width:112px;height:112px;border-radius:50%;display:flex;align-items:center;justify-content:center;
        margin:auto;font-size:1.8rem;font-weight:900;color:#271f25;
        background:conic-gradient(#2f765a var(--health),#eee4e6 0);
        position:relative;
    }
    .health-ring:before{
        content:"";position:absolute;width:82px;height:82px;border-radius:50%;
        background:#fffaf7;
    }
    .health-ring span{position:relative;z-index:2}
    .magic-card{
        background:linear-gradient(145deg,#fffefa,#f8f1ea);
        border:1px solid #e7dbd0;border-radius:20px;padding:16px 17px;height:100%;
        box-shadow:0 10px 32px rgba(56,38,48,.045);
    }
    .magic-card .m-label{font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:#8a7b83;font-weight:800}
    .magic-card .m-value{font-size:1.32rem;font-weight:900;color:#251e24;margin:.22rem 0}
    .magic-card .m-sub{font-size:.78rem;color:#847780;line-height:1.38}
    .family-chip{
        display:inline-block;padding:5px 9px;border-radius:999px;margin:2px 3px 2px 0;
        font-size:.72rem;font-weight:800;border:1px solid rgba(0,0,0,.06);
    }
    .shelf{
        display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;
        padding:10px 0;
    }
    .shelf-item{
        min-height:118px;border:1px solid #e5d9cf;border-radius:17px;padding:13px;
        background:linear-gradient(180deg,#fffefa,#f9f3ed);
        box-shadow:0 8px 22px rgba(45,31,39,.035);
    }
    .shelf-item .nm{font-weight:850;font-size:.9rem;color:#2a2127;line-height:1.25}
    .shelf-item .ref{font-size:.72rem;color:#887b82;margin-top:4px;min-height:32px}
    .shelf-item .qty{font-size:1.3rem;font-weight:900;color:#56354f;margin-top:8px}
    .alert-row{
        border-left:4px solid #b88945;background:#fffaf4;padding:11px 13px;border-radius:0 14px 14px 0;
        margin:.38rem 0;font-size:.86rem;color:#4c4047;
    }
    .alert-row.bad{border-left-color:#a74747;background:#fff4f4}
    .alert-row.good{border-left-color:#2f765a;background:#f2faf6}
    .action-card{
        border:1px solid #e6dad0;border-radius:18px;padding:14px 15px;margin:.35rem 0;
        background:#fffdf9;
    }
    .action-card b{color:#3c2b35}
    @media (max-width:1200px){
        .block-container{padding-left:1.25rem!important;padding-right:1.25rem!important;}
        [data-testid="stMetricValue"]{font-size:1.26rem!important;}
    }
    @media (max-width:850px){
        .block-container{padding-left:.8rem!important;padding-right:.8rem!important;}
    }
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
    "customer_preferences": "preferencias_clientes",
    "demand_requests": "demanda_no_cubierta",
    "audit_log": "auditoria",
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
            reference_house TEXT,
            reference_name TEXT,
            inspired_house TEXT,
            inspired_name TEXT,
            similarity_relation TEXT,
            similarity_confidence TEXT,
            fragrance_profile TEXT,
            priority TEXT,
            aliases TEXT,
            library_key TEXT,
            library_item INTEGER DEFAULT 0,
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

        CREATE TABLE IF NOT EXISTS customer_preferences(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            customer_id INTEGER,
            preference_type TEXT,
            value TEXT,
            weight REAL DEFAULT 1,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS demand_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            customer_id INTEGER,
            requested_text TEXT NOT NULL,
            matched_product_id INTEGER,
            status TEXT DEFAULT 'Pendiente',
            channel TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(matched_product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS audit_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            user_name TEXT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            before_json TEXT,
            after_json TEXT,
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
        return "Google alcanzó temporalmente la cuota. Backend BATCH v3.0 reduce la carga inicial a una sola lectura masiva. Esperá un minuto y reintentá."
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
          <p>PERFUME OS prueba cada capa por separado para identificar el punto exacto de falla. Backend BATCH v3.0.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if original_error is not None:
        st.error(f"Error que detuvo el inicio: {type(original_error).__name__}: {original_error}")

    with st.spinner("Ejecutando diagnóstico profundo de Google Sheets..."):
        results = run_google_sheets_diagnostic(deep_write_test=False)

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
        "worksheet_cache": {},
        "structure_ready": False,
        # None = pestaña sin encabezado todavía. Una lista = columnas que el usuario
        # decidió conservar actualmente en Google Sheets. Esto permite borrar
        # columnas opcionales sin que PERFUME OS deje de iniciar ni las recree
        # automáticamente en cada guardado.
        "sheet_headers": {},
        "sheet_schema_warnings": [],
    }


def get_conn():
    return get_backend()["conn"]


def _sheet_range(title, end_col="AZ"):
    safe = str(title).replace("'", "''")
    return f"'{safe}'!A1:{end_col}"


def _refresh_worksheet_cache():
    """
    ONE metadata request for every worksheet in the spreadsheet.
    """
    backend = get_backend()
    worksheets = backend["spreadsheet"].worksheets()
    backend["worksheet_cache"] = {ws.title: ws for ws in worksheets}
    return backend["worksheet_cache"]


def table_columns(table):
    return [r[1] for r in get_conn().execute(f"PRAGMA table_info({table})").fetchall()]


def _table_column_meta(table):
    """Metadata SQLite usada para tolerar Sheets con columnas eliminadas."""
    out = {}
    for r in get_conn().execute(f"PRAGMA table_info({table})").fetchall():
        out[str(r[1])] = {
            "type": str(r[2] or "TEXT").upper(),
            "notnull": bool(r[3]),
            "default": r[4],
            "pk": bool(r[5]),
        }
    return out


def _normalize_header_name(value):
    """Normaliza espacios/mayúsculas sin exigir que el Sheet sea idéntico al schema."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text


def _canonical_sheet_header(table, raw_header):
    """Devuelve columnas reales del schema que siguen existiendo en el Sheet, en su orden."""
    cols = table_columns(table)
    by_norm = {_normalize_header_name(c): c for c in cols}
    found = []
    seen = set()
    for raw in raw_header or []:
        key = _normalize_header_name(raw)
        col = by_norm.get(key)
        if col and col not in seen:
            found.append(col)
            seen.add(col)
    return found


def _parse_sqlite_default(raw):
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return raw
    txt = str(raw).strip()
    if len(txt) >= 2 and txt[0] == txt[-1] and txt[0] in ("'", '"'):
        return txt[1:-1].replace("''", "'")
    if txt.upper() == "NULL":
        return None
    try:
        return float(txt) if "." in txt else int(txt)
    except Exception:
        return txt


def _required_missing_value(table, col, meta, row_number):
    """
    Última red de seguridad para columnas NOT NULL borradas del Sheet.
    El objetivo es que una columna opcional/accidentalmente eliminada nunca tumbe
    toda la app. Los valores técnicos faltantes se regeneran sólo en memoria.
    """
    default = _parse_sqlite_default(meta.get("default"))
    if default is not None:
        return default

    c = str(col).lower()
    ctype = str(meta.get("type") or "TEXT").upper()

    if c == "created_at":
        return now_iso()
    if c == "date":
        return today_iso()
    if c == "username":
        return f"AUTO_USER_{row_number}"
    if c == "password_hash":
        # No inventamos una contraseña utilizable para usuarios importados dañados.
        return hash_password(uid("LOCKED_"))
    if c == "sku":
        return f"AUTO-{table.upper()}-{row_number}-{uuid.uuid4().hex[:6].upper()}"
    if c in {"name", "action", "requested_text", "entity_type", "direction", "category", "move_type"}:
        return "(sin dato)"
    if any(token in ctype for token in ("INT", "REAL", "FLOA", "DOUB", "NUM")):
        return 0
    return ""


def _sheet_target_columns(table):
    """
    Columnas que PERFUME OS debe escribir de vuelta.
    Si el usuario borró columnas de una pestaña existente, se respeta esa decisión.
    Si la pestaña todavía no tenía encabezado, se inicializa con el schema completo.
    """
    backend = get_backend()
    all_cols = table_columns(table)
    remembered = backend.get("sheet_headers", {}).get(table, None)
    if remembered is None:
        return all_cols
    return [c for c in remembered if c in all_cols]


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


def _worksheet_for_table(table):
    """
    Uses cached metadata. Never treats quota/permission errors as 'sheet missing'.
    """
    backend = get_backend()
    title = SHEET_NAMES[table]
    cache = backend.get("worksheet_cache") or _refresh_worksheet_cache()

    if title in cache:
        return cache[title]

    # If this path is reached, genuinely missing sheet. Create only this one.
    cols = table_columns(table)
    try:
        ws = backend["spreadsheet"].add_worksheet(
            title=title,
            rows=1000,
            cols=max(30, len(cols) + 3),
        )
        backend["worksheet_cache"][title] = ws
        # One header write.
        backend["spreadsheet"].values_update(
            _sheet_range(title, "AZ"),
            params={"valueInputOption": "RAW"},
            body={"values": [cols]},
        )
        backend.setdefault("sheet_headers", {})[table] = list(cols)
        return ws
    except Exception as e:
        if "already exists" in str(e).lower():
            cache = _refresh_worksheet_cache()
            if title in cache:
                return cache[title]
        raise


def ensure_sheet_structure():
    """
    Creates ALL missing worksheets in one Google Sheets batchUpdate request.
    Writes ALL new headers in one values.batchUpdate request.
    """
    backend = get_backend()
    with backend["lock"]:
        if backend.get("structure_ready", False):
            return

        cache = _refresh_worksheet_cache()
        missing = [t for t in TABLE_ORDER if SHEET_NAMES[t] not in cache]

        if missing:
            requests = []
            for table in missing:
                cols = table_columns(table)
                requests.append({
                    "addSheet": {
                        "properties": {
                            "title": SHEET_NAMES[table],
                            "gridProperties": {
                                "rowCount": 1000,
                                "columnCount": max(30, len(cols) + 3),
                            },
                        }
                    }
                })

            try:
                backend["spreadsheet"].batch_update({"requests": requests})
            except Exception as e:
                # A concurrent instance may have created one or more tabs already.
                # Refresh once; if all expected tabs now exist, continue.
                if "already exists" not in str(e).lower():
                    raise

            cache = _refresh_worksheet_cache()

            still_missing = [t for t in TABLE_ORDER if SHEET_NAMES[t] not in cache]
            if still_missing:
                raise RuntimeError(
                    "Google no creó todas las pestañas requeridas: "
                    + ", ".join(SHEET_NAMES[t] for t in still_missing)
                )

            data = []
            for table in missing:
                title = SHEET_NAMES[table]
                cols = table_columns(table)
                data.append({
                    "range": _sheet_range(title, "AZ"),
                    "majorDimension": "ROWS",
                    "values": [cols],
                })
            if data:
                backend["spreadsheet"].values_batch_update({
                    "valueInputOption": "RAW",
                    "data": data,
                })
            for table in missing:
                backend.setdefault("sheet_headers", {})[table] = list(table_columns(table))

        backend["structure_ready"] = True


def _insert_sheet_values_into_table(table, values):
    """
    Carga una matriz ya leída desde Google Sheets al cache SQLite en memoria.

    Importante: el Sheet es de esquema FLEXIBLE. Si el usuario borró una columna,
    la app sigue iniciando. Las columnas presentes se leen por nombre y las columnas
    NOT NULL que falten reciben un valor técnico seguro sólo en memoria.
    """
    conn = get_conn()
    cols = table_columns(table)
    meta = _table_column_meta(table)
    conn.execute(f"DELETE FROM {table}")

    if not values:
        return

    raw_header = [str(x).strip() for x in (values[0] or [])]
    recognized = _canonical_sheet_header(table, raw_header)

    # Tablas internas: si sus columnas clave fueron borradas, preferimos regenerar
    # defaults locales antes que bloquear el acceso a toda la aplicación.
    if table == "settings" and not {"key", "value"}.issubset(set(recognized)):
        get_backend().setdefault("sheet_schema_warnings", []).append(
            "configuracion: faltan key/value; se usaron defaults locales"
        )
        return
    if table == "users" and not {"username", "password_hash"}.issubset(set(recognized)):
        get_backend().setdefault("sheet_schema_warnings", []).append(
            "usuarios: faltan username/password_hash; se regeneró el usuario local por defecto"
        )
        return

    if len(values) <= 1:
        return

    # Mapeo robusto: tolera mayúsculas, espacios y columnas eliminadas/intermedias.
    norm_positions = {}
    for i, raw in enumerate(raw_header):
        key = _normalize_header_name(raw)
        if key and key not in norm_positions:
            norm_positions[key] = i
    col_positions = {}
    for c in cols:
        pos = norm_positions.get(_normalize_header_name(c))
        if pos is not None:
            col_positions[c] = pos

    # Usamos todas las columnas existentes + sólo las NOT NULL sin default que
    # fueron borradas. Los INTEGER PRIMARY KEY ausentes se dejan autogenerar.
    insert_cols = list(recognized)
    for c in cols:
        m = meta.get(c, {})
        if c in insert_cols:
            continue
        if m.get("pk") and "INT" in str(m.get("type", "")).upper():
            continue
        if m.get("notnull") and m.get("default") is None:
            insert_cols.append(c)

    if not insert_cols:
        return

    placeholders = ",".join(["?"] * len(insert_cols))
    sql = f"INSERT INTO {table} ({','.join(insert_cols)}) VALUES ({placeholders})"

    rows = []
    skipped = 0
    for row_number, raw in enumerate(values[1:], start=2):
        if not any(str(x).strip() for x in raw):
            continue

        row = []
        for c in insert_cols:
            m = meta.get(c, {})
            idx = col_positions.get(c)
            present = idx is not None and idx < len(raw)
            val = raw[idx] if present else None

            if val == "":
                val = None

            if val is None and m.get("notnull"):
                val = _required_missing_value(table, c, m, row_number)

            row.append(val)

        try:
            conn.execute(sql, tuple(row))
        except sqlite3.IntegrityError as e:
            # Una fila dañada no debe impedir entrar a toda la app. Reintentamos
            # una vez sustituyendo campos obligatorios/únicos típicos.
            patched = list(row)
            for i, c in enumerate(insert_cols):
                m = meta.get(c, {})
                if patched[i] is None and m.get("notnull"):
                    patched[i] = _required_missing_value(table, c, m, row_number)
                if c == "sku" and not str(patched[i] or "").strip():
                    patched[i] = f"AUTO-{table.upper()}-{row_number}-{uuid.uuid4().hex[:6].upper()}"
                if c == "username" and not str(patched[i] or "").strip():
                    patched[i] = f"AUTO_USER_{row_number}_{uuid.uuid4().hex[:4]}"
            try:
                conn.execute(sql, tuple(patched))
            except Exception:
                skipped += 1
                get_backend().setdefault("sheet_schema_warnings", []).append(
                    f"{SHEET_NAMES.get(table, table)}: fila {row_number} omitida por datos incompatibles ({type(e).__name__})"
                )
        except Exception as e:
            skipped += 1
            get_backend().setdefault("sheet_schema_warnings", []).append(
                f"{SHEET_NAMES.get(table, table)}: fila {row_number} omitida ({type(e).__name__})"
            )

    if skipped:
        # No hacemos st.warning aquí porque esta función corre durante el arranque.
        # El warning queda disponible para diagnóstico/configuración sin bloquear.
        pass


def _batch_read_all_tables():
    """
    Reads ALL business tables from Google Sheets with ONE Sheets API batchGet request.
    This is the key anti-quota change.
    """
    backend = get_backend()
    ranges = [_sheet_range(SHEET_NAMES[t], "AZ") for t in TABLE_ORDER]

    response = backend["spreadsheet"].values_batch_get(
        ranges,
        params={
            "majorDimension": "ROWS",
            "valueRenderOption": "UNFORMATTED_VALUE",
        },
    )

    value_ranges = response.get("valueRanges", [])
    matrices = {}

    # Google returns valueRanges in request order.
    header_state = backend.setdefault("sheet_headers", {})
    for idx, table in enumerate(TABLE_ORDER):
        vr = value_ranges[idx] if idx < len(value_ranges) else {}
        matrix = vr.get("values", [])
        matrices[table] = matrix
        if matrix and len(matrix) >= 1:
            # Lista vacía = había encabezado, pero ninguna columna reconocida.
            # None = pestaña verdaderamente vacía/sin encabezado.
            header_state[table] = _canonical_sheet_header(table, matrix[0])
        else:
            header_state.setdefault(table, None)

    return matrices


def reload_from_sheets():
    """
    Full refresh = ONE batchGet request instead of 18+ separate reads.
    """
    backend = get_backend()
    conn = get_conn()

    with backend["lock"]:
        backend["sync_enabled"] = False
        matrices = _batch_read_all_tables()

        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            for table in reversed(TABLE_ORDER):
                conn.execute(f"DELETE FROM {table}")
            for table in TABLE_ORDER:
                _insert_sheet_values_into_table(table, matrices.get(table, []))
            conn.commit()
        finally:
            conn.execute("PRAGMA foreign_keys = ON")

        # Detect which sheets were originally empty BEFORE default seeding.
        settings_empty = not matrices.get("settings") or len(matrices.get("settings", [])) <= 1
        users_empty = not matrices.get("users") or len(matrices.get("users", [])) <= 1

        defaults = {
            "business_name": "Mi Perfumería",
            "currency": "ARS",
            "login_enabled": "0",
            "monthly_goal": "0",
            "target_margin": "35",
            "default_low_stock_days": "14",
        }
        for k, v in defaults.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",
                (k, v),
            )

        conn.execute(
            "INSERT OR IGNORE INTO users(username,password_hash,full_name,role,active,created_at) VALUES(?,?,?,?,?,?)",
            ("admin", hash_password("admin"), "Administrador", "Admin", 1, now_iso()),
        )
        conn.commit()

        backend["sync_enabled"] = True
        backend["loaded"] = True

        # Only seed Sheets if those tabs really had no records.
        seed_tables = []
        if settings_empty:
            seed_tables.append("settings")
        if users_empty:
            seed_tables.append("users")
        if seed_tables:
            sync_tables(seed_tables)


def _table_values(table):
    # Respeta las columnas que HOY existen en el Sheet. Si el usuario borró una
    # columna opcional, no la recreamos silenciosamente al guardar.
    cols = _sheet_target_columns(table)
    if not cols:
        return []
    df = pd.read_sql_query(
        f"SELECT {','.join(cols)} FROM {table}",
        get_conn(),
    )
    values = [cols]
    if not df.empty:
        for row in df.itertuples(index=False, name=None):
            values.append([_clean_sheet_value(v) for v in row])
    return values


def sync_table_to_sheet(table):
    sync_tables([table])


def sync_tables(tables):
    """
    Sincroniza tablas manteniendo el schema FLEXIBLE del Google Sheet.
    Las columnas que el usuario eliminó no se exigen ni se vuelven a crear.
    """
    backend = get_backend()

    if not backend.get("sync_enabled", False):
        return

    unique = [t for t in dict.fromkeys(tables) if t in SHEET_NAMES]
    writable = [t for t in unique if _sheet_target_columns(t)]
    if not writable:
        return

    with backend["lock"]:
        ranges = [_sheet_range(SHEET_NAMES[t], "AZ") for t in writable]

        # Clear old trailing rows in one request.
        backend["spreadsheet"].values_batch_clear(
            body={"ranges": ranges}
        )

        data = []
        for table in writable:
            values = _table_values(table)
            if not values:
                continue
            data.append({
                "range": _sheet_range(SHEET_NAMES[table], "AZ"),
                "majorDimension": "ROWS",
                "values": values,
            })

        if data:
            backend["spreadsheet"].values_batch_update({
                "valueInputOption": "RAW",
                "data": data,
            })


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

    # Streamlit reruns the whole script on every click.
    # Once loaded in this process, startup makes ZERO Google calls.
    if backend.get("loaded", False):
        return

    ensure_sheet_structure()
    reload_from_sheets()


try:
    init_db()
except Exception as _google_error:
    try:
        render_google_sheets_diagnostic(_google_error)
    except Exception as _diag_error:
        st.error("PERFUME OS no pudo iniciar Google Sheets.")
        st.code(
            f"ERROR DE INICIO:\n{type(_google_error).__name__}: {_google_error}\n\n"
            f"ERROR DEL DIAGNÓSTICO:\n{type(_diag_error).__name__}: {_diag_error}"
        )
        st.info(
            "No cambies los Secrets todavía. Copiame exactamente este bloque de error."
        )
    st.stop()

def get_setting(key, default=""):
    row = execute("SELECT value FROM settings WHERE key=?", (key,), commit=False).fetchone()
    return row["value"] if row else default

def set_setting(key, value):
    execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))

# ============================================================
# CIERRE HISTÓRICO CONCILIADO
# ============================================================
_HISTORY_RECON_DEFAULTS = {
    "history_recon_enabled": "1",
    "history_recon_start": "2026-09-01",
    "history_recon_cutoff": "2026-09-13",
    "history_recon_units_in": "144",
    "history_recon_units_sold": "52",
    "history_recon_unit_cost": "1900",
    "history_recon_note": "Cierre confirmado: 44+100 compradas; 38+14 vendidas; stock físico 92.",
}

def ensure_history_reconciliation_defaults():
    conn = get_conn()
    changed = False
    for k, v in _HISTORY_RECON_DEFAULTS.items():
        if not conn.execute("SELECT 1 FROM settings WHERE key=?", (k,)).fetchone():
            conn.execute("INSERT INTO settings(key,value) VALUES(?,?)", (k, v))
            changed = True
    # Migración automática de la versión anterior:
    # el corte 2026-09-14 absorbía movimientos nuevos realizados el 13/09.
    # El histórico confirmado 144/52 ya estaba cerrado antes del 13/09.
    old_cutoff = conn.execute("SELECT value FROM settings WHERE key='history_recon_cutoff'").fetchone()
    old_in = conn.execute("SELECT value FROM settings WHERE key='history_recon_units_in'").fetchone()
    old_sold = conn.execute("SELECT value FROM settings WHERE key='history_recon_units_sold'").fetchone()
    if (
        old_cutoff and str(old_cutoff[0]) == "2026-09-14"
        and old_in and abs(safe_float(old_in[0])-144) < 1e-9
        and old_sold and abs(safe_float(old_sold[0])-52) < 1e-9
    ):
        conn.execute("UPDATE settings SET value='2026-09-13' WHERE key='history_recon_cutoff'")
        changed = True

    if changed:
        conn.commit()
        sync_table_to_sheet("settings")

def history_reconciliation():
    enabled = get_setting("history_recon_enabled", "1") == "1"
    try:
        start = date.fromisoformat(get_setting("history_recon_start", "2026-09-01"))
    except Exception:
        start = date(2026, 9, 1)
    try:
        cutoff = date.fromisoformat(get_setting("history_recon_cutoff", "2026-09-13"))
    except Exception:
        cutoff = date(2026, 9, 13)
    if cutoff <= start:
        cutoff = start + timedelta(days=1)
    return {
        "enabled": enabled,
        "start": start,
        "cutoff": cutoff,
        "units_in": safe_float(get_setting("history_recon_units_in", "144")),
        "units_sold": safe_float(get_setting("history_recon_units_sold", "52")),
        "unit_cost": safe_float(get_setting("history_recon_unit_cost", "1900")),
    }

def _period_contains_recon(start, end, recon):
    try:
        s = start if isinstance(start, date) else date.fromisoformat(str(start)[:10])
        e = end if isinstance(end, date) else date.fromisoformat(str(end)[:10])
    except Exception:
        return False
    return recon["enabled"] and s <= recon["start"] and e >= recon["cutoff"]

def _raw_sold_units(start=None, end=None):
    where = ["s.status='Completada'"]
    params = []
    if start is not None:
        where.append("s.date>=?")
        params.append(str(start))
    if end is not None:
        where.append("s.date<?")
        params.append(str(end))
    return safe_float(scalar(
        f"""SELECT COALESCE(SUM(si.qty),0)
            FROM sale_items si
            JOIN sales s ON s.id=si.sale_id
            WHERE {' AND '.join(where)}""",
        tuple(params), 0
    ))

def _raw_sales_cogs(start=None, end=None):
    where = ["s.status='Completada'"]
    params = []
    if start is not None:
        where.append("s.date>=?")
        params.append(str(start))
    if end is not None:
        where.append("s.date<?")
        params.append(str(end))
    return safe_float(scalar(
        f"""SELECT COALESCE(SUM(si.qty*si.unit_cost),0)
            FROM sale_items si
            JOIN sales s ON s.id=si.sale_id
            WHERE {' AND '.join(where)}""",
        tuple(params), 0
    ))

def reconciled_sold_units(start=None, end=None):
    recon = history_reconciliation()
    raw = _raw_sold_units(start, end)
    if not recon["enabled"]:
        return raw
    raw_base = _raw_sold_units(recon["start"], recon["cutoff"])
    correction = recon["units_sold"] - raw_base
    if start is None and end is None:
        return raw + correction
    return raw + correction if _period_contains_recon(start, end, recon) else raw

def reconciled_sales_cogs(start=None, end=None):
    recon = history_reconciliation()
    raw = _raw_sales_cogs(start, end)
    if not recon["enabled"]:
        return raw
    raw_base = _raw_sales_cogs(recon["start"], recon["cutoff"])
    true_base = recon["units_sold"] * recon["unit_cost"]
    correction = true_base - raw_base
    if start is None and end is None:
        return raw + correction
    return raw + correction if _period_contains_recon(start, end, recon) else raw

def reconciled_acquisition_totals():
    kinds = ("COMPRA","STOCK_INICIAL","AJUSTE_EDICION","AJUSTE_POSITIVO")
    marks = ",".join(["?"] * len(kinds))
    raw_units = safe_float(scalar(
        f"""SELECT COALESCE(SUM(CASE WHEN qty>0 THEN qty ELSE 0 END),0)
            FROM inventory_moves WHERE move_type IN ({marks})""", kinds, 0
    ))
    raw_cost = safe_float(scalar(
        f"""SELECT COALESCE(SUM(CASE WHEN qty>0 THEN qty*unit_cost ELSE 0 END),0)
            FROM inventory_moves WHERE move_type IN ({marks})""", kinds, 0
    ))
    recon = history_reconciliation()
    if not recon["enabled"]:
        return raw_units, raw_cost
    params = kinds + (str(recon["start"]), str(recon["cutoff"]))
    raw_base_units = safe_float(scalar(
        f"""SELECT COALESCE(SUM(CASE WHEN qty>0 THEN qty ELSE 0 END),0)
            FROM inventory_moves
            WHERE move_type IN ({marks}) AND date>=? AND date<?""", params, 0
    ))
    raw_base_cost = safe_float(scalar(
        f"""SELECT COALESCE(SUM(CASE WHEN qty>0 THEN qty*unit_cost ELSE 0 END),0)
            FROM inventory_moves
            WHERE move_type IN ({marks}) AND date>=? AND date<?""", params, 0
    ))
    return (
        raw_units - raw_base_units + recon["units_in"],
        raw_cost - raw_base_cost + (recon["units_in"] * recon["unit_cost"]),
    )

def reconciled_profit(start, end, revenue=None):
    if revenue is None:
        df = period_sales(start, end)
        revenue = safe_float(df.total.sum()) if not df.empty else 0
    return revenue - reconciled_sales_cogs(start, end)

ensure_history_reconciliation_defaults()

def current_user():
    return st.session_state.get("user", {"username":"local","full_name":"Operador local","role":"Admin"})

def audit_event(action, entity_type="", entity_id="", before=None, after=None, notes=""):
    """Registro append-only. Nunca se edita desde la interfaz."""
    try:
        u = current_user()
        execute(
            """INSERT INTO audit_log(date,user_name,action,entity_type,entity_id,before_json,after_json,notes,created_at)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                today_iso(),
                str(u.get("full_name") or u.get("username") or "Sistema"),
                str(action),
                str(entity_type or ""),
                str(entity_id or ""),
                json.dumps(before, ensure_ascii=False, default=str) if before is not None else "",
                json.dumps(after, ensure_ascii=False, default=str) if after is not None else "",
                str(notes or ""),
                now_iso(),
            ),
        )
    except Exception:
        # La auditoría jamás debe romper una operación comercial.
        pass

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
    audit_event(
        "MOVIMIENTO_STOCK", "PRODUCT", product_id,
        after={"tipo":move_type,"cantidad":qty,"costo":unit_cost,"referencia":reference_type,"referencia_id":reference_id},
        notes=notes
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
        audit_event(
            "VENTA_CREADA","SALE",sale_id,
            after={
                "total":total,"costo":cost,"ganancia":profit,"margen":margin,
                "cobrado":paid,"cliente_id":customer_id,"canal":channel,
                "items":[{"product_id":i["product_id"],"qty":i["qty"],"unit_price":i["unit_price"]} for i in cart],
            },
            notes=notes
        )
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
        audit_event(
            "COMPRA_CREADA","PURCHASE",purchase_id,
            after={
                "total":total,"pagado":paid,"proveedor_id":supplier_id,"comprobante":invoice,
                "items":[{"product_id":i["product_id"],"qty":i["qty"],"unit_price":i["unit_price"]} for i in items],
            },
            notes=notes
        )
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
        audit_event(
            "VENTA_ANULADA","SALE",sale_id,
            before={"estado":"Completada","total":safe_float(sale["total"]),"cobrado":safe_float(sale["paid"])},
            after={"estado":"Anulada"}
        )
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
        "reservations","account_ledger","promotions","decant_pools","campaign_log",
        "customer_preferences","demand_requests","audit_log"
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

def executive_section(title, subtitle="", accent="#56354f"):
    st.markdown(
        f"""
        <div style="
            margin:1.15rem 0 .75rem 0;
            padding:.15rem 0 .15rem 1rem;
            border-left:4px solid {accent};
        ">
          <div style="font-size:.76rem;letter-spacing:.12em;text-transform:uppercase;
                      color:{accent};font-weight:850;margin-bottom:.18rem;">{title}</div>
          <div style="font-size:.92rem;color:#7d7279;line-height:1.45;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def product_intelligence_df(slow_days=7, target_days=14):
    """
    Una sola vista analítica por fragancia.
    No modifica datos: combina catálogo, stock, ventas y reservas.
    """
    inv = stock_df()
    if inv.empty:
        return pd.DataFrame(), {
            "days_observed": 1,
            "velocity_total": 0.0,
            "coverage_days": 0.0,
        }

    # Solo perfumes de 35 ml activos.
    inv = inv[
        (inv["active"] == 1)
        & (inv["product_type"].fillna("PERFUME") == "PERFUME")
        & (pd.to_numeric(inv["size_ml"], errors="coerce").fillna(0).round(3) == FIXED_SIZE_ML)
    ].copy()

    hist = qdf(
        """SELECT si.product_id,
                  SUM(si.qty) AS units_sold,
                  SUM(si.subtotal) AS revenue,
                  SUM((si.unit_price-si.unit_cost)*si.qty) AS profit,
                  COUNT(DISTINCT s.id) AS tickets,
                  MIN(s.date) AS first_sale_date,
                  MAX(s.date) AS last_sale_date
           FROM sale_items si
           JOIN sales s ON s.id=si.sale_id
           WHERE s.status='Completada'
           GROUP BY si.product_id"""
    )

    first_sale_global = scalar(
        "SELECT MIN(date) FROM sales WHERE status='Completada'",
        default=None
    )
    try:
        first_dt = date.fromisoformat(str(first_sale_global)[:10]) if first_sale_global else date.today()
    except Exception:
        first_dt = date.today()
    days_observed = max(1, min(30, (date.today() - first_dt).days + 1))
    recent_start = date.today() - timedelta(days=days_observed - 1)

    recent = qdf(
        """SELECT si.product_id, SUM(si.qty) AS units_recent
           FROM sale_items si
           JOIN sales s ON s.id=si.sale_id
           WHERE s.status='Completada' AND s.date>=?
           GROUP BY si.product_id""",
        (str(recent_start),)
    )

    demand = qdf(
        """SELECT product_id, SUM(qty) AS pending_demand
           FROM reservations
           WHERE status NOT IN ('Entregado','Cobrado','Cancelado')
           GROUP BY product_id"""
    )

    work = inv.merge(hist, left_on="id", right_on="product_id", how="left")
    if "product_id" in work.columns:
        work = work.drop(columns=["product_id"])
    work = work.merge(recent, left_on="id", right_on="product_id", how="left")
    if "product_id" in work.columns:
        work = work.drop(columns=["product_id"])
    work = work.merge(demand, left_on="id", right_on="product_id", how="left")
    if "product_id" in work.columns:
        work = work.drop(columns=["product_id"])

    for c in [
        "stock","avg_cost","sale_price","min_stock","units_sold","revenue","profit",
        "tickets","units_recent","pending_demand"
    ]:
        if c not in work.columns:
            work[c] = 0.0
        work[c] = pd.to_numeric(work[c], errors="coerce").fillna(0.0)

    # Nunca usamos stock negativo para valorizar.
    work["stock_pos"] = work["stock"].clip(lower=0)
    work["stock_cost_value"] = work["stock_pos"] * work["avg_cost"]
    work["stock_retail_value"] = work["stock_pos"] * work["sale_price"]
    work["potential_profit"] = work["stock_retail_value"] - work["stock_cost_value"]

    today_ts = pd.Timestamp(date.today())
    last_dt = pd.to_datetime(work.get("last_sale_date"), errors="coerce")
    work["days_since_sale"] = (today_ts - last_dt).dt.days
    work["days_since_sale"] = work["days_since_sale"].fillna(9999).astype(int)

    work["velocity_day"] = work["units_recent"] / float(days_observed)
    # Cobertura individual. 9999 = sin velocidad observada.
    work["coverage_days"] = np.where(
        work["velocity_day"] > 0,
        work["stock_pos"] / work["velocity_day"],
        9999.0
    )

    # Motor de reposición conservador:
    # - cubre target_days a la velocidad reciente;
    # - respeta mínimo;
    # - cubre reservas activas;
    # - si históricamente vendió y quedó en cero, recomienda al menos 1.
    velocity_target = np.ceil(work["velocity_day"] * float(target_days))
    base_target = np.maximum(work["min_stock"], velocity_target)
    base_target = np.maximum(base_target, work["pending_demand"])
    base_target = np.where(
        (work["units_sold"] > 0) & (base_target < 1),
        1,
        base_target
    )
    work["target_stock"] = np.ceil(base_target).astype(float)
    work["reorder_qty"] = np.ceil(
        np.maximum(0, work["target_stock"] - work["stock_pos"])
    ).astype(float)
    work["reorder_investment"] = work["reorder_qty"] * work["avg_cost"]

    work["slow"] = (
        (work["stock_pos"] > 0)
        & (
            (work["units_sold"] <= 0)
            | (work["days_since_sale"] >= int(slow_days))
        )
    )
    work["sold_out_with_history"] = (
        (work["stock_pos"] <= 0)
        & (work["units_sold"] > 0)
        & (work["sellable"] == 1)
    )

    work["original_similar"] = work.apply(
        lambda r: (
            f"{str(r.get('inspired_house') or '').strip()} "
            f"{str(r.get('inspired_name') or '').strip()}"
        ).strip() or "—",
        axis=1
    )
    work["display_name"] = work.apply(
        lambda r: f"{str(r.get('brand') or '').strip()} {str(r.get('name') or '').strip()}".strip(),
        axis=1
    )

    velocity_total = float(work["units_recent"].sum()) / float(days_observed)
    stock_total = float(work["stock_pos"].sum())
    coverage_total = (stock_total / velocity_total) if velocity_total > 0 else 0.0

    return work, {
        "days_observed": days_observed,
        "velocity_total": velocity_total,
        "coverage_days": coverage_total,
    }


# ============================================================
# MOTOR 360 — ANALÍTICA VISUAL, CONTROL Y DECISIÓN
# ============================================================

FAMILY_COLORS = {
    "dulce":"#f3d5df","gourmand":"#ead4b4","oriental":"#dfd2ef","amader":"#d9c8b6",
    "floral":"#efd5e7","fresco":"#d5e9ef","cítric":"#f4e2a9","citric":"#f4e2a9",
    "aromát":"#d3e6dc","aromat":"#d3e6dc","acuát":"#cee5ec","acuat":"#cee5ec",
    "frut":"#efd5ca","espec":"#e8d1c2","ámbar":"#e6cfad","ambar":"#e6cfad",
    "almiz":"#e5e1e2","cuero":"#d4c3b8","vain":"#eadac5",
}

def family_color(value):
    n = _norm35(value)
    for k,c in FAMILY_COLORS.items():
        if k in n:
            return c
    return "#e9e6e8"

def round_commercial_price(value, step=500):
    value = max(0.0, safe_float(value))
    if step <= 0:
        return value
    return float(math.ceil(value / step) * step)

def sales_daily_frame(days=90):
    start = date.today() - timedelta(days=max(1,int(days))-1)
    df = qdf(
        """SELECT date,
                  SUM(total) AS revenue,
                  SUM(profit) AS raw_profit,
                  COUNT(*) AS tickets
           FROM sales
           WHERE status='Completada' AND date>=?
           GROUP BY date ORDER BY date""",
        (str(start),)
    )
    full = pd.DataFrame({"date": pd.date_range(start, date.today(), freq="D")})
    if df.empty:
        full["revenue"] = 0.0
        full["raw_profit"] = 0.0
        full["tickets"] = 0
        return full
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    full = full.merge(df, on="date", how="left")
    for c in ["revenue","raw_profit","tickets"]:
        full[c] = pd.to_numeric(full[c], errors="coerce").fillna(0)
    return full

def business_health_snapshot():
    inv = stock_df()
    stock_cost, stock_retail, stock_potential = inventory_value()
    cash = safe_float(scalar(
        "SELECT COALESCE(SUM(CASE WHEN direction='INGRESO' THEN amount ELSE -amount END),0) FROM cash_moves",
        default=0
    ))
    receivables = safe_float(scalar(
        "SELECT COALESCE(SUM(debit-credit),0) FROM account_ledger WHERE entity_type='CUSTOMER'", default=0
    ))
    payables = safe_float(scalar(
        "SELECT COALESCE(SUM(credit-debit),0) FROM account_ledger WHERE entity_type='SUPPLIER'", default=0
    ))
    rev = safe_float(scalar("SELECT COALESCE(SUM(total),0) FROM sales WHERE status='Completada'", default=0))
    units = reconciled_sold_units()
    cogs = reconciled_sales_cogs()
    realized_profit = rev - cogs
    margin = realized_profit / rev * 100 if rev else 0.0

    acquired_units, acquired_cost = reconciled_acquisition_totals()
    stock_units = safe_float(inv.stock.clip(lower=0).sum()) if not inv.empty else 0.0

    intel, meta = product_intelligence_df(slow_days=14, target_days=14)
    slow_capital = float(intel.loc[intel.slow, "stock_cost_value"].sum()) if not intel.empty else 0.0
    zero_price = int(((intel.sale_price <= 0) & (intel.stock_pos > 0)).sum()) if not intel.empty else 0
    zero_cost = int(((intel.avg_cost <= 0) & (intel.stock_pos > 0)).sum()) if not intel.empty else 0
    critical = int(((intel.min_stock > 0) & (intel.stock_pos <= intel.min_stock)).sum()) if not intel.empty else 0
    overdue = safe_float(scalar(
        """SELECT COALESCE(SUM(debit-credit),0) FROM account_ledger
           WHERE entity_type='CUSTOMER'""", default=0
    ))

    # Score 0-100: simple, explícito y estable.
    score = 100.0
    if rev > 0 and margin < TARGET_MARGIN:
        score -= min(25, (TARGET_MARGIN-margin)*1.4)
    if stock_cost > 0:
        score -= min(18, (slow_capital/stock_cost)*22)
    if payables > cash + receivables:
        score -= 12
    if critical > 0:
        score -= min(12, critical*1.5)
    if zero_price:
        score -= min(10, zero_price*2)
    if zero_cost:
        score -= min(12, zero_cost*2)
    if abs((acquired_units-units)-stock_units) > 0.001:
        score -= 20
    score = max(0.0, min(100.0, score))

    if score >= 85:
        status, status_text = "Excelente", "El negocio está sano y sin desvíos importantes."
    elif score >= 70:
        status, status_text = "Sano", "Hay oportunidades de optimización, pero no una alarma estructural."
    elif score >= 55:
        status, status_text = "Atención", "Hay puntos que conviene corregir antes de acelerar compras."
    else:
        status, status_text = "Crítico", "Conviene priorizar caja, datos y rotación antes de crecer."

    return {
        "score":score, "status":status, "status_text":status_text,
        "cash":cash, "receivables":receivables, "payables":payables,
        "stock_cost":stock_cost, "stock_retail":stock_retail, "stock_potential":stock_potential,
        "revenue":rev, "units_sold":units, "cogs":cogs, "realized_profit":realized_profit,
        "margin":margin, "acquired_units":acquired_units, "acquired_cost":acquired_cost,
        "stock_units":stock_units, "slow_capital":slow_capital, "critical":critical,
        "zero_price":zero_price, "zero_cost":zero_cost, "overdue":overdue,
        "operating_equity":cash+receivables+stock_cost-payables,
        "commercial_potential":cash+receivables+stock_retail-payables,
        "potential_total_profit":realized_profit+stock_potential,
        "coverage_days":safe_float(meta.get("coverage_days",0)),
    }

def product_master_intelligence(slow_days=14, target_days=14):
    df, meta = product_intelligence_df(slow_days=slow_days, target_days=target_days)
    if df.empty:
        return df, meta

    target_margin = max(1.0, min(95.0, safe_float(TARGET_MARGIN))) / 100.0
    base_price = np.where(
        df["avg_cost"] > 0,
        df["avg_cost"] / max(0.01, (1-target_margin)),
        df["sale_price"]
    )
    # Alta rotación admite un pequeño premium; baja rotación conserva el piso de margen.
    speed_factor = np.where(df["velocity_day"] >= 0.5, 1.05, np.where(df["slow"], 0.97, 1.0))
    suggested = np.maximum(base_price, df["sale_price"] * speed_factor)
    df["suggested_price"] = [round_commercial_price(v,500) for v in suggested]
    df["current_margin"] = np.where(
        df["sale_price"] > 0,
        (df["sale_price"]-df["avg_cost"]) / df["sale_price"] * 100,
        0
    )
    # Índice de rotación 0-100.
    df["rotation_index"] = np.where(
        df["stock_pos"] > 0,
        100*(1-np.exp(-(df["velocity_day"]*30)/(df["stock_pos"]+1))),
        np.where(df["units_sold"]>0,100,0)
    )
    df["days_to_stockout"] = np.where(
        df["velocity_day"]>0,
        df["stock_pos"]/df["velocity_day"],
        np.nan
    )

    # Edad aproximada: última entrada positiva. El detalle FIFO se calcula aparte.
    last_in = qdf(
        """SELECT product_id, MAX(date) AS last_stock_in
           FROM inventory_moves WHERE qty>0 GROUP BY product_id"""
    )
    if not last_in.empty:
        df = df.merge(last_in, left_on="id", right_on="product_id", how="left")
        if "product_id" in df.columns:
            df = df.drop(columns=["product_id"])
    else:
        df["last_stock_in"] = None
    din = pd.to_datetime(df["last_stock_in"], errors="coerce")
    df["stock_age_days"] = (pd.Timestamp(date.today())-din).dt.days.fillna(0).clip(lower=0)

    # Score comercial 0-100: venta + margen + velocidad + recurrencia + señal de agotado.
    def norm_col(s):
        s = pd.to_numeric(s, errors="coerce").fillna(0)
        mx = float(s.max()) if len(s) else 0
        return (s/mx*100) if mx>0 else s*0
    sales_n = norm_col(df["units_sold"])
    profit_n = norm_col(df["profit"].clip(lower=0))
    velocity_n = norm_col(df["velocity_day"])
    margin_n = df["current_margin"].clip(lower=0,upper=80)/80*100
    demand_n = norm_col(df["pending_demand"])
    df["commercial_score"] = (
        sales_n*0.32 + profit_n*0.24 + velocity_n*0.20 + margin_n*0.14 + demand_n*0.10
    ).clip(0,100)

    return df, meta

def fifo_lots_df():
    """Reconstrucción FIFO de lotes restantes a partir del libro de movimientos."""
    moves = qdf(
        """SELECT im.id,im.date,im.product_id,im.move_type,im.qty,im.unit_cost,
                  im.reference_type,im.reference_id,
                  p.sku,p.brand,p.name,p.location
           FROM inventory_moves im
           JOIN products p ON p.id=im.product_id
           ORDER BY im.product_id,im.date,im.id"""
    )
    if moves.empty:
        return pd.DataFrame()

    rows = []
    today = date.today()
    for pid, g in moves.groupby("product_id", sort=False):
        lots = deque()
        for _, r in g.iterrows():
            qty = safe_float(r["qty"])
            if qty > 0:
                lots.append({
                    "source_id":r["id"], "date":str(r["date"]), "qty":qty,
                    "unit_cost":safe_float(r["unit_cost"]),
                    "move_type":r["move_type"], "reference_type":r["reference_type"],
                    "reference_id":r["reference_id"], "sku":r["sku"],
                    "brand":r["brand"], "name":r["name"], "location":r["location"],
                })
            elif qty < 0:
                need = -qty
                while need > 1e-9 and lots:
                    lot = lots[0]
                    take = min(need, lot["qty"])
                    lot["qty"] -= take
                    need -= take
                    if lot["qty"] <= 1e-9:
                        lots.popleft()
        for lot in lots:
            try:
                d = date.fromisoformat(str(lot["date"])[:10])
                age = max(0,(today-d).days)
            except Exception:
                age = 0
            rows.append({
                "product_id":pid,
                "SKU":lot["sku"],
                "Producto":f"{lot['brand'] or ''} {lot['name'] or ''}".strip(),
                "Fecha ingreso":lot["date"],
                "Tipo":lot["move_type"],
                "Referencia":f"{lot['reference_type'] or ''} {lot['reference_id'] or ''}".strip(),
                "Unidades restantes":round(lot["qty"],4),
                "Costo unitario":lot["unit_cost"],
                "Capital restante":lot["qty"]*lot["unit_cost"],
                "Edad días":age,
                "Ubicación":lot["location"] or "",
            })
    return pd.DataFrame(rows)

def business_anomalies():
    rows = []
    inv = stock_df(active_only=False)
    if not inv.empty:
        for _,r in inv.iterrows():
            stock = safe_float(r.stock)
            cost = safe_float(r.avg_cost)
            price = safe_float(r.sale_price)
            if stock < -1e-6:
                rows.append(("Crítica","Stock negativo",product_label(r),f"Stock {stock:g}"))
            if stock > 0 and cost <= 0:
                rows.append(("Crítica","Costo faltante",product_label(r),"Hay stock con costo $0"))
            if stock > 0 and price <= 0:
                rows.append(("Crítica","Precio faltante",product_label(r),"Hay stock sin precio de venta"))
            if price > 0 and cost > price:
                rows.append(("Crítica","Venta bajo costo",product_label(r),f"Costo {money(cost)} > venta {money(price)}"))
            if price > 0 and cost > 0:
                m = (price-cost)/price*100
                if m < TARGET_MARGIN:
                    rows.append(("Atención","Margen bajo",product_label(r),f"{m:.1f}% vs meta {TARGET_MARGIN:.1f}%"))

    dup_skus = qdf(
        """SELECT sku,COUNT(*) n FROM products GROUP BY sku HAVING COUNT(*)>1"""
    )
    for _,r in dup_skus.iterrows():
        rows.append(("Crítica","SKU duplicado",str(r.sku),f"{int(r.n)} productos"))

    orphan_sales = qdf(
        """SELECT s.id FROM sales s LEFT JOIN sale_items si ON si.sale_id=s.id
           WHERE s.status='Completada' GROUP BY s.id HAVING COUNT(si.id)=0"""
    )
    for _,r in orphan_sales.iterrows():
        rows.append(("Crítica","Venta sin detalle",f"Venta #{int(r.id):06d}","No tiene items asociados"))

    mism = qdf(
        """SELECT s.id,
                  COALESCE(SUM(si.subtotal),0) items_total,
                  s.subtotal sale_subtotal
           FROM sales s LEFT JOIN sale_items si ON si.sale_id=s.id
           WHERE s.status='Completada'
           GROUP BY s.id
           HAVING ABS(COALESCE(SUM(si.subtotal),0)-s.subtotal)>0.01"""
    )
    for _,r in mism.iterrows():
        rows.append(("Atención","Ticket inconsistente",f"Venta #{int(r.id):06d}",f"Detalle {money(r.items_total)} vs subtotal {money(r.sale_subtotal)}"))

    if not rows:
        return pd.DataFrame(columns=["Nivel","Tipo","Entidad","Detalle"])
    return pd.DataFrame(rows,columns=["Nivel","Tipo","Entidad","Detalle"])

def business_alerts():
    alerts = []
    snap = business_health_snapshot()
    intel, _ = product_master_intelligence()
    anomalies = business_anomalies()

    if not anomalies.empty:
        critical_n = int((anomalies.Nivel=="Crítica").sum())
        if critical_n:
            alerts.append(("bad",f"{critical_n} anomalía(s) crítica(s) de datos o precios requieren revisión."))
    if snap["payables"] > 0:
        alerts.append(("bad",f"Hay {money(snap['payables'])} pendientes de pagar."))
    if snap["receivables"] > 0:
        alerts.append(("warn",f"Hay {money(snap['receivables'])} pendientes de cobrar."))
    if snap["slow_capital"] > 0:
        alerts.append(("warn",f"{money(snap['slow_capital'])} están inmovilizados en stock lento."))
    if snap["critical"] > 0:
        alerts.append(("warn",f"{snap['critical']} fragancia(s) están en stock mínimo o por debajo."))
    if not intel.empty:
        soldout = intel[(intel.stock_pos<=0)&(intel.units_sold>0)]
        if len(soldout):
            alerts.append(("warn",f"{len(soldout)} fragancia(s) que ya vendieron están agotadas."))
        low_margin = intel[(intel.sale_price>0)&(intel.avg_cost>0)&(intel.current_margin<TARGET_MARGIN)]
        if len(low_margin):
            alerts.append(("warn",f"{len(low_margin)} producto(s) tienen margen inferior a {TARGET_MARGIN:.0f}%."))
    if not alerts:
        alerts.append(("good","No hay alertas críticas en este momento."))
    return alerts

def forecast_sales():
    daily = sales_daily_frame(45)
    if daily.empty:
        return {"daily":0,"trend":0,"7":0,"15":0,"30":0}
    recent7 = float(daily.tail(7).revenue.mean())
    recent14 = float(daily.tail(14).revenue.mean())
    recent30 = float(daily.tail(30).revenue.mean())
    weighted = recent7*0.50 + recent14*0.30 + recent30*0.20
    prev7 = float(daily.iloc[-14:-7].revenue.mean()) if len(daily)>=14 else recent7
    trend = ((recent7-prev7)/prev7*100) if prev7>0 else 0.0
    return {
        "daily":weighted, "trend":trend,
        "7":weighted*7, "15":weighted*15, "30":weighted*30
    }

def allocate_purchase_budget(budget, target_units=0, only_proven=True):
    intel, _ = product_master_intelligence(slow_days=14,target_days=21)
    if intel.empty or budget <= 0:
        return pd.DataFrame()
    pool = intel[(intel.active==1)&(intel.sellable==1)&(intel.avg_cost>0)].copy()
    if only_proven:
        pool = pool[(pool.units_sold>0)|(pool.pending_demand>0)]
    if pool.empty:
        return pd.DataFrame()

    # Prioridad: agotado / reserva / score comercial / velocidad / cobertura.
    pool["need_score"] = (
        (pool.stock_pos<=0).astype(int)*35
        + np.minimum(pool.pending_demand,5)*8
        + pool.commercial_score*0.35
        + np.minimum(pool.velocity_day*20,20)
        + np.where(pool.coverage_days<7,12,0)
    )
    pool = pool.sort_values(["need_score","commercial_score"],ascending=False)

    left = float(budget)
    units_left = int(target_units) if target_units and target_units>0 else 10**9
    picks = defaultdict(int)
    # round-robin para no poner todo el capital en un solo perfume
    active = pool.to_dict("records")
    guard = 0
    while left > 0 and units_left > 0 and active and guard < 5000:
        guard += 1
        made = False
        next_active = []
        for r in active:
            cost = safe_float(r["avg_cost"])
            desired_base = max(1, int(math.ceil(safe_float(r["reorder_qty"]))))
            if target_units and target_units>0:
                # En modo cantidad permitimos completar el pedido, pero evitamos
                # concentrar más de ~15% en un solo SKU salvo necesidad real mayor.
                desired = max(desired_base, int(math.ceil(target_units*0.15)))
            else:
                desired = desired_base
            if picks[int(r["id"])] >= desired:
                continue
            if cost <= left + 1e-9 and units_left > 0:
                picks[int(r["id"])] += 1
                left -= cost
                units_left -= 1
                made = True
            if picks[int(r["id"])] < desired:
                next_active.append(r)
        active = next_active
        if not made:
            break

    if not picks:
        return pd.DataFrame()

    out = pool[pool.id.isin(picks.keys())].copy()
    out["Comprar"] = out.id.map(picks).astype(int)
    out["Inversión"] = out["Comprar"]*out["avg_cost"]
    out["Stock después"] = out["stock_pos"]+out["Comprar"]
    out["Perfume"] = out["display_name"]
    out["Original / similar"] = out["original_similar"]
    return out.sort_values(["need_score","Comprar"],ascending=False)

def human_product_search(query, include_no_stock=True, limit=20):
    inv = stock_df()
    if inv.empty:
        return inv
    q = _norm35(query)
    if not q:
        return inv.head(limit)
    tokens = [t for t in q.split() if len(t)>1]
    rows = []
    for _,r in inv.iterrows():
        if not include_no_stock and safe_float(r.stock)<=0:
            continue
        blob = _norm35(_product_reference_text35(r))
        direct = sum(1 for t in tokens if t in blob)
        ratio = difflib.SequenceMatcher(None,q,blob[:max(len(q)*4,60)]).ratio()
        score = direct*25 + ratio*40
        if q in blob:
            score += 45
        if score >= 18:
            d = r.to_dict()
            d["_search_score"] = score
            rows.append(d)
    if not rows:
        return inv.iloc[0:0].copy()
    return pd.DataFrame(rows).sort_values("_search_score",ascending=False).head(limit)

def sales_assistant_recommendations(query="", gender="", family="", budget=0, customer_id=None, limit=8):
    intel, _ = product_master_intelligence(slow_days=21,target_days=14)
    if intel.empty:
        return intel
    pool = intel[(intel.stock_pos>0)&(intel.sellable==1)&(intel.active==1)].copy()
    if pool.empty:
        return pool

    pool["_assistant_score"] = pool["commercial_score"]*0.35 + pool["rotation_index"]*0.15
    q = _norm35(query)
    if q:
        def semantic_score(r):
            blob = _norm35(_product_reference_text35(r))
            tokens=[t for t in q.split() if len(t)>1]
            return (55 if q in blob else 0) + sum(16 for t in tokens if t in blob)
        pool["_assistant_score"] += pool.apply(semantic_score,axis=1)

    if gender:
        g = _norm35(gender)
        pool["_assistant_score"] += pool["gender"].fillna("").apply(lambda x: 18 if g in _norm35(x) or "unisex" in _norm35(x) else 0)
    if family:
        f = _norm35(family)
        pool["_assistant_score"] += pool["olfactory_family"].fillna("").apply(lambda x: 25 if f and f in _norm35(x) else 0)
    if budget and budget>0:
        pool["_assistant_score"] += np.where(pool.sale_price<=budget,15,-45)

    # Historial del cliente: familia / perfumes ya comprados.
    if customer_id:
        hist = qdf(
            """SELECT p.olfactory_family,p.inspired_house,p.inspired_name,p.id product_id,SUM(si.qty) qty
               FROM sale_items si JOIN sales s ON s.id=si.sale_id JOIN products p ON p.id=si.product_id
               WHERE s.customer_id=? AND s.status='Completada'
               GROUP BY p.id""",(int(customer_id),)
        )
        if not hist.empty:
            fams = [_norm35(x) for x in hist.olfactory_family.dropna().astype(str) if str(x).strip()]
            bought_ids = set(pd.to_numeric(hist.product_id,errors="coerce").dropna().astype(int))
            pool["_assistant_score"] += pool["olfactory_family"].fillna("").apply(
                lambda x: 14 if any(f in _norm35(x) for f in fams if f) else 0
            )
            # evita recomendar exactamente lo mismo primero, pero no lo elimina
            pool["_assistant_score"] += pool.id.apply(lambda x:-6 if int(x) in bought_ids else 5)

    pool["Razón"] = pool.apply(
        lambda r: (
            ("Coincide con tu búsqueda · " if q and any(t in _norm35(_product_reference_text35(r)) for t in q.split() if len(t)>1) else "")
            + (f"{r.get('olfactory_family') or 'perfil definido'} · ")
            + (f"margen {safe_float(r.get('current_margin')):.0f}% · ")
            + (f"stock {safe_float(r.get('stock_pos')):g}")
        ).strip(" ·"),
        axis=1
    )
    return pool.sort_values("_assistant_score",ascending=False).head(limit)

def customer_360_df():
    df = qdf(
        """SELECT c.id,c.name,c.phone,c.instagram,c.gender,c.preferred_families,c.vip,
                  COUNT(DISTINCT CASE WHEN s.status='Completada' THEN s.id END) AS purchases,
                  COALESCE(SUM(CASE WHEN s.status='Completada' THEN s.total ELSE 0 END),0) AS spend,
                  COALESCE(AVG(CASE WHEN s.status='Completada' THEN s.total END),0) AS avg_ticket,
                  MIN(CASE WHEN s.status='Completada' THEN s.date END) AS first_purchase,
                  MAX(CASE WHEN s.status='Completada' THEN s.date END) AS last_purchase
           FROM customers c LEFT JOIN sales s ON s.customer_id=c.id
           WHERE c.active=1
           GROUP BY c.id"""
    )
    if df.empty:
        return df
    last = pd.to_datetime(df.last_purchase,errors="coerce")
    df["days_since_purchase"]=(pd.Timestamp(date.today())-last).dt.days.fillna(9999)
    # RFM simplificado, transparente.
    spend = pd.to_numeric(df.spend,errors="coerce").fillna(0)
    freq = pd.to_numeric(df.purchases,errors="coerce").fillna(0)
    rec = df.days_since_purchase
    max_spend=max(float(spend.max()),1)
    max_freq=max(float(freq.max()),1)
    rec_score=np.clip(100-(rec.clip(upper=180)/180*100),0,100)
    df["customer_score"]=(spend/max_spend*40 + freq/max_freq*35 + rec_score*25).clip(0,100)
    return df.sort_values("customer_score",ascending=False)

def repurchase_opportunities(cycle_days=45):
    c = customer_360_df()
    if c.empty:
        return c
    c = c[c.last_purchase.notna()].copy()
    c["expected_repurchase_date"] = pd.to_datetime(c.last_purchase)+pd.to_timedelta(int(cycle_days),unit="D")
    c["days_to_repurchase"]=(c["expected_repurchase_date"]-pd.Timestamp(date.today())).dt.days
    c["due"] = c["days_to_repurchase"] <= 0
    return c.sort_values(["due","customer_score","days_to_repurchase"],ascending=[False,False,True])

def financial_timeline_df(days=90):
    start = str(date.today()-timedelta(days=max(1,int(days))-1))
    sales = qdf(
        """SELECT date,'Venta' AS Tipo,total AS Importe,
                  printf('Venta #%06d',id) AS Detalle
           FROM sales WHERE status='Completada' AND date>=?""",(start,)
    )
    purchases = qdf(
        """SELECT date,'Compra' AS Tipo,-total AS Importe,
                  'Compra #'||id AS Detalle
           FROM purchases WHERE date>=?""",(start,)
    )
    expenses = qdf(
        """SELECT date,'Gasto' AS Tipo,-amount AS Importe,
                  COALESCE(category,'Gasto') AS Detalle
           FROM expenses WHERE date>=?""",(start,)
    )
    frames=[x for x in [sales,purchases,expenses] if not x.empty]
    if not frames:
        return pd.DataFrame(columns=["date","Tipo","Importe","Detalle"])
    out=pd.concat(frames,ignore_index=True)
    out["date"]=pd.to_datetime(out["date"],errors="coerce")
    return out.sort_values("date")

def explain_kpi(metric):
    snap=business_health_snapshot()
    data = {
        "Patrimonio operativo":(
            "Caja + cuentas por cobrar + stock a costo − cuentas por pagar",
            [
                ("Caja",snap["cash"]),("Por cobrar",snap["receivables"]),
                ("Stock a costo",snap["stock_cost"]),("Por pagar",-snap["payables"])
            ],
            snap["operating_equity"]
        ),
        "Potencial comercial":(
            "Caja + cuentas por cobrar + stock a precio de venta − cuentas por pagar",
            [
                ("Caja",snap["cash"]),("Por cobrar",snap["receivables"]),
                ("Stock a venta",snap["stock_retail"]),("Por pagar",-snap["payables"])
            ],
            snap["commercial_potential"]
        ),
        "Ganancia realizada":(
            "Facturación acumulada − costo de mercadería vendida",
            [("Facturación",snap["revenue"]),("Costo vendido",-snap["cogs"])],
            snap["realized_profit"]
        ),
        "Ganancia potencial":(
            "Valor de venta del stock actual − costo del stock actual",
            [("Stock a venta",snap["stock_retail"]),("Stock a costo",-snap["stock_cost"])],
            snap["stock_potential"]
        ),
        "Capital histórico":(
            "Costo conciliado de todas las unidades ingresadas",
            [("Capital ingresado",snap["acquired_cost"])],
            snap["acquired_cost"]
        ),
    }
    return data.get(metric,data["Patrimonio operativo"])

def build_label_pdf(product_ids):
    if rl_canvas is None or qrcode is None or ImageReader is None:
        return None
    ids=[int(x) for x in product_ids]
    if not ids:
        return None
    marks=",".join(["?"]*len(ids))
    df=qdf(f"SELECT * FROM products WHERE id IN ({marks}) ORDER BY brand,name",tuple(ids))
    if df.empty:
        return None

    buf=io.BytesIO()
    c=rl_canvas.Canvas(buf,pagesize=A4)
    W,H=A4
    margin=28
    cols,rows=3,8
    cell_w=(W-2*margin)/cols
    cell_h=(H-2*margin)/rows

    for idx,(_,r) in enumerate(df.iterrows()):
        if idx>0 and idx%(cols*rows)==0:
            c.showPage()
        slot=idx%(cols*rows)
        col=slot%cols
        row=slot//cols
        x=margin+col*cell_w
        y=H-margin-(row+1)*cell_h

        c.roundRect(x+4,y+4,cell_w-8,cell_h-8,8,stroke=1,fill=0)
        name=f"{r['brand'] or ''} {r['name'] or ''}".strip()
        original=f"{r['inspired_house'] or ''} {r['inspired_name'] or ''}".strip()
        c.setFont("Helvetica-Bold",8.4)
        c.drawString(x+10,y+cell_h-20,name[:31])
        c.setFont("Helvetica",6.8)
        c.drawString(x+10,y+cell_h-31,(original or "35 ml")[:36])
        c.setFont("Helvetica-Bold",10)
        c.drawString(x+10,y+11,money(r["sale_price"]))

        qr_payload=f"PERFUME35|{r['sku']}|{r['id']}"
        qr=qrcode.make(qr_payload)
        qbuf=io.BytesIO()
        qr.save(qbuf,format="PNG")
        qbuf.seek(0)
        c.drawImage(ImageReader(qbuf),x+cell_w-48,y+10,width=34,height=34,preserveAspectRatio=True,mask='auto')
    c.save()
    buf.seek(0)
    return buf.getvalue()

def decode_uploaded_code(uploaded):
    if uploaded is None:
        return ""
    try:
        img=Image.open(uploaded).convert("RGB") if Image is not None else None
        if img is None:
            return ""
        if zbar_decode is not None:
            decoded=zbar_decode(img)
            if decoded:
                return decoded[0].data.decode("utf-8",errors="ignore")
        if cv2 is not None:
            arr=np.array(img)
            detector=cv2.QRCodeDetector()
            data,_,_=detector.detectAndDecode(arr)
            return data or ""
    except Exception:
        return ""
    return ""

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


def sales_master_df(start=None, end=None):
    """Vista maestra de ventas con productos resumidos. Solo consulta el cache local."""
    where = []
    params = []
    if start is not None:
        where.append("s.date >= ?")
        params.append(str(start))
    if end is not None:
        where.append("s.date < ?")
        params.append(str(end))
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    return qdf(
        f"""
        SELECT
            s.id,
            s.date,
            CASE WHEN LENGTH(COALESCE(s.created_at,'')) >= 16 THEN SUBSTR(s.created_at,12,5) ELSE '' END AS hora,
            COALESCE(c.name,'Consumidor final') AS cliente,
            COALESCE(c.phone,'') AS telefono,
            COALESCE(v.name,'Venta directa') AS vendedor,
            COALESCE(s.channel,'Sin canal') AS canal,
            COALESCE(s.payment_method,'Sin definir') AS medio_pago,
            s.subtotal,
            s.discount AS descuento,
            s.shipping AS envio,
            s.total,
            s.cost AS costo,
            s.profit AS ganancia,
            s.margin AS margen,
            s.paid AS cobrado,
            MAX(s.total-s.paid,0) AS saldo,
            s.status AS estado,
            COALESCE(s.notes,'') AS notas,
            COUNT(si.id) AS lineas,
            COALESCE(SUM(si.qty),0) AS unidades,
            COALESCE(GROUP_CONCAT(
                p.brand || ' ' || p.name ||
                CASE WHEN COALESCE(p.size_ml,0)>0 THEN ' ' || CAST(p.size_ml AS INT) || 'ml' ELSE '' END ||
                ' ×' || CAST(si.qty AS TEXT)
            , ' · '),'') AS productos
        FROM sales s
        LEFT JOIN customers c ON c.id=s.customer_id
        LEFT JOIN vendors v ON v.id=s.vendor_id
        LEFT JOIN sale_items si ON si.sale_id=s.id
        LEFT JOIN products p ON p.id=si.product_id
        {where_sql}
        GROUP BY s.id
        ORDER BY s.id DESC
        """,
        tuple(params),
    )


def sale_items_detail_df(sale_id):
    return qdf(
        """
        SELECT
            p.sku AS SKU,
            p.brand AS Marca,
            p.name AS Perfume,
            p.size_ml AS ml,
            p.gender AS Genero,
            p.product_type AS Tipo,
            si.qty AS Cantidad,
            si.unit_price AS Precio_unitario,
            si.unit_cost AS Costo_unitario,
            si.subtotal AS Subtotal,
            (si.unit_price-si.unit_cost)*si.qty AS Ganancia,
            CASE WHEN si.unit_price>0
                 THEN ((si.unit_price-si.unit_cost)/si.unit_price)*100
                 ELSE 0 END AS Margen_pct
        FROM sale_items si
        JOIN products p ON p.id=si.product_id
        WHERE si.sale_id=?
        ORDER BY si.id
        """,
        (int(sale_id),),
    )


def sale_header_row(sale_id):
    df = qdf(
        """
        SELECT s.*, COALESCE(c.name,'Consumidor final') cliente,
               COALESCE(c.phone,'') telefono, COALESCE(c.instagram,'') instagram,
               COALESCE(v.name,'Venta directa') vendedor
        FROM sales s
        LEFT JOIN customers c ON c.id=s.customer_id
        LEFT JOIN vendors v ON v.id=s.vendor_id
        WHERE s.id=?
        """,
        (int(sale_id),),
    )
    return None if df.empty else df.iloc[0]


def render_sale_detail(sale_id, key_prefix="sale"):
    row = sale_header_row(sale_id)
    if row is None:
        st.warning("La venta seleccionada no existe.")
        return

    items = sale_items_detail_df(sale_id)
    status = str(row.status or "")
    badge_class = "badge-good" if status == "Completada" else ("badge-bad" if status == "Anulada" else "badge-warn")
    product_count = safe_float(items["Cantidad"].sum()) if not items.empty else 0
    saldo = max(0.0, safe_float(row.total)-safe_float(row.paid))

    st.markdown(
        f"""
        <div class="sale-ticket">
          <div class="ticket-id">TICKET DE VENTA · #{int(row.id):06d}</div>
          <div class="ticket-title">{row.cliente}</div>
          <div class="ticket-meta">
            {row.date} · {str(row.created_at)[11:16] if row.created_at else ''} &nbsp;•&nbsp;
            {row.channel or 'Sin canal'} &nbsp;•&nbsp; {row.payment_method or 'Sin medio'} &nbsp;•&nbsp;
            {row.vendedor}
          </div>
          <div style="margin-top:12px">
            <span class="badge {badge_class}">{status}</span>
            <span class="badge badge-plum">{product_count:g} unidad(es)</span>
            <span class="badge {'badge-good' if saldo <= 0 else 'badge-warn'}">{'Cobrado' if saldo <= 0 else 'Saldo pendiente'}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    a,b,c,d,e = st.columns(5)
    a.metric("Total", money(row.total))
    b.metric("Cobrado", money(row.paid))
    c.metric("Saldo", money(saldo))
    d.metric("Ganancia", money(row.profit))
    e.metric("Margen", pct(row.margin))

    st.markdown("#### Productos vendidos")
    if items.empty:
        st.info("Esta venta no tiene líneas de producto registradas.")
    else:
        show = items.copy()
        show["Producto"] = (
            show["Marca"].fillna("") + " " + show["Perfume"].fillna("") +
            show["ml"].apply(lambda x: f" · {safe_float(x):g} ml" if safe_float(x)>0 else "")
        )
        show = show[["SKU","Producto","Cantidad","Precio_unitario","Costo_unitario","Subtotal","Ganancia","Margen_pct"]]
        st.dataframe(
            show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Precio_unitario": st.column_config.NumberColumn("Precio unit.", format="$ %.0f"),
                "Costo_unitario": st.column_config.NumberColumn("Costo unit.", format="$ %.0f"),
                "Subtotal": st.column_config.NumberColumn("Subtotal", format="$ %.0f"),
                "Ganancia": st.column_config.NumberColumn("Ganancia", format="$ %.0f"),
                "Margen_pct": st.column_config.ProgressColumn("Margen", min_value=0, max_value=100, format="%.1f%%"),
            },
        )

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown('<div class="section-title">Cliente</div>', unsafe_allow_html=True)
        st.write(f"**{row.cliente}**")
        if row.telefono:
            st.caption(f"WhatsApp: {row.telefono}")
        if row.instagram:
            st.caption(f"Instagram: {row.instagram}")
    with c2:
        st.markdown('<div class="section-title">Operación</div>', unsafe_allow_html=True)
        st.write(f"**Canal:** {row.channel or '—'}")
        st.caption(f"Vendedor: {row.vendedor}")
    with c3:
        st.markdown('<div class="section-title">Cobro</div>', unsafe_allow_html=True)
        st.write(f"**{row.payment_method or '—'}**")
        st.caption(f"Pagado {money(row.paid)} de {money(row.total)}")

    if str(row.notes or "").strip():
        st.markdown('<div class="section-title">Observaciones</div>', unsafe_allow_html=True)
        st.info(str(row.notes))


def pro_kpi(label, value, sub="", accent="gold"):
    colors = {
        "gold":"#b88945","plum":"#56354f","rose":"#9b5365",
        "green":"#2f765a","blue":"#486a8a","red":"#ad4a4a"
    }
    color = colors.get(accent, colors["gold"])
    st.markdown(
        f"""
        <div class="pro-card" style="border-top:3px solid {color}">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          <div class="sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



# ============================================================
# BIBLIOTECA MAESTRA 35 ML
# Equivalencias orientativas: sirven para búsqueda y venta asistida.
# No implican autenticidad, afiliación ni identidad 1:1 con otra marca.
# ============================================================
FRAGRANCE_LIBRARY = [{'tube_name': 'Asad', 'reference_house': 'Lattafa', 'reference_name': 'Asad', 'designer_house': 'Dior', 'designer_name': 'Sauvage Elixir', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Hombre', 'family': 'Ambarado especiado', 'profile': 'Especiado, ambarado, intenso, nocturno', 'priority': 'A+', 'aliases': 'Asad negro|Assad|Sauvage Elixir'}, {'tube_name': 'Asad Zanzibar', 'reference_house': 'Lattafa', 'reference_name': 'Asad Zanzibar', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Hombre', 'family': 'Aromático dulce', 'profile': 'Fresco, salado, cremoso, tropical', 'priority': 'A', 'aliases': 'Asad azul|Zanzibar'}, {'tube_name': 'Asad Bourbon', 'reference_house': 'Lattafa', 'reference_name': 'Asad Bourbon', 'designer_house': 'Azzaro', 'designer_name': 'The Most Wanted', 'relation': 'ADN similar / comparación frecuente', 'confidence': 'Media', 'gender': 'Hombre', 'family': 'Ambarado gourmand', 'profile': 'Vainilla, cacao, especias, cálido', 'priority': 'A', 'aliases': 'Asad marrón|Bourbon|Most Wanted'}, {'tube_name': 'Yara Rosa', 'reference_house': 'Lattafa', 'reference_name': 'Yara', 'designer_house': 'Dior', 'designer_name': 'Poison Girl', 'relation': 'ADN similar; no clon 1:1', 'confidence': 'Media', 'gender': 'Mujer', 'family': 'Floral gourmand', 'profile': 'Cremoso, dulce, avainillado, femenino', 'priority': 'A+', 'aliases': 'Yara Pink|Yara rosada|Yara'}, {'tube_name': 'Yara Candy', 'reference_house': 'Lattafa', 'reference_name': 'Yara Candy', 'designer_house': 'Dior', 'designer_name': 'Poison Girl', 'relation': 'Comparación frecuente; no clon 1:1', 'confidence': 'Media', 'gender': 'Mujer', 'family': 'Frutal gourmand', 'profile': 'Frutilla, caramelo, vainilla, dulce', 'priority': 'A+', 'aliases': 'Yara fucsia|Candy'}, {'tube_name': 'Yara Tous', 'reference_house': 'Lattafa', 'reference_name': 'Yara Tous', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Tropical floral', 'profile': 'Mango, coco, flores blancas, tropical', 'priority': 'A+', 'aliases': 'Yara naranja|Tous'}, {'tube_name': 'Yara Moi', 'reference_house': 'Lattafa', 'reference_name': 'Yara Moi', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Floral ambarado', 'profile': 'Durazno, jazmín, caramelo, elegante', 'priority': 'A', 'aliases': 'Yara blanca|Moi'}, {'tube_name': 'Khamrah', 'reference_house': 'Lattafa', 'reference_name': 'Khamrah', 'designer_house': 'Kilian', 'designer_name': "Angels' Share", 'relation': 'Mismo territorio gourmand; no clon exacto', 'confidence': 'Media', 'gender': 'Unisex', 'family': 'Gourmand especiado', 'profile': 'Canela, dátiles, vainilla, cálido', 'priority': 'A+', 'aliases': 'Kharah|Khamra|Angels Share'}, {'tube_name': 'Khamrah Qahwa', 'reference_house': 'Lattafa', 'reference_name': 'Khamrah Qahwa', 'designer_house': 'Kilian', 'designer_name': "Angels' Share", 'relation': 'ADN gourmand similar + café', 'confidence': 'Media', 'gender': 'Unisex', 'family': 'Gourmand café', 'profile': 'Café, canela, vainilla, especias', 'priority': 'A+', 'aliases': 'Qahwa|Khamrah café'}, {'tube_name': 'Khamrah Dukhan', 'reference_house': 'Lattafa', 'reference_name': 'Khamrah Dukhan', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Unisex', 'family': 'Gourmand ahumado', 'profile': 'Dulce, especiado, ahumado, oscuro', 'priority': 'A', 'aliases': 'Dukhan'}, {'tube_name': '9PM', 'reference_house': 'Afnan', 'reference_name': '9PM', 'designer_house': 'Jean Paul Gaultier', 'designer_name': 'Ultra Male', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Hombre', 'family': 'Ambarado vainilla', 'profile': 'Manzana, vainilla, dulce, nocturno', 'priority': 'A+', 'aliases': '9 pm negro|Nine PM|Ultra Male'}, {'tube_name': '9PM Rebel', 'reference_house': 'Afnan', 'reference_name': '9PM Rebel', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Hombre', 'family': 'Frutal amaderado', 'profile': 'Frutal, dulce, moderno, juvenil', 'priority': 'A', 'aliases': '9 pm rebel|Rebel'}, {'tube_name': '9AM Dive', 'reference_house': 'Afnan', 'reference_name': '9AM Dive', 'designer_house': 'Yves Saint Laurent / Chanel', 'designer_name': 'Y EDP / Bleu de Chanel (ADN azul)', 'relation': 'Perfil azul similar; no clon 1:1', 'confidence': 'Media', 'gender': 'Hombre', 'family': 'Aromático azul', 'profile': 'Fresco, cítrico, especiado, versátil', 'priority': 'A', 'aliases': '9am|9 am|Dive'}, {'tube_name': 'Club de Nuit Intense Man', 'reference_house': 'Armaf', 'reference_name': 'Club de Nuit Intense Man', 'designer_house': 'Creed', 'designer_name': 'Aventus', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Hombre', 'family': 'Frutal amaderado', 'profile': 'Limón, piña, maderas, ahumado', 'priority': 'A+', 'aliases': 'CDNIM|Club de nuit intense|Aventus'}, {'tube_name': 'Club de Nuit Untold', 'reference_house': 'Armaf', 'reference_name': 'Club de Nuit Untold', 'designer_house': 'Maison Francis Kurkdjian', 'designer_name': 'Baccarat Rouge 540', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Ámbar floral', 'profile': 'Azafrán, ámbar, dulce, aireado', 'priority': 'A+', 'aliases': 'Untold|BR540|Baccarat'}, {'tube_name': 'Club de Nuit Woman', 'reference_house': 'Armaf', 'reference_name': 'Club de Nuit Woman', 'designer_house': 'Chanel', 'designer_name': 'Coco Mademoiselle', 'relation': 'Inspiración muy conocida', 'confidence': 'Alta', 'gender': 'Mujer', 'family': 'Chipre floral', 'profile': 'Cítrico, rosa, patchouli, elegante', 'priority': 'A', 'aliases': 'CDN Woman|Coco Mademoiselle'}, {'tube_name': 'Fakhar Black', 'reference_house': 'Lattafa', 'reference_name': 'Fakhar Black', 'designer_house': 'Yves Saint Laurent', 'designer_name': 'Y Eau de Parfum', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Hombre', 'family': 'Aromático', 'profile': 'Manzana, jengibre, lavanda, limpio', 'priority': 'A+', 'aliases': 'Fakhar negro|Fakhar|YSL Y|Y EDP'}, {'tube_name': 'Fakhar Rose', 'reference_house': 'Lattafa', 'reference_name': 'Fakhar Rose', 'designer_house': 'Givenchy', 'designer_name': "L'Interdit EDP", 'relation': 'Comparación frecuente; interpretación floral', 'confidence': 'Media', 'gender': 'Mujer', 'family': 'Floral blanco', 'profile': 'Tuberosa, jazmín, vainilla, elegante', 'priority': 'A', 'aliases': 'Fakhar blanco|Fakhar rosa|Linterdit'}, {'tube_name': 'Qaed Al Fursan', 'reference_house': 'Lattafa', 'reference_name': 'Qaed Al Fursan', 'designer_house': 'Creed', 'designer_name': 'Aventus', 'relation': 'ADN de piña tipo Aventus; no clon exacto', 'confidence': 'Media', 'gender': 'Hombre', 'family': 'Frutal amaderado', 'profile': 'Piña, madera, dulce, tropical', 'priority': 'A', 'aliases': 'Qaed negro|Al Fursan|Fursan'}, {'tube_name': 'Qaed Al Fursan Unlimited', 'reference_house': 'Lattafa', 'reference_name': 'Qaed Al Fursan Unlimited', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Unisex', 'family': 'Tropical cremoso', 'profile': 'Coco, piña, vainilla, solar', 'priority': 'A', 'aliases': 'Qaed blanco|Fursan white|Unlimited'}, {'tube_name': "Bade'e Al Oud Oud for Glory", 'reference_house': 'Lattafa', 'reference_name': "Bade'e Al Oud Oud for Glory", 'designer_house': 'Initio', 'designer_name': 'Oud for Greatness', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Oud especiado', 'profile': 'Oud, azafrán, especias, oscuro', 'priority': 'A', 'aliases': 'Badee negro|Oud for Glory|Oud for Greatness'}, {'tube_name': "Bade'e Al Oud Amethyst", 'reference_house': 'Lattafa', 'reference_name': "Bade'e Al Oud Amethyst", 'designer_house': 'Initio', 'designer_name': 'Atomic Rose', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Rosa ambarada', 'profile': 'Rosa, vainilla, ámbar, intenso', 'priority': 'A', 'aliases': 'Amethyst|Badee violeta|Atomic Rose'}, {'tube_name': "Bade'e Al Oud Honor & Glory", 'reference_house': 'Lattafa', 'reference_name': "Bade'e Al Oud Honor & Glory", 'designer_house': '', 'designer_name': '', 'relation': 'Sin clon 1:1 consolidado', 'confidence': 'Orientativa', 'gender': 'Unisex', 'family': 'Gourmand especiado', 'profile': 'Piña brûlée, vainilla, especias, cremoso', 'priority': 'A+', 'aliases': 'Honor and Glory|Honor Glory|Badee blanco'}, {'tube_name': "Bade'e Al Oud Sublime", 'reference_house': 'Lattafa', 'reference_name': "Bade'e Al Oud Sublime", 'designer_house': 'Kayali', 'designer_name': 'Eden Juicy Apple 01', 'relation': 'ADN frutal similar; no clon exacto', 'confidence': 'Media', 'gender': 'Unisex', 'family': 'Frutal dulce', 'profile': 'Manzana roja, frutas, musgo, dulce', 'priority': 'A', 'aliases': 'Sublime|Badee rojo|Eden Juicy Apple'}, {'tube_name': 'Eclaire', 'reference_house': 'Lattafa', 'reference_name': 'Eclaire', 'designer_house': 'Giardini di Toscana', 'designer_name': 'Bianco Latte', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Mujer', 'family': 'Gourmand lactónico', 'profile': 'Caramelo, leche, miel, vainilla', 'priority': 'A+', 'aliases': 'Eclair|Bianco Latte|Eclaire'}, {'tube_name': 'Her Confession', 'reference_house': 'Lattafa', 'reference_name': 'Her Confession', 'designer_house': 'Les Liquides Imaginaires', 'designer_name': 'Blanche Bête', 'relation': 'Inspiración / alternativa muy cercana', 'confidence': 'Alta', 'gender': 'Mujer', 'family': 'Lactónico floral', 'profile': 'Leche, vainilla, flores blancas, incienso', 'priority': 'A+', 'aliases': 'Her confession|Blanche Bete'}, {'tube_name': 'His Confession', 'reference_house': 'Lattafa', 'reference_name': 'His Confession', 'designer_house': 'Givenchy / Dior', 'designer_name': 'Gentleman EDP / Dior Homme Intense (ADN)', 'relation': 'ADN iris-vainilla similar; no clon 1:1', 'confidence': 'Media', 'gender': 'Hombre', 'family': 'Ambarado iris', 'profile': 'Iris, vainilla, ámbar, elegante', 'priority': 'A', 'aliases': 'His confession|Dior Homme Intense|Gentleman'}, {'tube_name': 'Mayar', 'reference_house': 'Lattafa', 'reference_name': 'Mayar', 'designer_house': 'Mugler', 'designer_name': 'Angel Nova', 'relation': 'Similar / alternativa, no clon exacto', 'confidence': 'Media', 'gender': 'Mujer', 'family': 'Frutal floral', 'profile': 'Lichi, frambuesa, rosa, almizcle', 'priority': 'A', 'aliases': 'Mayar rosa|Angel Nova'}, {'tube_name': 'Mayar Natural Intense', 'reference_house': 'Lattafa', 'reference_name': 'Mayar Natural Intense', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Frutal acuático', 'profile': 'Higo, coco, flores, fresco', 'priority': 'B', 'aliases': 'Mayar verde|Natural Intense'}, {'tube_name': 'Ameerat Al Arab', 'reference_house': 'Asdaaf', 'reference_name': 'Ameerat Al Arab', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Floral frutal', 'profile': 'Dulce, floral, almizclado, femenino', 'priority': 'A+', 'aliases': 'Amerat al arab|Ameerat|Princesa arabe'}, {'tube_name': 'Ameerat Al Arab Prive Rose', 'reference_house': 'Asdaaf', 'reference_name': 'Ameerat Al Arab Prive Rose', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Floral dulce', 'profile': 'Rosa, frutas, vainilla, femenino', 'priority': 'A', 'aliases': 'Ameerat rose|Prive Rose|Amerat rose'}, {'tube_name': 'Ameer Al Arab Imperium', 'reference_house': 'Asdaaf', 'reference_name': 'Ameer Al Arab Imperium', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Hombre', 'family': 'Aromático amaderado', 'profile': 'Fresco, especiado, amaderado', 'priority': 'B', 'aliases': 'Ameerat imperium|Imperium Asdaaf'}, {'tube_name': 'Hayaati Black', 'reference_house': 'Lattafa', 'reference_name': 'Hayaati', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Hombre', 'family': 'Aromático frutal', 'profile': 'Manzana, bergamota, canela, maderas', 'priority': 'A', 'aliases': 'Hayaati negro|Hayaati black'}, {'tube_name': 'Hayaati Gold Elixir', 'reference_house': 'Lattafa', 'reference_name': 'Hayaati Gold Elixir', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Unisex', 'family': 'Ambarado dulce', 'profile': 'Frutal, vainilla, cuero suave, almizcle', 'priority': 'B', 'aliases': 'Hayaati gold|Gold Elixir'}, {'tube_name': 'Hayaati Florence', 'reference_house': 'Lattafa', 'reference_name': 'Hayaati Florence', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Floral frutal', 'profile': 'Frutal, floral, dulce, femenino', 'priority': 'B', 'aliases': 'Florence|Hayaati rosa'}, {'tube_name': 'Haya', 'reference_house': 'Lattafa', 'reference_name': 'Haya', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Floral frutal', 'profile': 'Frutilla, champagne, flores, vainilla', 'priority': 'B', 'aliases': 'Haya Lattafa'}, {'tube_name': 'Afeef', 'reference_house': 'Lattafa', 'reference_name': 'Afeef', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Unisex', 'family': 'Floral amaderado', 'profile': 'Cítrico, floral, especiado, elegante', 'priority': 'B', 'aliases': 'Afeef Lattafa'}, {'tube_name': 'Sehr', 'reference_house': 'Lattafa', 'reference_name': 'Sehr', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Unisex', 'family': 'Ambarado gourmand', 'profile': 'Canela, almendra, vainilla, ámbar', 'priority': 'A', 'aliases': 'Sehr Lattafa'}, {'tube_name': 'Emaan', 'reference_house': 'Lattafa', 'reference_name': 'Emaan', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Floral blanco', 'profile': 'Azahar, jazmín, tuberosa, elegante', 'priority': 'B', 'aliases': 'Eman|Emaan Lattafa'}, {'tube_name': 'Raghba', 'reference_house': 'Lattafa', 'reference_name': 'Raghba', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Unisex', 'family': 'Oriental gourmand', 'profile': 'Vainilla, oud, azúcar, incienso', 'priority': 'A', 'aliases': 'Ragba|Raghba Lattafa'}, {'tube_name': 'Musamam White Intense', 'reference_house': 'Lattafa', 'reference_name': 'Musamam White Intense', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Unisex', 'family': 'Amaderado cremoso', 'profile': 'Coco, sándalo, especias, elegante', 'priority': 'A', 'aliases': 'Musamam white|Musamam blanco'}, {'tube_name': 'Maahir Legacy', 'reference_house': 'Lattafa', 'reference_name': 'Maahir Legacy', 'designer_house': 'Parfums de Marly', 'designer_name': 'Sedley', 'relation': 'Inspiración / comparación muy conocida', 'confidence': 'Alta', 'gender': 'Hombre', 'family': 'Aromático cítrico', 'profile': 'Lima, menta, lavanda, fresco', 'priority': 'A', 'aliases': 'Mahir Legacy|Maahir|Sedley'}, {'tube_name': 'Ana Abiyedh Rouge', 'reference_house': 'Lattafa', 'reference_name': 'Ana Abiyedh Rouge', 'designer_house': 'Maison Francis Kurkdjian', 'designer_name': 'Baccarat Rouge 540', 'relation': 'Inspiración / alternativa muy conocida', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Ámbar floral', 'profile': 'Dulce, azafrán, almizcle, amaderado', 'priority': 'A', 'aliases': 'Ana Abiyedh rojo|Ana rouge|BR540'}, {'tube_name': 'Rave Now Black', 'reference_house': 'Rave', 'reference_name': 'Now', 'designer_house': 'Creed', 'designer_name': 'Aventus', 'relation': 'ADN de piña tipo Aventus; no clon exacto', 'confidence': 'Media', 'gender': 'Hombre', 'family': 'Frutal amaderado', 'profile': 'Piña intensa, maderas, dulce', 'priority': 'A', 'aliases': 'Now Rave negro|Rave Now|Aventus'}, {'tube_name': 'Sakeena', 'reference_house': 'Lattafa', 'reference_name': 'Sakeena', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Frutal gourmand', 'profile': 'Fruta de la pasión, frambuesa, vainilla', 'priority': 'B', 'aliases': 'Sakina|Sakeena Lattafa'}, {'tube_name': 'Island Bliss', 'reference_house': 'Armaf', 'reference_name': 'Club de Nuit Island Bliss', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Tropical gourmand', 'profile': 'Coco, frutas, vainilla, playa', 'priority': 'A', 'aliases': 'Island bliss|CDN Island Bliss'}, {'tube_name': 'Yum Yum', 'reference_house': 'Armaf', 'reference_name': 'Yum Yum', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Frutal gourmand', 'profile': 'Cereza, frutos rojos, vainilla, dulce', 'priority': 'A', 'aliases': 'YumYum|Yum yam'}, {'tube_name': 'Ajwad', 'reference_house': 'Lattafa', 'reference_name': 'Ajwad', 'designer_house': 'Mancera', 'designer_name': 'Roses Vanille', 'relation': 'ADN similar / comparación frecuente', 'confidence': 'Media', 'gender': 'Unisex', 'family': 'Rosa dulce', 'profile': 'Rosa, frutas, vainilla, almizcle', 'priority': 'A', 'aliases': 'Ajwad Lattafa|Roses Vanille'}, {'tube_name': 'Nebras', 'reference_house': 'Lattafa', 'reference_name': 'Nebras', 'designer_house': 'Billie Eilish', 'designer_name': 'Eilish No. 1', 'relation': 'Inspiración / comparación muy conocida', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Gourmand vainilla', 'profile': 'Cacao, vainilla, frutos rojos, ámbar', 'priority': 'A+', 'aliases': 'Nebras Pride|Eilish'}, {'tube_name': 'Liam Grey', 'reference_house': 'Lattafa', 'reference_name': 'Liam Grey', 'designer_house': 'BDK Parfums', 'designer_name': 'Gris Charnel', 'relation': 'Inspiración / comparación muy conocida', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Amaderado especiado', 'profile': 'Higo, té negro, cardamomo, sándalo', 'priority': 'A', 'aliases': 'Liam gris|Gris Charnel'}, {'tube_name': 'Vintage Radio', 'reference_house': 'Lattafa', 'reference_name': 'Vintage Radio', 'designer_house': 'Initio', 'designer_name': 'Paragon', 'relation': 'Inspiración / comparación muy conocida', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Amaderado aromático', 'profile': 'Ciruela, palo santo, lavanda, cremoso', 'priority': 'A', 'aliases': 'Radio Vintage|Paragon'}, {'tube_name': 'Al Nashama Caprice', 'reference_house': 'Lattafa', 'reference_name': 'Al Nashama Caprice', 'designer_house': 'Yves Saint Laurent', 'designer_name': "La Nuit de L'Homme Bleu Électrique", 'relation': 'Inspiración / comparación muy conocida', 'confidence': 'Alta', 'gender': 'Hombre', 'family': 'Aromático especiado', 'profile': 'Cardamomo, lavanda, jengibre, sensual', 'priority': 'A', 'aliases': 'Nashama Caprice|Bleu Electrique'}, {'tube_name': 'Jean Lowe Immortel', 'reference_house': 'Maison Alhambra', 'reference_name': 'Jean Lowe Immortel', 'designer_house': 'Louis Vuitton', 'designer_name': "L'Immensité", 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Hombre', 'family': 'Cítrico ambarado', 'profile': 'Pomelo, jengibre, ámbar, limpio', 'priority': 'A', 'aliases': 'Immortal|Immortel|Limmensite'}, {'tube_name': 'Jean Lowe Ombre', 'reference_house': 'Maison Alhambra', 'reference_name': 'Jean Lowe Ombre', 'designer_house': 'Louis Vuitton', 'designer_name': 'Ombre Nomade', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Oud ambarado', 'profile': 'Oud, rosa, incienso, oscuro', 'priority': 'A', 'aliases': 'Jean Lowe Noir|Ombre Nomade'}, {'tube_name': 'Tobacco Touch', 'reference_house': 'Maison Alhambra', 'reference_name': 'Tobacco Touch', 'designer_house': 'Tom Ford', 'designer_name': 'Tobacco Vanille', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Tabaco vainilla', 'profile': 'Tabaco dulce, vainilla, cacao, especias', 'priority': 'A', 'aliases': 'Tobacco Vanille|Tabaco Touch'}, {'tube_name': 'Lovely Chèrie', 'reference_house': 'Maison Alhambra', 'reference_name': 'Lovely Chèrie', 'designer_house': 'Tom Ford', 'designer_name': 'Lost Cherry', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Gourmand cereza', 'profile': 'Cereza, almendra, licor, maderas', 'priority': 'A', 'aliases': 'Lovely Cherry|Lost Cherry|Cherie'}, {'tube_name': 'Toscano Leather', 'reference_house': 'Maison Alhambra', 'reference_name': 'Toscano Leather', 'designer_house': 'Tom Ford', 'designer_name': 'Tuscan Leather', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Cuero', 'profile': 'Cuero, frambuesa, azafrán, intenso', 'priority': 'B', 'aliases': 'Tuscan Leather|Toscano'}, {'tube_name': 'Bright Peach', 'reference_house': 'Maison Alhambra', 'reference_name': 'Bright Peach', 'designer_house': 'Tom Ford', 'designer_name': 'Bitter Peach', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Frutal dulce', 'profile': 'Durazno, ron, vainilla, sensual', 'priority': 'A', 'aliases': 'Bitter Peach|Peach'}, {'tube_name': 'Woody Oud', 'reference_house': 'Maison Alhambra', 'reference_name': 'Woody Oud', 'designer_house': 'Tom Ford', 'designer_name': 'Oud Wood', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Amaderado oud', 'profile': 'Oud limpio, cardamomo, sándalo', 'priority': 'B', 'aliases': 'Oud Wood|Woody'}, {'tube_name': 'Porto Neroli', 'reference_house': 'Maison Alhambra', 'reference_name': 'Porto Neroli', 'designer_house': 'Tom Ford', 'designer_name': 'Neroli Portofino', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Cítrico aromático', 'profile': 'Neroli, cítricos, limpio, verano', 'priority': 'B', 'aliases': 'Neroli Portofino|Porto'}, {'tube_name': 'Fabulo Intense', 'reference_house': 'Maison Alhambra', 'reference_name': 'Fabulo Intense', 'designer_house': 'Tom Ford', 'designer_name': 'Fucking Fabulous', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Cuero aromático', 'profile': 'Almendra, cuero, lavanda, tonka', 'priority': 'B', 'aliases': 'Fabulous|Fabulo'}, {'tube_name': 'Rose Petals', 'reference_house': 'Maison Alhambra', 'reference_name': 'Rose Petals', 'designer_house': 'Tom Ford', 'designer_name': 'Rose Prick', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Rosa especiada', 'profile': 'Rosa, pimienta, pachuli', 'priority': 'B', 'aliases': 'Rose Prick|Petals'}, {'tube_name': 'Barakkat Rouge 540', 'reference_house': 'Fragrance World', 'reference_name': 'Barakkat Rouge 540', 'designer_house': 'Maison Francis Kurkdjian', 'designer_name': 'Baccarat Rouge 540', 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Ámbar floral', 'profile': 'Azafrán, jazmín, ámbar, dulce', 'priority': 'A+', 'aliases': 'Barakat|Baccarat|BR540'}, {'tube_name': 'Cocktail Intense', 'reference_house': 'Fragrance World', 'reference_name': 'Cocktail Intense', 'designer_house': 'Kilian', 'designer_name': "Angels' Share", 'relation': 'Inspiración / dupe muy conocido', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Gourmand licoroso', 'profile': 'Canela, coñac, vainilla, cálido', 'priority': 'A', 'aliases': 'Cocktail|Angels Share'}, {'tube_name': 'Imperium', 'reference_house': 'Paris Corner Emir', 'reference_name': 'Imperium', 'designer_house': 'Roja Parfums', 'designer_name': 'Elysium Pour Homme', 'relation': 'Inspiración / comparación muy conocida', 'confidence': 'Alta', 'gender': 'Hombre', 'family': 'Cítrico aromático', 'profile': 'Pomelo, vetiver, maderas, fresco', 'priority': 'A', 'aliases': 'Emir Imperium|Elysium'}, {'tube_name': 'Cedrat Essence', 'reference_house': 'Paris Corner Emir', 'reference_name': 'Cedrat Essence', 'designer_house': 'Mancera', 'designer_name': 'Cedrat Boise', 'relation': 'Inspiración / comparación muy conocida', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Cítrico amaderado', 'profile': 'Cítricos, frutas, cuero, maderas', 'priority': 'B', 'aliases': 'Cedrat Boise|Cedrat'}, {'tube_name': 'Vibrant Vetiver Delight', 'reference_house': 'Paris Corner Emir', 'reference_name': 'Vibrant Vetiver Delight', 'designer_house': 'Byredo', 'designer_name': "Bal d'Afrique", 'relation': 'Inspiración / comparación muy conocida', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Cítrico vetiver', 'profile': 'Cítrico, vetiver, limpio, luminoso', 'priority': 'B', 'aliases': 'Vetiver Delight|Bal dAfrique'}, {'tube_name': 'Khair Pistachio', 'reference_house': 'Paris Corner', 'reference_name': 'Khair Pistachio', 'designer_house': 'Kayali', 'designer_name': 'Yum Pistachio Gelato 33', 'relation': 'Inspiración / comparación muy conocida', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Gourmand pistacho', 'profile': 'Pistacho, crema, marshmallow, dulce', 'priority': 'A+', 'aliases': 'Pistachio|Yum Pistachio'}, {'tube_name': 'Baccarat Rouge 540', 'reference_house': 'Referencia directa 35 ml', 'reference_name': 'Baccarat Rouge 540', 'designer_house': 'Maison Francis Kurkdjian', 'designer_name': 'Baccarat Rouge 540', 'relation': 'Nombre directo de la referencia', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Ámbar floral', 'profile': 'Azafrán, jazmín, ámbar, dulce', 'priority': 'A+', 'aliases': 'Baccarat|BR540'}, {'tube_name': 'Erba Pura', 'reference_house': 'Referencia directa 35 ml', 'reference_name': 'Erba Pura', 'designer_house': 'Xerjoff', 'designer_name': 'Erba Pura', 'relation': 'Nombre directo de la referencia', 'confidence': 'Alta', 'gender': 'Unisex', 'family': 'Frutal almizclado', 'profile': 'Frutas, cítricos, almizcle, vainilla', 'priority': 'A', 'aliases': 'Erba Pura Xerjoff|Erba'}, {'tube_name': 'Cauvage', 'reference_house': 'Genérico 35 ml', 'reference_name': 'Cauvage', 'designer_house': 'Dior', 'designer_name': 'Sauvage', 'relation': 'Inspiración nominal directa', 'confidence': 'Alta', 'gender': 'Hombre', 'family': 'Aromático azul', 'profile': 'Bergamota, ambroxan, especias, fresco', 'priority': 'A', 'aliases': 'Sauvage|Cauvage'}, {'tube_name': 'Cenale Nº 5', 'reference_house': 'Genérico 35 ml', 'reference_name': 'Cenale Nº 5', 'designer_house': 'Chanel', 'designer_name': 'Nº 5', 'relation': 'Inspiración nominal directa', 'confidence': 'Alta', 'gender': 'Mujer', 'family': 'Aldehídico floral', 'profile': 'Aldehídos, flores, clásico, elegante', 'priority': 'B', 'aliases': 'Chanel 5|Chanel Nº5|Cenale'}, {'tube_name': 'Odor Epic', 'reference_house': 'Genérico 35 ml', 'reference_name': 'Odor Epic', 'designer_house': 'Amouage', 'designer_name': 'Epic (ADN)', 'relation': 'Inspiración nominal / orientativa', 'confidence': 'Media', 'gender': 'Unisex', 'family': 'Oriental especiado', 'profile': 'Especias, incienso, maderas, intenso', 'priority': 'C', 'aliases': 'Epic Man|Epic Woman|Odor'}, {'tube_name': 'Gissah Calabria', 'reference_house': 'Gissah', 'reference_name': 'Calabria', 'designer_house': '', 'designer_name': '', 'relation': 'Referencia árabe directa; sin dupe 1:1 seguro', 'confidence': 'Orientativa', 'gender': 'Unisex', 'family': 'Frutal aromático', 'profile': 'Frutal, fresco, moderno', 'priority': 'A', 'aliases': 'Calabria|Gissa Calabria'}, {'tube_name': 'Soprano', 'reference_house': 'Referencia 35 ml', 'reference_name': 'Soprano', 'designer_house': 'Xerjoff', 'designer_name': 'Soprano', 'relation': 'Nombre usado como referencia; verificar lote', 'confidence': 'Media', 'gender': 'Unisex', 'family': 'Floral oriental', 'profile': 'Rosa, frutas, oud, dulce', 'priority': 'B', 'aliases': 'Xerjoff Soprano|Soprano'}, {'tube_name': 'Miracle', 'reference_house': 'Referencia 35 ml', 'reference_name': 'Miracle', 'designer_house': 'Lancôme', 'designer_name': 'Miracle', 'relation': 'Nombre usado como referencia; verificar lote', 'confidence': 'Media', 'gender': 'Mujer', 'family': 'Floral especiado', 'profile': 'Floral, fresco, especiado, femenino', 'priority': 'B', 'aliases': 'Lancome Miracle|Miracle'}, {'tube_name': 'Marshmallow', 'reference_house': 'Genérico 35 ml', 'reference_name': 'Marshmallow', 'designer_house': 'Kayali', 'designer_name': 'Yum Boujee Marshmallow 81 (ADN)', 'relation': 'ADN gourmand similar / orientativo', 'confidence': 'Media', 'gender': 'Mujer', 'family': 'Gourmand', 'profile': 'Marshmallow, frutilla, vainilla, dulce', 'priority': 'A', 'aliases': 'Malvavisco|Boujee Marshmallow'}, {'tube_name': 'Andaleeb', 'reference_house': 'Asdaaf', 'reference_name': 'Andaleeb', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Floral frutal', 'profile': 'Cítrico, floral, dulce, amaderado', 'priority': 'A', 'aliases': 'Andaleb|Andaleeb Asdaaf'}, {'tube_name': 'Rose Secret', 'reference_house': 'Referencia 35 ml', 'reference_name': 'Rose Secret', 'designer_house': '', 'designer_name': '', 'relation': 'Sin equivalencia 1:1 segura', 'confidence': 'Orientativa', 'gender': 'Mujer', 'family': 'Floral rosa', 'profile': 'Rosa, dulce, femenino, suave', 'priority': 'A', 'aliases': 'Secret Rose|Rose secret'}]

def _norm35(value):
    s = str(value or '').strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def fragrance_library_df():
    """Biblioteca viva: después de la primera migración, Google Sheets/productos es la fuente editable."""
    try:
        df = qdf(
            """
            SELECT id, sku, brand, name, reference_house, reference_name,
                   inspired_house, inspired_name, similarity_relation,
                   similarity_confidence, gender, olfactory_family,
                   fragrance_profile, priority, aliases, avg_cost, sale_price,
                   min_stock, location, sellable, active, library_key
            FROM products
            WHERE library_item=1 AND product_type!='DECANT'
            ORDER BY CASE priority WHEN 'A+' THEN 1 WHEN 'A' THEN 2 WHEN 'B' THEN 3 WHEN 'C' THEN 4 ELSE 5 END,
                     name
            """
        )
        if not df.empty:
            out = pd.DataFrame({
                "tube_name": df["name"].fillna(""),
                "reference_house": df["reference_house"].fillna(""),
                "reference_name": df["reference_name"].fillna(""),
                "designer_house": df["inspired_house"].fillna(""),
                "designer_name": df["inspired_name"].fillna(""),
                "relation": df["similarity_relation"].fillna(""),
                "confidence": df["similarity_confidence"].fillna(""),
                "gender": df["gender"].fillna(""),
                "family": df["olfactory_family"].fillna(""),
                "profile": df["fragrance_profile"].fillna(""),
                "priority": df["priority"].fillna(""),
                "aliases": df["aliases"].fillna(""),
                "product_id": df["id"],
                "sku": df["sku"].fillna(""),
                "avg_cost": df["avg_cost"].fillna(0),
                "sale_price": df["sale_price"].fillna(0),
                "min_stock": df["min_stock"].fillna(0),
                "location": df["location"].fillna(""),
                "sellable": df["sellable"].fillna(1),
                "active": df["active"].fillna(1),
                "library_key": df["library_key"].fillna(""),
            })
            return out
    except Exception:
        pass
    return pd.DataFrame(FRAGRANCE_LIBRARY).copy()


def _meta_keys35(meta):
    keys = [meta.get('tube_name',''), meta.get('reference_name','')]
    keys += [x.strip() for x in str(meta.get('aliases','')).split('|') if x.strip()]
    return [_norm35(x) for x in keys if _norm35(x)]


def match_fragrance35(name, brand=''):
    """Fallback semántico sobre la biblioteca base para reconocer nombres heredados."""
    name_n = _norm35(name)
    full_n = _norm35(f'{brand} {name}')
    for meta in FRAGRANCE_LIBRARY:
        keys = _meta_keys35(meta)
        if name_n and name_n in keys:
            return meta
    best = None
    best_len = 0
    for meta in FRAGRANCE_LIBRARY:
        for k in _meta_keys35(meta):
            if len(k) >= 4 and k in full_n and len(k) > best_len:
                best, best_len = meta, len(k)
    return best


def _product_reference_text35(row):
    vals = []
    for c in [
        'brand','name','sku','line','reference_house','reference_name','inspired_house','inspired_name',
        'similarity_relation','similarity_confidence','gender','olfactory_family','fragrance_profile',
        'priority','aliases','origin_country','category','location'
    ]:
        try:
            vals.append(str(row.get(c,'') or ''))
        except Exception:
            pass
    if not any(vals):
        return fragrance_search_text35(row.get('name',''), row.get('brand',''))
    return ' '.join(vals)


def fragrance_search_text35(name, brand=''):
    m = match_fragrance35(name, brand)
    if not m:
        return ''
    return ' '.join(str(m.get(k,'') or '') for k in [
        'tube_name','reference_house','reference_name','designer_house','designer_name',
        'relation','gender','family','profile','aliases'
    ])


def fragrance_reference_label35(name, brand=''):
    try:
        r = get_conn().execute(
            """SELECT inspired_house,inspired_name,similarity_relation
               FROM products WHERE name=? AND product_type!='DECANT'
               ORDER BY library_item DESC, active DESC LIMIT 1""",
            (name,),
        ).fetchone()
        if r and str(r['inspired_name'] or '').strip():
            original = f"{r['inspired_house'] or ''} {r['inspired_name'] or ''}".strip()
            relation = str(r['similarity_relation'] or '').strip()
            return f"{original}{' · ' + relation if relation else ''}"
    except Exception:
        pass
    m = match_fragrance35(name, brand)
    if not m:
        return 'Sin referencia cargada'
    if m.get('designer_name'):
        return f"{m.get('designer_house','')} {m.get('designer_name','')} · {m.get('relation','')}".strip()
    return f"{m.get('reference_house','')} {m.get('reference_name','')} · {m.get('relation','')}".strip()


def auto_sku35(name):
    base = re.sub(r'[^A-Z0-9]+','-', _norm35(name).upper()).strip('-')[:18] or 'PERFUME'
    digest = hashlib.sha1(str(name).encode('utf-8')).hexdigest()[:5].upper()
    return f'35-{base}-{digest}'


def enrich_35ml_df(df):
    if df is None or df.empty:
        return df
    out = df.copy()
    if 'inspired_name' in out.columns:
        out['Referencia 35 ml'] = out.get('reference_name', pd.Series('', index=out.index)).fillna('')
        out['Inspirado / similar a'] = out.apply(
            lambda r: (f"{r.get('inspired_house','') or ''} {r.get('inspired_name','') or ''}".strip() or '—'), axis=1
        )
        out['Perfil'] = out.get('fragrance_profile', pd.Series('', index=out.index)).fillna('')
        return out
    metas = [match_fragrance35(r.get('name',''), r.get('brand','')) for _, r in out.iterrows()]
    out['Referencia 35 ml'] = [m.get('reference_name','') if m else '' for m in metas]
    out['Inspirado / similar a'] = [
        (f"{m.get('designer_house','')} {m.get('designer_name','')}".strip() if m and m.get('designer_name') else '—')
        for m in metas
    ]
    out['Perfil'] = [m.get('profile','') if m else '' for m in metas]
    return out


LIBRARY_SEED_VERSION = '35ML-MASTER-2026-09-A'


def _catalog_key35(value):
    s = _norm35(value)
    s = re.sub(r'\b(35\s*ml|35ml|tubito|perfume|fragancia)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def _unique_sku35(conn, wanted, keep_id=None):
    base = str(wanted or '').strip() or uid('35-')
    candidate = base
    n = 2
    while True:
        row = conn.execute('SELECT id FROM products WHERE sku=?', (candidate,)).fetchone()
        if not row or (keep_id is not None and int(row['id']) == int(keep_id)):
            return candidate
        candidate = f"{base[:22]}-{n}"
        n += 1


def ensure_library_catalog35():
    """
    Integra la biblioteca completa al catálogo real una sola vez.
    - Si una fragancia ya existe, conserva su ID, costos, precios y stock.
    - Si no existe, crea la ficha con stock 0.
    - No vuelve a pisar ediciones manuales una vez migrada.
    """
    conn = get_conn()
    seeded = str(scalar("SELECT value FROM settings WHERE key='library_seed_version'", default='') or '')
    existing = qdf("SELECT * FROM products WHERE product_type!='DECANT'")
    present_keys = set(existing.library_key.fillna('').astype(str)) if ('library_key' in existing.columns and not existing.empty) else set()
    missing_keys = {_norm35(m['tube_name']) for m in FRAGRANCE_LIBRARY} - present_keys
    if seeded == LIBRARY_SEED_VERSION and not missing_keys:
        return

    backend = get_backend()
    old_sync = backend.get('sync_enabled', True)
    backend['sync_enabled'] = False
    changed = False
    try:
        rows = [dict(r) for r in conn.execute("SELECT * FROM products WHERE product_type!='DECANT'").fetchall()]
        claimed_ids = set()

        for meta in FRAGRANCE_LIBRARY:
            lib_key = _norm35(meta.get('tube_name',''))
            exact_keys = {_catalog_key35(meta.get('tube_name','')), _catalog_key35(meta.get('reference_name',''))}
            exact_keys.discard('')

            keeper = None
            # Stable library_key has priority.
            for r in rows:
                if str(r.get('library_key') or '') == lib_key:
                    keeper = r
                    break
            # Then exact/canonical name matching only. We deliberately avoid designer aliases here.
            if keeper is None:
                candidates = []
                for r in rows:
                    if int(r.get('id') or 0) in claimed_ids:
                        continue
                    nk = _catalog_key35(r.get('name',''))
                    matched = nk in exact_keys
                    if not matched and nk:
                        matched = any(len(ek) >= 5 and (nk.endswith(ek) or nk.startswith(ek)) for ek in exact_keys)
                    if matched:
                        candidates.append(r)
                if candidates:
                    candidates.sort(
                        key=lambda r: (
                            1 if int(r.get('active') or 0) else 0,
                            max(0.0, current_stock(int(r['id']))),
                            safe_float(r.get('sale_price',0)),
                        ),
                        reverse=True,
                    )
                    keeper = candidates[0]

            ref_line = f"{meta.get('reference_house','')} {meta.get('reference_name','')}".strip()
            if keeper is not None:
                pid = int(keeper['id'])
                claimed_ids.add(pid)
                conn.execute(
                    """UPDATE products SET
                       size_ml=?,
                       brand=CASE WHEN TRIM(COALESCE(brand,''))='' THEN 'Tubito 35 ml' ELSE brand END,
                       line=CASE WHEN TRIM(COALESCE(line,''))='' THEN ? ELSE line END,
                       gender=CASE WHEN TRIM(COALESCE(gender,''))='' THEN ? ELSE gender END,
                       concentration=CASE WHEN TRIM(COALESCE(concentration,''))='' THEN 'EDP' ELSE concentration END,
                       category=CASE WHEN TRIM(COALESCE(category,''))='' THEN 'Tubito 35 ml' ELSE category END,
                       olfactory_family=CASE WHEN TRIM(COALESCE(olfactory_family,''))='' THEN ? ELSE olfactory_family END,
                       reference_house=?,reference_name=?,inspired_house=?,inspired_name=?,
                       similarity_relation=?,similarity_confidence=?,fragrance_profile=?,priority=?,aliases=?,
                       library_key=?,library_item=1,active=1
                       WHERE id=?""",
                    (
                        FIXED_SIZE_ML, ref_line, meta.get('gender','Unisex'), meta.get('family',''),
                        meta.get('reference_house',''), meta.get('reference_name',''), meta.get('designer_house',''),
                        meta.get('designer_name',''), meta.get('relation',''), meta.get('confidence',''),
                        meta.get('profile',''), meta.get('priority',''), meta.get('aliases',''), lib_key, pid,
                    ),
                )
                changed = True
                continue

            wanted_sku = _unique_sku35(conn, auto_sku35(meta.get('tube_name','')))
            conn.execute(
                """INSERT INTO products(
                   sku,barcode,brand,name,line,gender,concentration,size_ml,origin_country,category,product_type,
                   olfactory_family,reference_house,reference_name,inspired_house,inspired_name,
                   similarity_relation,similarity_confidence,fragrance_profile,priority,aliases,library_key,library_item,
                   top_notes,heart_notes,base_notes,season,use_time,batch_code,supplier_id,avg_cost,sale_price,
                   wholesale_price,reseller_price,promo_price,min_stock,location,sellable,active,created_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    wanted_sku,'','Tubito 35 ml',meta.get('tube_name',''),ref_line,meta.get('gender','Unisex'),'EDP',
                    FIXED_SIZE_ML,'','Tubito 35 ml','PERFUME',meta.get('family',''),meta.get('reference_house',''),
                    meta.get('reference_name',''),meta.get('designer_house',''),meta.get('designer_name',''),
                    meta.get('relation',''),meta.get('confidence',''),meta.get('profile',''),meta.get('priority',''),
                    meta.get('aliases',''),lib_key,1,'','','','','','',None,0,0,0,0,0,0,'',1,1,now_iso()
                ),
            )
            rows.append(dict(conn.execute('SELECT * FROM products WHERE id=last_insert_rowid()').fetchone()))
            changed = True

        conn.execute(
            """INSERT INTO settings(key,value) VALUES('library_seed_version',?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (LIBRARY_SEED_VERSION,),
        )
        conn.commit()
        backend['sync_enabled'] = old_sync
        if changed or seeded != LIBRARY_SEED_VERSION:
            sync_tables(['products','settings'])
    except Exception:
        conn.rollback()
        backend['sync_enabled'] = old_sync
        raise


def _product_editor_frame35(df, include_stock=True, compact=False):
    if df is None or df.empty:
        return pd.DataFrame()
    work = df.copy()
    if 'stock' not in work.columns:
        work['stock'] = work['id'].apply(current_stock)
    inspired = work.apply(lambda r: f"{r.get('inspired_house','') or ''} {r.get('inspired_name','') or ''}".strip(), axis=1)
    base = pd.DataFrame({
        'ID': work['id'].astype(int),
        'SKU': work['sku'].fillna(''),
        'Marca / fabricante': work['brand'].fillna(''),
        'Nombre': work['name'].fillna(''),
        'Casa de referencia': work.get('reference_house', pd.Series('',index=work.index)).fillna(''),
        'Nombre de referencia': work.get('reference_name', pd.Series('',index=work.index)).fillna(''),
        'Marca original / similar': work.get('inspired_house', pd.Series('',index=work.index)).fillna(''),
        'Perfume original / similar': work.get('inspired_name', pd.Series('',index=work.index)).fillna(''),
        'Relación': work.get('similarity_relation', pd.Series('',index=work.index)).fillna(''),
        'Confianza': work.get('similarity_confidence', pd.Series('',index=work.index)).fillna(''),
        'Género': work['gender'].fillna(''),
        'Familia olfativa': work['olfactory_family'].fillna(''),
        'Perfil olfativo': work.get('fragrance_profile', pd.Series('',index=work.index)).fillna(''),
        'Nivel': work.get('priority', pd.Series('',index=work.index)).fillna(''),
        'Alias / búsquedas': work.get('aliases', pd.Series('',index=work.index)).fillna(''),
        'Concentración': work['concentration'].fillna(''),
        'País / origen': work['origin_country'].fillna(''),
        'Categoría': work['category'].fillna(''),
        'Referencia / línea': work['line'].fillna(''),
        'Código de barras': work['barcode'].fillna(''),
        'Costo': work['avg_cost'].fillna(0).astype(float),
        'Precio venta': work['sale_price'].fillna(0).astype(float),
        'Mayorista': work['wholesale_price'].fillna(0).astype(float),
        'Revendedor': work['reseller_price'].fillna(0).astype(float),
        'Promocional': work['promo_price'].fillna(0).astype(float),
        'Stock actual': work['stock'].fillna(0).astype(float),
        'Stock objetivo': work['stock'].fillna(0).astype(float),
        'Stock mínimo': work['min_stock'].fillna(0).astype(float),
        'Ubicación': work['location'].fillna(''),
        'Notas de salida': work['top_notes'].fillna(''),
        'Notas de corazón': work['heart_notes'].fillna(''),
        'Notas de fondo': work['base_notes'].fillna(''),
        'Temporada': work['season'].fillna(''),
        'Uso': work['use_time'].fillna(''),
        'Batch': work['batch_code'].fillna(''),
        'Proveedor ID': work['supplier_id'],
        'Vendible': work['sellable'].fillna(1).astype(bool),
        'Activo': work['active'].fillna(1).astype(bool),
    })
    if not include_stock:
        base = base.drop(columns=['Stock actual','Stock objetivo'])
    if compact:
        keep = ['ID','SKU','Marca / fabricante','Nombre','Perfume original / similar','Género','Costo','Precio venta','Stock actual','Stock objetivo','Stock mínimo','Ubicación','Vendible','Activo']
        base = base[[c for c in keep if c in base.columns]]
    return base


_PRODUCT_UI_TO_DB35 = {
    'SKU':'sku','Marca / fabricante':'brand','Nombre':'name','Casa de referencia':'reference_house',
    'Nombre de referencia':'reference_name','Marca original / similar':'inspired_house',
    'Perfume original / similar':'inspired_name','Relación':'similarity_relation','Confianza':'similarity_confidence',
    'Género':'gender','Familia olfativa':'olfactory_family','Perfil olfativo':'fragrance_profile','Nivel':'priority',
    'Alias / búsquedas':'aliases','Concentración':'concentration','País / origen':'origin_country','Categoría':'category',
    'Referencia / línea':'line','Código de barras':'barcode','Costo':'avg_cost','Precio venta':'sale_price',
    'Mayorista':'wholesale_price','Revendedor':'reseller_price','Promocional':'promo_price','Stock mínimo':'min_stock',
    'Ubicación':'location','Notas de salida':'top_notes','Notas de corazón':'heart_notes','Notas de fondo':'base_notes',
    'Temporada':'season','Uso':'use_time','Batch':'batch_code','Proveedor ID':'supplier_id','Vendible':'sellable','Activo':'active',
}


def _clean_editor_value35(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, (np.bool_, bool)):
        return int(bool(v))
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def save_product_editor35(edited):
    if edited is None or edited.empty:
        return 0, 0
    conn = get_conn()
    backend = get_backend()
    old_sync = backend.get('sync_enabled', True)
    backend['sync_enabled'] = False
    updated = 0
    adjusted = 0
    try:
        for _, row in edited.iterrows():
            pid = int(row['ID'])
            fields = []
            values = []
            for ui, dbcol in _PRODUCT_UI_TO_DB35.items():
                if ui not in edited.columns:
                    continue
                fields.append(f'{dbcol}=?')
                values.append(_clean_editor_value35(row[ui]))
            # 35 ml es una regla del negocio, no una celda editable.
            fields += ['size_ml=?']
            values += [FIXED_SIZE_ML]
            if fields:
                conn.execute(f"UPDATE products SET {','.join(fields)} WHERE id=?", tuple(values+[pid]))
                updated += 1
            if 'Stock objetivo' in edited.columns:
                target = max(0.0, safe_float(row['Stock objetivo']))
                current = current_stock(pid)
                delta = target - current
                if abs(delta) > 1e-9:
                    cost = max(0.0, safe_float(row.get('Costo', scalar('SELECT avg_cost FROM products WHERE id=?',(pid,),0))))
                    conn.execute(
                        """INSERT INTO inventory_moves(date,product_id,move_type,qty,unit_cost,reference_type,reference_id,notes,user_name,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?)""",
                        (today_iso(),pid,'AJUSTE_EDICION',delta,cost,'EDICION',None,'Ajuste desde editor',current_user().get('username','local'),now_iso())
                    )
                    adjusted += 1
        conn.commit()
        backend['sync_enabled'] = old_sync
        sync_tables(['products','inventory_moves'] if adjusted else ['products'])
        audit_event(
            "EDICION_CATALOGO","PRODUCT","MULTIPLE",
            after={"fichas_actualizadas":updated,"ajustes_stock":adjusted}
        )
        return updated, adjusted
    except Exception:
        conn.rollback()
        backend['sync_enabled'] = old_sync
        raise


def _primary_key_for_table(table):
    info = get_conn().execute(f'PRAGMA table_info({table})').fetchall()
    pks = [r[1] for r in info if int(r[5] or 0) > 0]
    return pks[0] if pks else None


def save_generic_table35(table, edited):
    """Editor directo avanzado para cualquier tabla ya existente, sin permitir cambiar su clave primaria."""
    if table not in TABLE_ORDER or edited is None or edited.empty:
        return 0
    pk = _primary_key_for_table(table)
    if not pk or pk not in edited.columns:
        raise ValueError('La tabla no tiene una clave primaria editable de forma segura.')
    valid_cols = table_columns(table)
    cols = [c for c in edited.columns if c in valid_cols and c != pk]
    if not cols:
        return 0
    conn = get_conn()
    backend = get_backend()
    old_sync = backend.get('sync_enabled', True)
    backend['sync_enabled'] = False
    count = 0
    try:
        for _, row in edited.iterrows():
            pkv = _clean_editor_value35(row[pk])
            sets = ','.join(f'{c}=?' for c in cols)
            vals = [_clean_editor_value35(row[c]) for c in cols]
            conn.execute(f'UPDATE {table} SET {sets} WHERE {pk}=?', tuple(vals+[pkv]))
            count += 1
        conn.commit()
        backend['sync_enabled'] = old_sync
        sync_tables([table])
        audit_event(
            "EDICION_GLOBAL",table.upper(),"MULTIPLE",
            after={"registros_guardados":count}
        )
        return count
    except Exception:
        conn.rollback()
        backend['sync_enabled'] = old_sync
        raise


# La biblioteca deja de ser una lista separada: desde aquí forma parte del catálogo/inventario real.
try:
    ensure_library_catalog35()
except Exception as _library_error:
    st.error(f"No pude integrar la biblioteca 35 ml con el catálogo: {_library_error}")
    st.stop()



st.markdown(
    """
    <style>
    .format35-badge{display:inline-flex;gap:8px;align-items:center;padding:7px 11px;border-radius:999px;background:#f1e8df;border:1px solid #e6d5c4;color:#56354f;font-weight:800;font-size:.78rem;letter-spacing:.03em}
    .ref35{background:linear-gradient(135deg,#fffaf4,#f5edf2);border:1px solid #eadfd7;border-radius:18px;padding:16px 18px;margin:8px 0 14px 0;box-shadow:0 8px 24px rgba(40,20,30,.035)}
    .ref35 .r-title{font-size:1.05rem;font-weight:850;color:#221d24}.ref35 .r-big{font-size:1.25rem;font-weight:900;color:#56354f;margin:.2rem 0}.ref35 .r-sub{font-size:.88rem;color:#756b74}
    .guide-note{background:#fffdf9;border-left:4px solid #b88945;padding:12px 14px;border-radius:10px;color:#5e5660;font-size:.88rem;margin:.5rem 0 1rem}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.markdown(f"### ✦ {APP_NAME}")
    st.caption(BUSINESS_NAME)
    st.markdown('<span class="format35-badge">✦ FORMATO ÚNICO · 35 ML</span>', unsafe_allow_html=True)
    st.divider()
    pages = [
        "◎ Centro Ejecutivo",
        "✦ Control 360",
        "▣ Venta rápida",
        "◉ Ventas",
        "⌕ Biblioteca 35 ml",
        "◈ Catálogo",
        "▤ Inventario",
        "◆ Compras",
        "♙ Clientes",
        "♜ Vendedores",
        "◫ Reservas y pedidos",
        "↔ Cuentas corrientes",
        "$ Caja y finanzas",
        "◇ Promociones y marketing",
        "↻ Reposición",
        "✦ Centro inteligente",
        "▥ Reportes",
        "✎ Edición global",
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
        "Tu negocio de 35 ml en una sola vista: ventas, unidades, rentabilidad, inventario, caja y reposición.",
        BUSINESS_NAME.upper(),
    )

    # Pulso del día
    _today = today_iso()
    _tomorrow = (date.today()+timedelta(days=1)).isoformat()
    _today_sales = period_sales(_today, _tomorrow)
    _today_rev = safe_float(_today_sales.total.sum()) if not _today_sales.empty else 0
    _today_profit = safe_float(_today_sales.profit.sum()) if not _today_sales.empty else 0
    _today_tickets = len(_today_sales)
    _inv_pulse = stock_df()
    _critical = len(_inv_pulse[(_inv_pulse.min_stock>0) & (_inv_pulse.stock <= _inv_pulse.min_stock) & (_inv_pulse.active==1)]) if not _inv_pulse.empty else 0
    p1,p2,p3,p4 = st.columns(4)
    with p1: pro_kpi("VENTAS HOY", money(_today_rev), f"{_today_tickets} ticket(s)", "plum")
    with p2: pro_kpi("GANANCIA HOY", money(_today_profit), "Resultado bruto del día", "green")
    with p3: pro_kpi("STOCK CRÍTICO", str(_critical), "SKUs en mínimo o menos", "rose")
    with p4:
        _clients_total = safe_int(scalar("SELECT COUNT(*) FROM customers WHERE active=1", default=0))
        pro_kpi("CLIENTES", str(_clients_total), "Base comercial activa", "gold")
    st.markdown("")

    month = st.date_input("Mes a analizar", value=date.today().replace(day=1), key="dash_month")
    start, end = date_range_for_month(month)
    sales = period_sales(start, end)
    prev_month_end = start
    prev_month_start = (start - timedelta(days=1)).replace(day=1)
    prev_sales = period_sales(prev_month_start, prev_month_end)

    revenue = safe_float(sales.total.sum()) if not sales.empty else 0
    units = reconciled_sold_units(start, end)
    profit = reconciled_profit(start, end, revenue)
    tickets = len(sales)
    avg_ticket = revenue / tickets if tickets else 0
    margin = profit/revenue*100 if revenue else 0
    prev_revenue = safe_float(prev_sales.total.sum()) if not prev_sales.empty else 0
    growth = ((revenue-prev_revenue)/prev_revenue*100) if prev_revenue else 0
    stock_cost, stock_retail, stock_potential = inventory_value()

    # Totales globales del negocio (independientes del mes seleccionado).
    total_sold_global = safe_float(scalar(
        "SELECT COALESCE(SUM(total),0) FROM sales WHERE status='Completada'",
        default=0
    ))
    total_commercial_value = total_sold_global + stock_retail

    # Unidades físicas disponibles actualmente en inventario.
    # Usamos el mismo criterio que el módulo Inventario: solo stock positivo
    # de productos activos, para que ambos paneles siempre coincidan.
    stock_units = safe_float(_inv_pulse.stock.clip(lower=0).sum()) if not _inv_pulse.empty else 0
    cash_balance = safe_float(scalar(
        "SELECT COALESCE(SUM(CASE WHEN direction='INGRESO' THEN amount ELSE -amount END),0) FROM cash_moves", default=0
    ))
    stock_plus_cash = stock_retail + cash_balance

    receivables = safe_float(scalar(
        "SELECT COALESCE(SUM(debit-credit),0) FROM account_ledger WHERE entity_type='CUSTOMER'", default=0
    ))
    payables = safe_float(scalar(
        "SELECT COALESCE(SUM(credit-debit),0) FROM account_ledger WHERE entity_type='SUPPLIER'", default=0
    ))

    # ========================================================
    # CONCILIACIÓN HISTÓRICA DE UNIDADES Y COSTOS
    # ========================================================
    acquired_units, acquired_cost = reconciled_acquisition_totals()

    # Dos fuentes distintas para detectar inconsistencias:
    # A) detalle de ventas (sale_items)
    sold_items_global = reconciled_sold_units()
    # B) movimientos físicos de inventario generados por ventas
    sold_moves_global = reconciled_sold_units()
    sold_moves_month = reconciled_sold_units(start, end)
    cogs_moves_global = reconciled_sales_cogs()

    other_out_df = qdf(
        """SELECT move_type AS tipo, COALESCE(SUM(-qty),0) AS unidades
           FROM inventory_moves
           WHERE qty<0 AND move_type<>'VENTA'
           GROUP BY move_type
           HAVING ABS(SUM(qty))>0.000001
           ORDER BY unidades DESC"""
    )
    other_out_units = safe_float(other_out_df["unidades"].sum()) if not other_out_df.empty else 0

    # Diferencias entre cada línea de venta y su salida física de inventario.
    _audit_items = qdf(
        """SELECT s.id AS venta_id, s.date AS fecha, si.product_id,
                  SUM(si.qty) AS unidades_detalle
           FROM sale_items si
           JOIN sales s ON s.id=si.sale_id
           WHERE s.status='Completada'
           GROUP BY s.id,s.date,si.product_id"""
    )
    _audit_moves = qdf(
        """SELECT s.id AS venta_id, s.date AS fecha, im.product_id,
                  SUM(-im.qty) AS unidades_inventario
           FROM inventory_moves im
           JOIN sales s ON s.id=im.reference_id
           WHERE im.reference_type='SALE'
             AND im.move_type='VENTA'
             AND im.qty<0
             AND s.status='Completada'
           GROUP BY s.id,s.date,im.product_id"""
    )
    if _audit_items.empty and _audit_moves.empty:
        sales_unit_mismatches = pd.DataFrame()
    else:
        sales_unit_mismatches = pd.merge(
            _audit_items,
            _audit_moves,
            on=["venta_id","fecha","product_id"],
            how="outer"
        )
        sales_unit_mismatches["unidades_detalle"] = pd.to_numeric(
            sales_unit_mismatches.get("unidades_detalle", 0), errors="coerce"
        ).fillna(0)
        sales_unit_mismatches["unidades_inventario"] = pd.to_numeric(
            sales_unit_mismatches.get("unidades_inventario", 0), errors="coerce"
        ).fillna(0)
        sales_unit_mismatches["diferencia"] = (
            sales_unit_mismatches["unidades_inventario"] -
            sales_unit_mismatches["unidades_detalle"]
        )
        sales_unit_mismatches = sales_unit_mismatches[
            sales_unit_mismatches["diferencia"].abs() > 0.000001
        ].copy()
        if not sales_unit_mismatches.empty:
            _prod_audit = qdf("SELECT id AS product_id,sku,brand,name FROM products")
            sales_unit_mismatches = sales_unit_mismatches.merge(
                _prod_audit, on="product_id", how="left"
            )

    # ========================================================
    # DIRECCIÓN DEL NEGOCIO
    # ========================================================
    realized_profit_global = total_sold_global - cogs_moves_global
    realized_margin_global = (
        realized_profit_global / total_sold_global * 100
        if total_sold_global else 0
    )
    operating_equity = cash_balance + receivables + stock_cost - payables
    commercial_potential = cash_balance + receivables + stock_retail - payables
    potential_total_result = realized_profit_global + stock_potential
    investment_coverage = (
        total_sold_global / acquired_cost * 100
        if acquired_cost else 0
    )
    unit_sell_through = (
        sold_items_global / acquired_units * 100
        if acquired_units else 0
    )

    # --------------------------
    # Período seleccionado
    # --------------------------
    executive_section(
        "MES SELECCIONADO",
        "Qué pasó en el período que elegiste. El resto del tablero muestra la salud acumulada del negocio.",
        "#56354f",
    )
    m1,m2,m3,m4 = st.columns(4)
    with m1:
        pro_kpi("FACTURACIÓN", money(revenue), f"{growth:+.1f}% vs mes anterior", "plum")
    with m2:
        pro_kpi("GANANCIA DEL PERÍODO", money(profit), f"Margen {margin:.1f}% · meta {TARGET_MARGIN:.0f}%", "green" if margin >= TARGET_MARGIN else "gold")
    with m3:
        pro_kpi("UNIDADES VENDIDAS", f"{units:g}", f"{tickets} ticket(s)", "blue")
    with m4:
        pro_kpi("TICKET PROMEDIO", money(avg_ticket), "Facturación promedio por ticket", "gold")

    # --------------------------
    # VENDÍ
    # --------------------------
    executive_section(
        "VENDÍ",
        "Resultado acumulado real: lo que ya salió del inventario y lo que el negocio ya generó.",
        "#2f765a",
    )
    v1,v2,v3,v4 = st.columns(4)
    with v1:
        pro_kpi("FACTURACIÓN ACUMULADA", money(total_sold_global), "Ventas completadas registradas", "plum")
    with v2:
        pro_kpi("UNIDADES VENDIDAS", f"{sold_items_global:g}", f"{unit_sell_through:.1f}% de las unidades ingresadas", "blue")
    with v3:
        pro_kpi("GANANCIA REALIZADA", money(realized_profit_global), "Facturación − costo de mercadería vendida", "green")
    with v4:
        pro_kpi("MARGEN REALIZADO", pct(realized_margin_global), f"Costo vendido {money(cogs_moves_global)}", "green" if realized_margin_global >= TARGET_MARGIN else "gold")

    # --------------------------
    # TENGO
    # --------------------------
    executive_section(
        "TENGO",
        "Mercadería que hoy sigue físicamente en el negocio y cuánto representa a costo y a precio de venta.",
        "#486a8a",
    )
    h1,h2,h3,h4 = st.columns(4)
    with h1:
        pro_kpi("UNIDADES EN STOCK", f"{stock_units:g}", "Perfumes de 35 ml disponibles", "blue")
    with h2:
        pro_kpi("STOCK A COSTO", money(stock_cost), "Capital actualmente inmovilizado", "rose")
    with h3:
        pro_kpi("STOCK A PRECIO DE VENTA", money(stock_retail), "Facturación posible del stock actual", "gold")
    with h4:
        pro_kpi("GANANCIA POTENCIAL DEL STOCK", money(stock_potential), "Si vendés el stock a los precios cargados", "green")

    # --------------------------
    # MI PLATA
    # --------------------------
    executive_section(
        "MI PLATA",
        "Separación entre capital histórico, capital ya liberado por ventas y patrimonio operativo actual.",
        "#b88945",
    )
    p1,p2,p3,p4 = st.columns(4)
    with p1:
        pro_kpi("CAPITAL INVERTIDO HISTÓRICO", money(acquired_cost), f"{acquired_units:g} unidades ingresadas", "plum")
    with p2:
        pro_kpi("CAPITAL RECUPERADO · COSTO", money(cogs_moves_global), f"Costo de {sold_items_global:g} unidades ya vendidas", "green")
    with p3:
        pro_kpi("CAPITAL INMOVILIZADO", money(stock_cost), f"Costo de las {stock_units:g} unidades actuales", "rose")
    with p4:
        pro_kpi("PATRIMONIO OPERATIVO", money(operating_equity), "Caja + cobrar + stock a costo − pagar", "blue")

    # Recupero visual.
    st.markdown(
        f"""
        <div class="insight">
          <b>Cobertura de inversión por ventas:</b> {investment_coverage:.1f}% ·
          facturaste {money(total_sold_global)} frente a {money(acquired_cost)} de costo histórico ingresado.
          <br><span style="color:#887c82;font-size:.82rem">
          Es un indicador comercial de avance, no reemplaza el resultado contable.
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, max(0.0, investment_coverage / 100.0)))

    # --------------------------
    # PUEDO GANAR
    # --------------------------
    executive_section(
        "PUEDO GANAR",
        "Escenario comercial con el stock actual. No confunde patrimonio real con ventas que todavía no ocurrieron.",
        "#9b5365",
    )
    g1,g2,g3,g4 = st.columns(4)
    with g1:
        pro_kpi("GANANCIA FUTURA POSIBLE", money(stock_potential), "Margen contenido en el stock actual", "green")
    with g2:
        pro_kpi("RESULTADO POTENCIAL TOTAL", money(potential_total_result), "Ganancia realizada + ganancia potencial", "green")
    with g3:
        pro_kpi("POTENCIAL COMERCIAL", money(commercial_potential), "Caja + cobrar + stock a venta − pagar", "blue")
    with g4:
        pro_kpi("CAJA TEÓRICA", money(cash_balance), f"Por cobrar {money(receivables)} · por pagar {money(payables)}", "plum")

    # ========================================================
    # INTELIGENCIA DE STOCK Y ROTACIÓN
    # ========================================================
    executive_section(
        "INTELIGENCIA DE STOCK",
        "Qué se mueve, qué está quieto, qué reponer y cuánto dinero tenés inmovilizado en mercadería lenta.",
        "#486a8a",
    )

    with st.expander("Parámetros del motor de reposición", expanded=False):
        par1,par2 = st.columns(2)
        slow_days = int(par1.number_input(
            "Considerar lento después de N días sin venta",
            min_value=1, max_value=120, value=7, step=1,
            key="exec_slow_days"
        ))
        target_days = int(par2.number_input(
            "Cobertura objetivo para reposición (días)",
            min_value=3, max_value=90, value=14, step=1,
            key="exec_target_days"
        ))

    bi, bi_meta = product_intelligence_df(slow_days=slow_days, target_days=target_days)

    if bi.empty:
        st.info("Todavía no hay productos activos para analizar.")
    else:
        stocked = bi[bi.stock_pos > 0].copy()
        sold_history = bi[bi.units_sold > 0].copy()
        slow = bi[bi.slow].copy()
        sold_out = bi[bi.sold_out_with_history].copy()
        never_sold_stock = bi[(bi.stock_pos > 0) & (bi.units_sold <= 0)].copy()
        reorder = bi[bi.reorder_qty > 0].copy()
        pending_no_stock = bi[(bi.pending_demand > 0) & (bi.stock_pos <= 0)].copy()

        stocked_skus = int(len(stocked))
        slow_count = int(len(slow))
        sold_out_count = int(len(sold_out))
        never_sold_count = int(len(never_sold_stock))
        slow_capital = float(slow.stock_cost_value.sum()) if not slow.empty else 0.0
        reorder_units = float(reorder.reorder_qty.sum()) if not reorder.empty else 0.0
        reorder_investment = float(reorder.reorder_investment.sum()) if not reorder.empty else 0.0
        coverage_days = float(bi_meta.get("coverage_days", 0) or 0)

        sales_total_identified = float(sold_history.units_sold.sum()) if not sold_history.empty else 0.0
        top10_units = float(
            sold_history.sort_values("units_sold", ascending=False).head(10).units_sold.sum()
        ) if sales_total_identified else 0.0
        top10_share = (top10_units / sales_total_identified * 100) if sales_total_identified else 0.0

        k1,k2,k3,k4 = st.columns(4)
        with k1:
            pro_kpi("FRAGANCIAS CON STOCK", str(stocked_skus), f"{stock_units:g} unidades físicas", "blue")
        with k2:
            pro_kpi("AGOTADAS QUE YA VENDIERON", str(sold_out_count), "Prioridad natural de reposición", "rose" if sold_out_count else "green")
        with k3:
            pro_kpi("LENTAS / SIN MOVIMIENTO", str(slow_count), f"{never_sold_count} nunca vendidas con stock", "gold" if slow_count else "green")
        with k4:
            pro_kpi("CAPITAL EN STOCK LENTO", money(slow_capital), f"Sin venta hace {slow_days}+ días o nunca vendidas", "rose" if slow_capital else "green")

        k5,k6,k7,k8 = st.columns(4)
        with k5:
            cov_txt = f"{coverage_days:.1f} días" if coverage_days > 0 else "Sin velocidad"
            pro_kpi("COBERTURA ESTIMADA", cov_txt, f"Velocidad observada en {bi_meta.get('days_observed',1)} día(s)", "blue")
        with k6:
            pro_kpi("CONCENTRACIÓN TOP 10", pct(top10_share), "Participación de los 10 perfumes más vendidos", "plum")
        with k7:
            pro_kpi("UNIDADES A REPONER", f"{reorder_units:g}", f"Objetivo de cobertura: {target_days} días", "gold" if reorder_units else "green")
        with k8:
            pro_kpi("INVERSIÓN DE REPOSICIÓN", money(reorder_investment), "Estimación usando costo promedio actual", "rose" if reorder_investment else "green")

        tab_move, tab_reorder, tab_slow, tab_opportunities = st.tabs(
            ["Qué se vende", "Qué reponer", "Qué frena capital", "Oportunidades"]
        )

        with tab_move:
            top_products = bi[bi.units_sold > 0].sort_values(
                ["units_sold","revenue"], ascending=False
            ).head(15).copy()
            if top_products.empty:
                st.info("Todavía no hay ventas identificadas por producto.")
            else:
                top_products["Perfume"] = top_products["display_name"]
                top_products["Original / similar"] = top_products["original_similar"]
                top_products["Vendidas"] = top_products["units_sold"]
                top_products["Stock"] = top_products["stock_pos"]
                top_products["Facturación"] = top_products["revenue"]
                top_products["Ganancia"] = top_products["profit"]
                top_products["Última venta"] = top_products["last_sale_date"].fillna("—")
                st.dataframe(
                    top_products[
                        ["Perfume","Original / similar","Vendidas","Stock","Facturación","Ganancia","Última venta"]
                    ],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Facturación": st.column_config.NumberColumn("Facturación", format="$ %.0f"),
                        "Ganancia": st.column_config.NumberColumn("Ganancia", format="$ %.0f"),
                    },
                )
                unidentified = max(0.0, sold_items_global - sales_total_identified)
                if unidentified > 0:
                    st.caption(
                        f"Hay {unidentified:g} unidad(es) del cierre histórico conciliado sin perfume individual identificado; "
                        "no se asignan a ningún producto para no inventar el ranking."
                    )

        with tab_reorder:
            if reorder.empty:
                st.success("Con los parámetros actuales no hay reposiciones urgentes.")
            else:
                rr = reorder.sort_values(
                    ["pending_demand","reorder_qty","units_recent"],
                    ascending=False
                ).head(25).copy()
                rr["Perfume"] = rr["display_name"]
                rr["Original / similar"] = rr["original_similar"]
                rr["Stock"] = rr["stock_pos"]
                rr["Vendidas recientes"] = rr["units_recent"]
                rr["Demanda reservada"] = rr["pending_demand"]
                rr["Comprar"] = rr["reorder_qty"]
                rr["Inversión"] = rr["reorder_investment"]
                st.dataframe(
                    rr[
                        ["Perfume","Original / similar","Stock","Vendidas recientes","Demanda reservada","Comprar","Inversión"]
                    ],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Inversión": st.column_config.NumberColumn("Inversión", format="$ %.0f"),
                    },
                )
                st.caption(
                    "Comprar = cobertura objetivo por velocidad reciente, respetando stock mínimo y reservas activas."
                )

        with tab_slow:
            if slow.empty:
                st.success("No hay capital atrapado en productos lentos con este criterio.")
            else:
                ss = slow.sort_values("stock_cost_value", ascending=False).head(25).copy()
                ss["Perfume"] = ss["display_name"]
                ss["Original / similar"] = ss["original_similar"]
                ss["Stock"] = ss["stock_pos"]
                ss["Vendidas"] = ss["units_sold"]
                ss["Días sin venta"] = ss["days_since_sale"].replace(9999, np.nan)
                ss["Capital inmovilizado"] = ss["stock_cost_value"]
                ss["Valor a venta"] = ss["stock_retail_value"]
                st.dataframe(
                    ss[
                        ["Perfume","Original / similar","Stock","Vendidas","Días sin venta","Capital inmovilizado","Valor a venta"]
                    ],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Capital inmovilizado": st.column_config.NumberColumn("Capital inmovilizado", format="$ %.0f"),
                        "Valor a venta": st.column_config.NumberColumn("Valor a venta", format="$ %.0f"),
                    },
                )
                st.caption("Estos productos no necesariamente son malos: son los primeros candidatos a impulsar antes de recomprar.")

        with tab_opportunities:
            # Demanda real sin stock.
            if not pending_no_stock.empty:
                st.markdown("#### Demanda real sin stock")
                pdem = pending_no_stock.sort_values("pending_demand", ascending=False).copy()
                pdem["Perfume"] = pdem["display_name"]
                pdem["Pedidos / reservas"] = pdem["pending_demand"]
                pdem["Original / similar"] = pdem["original_similar"]
                st.dataframe(
                    pdem[["Perfume","Original / similar","Pedidos / reservas"]],
                    use_container_width=True,
                    hide_index=True,
                )

            # Biblioteca A+ todavía no probada: oportunidad, no orden de compra.
            trial = bi[
                (bi.stock_pos <= 0)
                & (bi.units_sold <= 0)
                & (bi.priority.fillna("") == "A+")
            ].copy()
            if not trial.empty:
                st.markdown("#### Fragancias A+ de biblioteca todavía no probadas")
                trial["Perfume"] = trial["display_name"]
                trial["Original / similar"] = trial["original_similar"]
                trial["Género"] = trial["gender"].fillna("—")
                trial["Familia"] = trial["olfactory_family"].fillna("—")
                st.dataframe(
                    trial[["Perfume","Original / similar","Género","Familia"]].head(20),
                    use_container_width=True,
                    hide_index=True,
                )
                st.caption("Son oportunidades de testeo, no una recomendación automática de compra.")

    # ========================================================
    # MAPA COMERCIAL DE FRAGANCIAS
    # ========================================================
    executive_section(
        "MAPA COMERCIAL DE FRAGANCIAS",
        "Qué equivalencias, marcas de referencia, géneros y familias están generando movimiento real.",
        "#56354f",
    )

    if bi.empty or float(bi.units_sold.sum()) <= 0:
        st.info("Todavía faltan ventas por producto para construir el mapa comercial.")
    else:
        map1,map2,map3 = st.columns(3)

        with map1:
            st.markdown("#### Originales / inspiraciones")
            originals = (
                bi[(bi.units_sold > 0) & (bi.original_similar != "—")]
                .groupby("original_similar", as_index=False)["units_sold"].sum()
                .sort_values("units_sold", ascending=False)
                .head(10)
            )
            if originals.empty:
                st.caption("Sin equivalencias vendidas todavía.")
            else:
                st.bar_chart(
                    originals.set_index("original_similar")["units_sold"],
                    use_container_width=True
                )

        with map2:
            st.markdown("#### Marcas de referencia")
            brands = (
                bi[bi.units_sold > 0]
                .assign(Marca=bi["reference_house"].fillna("").replace("", "Sin definir"))
                .groupby("Marca", as_index=False)["units_sold"].sum()
                .sort_values("units_sold", ascending=False)
                .head(10)
            )
            st.bar_chart(
                brands.set_index("Marca")["units_sold"],
                use_container_width=True
            )

        with map3:
            st.markdown("#### Género")
            genders = (
                bi[bi.units_sold > 0]
                .assign(Genero=bi["gender"].fillna("").replace("", "Sin definir"))
                .groupby("Genero", as_index=False)["units_sold"].sum()
                .sort_values("units_sold", ascending=False)
            )
            st.bar_chart(
                genders.set_index("Genero")["units_sold"],
                use_container_width=True
            )

        fam = (
            bi[bi.units_sold > 0]
            .assign(Familia=bi["olfactory_family"].fillna("").replace("", "Sin definir"))
            .groupby("Familia", as_index=False)
            .agg(Unidades=("units_sold","sum"), Facturacion=("revenue","sum"))
            .sort_values(["Unidades","Facturacion"], ascending=False)
            .head(15)
        )
        if not fam.empty:
            st.markdown("#### Familias olfativas con mayor salida")
            st.dataframe(
                fam,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Facturacion": st.column_config.NumberColumn("Facturación", format="$ %.0f")
                },
            )

    # ========================================================
    # SIGUIENTE DECISIÓN
    # ========================================================
    executive_section(
        "SIGUIENTE DECISIÓN",
        "La app resume lo que merece atención ahora mismo, sin mezclar ventas potenciales con dinero real.",
        "#9b5365",
    )

    decision_lines = []
    if not bi.empty:
        if reorder_units > 0:
            decision_lines.append(
                f"<b>Reposición:</b> el motor propone {reorder_units:g} unidad(es), "
                f"con una inversión estimada de {money(reorder_investment)}."
            )
        if slow_capital > 0:
            decision_lines.append(
                f"<b>Capital lento:</b> {money(slow_capital)} está en fragancias sin movimiento reciente. "
                "Antes de recomprarlas, conviene moverlas."
            )
        if sold_out_count > 0:
            decision_lines.append(
                f"<b>Agotados con demanda demostrada:</b> {sold_out_count} fragancia(s) ya vendieron y hoy están en cero."
            )
        if not pending_no_stock.empty:
            decision_lines.append(
                f"<b>Demanda pendiente:</b> {int(len(pending_no_stock))} fragancia(s) tienen reserva/pedido y no tienen stock."
            )
    if margin and margin < TARGET_MARGIN:
        decision_lines.append(
            f"<b>Margen:</b> el período está en {margin:.1f}%, debajo de tu meta de {TARGET_MARGIN:.1f}%."
        )
    if receivables > 0:
        decision_lines.append(f"<b>Cobranza:</b> tenés {money(receivables)} pendientes de cobrar.")
    if payables > 0:
        decision_lines.append(f"<b>Pagos:</b> tenés {money(payables)} pendientes de pagar.")
    if not decision_lines:
        decision_lines.append("<b>Sin alertas críticas:</b> ventas, stock y caja no muestran una urgencia operativa evidente.")

    for line in decision_lines[:5]:
        st.markdown(f'<div class="insight">{line}</div>', unsafe_allow_html=True)

    # ========================================================
    # CONTROL DE CONSISTENCIA
    # ========================================================
    _unit_balance = acquired_units - sold_items_global
    _cost_balance = acquired_cost - cogs_moves_global

    with st.expander("Control interno de mercadería", expanded=False):
        c1,c2,c3 = st.columns(3)
        with c1:
            pro_kpi("INGRESADAS", f"{acquired_units:g}", money(acquired_cost), "blue")
        with c2:
            pro_kpi("VENDIDAS", f"{sold_items_global:g}", f"Costo {money(cogs_moves_global)}", "green")
        with c3:
            pro_kpi("EN STOCK", f"{stock_units:g}", f"Costo {money(stock_cost)}", "gold")

        if abs(_unit_balance - stock_units) < 0.000001 and abs(_cost_balance - stock_cost) < 0.01:
            st.success(
                f"Todo cierra: {acquired_units:g} − {sold_items_global:g} = {stock_units:g} unidades · "
                f"{money(acquired_cost)} − {money(cogs_moves_global)} = {money(stock_cost)}."
            )
        else:
            st.warning(
                f"Revisar: unidades teóricas {_unit_balance:g} vs stock {stock_units:g} · "
                f"costo teórico {money(_cost_balance)} vs stock a costo {money(stock_cost)}."
            )

    # ========================================================
    # OBJETIVO Y EVOLUCIÓN
    # ========================================================
    if MONTHLY_GOAL > 0:
        executive_section("OBJETIVO MENSUAL", "Avance contra la meta configurada.", "#b88945")
        progress = min(1.0, revenue / MONTHLY_GOAL)
        st.progress(progress)
        st.caption(f"{money(revenue)} de {money(MONTHLY_GOAL)} · {progress*100:.1f}%")

    executive_section(
        "EVOLUCIÓN",
        "Facturación, ganancia y canales del período seleccionado.",
        "#56354f",
    )
    c1, c2 = st.columns([1.35,1])
    with c1:
        st.markdown("#### Evolución de ventas")
        if sales.empty:
            st.info("Todavía no hay ventas para este período.")
        else:
            # La facturación diaria sí tiene fecha exacta. La ganancia total usa el
            # cierre histórico conciliado, cuya unidad corregida no tiene una fecha
            # individual confiable; por eso no inventamos su posición en la curva.
            daily = sales.groupby("date", as_index=False).agg(
                Facturación=("total","sum")
            )
            st.line_chart(
                daily.set_index("date")[["Facturación"]],
                use_container_width=True
            )

    with c2:
        st.markdown("#### Canales")
        if not sales.empty:
            ch = (
                sales.groupby("channel", as_index=False).total.sum()
                .sort_values("total", ascending=False)
            )
            st.bar_chart(
                ch.set_index("channel")["total"],
                use_container_width=True
            )
        else:
            st.info("Sin datos.")



# ============================================================
# PAGE: CONTROL 360
# ============================================================
elif page == "✦ Control 360":
    hero(
        "Control 360",
        "Una sala de mando para ver la salud del negocio, anticipar problemas, decidir compras, vender mejor y entender cada peso.",
        "DIRECCIÓN · DECISIÓN · CONTROL",
    )

    snap = business_health_snapshot()
    alerts_360 = business_alerts()
    forecast = forecast_sales()
    intel360, intel_meta360 = product_master_intelligence(slow_days=14,target_days=14)

    td0,td1 = today_iso(), (date.today()+timedelta(days=1)).isoformat()
    today_sales360 = period_sales(td0,td1)
    today_rev360 = safe_float(today_sales360.total.sum()) if not today_sales360.empty else 0
    today_profit360 = safe_float(today_sales360.profit.sum()) if not today_sales360.empty else 0
    today_units360 = safe_float(qdf(
        """SELECT COALESCE(SUM(si.qty),0) q FROM sale_items si
           JOIN sales s ON s.id=si.sale_id
           WHERE s.date>=? AND s.date<? AND s.status='Completada'""",(td0,td1)
    ).iloc[0,0])

    st.markdown(
        f"""
        <div class="command-banner">
          <div class="status">● SALUD DEL NEGOCIO · {snap['status'].upper()}</div>
          <div class="headline">Hoy: {money(today_rev360)} vendidos · {today_units360:g} unidades · {money(today_profit360)} de ganancia</div>
          <div class="detail">{snap['status_text']} · Patrimonio operativo {money(snap['operating_equity'])} ·
          Stock {snap['stock_units']:g} unidades · Caja {money(snap['cash'])}.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    owner_mode = st.toggle("Modo dueño · mostrar solo lo indispensable", value=False, key="owner_mode_360")
    if owner_mode:
        executive_section("MODO DUEÑO","Ocho números para saber en menos de diez segundos cómo está el negocio.","#56354f")
        o1,o2,o3,o4 = st.columns(4)
        with o1: pro_kpi("SALUD",f"{snap['score']:.0f}/100",snap["status"],"green" if snap["score"]>=70 else "rose")
        with o2: pro_kpi("CAJA",money(snap["cash"]),"Disponible teórico","plum")
        with o3: pro_kpi("PATRIMONIO",money(snap["operating_equity"]),"Caja + cobrar + stock costo − pagar","blue")
        with o4: pro_kpi("GANANCIA REALIZADA",money(snap["realized_profit"]),f"Margen {snap['margin']:.1f}%","green")
        o5,o6,o7,o8 = st.columns(4)
        with o5: pro_kpi("STOCK",f"{snap['stock_units']:g}",money(snap["stock_cost"]),"gold")
        with o6: pro_kpi("CAPITAL LENTO",money(snap["slow_capital"]),"Mercadería sin movimiento","rose" if snap["slow_capital"] else "green")
        with o7: pro_kpi("PRÓXIMOS 30 DÍAS",money(forecast["30"]),"Proyección por ritmo reciente","blue")
        with o8: pro_kpi("POTENCIAL TOTAL",money(snap["potential_total_profit"]),"Realizado + potencial del stock","green")
        st.markdown("### Qué merece tu atención")
        for klass,msg in alerts_360[:6]:
            st.markdown(f'<div class="alert-row {klass}">{msg}</div>',unsafe_allow_html=True)
        st.stop()

    tabs360 = st.tabs([
        "Estado",
        "Ventas visuales",
        "Productos",
        "Simuladores",
        "Asistente de venta",
        "Clientes",
        "QR y etiquetas",
        "Control y auditoría",
    ])

    with tabs360[0]:
        a,b = st.columns([1,3])
        with a:
            st.markdown(
                f'<div class="health-ring" style="--health:{snap["score"]:.0f}%"><span>{snap["score"]:.0f}</span></div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='text-align:center;font-weight:850;margin-top:.5rem'>{snap['status']}</div>"
                f"<div style='text-align:center;color:#82757d;font-size:.8rem'>{snap['status_text']}</div>",
                unsafe_allow_html=True
            )
        with b:
            executive_section("HOY TENÉS","Dinero real y mercadería real, separados de lo que todavía no vendiste.","#b88945")
            h1,h2,h3,h4 = st.columns(4)
            with h1: pro_kpi("CAJA",money(snap["cash"]),"Saldo teórico","plum")
            with h2: pro_kpi("STOCK A COSTO",money(snap["stock_cost"]),f"{snap['stock_units']:g} unidades","blue")
            with h3: pro_kpi("POR COBRAR",money(snap["receivables"]),"Derechos de cobro","gold")
            with h4: pro_kpi("PATRIMONIO OPERATIVO",money(snap["operating_equity"]),"Neto operativo","green")

        executive_section("MAPA DEL DINERO","Dónde está el valor económico actual del negocio.","#486a8a")
        if go is not None:
            _money_values=[max(0,snap["cash"]),max(0,snap["receivables"]),max(0,snap["stock_cost"])]
            fig=go.Figure(go.Treemap(
                labels=["Activos operativos","Caja","Por cobrar","Stock a costo"],
                parents=["","Activos operativos","Activos operativos","Activos operativos"],
                values=[sum(_money_values)]+_money_values,
                branchvalues="total",
                root=dict(color="white"),
                textinfo="label+value+percent parent"
            ))
            fig.update_layout(height=360,margin=dict(l=5,r=5,t=5,b=5))
            st.plotly_chart(fig,use_container_width=True)
            if snap["payables"]>0:
                st.caption(f"El mapa muestra activos positivos. Cuentas por pagar: {money(snap['payables'])}; se descuentan en Patrimonio operativo.")
        else:
            st.dataframe(pd.DataFrame({
                "Componente":["Caja","Por cobrar","Stock a costo","Por pagar"],
                "Valor":[snap["cash"],snap["receivables"],snap["stock_cost"],-snap["payables"]]
            }),use_container_width=True,hide_index=True)

        executive_section("SI VENDIERAS TODO HOY","Escenario teórico: no se presenta como dinero actual.","#2f765a")
        s1,s2,s3,s4=st.columns(4)
        with s1: pro_kpi("FACTURACIÓN DEL STOCK",money(snap["stock_retail"]),"A precios actuales","gold")
        with s2: pro_kpi("GANANCIA DEL STOCK",money(snap["stock_potential"]),"Venta − costo actual","green")
        with s3: pro_kpi("POTENCIAL COMERCIAL",money(snap["commercial_potential"]),"Caja + cobrar + stock venta − pagar","blue")
        with s4: pro_kpi("RESULTADO POTENCIAL TOTAL",money(snap["potential_total_profit"]),"Realizado + potencial","green")

        executive_section("CENTRO DE ALERTAS","Solo cosas que requieren una decisión o revisión.","#9b5365")
        for klass,msg in alerts_360:
            st.markdown(f'<div class="alert-row {klass}">{msg}</div>',unsafe_allow_html=True)

        executive_section("¿DE DÓNDE SALE ESTE NÚMERO?","Elegí un KPI y la app te muestra su fórmula y componentes.","#56354f")
        metric_name=st.selectbox(
            "Explicar",
            ["Patrimonio operativo","Potencial comercial","Ganancia realizada","Ganancia potencial","Capital histórico"],
            key="explain_kpi_360"
        )
        formula,parts,result=explain_kpi(metric_name)
        st.markdown(f"**Fórmula:** `{formula}`")
        expdf=pd.DataFrame(parts,columns=["Componente","Importe"])
        st.dataframe(expdf,use_container_width=True,hide_index=True,column_config={"Importe":st.column_config.NumberColumn("Importe",format="$ %.0f")})
        st.success(f"Resultado: {money(result)}")

    with tabs360[1]:
        executive_section("CALENDARIO DE VENTAS","Cuanto más intensa la celda, más facturación tuvo ese día.","#56354f")
        lookback=int(st.select_slider("Ventana",options=[28,56,84,112,168],value=112,key="heat_days"))
        daily=sales_daily_frame(lookback)
        if go is not None and not daily.empty:
            d=daily.copy()
            d["weekday"]=d.date.dt.weekday
            d["weekday_name"]=d.date.dt.day_name().map({
                "Monday":"Lun","Tuesday":"Mar","Wednesday":"Mié","Thursday":"Jue",
                "Friday":"Vie","Saturday":"Sáb","Sunday":"Dom"
            })
            d["week_start"]=d["date"]-pd.to_timedelta(d["weekday"],unit="D")
            piv=d.pivot_table(index="weekday_name",columns="week_start",values="revenue",aggfunc="sum",fill_value=0)
            order=["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
            piv=piv.reindex([x for x in order if x in piv.index])
            fig=go.Figure(data=go.Heatmap(
                z=piv.values,x=[pd.Timestamp(x).strftime("%d/%m") for x in piv.columns],y=piv.index,
                colorbar=dict(title="Ventas"),hovertemplate="%{y} · semana %{x}<br>$ %{z:,.0f}<extra></extra>"
            ))
            fig.update_layout(height=330,margin=dict(l=20,r=20,t=20,b=20))
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.dataframe(daily,use_container_width=True,hide_index=True)

        executive_section("HORAS Y DÍAS QUE MÁS VENDEN","Se calcula usando la hora real de creación de cada ticket.","#486a8a")
        rawh=qdf("""SELECT created_at,total FROM sales WHERE status='Completada' AND created_at IS NOT NULL AND created_at<>''""")
        if rawh.empty:
            st.info("Todavía no hay horas de venta suficientes.")
        else:
            rawh["dt"]=pd.to_datetime(rawh.created_at,errors="coerce")
            rawh=rawh.dropna(subset=["dt"])
            rawh["hora"]=rawh["dt"].dt.hour
            rawh["dia"]=rawh["dt"].dt.dayofweek
            names={0:"Lun",1:"Mar",2:"Mié",3:"Jue",4:"Vie",5:"Sáb",6:"Dom"}
            rawh["dia_name"]=rawh.dia.map(names)
            mat=rawh.pivot_table(index="dia_name",columns="hora",values="total",aggfunc="sum",fill_value=0)
            mat=mat.reindex([x for x in ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"] if x in mat.index])
            if go is not None:
                fig=go.Figure(go.Heatmap(z=mat.values,x=mat.columns,y=mat.index,hovertemplate="%{y} · %{x}:00<br>$ %{z:,.0f}<extra></extra>"))
                fig.update_layout(height=330,margin=dict(l=20,r=20,t=20,b=20))
                st.plotly_chart(fig,use_container_width=True)
            else:
                st.dataframe(mat,use_container_width=True)

        executive_section("LÍNEA DE TIEMPO FINANCIERA","Ventas, compras y gastos para entender cómo fue cambiando el negocio.","#b88945")
        timeline=financial_timeline_df(120)
        if timeline.empty:
            st.info("Sin movimientos suficientes.")
        elif px is not None:
            fig=px.scatter(timeline,x="date",y="Importe",size=np.maximum(np.abs(timeline.Importe),1),symbol="Tipo",hover_name="Detalle")
            fig.add_hline(y=0,line_width=1,line_dash="dot")
            fig.update_layout(height=390,margin=dict(l=20,r=20,t=20,b=20),legend_title_text="")
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.dataframe(timeline,use_container_width=True,hide_index=True)

        executive_section("PRONÓSTICO","Proyección simple y transparente basada en el ritmo ponderado de los últimos 7, 14 y 30 días.","#2f765a")
        f1,f2,f3,f4=st.columns(4)
        with f1: pro_kpi("RITMO DIARIO",money(forecast["daily"]),f"Tendencia 7d {forecast['trend']:+.1f}%","blue")
        with f2: pro_kpi("PRÓXIMOS 7 DÍAS",money(forecast["7"]),"Escenario base","green")
        with f3: pro_kpi("PRÓXIMOS 15 DÍAS",money(forecast["15"]),"Escenario base","green")
        with f4: pro_kpi("PRÓXIMOS 30 DÍAS",money(forecast["30"]),"Escenario base","green")

        scenarios=pd.DataFrame({"Escenario":["Conservador","Base","Fuerte"],"Factor":[0.75,1.0,1.25]})
        scenarios["7 días"]=scenarios.Factor*forecast["7"]
        scenarios["15 días"]=scenarios.Factor*forecast["15"]
        scenarios["30 días"]=scenarios.Factor*forecast["30"]
        st.dataframe(
            scenarios[["Escenario","7 días","15 días","30 días"]],
            use_container_width=True,hide_index=True,
            column_config={
                "7 días":st.column_config.NumberColumn("7 días",format="$ %.0f"),
                "15 días":st.column_config.NumberColumn("15 días",format="$ %.0f"),
                "30 días":st.column_config.NumberColumn("30 días",format="$ %.0f"),
            }
        )

    with tabs360[2]:
        if intel360.empty:
            st.info("No hay productos para analizar.")
        else:
            executive_section("MAPA DE PRODUCTOS ESTRELLA","Ventas y margen juntos: permite distinguir estrellas, volumen con poco margen, nichos rentables y productos débiles.","#2f765a")
            quad=intel360[(intel360.units_sold>0)|(intel360.stock_pos>0)].copy()
            if px is not None and not quad.empty:
                quad["Perfume"]=quad["display_name"]
                quad["Tamaño"]=np.maximum(quad["revenue"],1000)
                fig=px.scatter(
                    quad,x="units_sold",y="current_margin",size="Tamaño",
                    hover_name="Perfume",hover_data=["stock_pos","commercial_score","rotation_index","days_to_stockout"],
                )
                fig.add_hline(y=TARGET_MARGIN,line_dash="dot")
                if len(quad):
                    fig.add_vline(x=float(quad.units_sold.median()),line_dash="dot")
                fig.update_layout(height=470,margin=dict(l=20,r=20,t=20,b=20),xaxis_title="Unidades vendidas",yaxis_title="Margen %")
                st.plotly_chart(fig,use_container_width=True)

            executive_section("RANKING INTELIGENTE","Puntaje 0–100 combinando ventas, ganancia, velocidad, margen y demanda pendiente.","#56354f")
            rank=intel360.sort_values("commercial_score",ascending=False).head(30).copy()
            rank["Perfume"]=rank["display_name"]
            rank["Original / similar"]=rank["original_similar"]
            rank["Puntaje"]=rank["commercial_score"]
            rank["Rotación"]=rank["rotation_index"]
            rank["Vendidas"]=rank["units_sold"]
            rank["Stock"]=rank["stock_pos"]
            rank["Margen"]=rank["current_margin"]
            rank["Agota en días"]=rank["days_to_stockout"]
            rank["Precio sugerido"]=rank["suggested_price"]
            st.dataframe(
                rank[["Perfume","Original / similar","Puntaje","Rotación","Vendidas","Stock","Margen","Agota en días","Precio sugerido"]],
                use_container_width=True,hide_index=True,height=520,
                column_config={
                    "Puntaje":st.column_config.ProgressColumn("Puntaje",min_value=0,max_value=100,format="%.0f"),
                    "Rotación":st.column_config.ProgressColumn("Rotación",min_value=0,max_value=100,format="%.0f"),
                    "Margen":st.column_config.NumberColumn("Margen",format="%.1f%%"),
                    "Agota en días":st.column_config.NumberColumn("Agota en días",format="%.1f"),
                    "Precio sugerido":st.column_config.NumberColumn("Precio sugerido",format="$ %.0f"),
                }
            )
            _identified_units=safe_float(intel360["units_sold"].sum())
            _recon_gap=max(0.0,reconciled_sold_units()-_identified_units)
            if _recon_gap>0:
                st.caption(
                    f"El cierre histórico incluye {_recon_gap:g} unidad(es) conciliada(s) sin producto individual identificado. "
                    "No se asignan artificialmente a ningún perfume, por eso no alteran el ranking."
                )

            executive_section("EDAD Y AGOTAMIENTO","Anticipa qué stock envejece y qué perfume puede quedarse sin unidades.","#9b5365")
            aged=intel360[intel360.stock_pos>0].sort_values(["stock_age_days","stock_cost_value"],ascending=False).copy()
            aged["Perfume"]=aged["display_name"]
            aged["Edad aprox."]=aged["stock_age_days"]
            aged["Capital"]=aged["stock_cost_value"]
            aged["Agota en días"]=aged["days_to_stockout"]
            st.dataframe(
                aged[["Perfume","stock_pos","Edad aprox.","days_since_sale","Capital","Agota en días"]].head(35),
                use_container_width=True,hide_index=True,
                column_config={"Capital":st.column_config.NumberColumn("Capital",format="$ %.0f")}
            )
            old_capital=float(aged.loc[aged["stock_age_days"]>=30,"stock_cost_value"].sum())
            if old_capital>0:
                st.warning(f"Hay {money(old_capital)} en stock cuya última entrada fue hace 30+ días.")

            executive_section("ESTANTERÍA VIRTUAL","Vista rápida de las fragancias con stock. El color representa la familia olfativa.","#b88945")
            shelf=intel360[intel360.stock_pos>0].sort_values(["location","commercial_score"],ascending=[True,False]).head(60)
            html='<div class="shelf">'
            for _,r in shelf.iterrows():
                bg=family_color(r.get("olfactory_family",""))
                ref=str(r.get("original_similar") or "—")
                html+=f"""<div class="shelf-item" style="border-top:4px solid {bg}">
                    <div class="nm">{r["display_name"]}</div>
                    <div class="ref">{ref}</div>
                    <span class="family-chip" style="background:{bg}">{r.get("olfactory_family") or "Sin familia"}</span>
                    <div class="qty">{safe_float(r["stock_pos"]):g} u.</div>
                    <div class="mini">{r.get("location") or "Sin ubicación"} · {money(r.get("sale_price",0))}</div>
                </div>"""
            html+='</div>'
            st.markdown(html,unsafe_allow_html=True)

            executive_section("MAPA DE EQUIVALENCIAS","Tubito → perfume original o referencia similar.","#486a8a")
            eq=intel360.copy()
            eq=eq[(eq.original_similar!="—")].copy()
            eq["Tubito"]=eq["display_name"]
            eq["Original / similar"]=eq["original_similar"]
            eq["Familia"]=eq["olfactory_family"].fillna("—")
            eq["Género"]=eq["gender"].fillna("—")
            eq["Stock"]=eq["stock_pos"]
            eq["Vendidas"]=eq["units_sold"]
            st.dataframe(eq[["Tubito","Original / similar","Familia","Género","Stock","Vendidas"]].sort_values("Vendidas",ascending=False),use_container_width=True,hide_index=True,height=480)

            executive_section("COMPARADOR","Elegí hasta tres fragancias y comparalas lado a lado.","#56354f")
            labels={r["display_name"]:int(r["id"]) for _,r in intel360.iterrows()}
            cmp_names=st.multiselect("Perfumes a comparar",list(labels.keys()),max_selections=3,key="compare_360")
            if cmp_names:
                cmp=intel360[intel360.id.isin([labels[x] for x in cmp_names])].copy()
                rows=[]
                for _,r in cmp.iterrows():
                    rows.append({
                        "Perfume":r["display_name"],"Original":r["original_similar"],
                        "Familia":r.get("olfactory_family") or "—","Género":r.get("gender") or "—",
                        "Stock":r["stock_pos"],"Vendidas":r["units_sold"],"Margen %":r["current_margin"],
                        "Rotación":r["rotation_index"],"Precio":r["sale_price"],"Puntaje":r["commercial_score"],
                    })
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    with tabs360[3]:
        executive_section("COMPRA INTELIGENTE","Decidí por cantidad o por presupuesto. El motor prioriza demanda demostrada, agotados, velocidad y cobertura.","#b88945")
        sm1,sm2,sm3=st.columns(3)
        mode=sm1.radio("Objetivo",["Presupuesto","100 unidades","Cantidad personalizada"],horizontal=False,key="alloc_mode")
        if mode=="Presupuesto":
            budget=sm2.number_input("Presupuesto disponible",min_value=0.0,value=200000.0,step=10000.0,key="alloc_budget")
            units_target=0
        elif mode=="100 unidades":
            budget=sm2.number_input("Presupuesto máximo",min_value=0.0,value=300000.0,step=10000.0,key="alloc_budget100")
            units_target=100
        else:
            budget=sm2.number_input("Presupuesto máximo",min_value=0.0,value=200000.0,step=10000.0,key="alloc_budget_custom")
            units_target=int(sm3.number_input("Unidades objetivo",min_value=1,value=50,step=1,key="alloc_units_custom"))
        only_proven=st.checkbox("Priorizar únicamente perfumes con ventas o demanda demostrada",value=True,key="alloc_proven")
        allocation=allocate_purchase_budget(budget,units_target,only_proven)
        if allocation.empty:
            st.info("No encontré una asignación compatible con presupuesto, costos y datos actuales.")
        else:
            inv_alloc=float(allocation["Inversión"].sum())
            units_alloc=int(allocation["Comprar"].sum())
            aa1,aa2,aa3=st.columns(3)
            aa1.metric("Unidades sugeridas",units_alloc)
            aa2.metric("Inversión",money(inv_alloc))
            aa3.metric("Saldo de presupuesto",money(max(0,budget-inv_alloc)))
            st.dataframe(
                allocation[["Perfume","Original / similar","stock_pos","units_sold","Comprar","Inversión","Stock después"]],
                use_container_width=True,hide_index=True,
                column_config={"Inversión":st.column_config.NumberColumn("Inversión",format="$ %.0f")}
            )
            if st.button("Preparar esta reposición en Compras",type="primary",use_container_width=True,key="prepare_alloc"):
                st.session_state.purchase_cart=[
                    {
                        "product_id":int(r.id),
                        "label":product_label(r),
                        "qty":float(r["Comprar"]),
                        "unit_price":float(r.avg_cost),
                    }
                    for _,r in allocation.iterrows() if safe_float(r["Comprar"])>0
                ]
                st.success("Reposición preparada. Entrá a Compras para revisar proveedor, envío y confirmar.")

        executive_section("SIMULADOR DE PRECIO","Probá un precio antes de tocar el catálogo.","#2f765a")
        if not intel360.empty:
            pmap={r["display_name"]:int(r["id"]) for _,r in intel360.iterrows()}
            ps1,ps2,ps3=st.columns([2,1,1])
            pn=ps1.selectbox("Perfume",list(pmap.keys()),key="price_sim_prod")
            pr=intel360[intel360.id==pmap[pn]].iloc[0]
            npv=ps2.number_input("Nuevo precio",min_value=0.0,value=float(pr.sale_price),step=100.0,key="price_sim_value")
            qsim=ps3.number_input("Unidades a simular",min_value=1.0,value=max(1.0,float(pr.stock_pos)),step=1.0,key="price_sim_qty")
            margin_new=((npv-safe_float(pr.avg_cost))/npv*100) if npv else 0
            profit_new=(npv-safe_float(pr.avg_cost))*qsim
            pp1,pp2,pp3,pp4=st.columns(4)
            pp1.metric("Costo",money(pr.avg_cost))
            pp2.metric("Margen nuevo",pct(margin_new))
            pp3.metric("Ganancia simulada",money(profit_new))
            pp4.metric("Precio sugerido",money(pr.suggested_price))
            if margin_new<TARGET_MARGIN:
                st.error(f"Este precio deja un margen de {margin_new:.1f}%, debajo de la meta de {TARGET_MARGIN:.1f}%.")
            else:
                st.success("El precio supera el margen objetivo.")
            sb1,sb2=st.columns(2)
            if sb1.button("Guardar precio simulado",use_container_width=True,key="save_sim_price"):
                before_price=safe_float(pr.sale_price)
                execute("UPDATE products SET sale_price=? WHERE id=?",(npv,int(pr.id)))
                audit_event("CAMBIO_PRECIO","PRODUCT",int(pr.id),before={"precio":before_price},after={"precio":npv})
                st.success("Precio actualizado en Catálogo, Inventario y Venta rápida.")
                st.rerun()
            if sb2.button("Aplicar precio sugerido",use_container_width=True,key="save_suggested_price"):
                before_price=safe_float(pr.sale_price)
                execute("UPDATE products SET sale_price=? WHERE id=?",(safe_float(pr.suggested_price),int(pr.id)))
                audit_event("CAMBIO_PRECIO_SUGERIDO","PRODUCT",int(pr.id),before={"precio":before_price},after={"precio":safe_float(pr.suggested_price)})
                st.success("Precio sugerido aplicado.")
                st.rerun()

        executive_section("DETECTOR DE PRECIO Y MARGEN","Productos cuyo precio necesita atención.","#9b5365")
        if not intel360.empty:
            risky=intel360[
                ((intel360.stock_pos>0)&((intel360.avg_cost<=0)|(intel360.sale_price<=0)))
                | ((intel360.sale_price>0)&(intel360.avg_cost>0)&(intel360.current_margin<TARGET_MARGIN))
            ].copy()
            if risky.empty:
                st.success("No hay precios con riesgo evidente.")
            else:
                risky["Perfume"]=risky["display_name"]
                risky["Margen"]=risky["current_margin"]
                risky["Sugerido"]=risky["suggested_price"]
                st.dataframe(
                    risky[["Perfume","avg_cost","sale_price","Margen","Sugerido","stock_pos"]],
                    use_container_width=True,hide_index=True,
                    column_config={
                        "avg_cost":st.column_config.NumberColumn("Costo",format="$ %.0f"),
                        "sale_price":st.column_config.NumberColumn("Venta",format="$ %.0f"),
                        "Sugerido":st.column_config.NumberColumn("Sugerido",format="$ %.0f"),
                        "Margen":st.column_config.NumberColumn("Margen",format="%.1f%%"),
                    }
                )

    with tabs360[4]:
        executive_section("EL CLIENTE PIDE…","Describí lo que busca con palabras normales: original, dulce, noche, mujer, vainilla, Sauvage, etc.","#56354f")
        customers360=qdf("SELECT id,name,phone FROM customers WHERE active=1 ORDER BY name")
        customer_opts360={"Sin cliente":None}
        if not customers360.empty:
            customer_opts360.update({f"{r['name']} · {r['phone'] or ''}":int(r.id) for _,r in customers360.iterrows()})
        as1,as2,as3,as4=st.columns([2.2,1,1,1])
        ask=as1.text_input("Qué está buscando",placeholder="Ej.: dulce femenino para noche, parecido a Good Girl...",key="assist_query")
        gen=as2.selectbox("Perfil",["","Mujer","Hombre","Unisex"],key="assist_gender")
        fam=as3.text_input("Familia",placeholder="gourmand",key="assist_family")
        bud=as4.number_input("Presupuesto máx.",min_value=0.0,value=0.0,step=500.0,key="assist_budget")
        client_label=st.selectbox("Cliente (opcional)",list(customer_opts360.keys()),key="assist_client")
        rec=sales_assistant_recommendations(ask,gen,fam,bud,customer_opts360[client_label],limit=8)
        if rec.empty:
            st.warning("No encontré una opción con stock que encaje suficientemente.")
            with st.form("unmet_demand_form",clear_on_submit=True):
                requested=st.text_input("Registrar lo que pidió",value=ask)
                channel=st.selectbox("Canal",["Local","WhatsApp","Instagram","Particular","Otro"])
                notes=st.text_input("Detalle adicional")
                save_req=st.form_submit_button("Guardar demanda no cubierta",type="primary")
            if save_req and requested.strip():
                execute(
                    """INSERT INTO demand_requests(date,customer_id,requested_text,matched_product_id,status,channel,notes,created_at)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (today_iso(),customer_opts360[client_label],requested.strip(),None,"Pendiente",channel,notes,now_iso())
                )
                audit_event("DEMANDA_NO_CUBIERTA","DEMAND","",after={"texto":requested,"cliente":customer_opts360[client_label]})
                st.success("Pedido registrado. Va a aparecer en oportunidades de compra.")
                st.rerun()
        else:
            st.caption("Ordenadas por coincidencia, comportamiento comercial, margen, rotación y disponibilidad.")
            for row_start in range(0,len(rec),4):
                cols=st.columns(4)
                for j,(_,r) in enumerate(rec.iloc[row_start:row_start+4].iterrows()):
                    ref=r["original_similar"]
                    famtxt=r.get("olfactory_family") or "Sin familia"
                    with cols[j]:
                        st.markdown(
                            f"""<div class="magic-card">
                            <div class="m-label">{r.get("brand") or ""} · 35 ml</div>
                            <div class="m-value">{r.get("name")}</div>
                            <div class="m-sub"><b>Similar / original:</b> {ref}<br>
                            <b>Familia:</b> {famtxt}<br>
                            <b>Stock:</b> {safe_float(r.stock_pos):g} · <b>Precio:</b> {money(r.sale_price)}<br>
                            <b>Margen:</b> {safe_float(r.current_margin):.1f}% · <b>Puntaje:</b> {safe_float(r.commercial_score):.0f}/100<br>
                            {r["Razón"]}</div></div>""",
                            unsafe_allow_html=True
                        )
                        if st.button("Agregar al carrito",key=f"assist_add_{int(r.id)}",use_container_width=True):
                            ensure_cart()
                            existing=next((x for x in st.session_state.cart if x["product_id"]==int(r.id)),None)
                            if existing:
                                existing["qty"]+=1
                            else:
                                st.session_state.cart.append({
                                    "product_id":int(r.id),"label":product_label(r),"qty":1.0,
                                    "unit_price":safe_float(r.sale_price),"unit_cost":safe_float(r.avg_cost)
                                })
                            st.success("Agregado al carrito de Venta rápida.")

        pending_dem=qdf(
            """SELECT requested_text AS Pedido,COUNT(*) AS Veces,MAX(date) AS Ultima_vez
               FROM demand_requests WHERE status='Pendiente'
               GROUP BY requested_text ORDER BY Veces DESC,Ultima_vez DESC"""
        )
        if not pending_dem.empty:
            executive_section("LO QUE TE ESTÁN PIDIENDO Y NO TENÉS","Demanda no cubierta registrada desde el asistente.","#9b5365")
            st.dataframe(pending_dem,use_container_width=True,hide_index=True)

        executive_section("BÚSQUEDA HUMANA","Sirve aunque recuerdes solo una parte del nombre o el perfume original.","#486a8a")
        hs=st.text_input("Buscar como lo dirías vos",placeholder="el parecido a sauvage / el rosa dulce / club nuit...",key="human_search_360")
        if hs:
            hres=human_product_search(hs,include_no_stock=True,limit=20)
            if hres.empty:
                st.info("Sin coincidencias.")
            else:
                hres["Perfume"]=hres.apply(lambda r:f"{r.brand or ''} {r['name'] or ''}".strip(),axis=1)
                hres["Original / similar"]=hres.apply(lambda r:f"{r.inspired_house or ''} {r.inspired_name or ''}".strip() or "—",axis=1)
                st.dataframe(hres[["Perfume","Original / similar","olfactory_family","stock","sale_price","sku"]],use_container_width=True,hide_index=True)

    with tabs360[5]:
        executive_section("CLIENTES RECURRENTES","Recencia, frecuencia y gasto en un puntaje 0–100.","#2f765a")
        c360=customer_360_df()
        if c360.empty:
            st.info("Todavía no hay clientes suficientes.")
        else:
            show=c360.copy()
            show["Cliente"]=show["name"]
            show["Compras"]=show["purchases"]
            show["Gastado"]=show["spend"]
            show["Ticket"]=show["avg_ticket"]
            show["Días sin comprar"]=show["days_since_purchase"]
            show["Puntaje"]=show["customer_score"]
            st.dataframe(
                show[["Cliente","phone","Compras","Gastado","Ticket","Días sin comprar","Puntaje","preferred_families"]],
                use_container_width=True,hide_index=True,height=430,
                column_config={
                    "Gastado":st.column_config.NumberColumn("Gastado",format="$ %.0f"),
                    "Ticket":st.column_config.NumberColumn("Ticket",format="$ %.0f"),
                    "Puntaje":st.column_config.ProgressColumn("Puntaje",min_value=0,max_value=100,format="%.0f"),
                }
            )

            executive_section("RECOMPRA","El ciclo es editable porque cada cliente usa 35 ml a una velocidad diferente.","#b88945")
            cycle=int(st.slider("Ciclo estimado de recompra (días)",15,120,45,key="repurchase_cycle"))
            rep=repurchase_opportunities(cycle)
            due=rep[rep.due].copy() if not rep.empty else rep
            if due.empty:
                st.success("No hay clientes vencidos según el ciclo elegido.")
            else:
                due["Cliente"]=due["name"]
                due["Última compra"]=due["last_purchase"]
                due["Días desde compra"]=due["days_since_purchase"]
                due["Fecha esperada"]=due["expected_repurchase_date"].dt.date
                due["Atraso"]=(-due["days_to_repurchase"]).clip(lower=0)
                st.dataframe(due[["Cliente","phone","Última compra","Días desde compra","Fecha esperada","Atraso","customer_score"]].head(30),use_container_width=True,hide_index=True)

            executive_section("PREFERENCIAS APRENDIDAS","La app combina historial real y notas que vos cargues.","#56354f")
            cmap={f"{r['name']} · {r['phone'] or ''}":int(r.id) for _,r in c360.iterrows()}
            clabel=st.selectbox("Abrir cliente",list(cmap.keys()),key="pref_client")
            cid=cmap[clabel]
            hist=qdf(
                """SELECT p.brand,p.name,p.olfactory_family,p.inspired_house,p.inspired_name,SUM(si.qty) qty
                   FROM sale_items si JOIN sales s ON s.id=si.sale_id JOIN products p ON p.id=si.product_id
                   WHERE s.customer_id=? AND s.status='Completada'
                   GROUP BY p.id ORDER BY qty DESC""",(cid,)
            )
            pref=qdf("SELECT * FROM customer_preferences WHERE customer_id=? ORDER BY id DESC",(cid,))
            c1,c2=st.columns(2)
            with c1:
                st.markdown("**Aprendido de compras**")
                st.dataframe(hist,use_container_width=True,hide_index=True,height=260)
            with c2:
                st.markdown("**Preferencias explícitas**")
                st.dataframe(pref,use_container_width=True,hide_index=True,height=260)
            with st.form("preference_add",clear_on_submit=True):
                p1,p2,p3=st.columns([1,2,1])
                ptype=p1.selectbox("Tipo",["Familia","Nota","Original","Uso","No le gusta","Otro"])
                pvalue=p2.text_input("Preferencia")
                pweight=p3.slider("Peso",0.5,3.0,1.0,0.5)
                pnotes=st.text_input("Notas")
                psave=st.form_submit_button("Guardar preferencia")
            if psave and pvalue.strip():
                execute(
                    """INSERT INTO customer_preferences(date,customer_id,preference_type,value,weight,notes,created_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (today_iso(),cid,ptype,pvalue.strip(),pweight,pnotes,now_iso())
                )
                audit_event("PREFERENCIA_CLIENTE","CUSTOMER",cid,after={"tipo":ptype,"valor":pvalue,"peso":pweight})
                st.success("Preferencia guardada.")
                st.rerun()

    with tabs360[6]:
        executive_section("ESCÁNER","Podés usar un lector de código que escriba texto o subir una foto de QR/barcode.","#486a8a")
        sc1,sc2,sc3=st.columns([1.25,1,1])
        manual=sc1.text_input("Código / SKU / QR",placeholder="Escaneá aquí o escribí el código",key="scan_manual")
        upload=sc2.file_uploader("Subir foto",type=["png","jpg","jpeg"],key="scan_upload")
        camera=sc3.camera_input("Usar cámara",key="scan_camera")
        decoded=decode_uploaded_code(camera) if camera else (decode_uploaded_code(upload) if upload else "")
        code=(decoded or manual).strip()
        if decoded:
            st.success(f"Código leído: {decoded}")
        if code:
            lookup=code
            pid_code=None
            if code.startswith("PERFUME35|"):
                parts=code.split("|")
                if len(parts)>=3:
                    lookup=parts[1]
                    try: pid_code=int(parts[2])
                    except Exception: pid_code=None
            if pid_code:
                found=qdf("SELECT * FROM products WHERE id=?",(pid_code,))
            else:
                found=qdf("SELECT * FROM products WHERE sku=? OR barcode=?",(lookup,lookup))
            if found.empty:
                found=human_product_search(lookup,True,5)
            if found is not None and not found.empty:
                r=found.iloc[0]
                invr=stock_df(active_only=False)
                rr=invr[invr.id==int(r.id)]
                stk=safe_float(rr.iloc[0].stock) if not rr.empty else 0
                ref=f"{r.get('inspired_house','') or ''} {r.get('inspired_name','') or ''}".strip() or "—"
                st.markdown(
                    f"""<div class="ref35"><div class="r-title">{r.get("brand","")} {r.get("name","")} · 35 ml</div>
                    <div class="r-big">{ref}</div><div class="r-sub">SKU {r.get("sku","")} · Stock {stk:g} · Precio {money(r.get("sale_price",0))}</div></div>""",
                    unsafe_allow_html=True
                )
            else:
                st.warning("No encontré ese código.")

        executive_section("ETIQUETAS CON QR","Genera una hoja A4 lista para imprimir con nombre, equivalencia, precio y QR.","#b88945")
        prodlab=stock_df(active_only=False)
        prodlab=prodlab[(prodlab.product_type=="PERFUME")&(pd.to_numeric(prodlab.size_ml,errors="coerce").fillna(0)==FIXED_SIZE_ML)] if not prodlab.empty else prodlab
        if prodlab.empty:
            st.info("Sin perfumes.")
        else:
            labmap={product_label(r):int(r.id) for _,r in prodlab.iterrows()}
            selected_labels=st.multiselect("Perfumes a etiquetar",list(labmap.keys()),key="labels_select")
            if selected_labels:
                pdfbytes=build_label_pdf([labmap[x] for x in selected_labels])
                if pdfbytes:
                    st.download_button(
                        "Descargar etiquetas A4",
                        data=pdfbytes,
                        file_name=f"etiquetas_perfumes_{today_iso()}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error("No pude generar el PDF de etiquetas en este entorno.")

    with tabs360[7]:
        executive_section("RADAR DE ANOMALÍAS","Busca datos imposibles o peligrosos antes de que alteren decisiones.","#9b5365")
        anomalies=business_anomalies()
        if anomalies.empty:
            st.success("No encontré anomalías estructurales.")
        else:
            st.dataframe(anomalies,use_container_width=True,hide_index=True,height=360)

        executive_section("CONCILIACIÓN PERMANENTE","Comprado − vendido = stock. También concilia el costo histórico.","#2f765a")
        acq_u,acq_c=reconciled_acquisition_totals()
        sold_u=reconciled_sold_units()
        sold_c=reconciled_sales_cogs()
        iu=stock_df()
        stock_u=safe_float(iu.stock.clip(lower=0).sum()) if not iu.empty else 0
        scost,_,_=inventory_value()
        cc1,cc2,cc3=st.columns(3)
        cc1.metric("Ingresadas",f"{acq_u:g}",money(acq_c))
        cc2.metric("Vendidas",f"{sold_u:g}",money(sold_c))
        cc3.metric("Stock",f"{stock_u:g}",money(scost))
        if abs((acq_u-sold_u)-stock_u)<0.001 and abs((acq_c-sold_c)-scost)<0.01:
            st.success(f"Todo cierra: {acq_u:g} − {sold_u:g} = {stock_u:g} · {money(acq_c)} − {money(sold_c)} = {money(scost)}.")
        else:
            st.error("La conciliación no cierra. Revisá el radar y los lotes antes de hacer ajustes.")

        executive_section("LOTES FIFO","Reconstrucción de qué lotes todavía deberían quedar, asumiendo salida FIFO.","#486a8a")
        lots=fifo_lots_df()
        if lots.empty:
            st.info("No hay lotes activos.")
        else:
            l1,l2,l3=st.columns(3)
            l1.metric("Lotes activos",len(lots))
            l2.metric("Unidades en lotes",f"{safe_float(lots['Unidades restantes'].sum()):g}")
            l3.metric("Capital por lotes",money(lots["Capital restante"].sum()))
            st.dataframe(
                lots.sort_values(["Edad días","Capital restante"],ascending=False),
                use_container_width=True,hide_index=True,height=430,
                column_config={
                    "Costo unitario":st.column_config.NumberColumn("Costo unitario",format="$ %.0f"),
                    "Capital restante":st.column_config.NumberColumn("Capital restante",format="$ %.0f"),
                }
            )

        executive_section("RECEPCIÓN MASIVA","Pegá una lista. La app intenta reconocer cada perfume y arma la compra para revisar.","#b88945")
        pasted=st.text_area(
            "Lista",
            placeholder="Yara x 10\nAsad x 12\n9PM x 8\nClub de Nuit x 5",
            height=150,key="mass_receive_text"
        )
        if pasted.strip():
            parsed=[]
            for line in pasted.splitlines():
                line=line.strip()
                if not line:
                    continue
                m=re.match(r"(.+?)(?:\s+[xX]\s*|\s+)(\d+(?:[\.,]\d+)?)\s*$",line)
                if m:
                    nm=m.group(1).strip()
                    qty=safe_float(m.group(2).replace(",","."))
                else:
                    nm=line
                    qty=1
                hits=human_product_search(nm,include_no_stock=True,limit=1)
                if hits.empty:
                    parsed.append({"Texto":nm,"Producto":"NO RECONOCIDO","product_id":None,"Cantidad":qty,"Costo unitario":1900.0})
                else:
                    r=hits.iloc[0]
                    parsed.append({"Texto":nm,"Producto":f"{r.brand} {r['name']}","product_id":int(r.id),"Cantidad":qty,"Costo unitario":safe_float(r.avg_cost) or 1900.0})
            pdfm=pd.DataFrame(parsed)
            edited_mass=st.data_editor(
                pdfm,use_container_width=True,hide_index=True,
                disabled=["Texto","Producto","product_id"],
                column_config={
                    "Cantidad":st.column_config.NumberColumn("Cantidad",min_value=0,step=1),
                    "Costo unitario":st.column_config.NumberColumn("Costo unitario",min_value=0,format="$ %.0f")
                },
                key="mass_receive_editor"
            )
            recognized=edited_mass[edited_mass.product_id.notna()] if not edited_mass.empty else edited_mass
            if len(recognized):
                suppliers360=qdf("SELECT id,name FROM suppliers WHERE active=1 ORDER BY name")
                supmap360={"Sin proveedor":None}
                if not suppliers360.empty:
                    supmap360.update({r["name"]:int(r.id) for _,r in suppliers360.iterrows()})
                mr1,mr2,mr3=st.columns(3)
                supl=mr1.selectbox("Proveedor",list(supmap360.keys()),key="mass_supplier")
                paym=mr2.selectbox("Pago",["Efectivo","Transferencia","Mercado Pago","Tarjeta","Cuenta corriente","Otro"],key="mass_payment")
                invref=mr3.text_input("Referencia",value=f"Recepción {today_iso()}",key="mass_invoice")
                if st.button("Registrar recepción reconocida",type="primary",use_container_width=True,key="mass_save"):
                    inv_all=stock_df(active_only=False)
                    items=[]
                    for _,r in recognized.iterrows():
                        rr=inv_all[inv_all.id==int(r.product_id)].iloc[0]
                        items.append({
                            "product_id":int(r.product_id),
                            "label":product_label(rr),
                            "qty":safe_float(r["Cantidad"]),
                            "unit_price":safe_float(r["Costo unitario"]),
                        })
                    total_mass=sum(i["qty"]*i["unit_price"] for i in items)
                    purchase_id=save_purchase(items,supmap360[supl],invref,paym,0,0,0,total_mass,"Recibida","Recepción masiva")
                    st.success(f"Compra #{purchase_id} registrada con {len(items)} fragancias.")
                    st.rerun()

        executive_section("HISTORIAL DE CAMBIOS","Append-only: sirve para saber quién hizo qué y cuándo. No se edita.","#56354f")
        aud=qdf("SELECT * FROM audit_log ORDER BY id DESC LIMIT 300")
        if aud.empty:
            st.caption("El historial empezará a poblarse con las nuevas operaciones.")
        else:
            st.dataframe(aud,use_container_width=True,hide_index=True,height=390)

        executive_section("QUÉ HARÍA AHORA","Acciones concretas priorizadas por impacto.","#2f765a")
        action_lines=[]
        if not anomalies.empty:
            ncrit=int((anomalies.Nivel=="Crítica").sum())
            if ncrit:
                action_lines.append((1,f"Corregir {ncrit} anomalía(s) crítica(s) antes de tomar decisiones con esos datos."))
        if not intel360.empty:
            soldout=int(((intel360.stock_pos<=0)&(intel360.units_sold>0)).sum())
            if soldout:
                action_lines.append((2,f"Reponer primero las {soldout} fragancias agotadas que ya demostraron ventas."))
            slowcap=float(intel360.loc[intel360.slow,"stock_cost_value"].sum())
            if slowcap:
                action_lines.append((3,f"No volvería a comprar stock lento hasta mover al menos parte de los {money(slowcap)} inmovilizados."))
            topbuy=allocate_purchase_budget(max(0,min(snap["cash"],200000)),0,True)
            if not topbuy.empty:
                preview=", ".join(f"{r['Perfume']} ×{int(r['Comprar'])}" for _,r in topbuy.head(3).iterrows())
                action_lines.append((4,f"Si vas a reinvertir caja hoy, empezaría por: {preview}."))
        if snap["receivables"]>0:
            action_lines.append((5,f"Cobrar {money(snap['receivables'])} antes de aumentar compras."))
        if snap["payables"]>0:
            action_lines.append((6,f"Reservar {money(snap['payables'])} para compromisos pendientes."))
        if snap["margin"]<TARGET_MARGIN and snap["revenue"]>0:
            action_lines.append((7,f"Revisar precios: margen realizado {snap['margin']:.1f}% vs meta {TARGET_MARGIN:.1f}%."))
        if not action_lines:
            action_lines.append((9,"No veo una urgencia: priorizaría vender, medir rotación y recomprar solo lo que demuestre salida."))
        for _,line in sorted(action_lines,key=lambda x:x[0])[:6]:
            st.markdown(f'<div class="action-card">{line}</div>',unsafe_allow_html=True)

        with st.expander("Cobertura de las 50 mejoras"):
            features = [
                "Centro de mando vivo","Mapa visual del dinero","Salud 0–100","Hoy tenés","Si vendieras todo hoy",
                "Radar de anomalías","Conciliación permanente","Timeline financiera","Heatmap de ventas","Heatmap por horario",
                "Mapa estrella de productos","Ranking inteligente","Índice de rotación","Capital atrapado","Edad del stock",
                "Alertas de stock envejecido","Reposición inteligente","Simulador de 100 unidades","Compra por presupuesto","Stock objetivo dinámico",
                "Predicción de agotamiento","Predicción 7/15/30 días","Escenarios","Simulador de precio","Precio sugerido",
                "Detector de margen peligroso","Buscador humano","Búsqueda por original","Ficha visual","Galería / estantería",
                "Estantería virtual","Colores por familia","Mapa de equivalencias","Comparador","Perfil del cliente",
                "Asistente de venta","Preferencias del cliente","Clientes recurrentes","Recompra","Venta en un toque",
                "QR / barcode","Etiquetas imprimibles","Recepción masiva","Control por lote FIFO","Historial append-only",
                "Explicación de KPI","Centro de alertas","Resumen diario","Modo dueño","Qué haría ahora",
            ]
            st.caption(" · ".join(f"{i+1}. {x}" for i,x in enumerate(features)))


# ============================================================
# PAGE: VENTAS
# ============================================================
elif page == "◉ Ventas":
    hero(
        "Ventas",
        "Explorador comercial completo: cada ticket, cada perfume, cada margen, cada cliente y cada peso cobrado.",
        "CONTROL COMERCIAL · 360°",
    )

    # ---- Filtros maestros
    st.markdown('<div class="section-title">Período y filtros</div>', unsafe_allow_html=True)
    f1,f2,f3,f4 = st.columns([1,1,1.2,1.2])
    v_start = f1.date_input("Desde", value=date.today().replace(day=1), key="vp_start")
    v_end = f2.date_input("Hasta", value=date.today(), key="vp_end")
    base_sales = sales_master_df(v_start, v_end + timedelta(days=1))

    statuses = sorted([str(x) for x in base_sales.estado.dropna().unique()]) if not base_sales.empty else []
    channels = sorted([str(x) for x in base_sales.canal.dropna().unique()]) if not base_sales.empty else []
    payments = sorted([str(x) for x in base_sales.medio_pago.dropna().unique()]) if not base_sales.empty else []
    status_filter = f3.multiselect("Estado", statuses, default=statuses)
    channel_filter = f4.multiselect("Canal", channels)

    f5,f6,f7 = st.columns([1.5,1.2,1.2])
    payment_filter = f5.multiselect("Medio de pago", payments)
    search_sale = f6.text_input("Buscar", placeholder="#ticket, cliente, perfume...")
    only_pending = f7.toggle("Solo saldos pendientes", value=False)

    sales_view = base_sales.copy()
    if not sales_view.empty:
        if status_filter:
            sales_view = sales_view[sales_view.estado.astype(str).isin(status_filter)]
        if channel_filter:
            sales_view = sales_view[sales_view.canal.astype(str).isin(channel_filter)]
        if payment_filter:
            sales_view = sales_view[sales_view.medio_pago.astype(str).isin(payment_filter)]
        if only_pending:
            sales_view = sales_view[sales_view.saldo > 0]
        if search_sale.strip():
            q = search_sale.strip().lower()
            mask = (
                sales_view.id.astype(str).str.lower().str.contains(q, regex=False)
                | sales_view.cliente.fillna("").astype(str).str.lower().str.contains(q, regex=False)
                | sales_view.productos.fillna("").astype(str).str.lower().str.contains(q, regex=False)
                | sales_view.vendedor.fillna("").astype(str).str.lower().str.contains(q, regex=False)
            )
            sales_view = sales_view[mask]

    completed = sales_view[sales_view.estado=="Completada"].copy() if not sales_view.empty else sales_view
    gross_rev = safe_float(completed.total.sum()) if not completed.empty else 0
    gross_profit = safe_float(completed.ganancia.sum()) if not completed.empty else 0
    gross_cost = safe_float(completed.costo.sum()) if not completed.empty else 0
    paid_sum = safe_float(completed.cobrado.sum()) if not completed.empty else 0
    pending_sum = safe_float(completed.saldo.sum()) if not completed.empty else 0
    units_sum = safe_float(completed.unidades.sum()) if not completed.empty else 0
    avg_ticket = gross_rev / len(completed) if len(completed) else 0
    real_margin = gross_profit/gross_rev*100 if gross_rev else 0

    k1,k2,k3 = st.columns(3)
    with k1: pro_kpi("FACTURACIÓN", money(gross_rev), f"{len(completed)} ventas", "plum")
    with k2: pro_kpi("GANANCIA", money(gross_profit), f"Margen {real_margin:.1f}%", "green")
    with k3: pro_kpi("TICKET MEDIO", money(avg_ticket), f"{units_sum:g} unidades", "gold")
    k4,k5,k6 = st.columns(3)
    with k4: pro_kpi("COBRADO", money(paid_sum), f"{(paid_sum/gross_rev*100 if gross_rev else 0):.1f}% del total", "blue")
    with k5: pro_kpi("POR COBRAR", money(pending_sum), "Saldo comercial", "rose" if pending_sum else "green")
    with k6: pro_kpi("COSTO VENDIDO", money(gross_cost), "Costo de mercadería", "gold")

    st.markdown("")
    tab_explorer, tab_detail, tab_products, tab_clients, tab_channels, tab_profit, tab_export = st.tabs(
        ["🧾 Explorador", "🔎 Ticket 360", "🧴 Productos", "👥 Clientes", "📡 Canales y cobros", "💎 Rentabilidad", "⬇ Exportar"]
    )

    with tab_explorer:
        if sales_view.empty:
            st.info("No hay ventas con los filtros elegidos.")
        else:
            trend = completed.groupby("date",as_index=False).agg(
                Facturacion=("total","sum"), Ganancia=("ganancia","sum"), Tickets=("id","count")
            ) if not completed.empty else pd.DataFrame()
            if not trend.empty:
                c1,c2 = st.columns([1.55,1])
                with c1:
                    st.markdown("#### Evolución comercial")
                    st.area_chart(trend.set_index("date")[["Facturacion","Ganancia"]], use_container_width=True)
                with c2:
                    st.markdown("#### Lectura rápida")
                    best_day = trend.loc[trend.Facturacion.idxmax()]
                    st.markdown(
                        f'<div class="insight"><b>Mejor día:</b> {best_day["date"]} · '
                        f'{money(best_day["Facturacion"])} facturados.</div>',
                        unsafe_allow_html=True
                    )
                    if real_margin < TARGET_MARGIN and gross_rev:
                        st.markdown(
                            f'<div class="insight"><b>Margen:</b> {real_margin:.1f}% · '
                            f'por debajo de tu meta de {TARGET_MARGIN:.1f}%.</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f'<div class="insight"><b>Margen:</b> {real_margin:.1f}% · '
                            f'{"en línea con la meta." if gross_rev else "sin ventas."}</div>',
                            unsafe_allow_html=True
                        )
                    if pending_sum:
                        st.markdown(
                            f'<div class="insight"><b>Cobranza:</b> {money(pending_sum)} todavía pendientes.</div>',
                            unsafe_allow_html=True
                        )

            st.markdown("#### Libro de ventas")
            table = sales_view.copy()
            table["Ticket"] = table.id.apply(lambda x: f"#{int(x):06d}")
            table["Fecha"] = table.date.astype(str) + table.hora.fillna("").apply(lambda x: f" · {x}" if x else "")
            table["Cliente"] = table.cliente
            table["Productos"] = table.productos
            table["Canal"] = table.canal
            table["Pago"] = table.medio_pago
            table["Unid."] = table.unidades
            table["Total"] = table.total
            table["Cobrado"] = table.cobrado
            table["Saldo"] = table.saldo
            table["Ganancia"] = table.ganancia
            table["Margen"] = table.margen
            table["Estado"] = table.estado
            table["Vendedor"] = table.vendedor
            st.dataframe(
                table[["Ticket","Fecha","Cliente","Productos","Unid.","Canal","Pago","Total","Cobrado","Saldo","Ganancia","Margen","Vendedor","Estado"]],
                use_container_width=True,
                hide_index=True,
                height=520,
                column_config={
                    "Productos": st.column_config.TextColumn("Productos vendidos", width="large"),
                    "Total": st.column_config.NumberColumn("Total", format="$ %.0f"),
                    "Cobrado": st.column_config.NumberColumn("Cobrado", format="$ %.0f"),
                    "Saldo": st.column_config.NumberColumn("Saldo", format="$ %.0f"),
                    "Ganancia": st.column_config.NumberColumn("Ganancia", format="$ %.0f"),
                    "Margen": st.column_config.ProgressColumn("Margen", min_value=0, max_value=100, format="%.1f%%"),
                },
            )

    with tab_detail:
        if sales_view.empty:
            st.info("No hay tickets para abrir.")
        else:
            labels = {}
            for _,r in sales_view.iterrows():
                summary = str(r.productos or "")
                if len(summary)>70: summary=summary[:67]+"..."
                labels[f"#{int(r.id):06d} · {r.date} · {r.cliente} · {money(r.total)} · {summary}"] = int(r.id)
            default_index = 0
            selected_label = st.selectbox("Seleccionar venta", list(labels.keys()), index=default_index, key="vp_ticket")
            selected_id = labels[selected_label]
            render_sale_detail(selected_id, "vp")

            row = sale_header_row(selected_id)
            if row is not None and str(row.status)=="Completada":
                with st.expander("⚠️ Anular esta venta"):
                    st.caption("La anulación reintegra el stock y registra el egreso correspondiente del dinero cobrado.")
                    confirm_void = st.checkbox(f"Confirmo anular la venta #{selected_id}", key=f"void_confirm_{selected_id}")
                    if st.button("ANULAR VENTA", disabled=not confirm_void, key=f"void_btn_{selected_id}"):
                        try:
                            refund_sale(selected_id)
                            st.success("Venta anulada correctamente. Stock reintegrado.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

    with tab_products:
        items_all = qdf(
            """
            SELECT p.id,p.sku,p.brand,p.name,p.size_ml,p.gender,p.category,
                   SUM(si.qty) unidades,
                   SUM(si.subtotal) facturacion,
                   SUM(si.qty*si.unit_cost) costo,
                   SUM((si.unit_price-si.unit_cost)*si.qty) ganancia,
                   CASE WHEN SUM(si.subtotal)>0
                     THEN SUM((si.unit_price-si.unit_cost)*si.qty)/SUM(si.subtotal)*100 ELSE 0 END margen,
                   COUNT(DISTINCT s.id) tickets
            FROM sale_items si
            JOIN sales s ON s.id=si.sale_id
            JOIN products p ON p.id=si.product_id
            WHERE s.date>=? AND s.date<? AND s.status='Completada'
            GROUP BY p.id
            ORDER BY ganancia DESC
            """,
            (str(v_start), str(v_end+timedelta(days=1))),
        )
        if items_all.empty:
            st.info("Sin productos vendidos en el período.")
        else:
            a,b = st.columns([1.4,1])
            with a:
                st.markdown("#### Ranking por ganancia")
                st.bar_chart(items_all.head(12).set_index(items_all.head(12).apply(lambda r:f"{r.brand} {r['name']}",axis=1))["ganancia"])
            with b:
                star = items_all.iloc[0]
                st.markdown(
                    f'<div class="pro-card"><div class="label">PRODUCTO #1 POR GANANCIA</div>'
                    f'<div class="value">{star.brand} {star["name"]}</div>'
                    f'<div class="sub">{star.unidades:g} u. · {money(star.facturacion)} · {money(star.ganancia)} ganancia</div></div>',
                    unsafe_allow_html=True
                )
            items_all["Producto"]=items_all.apply(lambda r:f"{r.brand} {r['name']} · {safe_float(r.size_ml):g}ml",axis=1)
            st.dataframe(
                items_all[["sku","Producto","unidades","tickets","facturacion","costo","ganancia","margen"]],
                use_container_width=True,hide_index=True,
                column_config={
                    "facturacion":st.column_config.NumberColumn("Facturación",format="$ %.0f"),
                    "costo":st.column_config.NumberColumn("Costo",format="$ %.0f"),
                    "ganancia":st.column_config.NumberColumn("Ganancia",format="$ %.0f"),
                    "margen":st.column_config.ProgressColumn("Margen",min_value=0,max_value=100,format="%.1f%%"),
                }
            )

    with tab_clients:
        clients_rank = qdf(
            """
            SELECT COALESCE(c.name,'Consumidor final') cliente,
                   COALESCE(c.phone,'') telefono,
                   COUNT(s.id) tickets,
                   SUM(s.total) facturacion,
                   SUM(s.profit) ganancia,
                   AVG(s.total) ticket_promedio,
                   MAX(s.date) ultima_compra
            FROM sales s
            LEFT JOIN customers c ON c.id=s.customer_id
            WHERE s.date>=? AND s.date<? AND s.status='Completada'
            GROUP BY COALESCE(c.id,0)
            ORDER BY facturacion DESC
            """,
            (str(v_start), str(v_end+timedelta(days=1))),
        )
        if clients_rank.empty:
            st.info("Sin clientes para analizar.")
        else:
            st.dataframe(
                clients_rank,use_container_width=True,hide_index=True,
                column_config={
                    "facturacion":st.column_config.NumberColumn("Facturación",format="$ %.0f"),
                    "ganancia":st.column_config.NumberColumn("Ganancia",format="$ %.0f"),
                    "ticket_promedio":st.column_config.NumberColumn("Ticket medio",format="$ %.0f"),
                }
            )

    with tab_channels:
        if completed.empty:
            st.info("Sin ventas completadas.")
        else:
            c1,c2 = st.columns(2)
            with c1:
                st.markdown("#### Facturación por canal")
                by_ch = completed.groupby("canal",as_index=False).agg(Facturacion=("total","sum"),Tickets=("id","count"))
                st.bar_chart(by_ch.set_index("canal")["Facturacion"],use_container_width=True)
                st.dataframe(by_ch,use_container_width=True,hide_index=True)
            with c2:
                st.markdown("#### Cobros por medio")
                by_pay = completed.groupby("medio_pago",as_index=False).agg(Facturacion=("total","sum"),Cobrado=("cobrado","sum"),Tickets=("id","count"))
                st.bar_chart(by_pay.set_index("medio_pago")["Cobrado"],use_container_width=True)
                st.dataframe(by_pay,use_container_width=True,hide_index=True)

    with tab_profit:
        if completed.empty:
            st.info("Sin datos de rentabilidad.")
        else:
            low_margin = completed[completed.margen < TARGET_MARGIN].sort_values("margen")
            high_margin = completed.sort_values("ganancia",ascending=False).head(10)
            c1,c2 = st.columns(2)
            with c1:
                st.markdown(f"#### Ventas bajo margen objetivo ({TARGET_MARGIN:.0f}%)")
                if low_margin.empty:
                    st.success("Todas las ventas están por encima del margen objetivo.")
                else:
                    st.dataframe(
                        low_margin[["id","date","cliente","productos","total","ganancia","margen"]],
                        use_container_width=True,hide_index=True,
                        column_config={
                            "total":st.column_config.NumberColumn("Total",format="$ %.0f"),
                            "ganancia":st.column_config.NumberColumn("Ganancia",format="$ %.0f"),
                            "margen":st.column_config.NumberColumn("Margen",format="%.1f%%"),
                        }
                    )
            with c2:
                st.markdown("#### Top operaciones por ganancia")
                st.dataframe(
                    high_margin[["id","date","cliente","productos","total","ganancia","margen"]],
                    use_container_width=True,hide_index=True,
                    column_config={
                        "total":st.column_config.NumberColumn("Total",format="$ %.0f"),
                        "ganancia":st.column_config.NumberColumn("Ganancia",format="$ %.0f"),
                        "margen":st.column_config.NumberColumn("Margen",format="%.1f%%"),
                    }
                )

    with tab_export:
        if sales_view.empty:
            st.info("No hay datos para exportar.")
        else:
            csv_sales = sales_view.to_csv(index=False).encode("utf-8-sig")
            items_export = qdf(
                """
                SELECT s.id venta_id,s.date,p.sku,p.brand,p.name,p.size_ml,si.qty,
                       si.unit_price,si.unit_cost,si.subtotal,
                       (si.unit_price-si.unit_cost)*si.qty ganancia
                FROM sale_items si
                JOIN sales s ON s.id=si.sale_id
                JOIN products p ON p.id=si.product_id
                WHERE s.date>=? AND s.date<?
                ORDER BY s.id DESC,si.id
                """,
                (str(v_start),str(v_end+timedelta(days=1)))
            )
            c1,c2 = st.columns(2)
            c1.download_button(
                "⬇ Descargar libro de ventas",
                csv_sales,
                file_name=f"ventas_{v_start}_{v_end}.csv",
                mime="text/csv",
                use_container_width=True
            )
            c2.download_button(
                "⬇ Descargar detalle por producto",
                items_export.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"detalle_productos_{v_start}_{v_end}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.caption("Los archivos reflejan los datos cargados desde Google Sheets en la sesión actual.")


# ============================================================
# PAGE: POS
# ============================================================
elif page == "▣ Venta rápida":
    hero("Venta rápida", "Caja comercial premium: elegí el perfume, controlá el margen y cerrá la operación sin perder trazabilidad.", "POS · PERFUME OS")
    ensure_cart()

    _q_today = sales_master_df(today_iso(), (date.today()+timedelta(days=1)).isoformat())
    _q_completed = _q_today[_q_today.estado=="Completada"] if not _q_today.empty else _q_today
    q1,q2,q3,q4 = st.columns(4)
    with q1: pro_kpi("HOY", money(_q_completed.total.sum() if not _q_completed.empty else 0), f"{len(_q_completed)} tickets", "plum")
    with q2: pro_kpi("GANANCIA HOY", money(_q_completed.ganancia.sum() if not _q_completed.empty else 0), "Resultado bruto", "green")
    with q3: pro_kpi("TICKET MEDIO", money((_q_completed.total.mean() if not _q_completed.empty else 0)), "Promedio por venta", "gold")
    with q4: pro_kpi("POR COBRAR", money(_q_completed.saldo.sum() if not _q_completed.empty else 0), "Ventas del día", "rose")
    st.markdown("")

    inv = stock_df()
    inv = inv[(inv.stock > 0) & (inv.sellable==1) & (inv.active==1)].copy() if not inv.empty else inv

    # Venta ultrarrápida: los perfumes que más rotan quedan a un toque.
    if not inv.empty:
        fast = qdf(
            """SELECT p.id,COALESCE(SUM(CASE WHEN s.status='Completada' THEN si.qty ELSE 0 END),0) sold
               FROM products p
               LEFT JOIN sale_items si ON si.product_id=p.id
               LEFT JOIN sales s ON s.id=si.sale_id
               WHERE p.active=1 AND p.sellable=1
               GROUP BY p.id
               ORDER BY sold DESC,p.name
               LIMIT 8"""
        )
        fast = fast[fast.id.isin(inv.id)] if not fast.empty else fast
        if not fast.empty:
            st.markdown('<div class="soft-title">Venta en un toque</div>', unsafe_allow_html=True)
            fast_cols = st.columns(min(4,len(fast)))
            for ix,(_,fr) in enumerate(fast.iterrows()):
                rr = inv[inv.id==int(fr.id)]
                if rr.empty:
                    continue
                rr = rr.iloc[0]
                price = safe_float(rr.promo_price if safe_float(rr.promo_price)>0 else rr.sale_price)
                label = f"{rr['name']} · {money(price)}"
                if fast_cols[ix % len(fast_cols)].button(label,use_container_width=True,key=f"fast_sell_{int(rr.id)}"):
                    existing = next((x for x in st.session_state.cart if x["product_id"]==int(rr.id) and abs(x["unit_price"]-price)<1e-9),None)
                    if existing:
                        existing["qty"] += 1
                    else:
                        st.session_state.cart.append({
                            "product_id":int(rr.id),
                            "label":product_label(rr),
                            "qty":1.0,
                            "unit_price":price,
                            "unit_cost":safe_float(rr.avg_cost),
                        })
                    st.rerun()
            st.caption("Un toque agrega 1 unidad al carrito al precio vigente.")

    search = st.text_input(
        "Buscar perfume",
        placeholder="Ej.: Asad, Sauvage, Baccarat, vainilla, Yara, 9PM...",
        help="Podés buscar por el nombre del tubito o por el perfume original/inspiración que recordás."
    )

    if not inv.empty:
        inv["_ref35_search"] = inv.apply(lambda r: fragrance_search_text35(r.get("name",""), r.get("brand","")), axis=1)
        if search:
            mask = (
                inv["brand"].fillna("").str.contains(search, case=False, regex=False)
                | inv["name"].fillna("").str.contains(search, case=False, regex=False)
                | inv["sku"].fillna("").str.contains(search, case=False, regex=False)
                | inv["barcode"].fillna("").str.contains(search, case=False, regex=False)
                | inv["_ref35_search"].fillna("").str.contains(search, case=False, regex=False)
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
            _p_margin = ((price-float(prow.avg_cost))/price*100) if price else 0
            _ref_label = fragrance_reference_label35(prow["name"], prow.brand)
            st.markdown(
                f'<div class="insight"><b>{prow.brand} {prow["name"]}</b> · 35 ml · stock {prow.stock:g} · '
                f'costo {money(prow.avg_cost)} · precio {money(price)} · margen <b>{_p_margin:.1f}%</b>'
                f'{" · ⚠ debajo de meta" if _p_margin < TARGET_MARGIN else ""}<br>'
                f'<span class="mini">Referencia olfativa: {_ref_label}</span></div>',
                unsafe_allow_html=True
            )
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
        cart_df["Ganancia"] = cart_df["Subtotal"] - cart_df["Costo"]
        cart_df["Margen"] = np.where(cart_df["Subtotal"]>0,cart_df["Ganancia"]/cart_df["Subtotal"]*100,0)
        st.dataframe(
            cart_df[["label","qty","unit_price","Subtotal","Costo","Ganancia","Margen"]],
            use_container_width=True, hide_index=True,
            column_config={
                "label":"Producto",
                "qty":"Cant.",
                "unit_price":st.column_config.NumberColumn("Precio", format="$ %.0f"),
                "Subtotal":st.column_config.NumberColumn("Subtotal", format="$ %.0f"),
                "Costo":st.column_config.NumberColumn("Costo", format="$ %.0f"),
                "Ganancia":st.column_config.NumberColumn("Ganancia", format="$ %.0f"),
                "Margen":st.column_config.ProgressColumn("Margen", min_value=0, max_value=100, format="%.1f%%"),
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
                st.session_state["last_sale_id"] = sale_id
                st.success(f"Venta #{sale_id} registrada correctamente.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.divider()
    st.markdown("### Ventas recientes")
    recent = sales_master_df((date.today()-timedelta(days=14)).isoformat(), (date.today()+timedelta(days=1)).isoformat()).head(40)
    if recent.empty:
        st.caption("Sin ventas todavía.")
    else:
        recent_show = recent.copy()
        recent_show["Ticket"]=recent_show.id.apply(lambda x:f"#{int(x):06d}")
        recent_show["Fecha"]=recent_show.date.astype(str)
        recent_show["Cliente"]=recent_show.cliente
        recent_show["Productos"]=recent_show.productos
        recent_show["Total"]=recent_show.total
        recent_show["Ganancia"]=recent_show.ganancia
        recent_show["Margen"]=recent_show.margen
        recent_show["Pago"]=recent_show.medio_pago
        recent_show["Estado"]=recent_show.estado
        st.dataframe(
            recent_show[["Ticket","Fecha","Cliente","Productos","Pago","Total","Ganancia","Margen","Estado"]],
            use_container_width=True,hide_index=True,height=350,
            column_config={
                "Productos":st.column_config.TextColumn("Productos vendidos",width="large"),
                "Total":st.column_config.NumberColumn("Total",format="$ %.0f"),
                "Ganancia":st.column_config.NumberColumn("Ganancia",format="$ %.0f"),
                "Margen":st.column_config.ProgressColumn("Margen",min_value=0,max_value=100,format="%.1f%%"),
            }
        )
        options={f"#{int(r.id):06d} · {r.date} · {r.cliente} · {money(r.total)}":int(r.id) for _,r in recent.iterrows()}
        default_sale = st.session_state.get("last_sale_id")
        opt_keys=list(options.keys())
        default_idx=0
        if default_sale:
            for i,k in enumerate(opt_keys):
                if options[k]==default_sale:
                    default_idx=i; break
        selected_recent=st.selectbox("Abrir detalle de venta",opt_keys,index=default_idx,key="quick_recent_detail")
        render_sale_detail(options[selected_recent],"quick")


# ============================================================
# PAGE: 35 ML MASTER LIBRARY
# ============================================================
elif page == "⌕ Biblioteca 35 ml":
    hero(
        "Biblioteca 35 ml",
        "La biblioteca y tu inventario ahora son una sola base. Todas las fragancias aparecen en Catálogo e Inventario aunque tengan stock 0, y sus datos se pueden corregir cuando quieras.",
        "PERFUME 35 OS · REFERENCIAS Y EQUIVALENCIAS",
    )
    inv35 = stock_df(active_only=False)
    lib_inv = inv35[(inv35.library_item==1) & (inv35.product_type!='DECANT')].copy() if (not inv35.empty and 'library_item' in inv35.columns) else pd.DataFrame()
    if lib_inv.empty:
        st.warning("La biblioteca todavía no está disponible en el catálogo.")
    else:
        lib_inv['original_similar'] = lib_inv.apply(
            lambda r: f"{r.get('inspired_house','') or ''} {r.get('inspired_name','') or ''}".strip() or '—', axis=1
        )
        total_lib = len(lib_inv)
        with_stock = int((lib_inv.stock>0).sum())
        units = safe_float(lib_inv.stock.clip(lower=0).sum())
        retail = safe_float((lib_inv.stock.clip(lower=0)*lib_inv.sale_price).sum())
        mapped = int(lib_inv.inspired_name.fillna('').astype(str).str.strip().ne('').sum())
        k1,k2,k3,k4 = st.columns(4)
        with k1: pro_kpi("FRAGANCIAS", f"{total_lib}", "Todas integradas al catálogo", "plum")
        with k2: pro_kpi("CON STOCK", f"{with_stock}", f"{units:g} unidades físicas", "green")
        with k3: pro_kpi("CON EQUIVALENCIA", f"{mapped}", "Referencia olfativa cargada", "gold")
        with k4: pro_kpi("VALOR EN STOCK", money(retail), "A precio de venta actual", "rose")

        st.markdown('<div class="edit-callout"><b>Una sola base:</b> cambiar un nombre, precio, equivalencia, perfil o ubicación acá modifica el mismo artículo que ves en Catálogo e Inventario. El stock se corrige por movimientos para conservar trazabilidad.</div>', unsafe_allow_html=True)

        tab_search, tab_edit, tab_map = st.tabs(["⌕ Explorar", "✎ Editar biblioteca", "≡ Guía completa"])

        with tab_search:
            c1,c2,c3,c4 = st.columns([2.2,1,1,1])
            q = c1.text_input("Buscar por cualquier dato", placeholder="Sauvage, Baccarat, pistacho, Yara, vainilla, mujer...", key="lib35_search_v6")
            genders = sorted([x for x in lib_inv.gender.fillna('').unique() if str(x).strip()])
            priorities = [x for x in ['A+','A','B','C'] if x in lib_inv.priority.fillna('').unique().tolist()]
            g = c2.multiselect("Género", genders, key="lib35_g_v6")
            p = c3.multiselect("Nivel", priorities, key="lib35_p_v6")
            stock_mode = c4.selectbox("Stock", ["Todos","Con stock","Sin stock"], key="lib35_stock_v6")
            v = lib_inv.copy()
            if q:
                qn = _norm35(q)
                blob = v.apply(lambda r: _norm35(_product_reference_text35(r)), axis=1)
                v = v[blob.str.contains(qn, regex=False)]
            if g: v = v[v.gender.isin(g)]
            if p: v = v[v.priority.isin(p)]
            if stock_mode == "Con stock": v = v[v.stock>0]
            if stock_mode == "Sin stock": v = v[v.stock<=0]

            if v.empty:
                st.info("No hay coincidencias con esos filtros.")
            else:
                show = pd.DataFrame({
                    "Nivel":v.priority.fillna(''),
                    "Nombre 35 ml":v['name'].fillna(''),
                    "Referencia":(v.reference_house.fillna('')+' '+v.reference_name.fillna('')).str.strip(),
                    "Inspirado / similar a":v.original_similar,
                    "Género":v.gender.fillna(''),
                    "Familia":v.olfactory_family.fillna(''),
                    "Perfil":v.fragrance_profile.fillna(''),
                    "Stock":v.stock,
                    "Precio":v.sale_price,
                })
                st.dataframe(
                    show,use_container_width=True,hide_index=True,height=min(620,110+34*len(show)),
                    column_config={
                        "Stock":st.column_config.NumberColumn("Stock",format="%.0f"),
                        "Precio":st.column_config.NumberColumn("Precio",format="$ %.0f"),
                    }
                )
                labels = {f"{r['name']} · {r.get('reference_house','') or ''} · stock {safe_float(r.stock):g}":int(r.id) for _,r in v.iterrows()}
                selected = st.selectbox("Ficha de fragancia", list(labels.keys()), key="lib35_card_v6")
                r = v[v.id==labels[selected]].iloc[0]
                original = f"{r.inspired_house or ''} {r.inspired_name or ''}".strip() or "Sin equivalencia 1:1 definida"
                st.markdown(
                    f"""<div class="ref35"><div class="r-title">{r['name']} · 35 ml</div>
                    <div class="r-big">{original}</div>
                    <div class="r-sub"><b>Referencia:</b> {r.reference_house or '—'} {r.reference_name or ''}<br>
                    <b>Relación:</b> {r.similarity_relation or '—'} · <b>Confianza:</b> {r.similarity_confidence or '—'}<br>
                    <b>Perfil:</b> {r.fragrance_profile or '—'}<br><b>Familia:</b> {r.olfactory_family or '—'} · <b>Género:</b> {r.gender or '—'}<br>
                    <b>Stock:</b> {safe_float(r.stock):g} · <b>Costo:</b> {money(r.avg_cost)} · <b>Venta:</b> {money(r.sale_price)}</div></div>""",
                    unsafe_allow_html=True,
                )

        with tab_edit:
            st.markdown('<div class="soft-title">Edición masiva de referencias y datos comerciales</div>', unsafe_allow_html=True)
            st.caption("Podés modificar cada dato. ‘Stock objetivo’ crea automáticamente el ajuste necesario en movimientos de stock.")
            editor = _product_editor_frame35(lib_inv, include_stock=True, compact=False)
            edited = st.data_editor(
                editor,
                use_container_width=True,
                hide_index=True,
                height=640,
                disabled=['ID','Stock actual'],
                column_config={
                    'ID':st.column_config.NumberColumn('ID',format='%d'),
                    'Costo':st.column_config.NumberColumn('Costo',min_value=0,format='$ %.0f'),
                    'Precio venta':st.column_config.NumberColumn('Precio venta',min_value=0,format='$ %.0f'),
                    'Mayorista':st.column_config.NumberColumn('Mayorista',min_value=0,format='$ %.0f'),
                    'Revendedor':st.column_config.NumberColumn('Revendedor',min_value=0,format='$ %.0f'),
                    'Promocional':st.column_config.NumberColumn('Promocional',min_value=0,format='$ %.0f'),
                    'Stock actual':st.column_config.NumberColumn('Stock actual',format='%.0f'),
                    'Stock objetivo':st.column_config.NumberColumn('Stock objetivo',min_value=0,step=1,format='%.0f'),
                    'Stock mínimo':st.column_config.NumberColumn('Stock mínimo',min_value=0,step=1,format='%.0f'),
                    'Vendible':st.column_config.CheckboxColumn('Vendible'),
                    'Activo':st.column_config.CheckboxColumn('Activo'),
                },
                key='library_full_editor_v6',
            )
            if st.button("Guardar cambios de biblioteca", type="primary", use_container_width=True, key="save_library_v6"):
                try:
                    upd, adj = save_product_editor35(edited)
                    st.success(f"Guardado: {upd} fichas actualizadas · {adj} ajustes de stock registrados.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No pude guardar los cambios: {e}")

        with tab_map:
            guide = pd.DataFrame({
                'Nivel':lib_inv.priority.fillna(''),
                'Nombre 35 ml':lib_inv['name'].fillna(''),
                'Casa / referencia':(lib_inv.reference_house.fillna('')+' '+lib_inv.reference_name.fillna('')).str.strip(),
                'Inspirado / similar a':lib_inv.original_similar,
                'Relación':lib_inv.similarity_relation.fillna(''),
                'Confianza':lib_inv.similarity_confidence.fillna(''),
                'Género':lib_inv.gender.fillna(''),
                'Familia':lib_inv.olfactory_family.fillna(''),
                'Perfil':lib_inv.fragrance_profile.fillna(''),
                'Alias':lib_inv.aliases.fillna(''),
                'Stock':lib_inv.stock,
                'Precio':lib_inv.sale_price,
            })
            st.dataframe(guide,use_container_width=True,hide_index=True,height=680)
            st.download_button("Descargar guía actual CSV",guide.to_csv(index=False).encode('utf-8-sig'),'guia_35ml_actual.csv','text/csv',use_container_width=True)

# ============================================================
# PAGE: CATALOG
# ============================================================
elif page == "◈ Catálogo":
    hero("Catálogo 35 ml", "Una única base para todas las fragancias: incluso las que hoy tienen stock 0. Nombres, equivalencias, costos, precios, stock y ficha olfativa quedan conectados.", "PERFUME 35 OS")
    tab1, tab2, tab3, tab4 = st.tabs(["Catálogo", "Edición completa", "Nuevo perfume", "Ficha"])

    with tab1:
        inv = stock_df(active_only=False)
        if inv.empty:
            st.info("Sin productos.")
        else:
            c1,c2,c3,c4 = st.columns([2.3,1,1,1])
            search = c1.text_input("Buscar en todo el catálogo", placeholder="Nombre, original, marca, perfil, alias, SKU...", key="catalog_search_v6")
            gender_opts = sorted([x for x in inv.gender.fillna('').unique() if str(x).strip()])
            gender = c2.multiselect("Género", gender_opts, key="catalog_gender_v6")
            stock_filter = c3.selectbox("Stock", ["Todos","Con stock","Sin stock"], key="catalog_stock_v6")
            active_filter = c4.selectbox("Estado", ["Activos","Todos","Inactivos"], key="catalog_active_v6")
            view = inv[inv.product_type!='DECANT'].copy()
            if search:
                qn = _norm35(search)
                blob = view.apply(lambda r:_norm35(_product_reference_text35(r)),axis=1)
                view = view[blob.str.contains(qn,regex=False)]
            if gender: view=view[view.gender.isin(gender)]
            if stock_filter=="Con stock": view=view[view.stock>0]
            elif stock_filter=="Sin stock": view=view[view.stock<=0]
            if active_filter=="Activos": view=view[view.active==1]
            elif active_filter=="Inactivos": view=view[view.active==0]

            show = enrich_35ml_df(view)
            if show.empty:
                st.info("No hay productos con esos filtros.")
            else:
                show['Margen %'] = np.where(show.sale_price>0,(show.sale_price-show.avg_cost)/show.sale_price*100,0)
                show['Valor stock'] = show.stock.clip(lower=0)*show.sale_price
                show = show[[
                    'sku','brand','name','Inspirado / similar a','gender','olfactory_family','stock','avg_cost','sale_price','Margen %','Valor stock','min_stock','location','active'
                ]].copy()
                show.columns=['SKU','Marca','Nombre','Inspirado / similar a','Género','Familia','Stock','Costo','Precio','Margen %','Valor stock','Mínimo','Ubicación','Activo']
                st.dataframe(
                    show,use_container_width=True,hide_index=True,height=650,
                    column_config={
                        'Stock':st.column_config.NumberColumn('Stock',format='%.0f'),
                        'Costo':st.column_config.NumberColumn('Costo',format='$ %.0f'),
                        'Precio':st.column_config.NumberColumn('Precio',format='$ %.0f'),
                        'Margen %':st.column_config.ProgressColumn('Margen',min_value=0,max_value=100,format='%.1f%%'),
                        'Valor stock':st.column_config.NumberColumn('Valor stock',format='$ %.0f'),
                        'Activo':st.column_config.CheckboxColumn('Activo'),
                    }
                )

    with tab2:
        inv = stock_df(active_only=False)
        inv = inv[inv.product_type!='DECANT'].copy() if not inv.empty else inv
        if inv.empty:
            st.info("Sin productos para editar.")
        else:
            st.markdown('<div class="edit-callout"><b>Editor conectado:</b> lo que modifiques acá también cambia Biblioteca e Inventario. Para stock, escribí la cantidad final deseada en “Stock objetivo”.</div>', unsafe_allow_html=True)
            c1,c2 = st.columns([2.5,1])
            qedit = c1.text_input("Filtrar antes de editar", key="catalog_edit_filter_v6")
            scope = c2.selectbox("Mostrar", ["Todos","Solo biblioteca","Solo con stock","Solo sin stock"], key="catalog_edit_scope_v6")
            v = inv.copy()
            if qedit:
                qn=_norm35(qedit); blob=v.apply(lambda r:_norm35(_product_reference_text35(r)),axis=1); v=v[blob.str.contains(qn,regex=False)]
            if scope=="Solo biblioteca": v=v[v.library_item==1]
            elif scope=="Solo con stock": v=v[v.stock>0]
            elif scope=="Solo sin stock": v=v[v.stock<=0]
            editor = _product_editor_frame35(v, include_stock=True, compact=False)
            edited = st.data_editor(
                editor,use_container_width=True,hide_index=True,height=680,disabled=['ID','Stock actual'],
                column_config={
                    'Costo':st.column_config.NumberColumn('Costo',min_value=0,format='$ %.0f'),
                    'Precio venta':st.column_config.NumberColumn('Precio venta',min_value=0,format='$ %.0f'),
                    'Mayorista':st.column_config.NumberColumn('Mayorista',min_value=0,format='$ %.0f'),
                    'Revendedor':st.column_config.NumberColumn('Revendedor',min_value=0,format='$ %.0f'),
                    'Promocional':st.column_config.NumberColumn('Promocional',min_value=0,format='$ %.0f'),
                    'Stock actual':st.column_config.NumberColumn('Stock actual',format='%.0f'),
                    'Stock objetivo':st.column_config.NumberColumn('Stock objetivo',min_value=0,step=1,format='%.0f'),
                    'Stock mínimo':st.column_config.NumberColumn('Stock mínimo',min_value=0,step=1,format='%.0f'),
                    'Vendible':st.column_config.CheckboxColumn('Vendible'),
                    'Activo':st.column_config.CheckboxColumn('Activo'),
                },
                key='catalog_full_editor_v6',
            )
            if st.button("Guardar catálogo",type="primary",use_container_width=True,key="save_catalog_v6"):
                try:
                    upd,adj=save_product_editor35(edited)
                    st.success(f"Catálogo actualizado: {upd} fichas · {adj} ajustes de stock.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No pude guardar: {e}")

    with tab3:
        st.markdown('<span class="format35-badge">TAMAÑO FIJO · 35 ML</span>', unsafe_allow_html=True)
        lib_new = fragrance_library_df()
        templates = ['Carga manual'] + sorted(lib_new.tube_name.dropna().astype(str).unique().tolist()) if not lib_new.empty else ['Carga manual']
        template_label = st.selectbox("Usar una ficha como plantilla", templates, key="new35_template_v6")
        template = None
        if template_label != 'Carga manual' and not lib_new.empty:
            rr=lib_new[lib_new.tube_name==template_label]
            template=rr.iloc[0].to_dict() if not rr.empty else None
        suppliers = qdf("SELECT id,name FROM suppliers WHERE active=1 ORDER BY name")
        sup_opts={'Sin proveedor':None}; sup_opts.update({r['name']:int(r['id']) for _,r in suppliers.iterrows()} if not suppliers.empty else {})
        with st.form('new_product_form_v6',clear_on_submit=True):
            a,b,c,d=st.columns(4)
            tname=(template or {}).get('tube_name',''); tref=(template or {}).get('reference_house','')
            sku=a.text_input('SKU*',value=auto_sku35(tname) if tname else uid('35-'))
            barcode=b.text_input('Código de barras')
            brand=c.text_input('Marca / fabricante',value='Tubito 35 ml')
            name=d.text_input('Nombre*',value=tname)
            a,b,c,d=st.columns(4)
            ref_house=a.text_input('Casa de referencia',value=tref)
            ref_name=b.text_input('Nombre de referencia',value=(template or {}).get('reference_name',''))
            inspired_house=c.text_input('Marca original / similar',value=(template or {}).get('designer_house',''))
            inspired_name=d.text_input('Perfume original / similar',value=(template or {}).get('designer_name',''))
            a,b,c,d=st.columns(4)
            relation=a.text_input('Tipo de relación',value=(template or {}).get('relation',''))
            confidence=b.text_input('Confianza',value=(template or {}).get('confidence',''))
            priority=c.selectbox('Nivel',['A+','A','B','C',''],index=1)
            gender=d.selectbox('Género',['Hombre','Mujer','Unisex','Otro'],index=2)
            a,b,c,d=st.columns(4)
            family=a.text_input('Familia olfativa',value=(template or {}).get('family',''))
            profile=b.text_input('Perfil olfativo',value=(template or {}).get('profile',''))
            aliases=c.text_input('Alias / búsquedas',value=(template or {}).get('aliases',''))
            concentration=d.selectbox('Concentración',['EDP','EDT','Parfum','Extrait','Cologne','Otro'])
            a,b,c,d=st.columns(4)
            origin=a.text_input('País / origen')
            category=b.text_input('Categoría',value='Tubito 35 ml')
            line=c.text_input('Referencia / línea')
            location=d.text_input('Ubicación')
            a,b,c=st.columns(3)
            top=a.text_area('Notas de salida'); heart=b.text_area('Notas de corazón'); base=c.text_area('Notas de fondo')
            a,b,c,d=st.columns(4)
            season=a.text_input('Temporada'); use_time=b.text_input('Uso'); batch=c.text_input('Batch'); supplier_label=d.selectbox('Proveedor',list(sup_opts.keys()))
            a,b,c,d,e=st.columns(5)
            cost=a.number_input('Costo',min_value=0.0,value=0.0,step=100.0)
            sale=b.number_input('Precio venta',min_value=0.0,value=0.0,step=100.0)
            wholesale=c.number_input('Mayorista',min_value=0.0,value=0.0,step=100.0)
            reseller=d.number_input('Revendedor',min_value=0.0,value=0.0,step=100.0)
            promo=e.number_input('Promocional',min_value=0.0,value=0.0,step=100.0)
            a,b,c=st.columns(3)
            min_stock=a.number_input('Stock mínimo',min_value=0.0,value=0.0,step=1.0)
            initial_stock=b.number_input('Stock inicial',min_value=0.0,value=0.0,step=1.0)
            sellable=c.checkbox('Vendible',value=True)
            submit=st.form_submit_button('Crear perfume',type='primary',use_container_width=True)
        if submit:
            if not sku.strip() or not name.strip():
                st.error('SKU y nombre son obligatorios.')
            else:
                try:
                    cur=execute(
                        """INSERT INTO products(
                        sku,barcode,brand,name,line,gender,concentration,size_ml,origin_country,category,product_type,olfactory_family,
                        reference_house,reference_name,inspired_house,inspired_name,similarity_relation,similarity_confidence,fragrance_profile,priority,aliases,
                        top_notes,heart_notes,base_notes,season,use_time,batch_code,supplier_id,avg_cost,sale_price,wholesale_price,reseller_price,promo_price,min_stock,location,sellable,active,created_at
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (sku.strip(),barcode.strip(),brand.strip() or 'Tubito 35 ml',name.strip(),line.strip(),gender,concentration,FIXED_SIZE_ML,origin.strip(),category.strip(),'PERFUME',family.strip(),
                         ref_house.strip(),ref_name.strip(),inspired_house.strip(),inspired_name.strip(),relation.strip(),confidence.strip(),profile.strip(),priority,aliases.strip(),top.strip(),heart.strip(),base.strip(),season.strip(),use_time.strip(),batch.strip(),sup_opts[supplier_label],cost,sale,wholesale,reseller,promo,min_stock,location.strip(),int(sellable),1,now_iso())
                    )
                    if initial_stock>0:
                        add_inventory_move(cur.lastrowid,'STOCK_INICIAL',initial_stock,cost,'SETUP',None,'Carga inicial')
                    st.success('Perfume creado.')
                    st.rerun()
                except sqlite3.IntegrityError as e:
                    st.error(f'No se pudo crear: {e}')

    with tab4:
        inv=stock_df(active_only=False)
        inv=inv[inv.product_type!='DECANT'].copy() if not inv.empty else inv
        if inv.empty:
            st.info('Sin productos.')
        else:
            labels={product_label(r):int(r['id']) for _,r in inv.iterrows()}
            sel=st.selectbox('Elegir perfume',list(labels.keys()),key='catalog_card_v6')
            r=inv[inv.id==labels[sel]].iloc[0]
            a,b,c,d=st.columns(4)
            a.metric('Stock',f'{safe_float(r.stock):g}'); b.metric('Costo',money(r.avg_cost)); c.metric('Venta',money(r.sale_price)); d.metric('Valor stock',money(max(0,safe_float(r.stock))*safe_float(r.sale_price)))
            original=f"{r.inspired_house or ''} {r.inspired_name or ''}".strip() or 'Sin equivalencia definida'
            st.markdown(f"""<div class="ref35"><div class="r-title">{r.brand or ''} {r['name']} · 35 ml</div><div class="r-big">{original}</div>
            <div class="r-sub"><b>Referencia:</b> {r.reference_house or '—'} {r.reference_name or ''}<br><b>Relación:</b> {r.similarity_relation or '—'} · <b>Confianza:</b> {r.similarity_confidence or '—'}<br>
            <b>Familia:</b> {r.olfactory_family or '—'} · <b>Perfil:</b> {r.fragrance_profile or '—'}<br><b>Ubicación:</b> {r.location or '—'} · <b>Origen:</b> {r.origin_country or '—'}</div></div>""",unsafe_allow_html=True)

# ============================================================
# PAGE: INVENTORY
# ============================================================
elif page == "▤ Inventario":
    hero("Inventario 35 ml", "Todas las fragancias están visibles, tengan o no stock. El stock se controla por unidades y cada corrección queda registrada como movimiento.", "PERFUME 35 OS")
    inv = stock_df(active_only=False)
    inv = inv[inv.product_type!='DECANT'].copy() if not inv.empty else inv
    last = last_sale_by_product()
    if not inv.empty:
        inv = inv.merge(last,how='left',left_on='id',right_on='product_id')
        inv['stock_value']=inv.stock.clip(lower=0)*inv.avg_cost
        inv['retail_value']=inv.stock.clip(lower=0)*inv.sale_price
        inv['last_sale_date']=pd.to_datetime(inv.last_sale_date,errors='coerce')
        inv['days_without_sale']=(pd.Timestamp.today().normalize()-inv.last_sale_date).dt.days
        inv.loc[inv.last_sale_date.isna(),'days_without_sale']=9999
    active_inv=inv[inv.active==1].copy() if not inv.empty else inv
    units=safe_float(active_inv.stock.clip(lower=0).sum()) if not active_inv.empty else 0
    costv=safe_float(active_inv.stock_value.sum()) if not active_inv.empty else 0
    retailv=safe_float(active_inv.retail_value.sum()) if not active_inv.empty else 0
    critical=len(active_inv[(active_inv.min_stock>0)&(active_inv.stock<=active_inv.min_stock)]) if not active_inv.empty else 0
    zero=len(active_inv[active_inv.stock<=0]) if not active_inv.empty else 0
    k1,k2,k3,k4,k5=st.columns(5)
    k1.metric('Fragancias',len(active_inv) if not active_inv.empty else 0)
    k2.metric('Unidades físicas',f'{units:g}',f'{zero} sin stock')
    k3.metric('Stock a costo',money(costv))
    k4.metric('Stock a venta',money(retailv))
    k5.metric('Ganancia potencial',money(retailv-costv),f'{critical} para reponer')

    tabs=st.tabs(['Stock completo','Edición rápida','Movimientos','Ajuste puntual','Rotación','Ubicaciones'])
    with tabs[0]:
        if inv.empty:
            st.info('Sin productos.')
        else:
            a,b,c,d=st.columns([2.2,1,1,1])
            q=a.text_input('Buscar',placeholder='Nombre, original, marca, familia...',key='inv_search_v6')
            state=b.selectbox('Estado',['Todos','Con stock','Sin stock','Crítico'],key='inv_state_v6')
            active_mode=c.selectbox('Actividad',['Activos','Todos','Inactivos'],key='inv_active_v6')
            order=d.selectbox('Orden',['Nombre','Menor stock','Mayor stock','Mayor valor'],key='inv_order_v6')
            v=inv.copy()
            if q:
                qn=_norm35(q); blob=v.apply(lambda r:_norm35(_product_reference_text35(r)),axis=1); v=v[blob.str.contains(qn,regex=False)]
            if state=='Con stock': v=v[v.stock>0]
            elif state=='Sin stock': v=v[v.stock<=0]
            elif state=='Crítico': v=v[(v.min_stock>0)&(v.stock<=v.min_stock)]
            if active_mode=='Activos': v=v[v.active==1]
            elif active_mode=='Inactivos': v=v[v.active==0]
            if order=='Menor stock': v=v.sort_values(['stock','name'])
            elif order=='Mayor stock': v=v.sort_values(['stock','name'],ascending=[False,True])
            elif order=='Mayor valor': v=v.sort_values('retail_value',ascending=False)
            else: v=v.sort_values(['brand','name'])
            v=enrich_35ml_df(v)
            show=v[['sku','brand','name','Inspirado / similar a','stock','min_stock','avg_cost','sale_price','stock_value','retail_value','location','active']].copy()
            show.columns=['SKU','Marca','Nombre','Inspirado / similar a','Stock','Mínimo','Costo','Venta','Valor costo','Valor venta','Ubicación','Activo']
            st.dataframe(show,use_container_width=True,hide_index=True,height=670,column_config={
                'Stock':st.column_config.NumberColumn('Stock',format='%.0f'),'Mínimo':st.column_config.NumberColumn('Mínimo',format='%.0f'),
                'Costo':st.column_config.NumberColumn('Costo',format='$ %.0f'),'Venta':st.column_config.NumberColumn('Venta',format='$ %.0f'),
                'Valor costo':st.column_config.NumberColumn('Valor costo',format='$ %.0f'),'Valor venta':st.column_config.NumberColumn('Valor venta',format='$ %.0f'),
                'Activo':st.column_config.CheckboxColumn('Activo')})

    with tabs[1]:
        if inv.empty:
            st.info('Sin inventario.')
        else:
            st.markdown('<div class="edit-callout"><b>Edición rápida:</b> corregí stock final, costo, precio, mínimo y ubicación directamente. El stock no se pisa: la app crea un movimiento por la diferencia para conservar historial.</div>',unsafe_allow_html=True)
            q=st.text_input('Filtrar fragancias para editar',key='inv_edit_filter_v6')
            v=inv.copy()
            if q:
                qn=_norm35(q); blob=v.apply(lambda r:_norm35(_product_reference_text35(r)),axis=1); v=v[blob.str.contains(qn,regex=False)]
            editor=_product_editor_frame35(v,include_stock=True,compact=True)
            edited=st.data_editor(editor,use_container_width=True,hide_index=True,height=680,disabled=['ID','Stock actual'],column_config={
                'Costo':st.column_config.NumberColumn('Costo',min_value=0,format='$ %.0f'),
                'Precio venta':st.column_config.NumberColumn('Precio venta',min_value=0,format='$ %.0f'),
                'Stock actual':st.column_config.NumberColumn('Stock actual',format='%.0f'),
                'Stock objetivo':st.column_config.NumberColumn('Stock objetivo',min_value=0,step=1,format='%.0f'),
                'Stock mínimo':st.column_config.NumberColumn('Stock mínimo',min_value=0,step=1,format='%.0f'),
                'Vendible':st.column_config.CheckboxColumn('Vendible'),'Activo':st.column_config.CheckboxColumn('Activo')},key='inv_quick_editor_v6')
            if st.button('Guardar inventario',type='primary',use_container_width=True,key='save_inv_v6'):
                try:
                    upd,adj=save_product_editor35(edited); st.success(f'Inventario actualizado: {upd} fichas · {adj} ajustes de stock.'); st.rerun()
                except Exception as e: st.error(f'No pude guardar: {e}')

    with tabs[2]:
        moves=qdf("""SELECT im.id,im.date,p.sku,p.brand,p.name,im.move_type,im.qty,im.unit_cost,im.reference_type,im.reference_id,im.notes,im.user_name
                     FROM inventory_moves im JOIN products p ON p.id=im.product_id ORDER BY im.id DESC LIMIT 800""")
        st.dataframe(moves,use_container_width=True,hide_index=True,height=650)

    with tabs[3]:
        if inv.empty: st.info('Sin productos.')
        else:
            labels={product_label(r):int(r['id']) for _,r in inv.iterrows()}
            with st.form('adjust_stock_v6'):
                sel=st.selectbox('Producto',list(labels.keys())); kind=st.selectbox('Tipo',['AJUSTE_POSITIVO','AJUSTE_NEGATIVO','ROTURA','PERDIDA','REGALO','MUESTRA','USO_PERSONAL','DEVOLUCION'])
                qty=st.number_input('Cantidad',min_value=0.01,value=1.0,step=1.0); note=st.text_input('Motivo / observación'); submit=st.form_submit_button('Registrar movimiento',type='primary')
            if submit:
                sign=1 if kind in ['AJUSTE_POSITIVO','DEVOLUCION'] else -1; pid=labels[sel]
                if sign<0 and current_stock(pid)<qty: st.error('No hay stock suficiente.')
                else:
                    cost=safe_float(scalar('SELECT avg_cost FROM products WHERE id=?',(pid,),0)); add_inventory_move(pid,kind,sign*qty,cost,'MANUAL',None,note); st.success('Movimiento registrado.'); st.rerun()

    with tabs[4]:
        if inv.empty: st.info('Sin inventario.')
        else:
            age=inv[(inv.stock>0)&(inv.days_without_sale>=60)].copy(); age['days_without_sale']=age.days_without_sale.replace(9999,np.nan)
            if age.empty: st.success('No hay stock con más de 60 días sin venta.')
            else:
                st.warning(f"{money(age.stock_value.sum())} están inmovilizados en fragancias con baja o nula rotación.")
                st.dataframe(age[['brand','name','stock','stock_value','retail_value','last_sale_date','days_without_sale','sale_price']],use_container_width=True,hide_index=True,height=600)

    with tabs[5]:
        if inv.empty: st.info('Sin datos.')
        else:
            loc=inv.groupby(inv.location.fillna('Sin ubicación'),as_index=False).agg(SKUs=('id','count'),Unidades=('stock','sum'),Capital=('stock_value','sum'),Venta=('retail_value','sum'))
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
        inv.loc[(inv["daily_velocity"]==0)&(inv["min_stock"]>0)&(inv["stock"]<=inv["min_stock"]),"suggested_qty"]=np.maximum(
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
        low=inv[(inv.min_stock>0)&(inv.stock<=inv.min_stock)&(inv.active==1)&(inv.sellable==1)]
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
            low=inv[(inv.min_stock>0)&(inv.stock<=inv.min_stock)&(inv.active==1)]
            if low.empty:
                st.success("No hay productos por debajo del mínimo configurado.")
            else:
                st.dataframe(low[["brand","name","stock","min_stock","avg_cost"]],use_container_width=True,hide_index=True)
        elif "margen" in q:
            st.write(f"Margen del mes actual: **{mm:.1f}%**. Meta configurada: **{TARGET_MARGIN:.1f}%**.")
        elif any(x in q for x in ["parecido", "similar", "inspir", "dupe", "sauvage", "baccarat", "aventus", "original"]):
            libq = fragrance_library_df()
            qn = _norm35(question)
            # Prioritize direct token hits across the whole reference map.
            tokens = [t for t in qn.split() if len(t) >= 3 and t not in {"que","cual","cuales","perfume","parecido","similar","inspirado","original"}]
            blob = libq.apply(lambda r: _norm35(" ".join(str(r.get(c,"") or "") for c in libq.columns)), axis=1)
            mask = pd.Series(False, index=libq.index)
            for tok in tokens:
                mask = mask | blob.str.contains(tok, regex=False)
            ans = libq[mask].head(12) if tokens else pd.DataFrame()
            if ans.empty:
                st.info("No encontré esa referencia. Probá el buscador de Biblioteca 35 ml.")
            else:
                ans = ans.copy()
                ans["Referencia"] = (ans.designer_house.fillna("")+" "+ans.designer_name.fillna("")).str.strip().replace("","—")
                st.dataframe(ans[["tube_name","reference_house","Referencia","relation","profile"]].rename(columns={"tube_name":"35 ml","reference_house":"Marca","relation":"Relación","profile":"Perfil"}),use_container_width=True,hide_index=True)
        else:
            st.info("Puedo resolver ventas, productos top, reposición, margen, stock inmovilizado, cuentas por cobrar y también equivalencias de perfumes 35 ml.")

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
        _rep_revenue = safe_float(sales.total.sum())
        _rep_profit = reconciled_profit(start, end_ex, _rep_revenue)
        a.metric("Ventas",money(_rep_revenue))
        b.metric("Ganancia",money(_rep_profit))
        c.metric("Margen",pct(_rep_profit/_rep_revenue*100 if _rep_revenue else 0))
        d.metric("Unidades",f"{reconciled_sold_units(start,end_ex):g}")
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
# PAGE: GLOBAL DATA EDITOR
# ============================================================
elif page == "✎ Edición global":
    hero("Edición global", "Un único lugar para corregir la información almacenada en Google Sheets. Los identificadores técnicos quedan bloqueados; el resto de los campos puede editarse y guardarse.", "CONTROL DE DATOS")
    st.markdown('<div class="edit-callout"><b>Importante:</b> Catálogo e Inventario tienen editores especializados y más cómodos. Esta pantalla existe para que también puedas corregir clientes, proveedores, ventas, compras, caja, reservas, promociones, preferencias y demanda no cubierta sin salir de la app. <b>La auditoría es la única excepción:</b> es append-only para conservar trazabilidad.</div>',unsafe_allow_html=True)
    labels={
        'Productos':'products','Clientes':'customers','Proveedores':'suppliers','Vendedores':'vendors','Ventas':'sales','Detalle de ventas':'sale_items',
        'Movimientos de stock':'inventory_moves','Compras':'purchases','Detalle de compras':'purchase_items','Caja':'cash_moves','Gastos':'expenses',
        'Reservas':'reservations','Cuentas corrientes':'account_ledger','Promociones':'promotions','Campañas':'campaign_log',
        'Preferencias de clientes':'customer_preferences','Demanda no cubierta':'demand_requests',
        'Configuración':'settings','Usuarios':'users','Pools decant':'decant_pools'
    }
    c1,c2=st.columns([1.5,3])
    label=c1.selectbox('Conjunto de datos',list(labels.keys()),key='global_table_v6')
    table=labels[label]
    c2.caption(f"Google Sheets: {SHEET_NAMES.get(table,table)} · Tabla interna: {table}")
    df=qdf(f'SELECT * FROM {table}')
    if df.empty:
        st.info('Esta tabla todavía no tiene registros.')
    else:
        pk=_primary_key_for_table(table)
        st.caption(f"{len(df)} registros · clave técnica bloqueada: {pk or 'no detectada'}")
        edited=st.data_editor(df,use_container_width=True,hide_index=True,height=690,disabled=[pk] if pk else [],key=f'global_editor_{table}_v6')
        if st.button('Guardar cambios',type='primary',use_container_width=True,key=f'global_save_{table}_v6'):
            try:
                n=save_generic_table35(table,edited); st.success(f'{n} registros guardados en {SHEET_NAMES.get(table,table)}.'); st.rerun()
            except Exception as e:
                st.error(f'No pude guardar: {e}')

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

        st.markdown("### Cierre histórico conciliado")
        st.caption(
            "La app conserva el cierre real confirmado del primer ciclo y suma normalmente todos los movimientos posteriores."
        )
        _hr = history_reconciliation()
        with st.expander("Editar cierre histórico", expanded=False):
            with st.form("history_recon_form"):
                hr_enabled = st.checkbox("Usar cierre histórico", value=_hr["enabled"])
                h1,h2 = st.columns(2)
                hr_start = h1.date_input("Desde", value=_hr["start"], key="hr_start")
                hr_cutoff = h2.date_input("Corte exclusivo", value=_hr["cutoff"], key="hr_cutoff")
                h3,h4,h5 = st.columns(3)
                hr_in = h3.number_input("Unidades ingresadas reales", min_value=0.0, value=float(_hr["units_in"]), step=1.0)
                hr_sold = h4.number_input("Unidades vendidas reales", min_value=0.0, value=float(_hr["units_sold"]), step=1.0)
                hr_cost = h5.number_input("Costo unitario histórico", min_value=0.0, value=float(_hr["unit_cost"]), step=100.0)
                hr_save = st.form_submit_button("Guardar cierre", type="primary")
            if hr_save:
                if hr_cutoff <= hr_start:
                    st.error("El corte debe ser posterior a la fecha inicial.")
                else:
                    set_setting("history_recon_enabled", "1" if hr_enabled else "0")
                    set_setting("history_recon_start", hr_start.isoformat())
                    set_setting("history_recon_cutoff", hr_cutoff.isoformat())
                    set_setting("history_recon_units_in", hr_in)
                    set_setting("history_recon_units_sold", hr_sold)
                    set_setting("history_recon_unit_cost", hr_cost)
                    st.success("Cierre histórico actualizado.")
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
st.caption(f"{APP_NAME} · v{APP_VERSION} · {BUSINESS_NAME} · Google Sheets · Edición 35 ml")
