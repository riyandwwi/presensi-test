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

# ============================================================
# ZONA WAKTU & SESSION STATE
# ============================================================
tz_wib         = pytz.timezone('Asia/Jakarta')
waktu_sekarang = datetime.now(tz_wib)

DEFAULTS = {
    'dosen_login':       False,
    'sudah_presensi':    False,
    'halaman':           'landing',
    'nama_dosen_login':  None,
    'nim_terverifikasi': None,
    'nama_terverifikasi':None,
    'konfirmasi_data':   None,   # simpan data konfirmasi sukses mahasiswa
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# CONFIG HALAMAN
# ============================================================
st.set_page_config(page_title="Presensi Bisnis Digital", page_icon="📝", layout="centered")

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; color: #1E293B; }
.stApp { background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%); }
header {visibility:hidden;} footer {visibility:hidden;} #MainMenu {visibility:hidden;}

.header-banner {
    background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%);
    padding: 25px; border-radius: 16px; color: white;
    text-align: center; margin-bottom: 25px;
    box-shadow: 0 10px 20px rgba(79,70,229,0.15);
}
.header-banner h1 { color:white !important; font-weight:800; font-size:28px; margin-bottom:5px; }
.header-banner p  { color:#E0E7FF !important; font-size:15px; opacity:0.9; margin:0; }

div[data-testid="stForm"] {
    background: rgba(255,255,255,0.95); border: 1px solid #E2E8F0;
    border-radius: 20px !important; padding: 35px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.03) !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background-color: #F8FAFC !important; border: 1.5px solid #CBD5E1 !important;
    border-radius: 10px !important; padding: 12px 16px !important;
    font-size: 15px !important; transition: all 0.3s ease !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #4F46E5 !important; background-color: #FFFFFF !important;
    box-shadow: 0 0 0 4px rgba(79,70,229,0.1) !important;
}
button[kind="formSubmit"] {
    background: linear-gradient(135deg, #4F46E5 0%, #3B82F6 100%) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    padding: 12px 24px !important; font-size: 16px !important; font-weight: 700 !important;
    width: 100% !important; box-shadow: 0 4px 15px rgba(79,70,229,0.3) !important;
}
.clock-container {
    background-color: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px;
    padding: 12px; text-align: center; margin-bottom: 20px;
    color: #B45309; font-weight: 600; font-size: 14px;
}
.kelas-badge {
    background: white; border-left: 4px solid #4F46E5; border-radius: 8px;
    padding: 12px 16px; margin-bottom: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.02); color: #334155;
}
.konfirmasi-box {
    background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
    border: 2px solid #10B981; border-radius: 20px;
    padding: 30px; text-align: center; margin: 10px 0 20px 0;
}
.konfirmasi-box h2 { color: #065F46 !important; font-size: 22px; margin-bottom: 8px; }
.konfirmasi-box .detail { color: #047857; font-size: 15px; line-height: 1.8; }
.counter-box {
    background: white; border-radius: 12px; padding: 14px 20px;
    text-align: center; border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-top: 10px;
}
.counter-box .angka { font-size: 32px; font-weight: 800; color: #4F46E5; }
.counter-box .label { font-size: 13px; color: #64748B; margin-top: 2px; }
.histori-container {
    background-color: #FFFFFF; border: 1px solid #E2E8F0;
    border-left: 4px solid #10B981; border-radius: 8px;
    padding: 15px; margin-bottom: 12px;
}
.token-expired {
    background: #FEF2F2; border: 2px solid #FECACA; border-radius: 16px;
    padding: 24px; text-align: center; color: #DC2626;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# GOOGLE SHEETS
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

def baca_semua_kelas_aktif():
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
        st.error(f"Gagal terhubung ke database: {e}")
        return []

def baca_status_kelas_dosen(dosen_key):
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
    except Exception: pass
    return {"makul":"Belum Diatur","semester":"-","pertemuan":"-","aktif":False}

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
                ws.update_cell(i, col_ak, "0"); return True
    except Exception: pass
    return False

def tutup_kelas_by_makul(makul):
    try:
        sheet  = get_sheet()
        ws     = sheet.worksheet(STATUS_SHEET)
        data   = ws.get_all_values()
        header = data[0]
        col_m  = header.index("makul") + 1
        col_ak = header.index("aktif") + 1
        for i, row in enumerate(data[1:], start=2):
            if len(row) >= col_m and row[col_m-1] == makul:
                ws.update_cell(i, col_ak, "0"); return True
    except Exception: pass
    return False

def hapus_entri_presensi(nama_ws, nim, pertemuan):
    """Hapus baris presensi berdasarkan NIM + pertemuan."""
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
    # Nama worksheet: maks 31 karakter (batasan Google Sheets), pakai hash suffix untuk uniqueness
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

def hitung_hadir(makul, pertemuan):
    """Hitung jumlah mahasiswa yang sudah hadir di kelas ini."""
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
        "AIK 2 A","AIK 4","AIK 2 B"
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
        "Pemrograman Web A","Basis Data",
        "Pemrograman Web B","Sistem Pendukung Keputusan"
    ],
    "Doni Uji Windiatmoko, S.Pd., M.Pd.": [
        "Kewarganegaraan B","Kewarganegaraan A"
    ],
    "Purwati, S.S., M.Hum.": [
        "Bahasa Inggris 2 A","Bahasa Inggris 2 B"
    ],
}

def ke_halaman(nama):
    st.session_state['halaman'] = nama
    st.rerun()

# ============================================================
# HEADER
# ============================================================
st.markdown("""
    <div class="header-banner">
        <h1>PRESENSI BISNIS DIGITAL</h1>
        <p>Beta ver 1.0</p>
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
            nm = k['makul'].rsplit(' (', 1)[0]
            nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
            st.markdown(
                f"<div class='kelas-badge'>📚 <b>{nm}</b><br>"
                f"<span style='color:#64748B;font-size:13px;'>👨‍🏫 {nd} &nbsp;|&nbsp; Pertemuan {k['pertemuan']}</span></div>",
                unsafe_allow_html=True
            )
    else:
        st.info("🕒 Belum ada kelas yang dibuka oleh dosen saat ini.")

    st.markdown("<br><h3 style='text-align:center;color:#1E293B;font-weight:700;'>Pilih Akses Anda</h3><br>", unsafe_allow_html=True)
    col_mhs, col_dos = st.columns(2)
    with col_mhs:
        st.markdown("""
            <div style='background:white;border-radius:16px;padding:30px 20px;
                text-align:center;border:1.5px solid #E2E8F0;'>
                <div style='font-size:45px;'>🧑‍🎓</div>
                <div style='font-weight:700;font-size:18px;margin-top:10px;'>Mahasiswa</div>
                <div style='font-size:13px;color:#64748B;margin-top:6px;'>Isi daftar hadir perkuliahan</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
        if st.button("Masuk Mahasiswa", use_container_width=True, key="btn_mhs"):
            ke_halaman('mahasiswa')
    with col_dos:
        st.markdown("""
            <div style='background:white;border-radius:16px;padding:30px 20px;
                text-align:center;border:1.5px solid #E2E8F0;'>
                <div style='font-size:45px;'>👨‍🏫</div>
                <div style='font-weight:700;font-size:18px;margin-top:10px;'>Dosen</div>
                <div style='font-size:13px;color:#64748B;margin-top:6px;'>Kelola kelas & rekap data</div>
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
            st.session_state['sudah_presensi']    = False
            st.session_state['konfirmasi_data']   = None
            ke_halaman('landing')

    # ── Tampilan setelah sukses submit ──
    if st.session_state['sudah_presensi'] and st.session_state['konfirmasi_data']:
        kd = st.session_state['konfirmasi_data']

        st.markdown(f"""
            <div class="konfirmasi-box">
                <h2>✅ Kehadiran Tercatat!</h2>
                <div class="detail">
                    <b>{kd['nama']}</b> &nbsp;·&nbsp; NIM: {kd['nim']}<br>
                    📚 {kd['makul']}<br>
                    📅 {kd['tanggal']} &nbsp;·&nbsp; 🕒 {kd['jam']} WIB<br>
                    📖 Pertemuan Ke-{kd['pertemuan']} &nbsp;·&nbsp; Semester {kd['semester']}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Counter mahasiswa yang sudah hadir
        total_hadir = hitung_hadir(kd['makul_raw'], kd['pertemuan'])
        st.markdown(f"""
            <div class="counter-box">
                <div class="angka">{total_hadir}</div>
                <div class="label">mahasiswa sudah hadir di kelas ini 🎉</div>
            </div>
        """, unsafe_allow_html=True)

        st.info("💡 Form telah dikunci untuk sesi ini. Terima kasih telah hadir!")

    else:
        # ── Form presensi ──
        semua_kelas_aktif = baca_semua_kelas_aktif()

        st.markdown(f"""
            <div class="clock-container">
                🕒 Tanggal: <b>{waktu_sekarang.strftime('%d-%m-%Y')}</b> &nbsp;|&nbsp;
                Jam: <b>{waktu_sekarang.strftime('%H:%M:%S')} WIB</b>
                <br><small style="color:#D97706;font-weight:normal;">Waktu server tercatat otomatis.</small>
            </div>
        """, unsafe_allow_html=True)

        with st.form(key="form_presensi", clear_on_submit=False):
            st.markdown("<h4 style='text-align:center;color:#1E293B;margin-bottom:20px;'>📝 Form Kehadiran</h4>", unsafe_allow_html=True)

            col_nama, col_nim = st.columns(2)
            with col_nama:
                nama = st.text_input("Nama Lengkap", placeholder="Sesuai SIAKAD")
            with col_nim:
                nim  = st.text_input("NIM", placeholder="Contoh: 220101001")

            if semua_kelas_aktif:
                def label_kelas(k):
                    nm = k['makul'].rsplit(' (', 1)[0]
                    nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                    return f"{nm} — {nd} | Pertemuan {k['pertemuan']}"
                opsi_kelas           = [label_kelas(k) for k in semua_kelas_aktif]
                pilihan_kelas_label  = st.selectbox("🏫 Pilih Sesi Kelas:", options=opsi_kelas)
            else:
                pilihan_kelas_label = None
                st.warning("⚠️ Belum ada kelas aktif. Silakan tunggu instruksi dosen.")

            materi = st.text_area(
                "Rangkuman Materi Hari Ini (min. 20 karakter)",
                placeholder="Tulis ringkasan singkat materi yang dibahas...",
                height=100
            )
            st.markdown("<br>", unsafe_allow_html=True)
            submit_button = st.form_submit_button(label="KIRIM BUKTI HADIR")

        if submit_button:
            if not semua_kelas_aktif or pilihan_kelas_label is None:
                st.error("Gagal! Belum ada kelas yang dibuka saat ini.")
            elif not nama.strip():
                st.error("Nama wajib diisi!")
            elif not nim.strip():
                st.error("NIM wajib diisi!")
            elif len(materi.strip()) < 20:
                st.error(f"Rangkuman materi terlalu pendek ({len(materi.strip())} karakter). Minimal 20 karakter.")
            else:
                idx_pilihan   = opsi_kelas.index(pilihan_kelas_label)
                kelas_dipilih = semua_kelas_aktif[idx_pilihan]
                tgl           = waktu_sekarang.strftime("%Y-%m-%d")
                jam           = waktu_sekarang.strftime("%H:%M:%S")
                try:
                    sheet   = get_sheet()
                    raw     = kelas_dipilih["makul"]
                    safe    = raw.replace("/","-").replace(":","-").replace("\\","-")
                    if len(safe) > 28:
                        suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                        safe   = safe[:24] + "_" + suffix
                    ws      = get_or_create_worksheet(sheet, safe)
                    records = ws.get_all_records()

                    # Cek duplikasi
                    sudah = any(
                        str(r.get('NIM','')).strip() == nim.strip() and
                        str(r.get('Pertemuan Ke','')) == str(kelas_dipilih["pertemuan"])
                        for r in records
                    )
                    if sudah:
                        st.error(f"❌ NIM {nim} sudah terdaftar hadir pada Pertemuan Ke-{kelas_dipilih['pertemuan']}!")
                    else:
                        simpan_ke_sheets({
                            "Tanggal":          tgl,
                            "Jam Isi":          jam,
                            "Mata Kuliah":      kelas_dipilih["makul"],
                            "Semester":         kelas_dipilih["semester"],
                            "Pertemuan Ke":     kelas_dipilih["pertemuan"],
                            "NIM":              nim.strip(),
                            "Nama":             nama.strip(),
                            "Rangkuman Materi": materi.strip()
                        })
                        nm_makul = kelas_dipilih['makul'].rsplit(' (', 1)[0]
                        st.session_state['konfirmasi_data'] = {
                            "nama":      nama.strip(),
                            "nim":       nim.strip(),
                            "makul":     nm_makul,
                            "makul_raw": kelas_dipilih["makul"],
                            "tanggal":   tgl,
                            "jam":       jam,
                            "pertemuan": kelas_dipilih["pertemuan"],
                            "semester":  kelas_dipilih["semester"],
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
        # ── Form Login Dosen ──
        st.markdown("<h3 style='color:#4F46E5;text-align:center;'>Autentikasi Dosen</h3>", unsafe_allow_html=True)

        with st.form(key="form_login_dosen"):
            # Pilih nama dosen SEBELUM masukkan password
            pilihan_nama_login = st.selectbox("Nama Dosen", options=list(DATA_JADWAL.keys()))
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
        # ── Dashboard Dosen ──
        nama_dosen_aktif = st.session_state.get('nama_dosen_login', list(DATA_JADWAL.keys())[0])
        dosen_key        = nama_dosen_aktif

        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.markdown(f"#### 👨‍🏫 Dashboard: {nama_dosen_aktif.split(',')[0]}")
        with col_logout:
            if st.button("Keluar", use_container_width=True):
                st.session_state['dosen_login']      = False
                st.session_state['nama_dosen_login'] = None
                ke_halaman('landing')

        kelas_aktif_sekarang = baca_semua_kelas_aktif()
        tab1, tab2, tab3 = st.tabs(["🚀 Buka Kelas & QR", "📋 Monitor Kelas Aktif", "📂 Arsip & Histori"])

        # ─────────────────────────────────────────
        # TAB 1 — BUKA KELAS & QR
        # ─────────────────────────────────────────
        with tab1:
            st.markdown("#### Aktivasi Perkuliahan")
            st.caption(f"Login sebagai: **{nama_dosen_aktif}**")

            daftar_makul  = DATA_JADWAL[nama_dosen_aktif]
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
                    # Semester dropdown 1-8
                    opt_smt       = [str(i) for i in range(1, 9)]
                    default_smt   = status_dosen["semester"] if status_dosen["semester"] in opt_smt else opt_smt[0]
                    input_semester = st.selectbox("Semester:", options=opt_smt, index=opt_smt.index(default_smt))
                with col2:
                    # Pertemuan dropdown 1-16
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
            st.markdown("#### Generator QR Code")

            # URL otomatis dari query params / hostname
            try:
                base_url_default = st.secrets.get("app_url", "https://your-app.streamlit.app")
            except Exception:
                base_url_default = "https://your-app.streamlit.app"

            url_aplikasi = st.text_input("Tautan URL Aplikasi:", value=base_url_default)
            if st.button("Tampilkan QR Code", type="primary"):
                if url_aplikasi:
                    qr_image = generate_qr(url_aplikasi)
                    st.image(qr_image, caption=f"Scan QR — {pilihan_makul} (P-{input_pertemuan})", width=250)
                    st.download_button(
                        label="⬇️ Unduh Gambar QR", data=qr_image,
                        file_name=f"QR_{pilihan_makul}_P{input_pertemuan}.png", mime="image/png"
                    )
                else:
                    st.warning("Masukkan URL terlebih dahulu.")

        # ─────────────────────────────────────────
        # TAB 2 — MONITOR KELAS AKTIF
        # ─────────────────────────────────────────
        with tab2:
            col_m, col_r = st.columns([4, 1])
            with col_m:
                st.metric("Total Kelas Berjalan (Global)", f"{len(kelas_aktif_sekarang)} Kelas")
            with col_r:
                st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
                if st.button("🔄 Reload", use_container_width=True, key="reload_mon"):
                    st.rerun()
            st.markdown("---")

            if kelas_aktif_sekarang:
                for idx_k, k in enumerate(kelas_aktif_sekarang):
                    nm = k['makul'].rsplit(' (', 1)[0]
                    nd = k['makul'].rsplit(' (', 1)[-1].rstrip(')').split(',')[0]
                    with st.container(border=True):
                        col_info, col_btn = st.columns([4, 1])
                        with col_info:
                            st.markdown(
                                f"📚 **{nm}**<br>"
                                f"<span style='color:#64748B;font-size:14px;'>👨‍🏫 {nd} | Smt {k['semester']} | Pertemuan {k['pertemuan']}</span>",
                                unsafe_allow_html=True
                            )
                        with col_btn:
                            if st.button("Tutup Paksa", key=f"tutup_{idx_k}", use_container_width=True):
                                tutup_kelas_by_makul(k['makul'])
                                st.toast(f"Kelas {nm} ditutup.", icon="🧹")
                                st.rerun()

                        with st.expander("Lihat mahasiswa yang sudah hadir"):
                            try:
                                raw   = k['makul']
                                safe  = raw.replace("/","-").replace(":","-").replace("\\","-")
                                if len(safe) > 28:
                                    suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                                    safe   = safe[:24] + "_" + suffix
                                ws_mon  = get_sheet().worksheet(safe)
                                data_m  = ws_mon.get_all_records()
                                df_m    = pd.DataFrame(data_m)
                                df_mf   = df_m[df_m['Pertemuan Ke'].astype(str) == str(k['pertemuan'])]
                                if not df_mf.empty:
                                    st.success(f"**{len(df_mf)} mahasiswa** sudah hadir")
                                    for i, row in df_mf.reset_index(drop=True).iterrows():
                                        st.markdown(
                                            f"**{i+1}. {row['Nama']}** &nbsp;<span style='color:#64748B;font-size:13px;'>({row['NIM']})</span>"
                                            f"<br><span style='font-size:12px;color:#94A3B8;'>🕒 {row['Jam Isi']} WIB</span>",
                                            unsafe_allow_html=True
                                        )
                                        if i < len(df_mf) - 1:
                                            st.markdown("<hr style='margin:6px 0;border-color:#F1F5F9;'>", unsafe_allow_html=True)
                                else:
                                    st.info("Belum ada mahasiswa yang hadir.")
                            except gspread.exceptions.WorksheetNotFound:
                                st.info("Belum ada data presensi.")
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.caption("Tidak ada kelas aktif saat ini.")

        # ─────────────────────────────────────────
        # TAB 3 — ARSIP & HISTORI
        # ─────────────────────────────────────────
        with tab3:
            st.markdown("#### Pusat Data Kehadiran")
            makul_opsi    = DATA_JADWAL[nama_dosen_aktif]
            pilih_makul_a = st.selectbox("Pilih Mata Kuliah:", options=makul_opsi, key="arsip_makul")
            makul_gabung  = f"{pilih_makul_a} ({nama_dosen_aktif})"

            # Sub-tabs: Data | Hapus Entri
            sub1, sub2 = st.tabs(["📊 Lihat & Unduh", "🗑️ Hapus Entri Salah"])

            with sub1:
                with st.expander("📥 Unduh Master Rekap Semester (P1-P16)", expanded=False):
                    if st.button("Generate Rekap Global", use_container_width=True):
                        try:
                            raw   = makul_gabung
                            safe  = raw.replace("/","-").replace(":","-").replace("\\","-")
                            if len(safe) > 28:
                                suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                                safe   = safe[:24] + "_" + suffix
                            ws    = get_sheet().worksheet(safe)
                            data  = ws.get_all_records()
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
                    opt_prt2      = [str(i) for i in range(1, 17)]
                    pilih_prt_a   = st.selectbox("Lihat Pertemuan Ke-:", options=opt_prt2)
                with col_a:
                    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
                    btn_tampil = st.button("Tampilkan Data", use_container_width=True)

                if btn_tampil:
                    try:
                        raw   = makul_gabung
                        safe  = raw.replace("/","-").replace(":","-").replace("\\","-")
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

                # Histori ringkasan
                st.markdown("---")
                st.markdown("##### 📜 Histori Log Kelas")
                try:
                    raw   = makul_gabung
                    safe  = raw.replace("/","-").replace(":","-").replace("\\","-")
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
                                        <span style='font-size:12px;color:#64748B;'>Tanggal: {rh['tgl']}</span>
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
                    opt_prt3    = [str(i) for i in range(1, 17)]
                    prt_hapus   = st.selectbox("Dari Pertemuan Ke-:", options=opt_prt3, key="hapus_prt")

                if st.button("🗑️ Hapus Entri Ini", type="primary", use_container_width=True):
                    if nim_hapus.strip():
                        raw   = makul_gabung
                        safe  = raw.replace("/","-").replace(":","-").replace("\\","-")
                        if len(safe) > 28:
                            suffix = hashlib.md5(raw.encode()).hexdigest()[:4]
                            safe   = safe[:24] + "_" + suffix
                        ok, pesan = hapus_entri_presensi(safe, nim_hapus.strip(), prt_hapus)
                        if ok: st.success(f"✅ {pesan}")
                        else:  st.error(f"❌ {pesan}")
                    else:
                        st.error("Masukkan NIM terlebih dahulu.")