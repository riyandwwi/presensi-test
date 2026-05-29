import streamlit as st
import pandas as pd
from datetime import datetime
import qrcode
from io import BytesIO
import gspread
from google.oauth2.service_account import Credentials
import pytz 

# ============================================================
# SET ZONA WAKTU (WIB) & INITIALISASI SESSION STATE
# ============================================================
tz_wib = pytz.timezone('Asia/Jakarta')
waktu_sekarang = datetime.now(tz_wib)

if 'dosen_login' not in st.session_state:
    st.session_state['dosen_login'] = False

# State untuk membatasi mahasiswa absen berkali-kali di perangkat yang sama
if 'sudah_presensi' not in st.session_state:
    st.session_state['sudah_presensi'] = False

if 'halaman' not in st.session_state:
    st.session_state['halaman'] = 'landing'

# ============================================================
# CONFIG HALAMAN
# ============================================================
st.set_page_config(
    page_title="Sistem Presensi Kuliah",
    page_icon="📝",
    layout="centered"
)

# ============================================================
# CSS
# ============================================================
# ============================================================
# CSS
# ============================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600&display=swap');
    html, body, [class*="css"], p, span, div, label { font-family: 'DM Sans', sans-serif !important; color: #0F172A; }
    h1, h2, h3, h4, h5 { font-family: 'Sora', sans-serif !important; }
    .stApp { background-color: #F1F5F9; }
    header {visibility: hidden;} footer {visibility: hidden;} #MainMenu {visibility: hidden;}

    /* TOP BAR */
    .top-bar {
        background: #0F172A; border-radius: 16px; padding: 18px 24px;
        display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;
    }
    .top-bar-logo {
        display: inline-flex; align-items: center; justify-content: center;
        width: 38px; height: 38px; background: #38BDF8; border-radius: 9px;
        font-family: 'Sora', sans-serif !important; font-weight: 800; font-size: 14px;
        color: #0F172A; margin-right: 12px; vertical-align: middle;
    }
    .top-bar-title { font-family: 'Sora', sans-serif !important; font-weight: 700; font-size: 15px; color: #F8FAFC; display: inline; }
    .top-bar-sub { font-size: 11px; color: #64748B; display: block; margin-top: 1px; }
    .top-bar-date { font-size: 12px; color: #64748B; font-weight: 500; }

    /* ROLE CARDS */
    .role-card {
        background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 18px;
        padding: 32px 20px 24px; text-align: center;
    }
    .role-card-label { font-family: 'Sora', sans-serif !important; font-weight: 700; font-size: 19px; color: #0F172A; margin-bottom: 6px; }
    .role-card-desc { font-size: 13px; color: #64748B; line-height: 1.5; }
    .role-divider { width: 36px; height: 3px; background: #38BDF8; border-radius: 99px; margin: 14px auto 0; }

    /* KELAS BADGE */
    .kelas-badge {
        background: #FFFFFF; border: 1.5px solid #E2E8F0; border-left: 4px solid #38BDF8;
        border-radius: 12px; padding: 11px 16px; margin-bottom: 8px;
        font-size: 14px; color: #0F172A; font-weight: 600;
    }
    .kelas-badge small { color: #64748B; font-weight: 400; }

    /* CLOCK */
    .clock-container {
        background: #0F172A; border-radius: 12px; padding: 14px 18px;
        text-align: center; margin-bottom: 20px; color: #38BDF8;
        font-family: 'Sora', sans-serif !important; font-weight: 700; font-size: 15px; letter-spacing: 0.3px;
    }
    .clock-container small { color: #475569; font-weight: 400; font-size: 11px; }

    /* FORM */
    div[data-testid="stForm"] {
        background: #FFFFFF !important; border: 1.5px solid #E2E8F0 !important;
        border-radius: 18px !important; padding: 30px !important;
        box-shadow: 0 2px 16px rgba(0,0,0,0.04) !important;
    }
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
        background-color: #F8FAFC !important; border: 1.5px solid #E2E8F0 !important;
        border-radius: 10px !important; padding: 11px 14px !important;
        font-size: 14px !important; transition: all 0.2s ease !important;
    }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {
        border-color: #38BDF8 !important; background-color: #FFFFFF !important;
        box-shadow: 0 0 0 3px rgba(56,189,248,0.12) !important;
    }
    button[kind="formSubmit"] {
        background: #0F172A !important; color: #38BDF8 !important; border: none !important;
        border-radius: 10px !important; padding: 13px 24px !important;
        font-size: 14px !important; font-weight: 700 !important;
        font-family: 'Sora', sans-serif !important; width: 100% !important; letter-spacing: 0.3px !important;
    }
    .stButton > button {
        border-radius: 10px !important; font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important; font-size: 13px !important;
        border: 1.5px solid #E2E8F0 !important; background: #FFFFFF !important;
        color: #0F172A !important; transition: all 0.15s !important;
    }
    .stButton > button:hover { border-color: #38BDF8 !important; color: #0369A1 !important; }

    /* HISTORI */
    .histori-container {
        background: #FFFFFF; border: 1.5px solid #E2E8F0; border-left: 4px solid #0F172A;
        border-radius: 12px; padding: 14px 18px; margin-bottom: 8px;
    }

    /* SECTION LABEL */
    .sec-label {
        font-family: 'Sora', sans-serif !important; font-size: 11px; font-weight: 700;
        color: #94A3B8; text-transform: uppercase; letter-spacing: 1.4px;
        margin: 22px 0 10px; padding-bottom: 8px; border-bottom: 1px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# KONEKSI GOOGLE SHEETS
# ============================================================
SHEET_ID = "1Msh_H8XgFpAJiQFuPB7l4V_0YDPcNWSBEW6y9X9eBk8"
SCOPES   = ["https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_sheet():
    creds  = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)

# ============================================================
# FUNGSI BACA / TULIS STATUS MULTI-KELAS KE GOOGLE SHEETS
# ============================================================
STATUS_SHEET = "STATUS_KELAS"

def baca_semua_kelas_aktif():
    try:
        sheet = get_sheet()
        try:
            ws = sheet.worksheet(STATUS_SHEET)
        except gspread.exceptions.WorksheetNotFound:
            ws = sheet.add_worksheet(title=STATUS_SHEET, rows="50", cols="6")
            ws.append_row(["makul", "semester", "pertemuan", "aktif", "dosen_key"])
            return []

        data = ws.get_all_records()
        aktif = []
        for row in data:
            if str(row.get("aktif", "0")) == "1":
                aktif.append({
                    "makul":     row.get("makul", ""),
                    "semester":  row.get("semester", "-"),
                    "pertemuan": row.get("pertemuan", "-"),
                    "dosen_key": row.get("dosen_key", ""),
                })
        return aktif
    except Exception as e:
        st.error(f"Gagal terhubung ke Google Sheets: {e}")
        return []

def baca_status_kelas_dosen(dosen_key):
    try:
        sheet = get_sheet()
        try:
            ws = sheet.worksheet(STATUS_SHEET)
        except gspread.exceptions.WorksheetNotFound:
            return {"makul": "Belum Diatur", "semester": "-", "pertemuan": "-", "aktif": False}

        data = ws.get_all_records()
        for row in data:
            if row.get("dosen_key", "") == dosen_key:
                return {
                    "makul":     row.get("makul", "Belum Diatur"),
                    "semester":  row.get("semester", "-"),
                    "pertemuan": row.get("pertemuan", "-"),
                    "aktif":     str(row.get("aktif", "0")) == "1",
                }
    except Exception as e:
        st.error(f"Gagal baca status kelas: {e}")
    return {"makul": "Belum Diatur", "semester": "-", "pertemuan": "-", "aktif": False}

def tulis_status_kelas(makul, semester, pertemuan, dosen_key, aktif=True):
    sheet = get_sheet()
    try:
        ws = sheet.worksheet(STATUS_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=STATUS_SHEET, rows="50", cols="6")
        ws.append_row(["makul", "semester", "pertemuan", "aktif", "dosen_key"])

    data = ws.get_all_values()
    header = data[0] if data else []

    try:
        col_dosen = header.index("dosen_key") + 1
    except ValueError:
        ws.append_row(["makul", "semester", "pertemuan", "aktif", "dosen_key"])
        col_dosen = 5

    row_idx = None
    for i, row in enumerate(data[1:], start=2):
        if len(row) >= col_dosen and row[col_dosen - 1] == dosen_key:
            row_idx = i
            break

    new_row = [makul, semester, pertemuan, "1" if aktif else "0", dosen_key]
    if row_idx:
        ws.update(f"A{row_idx}:E{row_idx}", [new_row])
    else:
        ws.append_row(new_row)

def tutup_kelas(dosen_key):
    sheet = get_sheet()
    ws = sheet.worksheet(STATUS_SHEET)
    data = ws.get_all_values()
    header = data[0] if data else []
    col_dosen = header.index("dosen_key") + 1
    col_aktif = header.index("aktif") + 1
    for i, row in enumerate(data[1:], start=2):
        if len(row) >= col_dosen and row[col_dosen - 1] == dosen_key:
            ws.update_cell(i, col_aktif, "0")
            return True
    return False

def tutup_kelas_by_makul(makul):
    sheet = get_sheet()
    ws = sheet.worksheet(STATUS_SHEET)
    data = ws.get_all_values()
    header = data[0] if data else []
    col_makul = header.index("makul") + 1
    col_aktif = header.index("aktif") + 1
    for i, row in enumerate(data[1:], start=2):
        if len(row) >= col_makul and row[col_makul - 1] == makul:
            ws.update_cell(i, col_aktif, "0")
            return True
    return False

# ============================================================
# FUNGSI SIMPAN PRESENSI
# ============================================================
def get_or_create_worksheet(sheet, title):
    try:
        ws = sheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=title, rows="1000", cols="10")
        ws.append_row(["Tanggal", "Jam Isi", "Semester", "Pertemuan Ke", "NIM", "Nama", "Rangkuman Materi"])
    return ws

def simpan_ke_sheets(data: dict):
    sheet   = get_sheet()
    nama_ws = data["Mata Kuliah"].replace("/", "-").replace(":", "-")[:50]
    ws      = get_or_create_worksheet(sheet, nama_ws)
    existing = ws.get_all_values()
    if not existing:
        ws.append_row(["Tanggal", "Jam Isi", "Semester", "Pertemuan Ke", "NIM", "Nama", "Rangkuman Materi"])
    ws.append_row([
        data["Tanggal"], data["Jam Isi"],
        data["Semester"], data["Pertemuan Ke"], data["NIM"],
        data["Nama"], data["Rangkuman Materi"]
    ])

# ============================================================
# FUNGSI QR CODE
# ============================================================
def generate_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E293B", back_color="#FFFFFF")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ============================================================
# DATA JADWAL DOSEN
# ============================================================
DATA_JADWAL = {
    "Riyan Dwi Yulian P, S.Kom., M.Kom.": [
        "Analisis Perancangan Berbasis Objek A",
        "Analisis Perancangan Berbasis Objek B",
        "Mata Kuliah Pilihan Digital (Data Analyze) A",
        "Pemrograman Mobile",
        "Data Mining A",
        "Data Mining B",
        "Mata Kuliah Pilihan Digital (Data Analyze) B"
    ],
    "Esti Nur Wakhidah, S.Pd., M.M.": [
        "Manajemen Pemasaran Bisnis A",
        "Metodologi Penelitian B",
        "Komunikasi Bisnis",
        "Metodologi Penelitian A",
        "Manajemen Pemasaran Bisnis B"
    ],
    "Didik Adi Sabara, S.M., M.E.": [
        "Mentoring Bisnis Digital A",
        "Mentoring Bisnis Digital B",
        "E-Commerce",
        "Kewirausahaan Digital A",
        "Kewirausahaan Digital B"
    ],
    "Nour Mohammed Moussa Al Fattah M.Pd.": [
        "AIK 2 A",
        "AIK 4",
        "AIK 2 B"
    ],
    "Ridhwan Sinatria, S.E., M.M.": [
        "Manajemen Sumber Daya Manusia B",
        "Mata Kuliah Pilihan Bisnis (Ekonomi Digital) A",
        "Manajemen Sumber Daya Manusia A",
        "Mata Kuliah Pilihan Bisnis (Ekonomi Digital) B",
        "Manajemen Risiko",
        "Kerja Praktek A (Team Teaching)",
        "Kerja Praktek B (Team Teaching)"
    ],
    "Kartika Dewi Permatasari, S.Ak., M.Ak., Ak.": [
        "Dasar-dasar Akuntansi A",
        "Dasar-dasar Akuntansi B",
        "Perpajakan",
        "Kerja Praktek A (Team Teaching)",
        "Kerja Praktek B (Team Teaching)"
    ],
    "Sriyati., S.Kom., M.Kom.": [
        "Pemrograman Web A",
        "Basis Data",
        "Pemrograman Web B",
        "Sistem Pendukung Keputusan"
    ],
    "Doni Uji Windiatmoko, S.Pd., M.Pd.": [
        "Kewarganegaraan B",
        "Kewarganegaraan A"
    ],
    "Purwati, S.S., M.Hum.": [
        "Bahasa Inggris 2 A",
        "Bahasa Inggris 2 B"
    ]
}

# ============================================================
# NAVIGASI HALAMAN
# ============================================================
def ke_halaman(nama):
    st.session_state['halaman'] = nama
    st.rerun()

# ============================================================
# HEADER (tampil di semua halaman)
# ============================================================
st.markdown(f"""
    <div class="top-bar">
        <div style="display:flex; align-items:center;">
            <div class="top-bar-logo">BD</div>
            <div>
                <span class="top-bar-title">PRESENSI BISNIS DIGITAL</span>
                <span class="top-bar-sub">Sistem Kehadiran Akademik — Ver 1.0</span>
            </div>
        </div>
        <div class="top-bar-date">{waktu_sekarang.strftime('%d %b %Y')}</div>
    </div>
""", unsafe_allow_html=True)

# ============================================================
# HALAMAN LANDING — pilih peran
# ============================================================
if st.session_state['halaman'] == 'landing':

    semua_kelas_aktif = baca_semua_kelas_aktif()

    if semua_kelas_aktif:
        st.markdown(f"<div class='sec-label'>Kelas Aktif Saat Ini — {len(semua_kelas_aktif)} Sesi</div>", unsafe_allow_html=True)
        for k in semua_kelas_aktif:
            nama_makul = k['makul'].rsplit(' (', 1)[0]
            nama_dosen = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
            st.markdown(
                f"<div class='kelas-badge'>{nama_makul}"
                f"<br><small>{nama_dosen} &nbsp;·&nbsp; Semester {k['semester']} &nbsp;·&nbsp; Pertemuan {k['pertemuan']}</small></div>",
                unsafe_allow_html=True
            )
    else:
        st.markdown("<div style='background:#FFF7ED;border:1.5px solid #FED7AA;border-radius:12px;padding:12px 18px;margin-bottom:16px;font-size:14px;color:#9A3412;font-weight:500;'>Belum ada kelas yang dibuka oleh Dosen saat ini.</div>", unsafe_allow_html=True)

    st.markdown("<div class='sec-label'>Masuk Sebagai</div>", unsafe_allow_html=True)

    col_mhs, col_dos = st.columns(2)
    with col_mhs:
        st.markdown("""
            <div class='role-card'>
                <div class='role-card-label'>Mahasiswa</div>
                <div class='role-card-desc'>Isi form presensi<br>kehadiran kuliah</div>
                <div class='role-divider'></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
        if st.button("Masuk →", use_container_width=True, key="btn_mhs"):
            ke_halaman('mahasiswa')
    with col_dos:
        st.markdown("""
            <div class='role-card'>
                <div class='role-card-label'>Dosen</div>
                <div class='role-card-desc'>Kelola kelas aktif<br>& rekap presensi</div>
                <div class='role-divider'></div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
        if st.button("Masuk →", use_container_width=True, key="btn_dos"):
            ke_halaman('dosen')

# ============================================================
# HALAMAN MAHASISWA — form presensi
# ============================================================
elif st.session_state['halaman'] == 'mahasiswa':

    if st.button("← Kembali", key="back_mhs"):
        ke_halaman('landing')

    if st.session_state['sudah_presensi']:
        st.success("✅ Anda sudah berhasil melakukan presensi pada sesi ini. Terima kasih!")
        st.info("💡 Untuk memberikan kesempatan presensi kepada mahasiswa lain menggunakan perangkat mereka sendiri, form telah dikunci untuk sesi ini.")
    else:
        semua_kelas_aktif = baca_semua_kelas_aktif()

        st.markdown(f"""
            <div class="clock-container">
                🕒 {waktu_sekarang.strftime('%d-%m-%Y')} pukul {waktu_sekarang.strftime('%H:%M:%S')} WIB
                <br><small style="color: #D97706; font-weight: normal;">*Waktu tercatat akurat menggunakan WIB (Asia/Jakarta).</small>
            </div>
        """, unsafe_allow_html=True)

        with st.form(key="form_presensi", clear_on_submit=True):
            nama = st.text_input("Nama Lengkap Mahasiswa", placeholder=" ")
            nim  = st.text_input("NIM (Nomor Induk Mahasiswa)", placeholder="")

            if semua_kelas_aktif:
                def label_kelas(k):
                    nama_makul = k['makul'].rsplit(' (', 1)[0]
                    nama_dosen_singkat = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                    return f"{nama_makul} — {nama_dosen_singkat} | Pertemuan {k['pertemuan']}"
                opsi_kelas = [label_kelas(k) for k in semua_kelas_aktif]
                pilihan_kelas_label = st.selectbox(
                    "🏫 Pilih Kelas yang Sedang Kamu Ikuti",
                    options=opsi_kelas,
                    help="Pilih sesuai mata kuliah yang kamu ikuti sekarang."
                )
            else:
                pilihan_kelas_label = None
                st.warning("⚠️ Belum ada kelas aktif. Tunggu dosen membuka presensi.")

            materi = st.text_area(
                "Materi Kuliah Hari Ini",
                placeholder="Masukkan topik materi yang dibahas",
                height=120
            )
            submit_button = st.form_submit_button(label="KIRIM KEHADIRAN AKTIF")

        if submit_button:
            if not semua_kelas_aktif or pilihan_kelas_label is None:
                st.error("Presensi gagal! Dosen belum mengaktifkan kelas hari ini.")
            elif nama and nim and materi:
                idx_pilihan   = opsi_kelas.index(pilihan_kelas_label)
                kelas_dipilih = semua_kelas_aktif[idx_pilihan]
                tanggal_hari_ini = waktu_sekarang.strftime("%Y-%m-%d")
                jam_menit_detik  = waktu_sekarang.strftime("%H:%M:%S")
                
                try:
                    sheet = get_sheet()
                    nama_ws = kelas_dipilih["makul"].replace("/", "-").replace(":", "-")[:50]
                    ws = get_or_create_worksheet(sheet, nama_ws)
                    
                    data_absen_eksisting = ws.get_all_records()
                    
                    sudah_absen = False
                    for baris in data_absen_eksisting:
                        if str(baris.get('NIM', '')).strip() == nim.strip() and str(baris.get('Pertemuan Ke', '')) == str(kelas_dipilih["pertemuan"]):
                            sudah_absen = True
                            break
                    
                    if sudah_absen:
                        st.error(f"❌ Ditolak: NIM {nim} sudah mengisi presensi pada Pertemuan Ke-{kelas_dipilih['pertemuan']}!")
                    else:
                        simpan_ke_sheets({
                            "Tanggal":          tanggal_hari_ini,
                            "Jam Isi":          jam_menit_detik,
                            "Mata Kuliah":      kelas_dipilih["makul"],
                            "Semester":         kelas_dipilih["semester"],
                            "Pertemuan Ke":     kelas_dipilih["pertemuan"],
                            "NIM":              nim.strip(),
                            "Nama":             nama.strip(),
                            "Rangkuman Materi": materi.strip()
                        })
                        st.balloons()
                        st.session_state['sudah_presensi'] = True 
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Gagal memproses validasi database: {e}")
            else:
                st.error("Gagal mengirim! Semua kolom wajib diisi.")

# ============================================================
# HALAMAN DOSEN — login + dashboard sidebar
# ============================================================
elif st.session_state['halaman'] == 'dosen':

    if not st.session_state.get('dosen_login', False):
        if st.button("← Kembali", key="back_dos"):
            ke_halaman('landing')

        st.markdown("<br>", unsafe_allow_html=True)
        col_c = st.columns([1,2,1])[1]
        with col_c:
            st.markdown("""
                <div style='background:#FFFFFF;border:1.5px solid #E2E8F0;border-radius:18px;padding:32px 28px;'>
                    <div style='font-family:Sora,sans-serif;font-weight:700;font-size:20px;color:#0F172A;margin-bottom:4px;'>Login Dosen</div>
                    <div style='font-size:13px;color:#64748B;margin-bottom:24px;'>Masukkan password untuk mengakses panel dosen</div>
                </div>
            """, unsafe_allow_html=True)
            with st.form(key="form_login_dosen"):
                password_input = st.text_input("Password", type="password", placeholder="••••••••••")
                tombol_login   = st.form_submit_button("Masuk ke Dashboard →")
            if tombol_login:
                PASSWORD_DOSEN = st.secrets.get("password_dosen", "dosen123")
                if password_input == PASSWORD_DOSEN:
                    st.session_state['dosen_login'] = True
                    st.session_state['menu_dosen'] = 'Kelas'
                    st.rerun()
                else:
                    st.error("Password salah!")

    else:
        # Init menu state
        if 'menu_dosen' not in st.session_state:
            st.session_state['menu_dosen'] = 'Kelas'

        # Pilihan dosen disimpan di session agar persist antar menu
        if 'pilihan_dosen' not in st.session_state:
            st.session_state['pilihan_dosen'] = list(DATA_JADWAL.keys())[0]

        MENU_ITEMS = [
            ("Kelas",   "Atur & Aktifkan"),
            ("Kelola",  "Semua Kelas Aktif"),
            ("QR Code", "Generate QR"),
            ("Rekap",   "Data & Histori"),
        ]

        # ── CSS SIDEBAR ──────────────────────────────────────────
        st.markdown("""
            <style>
            .sidebar-wrap {
                background: #0F172A; border-radius: 16px;
                padding: 20px 14px; min-height: 480px;
            }
            .sidebar-profile {
                text-align: center; padding-bottom: 18px;
                border-bottom: 1px solid #1E293B; margin-bottom: 16px;
            }
            .sidebar-avatar {
                width: 44px; height: 44px; background: #38BDF8;
                border-radius: 50%; display: flex; align-items: center;
                justify-content: center; margin: 0 auto 8px;
                font-family: 'Sora',sans-serif; font-weight: 800;
                font-size: 16px; color: #0F172A;
            }
            .sidebar-name { font-size: 12px; color: #F1F5F9; font-weight: 600; }
            .sidebar-role { font-size: 11px; color: #475569; margin-top: 2px; }
            .nav-item {
                padding: 10px 14px; border-radius: 10px; margin-bottom: 4px;
                cursor: pointer; display: flex; align-items: center; gap: 10px;
            }
            .nav-item-label { font-size: 13px; font-weight: 600; color: #94A3B8; }
            .nav-item-sub { font-size: 10px; color: #475569; }
            .nav-item.active { background: #1E293B; }
            .nav-item.active .nav-item-label { color: #38BDF8; }
            .dash-content {
                background: #FFFFFF; border: 1.5px solid #E2E8F0;
                border-radius: 16px; padding: 28px 24px; min-height: 480px;
            }
            .dash-title {
                font-family: 'Sora',sans-serif !important;
                font-size: 20px; font-weight: 700; color: #0F172A;
                margin-bottom: 4px;
            }
            .dash-sub { font-size: 13px; color: #64748B; margin-bottom: 24px; }
            </style>
        """, unsafe_allow_html=True)

        col_side, col_main = st.columns([1, 3])

        # ── SIDEBAR ───────────────────────────────────────────────
        with col_side:
            inisial = st.session_state['pilihan_dosen'][:2].upper()
            st.markdown(f"""
                <div class="sidebar-wrap">
                    <div class="sidebar-profile">
                        <div class="sidebar-avatar">{inisial}</div>
                        <div class="sidebar-name">Panel Dosen</div>
                        <div class="sidebar-role">Bisnis Digital</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:-8px'></div>", unsafe_allow_html=True)

            for label, sub in MENU_ITEMS:
                is_active = st.session_state['menu_dosen'] == label
                icon_map = {"Kelas": "◈", "Kelola": "◉", "QR Code": "◎", "Rekap": "≡"}
                bg = "background:#1E293B;border-radius:10px;" if is_active else ""
                color = "#38BDF8" if is_active else "#94A3B8"
                subcolor = "#64748B" if is_active else "#334155"
                st.markdown(f"""
                    <div style='padding:10px 14px;margin-bottom:3px;{bg}'>
                        <span style='font-size:13px;font-weight:600;color:{color};'>{icon_map[label]} {label}</span><br>
                        <span style='font-size:10px;color:{subcolor};'>{sub}</span>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(label, key=f"nav_{label}", use_container_width=True):
                    st.session_state['menu_dosen'] = label
                    st.rerun()

            st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
            if st.button("Logout", key="logout_btn", use_container_width=True):
                st.session_state['dosen_login'] = False
                ke_halaman('landing')

        # ── KONTEN UTAMA ──────────────────────────────────────────
        with col_main:
            menu = st.session_state['menu_dosen']

            # Pilih dosen (selalu tersedia, disimpan di session)
            pilihan_dosen = st.selectbox(
                "Dosen",
                options=list(DATA_JADWAL.keys()),
                index=list(DATA_JADWAL.keys()).index(st.session_state['pilihan_dosen']),
                key="select_dosen_global"
            )
            st.session_state['pilihan_dosen'] = pilihan_dosen
            dosen_key     = pilihan_dosen
            status_dosen  = baca_status_kelas_dosen(dosen_key)

            # ── MENU: KELAS ───────────────────────────────────────
            if menu == 'Kelas':
                st.markdown("<div class='dash-title'>Atur Kelas</div>", unsafe_allow_html=True)
                st.markdown("<div class='dash-sub'>Pilih mata kuliah, set semester & pertemuan, lalu aktifkan.</div>", unsafe_allow_html=True)

                if status_dosen["aktif"]:
                    nm_aktif = status_dosen['makul'].rsplit(' (', 1)[0]
                    st.markdown(f"""
                        <div style='background:#F0FDF4;border:1.5px solid #BBF7D0;border-left:4px solid #16A34A;
                                    border-radius:12px;padding:12px 16px;margin-bottom:16px;'>
                            <span style='font-size:13px;font-weight:700;color:#166534;'>Kelas Aktif</span><br>
                            <span style='font-size:14px;color:#14532D;'>{nm_aktif}</span>
                            <span style='font-size:12px;color:#4ADE80;'> · Sem {status_dosen['semester']} · Pertemuan {status_dosen['pertemuan']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("<div style='background:#FFF7ED;border:1.5px solid #FED7AA;border-left:4px solid #F97316;border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:#9A3412;font-weight:500;'>Belum ada kelas aktif untuk dosen ini.</div>", unsafe_allow_html=True)

                daftar_makul  = DATA_JADWAL[pilihan_dosen]
                pilihan_makul = st.selectbox("Mata Kuliah", options=daftar_makul)
                input_makul_gabungan = f"{pilihan_makul} ({pilihan_dosen})"

                col1, col2 = st.columns(2)
                with col1:
                    input_semester = st.text_input("Semester", value=status_dosen["semester"] if status_dosen["semester"] != "-" else "", placeholder="Contoh: 4")
                with col2:
                    input_pertemuan = st.text_input("Pertemuan Ke-", value=status_dosen["pertemuan"] if status_dosen["pertemuan"] != "-" else "", placeholder="Contoh: 3")

                col_buka, col_tutup = st.columns(2)
                with col_buka:
                    if st.button("Aktifkan Kelas", use_container_width=True, key="btn_aktifkan"):
                        if input_semester and input_pertemuan:
                            try:
                                tulis_status_kelas(input_makul_gabungan, input_semester, input_pertemuan, dosen_key=dosen_key, aktif=True)
                                st.success("Kelas berhasil diaktifkan!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal: {e}")
                        else:
                            st.error("Isi semester dan pertemuan!")
                with col_tutup:
                    if st.button("Tutup Kelas Saya", use_container_width=True, key="btn_tutup"):
                        try:
                            hasil = tutup_kelas(dosen_key=dosen_key)
                            st.success("Kelas ditutup.") if hasil else st.warning("Tidak ada kelas aktif.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")

            # ── MENU: KELOLA ──────────────────────────────────────
            elif menu == 'Kelola':
                st.markdown("<div class='dash-title'>Kelola Kelas Aktif</div>", unsafe_allow_html=True)
                st.markdown("<div class='dash-sub'>Semua kelas yang sedang dibuka saat ini. Tutup jika sesi selesai.</div>", unsafe_allow_html=True)

                kelas_aktif_sekarang = baca_semua_kelas_aktif()
                if kelas_aktif_sekarang:
                    for idx_k, k in enumerate(kelas_aktif_sekarang):
                        nm = k['makul'].rsplit(' (', 1)[0]
                        nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                        col_info, col_btn = st.columns([5, 2])
                        with col_info:
                            st.markdown(
                                f"<div class='kelas-badge'>{nm}"
                                f"<br><small>{nd} · Sem {k['semester']} · Pertemuan {k['pertemuan']}</small></div>",
                                unsafe_allow_html=True
                            )
                        with col_btn:
                            st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
                            if st.button("Tutup", key=f"tutup_k_{idx_k}", use_container_width=True):
                                try:
                                    tutup_kelas_by_makul(k['makul'])
                                    st.success(f"{nm} ditutup.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Gagal: {e}")
                else:
                    st.markdown("<div style='text-align:center;padding:48px 0;color:#94A3B8;font-size:14px;'>Tidak ada kelas aktif saat ini.</div>", unsafe_allow_html=True)

            # ── MENU: QR CODE ─────────────────────────────────────
            elif menu == 'QR Code':
                st.markdown("<div class='dash-title'>Generate QR Code</div>", unsafe_allow_html=True)
                st.markdown("<div class='dash-sub'>Buat QR untuk mahasiswa scan langsung ke form presensi.</div>", unsafe_allow_html=True)

                daftar_makul_qr  = DATA_JADWAL[pilihan_dosen]
                pilihan_makul_qr = st.selectbox("Mata Kuliah", options=daftar_makul_qr, key="qr_makul")
                input_pertemuan_qr = st.text_input("Pertemuan Ke-", placeholder="Contoh: 3", key="qr_pertemuan")
                url_aplikasi = st.text_input("URL Aplikasi", placeholder="https://nama-app.streamlit.app")

                if st.button("Generate QR Code", use_container_width=True):
                    if url_aplikasi:
                        qr_image = generate_qr(url_aplikasi)
                        col_img, col_dl = st.columns([1,1])
                        with col_img:
                            st.image(qr_image, width=220)
                        with col_dl:
                            st.markdown(f"<br><b>{pilihan_makul_qr}</b><br><small>Pertemuan {input_pertemuan_qr}</small>", unsafe_allow_html=True)
                            st.download_button(
                                label="Download QR",
                                data=qr_image,
                                file_name=f"qr_{pilihan_makul_qr}_P{input_pertemuan_qr}.png",
                                mime="image/png",
                                use_container_width=True
                            )
                    else:
                        st.error("Masukkan URL aplikasi!")

            # ── MENU: REKAP ───────────────────────────────────────
            elif menu == 'Rekap':
                st.markdown("<div class='dash-title'>Rekapitulasi & Histori</div>", unsafe_allow_html=True)
                st.markdown("<div class='dash-sub'>Lihat data kehadiran, filter per pertemuan, dan download Excel.</div>", unsafe_allow_html=True)

                makul_arsip_opsi = DATA_JADWAL[pilihan_dosen]
                pilih_makul_arsip = st.selectbox("Mata Kuliah", options=makul_arsip_opsi, key="rekap_makul")
                input_makul_arsip_gabungan = f"{pilih_makul_arsip} ({pilihan_dosen})"

                # Rekap semester
                st.markdown("<div class='sec-label'>Master Rekap Semester</div>", unsafe_allow_html=True)
                if st.button("Ambil Data Semua Pertemuan (1–16)", use_container_width=True):
                    try:
                        sheet   = get_sheet()
                        nama_ws = input_makul_arsip_gabungan.replace("/", "-").replace(":", "-")[:50]
                        ws      = sheet.worksheet(nama_ws)
                        data    = ws.get_all_records()
                        if data:
                            df_all = pd.DataFrame(data)
                            if 'Pertemuan Ke' in df_all.columns and 'NIM' in df_all.columns:
                                df_all['_p'] = pd.to_numeric(df_all['Pertemuan Ke'], errors='coerce')
                                df_all = df_all.sort_values(by=['_p', 'NIM']).drop(columns=['_p'])
                            st.success(f"Total {len(df_all)} baris data kehadiran.")
                            output_all = BytesIO()
                            df_all.to_excel(output_all, index=False, engine='openpyxl')
                            output_all.seek(0)
                            st.download_button(
                                label="Download Excel Rekap Semester",
                                data=output_all,
                                file_name=f"REKAP_{pilih_makul_arsip}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        else:
                            st.info("Belum ada data untuk mata kuliah ini.")
                    except gspread.exceptions.WorksheetNotFound:
                        st.info("Belum ada data presensi.")
                    except Exception as e:
                        st.error(f"Gagal: {e}")

                # Filter per pertemuan
                st.markdown("<div class='sec-label'>Filter Per Pertemuan</div>", unsafe_allow_html=True)
                col_p, col_btn2 = st.columns([2,1])
                with col_p:
                    pilih_pertemuan_arsip = st.selectbox("Pertemuan", options=[str(i) for i in range(1,17)], key="rekap_pertemuan")
                with col_btn2:
                    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
                    btn_tampil = st.button("Tampilkan", use_container_width=True)

                if btn_tampil:
                    try:
                        sheet   = get_sheet()
                        nama_ws = input_makul_arsip_gabungan.replace("/", "-").replace(":", "-")[:50]
                        ws      = sheet.worksheet(nama_ws)
                        data    = ws.get_all_records()
                        if data:
                            df_all      = pd.DataFrame(data)
                            df_filtered = df_all[df_all['Pertemuan Ke'].astype(str) == str(pilih_pertemuan_arsip)]
                            if not df_filtered.empty:
                                if "Mata Kuliah" in df_filtered.columns:
                                    df_filtered = df_filtered.drop(columns=["Mata Kuliah"])
                                st.success(f"{len(df_filtered)} mahasiswa hadir pada Pertemuan {pilih_pertemuan_arsip}")
                                st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)
                                out2 = BytesIO()
                                df_filtered.to_excel(out2, index=False, engine='openpyxl')
                                out2.seek(0)
                                st.download_button(
                                    label="Download Excel Pertemuan Ini",
                                    data=out2,
                                    file_name=f"presensi_{pilih_makul_arsip}_P{pilih_pertemuan_arsip}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            else:
                                st.warning(f"Tidak ada data untuk Pertemuan {pilih_pertemuan_arsip}.")
                        else:
                            st.info("Belum ada data.")
                    except gspread.exceptions.WorksheetNotFound:
                        st.info("Belum ada data presensi untuk kelas ini.")
                    except Exception as e:
                        st.error(f"Error: {e}")

                # Histori log
                st.markdown("<div class='sec-label'>Histori Log Aktivitas</div>", unsafe_allow_html=True)
                try:
                    sheet   = get_sheet()
                    nama_ws = input_makul_arsip_gabungan.replace("/", "-").replace(":", "-")[:50]
                    ws      = sheet.worksheet(nama_ws)
                    data_histori = ws.get_all_records()
                    if data_histori:
                        df_h = pd.DataFrame(data_histori)
                        if 'Pertemuan Ke' in df_h.columns:
                            summary = df_h.groupby('Pertemuan Ke').agg(
                                total_mhs=('NIM','count'), tgl_awal=('Tanggal','min'), tgl_akhir=('Tanggal','max')
                            ).reset_index()
                            summary['_p'] = pd.to_numeric(summary['Pertemuan Ke'], errors='coerce')
                            summary = summary.sort_values('_p').drop(columns=['_p'])
                            for _, rh in summary.iterrows():
                                tgl = rh['tgl_awal'] if rh['tgl_awal'] == rh['tgl_akhir'] else f"{rh['tgl_awal']} s/d {rh['tgl_akhir']}"
                                st.markdown(f"""
                                    <div class="histori-container">
                                        <b>Pertemuan Ke-{rh['Pertemuan Ke']}</b><br>
                                        <span style='font-size:12px;color:#475569;'>
                                            {rh['total_mhs']} mahasiswa hadir &nbsp;·&nbsp; {tgl}
                                        </span>
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.caption("Struktur kolom histori belum siap.")
                    else:
                        st.info("Belum ada histori pertemuan.")
                except gspread.exceptions.WorksheetNotFound:
                    st.info("Belum ada riwayat kelas (sheet belum terbentuk).")
                except Exception as e:
                    st.caption(f"Tidak dapat memuat histori: {e}")