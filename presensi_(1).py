import streamlit as st
import pandas as pd
from datetime import datetime
import qrcode
from io import BytesIO
import gspread
from google.oauth2.service_account import Credentials
import pytz
import hashlib
import time
import json

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
    # QR auto-fill
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
st.set_page_config(page_title="Presensi Bisnis Digital & Aktuaria", page_icon="📝", layout="centered")

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
header {visibility:hidden;} footer {visibility:hidden;} #MainMenu {visibility:hidden;}
.stApp { background: var(--background-color); }
.header-banner {
    background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%);
    padding: 25px; border-radius: 16px; color: white;
    text-align: center; margin-bottom: 25px;
    box-shadow: 0 10px 20px rgba(79,70,229,0.25);
}
.header-banner h1 { color:white !important; font-weight:800; font-size:28px; margin-bottom:5px; }
.header-banner p  { color:#E0E7FF !important; font-size:15px; opacity:0.9; margin:0; }
div[data-testid="stForm"] {
    background: var(--secondary-background-color) !important;
    border: 1px solid rgba(128,128,128,0.2) !important;
    border-radius: 20px !important; padding: 35px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.08) !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input {
    background-color: var(--secondary-background-color) !important;
    color: var(--text-color) !important;
    border: 1.5px solid rgba(128,128,128,0.35) !important;
    border-radius: 10px !important; font-size: 15px !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #6366F1 !important;
    box-shadow: 0 0 0 4px rgba(99,102,241,0.15) !important;
}
div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stTextArea"] textarea::placeholder {
    color: var(--text-color) !important; opacity: 0.4 !important;
}
div[data-testid="stSelectbox"] > div[data-baseweb="select"] > div {
    background-color: var(--secondary-background-color) !important;
    border: 1.5px solid rgba(128,128,128,0.35) !important;
    border-radius: 10px !important;
}
div[data-baseweb="select"] span, div[data-baseweb="select"] div,
div[data-testid="stSelectbox"] span { color: var(--text-color) !important; background-color: transparent !important; }
div[data-baseweb="select"] svg { fill: var(--text-color) !important; opacity: 0.6; }
div[data-baseweb="popover"], ul[data-baseweb="menu"], div[role="listbox"] {
    background-color: var(--secondary-background-color) !important;
    border: 1px solid rgba(128,128,128,0.25) !important;
    border-radius: 10px !important;
}
li[role="option"], div[role="option"] {
    background-color: var(--secondary-background-color) !important;
    color: var(--text-color) !important;
}
li[role="option"]:hover, li[aria-selected="true"] {
    background-color: rgba(99,102,241,0.15) !important;
}
div[data-testid="stRadio"] label, div[data-testid="stRadio"] p { color: var(--text-color) !important; }
div[data-testid="stRadio"] > div {
    background: var(--secondary-background-color) !important;
    border: 1px solid rgba(128,128,128,0.2) !important;
    border-radius: 10px !important; padding: 8px 16px !important;
}
label, .stLabel {
    color: var(--text-color) !important;
    font-weight: 600 !important; font-size: 14px !important;
}
button[kind="formSubmit"] {
    background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    padding: 12px 24px !important; font-size: 16px !important; font-weight: 700 !important;
    width: 100% !important;
}
button[kind="secondary"], button[data-testid="baseButton-secondary"] {
    background-color: var(--secondary-background-color) !important;
    color: var(--text-color) !important;
    border: 1px solid rgba(128,128,128,0.3) !important;
    border-radius: 10px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: var(--secondary-background-color) !important;
    border: 1px solid rgba(128,128,128,0.2) !important; border-radius: 12px !important;
}
button[data-baseweb="tab"] { color: var(--text-color) !important; background: transparent !important; opacity: 0.6; }
button[data-baseweb="tab"][aria-selected="true"] { color: #6366F1 !important; opacity: 1; border-bottom-color: #6366F1 !important; }
div[data-testid="stMetric"] {
    background: var(--secondary-background-color) !important;
    border: 1px solid rgba(128,128,128,0.2) !important;
    border-radius: 12px !important; padding: 12px 16px !important;
}
details[data-testid="stExpander"] > summary {
    background: var(--secondary-background-color) !important;
    border: 1px solid rgba(128,128,128,0.2) !important;
    border-radius: 8px !important;
}
div[data-testid="stExpanderDetails"] {
    background: var(--secondary-background-color) !important;
    border: 1px solid rgba(128,128,128,0.15) !important;
    border-top: none !important; border-radius: 0 0 8px 8px !important;
}
div[data-testid="stAlert"] { border-radius: 10px !important; }
div[data-testid="stDataFrame"] { border-radius: 10px !important; border: 1px solid rgba(128,128,128,0.2) !important; }
input[type="password"] {
    background-color: var(--secondary-background-color) !important;
    color: var(--text-color) !important;
    border: 1.5px solid rgba(128,128,128,0.35) !important; border-radius: 10px !important;
}
.clock-container {
    background: rgba(251,191,36,0.12); border: 1px solid rgba(251,191,36,0.4);
    border-radius: 12px; padding: 12px; text-align: center; margin-bottom: 20px;
    color: #D97706; font-weight: 600; font-size: 14px;
}
.kelas-badge {
    background: var(--secondary-background-color); border-left: 4px solid #6366F1;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06); color: var(--text-color);
}
.konfirmasi-box {
    background: linear-gradient(135deg, rgba(16,185,129,0.12) 0%, rgba(16,185,129,0.06) 100%);
    border: 2px solid rgba(16,185,129,0.5); border-radius: 20px;
    padding: 30px; text-align: center; margin: 10px 0 20px 0;
}
.konfirmasi-box h2 { color: #10B981 !important; font-size: 22px; margin-bottom: 8px; }
.counter-box {
    background: var(--secondary-background-color); border-radius: 12px;
    padding: 14px 20px; text-align: center;
    border: 1px solid rgba(128,128,128,0.2); margin-top: 10px;
}
.counter-box .angka { font-size: 32px; font-weight: 800; color: #6366F1; }
.histori-container {
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.2); border-left: 4px solid #10B981;
    border-radius: 8px; padding: 15px; margin-bottom: 12px;
}
.akses-card {
    background: var(--secondary-background-color); border-radius: 16px;
    padding: 30px 20px; text-align: center;
    border: 1.5px solid rgba(128,128,128,0.2); transition: all 0.2s;
}
.akses-card:hover { border-color: #6366F1; }
.qr-banner {
    background: linear-gradient(135deg, rgba(16,185,129,0.12) 0%, rgba(99,102,241,0.08) 100%);
    border: 2px solid rgba(16,185,129,0.4); border-radius: 16px;
    padding: 16px 20px; margin-bottom: 16px;
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

# Cache baca kelas aktif 30 detik — kurangi hit API secara drastis
@st.cache_data(ttl=30)
def baca_semua_kelas_aktif_cached():
    try:
        sheet = get_sheet()
        try:
            ws = sheet.worksheet(STATUS_SHEET)
        except gspread.exceptions.WorksheetNotFound:
            ws = sheet.add_worksheet(title=STATUS_SHEET, rows="50", cols="6")
            ws.append_row(["makul","semester","pertemuan","aktif","dosen_key"])
            return []
        data = ws.get_all_records()
        return [r for r in data if str(r.get("aktif","0")) == "1"]
    except Exception as e:
        return []

def baca_semua_kelas_aktif():
    """Wrapper — tampilkan error hanya sekali per session."""
    result = baca_semua_kelas_aktif_cached()
    return result

# Cache status dosen 15 detik
@st.cache_data(ttl=15)
def baca_status_kelas_dosen_cached(dosen_key):
    try:
        sheet = get_sheet()
        ws    = sheet.worksheet(STATUS_SHEET)
        for row in ws.get_all_records():
            if row.get("dosen_key","") == dosen_key:
                return {
                    "makul":     row.get("makul","Belum Diatur"),
                    "semester":  str(row.get("semester","-")),
                    "pertemuan": str(row.get("pertemuan","-")),
                    "aktif":     str(row.get("aktif","0")) == "1",
                }
    except Exception:
        pass
    return {"makul":"Belum Diatur","semester":"-","pertemuan":"-","aktif":False}

def baca_status_kelas_dosen(dosen_key):
    return baca_status_kelas_dosen_cached(dosen_key)

def tulis_status_kelas(makul, semester, pertemuan, dosen_key, aktif=True):
    sheet = get_sheet()
    try:    ws = sheet.worksheet(STATUS_SHEET)
    except: ws = sheet.add_worksheet(title=STATUS_SHEET, rows="50", cols="6")
    data   = ws.get_all_values()
    header = data[0] if data else []
    try:    col_dk = header.index("dosen_key") + 1
    except:
        ws.append_row(["makul","semester","pertemuan","aktif","dosen_key"])
        col_dk = 5
    row_idx = None
    for i, row in enumerate(data[1:], start=2):
        if len(row) >= col_dk and row[col_dk-1] == dosen_key:
            row_idx = i; break
    new_row = [makul, semester, pertemuan, "1" if aktif else "0", dosen_key]
    if row_idx: ws.update(f"A{row_idx}:E{row_idx}", [new_row])
    else:       ws.append_row(new_row)
    # Invalidasi cache setelah tulis
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
        sheet = get_sheet()
        ws    = sheet.worksheet(nama_ws)
        data  = ws.get_all_values()
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
    sheet   = get_sheet()
    raw     = data["Mata Kuliah"]
    safe    = raw.replace("/","-").replace(":","-").replace("\\","-")
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

# Cache hitung hadir 20 detik
@st.cache_data(ttl=20)
def hitung_hadir(makul, pertemuan):
    try:
        sheet  = get_sheet()
        raw    = makul
        safe   = raw.replace("/","-").replace(":","-").replace("\\","-")
        if len(safe) > 28:
            suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
            safe   = safe[:24] + "_" + suffix
        ws     = sheet.worksheet(safe)
        data   = ws.get_all_records()
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
    # Langsung arahkan ke halaman mahasiswa
    if st.session_state['halaman'] == 'landing':
        st.session_state['halaman'] = 'mahasiswa'

# ============================================================
# HEADER
# ============================================================
st.markdown("""
    <div class="header-banner">
        <h1>📝 PRESENSI PERKULIAHAN</h1>
        <p>Bisnis Digital & Aktuaria — Beta ver 3.0</p>
    </div>
""", unsafe_allow_html=True)

# ============================================================
# HALAMAN LANDING
# ============================================================
if st.session_state['halaman'] == 'landing':

    st.markdown("<h3 style='text-align:center;font-weight:700;'>🎓 Pilih Program Studi</h3>", unsafe_allow_html=True)
    idx_prodi = 0 if st.session_state['prodi'] == 'Bisnis Digital' else 1
    prodi_terpilih = st.radio("Program Studi", ["Bisnis Digital", "Aktuaria"],
                               index=idx_prodi, horizontal=True, label_visibility="collapsed")
    st.session_state['prodi'] = prodi_terpilih

    semua_kelas_aktif = baca_semua_kelas_aktif()
    jadwal_prodi      = DATA_JADWAL_AKT if prodi_terpilih == 'Aktuaria' else DATA_JADWAL_BD
    dosen_valid       = list(jadwal_prodi.keys())
    kelas_landing_aktif = [k for k in semua_kelas_aktif if k['dosen_key'] in dosen_valid]

    st.markdown("<hr style='opacity: 0.2;'>", unsafe_allow_html=True)

    if kelas_landing_aktif:
        st.success(f"📍 **{len(kelas_landing_aktif)} Kelas Terbuka Saat Ini (Prodi {prodi_terpilih}):**")
        for k in kelas_landing_aktif:
            nm = k['makul'].rsplit(' (', 1)[0]
            nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
            st.markdown(
                f"<div class='kelas-badge'>📚 <b>{nm}</b><br>"
                f"<span style='opacity:0.6;font-size:13px;'>👨‍🏫 {nd} &nbsp;|&nbsp; Pertemuan {k['pertemuan']}</span></div>",
                unsafe_allow_html=True
            )
    else:
        st.info(f"🕒 Belum ada kelas yang dibuka oleh dosen {prodi_terpilih} saat ini.")

    st.markdown("<br><h3 style='text-align:center;font-weight:700;'>Pilih Akses Anda</h3><br>", unsafe_allow_html=True)

    col_mhs, col_dos = st.columns(2)
    with col_mhs:
        st.markdown("""
            <div class='akses-card'>
                <div style='font-size:40px;'>🧑‍🎓</div>
                <div style='font-weight:700;font-size:17px;margin-top:10px;'>Mahasiswa</div>
                <div style='font-size:12px;opacity:0.6;margin-top:6px;'>Isi daftar hadir</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
        if st.button("Masuk Mahasiswa", use_container_width=True, key="btn_mhs"):
            ke_halaman('mahasiswa')

    with col_dos:
        st.markdown("""
            <div class='akses-card'>
                <div style='font-size:40px;'>👨‍🏫</div>
                <div style='font-weight:700;font-size:17px;margin-top:10px;'>Dosen</div>
                <div style='font-size:12px;opacity:0.6;margin-top:6px;'>Kelola kelas & rekap</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
        if st.button("Masuk Dosen", use_container_width=True, key="btn_dos"):
            ke_halaman('dosen')

# ============================================================
# HALAMAN MAHASISWA
# ============================================================
elif st.session_state['halaman'] == 'mahasiswa':

    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← Kembali", key="back_mhs"):
            # Reset QR state saat kembali
            st.session_state['qr_makul']     = None
            st.session_state['qr_pertemuan'] = None
            st.session_state['qr_semester']  = None
            st.session_state['sudah_presensi'] = False
            ke_halaman('landing')

    prodi_mhs = st.session_state.get('prodi', 'Bisnis Digital')

    if st.session_state.get('sudah_presensi') and st.session_state.get('konfirmasi_data'):
        konfirmasi = st.session_state['konfirmasi_data']
        jumlah_hadir = hitung_hadir(konfirmasi['makul_raw'], konfirmasi['pertemuan'])
        st.markdown(f"""
            <div class="konfirmasi-box">
                <h2>✅ Presensi Berhasil!</h2>
                <p style="font-size:18px;font-weight:700;margin:0">{konfirmasi['nama']}</p>
                <p style="opacity:0.6;margin:4px 0 0">NIM: {konfirmasi['nim']}</p>
                <hr style="opacity:0.2;margin:14px 0">
                <p style="margin:0;font-size:14px;">📚 {konfirmasi['makul']}</p>
                <p style="margin:4px 0;font-size:13px;opacity:0.7;">
                    Semester {konfirmasi['semester']} &nbsp;·&nbsp; Pertemuan ke-{konfirmasi['pertemuan']}
                </p>
                <p style="margin:4px 0;font-size:13px;opacity:0.7;">
                    🗓️ {konfirmasi['tanggal']} &nbsp;·&nbsp; ⏰ {konfirmasi['jam']} WIB
                </p>
            </div>
            <div class="counter-box">
                <div class="angka">{jumlah_hadir}</div>
                <div style="font-size:13px;opacity:0.6;">Mahasiswa hadir di sesi ini</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Kembali ke Beranda", use_container_width=True):
            st.session_state['sudah_presensi'] = False
            st.session_state['konfirmasi_data'] = None
            st.session_state['qr_makul'] = None
            st.session_state['qr_pertemuan'] = None
            st.session_state['qr_semester'] = None
            ke_halaman('landing')

    else:
        semua_kelas_aktif = baca_semua_kelas_aktif()
        jadwal_prodi      = DATA_JADWAL_AKT if prodi_mhs == 'Aktuaria' else DATA_JADWAL_BD
        dosen_valid       = list(jadwal_prodi.keys())
        kelas_mhs_aktif   = [k for k in semua_kelas_aktif if k['dosen_key'] in dosen_valid]

        st.markdown(f"""
            <div class="clock-container">
                🕒 {waktu_sekarang.strftime('%A, %d %B %Y — %H:%M:%S')} WIB
            </div>
        """, unsafe_allow_html=True)

        # ── Banner jika masuk dari QR ──
        qr_makul = st.session_state.get('qr_makul')
        if qr_makul:
            nama_tampil = qr_makul.rsplit(' (', 1)[0] if ' (' in qr_makul else qr_makul
            st.markdown(f"""
                <div class="qr-banner">
                    <div style="font-weight:700;font-size:15px;">📲 Scan QR Berhasil!</div>
                    <div style="font-size:13px;opacity:0.8;margin-top:4px;">
                        Kelas: <b>{nama_tampil}</b> &nbsp;·&nbsp;
                        Smt {st.session_state.get('qr_semester','-')} &nbsp;·&nbsp;
                        Pertemuan ke-{st.session_state.get('qr_pertemuan','-')}
                    </div>
                    <div style="font-size:12px;opacity:0.6;margin-top:2px;">
                        Sesi sudah otomatis terpilih. Isi nama, NIM, dan rangkuman.
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with st.form(key="form_presensi", clear_on_submit=False):
            st.markdown("<h4 style='text-align:center;margin-bottom:20px;'>📝 Form Kehadiran</h4>", unsafe_allow_html=True)

            col_nama, col_nim = st.columns(2)
            with col_nama:
                nama = st.text_input("Nama Lengkap", placeholder="Nama lengkap kamu")
            with col_nim:
                nim  = st.text_input("NIM", placeholder="Contoh: 220101001")

            # Jika dari QR → auto-select kelas, tidak bisa diubah
            if qr_makul:
                # Cari kelas yang sesuai dari kelas aktif
                kelas_qr = next(
                    (k for k in kelas_mhs_aktif if k['makul'] == qr_makul),
                    None
                )
                if kelas_qr:
                    nm  = kelas_qr['makul'].rsplit(' (', 1)[0]
                    nd  = kelas_qr['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                    st.markdown(f"""
                        <div style='background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.25);
                            border-radius:10px;padding:10px 14px;font-size:14px;margin-bottom:8px;'>
                            🏫 <b>{nm}</b> &nbsp;—&nbsp; {nd} &nbsp;|&nbsp; Pertemuan {kelas_qr['pertemuan']}
                        </div>
                    """, unsafe_allow_html=True)
                    kelas_terpilih_obj = kelas_qr
                    opsi_kelas = [f"{nm} — {nd} | Pertemuan {kelas_qr['pertemuan']}"]
                    pilihan_kelas_label = opsi_kelas[0]
                    # Hidden selectbox agar form valid
                    st.selectbox("🏫 Sesi Kelas:", options=opsi_kelas,
                                 label_visibility="collapsed", disabled=True)
                else:
                    st.warning("⚠️ Kelas dari QR ini sudah tidak aktif. Pilih kelas manual di bawah.")
                    kelas_terpilih_obj = None
                    qr_makul = None

            if not qr_makul:
                if kelas_mhs_aktif:
                    def label_kelas(k):
                        nm = k['makul'].rsplit(' (', 1)[0]
                        nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                        return f"{nm} — {nd} | Pertemuan {k['pertemuan']}"
                    opsi_kelas          = [label_kelas(k) for k in kelas_mhs_aktif]
                    pilihan_kelas_label = st.selectbox("🏫 Pilih Sesi Kelas:", options=opsi_kelas)
                    kelas_terpilih_obj  = None  # akan dicari saat submit
                else:
                    st.warning(f"⚠️ Belum ada kelas {prodi_mhs} yang aktif. Silakan tunggu instruksi dosen.")
                    pilihan_kelas_label = None
                    kelas_terpilih_obj  = None

            materi = st.text_area(
                "Rangkuman Materi Hari Ini (min. 20 karakter)",
                placeholder="Tulis ringkasan singkat materi yang dibahas...",
                height=100
            )
            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.form_submit_button(label="KIRIM BUKTI HADIR")

        if submit_button:
            # Cari kelas yang dipilih
            if kelas_terpilih_obj is None and kelas_mhs_aktif and pilihan_kelas_label:
                idx_pilihan   = opsi_kelas.index(pilihan_kelas_label)
                kelas_terpilih_obj = kelas_mhs_aktif[idx_pilihan]

            if not kelas_mhs_aktif and not kelas_terpilih_obj:
                st.error("Gagal! Belum ada kelas yang dibuka saat ini.")
            elif not nama.strip():
                st.error("Nama wajib diisi!")
            elif not nim.strip():
                st.error("NIM wajib diisi!")
            elif len(materi.strip()) < 20:
                st.error(f"Rangkuman terlalu pendek ({len(materi.strip())} karakter). Minimal 20 karakter.")
            elif kelas_terpilih_obj is None:
                st.error("Pilih kelas terlebih dahulu.")
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
                            "nama":      nama.strip(), "nim": nim.strip(),
                            "makul":     nm_makul,
                            "makul_raw": kelas_terpilih_obj["makul"],
                            "tanggal":   tgl, "jam": jam,
                            "pertemuan": kelas_terpilih_obj["pertemuan"],
                            "semester":  kelas_terpilih_obj["semester"],
                        }
                        st.session_state['sudah_presensi'] = True
                        st.balloons()
                        st.rerun()
                except Exception as e:
                    st.error(f"Gagal menghubungi database: {e}")

# ============================================================
# HALAMAN DOSEN
# ============================================================
elif st.session_state['halaman'] == 'dosen':

    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← Kembali", key="back_dos"):
            ke_halaman('landing')

    if not st.session_state.get('dosen_login', False):
        st.markdown("<h3 style='text-align:center;font-weight:800;color:#6366F1;'>Autentikasi Dosen</h3>", unsafe_allow_html=True)

        idx_prodi_dosen = 0 if st.session_state['prodi'] == 'Bisnis Digital' else 1
        prodi_dosen = st.selectbox("Pilih Program Studi", ["Bisnis Digital", "Aktuaria"], index=idx_prodi_dosen)
        st.session_state['prodi'] = prodi_dosen
        jadwal_aktif_login = DATA_JADWAL_AKT if prodi_dosen == 'Aktuaria' else DATA_JADWAL_BD

        with st.form(key="form_login_dosen"):
            pilihan_nama_login = st.selectbox("Nama Dosen", options=list(jadwal_aktif_login.keys()))
            password_input     = st.text_input("Kode Akses Panel", type="password", placeholder="Masukkan password...")
            st.markdown("<br>", unsafe_allow_html=True)
            tombol_login       = st.form_submit_button("Masuk Panel Dashboard")

        if tombol_login:
            PASSWORD_DOSEN = st.secrets.get("password_dosen", "dosen123")
            if password_input == PASSWORD_DOSEN:
                st.session_state['dosen_login']      = True
                st.session_state['nama_dosen_login'] = pilihan_nama_login
                st.rerun()
            else:
                st.error("Kode akses tidak valid!")

    else:
        nama_dosen_aktif = st.session_state.get('nama_dosen_login')
        dosen_key        = nama_dosen_aktif

        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.markdown(f"#### 👨‍🏫 Dashboard: {nama_dosen_aktif.split(',')[0]}")
        with col_logout:
            if st.button("Keluar", use_container_width=True):
                st.session_state['dosen_login']      = False
                st.session_state['nama_dosen_login'] = None
                ke_halaman('landing')

        semua_kelas_aktif    = baca_semua_kelas_aktif()
        prodi_dsn_sekarang   = 'Aktuaria' if nama_dosen_aktif in DATA_JADWAL_AKT else 'Bisnis Digital'
        jadwal_dsn_sekarang  = DATA_JADWAL_AKT if prodi_dsn_sekarang == 'Aktuaria' else DATA_JADWAL_BD
        dosen_valid          = list(jadwal_dsn_sekarang.keys())
        kelas_aktif_prodi_ini = [k for k in semua_kelas_aktif if k['dosen_key'] in dosen_valid]

        tab1, tab2, tab3 = st.tabs(["🚀 Buka Kelas & QR", "📋 Monitor Kelas Aktif", "📂 Arsip & Histori"])

        # ─── TAB 1 — BUKA KELAS & QR ───────────────────────────
        with tab1:
            st.markdown("#### Aktivasi Perkuliahan")
            st.caption(f"Login sebagai: **{nama_dosen_aktif}** (Prodi {prodi_dsn_sekarang})")

            daftar_makul  = get_makul_dosen(nama_dosen_aktif)
            pilihan_makul = st.selectbox("Nama Mata Kuliah", options=daftar_makul)
            input_makul_gabungan = f"{pilihan_makul} ({nama_dosen_aktif})"

            status_dosen = baca_status_kelas_dosen(dosen_key)
            if status_dosen["aktif"]:
                nm_aktif = status_dosen['makul'].rsplit(' (', 1)[0]
                st.success(f"🟢 Kelas Aktif: **{nm_aktif}** (Smt {status_dosen['semester']} - Pertemuan {status_dosen['pertemuan']})")
            else:
                st.info("⚪ Status: **Standby** — belum ada kelas aktif.")

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
                    if st.button("✅ Aktifkan Akses Kelas", use_container_width=True):
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

            st.markdown("---")
            st.markdown("#### 📲 Generator QR Code Presensi")
            st.caption("QR ini langsung membuka form presensi dengan sesi kelas sudah terpilih otomatis.")

            try:
                base_url_default = st.secrets.get("app_url", "https://your-app.streamlit.app")
            except Exception:
                base_url_default = "https://your-app.streamlit.app"

            if status_dosen["aktif"]:
                makul_qr    = status_dosen['makul']
                smt_qr      = status_dosen['semester']
                prt_qr      = status_dosen['pertemuan']
                import urllib.parse
                qr_url = (
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
                        <div style='background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);
                            border-radius:12px;padding:14px;font-size:13px;'>
                            <b>Cara pakai:</b><br>
                            1️⃣ Aktifkan kelas dulu (tombol di atas)<br>
                            2️⃣ Tampilkan / print QR ini<br>
                            3️⃣ Mahasiswa scan → langsung ke form<br>
                            4️⃣ Sesi otomatis terpilih, tinggal isi nama & NIM
                        </div>
                    """, unsafe_allow_html=True)
                    st.code(qr_url, language=None)
            else:
                st.warning("⚠️ Aktifkan kelas terlebih dahulu untuk generate QR.")
                st.markdown(f"**URL App:** `{base_url_default}`")
                st.caption("Isi `app_url` di secrets.toml dengan URL Streamlit app kamu.")

        # ─── TAB 2 — MONITOR ────────────────────────────────────
        with tab2:
            st.markdown("#### Monitor Kelas Aktif")
            if st.button("🔄 Refresh Data", use_container_width=True):
                baca_semua_kelas_aktif_cached.clear()
                hitung_hadir.clear()
                st.rerun()

            if not kelas_aktif_prodi_ini:
                st.caption(f"Tidak ada kelas aktif saat ini untuk Prodi {prodi_dsn_sekarang}.")
            else:
                for k in kelas_aktif_prodi_ini:
                    nm = k['makul'].rsplit(' (', 1)[0]
                    nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                    jumlah = hitung_hadir(k['makul'], k['pertemuan'])
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"**{nm}**")
                            st.caption(f"👨‍🏫 {nd} &nbsp;·&nbsp; Semester {k['semester']} &nbsp;·&nbsp; Pertemuan {k['pertemuan']}")
                        with c2:
                            st.metric("Hadir", jumlah)
                        try:
                            raw  = k['makul']
                            safe = raw.replace("/","-").replace(":","-").replace("\\","-")
                            if len(safe) > 28:
                                suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                                safe   = safe[:24] + "_" + suffix
                            ws_mon = get_sheet().worksheet(safe)
                            data_mon = ws_mon.get_all_records()
                            df_mf = pd.DataFrame(data_mon)
                            df_mf = df_mf[df_mf['Pertemuan Ke'].astype(str) == str(k['pertemuan'])]
                            if not df_mf.empty:
                                with st.expander(f"Lihat {len(df_mf)} mahasiswa hadir"):
                                    for i, row in df_mf.iterrows():
                                        st.markdown(
                                            f"<b>{row['NIM']}</b> — {row['Nama']}"
                                            f"<br><span style='font-size:12px;opacity:0.5;'>🕒 {row['Jam Isi']} WIB</span>",
                                            unsafe_allow_html=True
                                        )
                                        if i < len(df_mf) - 1:
                                            st.markdown("<hr style='margin:6px 0;opacity:0.1;'>", unsafe_allow_html=True)
                            else:
                                st.info("Belum ada mahasiswa yang hadir.")
                        except gspread.exceptions.WorksheetNotFound:
                            st.info("Belum ada data presensi.")
                        except Exception as e:
                            st.error(f"Error: {e}")

        # ─── TAB 3 — ARSIP ──────────────────────────────────────
        with tab3:
            st.markdown("#### Pusat Data Kehadiran")
            makul_opsi    = get_makul_dosen(nama_dosen_aktif)
            pilih_makul_a = st.selectbox("Pilih Mata Kuliah:", options=makul_opsi, key="arsip_makul")
            makul_gabung  = f"{pilih_makul_a} ({nama_dosen_aktif})"

            sub1, sub2 = st.tabs(["📊 Lihat & Unduh", "🗑️ Hapus Entri Salah"])

            with sub1:
                with st.expander("📥 Unduh Master Rekap Semester (P1-P16)", expanded=False):
                    if st.button("Generate Rekap Global", use_container_width=True):
                        try:
                            raw  = makul_gabung
                            safe = raw.replace("/","-").replace(":","-").replace("\\","-")
                            if len(safe) > 28:
                                suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                                safe   = safe[:24] + "_" + suffix
                            ws   = get_sheet().worksheet(safe)
                            data = ws.get_all_records()
                            if data:
                                df_all = pd.DataFrame(data)
                                if 'Pertemuan Ke' in df_all.columns:
                                    df_all['_sort'] = pd.to_numeric(df_all['Pertemuan Ke'], errors='coerce')
                                    df_all = df_all.sort_values(['_sort','NIM']).drop(columns=['_sort'])
                                out = BytesIO(); df_all.to_excel(out, index=False, engine='openpyxl'); out.seek(0)
                                st.success(f"{len(df_all)} total rekaman.")
                                st.download_button("⬇️ Download Excel Rekap", data=out,
                                    file_name=f"MASTER_{pilih_makul_a}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True)
                            else:
                                st.info("Database masih kosong.")
                        except gspread.exceptions.WorksheetNotFound:
                            st.info("Belum ada sheet untuk mata kuliah ini.")

                st.markdown("---")
                col_f, col_a = st.columns([2, 1])
                with col_f:
                    opt_prt2    = [str(i) for i in range(1, 17)]
                    pilih_prt_a = st.selectbox("Lihat Pertemuan Ke-:", options=opt_prt2)
                with col_a:
                    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
                    btn_tampil = st.button("Tampilkan Data", use_container_width=True)

                if btn_tampil:
                    try:
                        raw  = makul_gabung
                        safe = raw.replace("/","-").replace(":","-").replace("\\","-")
                        if len(safe) > 28:
                            suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                            safe   = safe[:24] + "_" + suffix
                        ws   = get_sheet().worksheet(safe)
                        data = ws.get_all_records()
                        if data:
                            df_f = pd.DataFrame(data)
                            df_f = df_f[df_f['Pertemuan Ke'].astype(str) == str(pilih_prt_a)]
                            if not df_f.empty:
                                if "Mata Kuliah" in df_f.columns:
                                    df_f = df_f.drop(columns=["Mata Kuliah"])
                                st.dataframe(df_f, use_container_width=True)
                                out = BytesIO(); df_f.to_excel(out, index=False, engine='openpyxl'); out.seek(0)
                                st.download_button("⬇️ Unduh Excel Sesi Ini", data=out,
                                    file_name=f"Sesi_{pilih_prt_a}_{pilih_makul_a}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                            else:
                                st.warning("Belum ada mahasiswa hadir di sesi ini.")
                        else:
                            st.info("Belum ada data presensi.")
                    except gspread.exceptions.WorksheetNotFound:
                        st.info("Sheet belum tersedia.")

                st.markdown("---")
                st.markdown("##### 📜 Histori Log Kelas")
                try:
                    raw  = makul_gabung
                    safe = raw.replace("/","-").replace(":","-").replace("\\","-")
                    if len(safe) > 28:
                        suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                        safe   = safe[:24] + "_" + suffix
                    ws   = get_sheet().worksheet(safe)
                    data = ws.get_all_records()
                    if data:
                        df_h = pd.DataFrame(data)
                        if 'Pertemuan Ke' in df_h.columns:
                            summ = df_h.groupby('Pertemuan Ke').agg(
                                total=('NIM','count'), tgl=('Tanggal','min')
                            ).reset_index()
                            summ['_s'] = pd.to_numeric(summ['Pertemuan Ke'], errors='coerce')
                            summ = summ.sort_values('_s', ascending=False).drop(columns=['_s'])
                            for _, rh in summ.iterrows():
                                st.markdown(f"""
                                    <div class="histori-container">
                                        <div style="display:flex;justify-content:space-between;">
                                            <span>📅 <b>Pertemuan Ke-{rh['Pertemuan Ke']}</b></span>
                                            <span style="color:#10B981;font-weight:600;">{rh['total']} Hadir</span>
                                        </div>
                                        <span style='font-size:12px;opacity:0.5;'>Tanggal: {rh['tgl']}</span>
                                    </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.caption("Belum ada riwayat kelas.")
                except Exception:
                    st.caption("Histori belum tersedia.")

            with sub2:
                st.warning("⚠️ Gunakan fitur ini hanya untuk menghapus entri yang salah (NIM typo, dll).")
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    nim_hapus = st.text_input("NIM yang akan dihapus", placeholder="Contoh: 220101001")
                with col_h2:
                    opt_prt3  = [str(i) for i in range(1, 17)]
                    prt_hapus = st.selectbox("Dari Pertemuan Ke-:", options=opt_prt3, key="hapus_prt")
                if st.button("🗑️ Hapus Entri Ini", type="primary", use_container_width=True):
                    if nim_hapus.strip():
                        raw  = makul_gabung
                        safe = raw.replace("/","-").replace(":","-").replace("\\","-")
                        if len(safe) > 28:
                            suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                            safe   = safe[:24] + "_" + suffix
                        ok, pesan = hapus_entri_presensi(safe, nim_hapus.strip(), prt_hapus)
                        if ok: st.success(f"✅ {pesan}")
                        else:  st.error(f"❌ {pesan}")
                    else:
                        st.error("Masukkan NIM terlebih dahulu.")