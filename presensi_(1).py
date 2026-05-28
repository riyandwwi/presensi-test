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
# FUNGSI BACA / TULIS STATUS KELAS KE GOOGLE SHEETS
# ============================================================
STATUS_SHEET = "STATUS_KELAS"

def baca_status_kelas():
    """Baca status kelas aktif dari Google Sheets."""
    try:
        sheet = get_sheet()
        try:
            ws = sheet.worksheet(STATUS_SHEET)
        except gspread.exceptions.WorksheetNotFound:
            ws = sheet.add_worksheet(title=STATUS_SHEET, rows="5", cols="5")
            ws.append_row(["makul", "semester", "pertemuan", "aktif"])
            ws.append_row(["Belum Diatur", "-", "-", "0"])

        data = ws.get_all_records()
        if data:
            row = data[0]
            return {
                "makul":     row.get("makul", "Belum Diatur"),
                "semester":  row.get("semester", "-"),
                "pertemuan": row.get("pertemuan", "-"),
                "aktif":     str(row.get("aktif", "0")) == "1"
            }
    except Exception as e:
        st.error(f"⚠️ Gagal terhubung ke Google Sheets: {e}")
    return {"makul": "Belum Diatur", "semester": "-", "pertemuan": "-", "aktif": False}

def tulis_status_kelas(makul, semester, pertemuan, aktif=True):
    """Simpan status kelas aktif ke Google Sheets."""
    sheet = get_sheet()
    try:
        ws = sheet.worksheet(STATUS_SHEET)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=STATUS_SHEET, rows="5", cols="5")
        ws.append_row(["makul", "semester", "pertemuan", "aktif"])

    ws.clear()
    ws.append_row(["makul", "semester", "pertemuan", "aktif"])
    ws.append_row([makul, semester, pertemuan, "1" if aktif else "0"])

def tutup_kelas():
    """Nonaktifkan kelas."""
    sheet = get_sheet()
    try:
        ws = sheet.worksheet(STATUS_SHEET)
        ws.clear()
        ws.append_row(["makul", "semester", "pertemuan", "aktif"])
        ws.append_row(["Belum Diatur", "-", "-", "0"])
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
# BACA STATUS KELAS DARI SHEETS
# ============================================================
status = baca_status_kelas()
makul_aktif     = status["makul"]
semester_aktif  = status["semester"]
pertemuan_aktif = status["pertemuan"]
kelas_aktif     = status["aktif"]

# ============================================================
# HEADER VIA MARKDOWN
# ============================================================
st.markdown("""
    <div class="header-banner">
        <h1>PRESENSI AKADEMIK BISNIS DIGITAL</h1>
        <p>Ver Beta 0.37</p>
    </div>
""", unsafe_allow_html=True)

if kelas_aktif and makul_aktif != "Belum Diatur":
    st.info(f"📍 **Kelas Aktif:** {makul_aktif} | **Semester:** {semester_aktif} | **Pertemuan Ke:** {pertemuan_aktif}")
else:
    st.warning("⚠️ **Status:** Presensi belum dibuka oleh Dosen.")

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
# FORM MAHASISWA
# ============================================================
with st.form(key="form_presensi", clear_on_submit=True):
    nama   = st.text_input("Nama Lengkap Mahasiswa", placeholder=" ")
    nim    = st.text_input("NIM (Nomor Induk Mahasiswa)", placeholder="")
    materi = st.text_area(
        "Materi Kuliah Hari Ini",
        placeholder="Masukan topik materi yang di bahas ",
        height=120
    )
    submit_button = st.form_submit_button(label="KIRIM KEHADIRAN AKTIF")

if submit_button:
    if not kelas_aktif or makul_aktif == "Belum Diatur":
        st.error("Presensi gagal! Dosen belum mengaktifkan kelas hari ini.")
    elif nama and nim and materi:
        tanggal_hari_ini = waktu_sekarang.strftime("%Y-%m-%d")
        jam_menit_detik  = waktu_sekarang.strftime("%H:%M:%S")
        try:
            simpan_ke_sheets({
                "Tanggal":          tanggal_hari_ini,
                "Jam Isi":          jam_menit_detik,
                "Mata Kuliah":      makul_aktif,
                "Semester":         semester_aktif,
                "Pertemuan Ke":     pertemuan_aktif,
                "NIM":              nim.strip(),
                "Nama":             nama.strip(),
                "Rangkuman Materi": materi.strip()
            })
            st.balloons()
            st.success(f"✨ Kehadiran berhasil! {nama} ({nim}) tercatat pukul {jam_menit_detik} WIB.")
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

        # --- 1. ATUR KELAS (DROPDOWN DINAMIS) ---
        st.markdown("<h4 style='color:#4F46E5;'>1. Atur & Aktifkan Kelas</h4>", unsafe_allow_html=True)

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

        pilihan_dosen = st.selectbox(
            "Nama Dosen Pengampu",
            options=list(DATA_JADWAL.keys()),
            placeholder="Pilih Nama Dosen..."
        )

        daftar_makul = DATA_JADWAL[pilihan_dosen]
        pilihan_makul = st.selectbox(
            "Nama Mata Kuliah",
            options=daftar_makul,
            placeholder="Pilih Mata Kuliah..."
        )

        input_makul_gabungan = f"{pilihan_makul} ({pilihan_dosen})"

        col1, col2 = st.columns(2)
        with col1:
            input_semester = st.text_input(
                "Semester",
                value=semester_aktif if semester_aktif != "-" else "",
                placeholder="Contoh: 4"
            )
        with col2:
            input_pertemuan = st.text_input(
                "Pertemuan Ke-",
                value=pertemuan_aktif if pertemuan_aktif != "-" else "",
                placeholder="Contoh: 3"
            )

        col_buka, col_tutup = st.columns(2)
        with col_buka:
            if st.button("Simpan & Aktifkan Kelas", use_container_width=True):
                if input_makul_gabungan and input_semester and input_pertemuan:
                    try:
                        tulis_status_kelas(input_makul_gabungan, input_semester, input_pertemuan, aktif=True)
                        st.success("Kelas berhasil diaktifkan! Semua device sekarang bisa presensi.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan: {e}")
                else:
                    st.error("Isi semua data kelas terlebih dahulu!")
        with col_tutup:
            if st.button("Tutup Presensi", use_container_width=True):
                try:
                    tutup_kelas()
                    st.success("Presensi ditutup.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menutup: {e}")

        # --- 2. QR CODE ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#4F46E5;'>2. Generate QR Code Absensi</h4>", unsafe_allow_html=True)
        url_aplikasi = st.text_input("URL Aplikasi", placeholder="https://nama-app.streamlit.app")

        if st.button("Generate QR Code"):
            if url_aplikasi:
                qr_image = generate_qr(url_aplikasi)
                st.image(qr_image,
                         caption=f"QR Presensi — {makul_aktif} Pertemuan {pertemuan_aktif}",
                         width=260)
                st.download_button(
                    label="⬇️ Download QR Code",
                    data=qr_image,
                    file_name=f"qr_{makul_aktif}_pertemuan{pertemuan_aktif}.png",
                    mime="image/png"
                )
            else:
                st.error("Masukkan URL aplikasi terlebih dahulu!")

        # --- 3. LIHAT DATA ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#4F46E5;'>3. Lihat & Download Data Presensi</h4>", unsafe_allow_html=True)

        if st.button("Tampilkan Data dari Google Sheets"):
            try:
                sheet   = get_sheet()
                nama_ws = makul_aktif.replace("/", "-").replace(":", "-")[:50]
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
                        file_name=f"presensi_{makul_aktif}_pertemuan{pertemuan_aktif}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("Belum ada data presensi untuk mata kuliah ini.")
            except gspread.exceptions.WorksheetNotFound:
                st.info("Belum ada data presensi untuk mata kuliah ini.")
            except Exception as e:
                st.error(f"Error: {e}")