import streamlit as st
import pandas as pd
from datetime import datetime
import qrcode
from io import BytesIO
import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# INISIALISASI SESSION STATE
# ============================================================
if 'dosen_login' not in st.session_state:
    st.session_state['dosen_login'] = False

# State untuk membatasi mahasiswa absen berkali-kali
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
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #2D3748;
    }
    .stApp {
        background: linear-gradient(135deg, #F0F4F8 0%, #E2E8F0 100%);
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .header-banner {
        background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(79, 70, 229, 0.15);
    }
    .header-banner h1 { color: white !important; font-weight: 800; font-size: 32px; margin-bottom: 5px; }
    .header-banner p  { color: #E0E7FF !important; font-size: 16px; opacity: 0.9; }
    div[data-testid="stForm"] {
        background: rgba(255,255,255,0.85);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.5);
        border-radius: 24px !important;
        padding: 40px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.04) !important;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        background-color: #FFFFFF !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 0 4px rgba(79,70,229,0.12) !important;
    }
    button[kind="formSubmit"] {
        background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 14px 28px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        width: 100% !important;
        box-shadow: 0 8px 20px rgba(79,70,229,0.25) !important;
    }
    .clock-container {
        background-color: #FFFbeb;
        border: 1px solid #FEF3C7;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        margin-bottom: 20px;
        color: #B45309;
        font-weight: 600;
        font-size: 14px;
    }
    .kelas-badge {
        background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
        border: 1px solid #C7D2FE;
        border-radius: 12px;
        padding: 10px 16px;
        margin-bottom: 8px;
        font-size: 14px;
        color: #3730A3;
        font-weight: 600;
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
# Header: makul | semester | pertemuan | aktif | dosen_key
# ============================================================
STATUS_SHEET = "STATUS_KELAS"

def baca_semua_kelas_aktif():
    """Baca semua kelas yang sedang aktif dari Google Sheets."""
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
    """Baca status kelas milik dosen tertentu."""
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
    """Simpan/update status kelas dosen (upsert by dosen_key)."""
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
    """Nonaktifkan kelas milik dosen tertentu saja."""
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
    """Nonaktifkan kelas berdasarkan nama makul (untuk panel kelola semua kelas)."""
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

waktu_sekarang = datetime.now()

# ============================================================
# HEADER (tampil di semua halaman)
# ============================================================
st.markdown("""
    <div class="header-banner">
        <h1>PRESENSI AKADEMIK BISNIS DIGITAL</h1>
        <p>Ver Beta 0.71</p>
    </div>
""", unsafe_allow_html=True)

# ============================================================
# HALAMAN LANDING — pilih peran
# ============================================================
if st.session_state['halaman'] == 'landing':

    semua_kelas_aktif = baca_semua_kelas_aktif()

    if semua_kelas_aktif:
        st.success(f"📍 **{len(semua_kelas_aktif)} Kelas Aktif Saat Ini:**")
        for k in semua_kelas_aktif:
            nama_makul = k['makul'].rsplit(' (', 1)[0]
            nama_dosen = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
            st.markdown(
                f"<div class='kelas-badge'>📚 {nama_makul} &nbsp;—&nbsp; {nama_dosen} &nbsp;|&nbsp; Pertemuan {k['pertemuan']}</div>",
                unsafe_allow_html=True
            )
    else:
        st.warning("⚠️ Belum ada kelas yang dibuka oleh Dosen.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#4F46E5;'>Pilih Role </h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_mhs, col_dos = st.columns(2)
    with col_mhs:
        st.markdown("""
            <div style='background:white; border-radius:20px; padding:30px 20px;
                        text-align:center; box-shadow:0 4px 20px rgba(0,0,0,0.06);
                        border: 1.5px solid #E2E8F0;'>
                <div style='font-size:48px;'> </div>
                <div style='font-weight:700; font-size:18px; margin-top:10px; color:#1E293B;'>Mahasiswa</div>
                <div style='font-size:13px; color:#64748B; margin-top:6px;'>Isi presensi kehadiran</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
        if st.button("Masuk sebagai Mahasiswa", use_container_width=True, key="btn_mhs"):
            ke_halaman('mahasiswa')
    with col_dos:
        st.markdown("""
            <div style='background:white; border-radius:20px; padding:30px 20px;
                        text-align:center; box-shadow:0 4px 20px rgba(0,0,0,0.06);
                        border: 1.5px solid #E2E8F0;'>
                <div style='font-size:48px;'></div>
                <div style='font-weight:700; font-size:18px; margin-top:10px; color:#1E293B;'>Dosen</div>
                <div style='font-size:13px; color:#64748B; margin-top:6px;'>Kelola kelas & presensi</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
        if st.button("Masuk sebagai Dosen", use_container_width=True, key="btn_dos"):
            ke_halaman('dosen')

# ============================================================
# HALAMAN MAHASISWA — form presensi
# ============================================================
elif st.session_state['halaman'] == 'mahasiswa':

    if st.button("← Kembali", key="back_mhs"):
        ke_halaman('landing')

    # CEK APAKAH SUDAH ABSEN DI SESI INI
    if st.session_state['sudah_presensi']:
        st.success("✅ Anda sudah berhasil melakukan presensi pada sesi ini. Terima kasih!")
        st.info("💡 Untuk memberikan kesempatan presensi kepada mahasiswa lain menggunakan perangkat mereka sendiri, form telah dikunci untuk sesi ini.")
    else:
        semua_kelas_aktif = baca_semua_kelas_aktif()

        st.markdown(f"""
            <div class="clock-container">
                🕒 {waktu_sekarang.strftime('%d-%m-%Y')} pukul {waktu_sekarang.strftime('%H:%M:%S')} WIB
                <br><small style="color: #D97706; font-weight: normal;">*Waktu scan tercatat akurat di database.</small>
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
                    # MENGUNCI FORM SETELAH BERHASIL
                    st.session_state['sudah_presensi'] = True 
                    st.rerun() # Refresh halaman untuk memunculkan pesan sukses
                except Exception as e:
                    st.error(f"Gagal menyimpan ke Google Sheets: {e}")
            else:
                st.error("Gagal mengirim! Semua kolom wajib diisi.")

# ============================================================
# HALAMAN DOSEN — login + panel kelola kelas
# ============================================================
elif st.session_state['halaman'] == 'dosen':

    # Tombol kembali hanya kalau belum login
    if not st.session_state.get('dosen_login', False):
        if st.button("← Kembali", key="back_dos"):
            ke_halaman('landing')

        st.markdown("<h3 style='color:#4F46E5; text-align:center;'>Login Dosen</h3>", unsafe_allow_html=True)
        with st.form(key="form_login_dosen"):
            password_input = st.text_input("Password", type="password", placeholder="Masukkan password dosen...")
            tombol_login   = st.form_submit_button("Login")

        if tombol_login:
            PASSWORD_DOSEN = st.secrets.get("password_dosen", "dosen123")
            if password_input == PASSWORD_DOSEN:
                st.session_state['dosen_login'] = True
                st.rerun()
            else:
                st.error("Password salah!")

    else:
        # Header panel dengan tombol logout
        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.markdown("#### ✅ Panel Dosen")
        with col_logout:
            if st.button("Logout"):
                st.session_state['dosen_login'] = False
                ke_halaman('landing')

        # --- 1. ATUR KELAS ---
        st.markdown("<h4 style='color:#4F46E5;'>1. Atur & Aktifkan Kelas</h4>", unsafe_allow_html=True)

        pilihan_dosen = st.selectbox(
            "Nama Dosen Pengampu",
            options=list(DATA_JADWAL.keys()),
        )
        daftar_makul  = DATA_JADWAL[pilihan_dosen]
        pilihan_makul = st.selectbox("Nama Mata Kuliah", options=daftar_makul)

        input_makul_gabungan = f"{pilihan_makul} ({pilihan_dosen})"
        dosen_key            = pilihan_dosen

        status_dosen = baca_status_kelas_dosen(dosen_key)
        if status_dosen["aktif"]:
            nama_makul_aktif = status_dosen['makul'].rsplit(' (', 1)[0]
            st.info(f"🟢 Kelas aktif: **{nama_makul_aktif}** | Sem {status_dosen['semester']} | Pertemuan {status_dosen['pertemuan']}")
        else:
            st.caption("🔴 Dosen ini belum membuka kelas saat ini.")

        col1, col2 = st.columns(2)
        with col1:
            input_semester = st.text_input(
                "Semester",
                value=status_dosen["semester"] if status_dosen["semester"] != "-" else "",
                placeholder="Contoh: 4"
            )
        with col2:
            input_pertemuan = st.text_input(
                "Pertemuan Ke-",
                value=status_dosen["pertemuan"] if status_dosen["pertemuan"] != "-" else "",
                placeholder="Contoh: 3"
            )

        col_buka, col_tutup = st.columns(2)
        with col_buka:
            if st.button("✅ Aktifkan Kelas", use_container_width=True):
                if input_semester and input_pertemuan:
                    try:
                        tulis_status_kelas(
                            input_makul_gabungan, input_semester, input_pertemuan,
                            dosen_key=dosen_key, aktif=True
                        )
                        st.success("Kelas berhasil diaktifkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan: {e}")
                else:
                    st.error("Isi semester dan pertemuan terlebih dahulu!")
        with col_tutup:
            if st.button("⛔ Tutup Kelas Saya", use_container_width=True):
                try:
                    hasil = tutup_kelas(dosen_key=dosen_key)
                    if hasil:
                        st.success("Kelas berhasil ditutup.")
                    else:
                        st.warning("Tidak ada kelas aktif untuk dosen ini.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menutup: {e}")

        # --- 2. KELOLA SEMUA KELAS AKTIF ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#4F46E5;'>📋 Kelola Semua Kelas Aktif</h4>", unsafe_allow_html=True)

        kelas_aktif_sekarang = baca_semua_kelas_aktif()
        if kelas_aktif_sekarang:
            for idx_k, k in enumerate(kelas_aktif_sekarang):
                nm = k['makul'].rsplit(' (', 1)[0]
                nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                col_info, col_btn = st.columns([5, 2])
                with col_info:
                    st.markdown(
                        f"<div class='kelas-badge'>📚 {nm}<br>"
                        f"<small style='font-weight:400'>{nd} &nbsp;|&nbsp; Sem {k['semester']} &nbsp;|&nbsp; Pertemuan {k['pertemuan']}</small></div>",
                        unsafe_allow_html=True
                    )
                with col_btn:
                    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
                    if st.button("⛔ Tutup", key=f"tutup_kelas_{idx_k}", use_container_width=True):
                        try:
                            tutup_kelas_by_makul(k['makul'])
                            st.success(f"{nm} ditutup.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
        else:
            st.caption("Belum ada kelas aktif saat ini.")

        # --- 3. QR CODE ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#4F46E5;'>2. Generate QR Code Absensi</h4>", unsafe_allow_html=True)
        url_aplikasi = st.text_input("URL Aplikasi", placeholder="https://nama-app.streamlit.app")

        if st.button("Generate QR Code"):
            if url_aplikasi:
                qr_image = generate_qr(url_aplikasi)
                st.image(qr_image,
                         caption=f"QR Presensi — {pilihan_makul} Pertemuan {input_pertemuan}",
                         width=260)
                st.download_button(
                    label="⬇️ Download QR Code",
                    data=qr_image,
                    file_name=f"qr_{pilihan_makul}_pertemuan{input_pertemuan}.png",
                    mime="image/png"
                )
            else:
                st.error("Masukkan URL aplikasi terlebih dahulu!")

        # --- 4. LIHAT DATA ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#4F46E5;'>3. Lihat & Download Data Presensi</h4>", unsafe_allow_html=True)

        kelas_aktif_sekarang = baca_semua_kelas_aktif()
        
        if not kelas_aktif_sekarang:
            st.warning("⚠️ Belum ada kelas yang aktif saat ini. Aktifkan kelas terlebih dahulu.")
        else:
            # Dosen bisa memilih kelas mana saja yang sedang aktif untuk dilihat
            opsi_makul_aktif = [k['makul'] for k in kelas_aktif_sekarang]
            pilih_makul_lihat = st.selectbox("Pilih Kelas Aktif yang Ingin Dilihat:", options=opsi_makul_aktif)
            
            col_tampil, col_reload = st.columns([3, 1])
            with col_tampil:
                btn_tampil = st.button("Tampilkan Data Terkini", use_container_width=True)
            with col_reload:
                # Tombol ini secara otomatis akan me-rerun script dan mengambil data terbaru dari Sheets
                btn_reload = st.button("🔄 Reload Data", use_container_width=True)

            if btn_tampil or btn_reload:
                try:
                    sheet   = get_sheet()
                    nama_ws = pilih_makul_lihat.replace("/", "-").replace(":", "-")[:50]
                    ws      = sheet.worksheet(nama_ws)
                    data    = ws.get_all_records()
                    
                    if data:
                        df = pd.DataFrame(data)
                        if "Mata Kuliah" in df.columns:
                            df = df.drop(columns=["Mata Kuliah"])
                        
                        # 1. Menampilkan Tabel
                        st.dataframe(df, use_container_width=True)
                        
                        # 2. Menyiapkan Data Excel untuk Download
                        output = BytesIO()
                        df.to_excel(output, index=False, engine='openpyxl')
                        output.seek(0)
                        
                        col_dw, col_space = st.columns([1, 2])
                        with col_dw:
                            st.download_button(
                                label="⬇️ Download Excel",
                                data=output,
                                file_name=f"presensi_{pilih_makul_lihat}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        # 3. Menampilkan List Mahasiswa yang Masuk di Bawah
                        st.markdown("---")
                        st.markdown(f"##### 👥 Daftar Kehadiran ({len(df)} Mahasiswa)")
                        st.markdown("<div style='background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
                        
                        # Looping isi dataframe
                        for index, row in df.iterrows():
                            st.markdown(f"**{index + 1}. {row['Nama']}** ({row['NIM']}) <br><small style='color: #64748B;'>🕒 Masuk pukul: {row['Jam Isi']} WIB</small>", unsafe_allow_html=True)
                            
                        st.markdown("</div>", unsafe_allow_html=True)

                    else:
                        st.info(f"Belum ada mahasiswa yang mengisi presensi untuk kelas {pilih_makul_lihat}.")
                except gspread.exceptions.WorksheetNotFound:
                    st.info(f"Worksheet belum terbuat karena belum ada presensi masuk untuk kelas {pilih_makul_lihat}.")
                except Exception as e:
                    st.error(f"Error: {e}")