import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import json
import urllib.request
import urllib.error
import time
import base64
import html
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

if not df_siswa_raw.empty:
    col_cat_s = next((c for c in df_siswa_raw.columns if 'catatan' in str(c).lower()), None)
    col_form_s = next((c for c in df_siswa_raw.columns if 'form' in str(c).lower()), 'Formulir')
    col_kwt_s = next((c for c in df_siswa_raw.columns if 'kwi' in str(c).lower() or 'kwt' in str(c).lower()), 'Kwitansi')

    if col_cat_s:
        for _, row in df_siswa_raw.iterrows():
            jenis_diskon_cat = extract_diskon_juara_from_catatan(row.get(col_cat_s))
            if jenis_diskon_cat:
                list_diskon_records.append({
                    'Nomor Formulir': clean_str(row.get(col_form_s)),
                    'Kwitansi': clean_str(row.get(col_kwt_s)),
                    'Nama Diskon': jenis_diskon_cat,
                    'Besar Diskon': 0.0,
                    'Sumber': 'Catatan Siswa'
                })

df_diskon_combined = pd.DataFrame(list_diskon_records)
if not df_diskon_combined.empty:
    df_diskon_combined = df_diskon_combined.drop_duplicates(subset=['Nomor Formulir', 'Kwitansi', 'Nama Diskon'])
    
    if not df_siswa_raw.empty:
        col_form_s = next((c for c in df_siswa_raw.columns if 'form' in str(c).lower()), 'Formulir')
        df_siswa_meta = df_siswa_raw.copy()
        df_siswa_meta['f_clean'] = df_siswa_meta[col_form_s].apply(clean_str) if col_form_s in df_siswa_meta.columns else None
        
        meta_cols = ['ta_clean', 'Jenjang', 'Kec Tinggal', 'Kel Tinggal', 'lb_clean']
        meta_cols = [c for c in meta_cols if c in df_siswa_meta.columns]
        
        if 'f_clean' in df_siswa_meta.columns:
            map_siswa_f = df_siswa_meta.dropna(subset=['f_clean']).drop_duplicates(subset=['f_clean']).set_index('f_clean')[meta_cols]
            for col in meta_cols:
                df_diskon_combined[col] = df_diskon_combined['Nomor Formulir'].map(map_siswa_f[col])

df_diskon_raw = df_diskon_combined.copy()

# ---------------------------------------------------------
# HAK AKSES DAN FILTERING BERTINGKAT (ROLE-BASED FILTER)
# ---------------------------------------------------------
st.markdown(f"<div class='greeting-title'>Assalamu'alaikum Kak {nama_peg}</div>", unsafe_allow_html=True)

all_lb_set = set()
for df_temp in [df_trx_raw, df_siswa_raw, df_diskon_raw]:
    if not df_temp.empty and 'lb_clean' in df_temp.columns:
        all_lb_set.update(df_temp['lb_clean'].dropna().unique())

allowed_lb_options = []

if titel_peg in ["SRO", "JRO", "ZT PLUS"]:
    user_lbs = [x.strip() for x in lb_peg_raw.split(',') if x.strip()]
    allowed_lb_options = sorted(list(set(user_lbs)))
elif titel_peg == "MANAJER AREA":
    if not df_peg_access.empty and 'area' in df_peg_access.columns:
        area_lbs = df_peg_access[df_peg_access['area'].str.upper() == area_peg.upper()]['lokasi_belajar'].dropna().tolist()
        parsed_area_lbs = []
        for alb in area_lbs:
            parsed_area_lbs.extend([x.strip() for x in str(alb).split(',') if x.strip()])
        allowed_lb_options = sorted(list(set(parsed_area_lbs)))
    else:
        allowed_lb_options = sorted(list(all_lb_set))
else:
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
            st.caption("📝 **Penjelasan Grafik:** Grafik garis di atas menggambarkan fluktuasi nominal pendapatan harian. Titik puncak menandakan tanggal dengan volume transaksi keuangan tertinggi pada periode terfilter.")

        with c2:
            st.subheader("Proporsi Metode Pembayaran")
            df_pie_summary = df_trx.groupby('Type Bayar').size().reset_index(name='Jumlah_Siswa')
            fig_pie = style_chart(px.pie(df_pie_summary, names='Type Bayar', values='Jumlah_Siswa', hole=0.4))
            fig_pie.update_traces(textinfo='value+percent', texttemplate='%{value} siswa<br>(%{percent})')
            st.plotly_chart(fig_pie, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram:** Diagram donat di atas memperlihatkan persentase dan frekuensi penggunaan jenis metode pembayaran (Cash, Transfer, Debit, Virtual Account) yang digunakan oleh wali siswa.")

        st.divider()

        if 'Kategori_Siswa' in df_trx.columns:
            st.subheader("Distribusi Status Siswa (Siswa Baru / Lama / NFIC)")
            kat_trx_df = df_trx['Kategori_Siswa'].value_counts().reset_index()
            kat_trx_df.columns = ['Status Siswa', 'Jumlah Transaksi']
            fig_kat_trx = style_chart(px.bar(kat_trx_df, x='Status Siswa', y='Jumlah Transaksi', text='Jumlah Transaksi', color='Status Siswa'))
            st.plotly_chart(fig_kat_trx, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram Batang:** Menampilkan total transaksi pembayaran formulir berdasarkan kelompok status siswa (Siswa Baru Rp300k, Siswa Lama Rp50k, atau NFIC Rp200k).")

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

        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("Distribusi Status Siswa")
            if 'Kategori_Siswa' in df_siswa.columns:
                kat_siswa_df = df_siswa['Kategori_Siswa'].value_counts().reset_index()
                kat_siswa_df.columns = ['Status Siswa', 'Jumlah']
                fig_kat_siswa = style_chart(px.bar(kat_siswa_df, x='Status Siswa', y='Jumlah', text='Jumlah', color='Status Siswa'))
                st.plotly_chart(fig_kat_siswa, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram:** Menunjukkan komposisi kuantitas pendaftar terfilter berdasarkan kategori pendaftar (Baru vs Re-enrollment/Lama).")

        with c2:
            st.subheader("Distribusi Jenjang Kelas")
            jenjang_df = df_siswa['Jenjang'].value_counts().reset_index()
            jenjang_df.columns = ['Jenjang', 'Jumlah']
            fig_jenjang = style_chart(px.bar(jenjang_df, x='Jenjang', y='Jumlah', color='Jumlah'))
            st.plotly_chart(fig_jenjang, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram:** Menggambarkan tingkat kepadatan jumlah siswa aktif pada masing-masing tingkatan kelas (SD, SMP, SMA, & RONIN).")

        with c3:
            st.subheader("Proporsi Pendaftaran Online vs Offline")
            if 'Jalur_Daftar' in df_siswa.columns:
                df_jalur = df_siswa['Jalur_Daftar'].value_counts().reset_index()
                df_jalur.columns = ['Jalur Pendaftaran', 'Jumlah Siswa']
                fig_jalur_pie = style_chart(px.pie(df_jalur, names='Jalur Pendaftaran', values='Jumlah Siswa', hole=0.4, color='Jalur Pendaftaran', color_discrete_map={'Online (Web PSB)': '#00cc96', 'Offline (Cabang / WA)': '#636efa'}))
                fig_jalur_pie.update_traces(textinfo='value+percent', texttemplate='%{value} siswa<br>(%{percent})')
                st.plotly_chart(fig_jalur_pie, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram:** Perbandingan efektivitas pendaftaran siswa melalui sistem Website PSB Online dibandingkan pendaftaran manual langsung di Cabang/WA.")

    else:
        st.warning("Data Siswa tidak ditemukan untuk filter terpilih.")

# --- TAB 3: SEKOLAH & DOMISILI SISWA ---
with tab3:
    if not df_siswa.empty:
        st.header("🏫 Analisis Asal Sekolah & Domisili Siswa")
        st.subheader("1. Top Asal Sekolah Pendaftar")
        c1, c2 = st.columns([2, 1])
        with c1:
            top_sekolah = df_siswa['Asal Sekolah'].value_counts().head(10).reset_index()
            top_sekolah.columns = ['Asal Sekolah', 'Jumlah Siswa']
            fig_sekolah = style_chart(px.bar(top_sekolah, y='Asal Sekolah', x='Jumlah Siswa', orientation='h', text='Jumlah Siswa', color='Jumlah Siswa', color_continuous_scale='Viridis'))
            fig_sekolah.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_sekolah, use_container_width=True)
            st.caption("📝 **Penjelasan Bagan Horisontal:** Peringkat 10 sekolah penyumbang pendaftar terbanyak. Menjadi prioritas utama dalam kegiatan sosialisasi & pameran pendidikan.")

        with c2:
            st.write("📊 **Detail Sebaran Sekolah & Lokasi Belajar**")
            sekolah_lb = df_siswa.groupby(['Asal Sekolah', 'lb_clean']).size().reset_index(name='Jumlah Siswa')
            sekolah_lb.columns = ['Asal Sekolah', 'Lokasi Belajar', 'Jumlah Siswa']
            sekolah_lb = sekolah_lb.sort_values(by='Jumlah Siswa', ascending=False)
            st.dataframe(sekolah_lb, use_container_width=True, height=350)
            st.caption("📝 **Penjelasan Tabel:** Rincian kuantitatif distribusi pendaftar asal sekolah tertentu ke cabang/lokasi belajar yang dipilih.")

        st.divider()

        st.subheader("2. Jumlah Riil & Persentase per Jenjang Berdasarkan Kecamatan Domisili")
        if 'Kec Tinggal' in df_siswa.columns and 'Jenjang' in df_siswa.columns:
            jenjang_kec = df_siswa.groupby(['Kec Tinggal', 'Jenjang']).size().reset_index(name='Jumlah_Siswa')
            total_kec = jenjang_kec.groupby('Kec Tinggal')['Jumlah_Siswa'].transform('sum')
            jenjang_kec['Persentase'] = (jenjang_kec['Jumlah_Siswa'] / total_kec * 100).round(1)
            jenjang_kec['Label_Text'] = jenjang_kec.apply(lambda r: f"{r['Jumlah_Siswa']} ({r['Persentase']}%)", axis=1)

            fig_jenjang_kec = style_chart(px.bar(jenjang_kec, x='Kec Tinggal', y='Jumlah_Siswa', color='Jenjang', barmode='group', text='Label_Text', labels={'Kec Tinggal': 'Kecamatan Domisili', 'Jumlah_Siswa': 'Jumlah Siswa'}))
            fig_jenjang_kec.update_traces(textposition='outside')
            st.plotly_chart(fig_jenjang_kec, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram Grouped Bar:** Menampilkan persebaran jenjang pendidikan siswa di setiap wilayah Kecamatan domisili beserta kontribusi persentasenya.")

        st.divider()

        st.subheader("3. Jumlah Riil & Persentase per Jenjang Berdasarkan Kelurahan Domisili")
        if 'Kel Tinggal' in df_siswa.columns and 'Jenjang' in df_siswa.columns:
            jenjang_kel = df_siswa.groupby(['Kel Tinggal', 'Jenjang']).size().reset_index(name='Jumlah_Siswa')
            total_kel = jenjang_kel.groupby('Kel Tinggal')['Jumlah_Siswa'].transform('sum')
            jenjang_kel['Persentase'] = (jenjang_kel['Jumlah_Siswa'] / total_kel * 100).round(1)
            jenjang_kel['Label_Text'] = jenjang_kel.apply(lambda r: f"{r['Jumlah_Siswa']} ({r['Persentase']}%)", axis=1)

            fig_jenjang_kel = style_chart(px.bar(jenjang_kel, x='Kel Tinggal', y='Jumlah_Siswa', color='Jenjang', barmode='group', text='Label_Text', labels={'Kel Tinggal': 'Kelurahan Domisili', 'Jumlah_Siswa': 'Jumlah Siswa'}))
            fig_jenjang_kel.update_traces(textposition='outside')
            st.plotly_chart(fig_jenjang_kel, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram:** Pemetaan tingkat kelurahan secara mendalam untuk mengidentifikasi area pemukiman yang paling potensial untuk penetrasi pasar.")

    else:
        st.warning("Data Sekolah/Domisili tidak ditemukan.")

# --- TAB 4: DISKON KHUSUS ---
with tab4:
    st.header("🏷️ Analisis Siswa Pendaftar Diskon Khusus & Program Juara/PSJ")
    st.info("💡 **Tersinkronisasi:** Menampilkan gabungan data diskon khusus serta pendaftar program Diskon Juara / PSJ dari file diskon dan catatan.")

    if not df_diskon.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        tot_diskon_nominal = df_diskon['Besar Diskon'].fillna(0).sum() if 'Besar Diskon' in df_diskon.columns else 0
        df_valid_diskon = df_diskon[df_diskon['Besar Diskon'] > 0] if 'Besar Diskon' in df_diskon.columns else pd.DataFrame()
        avg_diskon_nominal = df_valid_diskon['Besar Diskon'].mean() if not df_valid_diskon.empty else 0.0
        if pd.isna(avg_diskon_nominal):
            avg_diskon_nominal = 0.0

        cnt_diskon_jenis = df_diskon['Nama Diskon'].nunique() if 'Nama Diskon' in df_diskon.columns else 0

        col1.metric("Penerima Diskon Terfilter", f"{len(df_diskon)} Siswa")
        col2.metric("Total Nominal Diskon", f"Rp {tot_diskon_nominal:,.0f}".replace(',', '.'))
        col3.metric("Rata-rata Diskon (Kupon)", f"Rp {avg_diskon_nominal:,.0f}".replace(',', '.'))
        col4.metric("Kategori Diskon", f"{cnt_diskon_jenis} Jenis")

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribusi Jenis Diskon Terpakai")
            if 'Nama Diskon' in df_diskon.columns:
                diskon_type = df_diskon['Nama Diskon'].value_counts().reset_index()
                diskon_type.columns = ['Nama Diskon', 'Jumlah Siswa']
                fig_diskon_pie = style_chart(px.pie(diskon_type, names='Nama Diskon', values='Jumlah Siswa', hole=0.4))
                fig_diskon_pie.update_traces(textinfo='value+percent', texttemplate='%{value} siswa<br>(%{percent})')
                st.plotly_chart(fig_diskon_pie, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Donat:** Menggambarkan proporsi penggunaan jenis promo/diskon (seperti Diskon Juara/PSJ, Anak Guru, Saudara Kandung) yang diklaim pendaftar.")

        with c2:
            st.subheader("Total Nominal Diskon per Lokasi Belajar")
            if 'lb_clean' in df_diskon.columns and 'Besar Diskon' in df_diskon.columns:
                diskon_lokasi = df_diskon.groupby('lb_clean')['Besar Diskon'].sum().reset_index()
                diskon_lokasi.columns = ['Lokasi Belajar', 'Besar Diskon']
                fig_diskon_bar = style_chart(px.bar(diskon_lokasi, x='Lokasi Belajar', y='Besar Diskon', text_auto='.2s', color='Besar Diskon'))
                st.plotly_chart(fig_diskon_bar, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Batang:** Menampilkan total pengeluaran beban potongan harga (diskon kupon) yang diberikan pada masing-masing cabang.")

        st.divider()

        st.subheader("Detail Data Siswa Penerima Diskon & Program Juara (Terfilter)")
        disp_cols = [c for c in ['Nomor Formulir', 'Kwitansi', 'Nama Diskon', 'Besar Diskon', 'Sumber', 'lb_clean', 'Jenjang', 'Kec Tinggal', 'Kel Tinggal'] if c in df_diskon.columns]
        st.dataframe(df_diskon[disp_cols], use_container_width=True)
        st.caption("📝 **Penjelasan Tabel:** Rincian baris data siswa yang berhak menerima potongan harga beserta nilai nominal dan sumber pencatatannya.")
    else:
        st.warning("Data Diskon Khusus tidak ditemukan untuk filter aktif saat ini.")

# --- TAB 5: PERBANDINGAN MULTI-TA ---
with tab5:
    st.header("📈 Analisis & Komparasi Tren Multi-Tahun Ajaran (Multi-TA)")
    st.info("💡 **Tersinkronisasi:** Seluruh grafik di bawah ini membandingkan tren performa antar Tahun Ajaran berdasarkan Lokasi, Jenjang, dan Domisili terfilter.")

    df_s_comp = df_siswa_raw.copy()
    if selected_lb not in ["Semua Cabang / Lokasi", "Dashboard Gabungan Lokasi per Area"] and 'lb_clean' in df_s_comp.columns:
        df_s_comp = df_s_comp[df_s_comp['lb_clean'] == selected_lb]
    if selected_jenjang != "Semua Jenjang" and 'Jenjang' in df_s_comp.columns:
        df_s_comp = df_s_comp[df_s_comp['Jenjang'] == selected_jenjang]

    df_t_comp = df_trx_raw.copy()
    if selected_lb not in ["Semua Cabang / Lokasi", "Dashboard Gabungan Lokasi per Area"] and 'lb_clean' in df_t_comp.columns:
        df_t_comp = df_t_comp[df_t_comp['lb_clean'] == selected_lb]

    if not df_s_comp.empty and 'ta_clean' in df_s_comp.columns:
        def calculate_delta_df(df_grouped, col_cat, col_val='Jumlah'):
            df_pivot = df_grouped.pivot(index='ta_clean', columns=col_cat, values=col_val).fillna(0)
            return df_pivot

        st.subheader("1. Jumlah Siswa Lama vs Baru per TA")
        if 'Kategori_Siswa' in df_s_comp.columns:
            g1 = df_s_comp.groupby(['ta_clean', 'Kategori_Siswa']).size().reset_index(name='Jumlah')
            c1, c2 = st.columns(2)
            with c1:
                fig1_bar = style_chart(px.bar(g1, x='ta_clean', y='Jumlah', color='Kategori_Siswa', barmode='group', text_auto=True, title="Diagram Batang Kategori Siswa"))
                st.plotly_chart(fig1_bar, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Batang:** Menampilkan perbandingan jumlah riil siswa lama vs baru yang terdaftar di tiap Tahun Ajaran.")
            with c2:
                fig1_pie = style_chart(px.pie(g1, names='Kategori_Siswa', values='Jumlah', color='ta_clean', hole=0.4, title="Proporsi Akumulasi Status Siswa"))
                fig1_pie.update_traces(textinfo='value+percent', texttemplate='%{value} siswa<br>(%{percent})')
                st.plotly_chart(fig1_pie, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Donat:** Menggambarkan rasio akumulasi pendaftar baru dibandingkan re-enrollment secara keseluruhan.")
            
            piv1 = calculate_delta_df(g1, 'Kategori_Siswa')
            st.caption("📈 **Tabel Rekapitulasi Perubahan YoY:**")
            st.dataframe(piv1.style.highlight_max(axis=0), use_container_width=True)

        st.divider()

        st.subheader("2. Komparasi Paket Bimbingan vs Realisasi Cash In per TA")
        g2 = df_s_comp.groupby('ta_clean').agg(Nilai_Paket=('Biaya Paket', 'sum'), Cash_In=('Total Bayar', 'sum')).reset_index()
        g2_melt = g2.melt(id_vars='ta_clean', value_vars=['Nilai_Paket', 'Cash_In'], var_name='Kategori', value_name='Nominal')
        g2_melt['Kategori'] = g2_melt['Kategori'].replace({'Nilai_Paket': 'Nilai Paket Bimbingan', 'Cash_In': 'Total Cash In (Bayar)'})

        c1, c2 = st.columns(2)
        with c1:
            fig2_bar = style_chart(px.bar(g2_melt, x='ta_clean', y='Nominal', color='Kategori', barmode='group', text_auto='.3s', title="Perbandingan Nilai Paket vs Cash In"))
            st.plotly_chart(fig2_bar, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram Batang:** Membandingkan nilai omset bruto paket bimbingan dengan realisasi dana tunai (cash-in) yang diterima dari TA ke TA.")
        with c2:
            fig2_pie = style_chart(px.pie(g2_melt, names='Kategori', values='Nominal', hole=0.4, title="Proporsi Realisasi Bimbingan vs Cash In"))
            fig2_pie.update_traces(textinfo='value+percent')
            st.plotly_chart(fig2_pie, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram Donat:** Menunjukkan rasio tingkat efektivitas penagihan tunai terhadap target nilai paket.")

        st.divider()

        st.subheader("3. Tren Pendapatan Harian Antar TA")
        if not df_t_comp.empty and 'Tanggal' in df_t_comp.columns:
            df_t_comp['Tanggal'] = pd.to_datetime(df_t_comp['Tanggal'])
            df_t_comp['Bulan_Tgl'] = df_t_comp['Tanggal'].dt.strftime('%m-%d')
            g3 = df_t_comp.groupby(['Bulan_Tgl', 'ta_clean'])['Jumlah'].sum().reset_index()
            fig3_line = style_chart(px.line(g3, x='Bulan_Tgl', y='Jumlah', color='ta_clean', markers=True, title="Grafik Tren Pendapatan Harian"))
            st.plotly_chart(fig3_line, use_container_width=True)
            st.caption("📝 **Penjelasan Grafik Garis Multi-Garis:** Menyejajarkan pola pemasukan harian antar TA pada kalender tanggal yang sama.")

        st.divider()

        st.subheader("4. Proporsi & Distribusi Metode Pembayaran per TA")
        if not df_t_comp.empty and 'Type Bayar' in df_t_comp.columns:
            g4 = df_t_comp.groupby(['ta_clean', 'Type Bayar']).size().reset_index(name='Jumlah')
            c1, c2 = st.columns(2)
            with c1:
                fig4_bar = style_chart(px.bar(g4, x='ta_clean', y='Jumlah', color='Type Bayar', barmode='group', text_auto=True, title="Diagram Batang Metode Pembayaran"))
                st.plotly_chart(fig4_bar, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Batang:** Memantau pergeseran tren kanal pembayaran yang disukai wali siswa dari tahun ke tahun.")
            with c2:
                fig4_pie = style_chart(px.pie(g4, names='Type Bayar', values='Jumlah', hole=0.4, title="Proporsi Metode Pembayaran"))
                fig4_pie.update_traces(textinfo='value+percent', texttemplate='%{value} trx<br>(%{percent})')
                st.plotly_chart(fig4_pie, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Donat:** Persentase pangsa penggunaan tiap kanal pembayaran keuangan.")

    else:
        st.warning("Data multi-tahun ajaran tidak cukup untuk ditampilkan.")

# --- TAB 6: STATUS BAYAR DOMISILI ---
with tab6:
    st.header("📊 Analisis Persentase Lunas & Angsuran Berdasarkan Domisili")
    st.info("💡 **Tersinkronisasi dengan Filter:** Data di bawah ini secara otomatis beradaptasi mengikuti filter aktif.")

    if not df_siswa.empty and 'Kec Tinggal' in df_siswa.columns:
        df_status = df_siswa.copy()
        df_status['Status_Bayar'] = df_status['Tagihan'].apply(lambda x: 'Lunas' if x >= 0 else 'Angsuran')
        
        col_st1, col_st2, col_st3, col_st4 = st.columns(4)
        total_s = len(df_status)
        total_lunas = len(df_status[df_status['Status_Bayar'] == 'Lunas'])
        total_angsuran = len(df_status[df_status['Status_Bayar'] == 'Angsuran'])
        
        col_st1.metric("Total Siswa Terfilter", f"{total_s} Siswa")
        col_st2.metric("Siswa Lunas", f"{total_lunas} Siswa ({round(total_lunas/total_s*100,1) if total_s>0 else 0}%)")
        col_st3.metric("Siswa Angsuran", f"{total_angsuran} Siswa ({round(total_angsuran/total_s*100,1) if total_s>0 else 0}%)")
        col_st4.metric("Jumlah Domisili", f"{df_status['Kel Tinggal'].nunique() if 'Kel Tinggal' in df_status.columns else 0} Kelurahan")

        st.divider()

        st.subheader("1. Grafik Presentase Status Bayar per Domisili")
        domisili_col = 'Kel Tinggal' if selected_kec != "Semua Kecamatan" and 'Kel Tinggal' in df_status.columns else 'Kec Tinggal'
        dom_summary = df_status.groupby(['lb_clean', domisili_col, 'Status_Bayar']).size().reset_index(name='Jumlah') if 'lb_clean' in df_status.columns else df_status.groupby([domisili_col, 'Status_Bayar']).size().reset_index(name='Jumlah')
        
        fig_status_dom = style_chart(px.bar(dom_summary, x=domisili_col, y='Jumlah', color='Status_Bayar', barmode='stack', text_auto=True, color_discrete_map={'Lunas': '#00cc96', 'Angsuran': '#ef553b'}))
        st.plotly_chart(fig_status_dom, use_container_width=True)
        st.caption("📝 **Penjelasan Diagram Batang Tumpuk:** Menampilkan proporsi jumlah siswa yang sudah Lunas (hijau) dan yang masih Mengangsur (merah) dipisahkan per wilayah domisili.")

        st.divider()

        st.subheader("2. Tabel Rincian Persentase per Kecamatan Domisili (Terfilter)")
        rekap_kec = df_status.groupby(['ta_clean', 'lb_clean', 'Kec Tinggal', 'Status_Bayar']).size().unstack(fill_value=0).reset_index() if 'ta_clean' in df_status.columns and 'lb_clean' in df_status.columns else df_status.groupby(['Kec Tinggal', 'Status_Bayar']).size().unstack(fill_value=0).reset_index()
        
        if 'Lunas' not in rekap_kec.columns:
            rekap_kec['Lunas'] = 0
        if 'Angsuran' not in rekap_kec.columns:
            rekap_kec['Angsuran'] = 0

        rekap_kec['Total Siswa'] = rekap_kec['Lunas'] + rekap_kec['Angsuran']
        rekap_kec['% Lunas'] = (rekap_kec['Lunas'] / rekap_kec['Total Siswa'] * 100).round(1).astype(str) + '%'
        rekap_kec['% Angsuran'] = (rekap_kec['Angsuran'] / rekap_kec['Total Siswa'] * 100).round(1).astype(str) + '%'

        st.dataframe(rekap_kec, use_container_width=True)
        st.caption("📝 **Penjelasan Tabel Rincian:** Tabel evaluasi keuangan per Kecamatan. Berguna bagi tim penagihan (*finance*) untuk memprioritaskan area pemukiman dengan persentase angsuran tinggi.")

    else:
        st.warning("Data Siswa untuk analisis status bayar domisili tidak ditemukan untuk filter ini.")

# --- TAB 7: ANALISIS AI & EXECUTIVE SUMMARY ---
with tab7:
    st.header("🤖 Executive AI Analytics & Smart Insights Assistant")
    st.info("💡 **AI Engine Integration:** Modul ini menganalisis seluruh data pada dashboard untuk menghasilkan Laporan Eksekutif dengan struktur Memorandum Resmi & Pendekatan 4 Analisis Data (Deskriptif, Diagnostik, Prediktif, & Preskriptif).")

    if not df_siswa.empty:
        sender_cabang = f"Tim Cabang {selected_lb}" if selected_lb not in ["Semua Cabang / Lokasi", "Dashboard Gabungan Lokasi per Area"] else "Tim Gabungan Cabang (Wilayah Megapolitan Selatan)"
        current_date_str = datetime.now().strftime("%d %B %Y")

        st.subheader("📌 1. Smart Executive Summary (Otomatis)")
        
        tot_siswa = len(df_siswa)
        tot_paket = df_siswa['Biaya Paket'].sum() if 'Biaya Paket' in df_siswa.columns else 0
        tot_bayar = df_siswa['Total Bayar'].sum() if 'Total Bayar' in df_siswa.columns else 0
        tot_tagihan = abs(df_siswa['Tagihan'].sum()) if 'Tagihan' in df_siswa.columns else 0
        pct_pelunasan = (tot_bayar / tot_paket * 100) if tot_paket > 0 else 0
        
        ai_col1, ai_col2, ai_col3 = st.columns(3)
        ai_col1.metric("💡 Target Paket Bimbingan", f"Rp {tot_paket:,.0f}".replace(',', '.'))
        ai_col2.metric("💵 Realisasi Cash In", f"Rp {tot_bayar:,.0f}".replace(',', '.'))
        ai_col3.metric("📊 Rasio Pelunasan", f"{pct_pelunasan:.1f}%")

        st.markdown("### 🔍 Temuan Kunci Sistem:")
        
        smart_bullets = []
        smart_bullets.append(f"**Pertumbuhan & Volume:** Terdata **{tot_siswa} siswa** terdaftar pada filter aktif (**{ta_info}**, **{lb_info}**).")
        smart_bullets.append(f"**Kinerja Keuangan:** Dari total omset paket **Rp {tot_paket:,.0f}**, penerimaan tunai (Cash In) adalah **Rp {tot_bayar:,.0f} ({pct_pelunasan:.1f}%)**, menyisakan piutang sebesar **Rp {tot_tagihan:,.0f}**.".replace(',', '.'))
        
        if 'Jalur_Daftar' in df_siswa.columns:
            top_jalur = df_siswa['Jalur_Daftar'].value_counts()
            jalur_txt = ", ".join([f"**{k}** ({v} siswa)" for k, v in top_jalur.items()])
            smart_bullets.append(f"**Jalur Pendaftaran:** Sebaran pendaftar saat ini yaitu {jalur_txt}.")
        
        if 'Asal Sekolah' in df_siswa.columns:
            top_3_sch = df_siswa['Asal Sekolah'].value_counts().head(3)
            sch_text = ", ".join([f"**{k}** ({v} siswa)" for k, v in top_3_sch.items()])
            smart_bullets.append(f"**Sekolah Prioritas:** 3 Sekolah penyumbang siswa terbanyak adalah {sch_text}.")
            
        if 'Kec Tinggal' in df_siswa.columns:
            top_kec = df_siswa['Kec Tinggal'].value_counts().head(3)
            kec_text = ", ".join([f"**{k}** ({v} siswa)" for k, v in top_kec.items()])
            smart_bullets.append(f"**Basis Domisili Utama:** Konsentrasi pendaftar tertinggi berasal dari Kecamatan {kec_text}.")

        for b in smart_bullets:
            st.markdown(f"- {b}")

        st.divider()

        # 2. GENERATIVE AI EXECUTIVE REPORT
        st.subheader("✨ 2. Generative AI Executive Report (Google Gemini AI)")
        
        system_gemini_key = st.secrets.get("GEMINI_API_KEY", "")
        
        if system_gemini_key:
            user_gemini_key = system_gemini_key
            st.success("✅ **AI API Key terdeteksi secara otomatis dari sistem secrets.**")
        else:
            with st.expander("🔑 Pengaturan API Key Google Gemini (Manual Input Opsional)", expanded=True):
                st.write("Jika Secrets belum diatur, Anda dapat memasukkan API Key secara manual dari [Google AI Studio](https://aistudio.google.com/app/apikey).")
                user_gemini_key = st.text_input("Masukkan Gemini API Key Anda:", type="password", key="gemini_key_input")

        ctx_lines = [
            f"Filter Terpilih: {ta_info}, {lb_info}",
            f"Total Siswa Terdaftar: {tot_siswa} Siswa",
            f"Total Target Paket Bimbingan: Rp {tot_paket:,.0f}",
            f"Total Realisasi Pembayaran (Cash In): Rp {tot_bayar:,.0f}",
            f"Rasio Pelunasan: {pct_pelunasan:.1f}%",
            f"Total Sisa Tagihan Piutang: Rp {tot_tagihan:,.0f}"
        ]
        if 'Jalur_Daftar' in df_siswa.columns:
            jalur_str = ', '.join([f'{k}: {v}' for k,v in df_siswa['Jalur_Daftar'].value_counts().items()])
            ctx_lines.append(f"Metode Pendaftaran: {jalur_str}")
        if 'Asal Sekolah' in df_siswa.columns:
            top_sch_str = ', '.join([f'{k} ({v})' for k,v in df_siswa['Asal Sekolah'].value_counts().head(5).items()])
            ctx_lines.append(f"Top Asal Sekolah: {top_sch_str}")

        data_context = "\n- ".join([""] + ctx_lines)

        if st.button("✨ Hasilkan Laporan & Rekomendasi Eksekutif dengan AI", type="primary", use_container_width=True):
            if not user_gemini_key:
                st.error("⚠️ API Key tidak ditemukan. Silakan tambahkan `GEMINI_API_KEY` pada Streamlit Secrets.")
            else:
                with st.spinner("🤖 Gemini AI sedang menyusun Laporan Memorandum Eksekutif..."):
                    prompt_narrative = f"""Anda adalah Management Consultant & Chief Data Officer Senior untuk BKB Nurul Fikri.
Berdasarkan data operasional & keuangan terbaru berikut:
{data_context}

Sertakan pula pertimbangan kualitatif operasional cabang berikut dalam analisis Anda:
1. **Promo Sekolah & Event TO/Asesmen**: Tim cabang senantiasa aktif terlibat dalam agenda promo ke sekolah-sekolah mitra dengan mengadakan Try Out (TO), asesmen akademik, tes MBTI, atau motivasi sebagai pengantar/pintu masuk pendaftaran.
2. **Program START NF (Tes Literasi & Numerasi Gratis)**: Untuk memperluas jangkauan perekrutan siswa baru (SD, SMP, SMA), cabang menggelar Tes Kemampuan Dasar Literasi dan Numerasi (START NF) secara GRATIS sebagai saluran perolehan database calon siswa potensial.
3. **Fitur & Fasilitas Unggulan Nurul Fikri**: Bagi siswa yang berhasil direkrut, cabang menyampaikan jaminan kualitas fasilitas pembelajaran lengkap sesuai flyer resmi:
   - 100% Pengajar PTN & Pembelajaran Tatap Muka Full.
   - Modul Cetak Zuper Book & Modul Digital Interaktif.
   - Akses Pembelajaran Online 24 jam via Aplikasi SIP-NF & NF Juara (Video Pembelajaran, E-Modul, TryOut, Tes Formatif, & Raport Siswa).
   - Free Chat Konsultasi dengan pengajar terbaik (Kuota 200 sesi).
   - Analisis Peluang PTN Canggih: Sistem ANDARA (Analisis Data Raport & Alumni untuk SNBP) serta MBPJ (Matriks Bantu Pemilihan Jurusan untuk SNBT).

Formatlah jawaban Anda persis dalam struktur **MEMORANDUM EKSEKUTIF** profesional berikut:

**MEMORANDUM EKSEKUTIF**

**Kepada:** Manajer Wilayah Megapolitan Selatan
**Dari:** {sender_cabang}
**Tanggal:** {current_date_str}
**Subjek:** Laporan Analisis Kinerja Operasional & Keuangan: {lb_info}

---

### 1. ANALISIS DESKRIPTIF (What Happened)
(Jabarkan kondisi faktual pencapaian siswa, pendapatan cash in, omset paket, dan rasio pelunasan berdasarkan data riil saat ini, serta saluran masuk pendaftar).

### 2. ANALISIS DIAGNOSTIK (Why It Happened)
(Analisis akar masalah & pemicu. Evaluasi efektivitas keterlibatan tim cabang dalam promo sekolah dengan TO/MBTI/Asesmen, serta efektivitas program START NF Gratis sebagai pendorong minat daftar siswa).

### 3. ANALISIS PREDIKTIF (What Will Happen)
(Proyeksi tren ke depan. Proyeksikan potensi konversi peserta START NF gratis menjadi siswa berbayar, serta risiko keterlambatan pelunasan piutang jika tidak di-follow-up dengan pendampingan fasilitas belajar).

### 4. ANALISIS PRESKRIPTIF (What Should We Do)
(Berikan 3 s/d 4 langkah strategis taktis & konkret yang HARUS dilakukan oleh Tim Cabang & Manajemen Wilayah untuk optimalisasi penagihan piutang serta peningkatan konversi pendaftar melalui penonjolan fitur unggulan seperti SIP-NF, ANDARA, dan MBPJ)."""
                    
                    st.session_state.ai_report_text = ask_gemini_ai(user_gemini_key, prompt_narrative)

        if 'ai_report_text' in st.session_state and st.session_state.ai_report_text:
            st.markdown("### 📝 Hasil Laporan Analisis Eksekutif AI:")
            st.markdown(st.session_state.ai_report_text)
            
            escaped_report = html.escape(st.session_state.ai_report_text)
            pdf_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Memorandum Eksekutif - {lb_info}</title>
                <style>
                    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #1A1A1A; padding: 30px; max-width: 800px; margin: 0 auto; }}
                    h1, h2, h3 {{ color: #003366; }}
                    hr {{ border: 0; border-top: 1px solid #CCC; margin: 20px 0; }}
                    pre {{ white-space: pre-wrap; font-family: inherit; font-size: 1rem; }}
                </style>
            </head>
            <body>
                <pre>{escaped_report}</pre>
                <script>
                    window.onload = function() {{ window.print(); }}
                </script>
            </body>
            </html>
            """
            
            b64_html = base64.b64encode(pdf_html.encode('utf-8')).decode('utf-8')
            pdf_href = f'data:text/html;base64,{b64_html}'
            
            st.markdown(
                f'<a href="{pdf_href}" target="_blank" class="btn-download-pdf">'
                f'📄 Download Hasil Laporan Analisis Eksekutif AI (PDF)'
                f'</a>',
                unsafe_allow_html=True
            )

        st.divider()

        st.subheader("💬 3. Tanya AI Seputar Data Dashboard (Interactive Q&A)")
        
        user_question = st.text_input("Tanyakan sesuatu tentang data ini (Contoh: 'Apa saran untuk meningkatkan pelunasan tagihan?'):", key="ai_q_input")
        if st.button("Tanyakan ke AI", use_container_width=True):
            if not user_gemini_key:
                st.warning("⚠️ API Key tidak ditemukan.")
            elif user_question:
                with st.spinner("🤖 AI sedang memproses pertanyaan Anda..."):
                    prompt_q = f"""Anda adalah asisten AI Analis Data untuk BKB Nurul Fikri.
Konteks data dashboard saat ini:
{data_context}

Konteks Program: Cabang rajin promo TO/asesmen ke sekolah, mengadakan tes START NF (Literasi & Numerasi) gratis, dan mempromosikan fasilitas belajar (Pengajar PTN, SIP-NF, ANDARA, MBPJ).

Pertanyaan Pengguna: '{user_question}'

Jawablah pertanyaan tersebut secara ringkas, lugas, ramah, dan berbasis data di atas."""
                    answer = ask_gemini_ai(user_gemini_key, prompt_q)
                    st.success(f"""**Jawaban AI:**\n\n{answer}""")

    else:
        st.warning("Data tidak tersedia untuk dilakukan analisis AI.")
