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
    try:
        sheet = get_sheet()
        ws = sheet.worksheet(STATUS_SHEET)
        data = ws.get_all_values()
        header = data[0] if data else []
        try:
            col_dosen = header.index("dosen_key") + 1
            col_aktif = header.index("aktif") + 1
        except ValueError:
            return
        for i, row in enumerate(data[1:], start=2):
            if len(row) >= col_dosen and row[col_dosen - 1] == dosen_key:
                ws.update_cell(i, col_aktif, "0")
                break
    except Exception:
        pass

# ============================================================
# FUNGSI SIMPAN PRESENSI
# ============================================================
def get_or_create_worksheet(sheet, title):
    try:
        ws = sheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=title, rows="1000", cols="10")
        ws.append_row(["Tanggal", "Jam Isi", "Mata Kuliah",
                       "Semester", "Pertemuan Ke", "NIM", "Nama", "Rangkuman Materi"])
    return ws

def simpan_ke_sheets(data: dict):
    sheet   = get_sheet()
    nama_ws = data["Mata Kuliah"].replace("/", "-").replace(":", "-")[:50]
    ws      = get_or_create_worksheet(sheet, nama_ws)
    existing = ws.get_all_values()
    if not existing:
        ws.append_row(["Tanggal", "Jam Isi", "Mata Kuliah",
                       "Semester", "Pertemuan Ke", "NIM", "Nama", "Rangkuman Materi"])
    ws.append_row([
        data["Tanggal"], data["Jam Isi"], data["Mata Kuliah"],
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
# BACA SEMUA KELAS AKTIF
# ============================================================
semua_kelas_aktif = baca_semua_kelas_aktif()

# ============================================================
# HEADER
# ============================================================
st.markdown("""
    <div class="header-banner">
        <h1>PRESENSI AKADEMIK BISNIS DIGITAL</h1>
        <p>Ver Beta 0.40 — Multi Kelas</p>
    </div>
""", unsafe_allow_html=True)

if semua_kelas_aktif:
    st.success(f"📍 **{len(semua_kelas_aktif)} Kelas Aktif Saat Ini:**")
    for k in semua_kelas_aktif:
        st.markdown(
            f"<div class='kelas-badge'>📚 {k['makul']} &nbsp;|&nbsp; Sem {k['semester']} &nbsp;|&nbsp; Pertemuan {k['pertemuan']}</div>",
            unsafe_allow_html=True
        )
else:
    st.warning("⚠️ **Status:** Belum ada kelas yang dibuka oleh Dosen.")

waktu_sekarang = datetime.now()
st.markdown(f"""
    <div class="clock-container">
        🕒 WAKTU SERVER AKTIF: {waktu_sekarang.strftime('%d-%m-%Y')} pukul {waktu_sekarang.strftime('%H:%M:%S')} WIB
        <br><small style="color: #D97706; font-weight: normal;">
            *Waktu scan akan tercatat secara akurat di database.
        </small>
    </div>
""", unsafe_allow_html=True)

# ============================================================
# FORM MAHASISWA — DENGAN PILIHAN KELAS AKTIF
# ============================================================
with st.form(key="form_presensi", clear_on_submit=True):
    nama = st.text_input("Nama Lengkap Mahasiswa", placeholder=" ")
    nim  = st.text_input("NIM (Nomor Induk Mahasiswa)", placeholder="")

    if semua_kelas_aktif:
        opsi_kelas = [
            f"{k['makul']} | Sem {k['semester']} | Pertemuan {k['pertemuan']}"
            for k in semua_kelas_aktif
        ]
        pilihan_kelas_label = st.selectbox(
            "🏫 Pilih Kelas yang Sedang Kamu Ikuti",
            options=opsi_kelas,
            help="Pilih sesuai mata kuliah yang kamu ikuti sekarang."
        )
    else:
        pilihan_kelas_label = None
        st.info("Belum ada kelas aktif. Tunggu dosen membuka presensi.")

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
            st.success(
                f"✨ Kehadiran berhasil! **{nama}** ({nim}) tercatat di "
                f"**{kelas_dipilih['makul']}** pukul {jam_menit_detik} WIB."
            )
        except Exception as e:
            st.error(f"Gagal menyimpan ke Google Sheets: {e}")
    else:
        st.error("Gagal mengirim! Semua kolom wajib diisi.")

# ============================================================
# PANEL DOSEN — DILINDUNGI PASSWORD
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("PANEL DOSEN"):

    if not st.session_state.get('dosen_login', False):
        with st.form(key="form_login_dosen"):
            password_input = st.text_input("Password", type="password", placeholder="Masukkan password dosen...")
            tombol_login   = st.form_submit_button("Login")

        if tombol_login:
            PASSWORD_DOSEN = st.secrets.get("password_dosen", "dosen123")
            if password_input == PASSWORD_DOSEN:
                st.session_state['dosen_login'] = True
                st.success("Login berhasil!")
                st.rerun()
            else:
                st.error("Password salah!")
    else:
        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.markdown("#### ✅ Panel Dosen Aktif")
        with col_logout:
            if st.button("Logout"):
                st.session_state['dosen_login'] = False
                st.rerun()

        # --- 1. ATUR KELAS ---
        st.markdown("<h4 style='color:#4F46E5;'>1. Atur & Aktifkan Kelas</h4>", unsafe_allow_html=True)

        pilihan_dosen = st.selectbox(
            "Nama Dosen Pengampu",
            options=list(DATA_JADWAL.keys()),
            placeholder="Pilih Nama Dosen..."
        )

        daftar_makul  = DATA_JADWAL[pilihan_dosen]
        pilihan_makul = st.selectbox(
            "Nama Mata Kuliah",
            options=daftar_makul,
            placeholder="Pilih Mata Kuliah..."
        )

        input_makul_gabungan = f"{pilihan_makul} ({pilihan_dosen})"
        dosen_key            = pilihan_dosen

        # Tampilkan status kelas dosen yang dipilih
        status_dosen = baca_status_kelas_dosen(dosen_key)
        if status_dosen["aktif"]:
            st.info(
                f"🟢 Kelas aktif dosen ini: **{status_dosen['makul']}** "
                f"| Sem {status_dosen['semester']} | Pertemuan {status_dosen['pertemuan']}"
            )
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
            if st.button("Simpan & Aktifkan Kelas", use_container_width=True):
                if input_makul_gabungan and input_semester and input_pertemuan:
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
                    st.error("Isi semua data kelas terlebih dahulu!")
        with col_tutup:
            if st.button("Tutup Presensi Saya", use_container_width=True):
                try:
                    tutup_kelas(dosen_key=dosen_key)
                    st.success("Presensi kelas Anda telah ditutup.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menutup: {e}")

        # Ringkasan semua kelas aktif
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#4F46E5;'>📋 Semua Kelas Aktif Saat Ini</h4>", unsafe_allow_html=True)
        if semua_kelas_aktif:
            for k in semua_kelas_aktif:
                st.markdown(
                    f"<div class='kelas-badge'>📚 {k['makul']} &nbsp;|&nbsp; Sem {k['semester']} &nbsp;|&nbsp; Pertemuan {k['pertemuan']}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("Belum ada kelas aktif.")

        # --- 2. QR CODE ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#4F46E5;'>2. Generate QR Code Absensi</h4>", unsafe_allow_html=True)
        url_aplikasi = st.text_input("URL Aplikasi", placeholder="https://nama-app.streamlit.app")

        if st.button("Generate QR Code"):
            if url_aplikasi:
                qr_image = generate_qr(url_aplikasi)
                st.image(qr_image,
                         caption=f"QR Presensi — {input_makul_gabungan} Pertemuan {input_pertemuan}",
                         width=260)
                st.download_button(
                    label="⬇️ Download QR Code",
                    data=qr_image,
                    file_name=f"qr_{pilihan_makul}_pertemuan{input_pertemuan}.png",
                    mime="image/png"
                )
            else:
                st.error("Masukkan URL aplikasi terlebih dahulu!")

        # --- 3. LIHAT DATA ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#4F46E5;'>3. Lihat & Download Data Presensi</h4>", unsafe_allow_html=True)

        semua_makul_dosen = [
            f"{mk} ({pilihan_dosen})" for mk in DATA_JADWAL[pilihan_dosen]
        ]
        makul_lihat = st.selectbox("Pilih Mata Kuliah untuk Ditampilkan", semua_makul_dosen)

        if st.button("Tampilkan Data dari Google Sheets"):
            try:
                sheet   = get_sheet()
                nama_ws = makul_lihat.replace("/", "-").replace(":", "-")[:50]
                ws      = sheet.worksheet(nama_ws)
                data    = ws.get_all_records()
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    output = BytesIO()
                    df.to_excel(output, index=False, engine='openpyxl')
                    output.seek(0)
                    st.download_button(
                        label="Download Excel",
                        data=output,
                        file_name=f"presensi_{makul_lihat}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("Belum ada data presensi untuk mata kuliah ini.")
            except gspread.exceptions.WorksheetNotFound:
                st.info("Belum ada data presensi untuk mata kuliah ini.")
            except Exception as e:
                st.error(f"Error: {e}")