import streamlit as st
import pandas as pd
from datetime import datetime
import qrcode
from io import BytesIO
import gspread
from google.oauth2.service_account import Credentials
import pytz
import hashlib
import urllib.parse

# ============================================================
# ZONA WAKTU & SESSION STATE
# ============================================================
tz_wib         = pytz.timezone('Asia/Jakarta')
waktu_sekarang = datetime.now(tz_wib)

DEFAULTS = {
    'prodi':             'Bisnis Digital',
    'dosen_login':       False,
    'sudah_presensi':    False,
    'halaman':           'landing',
    'nama_dosen_login':  None,
    'nim_terverifikasi': None,
    'nama_terverifikasi':None,
    'konfirmasi_data':   None,
    'qr_makul':          None,
    'qr_pertemuan':      None,
    'qr_semester':       None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# CONFIG HALAMAN
# ============================================================
st.set_page_config(
    page_title="Presensi Bisnis Digital & Aktuaria",
    page_icon="📝",
    layout="centered"
)

# ============================================================
# CSS — Disesuaikan dengan HTML design system
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
header {visibility:hidden;} footer {visibility:hidden;} #MainMenu {visibility:hidden;}
.stApp { background: #f8f9ff !important; }
.block-container { max-width: 720px !important; padding: 0 1.5rem 5rem !important; }

/* ── Text Inputs & Textarea ── */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input {
    background: #ffffff !important;
    color: #0b1c30 !important;
    border: 1.5px solid #c7c4d8 !important;
    border-radius: 12px !important;
    font-size: 15px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #3525cd !important;
    box-shadow: 0 0 0 3px rgba(53,37,205,0.12) !important;
}
div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stTextArea"] textarea::placeholder {
    color: #464555 !important; opacity: 0.45 !important;
}

/* ── Selectbox ── */
div[data-testid="stSelectbox"] > div[data-baseweb="select"] > div {
    background: #ffffff !important;
    border: 1.5px solid #c7c4d8 !important;
    border-radius: 12px !important;
}
div[data-baseweb="select"] span, div[data-baseweb="select"] div,
div[data-testid="stSelectbox"] span {
    color: #0b1c30 !important; background: transparent !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
div[data-baseweb="select"] svg { fill: #464555 !important; opacity: 0.6; }
div[data-baseweb="popover"], ul[data-baseweb="menu"], div[role="listbox"] {
    background: #ffffff !important;
    border: 1px solid #c7c4d8 !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.10) !important;
}
li[role="option"], div[role="option"] {
    background: #ffffff !important; color: #0b1c30 !important;
}
li[role="option"]:hover, li[aria-selected="true"] {
    background: rgba(53,37,205,0.08) !important;
}

/* ── Labels ── */
label, .stLabel {
    color: #464555 !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ── Buttons ── */
button[kind="formSubmit"] {
    background: linear-gradient(135deg, #3525cd 0%, #0058be 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 14px 24px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    width: 100% !important;
    box-shadow: 0 4px 16px rgba(53,37,205,0.30) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
button[kind="primary"], button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #3525cd 0%, #0058be 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 12px rgba(53,37,205,0.25) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
button[kind="secondary"], button[data-testid="baseButton-secondary"] {
    background: #ffffff !important;
    color: #0b1c30 !important;
    border: 1.5px solid #c7c4d8 !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ── Tabs ── */
div[data-baseweb="tab-list"] {
    background: #e5eeff !important;
    border-radius: 16px !important;
    padding: 4px !important;
    gap: 2px !important;
    border: none !important;
}
button[data-baseweb="tab"] {
    color: #464555 !important;
    background: transparent !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 10px 16px !important;
    border: none !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #3525cd !important;
    background: #ffffff !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}

/* ── Container Borders ── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid rgba(199,196,216,0.45) !important;
    border-radius: 16px !important;
}

/* ── Metrics ── */
div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid rgba(199,196,216,0.45) !important;
    border-radius: 16px !important;
    padding: 16px 20px !important;
}
[data-testid="stMetricValue"] {
    color: #3525cd !important;
    font-weight: 800 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ── Expanders ── */
details[data-testid="stExpander"] > summary {
    background: #eff4ff !important;
    border: 1px solid rgba(199,196,216,0.45) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    color: #0b1c30 !important;
}
div[data-testid="stExpanderDetails"] {
    background: #ffffff !important;
    border: 1px solid rgba(199,196,216,0.25) !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
}

/* ── Alerts & DataFrames ── */
div[data-testid="stAlert"] { border-radius: 12px !important; }
div[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── Radio ── */
div[data-testid="stRadio"] label, div[data-testid="stRadio"] p {
    color: #0b1c30 !important;
}
div[data-testid="stRadio"] > div {
    background: #ffffff !important;
    border: 1px solid rgba(199,196,216,0.45) !important;
    border-radius: 12px !important;
    padding: 8px 16px !important;
}

/* ── Password ── */
input[type="password"] {
    background: #ffffff !important;
    color: #0b1c30 !important;
    border: 1.5px solid #c7c4d8 !important;
    border-radius: 12px !important;
}

/* ── Progress Bar ── */
div[data-testid="stProgress"] > div > div { background: #3525cd !important; }
div[data-testid="stProgress"] > div {
    background: #e5eeff !important;
    border-radius: 999px !important;
}

/* ══════════════════════════════════════════════════
   KOMPONEN KUSTOM
══════════════════════════════════════════════════ */

/* Header Banner */
.header-banner {
    background: linear-gradient(135deg, #3525cd 0%, #0058be 100%);
    padding: 28px 32px 24px;
    border-radius: 0 0 28px 28px;
    color: white;
    text-align: center;
    margin: -1rem -1.5rem 28px;
    box-shadow: 0 8px 28px rgba(53,37,205,0.28);
}
.header-banner h1 {
    color: white !important;
    font-weight: 800;
    font-size: 26px;
    margin: 0 0 5px;
    letter-spacing: -0.02em;
}
.header-banner p { color: rgba(255,255,255,0.85) !important; font-size: 13px; margin: 0; }

/* Clock Box */
.clock-box {
    background: rgba(245,158,11,0.10);
    border: 1px solid rgba(245,158,11,0.38);
    border-radius: 14px;
    padding: 12px 18px;
    text-align: center;
    color: #d97706;
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

/* Kelas Badge */
.kelas-badge {
    background: #ffffff;
    border-left: 4px solid #4f46e5;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    border: 1px solid rgba(199,196,216,0.35);
}
.kelas-badge b { color: #0b1c30; font-size: 15px; }
.kelas-badge .sub { color: #464555; font-size: 13px; opacity: 0.75; margin-top: 3px; }

/* Akses Card */
.akses-card {
    background: #ffffff;
    border-radius: 20px;
    padding: 28px 20px;
    text-align: center;
    border: 1.5px solid rgba(199,196,216,0.40);
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    margin-bottom: 10px;
    transition: all 0.2s;
}
.akses-card:hover { border-color: #3525cd; }
.akses-icon { font-size: 42px; margin-bottom: 10px; }
.akses-title { font-weight: 700; font-size: 17px; color: #0b1c30; margin-bottom: 6px; }
.akses-sub { font-size: 12px; color: #464555; opacity: 0.65; }

/* Section Label */
.section-label {
    font-size: 11px; font-weight: 700; color: #464555;
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 10px;
    display: block;
}

/* Active Class Badge (status bar) */
.badge-aktif-bar {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 12px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    font-weight: 700;
    color: #15803d;
    margin-bottom: 4px;
}
.dot-pulse {
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-dot 1.5s infinite;
    flex-shrink: 0;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.75); }
}

/* QR Banner (scan berhasil) */
.qr-banner {
    background: linear-gradient(135deg, rgba(16,185,129,0.10), rgba(99,102,241,0.06));
    border: 2px solid rgba(16,185,129,0.40);
    border-radius: 20px;
    padding: 18px 22px;
    margin-bottom: 16px;
}
.qr-banner .title { font-weight: 700; font-size: 15px; color: #0b1c30; }
.qr-banner .sub { font-size: 13px; color: #464555; margin-top: 4px; }
.qr-banner .hint { font-size: 12px; color: #464555; opacity: 0.60; margin-top: 3px; }

/* Konfirmasi Berhasil */
.konfirmasi-box {
    background: linear-gradient(135deg, rgba(16,185,129,0.10), rgba(16,185,129,0.04));
    border: 2px solid rgba(16,185,129,0.45);
    border-radius: 24px;
    padding: 32px 24px;
    text-align: center;
    margin-bottom: 16px;
    box-shadow: 0 8px 28px rgba(16,185,129,0.12);
}
.konfirmasi-box .check-icon {
    width: 56px; height: 56px;
    background: #10B981;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 14px;
    font-size: 30px;
}
.konfirmasi-box h2 { color: #10B981 !important; font-size: 22px; font-weight: 800; margin-bottom: 6px; }
.konfirmasi-box .nama { font-size: 18px; font-weight: 700; color: #0b1c30; margin: 0; }
.konfirmasi-box .nim-sub { font-size: 13px; color: #464555; opacity: 0.65; margin: 3px 0 14px; }
.konfirmasi-box .divider { border-top: 1px solid rgba(16,185,129,0.2); margin: 14px 0; }
.konfirmasi-box .info-row { font-size: 14px; color: #0b1c30; margin: 4px 0; }
.konfirmasi-box .info-sub { font-size: 13px; color: #464555; opacity: 0.70; margin: 3px 0; }

/* Counter Box */
.counter-box {
    background: #ffffff;
    border-radius: 18px;
    padding: 22px 24px;
    text-align: center;
    border: 1px solid rgba(199,196,216,0.40);
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    margin-top: 12px;
}
.counter-box .angka {
    font-size: 54px; font-weight: 800;
    color: #4f46e5; line-height: 1; letter-spacing: -0.02em;
}
.counter-box .sub {
    font-size: 13px; color: #464555; opacity: 0.65; margin-top: 8px;
}

/* Time Info Card */
.time-card {
    background: rgba(255,255,255,0.88);
    border: 1px solid rgba(199,196,216,0.35);
    border-radius: 18px;
    padding: 18px 22px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}
.time-card .label {
    font-size: 10px; font-weight: 700; letter-spacing: 0.06em;
    text-transform: uppercase; color: #464555; opacity: 0.60; margin-bottom: 4px;
}
.time-card .value { font-size: 15px; font-weight: 700; color: #10B981; }

/* Progress Bar Custom */
.progress-bar-wrap { margin-top: 12px; }
.progress-bar-header {
    display: flex; justify-content: space-between;
    font-size: 11px; color: #464555; opacity: 0.55; margin-bottom: 5px;
}
.progress-bar-track {
    background: rgba(199,196,216,0.35);
    border-radius: 999px; height: 7px; overflow: hidden;
}
.progress-bar-fill {
    height: 100%; border-radius: 999px;
    transition: width 0.3s ease;
}

/* Info Box */
.info-box {
    background: rgba(79,70,229,0.06);
    border: 1px solid rgba(79,70,229,0.18);
    border-radius: 14px;
    padding: 16px 18px;
    font-size: 13px;
    color: #0b1c30;
    line-height: 1.6;
}
.info-box b { color: #3525cd; }

/* Histori Item (monitor dosen) */
.histori-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 0;
}
.histori-avatar {
    width: 38px; height: 38px;
    border-radius: 50%;
    background: #e5eeff;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 13px; color: #3525cd;
    flex-shrink: 0;
}
.histori-name { font-weight: 600; font-size: 14px; color: #0b1c30; }
.histori-time { font-size: 12px; color: #464555; opacity: 0.60; margin-top: 2px; }
.histori-badge {
    background: #dcfce7; color: #15803d;
    border: 1px solid #86efac;
    border-radius: 999px; padding: 3px 10px;
    font-size: 10px; font-weight: 700;
    margin-left: auto; flex-shrink: 0;
}

/* Divider Light */
.divider-light { border: none; border-top: 1px solid rgba(199,196,216,0.25); margin: 8px 0; }

/* Login Header */
.login-header {
    text-align: center; margin-bottom: 24px; padding-top: 8px;
}
.login-header .icon-wrap {
    width: 60px; height: 60px;
    background: linear-gradient(135deg, #3525cd, #4f46e5);
    border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 14px;
    box-shadow: 0 6px 16px rgba(53,37,205,0.30);
    font-size: 28px;
}
.login-header h2 {
    color: #4f46e5 !important;
    font-size: 22px !important;
    font-weight: 800 !important;
    letter-spacing: -0.01em;
    margin-bottom: 6px;
}
.login-header p {
    font-size: 13px; color: #464555; max-width: 300px; margin: 0 auto;
}

/* Status Sekarang Card */
.status-card {
    background: rgba(255,255,255,0.88);
    border-left: 4px solid #10B981;
    border-radius: 14px;
    padding: 16px 20px;
    border: 1px solid rgba(199,196,216,0.30);
    border-left: 4px solid #10B981;
    margin-bottom: 8px;
}
.status-aktif-label {
    font-size: 10px; font-weight: 700; letter-spacing: 0.06em;
    text-transform: uppercase; color: #10B981;
    display: flex; align-items: center; gap: 6px;
    margin-bottom: 6px;
}

/* Dashboard Dosen Title */
.dashboard-title {
    font-size: 22px; font-weight: 800;
    color: #0b1c30; letter-spacing: -0.01em;
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# GOOGLE SHEETS — CACHE AGRESIF
# ============================================================
SHEET_ID = "1Msh_H8XgFpAJiQFuPB7l4V_0YDPcNWSBEW6y9X9eBk8"
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_sheet():
    creds  = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)

STATUS_SHEET = "STATUS_KELAS"
BATAS_JAM    = 24   # Kelas otomatis tutup setelah N jam

@st.cache_data(ttl=30)
def baca_semua_kelas_aktif_cached():
    try:
        sheet = get_sheet()
        try:
            ws = sheet.worksheet(STATUS_SHEET)
        except gspread.exceptions.WorksheetNotFound:
            ws = sheet.add_worksheet(title=STATUS_SHEET, rows="50", cols="7")
            ws.append_row(["makul","semester","pertemuan","aktif","dosen_key","waktu_buka"])
            return []
        data = ws.get_all_records()
        return [r for r in data if str(r.get("aktif","0")) == "1"]
    except Exception:
        return []

def cek_dan_tutup_kelas_kadaluarsa():
    try:
        sheet  = get_sheet()
        ws     = sheet.worksheet(STATUS_SHEET)
        data   = ws.get_all_values()
        if not data or len(data) < 2:
            return
        header = data[0]
        try:
            col_ak = header.index("aktif") + 1
            col_wb = header.index("waktu_buka") + 1
        except ValueError:
            return
        sekarang      = datetime.now(tz_wib)
        ada_perubahan = False
        for i, row in enumerate(data[1:], start=2):
            if len(row) < max(col_ak, col_wb):
                continue
            if str(row[col_ak - 1]) != "1":
                continue
            waktu_buka_str = str(row[col_wb - 1]).strip()
            if not waktu_buka_str:
                continue
            try:
                waktu_buka_dt = datetime.fromisoformat(waktu_buka_str)
                if waktu_buka_dt.tzinfo is None:
                    waktu_buka_dt = tz_wib.localize(waktu_buka_dt)
                selisih_jam = (sekarang - waktu_buka_dt).total_seconds() / 3600
                if selisih_jam >= BATAS_JAM:
                    ws.update_cell(i, col_ak, "0")
                    ada_perubahan = True
            except Exception:
                continue
        if ada_perubahan:
            baca_semua_kelas_aktif_cached.clear()
            baca_status_kelas_dosen_cached.clear()
    except Exception:
        pass

def baca_semua_kelas_aktif():
    return baca_semua_kelas_aktif_cached()

@st.cache_data(ttl=15)
def baca_status_kelas_dosen_cached(dosen_key):
    try:
        sheet = get_sheet()
        ws    = sheet.worksheet(STATUS_SHEET)
        for row in ws.get_all_records():
            if row.get("dosen_key","") == dosen_key:
                return {
                    "makul":      row.get("makul","Belum Diatur"),
                    "semester":   str(row.get("semester","-")),
                    "pertemuan":  str(row.get("pertemuan","-")),
                    "aktif":      str(row.get("aktif","0")) == "1",
                    "waktu_buka": str(row.get("waktu_buka","")),
                }
    except Exception:
        pass
    return {"makul":"Belum Diatur","semester":"-","pertemuan":"-","aktif":False,"waktu_buka":""}

def baca_status_kelas_dosen(dosen_key):
    return baca_status_kelas_dosen_cached(dosen_key)

def tulis_status_kelas(makul, semester, pertemuan, dosen_key, aktif=True):
    sheet = get_sheet()
    try:    ws = sheet.worksheet(STATUS_SHEET)
    except: ws = sheet.add_worksheet(title=STATUS_SHEET, rows="50", cols="7")
    data   = ws.get_all_values()
    header = data[0] if data else []
    try:    col_dk = header.index("dosen_key") + 1
    except:
        ws.append_row(["makul","semester","pertemuan","aktif","dosen_key","waktu_buka"])
        col_dk = 5
    waktu_buka_str = datetime.now(tz_wib).isoformat() if aktif else ""
    row_idx = None
    for i, row in enumerate(data[1:], start=2):
        if len(row) >= col_dk and row[col_dk-1] == dosen_key:
            row_idx = i; break
    new_row = [makul, semester, pertemuan, "1" if aktif else "0", dosen_key, waktu_buka_str]
    if row_idx: ws.update(f"A{row_idx}:F{row_idx}", [new_row])
    else:       ws.append_row(new_row)
    baca_semua_kelas_aktif_cached.clear()
    baca_status_kelas_dosen_cached.clear()

def tutup_kelas(dosen_key):
    try:
        sheet  = get_sheet()
        ws     = sheet.worksheet(STATUS_SHEET)
        data   = ws.get_all_values()
        header = data[0]
        col_dk = header.index("dosen_key") + 1
        col_ak = header.index("aktif") + 1
        for i, row in enumerate(data[1:], start=2):
            if len(row) >= col_dk and row[col_dk-1] == dosen_key:
                ws.update_cell(i, col_ak, "0")
                baca_semua_kelas_aktif_cached.clear()
                baca_status_kelas_dosen_cached.clear()
                return True
    except Exception:
        pass
    return False

def hapus_entri_presensi(nama_ws, nim, pertemuan):
    try:
        sheet  = get_sheet()
        ws     = sheet.worksheet(nama_ws)
        data   = ws.get_all_values()
        header = data[0] if data else []
        try:
            col_nim = header.index("NIM") + 1
            col_prt = header.index("Pertemuan Ke") + 1
        except ValueError:
            return False, "Kolom NIM/Pertemuan Ke tidak ditemukan."
        for i, row in enumerate(data[1:], start=2):
            if (len(row) >= max(col_nim, col_prt) and
                    str(row[col_nim-1]).strip() == str(nim).strip() and
                    str(row[col_prt-1]).strip() == str(pertemuan).strip()):
                ws.delete_rows(i)
                return True, "Data berhasil dihapus."
        return False, "Data tidak ditemukan."
    except gspread.exceptions.WorksheetNotFound:
        return False, "Sheet tidak ditemukan."
    except Exception as e:
        return False, str(e)

def get_or_create_worksheet(sheet, title):
    try:    return sheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=title, rows="1000", cols="10")
        ws.append_row(["Tanggal","Jam Isi","Semester","Pertemuan Ke","NIM","Nama","Rangkuman Materi"])
        return ws

def simpan_ke_sheets(data: dict):
    sheet = get_sheet()
    raw   = data["Mata Kuliah"]
    safe  = raw.replace("/","-").replace(":","-").replace("\\","-")
    if len(safe) > 28:
        suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
        safe   = safe[:24] + "_" + suffix
    ws = get_or_create_worksheet(sheet, safe)
    if not ws.get_all_values():
        ws.append_row(["Tanggal","Jam Isi","Semester","Pertemuan Ke","NIM","Nama","Rangkuman Materi"])
    ws.append_row([
        data["Tanggal"], data["Jam Isi"],
        data["Semester"], data["Pertemuan Ke"],
        data["NIM"], data["Nama"], data["Rangkuman Materi"]
    ])

@st.cache_data(ttl=20)
def hitung_hadir(makul, pertemuan):
    try:
        sheet = get_sheet()
        raw   = makul
        safe  = raw.replace("/","-").replace(":","-").replace("\\","-")
        if len(safe) > 28:
            suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
            safe   = safe[:24] + "_" + suffix
        ws   = sheet.worksheet(safe)
        data = ws.get_all_records()
        return sum(1 for r in data if str(r.get("Pertemuan Ke","")) == str(pertemuan))
    except Exception:
        return 0

def generate_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E293B", back_color="#FFFFFF")
    buf = BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()

# ============================================================
# DATA JADWAL DOSEN
# ============================================================
DATA_JADWAL_BD = {
    "Riyan Dwi Yulian P, S.Kom., M.Kom.": [
        "Analisis Perancangan Berbasis Objek A",
        "Analisis Perancangan Berbasis Objek B",
        "Mata Kuliah Pilihan Digital (Data Analyze) A",
        "Pemrograman Mobile",
        "Data Mining A", "Data Mining B",
        "Mata Kuliah Pilihan Digital (Data Analyze) B"
    ],
    "Esti Nur Wakhidah, S.Pd., M.M.": [
        "Manajemen Pemasaran Bisnis A", "Metodologi Penelitian B",
        "Komunikasi Bisnis", "Metodologi Penelitian A",
        "Manajemen Pemasaran Bisnis B"
    ],
    "Didik Adi Sabara, S.M., M.E.": [
        "Mentoring Bisnis Digital A", "Mentoring Bisnis Digital B",
        "E-Commerce", "Kewirausahaan Digital A", "Kewirausahaan Digital B"
    ],
    "Nour Mohammed Moussa Al Fattah M.Pd.": ["AIK 2 A","AIK 4","AIK 2 B"],
    "Ridhwan Sinatria, S.E., M.M.": [
        "Manajemen Sumber Daya Manusia B",
        "Mata Kuliah Pilihan Bisnis (Ekonomi Digital) A",
        "Manajemen Sumber Daya Manusia A",
        "Mata Kuliah Pilihan Bisnis (Ekonomi Digital) B",
        "Manajemen Risiko",
        "Kerja Praktek A (Team Teaching)", "Kerja Praktek B (Team Teaching)"
    ],
    "Kartika Dewi Permatasari, S.Ak., M.Ak., Ak.": [
        "Dasar-dasar Akuntansi A", "Dasar-dasar Akuntansi B",
        "Perpajakan", "Kerja Praktek A (Team Teaching)", "Kerja Praktek B (Team Teaching)"
    ],
    "Sriyati., S.Kom., M.Kom.": [
        "Pemrograman Web A","Basis Data","Pemrograman Web B","Sistem Pendukung Keputusan"
    ],
    "Doni Uji Windiatmoko, S.Pd., M.Pd.": ["Kewarganegaraan B","Kewarganegaraan A"],
    "Purwati, S.S., M.Hum.": ["Bahasa Inggris 2 A","Bahasa Inggris 2 B"],
}

DATA_JADWAL_AKT = {
    "Miftahul Jannah, S.Pd., M.Mat.": [
        "Algoritma dan Pemrogaman I A (Sebelum UTS)",
        "Pengantar Teori Ekonomi Mikro A (Sebelum UTS)",
        "Pengantar Teori Ekonomi Mikro A (Setelah UTS)",
        "Pengantar Akuntansi I A (Setelah UTS)",
        "Algoritma dan Pemrogaman I B (Sebelum UTS)",
        "Pengantar Teori Ekonomi Mikro B (Sebelum UTS)",
        "Pengantar Teori Ekonomi Mikro B (Setelah UTS)",
        "Pengantar Akuntansi I B (Setelah UTS)"
    ],
    "Adin Nadiya Ifati, S.Pd., M.Mat.": [
        "Algoritma dan Pemrogaman I A (Setelah UTS)",
        "Pengantar Akuntansi I A (Sebelum UTS)",
        "Kalkulus II A (Sebelum UTS)", "Kalkulus II A (Setelah UTS)",
        "Algoritma dan Pemrogaman I B (Setelah UTS)",
        "Pengantar Akuntansi I B (Sebelum UTS)",
        "Kalkulus II B (Sebelum UTS)", "Kalkulus II B (Setelah UTS)"
    ],
    "Rifki Chandra Utama, S.Si., M.Sc.": [
        "Matematika Keuangan I A (Sebelum UTS)", "Matematika Keuangan I A (Setelah UTS)",
        "Matematika Keuangan I B (Sebelum UTS)", "Matematika Keuangan I B (Setelah UTS)",
        "Pengantar Matematika Aktuaria II (Sebelum UTS)", "Pengantar Matematika Aktuaria II (Setelah UTS)",
        "Pengantar Teori Risiko I (Sebelum UTS)", "Pengantar Teori Risiko I (Setelah UTS)",
        "Pengelolaan Dana Pensiun (Sebelum UTS)", "Pengelolaan Dana Pensiun (Setelah UTS)"
    ],
    "Nour Muhammed Moussa Al-Fattah, S.Ag., M.Pd.": [
        "Al-Islam dan Kemuhammadiyahan II A (Sebelum UTS)",
        "Al-Islam dan Kemuhammadiyahan II A (Setelah UTS)",
        "Al-Islam dan Kemuhammadiyahan II B (Sebelum UTS)",
        "Al-Islam dan Kemuhammadiyahan II B (Setelah UTS)",
        "Al-Islam dan Kemuhammadiyahan IV (Sebelum UTS)",
        "Al-Islam dan Kemuhammadiyahan IV (Setelah UTS)"
    ],
    "Juwita Dien Maulida, S.Stat., M.Sc.": [
        "Pengantar Teori Probabilitas A (Sebelum UTS)",
        "Pengantar Teori Probabilitas A (Setelah UTS)",
        "Pengantar Teori Probabilitas B (Sebelum UTS)",
        "Pengantar Teori Probabilitas B (Setelah UTS)",
        "Proses Stokastik (Sebelum UTS)", "Proses Stokastik (Setelah UTS)"
    ],
    "Doni Uji Windiatmoko, S.Pd., M.Pd.": [
        "Kewarganegaraan A (Sebelum UTS)", "Kewarganegaraan A (Setelah UTS)",
        "Kewarganegaraan B (Sebelum UTS)", "Kewarganegaraan B (Setelah UTS)"
    ],
    "Ridhwan Sinatria, S.E., M.M.": [
        "Kewirausahaan (Sebelum UTS)", "Kewirausahaan (Setelah UTS)"
    ],
    "Nestria Agista, S.Stat., M.Sc.": [
        "Analisis Regresi (Sebelum UTS)", "Analisis Regresi (Setelah UTS)",
        "Statistika Matematika II (Sebelum UTS)", "Statistika Matematika II (Setelah UTS)"
    ],
    "Purwati, M.Hum.": ["Bahasa Inggris II (Sebelum UTS)", "Bahasa Inggris II (Setelah UTS)"],
    "Kartika Dewi Permatasari, S.AK., M.AK., AK.": [
        "Perpajakan (Sebelum UTS)", "Perpajakan (Setelah UTS)"
    ]
}

def get_makul_dosen(nama_dosen):
    if nama_dosen in DATA_JADWAL_BD:  return DATA_JADWAL_BD[nama_dosen]
    if nama_dosen in DATA_JADWAL_AKT: return DATA_JADWAL_AKT[nama_dosen]
    return []

def ke_halaman(nama):
    st.session_state['halaman'] = nama
    st.rerun()

# ============================================================
# HANDLE QR PARAMS — auto-fill sesi dari URL
# ============================================================
params = st.query_params
if params.get("makul") and not st.session_state.get('qr_makul'):
    st.session_state['qr_makul']     = params.get("makul")
    st.session_state['qr_pertemuan'] = params.get("pertemuan","")
    st.session_state['qr_semester']  = params.get("semester","")
    if st.session_state['halaman'] == 'landing':
        st.session_state['halaman'] = 'mahasiswa'

# Cek kelas kadaluarsa
cek_dan_tutup_kelas_kadaluarsa()

# ============================================================
# HEADER GLOBAL
# ============================================================
st.markdown("""
    <div class="header-banner">
        <h1>📝 PRESENSI PERKULIAHAN</h1>
        <p>Bisnis Digital &amp; Aktuaria — Beta ver 3.0</p>
    </div>
""", unsafe_allow_html=True)

# ============================================================
# HALAMAN LANDING
# ============================================================
if st.session_state['halaman'] == 'landing':

    # ── Pilih Program Studi ──────────────────────────────────
    st.markdown('<span class="section-label">Pilih Program Studi</span>', unsafe_allow_html=True)
    idx_prodi      = 0 if st.session_state['prodi'] == 'Bisnis Digital' else 1
    prodi_terpilih = st.radio(
        "Program Studi", ["Bisnis Digital", "Aktuaria"],
        index=idx_prodi, horizontal=True, label_visibility="collapsed"
    )
    st.session_state['prodi'] = prodi_terpilih

    st.markdown("<hr style='border:none;border-top:1px solid rgba(199,196,216,0.30);margin:16px 0;'>", unsafe_allow_html=True)

    # ── Status Kelas Aktif ───────────────────────────────────
    st.markdown('<span class="section-label">Status Kelas Aktif</span>', unsafe_allow_html=True)

    semua_kelas_aktif    = baca_semua_kelas_aktif()
    jadwal_prodi         = DATA_JADWAL_AKT if prodi_terpilih == 'Aktuaria' else DATA_JADWAL_BD
    dosen_valid          = list(jadwal_prodi.keys())
    kelas_landing_aktif  = [k for k in semua_kelas_aktif if k['dosen_key'] in dosen_valid]

    if kelas_landing_aktif:
        n = len(kelas_landing_aktif)
        st.markdown(
            f'<div class="badge-aktif-bar">'
            f'<span class="dot-pulse"></span>'
            f'{n} KELAS TERBUKA SAAT INI (PRODI {prodi_terpilih.upper()})'
            f'</div>',
            unsafe_allow_html=True
        )
        for k in kelas_landing_aktif:
            nm = k['makul'].rsplit(' (', 1)[0]
            nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
            st.markdown(f"""
                <div class="kelas-badge">
                    <b>📚 {nm}</b>
                    <div class="sub">👨‍🏫 {nd} &nbsp;|&nbsp; Pertemuan {k['pertemuan']}</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"🕒 Belum ada kelas yang dibuka oleh dosen {prodi_terpilih} saat ini.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Pilih Akses ──────────────────────────────────────────
    st.markdown('<span class="section-label">Pilih Akses Anda</span>', unsafe_allow_html=True)

    col_mhs, col_dos = st.columns(2)
    with col_mhs:
        st.markdown("""
            <div class="akses-card">
                <div class="akses-icon">🧑‍🎓</div>
                <div class="akses-title">Mahasiswa</div>
                <div class="akses-sub">Isi daftar hadir</div>
            </div>""", unsafe_allow_html=True)
        if st.button("Masuk Mahasiswa", use_container_width=True, key="btn_mhs"):
            ke_halaman('mahasiswa')

    with col_dos:
        st.markdown("""
            <div class="akses-card">
                <div class="akses-icon">👨‍🏫</div>
                <div class="akses-title">Dosen</div>
                <div class="akses-sub">Kelola kelas &amp; rekap</div>
            </div>""", unsafe_allow_html=True)
        if st.button("Masuk Dosen", use_container_width=True, key="btn_dos"):
            ke_halaman('dosen')

    st.markdown("""
        <hr style='border:none;border-top:1px solid rgba(199,196,216,0.28);margin:32px 0 16px;'>
        <p style='text-align:center;font-size:12px;color:#464555;opacity:0.65;'>
            © 2026 Institut Teknologi dan Bisnis Muhammadiyah Purbalingga
        </p>
    """, unsafe_allow_html=True)


# ============================================================
# HALAMAN MAHASISWA
# ============================================================
elif st.session_state['halaman'] == 'mahasiswa':

    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← Kembali", key="back_mhs"):
            st.session_state['qr_makul']       = None
            st.session_state['qr_pertemuan']   = None
            st.session_state['qr_semester']    = None
            st.session_state['sudah_presensi'] = False
            ke_halaman('landing')

    prodi_mhs = st.session_state.get('prodi', 'Bisnis Digital')

    # ── Halaman Konfirmasi Berhasil ──────────────────────────
    if st.session_state.get('sudah_presensi') and st.session_state.get('konfirmasi_data'):
        konfirmasi   = st.session_state['konfirmasi_data']
        jumlah_hadir = hitung_hadir(konfirmasi['makul_raw'], konfirmasi['pertemuan'])

        st.markdown(f"""
            <div class="konfirmasi-box">
                <div class="check-icon">✅</div>
                <h2>Presensi Berhasil!</h2>
                <p class="nama">{konfirmasi['nama']}</p>
                <p class="nim-sub">NIM: {konfirmasi['nim']}</p>
                <div class="divider"></div>
                <p class="info-row">📚 {konfirmasi['makul']}</p>
                <p class="info-sub">Semester {konfirmasi['semester']} &nbsp;·&nbsp; Pertemuan ke-{konfirmasi['pertemuan']}</p>
                <p class="info-sub">🗓️ {konfirmasi['tanggal']} &nbsp;·&nbsp; ⏰ {konfirmasi['jam']} WIB</p>
            </div>
            <div class="counter-box">
                <div class="angka">{jumlah_hadir}</div>
                <div class="sub">👥 Mahasiswa hadir di sesi ini</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Kembali ke Beranda", use_container_width=True):
            st.session_state['sudah_presensi'] = False
            st.session_state['konfirmasi_data'] = None
            st.session_state['qr_makul']        = None
            st.session_state['qr_pertemuan']    = None
            st.session_state['qr_semester']     = None
            ke_halaman('landing')

    # ── Form Presensi ────────────────────────────────────────
    else:
        semua_kelas_aktif = baca_semua_kelas_aktif()
        jadwal_prodi      = DATA_JADWAL_AKT if prodi_mhs == 'Aktuaria' else DATA_JADWAL_BD
        dosen_valid       = list(jadwal_prodi.keys())
        kelas_mhs_aktif   = [k for k in semua_kelas_aktif if k['dosen_key'] in dosen_valid]

        # Clock box (waktu server WIB)
        st.markdown(
            f'<div class="clock-box">🕒 {waktu_sekarang.strftime("%A, %d %B %Y — %H:%M:%S")} WIB</div>',
            unsafe_allow_html=True
        )

        # Banner QR berhasil scan
        qr_makul = st.session_state.get('qr_makul')
        if qr_makul:
            nama_tampil = qr_makul.rsplit(' (', 1)[0] if ' (' in qr_makul else qr_makul
            st.markdown(f"""
                <div class="qr-banner">
                    <div class="title">📲 Scan QR Berhasil!</div>
                    <div class="sub">
                        Kelas: <b>{nama_tampil}</b> &nbsp;·&nbsp;
                        Smt {st.session_state.get('qr_semester','-')} &nbsp;·&nbsp;
                        Pertemuan ke-{st.session_state.get('qr_pertemuan','-')}
                    </div>
                    <div class="hint">Sesi sudah otomatis terpilih. Isi nama, NIM, dan rangkuman.</div>
                </div>
            """, unsafe_allow_html=True)

        with st.form(key="form_presensi", clear_on_submit=False):
            st.markdown(
                "<h4 style='text-align:center;font-weight:800;font-size:20px;"
                "color:#3525cd;margin-bottom:4px;'>📝 Form Kehadiran</h4>"
                "<p style='text-align:center;font-size:13px;color:#464555;margin-bottom:20px;'>"
                "Silakan lengkapi data absensi Anda</p>",
                unsafe_allow_html=True
            )

            col_nama, col_nim = st.columns(2)
            with col_nama:
                nama = st.text_input("Nama Lengkap", placeholder="Nama lengkap kamu")
            with col_nim:
                nim  = st.text_input("NIM", placeholder="Contoh: 220101001")

            # Jika dari QR → auto-select kelas
            if qr_makul:
                kelas_qr = next(
                    (k for k in kelas_mhs_aktif if k['makul'] == qr_makul),
                    None
                )
                if kelas_qr:
                    nm = kelas_qr['makul'].rsplit(' (', 1)[0]
                    nd = kelas_qr['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                    st.markdown(f"""
                        <div style='background:rgba(79,70,229,0.07);border:1px solid rgba(79,70,229,0.22);
                            border-radius:12px;padding:12px 16px;font-size:14px;margin-bottom:8px;'>
                            🏫 <b>{nm}</b> &nbsp;—&nbsp; {nd} &nbsp;|&nbsp; Pertemuan {kelas_qr['pertemuan']}
                        </div>
                    """, unsafe_allow_html=True)
                    kelas_terpilih_obj  = kelas_qr
                    opsi_kelas          = [f"{nm} — {nd} | Pertemuan {kelas_qr['pertemuan']}"]
                    pilihan_kelas_label = opsi_kelas[0]
                    st.selectbox("🏫 Sesi Kelas:", options=opsi_kelas,
                                 label_visibility="collapsed", disabled=True)
                else:
                    st.warning("⚠️ Kelas dari QR ini sudah tidak aktif. Pilih kelas manual di bawah.")
                    kelas_terpilih_obj = None
                    qr_makul           = None

            if not qr_makul:
                if kelas_mhs_aktif:
                    def label_kelas(k):
                        nm = k['makul'].rsplit(' (', 1)[0]
                        nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                        return f"{nm} — {nd} | Pertemuan {k['pertemuan']}"
                    opsi_kelas          = [label_kelas(k) for k in kelas_mhs_aktif]
                    pilihan_kelas_label = st.selectbox("🏫 Pilih Sesi Kelas:", options=opsi_kelas)
                    kelas_terpilih_obj  = None
                else:
                    st.warning(f"⚠️ Belum ada kelas {prodi_mhs} yang aktif. Silakan tunggu instruksi dosen.")
                    pilihan_kelas_label = None
                    kelas_terpilih_obj  = None

            materi = st.text_area(
                "Rangkuman Materi Hari Ini (min. 20 karakter)",
                placeholder="Tulis ringkasan singkat materi yang dibahas...",
                height=110
            )
            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.form_submit_button(label="✉️  KIRIM BUKTI HADIR")

        if submit_button:
            if kelas_terpilih_obj is None and kelas_mhs_aktif and pilihan_kelas_label:
                idx_pilihan        = opsi_kelas.index(pilihan_kelas_label)
                kelas_terpilih_obj = kelas_mhs_aktif[idx_pilihan]

            if not kelas_mhs_aktif and not kelas_terpilih_obj:
                st.error("❌ Gagal! Belum ada kelas yang dibuka saat ini.")
            elif not nama.strip():
                st.error("❌ Nama wajib diisi!")
            elif not nim.strip():
                st.error("❌ NIM wajib diisi!")
            elif len(materi.strip()) < 20:
                st.error(f"❌ Rangkuman terlalu pendek ({len(materi.strip())} karakter). Minimal 20 karakter.")
            elif kelas_terpilih_obj is None:
                st.error("❌ Pilih kelas terlebih dahulu.")
            else:
                tgl = waktu_sekarang.strftime("%Y-%m-%d")
                jam = waktu_sekarang.strftime("%H:%M:%S")
                try:
                    sheet   = get_sheet()
                    raw     = kelas_terpilih_obj["makul"]
                    safe    = raw.replace("/","-").replace(":","-").replace("\\","-")
                    if len(safe) > 28:
                        suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                        safe   = safe[:24] + "_" + suffix
                    ws      = get_or_create_worksheet(sheet, safe)
                    records = ws.get_all_records()
                    sudah   = any(
                        str(r.get('NIM','')).strip() == nim.strip() and
                        str(r.get('Pertemuan Ke','')) == str(kelas_terpilih_obj["pertemuan"])
                        for r in records
                    )
                    if sudah:
                        st.error(f"❌ NIM {nim} sudah terdaftar hadir pada Pertemuan Ke-{kelas_terpilih_obj['pertemuan']}!")
                    else:
                        simpan_ke_sheets({
                            "Tanggal":          tgl,
                            "Jam Isi":          jam,
                            "Mata Kuliah":      kelas_terpilih_obj["makul"],
                            "Semester":         kelas_terpilih_obj["semester"],
                            "Pertemuan Ke":     kelas_terpilih_obj["pertemuan"],
                            "NIM":              nim.strip(),
                            "Nama":             nama.strip(),
                            "Rangkuman Materi": materi.strip()
                        })
                        nm_makul = kelas_terpilih_obj['makul'].rsplit(' (', 1)[0]
                        st.session_state['konfirmasi_data'] = {
                            "nama":      nama.strip(),
                            "nim":       nim.strip(),
                            "makul":     nm_makul,
                            "makul_raw": kelas_terpilih_obj["makul"],
                            "tanggal":   tgl,
                            "jam":       jam,
                            "pertemuan": kelas_terpilih_obj["pertemuan"],
                            "semester":  kelas_terpilih_obj["semester"],
                        }
                        st.session_state['sudah_presensi'] = True
                        st.balloons()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Gagal menghubungi database: {e}")


# ============================================================
# HALAMAN DOSEN
# ============================================================
elif st.session_state['halaman'] == 'dosen':

    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← Kembali", key="back_dos"):
            ke_halaman('landing')

    # ── Login Dosen ──────────────────────────────────────────
    if not st.session_state.get('dosen_login', False):

        st.markdown("""
            <div class="login-header">
                <div class="icon-wrap">🎓</div>
                <h2>Autentikasi Dosen</h2>
                <p>Silakan pilih program studi dan masukkan kode akses panel untuk memulai sesi.</p>
            </div>
        """, unsafe_allow_html=True)

        idx_prodi_dosen  = 0 if st.session_state['prodi'] == 'Bisnis Digital' else 1
        prodi_dosen      = st.selectbox("Pilih Program Studi", ["Bisnis Digital", "Aktuaria"], index=idx_prodi_dosen)
        st.session_state['prodi'] = prodi_dosen
        jadwal_aktif_login = DATA_JADWAL_AKT if prodi_dosen == 'Aktuaria' else DATA_JADWAL_BD

        with st.form(key="form_login_dosen"):
            pilihan_nama_login = st.selectbox("Nama Dosen", options=list(jadwal_aktif_login.keys()))
            password_input     = st.text_input("Kode Akses Panel", type="password", placeholder="Masukkan password...")
            st.markdown("<br>", unsafe_allow_html=True)
            tombol_login       = st.form_submit_button("🔑  Masuk Panel Dashboard")

        if tombol_login:
            PASSWORD_DOSEN = st.secrets.get("password_dosen", "dosen123")
            if password_input == PASSWORD_DOSEN:
                st.session_state['dosen_login']      = True
                st.session_state['nama_dosen_login'] = pilihan_nama_login
                st.rerun()
            else:
                st.error("❌ Kode akses tidak valid!")

        st.markdown("""
            <p style='text-align:center;font-size:13px;color:#464555;margin-top:16px;'>
                Lupa kode akses? <a href='#' style='color:#3525cd;font-weight:700;'>Hubungi Admin Prodi</a>
            </p>
        """, unsafe_allow_html=True)

    # ── Dashboard Dosen ──────────────────────────────────────
    else:
        nama_dosen_aktif = st.session_state.get('nama_dosen_login')
        dosen_key        = nama_dosen_aktif

        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.markdown(
                f'<div class="dashboard-title">👨‍🏫 Dashboard: {nama_dosen_aktif.split(",")[0]}</div>',
                unsafe_allow_html=True
            )
        with col_logout:
            if st.button("Keluar", use_container_width=True):
                st.session_state['dosen_login']      = False
                st.session_state['nama_dosen_login'] = None
                ke_halaman('landing')

        semua_kelas_aktif     = baca_semua_kelas_aktif()
        prodi_dsn_sekarang    = 'Aktuaria' if nama_dosen_aktif in DATA_JADWAL_AKT else 'Bisnis Digital'
        jadwal_dsn_sekarang   = DATA_JADWAL_AKT if prodi_dsn_sekarang == 'Aktuaria' else DATA_JADWAL_BD
        dosen_valid           = list(jadwal_dsn_sekarang.keys())
        kelas_aktif_prodi_ini = [k for k in semua_kelas_aktif if k['dosen_key'] in dosen_valid]

        tab1, tab2, tab3 = st.tabs(["🚀 Buka Kelas & QR", "📋 Monitor Kelas Aktif", "📂 Arsip & Histori"])

        # ─── TAB 1 — BUKA KELAS & QR ────────────────────────
        with tab1:
            st.markdown(
                "<h4 style='font-weight:800;font-size:18px;margin-bottom:4px;'>Aktivasi Perkuliahan</h4>"
                f"<p style='font-size:12px;color:#464555;margin-bottom:16px;'>"
                f"Login sebagai: <b>{nama_dosen_aktif}</b> (Prodi {prodi_dsn_sekarang})</p>",
                unsafe_allow_html=True
            )

            daftar_makul         = get_makul_dosen(nama_dosen_aktif)
            pilihan_makul        = st.selectbox("Mata Kuliah", options=daftar_makul)
            input_makul_gabungan = f"{pilihan_makul} ({nama_dosen_aktif})"

            status_dosen = baca_status_kelas_dosen(dosen_key)

            # Tampilkan status kelas aktif
            if status_dosen["aktif"]:
                nm_aktif     = status_dosen['makul'].rsplit(' (', 1)[0]
                waktu_buka_s = status_dosen.get("waktu_buka", "")
                sisa_info, progres_pct, waktu_buka_fmt = "", 0, ""

                if waktu_buka_s:
                    try:
                        wb_dt = datetime.fromisoformat(waktu_buka_s)
                        if wb_dt.tzinfo is None:
                            wb_dt = tz_wib.localize(wb_dt)
                        sekarang_dt = datetime.now(tz_wib)
                        selisih_sek = (sekarang_dt - wb_dt).total_seconds()
                        sisa_sek    = max(0, BATAS_JAM * 3600 - selisih_sek)
                        sisa_jam    = int(sisa_sek // 3600)
                        sisa_menit  = int((sisa_sek % 3600) // 60)
                        progres_pct = min(100, int((selisih_sek / (BATAS_JAM * 3600)) * 100))
                        waktu_buka_fmt = wb_dt.strftime("%d %b %Y, %H:%M WIB")
                        sisa_info   = f"{sisa_jam} jam {sisa_menit} menit" if sisa_sek > 0 else "Hampir habis"
                    except Exception:
                        pass

                st.markdown(
                    f'<div class="badge-aktif-bar">'
                    f'<span class="dot-pulse"></span>'
                    f'🟢 Kelas Aktif: <b>{nm_aktif}</b> (Smt {status_dosen["semester"]} — Pertemuan {status_dosen["pertemuan"]})'
                    f'</div>',
                    unsafe_allow_html=True
                )

                col_wb1, col_wb2 = st.columns(2)
                with col_wb1:
                    warna_s = "#10B981"
                    st.markdown(f"""
                        <div class="time-card">
                            <div class="label">Dibuka Sejak</div>
                            <div class="value" style="color:{warna_s};">{waktu_buka_fmt or "—"}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_wb2:
                    warna_sisa = "#10B981" if progres_pct < 75 else ("#F59E0B" if progres_pct < 90 else "#EF4444")
                    st.markdown(f"""
                        <div class="time-card">
                            <div class="label">Sisa Waktu (Auto-close {BATAS_JAM} jam)</div>
                            <div class="value" style="color:{warna_sisa};">{sisa_info or "—"}</div>
                        </div>
                    """, unsafe_allow_html=True)

                if progres_pct > 0:
                    warna_bar = "#10B981" if progres_pct < 75 else ("#F59E0B" if progres_pct < 90 else "#EF4444")
                    st.markdown(f"""
                        <div class="progress-bar-wrap">
                            <div class="progress-bar-header">
                                <span>Durasi terpakai</span>
                                <span>{progres_pct}%</span>
                            </div>
                            <div class="progress-bar-track">
                                <div class="progress-bar-fill" style="width:{progres_pct}%;background:{warna_bar};"></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            else:
                st.info("⚪ Status: **Standby** — belum ada kelas aktif.")

            # Panel aktivasi
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    opt_smt       = [str(i) for i in range(1, 9)]
                    default_smt   = status_dosen["semester"] if status_dosen["semester"] in opt_smt else opt_smt[0]
                    input_semester = st.selectbox("Semester:", options=opt_smt, index=opt_smt.index(default_smt))
                with col2:
                    opt_prt       = [str(i) for i in range(1, 17)]
                    default_prt   = status_dosen["pertemuan"] if status_dosen["pertemuan"] in opt_prt else opt_prt[0]
                    input_pertemuan = st.selectbox("Pertemuan Ke-:", options=opt_prt, index=opt_prt.index(default_prt))

                col_buka, col_tutup = st.columns(2)
                with col_buka:
                    if st.button("✅ Aktifkan Akses Kelas", use_container_width=True, type="primary"):
                        try:
                            tulis_status_kelas(input_makul_gabungan, input_semester, input_pertemuan, dosen_key=dosen_key, aktif=True)
                            st.toast("Kelas berhasil diaktifkan!", icon="🎉")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
                with col_tutup:
                    if st.button("⛔ Tutup Sesi Saya", use_container_width=True):
                        if tutup_kelas(dosen_key=dosen_key):
                            st.toast("Sesi kelas ditutup.", icon="🔒")
                            st.rerun()

            st.markdown("<hr style='border:none;border-top:1px solid rgba(199,196,216,0.28);margin:20px 0;'>", unsafe_allow_html=True)

            # Generator QR
            st.markdown(
                "<h4 style='font-weight:800;font-size:17px;margin-bottom:4px;'>📲 Generator QR Code Presensi</h4>"
                "<p style='font-size:12px;color:#464555;margin-bottom:16px;'>"
                "QR ini langsung membuka form presensi dengan sesi kelas sudah terpilih otomatis.</p>",
                unsafe_allow_html=True
            )

            try:
                base_url_default = st.secrets.get("app_url", "https://your-app.streamlit.app")
            except Exception:
                base_url_default = "https://your-app.streamlit.app"

            if status_dosen["aktif"]:
                makul_qr = status_dosen['makul']
                smt_qr   = status_dosen['semester']
                prt_qr   = status_dosen['pertemuan']
                qr_url   = (
                    f"{base_url_default}"
                    f"?makul={urllib.parse.quote(makul_qr)}"
                    f"&semester={smt_qr}"
                    f"&pertemuan={prt_qr}"
                )
                nm_qr = makul_qr.rsplit(' (', 1)[0]
                st.success(f"QR untuk: **{nm_qr}** — Pertemuan {prt_qr}")

                col_qr, col_info = st.columns([1, 1.5])
                with col_qr:
                    qr_bytes = generate_qr(qr_url)
                    st.image(qr_bytes, width=220)
                    st.download_button(
                        "⬇️ Download QR",
                        data=qr_bytes,
                        file_name=f"QR_P{prt_qr}_{nm_qr[:20]}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                with col_info:
                    st.markdown(f"""
                        <div class="info-box">
                            <b>Petunjuk Penggunaan:</b><br><br>
                            1️⃣ Aktifkan kelas dulu (tombol di atas)<br>
                            2️⃣ Tampilkan / print QR ini di proyektor<br>
                            3️⃣ Mahasiswa scan → langsung ke form<br>
                            4️⃣ Sesi otomatis terpilih, tinggal isi nama &amp; NIM
                        </div>
                    """, unsafe_allow_html=True)
                    st.code(qr_url, language=None)
            else:
                st.warning("⚠️ Aktifkan kelas terlebih dahulu untuk generate QR.")
                st.markdown(f"**URL App:** `{base_url_default}`")
                st.caption("Isi `app_url` di secrets.toml dengan URL Streamlit app kamu.")

        # ─── TAB 2 — MONITOR KELAS AKTIF ────────────────────
        with tab2:
            st.markdown(
                "<h4 style='font-weight:800;font-size:18px;margin-bottom:16px;'>📋 Monitor Kelas Aktif</h4>",
                unsafe_allow_html=True
            )
            if st.button("🔄 Refresh Data", use_container_width=True):
                baca_semua_kelas_aktif_cached.clear()
                hitung_hadir.clear()
                st.rerun()

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

            if not kelas_aktif_prodi_ini:
                st.info(f"ℹ️ Tidak ada kelas aktif saat ini untuk Prodi {prodi_dsn_sekarang}.")
            else:
                for k in kelas_aktif_prodi_ini:
                    nm     = k['makul'].rsplit(' (', 1)[0]
                    nd     = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                    jumlah = hitung_hadir(k['makul'], k['pertemuan'])

                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(
                                f"<p style='font-weight:700;font-size:16px;margin-bottom:3px;color:#0b1c30;'>{nm}</p>"
                                f"<p style='font-size:13px;color:#464555;margin:0;'>"
                                f"👨‍🏫 {nd} &nbsp;·&nbsp; Semester {k['semester']} &nbsp;·&nbsp; Pertemuan {k['pertemuan']}</p>",
                                unsafe_allow_html=True
                            )
                        with c2:
                            st.metric("Hadir", jumlah)

                        try:
                            raw  = k['makul']
                            safe = raw.replace("/","-").replace(":","-").replace("\\","-")
                            if len(safe) > 28:
                                suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                                safe   = safe[:24] + "_" + suffix
                            ws_mon   = get_sheet().worksheet(safe)
                            data_mon = ws_mon.get_all_records()
                            df_mf    = pd.DataFrame(data_mon)
                            df_mf    = df_mf[df_mf['Pertemuan Ke'].astype(str) == str(k['pertemuan'])]

                            if not df_mf.empty:
                                with st.expander(f"👁️ Lihat {len(df_mf)} mahasiswa hadir"):
                                    for _, row in df_mf.iterrows():
                                        inisial = "".join([w[0].upper() for w in str(row['Nama']).split()[:2]])
                                        st.markdown(f"""
                                            <div class="histori-item">
                                                <div class="histori-avatar">{inisial}</div>
                                                <div>
                                                    <div class="histori-name">{row['NIM']} — {row['Nama']}</div>
                                                    <div class="histori-time">🕒 {row['Jam Isi']} WIB</div>
                                                </div>
                                                <div class="histori-badge">Hadir</div>
                                            </div>
                                            <hr class="divider-light">
                                        """, unsafe_allow_html=True)
                            else:
                                st.info("Belum ada mahasiswa yang hadir.")
                        except gspread.exceptions.WorksheetNotFound:
                            st.info("Belum ada data presensi.")
                        except Exception as e:
                            st.error(f"Error: {e}")

        # ─── TAB 3 — ARSIP & HISTORI ────────────────────────
        with tab3:
            st.markdown(
                "<h4 style='font-weight:800;font-size:18px;margin-bottom:16px;'>📂 Pusat Data Kehadiran</h4>",
                unsafe_allow_html=True
            )

            makul_opsi    = get_makul_dosen(nama_dosen_aktif)
            pilih_makul_a = st.selectbox("Pilih Mata Kuliah:", options=makul_opsi, key="arsip_makul")
            makul_gabung  = f"{pilih_makul_a} ({nama_dosen_aktif})"

            def safe_name(raw):
                s = raw.replace("/","-").replace(":","-").replace("\\","-")
                if len(s) > 28:
                    suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                    s = s[:24] + "_" + suffix
                return s

            # Load data untuk makul terpilih
            df_makul = pd.DataFrame()
            try:
                ws_a = get_sheet().worksheet(safe_name(makul_gabung))
                rec  = ws_a.get_all_records()
                if rec:
                    df_makul = pd.DataFrame(rec)
            except gspread.exceptions.WorksheetNotFound:
                pass
            except Exception:
                pass

            if st.button("📊 Tampilkan Data", use_container_width=True, type="primary"):
                st.rerun()

            sub1, sub2, sub3 = st.tabs(["📜 Histori & Detail", "📥 Unduh Data", "🗑️ Hapus Entri"])

            # ── SUB TAB 1: HISTORI ───────────────────────────
            with sub1:
                if df_makul.empty:
                    st.info("Belum ada data presensi untuk mata kuliah ini.")
                else:
                    total_mhs_unik = df_makul['NIM'].nunique() if 'NIM' in df_makul.columns else 0
                    total_prt      = df_makul['Pertemuan Ke'].nunique() if 'Pertemuan Ke' in df_makul.columns else 0
                    total_presensi = len(df_makul)

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Presensi", total_presensi)
                    c2.metric("Mahasiswa Unik", total_mhs_unik)
                    c3.metric("Pertemuan Tercatat", total_prt)

                    st.markdown("<hr style='border:none;border-top:1px solid rgba(199,196,216,0.28);margin:16px 0;'>", unsafe_allow_html=True)
                    st.markdown("##### Riwayat Semua Pertemuan")

                    if 'Pertemuan Ke' in df_makul.columns:
                        summ = df_makul.groupby('Pertemuan Ke').agg(
                            total=('NIM','count'),
                            tgl=('Tanggal','min')
                        ).reset_index()
                        summ['_s'] = pd.to_numeric(summ['Pertemuan Ke'], errors='coerce')
                        summ = summ.sort_values('_s', ascending=False).drop(columns=['_s'])

                        for _, rh in summ.iterrows():
                            prt_num = rh['Pertemuan Ke']
                            df_prt  = df_makul[df_makul['Pertemuan Ke'].astype(str) == str(prt_num)]

                            with st.expander(
                                f"📅 Pertemuan Ke-{prt_num}  ·  {rh['tgl']}  ·  🎓 {rh['total']} Mahasiswa Hadir",
                                expanded=False
                            ):
                                cols_tampil = [c for c in ['NIM','Nama','Jam Isi','Semester','Rangkuman Materi'] if c in df_prt.columns]
                                df_show     = df_prt[cols_tampil].reset_index(drop=True)
                                df_show.index += 1
                                st.dataframe(df_show, use_container_width=True)

                                out_p = BytesIO()
                                df_show.to_excel(out_p, index=False, engine='openpyxl')
                                out_p.seek(0)
                                st.download_button(
                                    f"⬇️ Download Excel Pertemuan {prt_num}",
                                    data=out_p,
                                    file_name=f"P{prt_num}_{pilih_makul_a[:25]}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"dl_prt_{prt_num}"
                                )
                    else:
                        st.warning("Kolom 'Pertemuan Ke' tidak ditemukan di data.")

            # ── SUB TAB 2: UNDUH ─────────────────────────────
            with sub2:
                st.markdown("##### Download Rekap Master Semester")
                if df_makul.empty:
                    st.info("Belum ada data untuk diunduh.")
                else:
                    df_dl = df_makul.copy()
                    if 'Pertemuan Ke' in df_dl.columns:
                        df_dl['_sort'] = pd.to_numeric(df_dl['Pertemuan Ke'], errors='coerce')
                        df_dl = df_dl.sort_values(['_sort','NIM']).drop(columns=['_sort'])
                    out_all = BytesIO()
                    df_dl.to_excel(out_all, index=False, engine='openpyxl')
                    out_all.seek(0)
                    st.success(f"✅ {len(df_dl)} total rekaman tersedia.")
                    st.download_button(
                        "⬇️ Download Excel Rekap Lengkap",
                        data=out_all,
                        file_name=f"MASTER_{pilih_makul_a[:30]}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                st.markdown("<hr style='border:none;border-top:1px solid rgba(199,196,216,0.28);margin:16px 0;'>", unsafe_allow_html=True)
                st.markdown("##### Download Per Pertemuan")

                if not df_makul.empty and 'Pertemuan Ke' in df_makul.columns:
                    pertemuan_tersedia = sorted(
                        df_makul['Pertemuan Ke'].unique().tolist(),
                        key=lambda x: int(x) if str(x).isdigit() else 0
                    )
                    pilih_prt_dl = st.selectbox("Pilih Pertemuan:", options=pertemuan_tersedia, key="dl_prt_sel")
                    df_prt_dl    = df_makul[df_makul['Pertemuan Ke'].astype(str) == str(pilih_prt_dl)]
                    st.info(f"📌 {len(df_prt_dl)} mahasiswa hadir di pertemuan {pilih_prt_dl}")
                    cols_t = [c for c in ['NIM','Nama','Jam Isi','Semester','Rangkuman Materi'] if c in df_prt_dl.columns]
                    st.dataframe(df_prt_dl[cols_t].reset_index(drop=True), use_container_width=True)
                    out_prt = BytesIO()
                    df_prt_dl[cols_t].to_excel(out_prt, index=False, engine='openpyxl')
                    out_prt.seek(0)
                    st.download_button(
                        f"⬇️ Download Pertemuan {pilih_prt_dl}",
                        data=out_prt,
                        file_name=f"P{pilih_prt_dl}_{pilih_makul_a[:25]}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="dl_prt_btn"
                    )
                else:
                    st.info("Belum ada data pertemuan tersedia.")

            # ── SUB TAB 3: HAPUS ENTRI ───────────────────────
            with sub3:
                st.warning("⚠️ Gunakan fitur ini hanya untuk menghapus entri yang salah (NIM typo, dll).")
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    nim_hapus = st.text_input("NIM yang akan dihapus", placeholder="Contoh: 220101001")
                with col_h2:
                    if not df_makul.empty and 'Pertemuan Ke' in df_makul.columns:
                        prt_ada = sorted(
                            df_makul['Pertemuan Ke'].unique().tolist(),
                            key=lambda x: int(x) if str(x).isdigit() else 0
                        )
                    else:
                        prt_ada = [str(i) for i in range(1, 17)]
                    prt_hapus = st.selectbox("Dari Pertemuan Ke-:", options=prt_ada, key="hapus_prt")

                if st.button("🗑️ Hapus Entri Ini", type="primary", use_container_width=True):
                    if nim_hapus.strip():
                        ok, pesan = hapus_entri_presensi(safe_name(makul_gabung), nim_hapus.strip(), prt_hapus)
                        if ok: st.success(f"✅ {pesan}")
                        else:  st.error(f"❌ {pesan}")
                    else:
                        st.error("Masukkan NIM terlebih dahulu.")

        # Footer dosen
        st.markdown("""
            <hr style='border:none;border-top:1px solid rgba(199,196,216,0.28);margin:28px 0 12px;'>
            <p style='text-align:center;font-size:12px;color:#464555;opacity:0.60;'>
                © 2026 Institut Teknologi dan Bisnis Muhammadiyah Purbalingga
            </p>
        """, unsafe_allow_html=True)