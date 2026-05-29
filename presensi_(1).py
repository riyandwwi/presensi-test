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
# CSS CUSTOM
# ============================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #1E293B;
    }
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Header Banner */
    .header-banner {
        background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%);
        padding: 25px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 20px rgba(79, 70, 229, 0.15);
    }
    .header-banner h1 { color: white !important; font-weight: 800; font-size: 28px; margin-bottom: 5px; }
    .header-banner p  { color: #E0E7FF !important; font-size: 15px; opacity: 0.9; margin: 0;}
    
    /* Form Cards */
    div[data-testid="stForm"] {
        background: rgba(255,255,255,0.95);
        border: 1px solid #E2E8F0;
        border-radius: 20px !important;
        padding: 35px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.03) !important;
    }
    
    /* Inputs */
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        background-color: #F8FAFC !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #4F46E5 !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 0 0 4px rgba(79,70,229,0.1) !important;
    }
    
    /* Primary Button */
    button[kind="formSubmit"] {
        background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        width: 100% !important;
        box-shadow: 0 4px 15px rgba(79,70,229,0.3) !important;
        transition: transform 0.2s ease;
    }
    button[kind="formSubmit"]:hover {
        transform: translateY(-2px);
    }
    
    /* Utilities */
    .clock-container {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin-bottom: 20px;
        color: #B45309;
        font-weight: 600;
        font-size: 14px;
    }
    .kelas-badge {
        background: white;
        border-left: 4px solid #4F46E5;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
        color: #334155;
    }
    .histori-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #10B981;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    
    /* Tabs Styling */
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 15px !important;
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

def ke_halaman(nama):
    st.session_state['halaman'] = nama
    st.rerun()

# ============================================================
# HEADER APP
# ============================================================
st.markdown("""
    <div class="header-banner">
        <h1>PRESENSI BISNIS DIGITAL</h1>
        <p>Beta ver 0.932</p>
    </div>
""", unsafe_allow_html=True)

# ============================================================
# HALAMAN LANDING
# ============================================================
if st.session_state['halaman'] == 'landing':

    semua_kelas_aktif = baca_semua_kelas_aktif()

    if semua_kelas_aktif:
        st.success(f"📍 **{len(semua_kelas_aktif)} Kelas Terbuka Saat Ini:**")
        for k in semua_kelas_aktif:
            nama_makul = k['makul'].rsplit(' (', 1)[0]
            nama_dosen = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
            st.markdown(
                f"<div class='kelas-badge'>📚 <b>{nama_makul}</b> <br> <span style='color:#64748B; font-size:13px;'>👨‍🏫 {nama_dosen} &nbsp;|&nbsp; Pertemuan {k['pertemuan']}</span></div>",
                unsafe_allow_html=True
            )
    else:
        st.info("🕒 Belum ada kelas yang dibuka oleh dosen saat ini.")

    st.markdown("<br><h3 style='text-align:center; color:#1E293B; font-weight:700;'>Pilih Akses Anda</h3><br>", unsafe_allow_html=True)

    col_mhs, col_dos = st.columns(2)
    with col_mhs:
        st.markdown("""
            <div style='background:white; border-radius:16px; padding:30px 20px;
                        text-align:center; border: 1.5px solid #E2E8F0; transition: 0.3s;'>
                <div style='font-size:45px;'>🧑‍🎓</div>
                <div style='font-weight:700; font-size:18px; margin-top:10px; color:#1E293B;'>Mahasiswa</div>
                <div style='font-size:13px; color:#64748B; margin-top:6px;'>Isi daftar hadir perkuliahan</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
        if st.button("Masuk Mahasiswa", use_container_width=True, key="btn_mhs"):
            ke_halaman('mahasiswa')
    with col_dos:
        st.markdown("""
            <div style='background:white; border-radius:16px; padding:30px 20px;
                        text-align:center; border: 1.5px solid #E2E8F0;'>
                <div style='font-size:45px;'>👨‍🏫</div>
                <div style='font-weight:700; font-size:18px; margin-top:10px; color:#1E293B;'>Dosen</div>
                <div style='font-size:13px; color:#64748B; margin-top:6px;'>Kelola kelas & rekap data</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
        if st.button("Masuk Dosen", use_container_width=True, key="btn_dos"):
            ke_halaman('dosen')

# ============================================================
# HALAMAN MAHASISWA — Form Absen Manual (Nama & NIM)
# ============================================================
elif st.session_state['halaman'] == 'mahasiswa':

    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← Kembali", key="back_mhs"):
            ke_halaman('landing')

    if st.session_state['sudah_presensi']:
        st.success("✅ Anda sudah berhasil melakukan presensi pada sesi ini.")
        st.info("💡 Sistem telah mengunci form untuk perangkat ini guna menghindari duplikasi pengisian.")
    else:
        semua_kelas_aktif = baca_semua_kelas_aktif()

        st.markdown(f"""
            <div class="clock-container">
                🕒 Tanggal: <b>{waktu_sekarang.strftime('%d-%m-%Y')}</b> &nbsp;|&nbsp; Jam: <b>{waktu_sekarang.strftime('%H:%M:%S')} WIB</b>
                <br><small style="color: #D97706; font-weight: normal;">Catatan: Waktu server tercatat otomatis pada database.</small>
            </div>
        """, unsafe_allow_html=True)

        with st.form(key="form_presensi", clear_on_submit=True):
            st.markdown("<h4 style='text-align:center; color:#1E293B; margin-bottom:20px;'>📝 Form Kehadiran</h4>", unsafe_allow_html=True)
            
            # Layout input 2 kolom agar lebih rapi di layar lebar
            col_nama, col_nim = st.columns(2)
            with col_nama:
                nama = st.text_input("Nama Lengkap", placeholder="")
            with col_nim:
                nim  = st.text_input("NIM", placeholder="")

            if semua_kelas_aktif:
                def label_kelas(k):
                    nama_makul = k['makul'].rsplit(' (', 1)[0]
                    nama_dosen_singkat = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                    return f"{nama_makul} — {nama_dosen_singkat} | Pertemuan {k['pertemuan']}"
                opsi_kelas = [label_kelas(k) for k in semua_kelas_aktif]
                pilihan_kelas_label = st.selectbox(
                    "🏫 Pilih Sesi Kelas:",
                    options=opsi_kelas
                )
            else:
                pilihan_kelas_label = None
                st.warning("⚠️ Belum ada kelas aktif. Silakan tunggu instruksi dosen Anda.")

            materi = st.text_area(
                "Rangkuman Materi Hari Ini",
                placeholder="Tulis ringkasan singkat materi yang dibahas...",
                height=100
            )
            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.form_submit_button(label="KIRIM BUKTI HADIR")

        if submit_button:
            if not semua_kelas_aktif or pilihan_kelas_label is None:
                st.error("Gagal! Belum ada kelas kuliah yang dibuka saat ini.")
            elif not nama.strip() or not nim.strip() or not materi.strip():
                st.error("Peringatan: Seluruh form (Nama, NIM, Rangkuman) wajib diisi!")
            else:
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
                        st.error(f"❌ Ditolak: NIM {nim} sudah terdaftar hadir pada Pertemuan Ke-{kelas_dipilih['pertemuan']}!")
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
                    st.error(f"Gagal menghubungi server database: {e}")

# ============================================================
# HALAMAN DOSEN — PANEL DENGAN TABS (UI/UX BARU)
# ============================================================
elif st.session_state['halaman'] == 'dosen':

    if not st.session_state.get('dosen_login', False):
        col_back, _ = st.columns([1, 4])
        with col_back:
            if st.button("← Kembali", key="back_dos"):
                ke_halaman('landing')

        st.markdown("<h3 style='color:#4F46E5; text-align:center;'>Autentikasi Dosen</h3>", unsafe_allow_html=True)
        with st.form(key="form_login_dosen"):
            password_input = st.text_input("Kode Akses Panel", type="password", placeholder="Masukkan password...")
            st.markdown("<br>", unsafe_allow_html=True)
            tombol_login   = st.form_submit_button("Masuk Panel Dashboard")

        if tombol_login:
            PASSWORD_DOSEN = st.secrets.get("password_dosen", "dosen123")
            if password_input == PASSWORD_DOSEN:
                st.session_state['dosen_login'] = True
                st.rerun()
            else:
                st.error("Kode akses tidak valid!")

    else:
        # Header Dashboard Dosen
        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.markdown(" Dashboard Dosen")
        with col_logout:
            if st.button("Keluar", use_container_width=True):
                st.session_state['dosen_login'] = False
                ke_halaman('landing')
                
        # Membaca data metrik
        kelas_aktif_sekarang = baca_semua_kelas_aktif()
        
        # PENGGUNAAN TABS UNTUK MERAPIKAN TAMPILAN
        tab1, tab2, tab3 = st.tabs(["🚀 Buka Kelas & QR", "📋 Monitor Kelas Aktif", "📂 Arsip & Histori"])
        
        # ----------------------------------------------------
        # TAB 1: BUKA KELAS & QR CODE
        # ----------------------------------------------------
        with tab1:
            st.markdown("#### Aktivasi Perkuliahan Baru")
            st.caption("Pilih identitas Anda dan mata kuliah yang akan diajarkan saat ini.")
            
            pilihan_dosen = st.selectbox("Nama Dosen Pengampu", options=list(DATA_JADWAL.keys()))
            daftar_makul  = DATA_JADWAL[pilihan_dosen]
            pilihan_makul = st.selectbox("Nama Mata Kuliah", options=daftar_makul)

            input_makul_gabungan = f"{pilihan_makul} ({pilihan_dosen})"
            dosen_key            = pilihan_dosen

            status_dosen = baca_status_kelas_dosen(dosen_key)
            
            # Visualisasi Status Dosen Pribadi
            if status_dosen["aktif"]:
                nama_makul_aktif = status_dosen['makul'].rsplit(' (', 1)[0]
                st.success(f"🟢 Anda Sedang Membuka Kelas: **{nama_makul_aktif}** (Smt {status_dosen['semester']} - Pertemuan {status_dosen['pertemuan']})")
            else:
                st.info("⚪ Status Anda saat ini: **Standby** (Belum ada kelas aktif).")

            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    input_semester = st.text_input("Semester:", value=status_dosen["semester"] if status_dosen["semester"] != "-" else "")
                with col2:
                    input_pertemuan = st.text_input("Pertemuan Ke-:", value=status_dosen["pertemuan"] if status_dosen["pertemuan"] != "-" else "")

                col_buka, col_tutup = st.columns(2)
                with col_buka:
                    if st.button("✅ Aktifkan Akses Kelas", use_container_width=True):
                        if input_semester and input_pertemuan:
                            try:
                                tulis_status_kelas(input_makul_gabungan, input_semester, input_pertemuan, dosen_key=dosen_key, aktif=True)
                                st.toast("Kelas Anda berhasil diaktifkan!", icon="🎉")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal: {e}")
                        else:
                            st.warning("Lengkapi Semester dan Pertemuan.")
                with col_tutup:
                    if st.button("⛔ Tutup Sesi Saya", use_container_width=True):
                        if tutup_kelas(dosen_key=dosen_key):
                            st.toast("Sesi kelas Anda telah ditutup.", icon="🔒")
                            st.rerun()

            st.markdown("---")
            st.markdown("#### Generator QR Code")
            url_aplikasi = st.text_input("Tautan URL Aplikasi (Streamlit):", placeholder="https://app-anda.streamlit.app")
            if st.button("Tampilkan QR Code", type="primary"):
                if url_aplikasi:
                    qr_image = generate_qr(url_aplikasi)
                    st.image(qr_image, caption=f"Scan QR — {pilihan_makul} (P-{input_pertemuan})", width=250)
                    st.download_button(label="⬇️ Unduh Gambar QR", data=qr_image, file_name=f"QR_{pilihan_makul}.png", mime="image/png")
                else:
                    st.warning("Mohon masukkan tautan URL terlebih dahulu.")

        # ----------------------------------------------------
        # TAB 2: MONITOR KELAS AKTIF (GLOBAL)
        # ----------------------------------------------------
        with tab2:
            col_metric, col_reload = st.columns([4, 1])
            with col_metric:
                st.metric(label="Total Kelas Sedang Berjalan (Global)", value=f"{len(kelas_aktif_sekarang)} Kelas")
            with col_reload:
                st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
                if st.button("🔄 Reload", use_container_width=True, key="reload_monitor"):
                    st.rerun()

            st.markdown("---")

            if kelas_aktif_sekarang:
                for idx_k, k in enumerate(kelas_aktif_sekarang):
                    nm = k['makul'].rsplit(' (', 1)[0]
                    nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]

                    with st.container(border=True):
                        col_info, col_btn = st.columns([4, 1])
                        with col_info:
                            st.markdown(f"📚 **{nm}** <br><span style='color:#64748B; font-size:14px;'>👨‍🏫 {nd} | Smt {k['semester']} | Pertemuan {k['pertemuan']}</span>", unsafe_allow_html=True)
                        with col_btn:
                            if st.button("Tutup Paksa", key=f"tutup_kelas_{idx_k}", use_container_width=True):
                                tutup_kelas_by_makul(k['makul'])
                                st.toast(f"Kelas {nm} berhasil ditutup.", icon="🧹")
                                st.rerun()

                        # Expander lihat mahasiswa yang sudah mengisi
                        with st.expander(f"Lihat mahasiswa yang sudah hadir"):
                            try:
                                sheet_mon = get_sheet()
                                nama_ws_mon = k['makul'].replace("/", "-").replace(":", "-")[:50]
                                ws_mon = sheet_mon.worksheet(nama_ws_mon)
                                data_mon = ws_mon.get_all_records()

                                if data_mon:
                                    df_mon = pd.DataFrame(data_mon)
                                    # Filter hanya pertemuan yang sedang aktif
                                    df_mon_filtered = df_mon[
                                        df_mon['Pertemuan Ke'].astype(str) == str(k['pertemuan'])
                                    ]

                                    if not df_mon_filtered.empty:
                                        df_mon_filtered = df_mon_filtered.reset_index(drop=True)
                                        st.success(f"**{len(df_mon_filtered)} mahasiswa** sudah mengisi presensi Pertemuan {k['pertemuan']}")

                                        for i, row in df_mon_filtered.iterrows():
                                            st.markdown(
                                                f"**{i+1}. {row['Nama']}** &nbsp;<span style='color:#64748B;font-size:13px;'>({row['NIM']})</span>"
                                                f"<br><span style='font-size:12px;color:#94A3B8;'>🕒 {row['Jam Isi']} WIB &nbsp;·&nbsp; {row['Tanggal']}</span>",
                                                unsafe_allow_html=True
                                            )
                                            if i < len(df_mon_filtered) - 1:
                                                st.markdown("<hr style='margin:6px 0;border-color:#F1F5F9;'>", unsafe_allow_html=True)
                                    else:
                                        st.info(f"Belum ada mahasiswa yang mengisi presensi Pertemuan {k['pertemuan']}.")
                                else:
                                    st.info("Belum ada data presensi sama sekali untuk kelas ini.")

                            except gspread.exceptions.WorksheetNotFound:
                                st.info("Belum ada data presensi untuk kelas ini.")
                            except Exception as e:
                                st.error(f"Gagal memuat data: {e}")
            else:
                st.caption("Tidak ada aktivitas kelas di universitas saat ini.")

        # ----------------------------------------------------
        # TAB 3: ARSIP & HISTORI
        # ----------------------------------------------------
        with tab3:
            st.markdown("#### Pusat Data Kehadiran")
            makul_arsip_opsi = DATA_JADWAL[pilihan_dosen]
            pilih_makul_arsip = st.selectbox("Pilih Mata Kuliah untuk Dilihat:", options=makul_arsip_opsi)
            input_makul_arsip_gabungan = f"{pilih_makul_arsip} ({pilihan_dosen})"

            # Panel Download Rekap Master (1-16)
            with st.expander("📥 Unduh Master Rekap Semester (P1-P16)", expanded=False):
                st.caption("Fungsi ini akan menggabungkan seluruh data kehadiran dari pertemuan pertama hingga terakhir ke dalam satu file Excel.")
                if st.button("Generate Rekap Global", use_container_width=True):
                    try:
                        sheet   = get_sheet()
                        nama_ws = input_makul_arsip_gabungan.replace("/", "-").replace(":", "-")[:50]
                        ws      = sheet.worksheet(nama_ws)
                        data    = ws.get_all_records()
                        
                        if data:
                            df_all = pd.DataFrame(data)
                            if 'Pertemuan Ke' in df_all.columns and 'NIM' in df_all.columns:
                                df_all['Pertemuan Ke_Int'] = pd.to_numeric(df_all['Pertemuan Ke'], errors='coerce')
                                df_all = df_all.sort_values(by=['Pertemuan Ke_Int', 'NIM']).drop(columns=['Pertemuan Ke_Int'])
                            
                            output_all = BytesIO()
                            df_all.to_excel(output_all, index=False, engine='openpyxl')
                            output_all.seek(0)
                            
                            st.success(f"Selesai! Ditemukan {len(df_all)} total rekaman data.")
                            st.download_button(
                                label="⬇️ Download Excel Rekap",
                                data=output_all,
                                file_name=f"MASTER_REKAP_{pilih_makul_arsip}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        else:
                            st.info("Database presensi masih kosong.")
                    except gspread.exceptions.WorksheetNotFound:
                        st.info("Belum ada sheet database yang terbentuk untuk makul ini.")
            
            st.markdown("---")
            
            # Panel Filter per Sesi
            col_filter, col_aksi = st.columns([2, 1])
            with col_filter:
                pilih_pertemuan_arsip = st.selectbox("Lihat Detail Pertemuan Ke-:", options=[str(i) for i in range(1, 17)])
            with col_aksi:
                st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
                btn_tampil = st.button("Tampilkan Data", use_container_width=True)

            if btn_tampil:
                try:
                    sheet   = get_sheet()
                    nama_ws = input_makul_arsip_gabungan.replace("/", "-").replace(":", "-")[:50]
                    ws      = sheet.worksheet(nama_ws)
                    data    = ws.get_all_records()
                    
                    if data:
                        df_all = pd.DataFrame(data)
                        df_filtered = df_all[df_all['Pertemuan Ke'].astype(str) == str(pilih_pertemuan_arsip)]
                        
                        if not df_filtered.empty:
                            if "Mata Kuliah" in df_filtered.columns:
                                df_filtered = df_filtered.drop(columns=["Mata Kuliah"])
                            
                            st.toast(f"Memuat {len(df_filtered)} data pertemuan {pilih_pertemuan_arsip}...", icon="✅")
                            
                            st.dataframe(df_filtered, use_container_width=True)
                            
                            output = BytesIO()
                            df_filtered.to_excel(output, index=False, engine='openpyxl')
                            output.seek(0)
                            
                            st.download_button(label="⬇️ Unduh Excel Sesi Ini", data=output, file_name=f"Sesi_{pilih_pertemuan_arsip}_{pilih_makul_arsip}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                        else:
                            st.warning("Belum ada mahasiswa yang hadir di sesi ini.")
                    else:
                        st.info("Belum ada data presensi terekam.")
                except gspread.exceptions.WorksheetNotFound:
                    st.info("Sheet database belum tersedia.")

            # Histori Log
            st.markdown("---")
            st.markdown("##### 📜 Histori Log Kelas")
            try:
                sheet   = get_sheet()
                nama_ws = input_makul_arsip_gabungan.replace("/", "-").replace(":", "-")[:50]
                ws      = sheet.worksheet(nama_ws)
                data_histori = ws.get_all_records()
                
                if data_histori:
                    df_histori = pd.DataFrame(data_histori)
                    if 'Pertemuan Ke' in df_histori.columns:
                        summary_histori = df_histori.groupby('Pertemuan Ke').agg(
                            total_mhs=('NIM', 'count'),
                            tgl_awal=('Tanggal', 'min')
                        ).reset_index()
                        
                        summary_histori['Pertemuan_Int'] = pd.to_numeric(summary_histori['Pertemuan Ke'], errors='coerce')
                        summary_histori = summary_histori.sort_values(by='Pertemuan_Int', ascending=False).drop(columns=['Pertemuan_Int']) # Diurutkan dari pertemuan terbaru
                        
                        for _, row_h in summary_histori.iterrows():
                            st.markdown(f"""
                                <div class="histori-container">
                                    <div style="display:flex; justify-content:space-between;">
                                        <span>📅 <b>Pertemuan Ke-{row_h['Pertemuan Ke']}</b></span>
                                        <span style="color:#10B981; font-weight:600;">{row_h['total_mhs']} Hadir</span>
                                    </div>
                                    <span style='font-size:12px; color:#64748B;'>Dibuat: {row_h['tgl_awal']}</span>
                                </div>
                            """, unsafe_allow_html=True)
                else:
                    st.caption("Belum ada riwayat pelaksanaan kelas.")
            except:
                st.caption("Histori belum tersedia.")