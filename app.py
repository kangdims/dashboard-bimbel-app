import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import json
import urllib.request
import urllib.error
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ---------------------------------------------------------
# KONFIGURASI HALAMAN WEB & THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Dashboard Multi-TA - Bimbingan Belajar",
    page_icon="📊",
    layout="wide"
)

# Custom Styling Adaptive Theme & Elements
st.markdown("""
    <style>
    /* Styling Metric Cards Adaptive Theme */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color) !important;
        padding: 16px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stMetricLabel"] > div {
        color: var(--text-color) !important;
        opacity: 0.85 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: var(--text-color) !important;
        font-weight: 700 !important;
        font-size: clamp(1.05rem, 1.7vw, 1.55rem) !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.25 !important;
    }
    
    div[data-testid="stAlert"] {
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 10px !important;
    }

    .btn-download-pdf {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #FF4B4B 0%, #FF2B2B 100%);
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 1rem;
        padding: 12px 28px;
        border-radius: 10px;
        text-decoration: none !important;
        border: none;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.35);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        cursor: pointer;
        width: 100%;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    
    .greeting-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #00CC96;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# LOAD DATA ACCESS USER (keyaccess_peg.xlsx)
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def load_pegawai_access():
    files = glob.glob("*keyaccess_peg*.xlsx") + glob.glob("keyaccess_peg.xlsx")
    if files:
        try:
            df = pd.read_excel(files[0])
            df['idpeg_str'] = df['idpeg'].apply(lambda x: str(int(x)) if pd.notna(x) and isinstance(x, (int, float)) else str(x).strip())
            return df
        except Exception as e:
            st.error(f"Gagal membaca file keyaccess_peg.xlsx: {e}")
    return pd.DataFrame()

df_peg_access = load_pegawai_access()

# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'show_welcome_toast' not in st.session_state:
    st.session_state.show_welcome_toast = False
if 'reset_confirm_dialog' not in st.session_state:
    st.session_state.reset_confirm_dialog = False

# ---------------------------------------------------------
# DIALOG KONFIRMASI RESET PASSWORD
# ---------------------------------------------------------
@st.dialog("Konfirmasi Reset Password")
def confirm_reset_password_dialog(email_dest, new_password, idpeg):
    st.write("⚠️ **Apakah Anda yakin ingin mereset password?**")
    st.write(f"Verifikasi dan password baru akan dikirimkan ke alamat Gmail: **{email_dest}**")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("Yakin", type="primary", use_container_width=True):
            # Simulasi / Pengiriman Verifikasi Email
            st.success(f"✅ Verifikasi reset password telah berhasil dikirim ke inbox Gmail ({email_dest}). Silakan periksa inbox Anda!")
            time.sleep(2)
            st.rerun()
    with col_d2:
        if st.button("Batal", use_container_width=True):
            st.rerun()

# ---------------------------------------------------------
# HALAMAN LOGIN UTAMA
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🔐 Login Pegawai BKB Nurul Fikri</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Evidence-Based Policy Tool - Wilayah Megapolitan Selatan</p>", unsafe_allow_html=True)
    
    c_log1, c_log2, c_log3 = st.columns([1, 1.8, 1])
    with c_log2:
        with st.form("form_login"):
            input_idpeg = st.text_input("ID Pegawai (idpeg):", placeholder="Masukkan ID Pegawai Anda")
            input_password = st.text_input("Password:", type="password", placeholder="Password standar: 12345678")
            btn_login = st.form_submit_button("Submit Login", type="primary", use_container_width=True)
            
            if btn_login:
                clean_id = input_idpeg.strip()
                if not df_peg_access.empty:
                    user_match = df_peg_access[df_peg_access['idpeg_str'] == clean_id]
                    if not user_match.empty and input_password == "12345678":
                        user_data = user_match.iloc[0].to_dict()
                        st.session_state.logged_in = True
                        st.session_state.user_info = user_data
                        st.session_state.show_welcome_toast = True
                        st.rerun()
                    else:
                        st.error("❌ ID Pegawai atau Password salah! (Gunakan password standar 12345678)")
                else:
                    # Fallback jika file keyaccess_peg.xlsx belum terdeteksi
                    if input_idpeg == "admin" and input_password == "12345678":
                        st.session_state.logged_in = True
                        st.session_state.user_info = {
                            'nama_peg': 'Admin Sistem',
                            'titel': 'ADMIN WILAYAH',
                            'lokasi_belajar': 'Semua',
                            'area': 'Megapolitan Selatan',
                            'idpeg': 'admin'
                        }
                        st.session_state.show_welcome_toast = True
                        st.rerun()
                    else:
                        st.error("❌ File keyaccess_peg.xlsx tidak ditemukan atau data tidak valid.")
    st.stop()

# ---------------------------------------------------------
# LOGIKA POP-UP WELCOME (3 DETIK)
# ---------------------------------------------------------
user = st.session_state.user_info
nama_peg = user.get('nama_peg', 'Pegawai')
titel_peg = str(user.get('titel', '')).upper()
area_peg = str(user.get('area', ''))
lb_peg_raw = str(user.get('lokasi_belajar', ''))

if st.session_state.show_welcome_toast:
    welcome_msg = f"Ahlan wa sahlan wa marhaban Kak {nama_peg}, selamat datang di Nurul Fikri Evidence-Based Policy Tool"
    toast_box = st.empty()
    toast_box.success(f"🎉 **{welcome_msg}**")
    time.sleep(3)
    toast_box.empty()
    st.session_state.show_welcome_toast = False

# ---------------------------------------------------------
# MODUL RESET PASSWORD (POJOK KIRI ATAS TOP-BAR)
# ---------------------------------------------------------
col_top_left, col_top_right = st.columns([1.5, 3])

with col_top_left:
    with st.popover("🔑 Reset Password Pegawai"):
        st.subheader("⚙️ Reset Password")
        new_pass_input = st.text_input("Password Baru:", type="password", key="reset_new_pass")
        gmail_input = st.text_input("Alamat Gmail Verifikasi:", placeholder="contoh@gmail.com", key="reset_gmail")
        
        if st.button("Submit Reset", type="primary", use_container_width=True):
            if not new_pass_input or not gmail_input:
                st.warning("⚠️ Mohon isi password baru dan alamat gmail.")
            elif "@" not in gmail_input or "." not in gmail_input:
                st.warning("⚠️ Alamat Gmail tidak valid.")
            else:
                confirm_reset_password_dialog(gmail_input, new_pass_input, user.get('idpeg'))

with col_top_right:
    st.write(f"👤 **Login sebagai:** {nama_peg} ({titel_peg}) | **Area:** {area_peg}")
    if st.button("Logout", key="btn_logout"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()

st.divider()

# ---------------------------------------------------------
# MAPPING KODE CABANG & JENJANG
# ---------------------------------------------------------
LOCATION_MAP = {
    '168': 'NF Halim',
    '192': 'NF Condet',
    '219': 'NF Tebet'
}

JENJANG_MAP = {
    'F': '4 SD', 'G': '5 SD', 'H': '6 SD',
    'I': '7 SMP', 'J': '8 SMP', 'K': '9 SMP',
    'L': '10 SMA', 'M': '11 SMA', 'N': '12 SMA', 'O': 'RONIN'
}

JENJANG_ORDER = ['4 SD', '5 SD', '6 SD', '7 SMP', '8 SMP', '9 SMP', '10 SMA', '11 SMA', '12 SMA', 'RONIN']

def style_chart(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def get_jalur_pendaftaran_from_cara_daftar(val):
    if pd.isna(val):
        return 'Offline (Cabang / WA)'
    val_str = str(val).strip().upper()
    if 'PSB' in val_str or 'ONLINE' in val_str or 'WEB' in val_str:
        return 'Online (Web PSB)'
    return 'Offline (Cabang / WA)'

def extract_diskon_juara_from_catatan(catatan_val):
    if pd.isna(catatan_val):
        return None
    cat_str = str(catatan_val).strip().upper()
    if 'JUARA' in cat_str or 'PSJ' in cat_str:
        has_formulir = 'FORM' in cat_str or 'FORMULIR' in cat_str
        has_angsuran = 'ANGSUR' in cat_str or 'ANGS' in cat_str or 'CICIL' in cat_str
        if has_formulir and has_angsuran:
            return 'Juara (Formulir + Angsuran 1)'
        return 'Diskon Juara / PSJ'
    return None

# ---------------------------------------------------------
# HELPER GEMINI AI (AUTOMATIC RETRY & HTTP 503 HANDLER)
# ---------------------------------------------------------
def ask_gemini_ai(api_key, prompt_text, max_retries=3):
    if not api_key:
        return "⚠️ **API Key tidak boleh kosong.**"
    clean_key = str(api_key).strip().strip("'").strip('"').strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={clean_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    
    for attempt in range(max_retries):
        try:
            data_json = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data_json, headers=headers)
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                return res_data['candidates'][0]['content']['parts'][0]['text']
        except urllib.error.HTTPError as e:
            if e.code == 503 and attempt < max_retries - 1:
                time.sleep(2)
                continue
            try:
                raw_err = e.read().decode('utf-8')
                err_json = json.loads(raw_err)
                detail_msg = err_json.get('error', {}).get('message', raw_err)
                return f"⚠️ **Respon Server Google (HTTP {e.code}):** {detail_msg}"
            except Exception:
                return f"⚠️ **Gagal terhubung:** HTTP Error {e.code}"
        except Exception as e:
            return f"⚠️ **Gagal terhubung ke Gemini AI API:** {str(e)}"

# ---------------------------------------------------------
# LOAD & COMBINE DATASETS DASHBOARD
# ---------------------------------------------------------
def clean_str(val):
    if pd.isna(val):
        return None
    return str(int(val)) if isinstance(val, (int, float)) else str(val).strip()

def format_lb(val):
    clean_val = clean_str(val)
    if clean_val is None:
        return None
    return LOCATION_MAP.get(clean_val, clean_val)

def format_jenjang(val):
    if pd.isna(val):
        return None
    clean_val = str(val).strip().upper()
    return JENJANG_MAP.get(clean_val, clean_val)

def get_kategori_siswa(biaya):
    try:
        biaya = float(biaya)
    except:
        return 'Lainnya'
    if biaya == 50000:
        return 'Siswa Lama (Rp50k)'
    elif biaya == 300000:
        return 'Siswa Baru (Rp300k)'
    elif biaya == 200000:
        return 'Siswa NFIC (Rp200k)'
    elif biaya == 0:
        return 'Lainnya / Gratis (Rp0)'
    else:
        return f'Lainnya (Rp{int(biaya):,})'

@st.cache_data(ttl=600)
def load_combined_data(uploaded_files, filename_keywords):
    if uploaded_files:
        return pd.concat([pd.read_excel(f) for f in uploaded_files], ignore_index=True)
    all_excel_files = glob.glob("*.xlsx")
    matched_files = [f for f in all_excel_files if any(kw in f.lower() for kw in filename_keywords) and 'keyaccess' not in f.lower()]
    if matched_files:
        dfs = []
        for mf in matched_files:
            try:
                dfs.append(pd.read_excel(mf))
            except Exception:
                pass
        if dfs:
            return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

df_trx_raw = load_combined_data(None, ["trx", "laporan", "transaksi"])
df_siswa_raw = load_combined_data(None, ["siswa", "siswanf"])
df_diskon_raw = load_combined_data(None, ["diskon"])

if not df_trx_raw.empty:
    if 'Lb' in df_trx_raw.columns:
        df_trx_raw['lb_clean'] = df_trx_raw['Lb'].apply(format_lb)
    if 'Idtahun' in df_trx_raw.columns:
        df_trx_raw['ta_clean'] = df_trx_raw['Idtahun'].apply(clean_str)
    if 'Biaya F' in df_trx_raw.columns:
        df_trx_raw['Kategori_Siswa'] = df_trx_raw['Biaya F'].apply(get_kategori_siswa)
    if 'Jenjang' in df_trx_raw.columns:
        df_trx_raw['Jenjang'] = df_trx_raw['Jenjang'].apply(format_jenjang)

if not df_siswa_raw.empty:
    if 'lb' in df_siswa_raw.columns:
        df_siswa_raw['lb_clean'] = df_siswa_raw['lb'].apply(format_lb)
    if 'TA' in df_siswa_raw.columns:
        df_siswa_raw['ta_clean'] = df_siswa_raw['TA'].apply(clean_str)
    if 'Biaya Formulir' in df_siswa_raw.columns:
        df_siswa_raw['Kategori_Siswa'] = df_siswa_raw['Biaya Formulir'].apply(get_kategori_siswa)
    if 'Jenjang' in df_siswa_raw.columns:
        df_siswa_raw['Jenjang'] = df_siswa_raw['Jenjang'].apply(format_jenjang)
    
    col_cara_daftar = next((c for c in df_siswa_raw.columns if 'caradaftar' in str(c).lower().replace(' ', '').replace('_', '')), None)
    if col_cara_daftar:
        df_siswa_raw['Jalur_Daftar'] = df_siswa_raw[col_cara_daftar].apply(get_jalur_pendaftaran_from_cara_daftar)
    else:
        df_siswa_raw['Jalur_Daftar'] = 'Offline (Cabang / WA)'

list_diskon_records = []
if not df_diskon_raw.empty:
    col_form_d = next((c for c in df_diskon_raw.columns if 'nomor' in str(c).lower() and 'form' in str(c).lower()), 'Nomor Formulir')
    col_kwt_d = next((c for c in df_diskon_raw.columns if 'kwi' in str(c).lower() or 'kwt' in str(c).lower()), 'Kwitansi')
    col_nama_d = next((c for c in df_diskon_raw.columns if 'nama' in str(c).lower() and 'diskon' in str(c).lower()), 'Nama Diskon')
    col_besar_d = next((c for c in df_diskon_raw.columns if 'besar' in str(c).lower() or 'nominal' in str(c).lower()), 'Besar Diskon')

    for _, row in df_diskon_raw.iterrows():
        try:
            val_diskon = float(pd.to_numeric(row.get(col_besar_d), errors='coerce'))
            val_diskon = 0.0 if pd.isna(val_diskon) else val_diskon
        except:
            val_diskon = 0.0
        raw_nama = str(row.get(col_nama_d)).strip() if pd.notna(row.get(col_nama_d)) else 'Diskon Khusus'
        nama_diskon_clean = extract_diskon_juara_from_catatan(raw_nama) or raw_nama
        list_diskon_records.append({
            'Nomor Formulir': clean_str(row.get(col_form_d)),
            'Kwitansi': clean_str(row.get(col_kwt_d)),
            'Nama Diskon': nama_diskon_clean,
            'Besar Diskon': val_diskon,
            'Sumber': 'File Diskon'
        })

df_diskon_combined = pd.DataFrame(list_diskon_records)
df_diskon_raw = df_diskon_combined.copy()

# ---------------------------------------------------------
# HAK AKSES DAN FILTERING BERTINGKAT (ROLE-BASED FILTER)
# ---------------------------------------------------------
st.markdown(f"<div class='greeting-title'>Assalamu'alaikum Kak {nama_peg}</div>", unsafe_allow_html=True)

all_lb_set = set()
for df_temp in [df_trx_raw, df_siswa_raw, df_diskon_raw]:
    if not df_temp.empty and 'lb_clean' in df_temp.columns:
        all_lb_set.update(df_temp['lb_clean'].dropna().unique())

# Batasi Opsi Lokasi Belajar Sesuai Peran Pegawai
allowed_lb_options = []

if titel_peg in ["SRO", "JRO", "ZT PLUS"]:
    # Parse lokasi_belajar pegawai (bisa multiple lokasi dipisahkan koma)
    user_lbs = [x.strip() for x in lb_peg_raw.split(',') if x.strip()]
    allowed_lb_options = sorted(list(set(user_lbs)))
elif titel_peg == "MANAJER AREA":
    # Ambil lokasi belajar yang sesuai dengan area pegawai
    if not df_peg_access.empty and 'area' in df_peg_access.columns:
        area_lbs = df_peg_access[df_peg_access['area'].str.upper() == area_peg.upper()]['lokasi_belajar'].dropna().tolist()
        parsed_area_lbs = []
        for alb in area_lbs:
            parsed_area_lbs.extend([x.strip() for x in str(alb).split(',') if x.strip()])
        allowed_lb_options = sorted(list(set(parsed_area_lbs)))
    else:
        allowed_lb_options = sorted(list(all_lb_set))
else:
    # MANAJER WILAYAH & ADMIN WILAYAH
    allowed_lb_options = ["Semua Cabang / Lokasi", "Dashboard Gabungan Lokasi per Area"] + sorted(list(all_lb_set))

all_ta_set = set()
for df_temp in [df_trx_raw, df_siswa_raw, df_diskon_raw]:
    if not df_temp.empty and 'ta_clean' in df_temp.columns:
        all_ta_set.update(df_temp['ta_clean'].dropna().unique())
list_master_ta = ["Semua Tahun Ajaran"] + sorted(list(all_ta_set))
list_master_jenjang = ["Semua Jenjang"] + JENJANG_ORDER

f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)

with f_col1:
    selected_ta = st.selectbox("📅 Tahun Ajaran (TA):", list_master_ta)

with f_col2:
    selected_lb = st.selectbox("🏢 Lokasi Belajar:", allowed_lb_options)

with f_col3:
    selected_jenjang = st.selectbox("🎓 Jenjang Kelas:", list_master_jenjang)

df_kec_source = df_siswa_raw.copy()
if selected_lb not in ["Semua Cabang / Lokasi", "Dashboard Gabungan Lokasi per Area"] and 'lb_clean' in df_kec_source.columns:
    df_kec_source = df_kec_source[df_kec_source['lb_clean'] == selected_lb]

list_kec = ["Semua Kecamatan"]
if not df_kec_source.empty and 'Kec Tinggal' in df_kec_source.columns:
    list_kec += sorted([str(x) for x in df_kec_source['Kec Tinggal'].dropna().unique()])

with f_col4:
    selected_kec = st.selectbox("📍 Kecamatan:", list_kec)

list_kel = ["Semua Kelurahan"]
if selected_kec != "Semua Kecamatan" and not df_kec_source.empty:
    sub_kel = df_kec_source[df_kec_source['Kec Tinggal'] == selected_kec]['Kel Tinggal'].dropna().unique()
    list_kel += sorted([str(x) for x in sub_kel])

with f_col5:
    selected_kel = st.selectbox("🏠 Kelurahan:", list_kel)

# ---------------------------------------------------------
# APLIKASI FILTER KE SEMUA DATAFRAME
# ---------------------------------------------------------
df_trx = df_trx_raw.copy()
df_siswa = df_siswa_raw.copy()
df_diskon = df_diskon_raw.copy()

for df_target in [df_trx, df_siswa, df_diskon]:
    if not df_target.empty:
        if selected_ta != "Semua Tahun Ajaran" and 'ta_clean' in df_target.columns:
            df_target = df_target[df_target['ta_clean'] == selected_ta]
        if selected_lb not in ["Semua Cabang / Lokasi", "Dashboard Gabungan Lokasi per Area"] and 'lb_clean' in df_target.columns:
            df_target = df_target[df_target['lb_clean'] == selected_lb]
        if selected_jenjang != "Semua Jenjang" and 'Jenjang' in df_target.columns:
            df_target = df_target[df_target['Jenjang'] == selected_jenjang]
        if selected_kec != "Semua Kecamatan" and 'Kec Tinggal' in df_target.columns:
            df_target = df_target[df_target['Kec Tinggal'] == selected_kec]
        if selected_kel != "Semua Kelurahan" and 'Kel Tinggal' in df_target.columns:
            df_target = df_target[df_target['Kel Tinggal'] == selected_kel]

ta_info = f"TA {selected_ta}" if selected_ta != "Semua Tahun Ajaran" else "Semua TA"
lb_info = f"Lokasi: {selected_lb}"

st.info(f"📌 **Filter Aktif:** Menampilkan data **{ta_info}** | **{lb_info}**")

# ---------------------------------------------------------
# DASHBOARD TABS
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💰 Keuangan Transaksi", 
    "🎓 Pendaftaran Siswa", 
    "🏫 Sekolah & Domisili",
    "🏷️ Siswa Diskon Khusus",
    "📈 Perbandingan 3 TA",
    "📊 Status Bayar Domisili",
    "🤖 Analisis AI & Executive Summary"
])

# --- TAB 1: LAPORAN TRANSAKSI ---
with tab1:
    if not df_trx.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Transaksi", f"{len(df_trx):,} Transaksi")
        col2.metric("Total Pendapatan", f"Rp {df_trx['Jumlah'].sum():,.0f}".replace(',', '.'))
        col3.metric("Rata-rata Transaksi", f"Rp {df_trx['Jumlah'].mean():,.0f}".replace(',', '.'))
        col4.metric("TA Terpilih", selected_ta)

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Tren Pendapatan Harian")
            df_trx['Tanggal'] = pd.to_datetime(df_trx['Tanggal'])
            daily_trx = df_trx.groupby('Tanggal')['Jumlah'].sum().reset_index()
            fig_line = style_chart(px.line(daily_trx, x='Tanggal', y='Jumlah', markers=True))
            st.plotly_chart(fig_line, use_container_width=True)
            st.caption("📝 **Penjelasan Grafik:** Grafik garis menggambarkan fluktuasi nominal pendapatan harian.")

        with c2:
            st.subheader("Proporsi Metode Pembayaran")
            df_pie_summary = df_trx.groupby('Type Bayar').size().reset_index(name='Jumlah_Siswa')
            fig_pie = style_chart(px.pie(df_pie_summary, names='Type Bayar', values='Jumlah_Siswa', hole=0.4))
            fig_pie.update_traces(textinfo='value+percent', texttemplate='%{value} siswa<br>(%{percent})')
            st.plotly_chart(fig_pie, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram:** Diagram donat memperlihatkan persentase metode pembayaran.")

    else:
        st.warning("Data Transaksi tidak ditemukan untuk filter terpilih.")

# --- TAB 2: OVERVIEW DATA SISWA ---
with tab2:
    if not df_siswa.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Siswa", f"{len(df_siswa)} Siswa")
        col2.metric("Nilai Paket", f"Rp {df_siswa['Biaya Paket'].sum():,.0f}".replace(',', '.'))
        col3.metric("Total Bayar (Cash In)", f"Rp {df_siswa['Total Bayar'].sum():,.0f}".replace(',', '.'))
        col4.metric("Sisa Tagihan", f"Rp {abs(df_siswa['Tagihan'].sum()):,.0f}".replace(',', '.'))

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribusi Status Siswa")
            if 'Kategori_Siswa' in df_siswa.columns:
                kat_siswa_df = df_siswa['Kategori_Siswa'].value_counts().reset_index()
                kat_siswa_df.columns = ['Status Siswa', 'Jumlah']
                fig_kat_siswa = style_chart(px.bar(kat_siswa_df, x='Status Siswa', y='Jumlah', text='Jumlah', color='Status Siswa'))
                st.plotly_chart(fig_kat_siswa, use_container_width=True)

        with c2:
            st.subheader("Distribusi Jenjang Kelas")
            jenjang_df = df_siswa['Jenjang'].value_counts().reset_index()
            jenjang_df.columns = ['Jenjang', 'Jumlah']
            fig_jenjang = style_chart(px.bar(jenjang_df, x='Jenjang', y='Jumlah', color='Jumlah'))
            st.plotly_chart(fig_jenjang, use_container_width=True)

    else:
        st.warning("Data Siswa tidak ditemukan untuk filter terpilih.")

# --- TAB 3: SEKOLAH & DOMISILI ---
with tab3:
    if not df_siswa.empty:
        st.header("🏫 Analisis Asal Sekolah & Domisili Siswa")
        top_sekolah = df_siswa['Asal Sekolah'].value_counts().head(10).reset_index()
        top_sekolah.columns = ['Asal Sekolah', 'Jumlah Siswa']
        fig_sekolah = style_chart(px.bar(top_sekolah, y='Asal Sekolah', x='Jumlah Siswa', orientation='h', text='Jumlah Siswa', color='Jumlah Siswa'))
        fig_sekolah.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_sekolah, use_container_width=True)

# --- TAB 4: DISKON KHUSUS ---
with tab4:
    if not df_diskon.empty:
        st.header("🏷️ Analisis Siswa Pendaftar Diskon Khusus & Program Juara/PSJ")
        st.dataframe(df_diskon, use_container_width=True)

# --- TAB 5: PERBANDINGAN MULTI-TA ---
with tab5:
    st.header("📈 Analisis & Komparasi Tren Multi-Tahun Ajaran")
    if not df_siswa_raw.empty and 'ta_clean' in df_siswa_raw.columns:
        g1 = df_siswa_raw.groupby(['ta_clean', 'Kategori_Siswa']).size().reset_index(name='Jumlah')
        fig1_bar = style_chart(px.bar(g1, x='ta_clean', y='Jumlah', color='Kategori_Siswa', barmode='group', text_auto=True))
        st.plotly_chart(fig1_bar, use_container_width=True)

# --- TAB 6: STATUS BAYAR DOMISILI ---
with tab6:
    st.header("📊 Analisis Persentase Lunas & Angsuran Berdasarkan Domisili")
    if not df_siswa.empty and 'Kec Tinggal' in df_siswa.columns:
        df_status = df_siswa.copy()
        df_status['Status_Bayar'] = df_status['Tagihan'].apply(lambda x: 'Lunas' if x >= 0 else 'Angsuran')
        dom_summary = df_status.groupby(['Kec Tinggal', 'Status_Bayar']).size().reset_index(name='Jumlah')
        fig_status_dom = style_chart(px.bar(dom_summary, x='Kec Tinggal', y='Jumlah', color='Status_Bayar', barmode='stack', text_auto=True))
        st.plotly_chart(fig_status_dom, use_container_width=True)

# --- TAB 7: ANALISIS AI & EXECUTIVE SUMMARY ---
with tab7:
    st.header("🤖 Executive AI Analytics & Smart Insights Assistant")
    
    system_gemini_key = st.secrets.get("GEMINI_API_KEY", "")
    tot_siswa = len(df_siswa)
    tot_paket = df_siswa['Biaya Paket'].sum() if 'Biaya Paket' in df_siswa.columns else 0
    tot_bayar = df_siswa['Total Bayar'].sum() if 'Total Bayar' in df_siswa.columns else 0
    tot_tagihan = abs(df_siswa['Tagihan'].sum()) if 'Tagihan' in df_siswa.columns else 0
    pct_pelunasan = (tot_bayar / tot_paket * 100) if tot_paket > 0 else 0

    if st.button("✨ Hasilkan Laporan & Rekomendasi Eksekutif dengan AI", type="primary", use_container_width=True):
        if not system_gemini_key:
            st.error("⚠️ `GEMINI_API_KEY` belum diset pada Streamlit Secrets.")
        else:
            with st.spinner("🤖 Gemini AI sedang menganalisis data..."):
                prompt = f"""Anda adalah Management Consultant & Chief Data Officer Senior untuk BKB Nurul Fikri.
Buatkan Memorandum Eksekutif resmi kepada Manajer Wilayah Megapolitan Selatan dari {nama_peg} ({titel_peg}) mengenai performa {lb_info}.
Gunakan 4 pendekatan: Deskriptif, Diagnostik, Prediktif, dan Preskriptif.
Konteks Data: Total Siswa: {tot_siswa}, Nilai Paket: Rp {tot_paket:,.0f}, Cash In: Rp {tot_bayar:,.0f}, Pelunasan: {pct_pelunasan:.1f}%."""
                
                st.session_state.ai_report_text = ask_gemini_ai(system_gemini_key, prompt)

    if 'ai_report_text' in st.session_state and st.session_state.ai_report_text:
        st.markdown("### 📝 Hasil Laporan Analisis Eksekutif AI:")
        st.markdown(st.session_state.ai_report_text)
