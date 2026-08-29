import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import json
import urllib.request
import urllib.error

# ---------------------------------------------------------
# KONFIGURASI HALAMAN WEB & THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Dashboard Multi-TA - Bimbingan Belajar",
    page_icon="📊",
    layout="wide"
)

# Custom Styling Adaptive Theme (Support Light, Dark, & System Mode)
st.markdown("""
    <style>
    /* Styling Metric Cards Adaptive Theme & Auto-Fit Text */
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
    
    /* Custom Styling Alert Info Banner Adaptive */
    div[data-testid="stAlert"] {
        background-color: var(--secondary-background-color) !important;
        color: var(--text-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MAPPING KODE CABANG & JENJANG
# ---------------------------------------------------------
LOCATION_MAP = {
    '168': 'NF Halim',
    '192': 'NF Condet',
    '219': 'NF Tebet'
}

JENJANG_MAP = {
    'F': '4 SD',
    'G': '5 SD',
    'H': '6 SD',
    'I': '7 SMP',
    'J': '8 SMP',
    'K': '9 SMP',
    'L': '10 SMA',
    'M': '11 SMA',
    'N': '12 SMA',
    'O': 'RONIN'
}

JENJANG_ORDER = [
    '4 SD', '5 SD', '6 SD',
    '7 SMP', '8 SMP', '9 SMP',
    '10 SMA', '11 SMA', '12 SMA', 'RONIN'
]

# Helper Function Plotly Transparent
def style_chart(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# Helper Function Pendaftaran Online vs Offline dari kolom 'Cara Daftar'
def get_jalur_pendaftaran_from_cara_daftar(val):
    if pd.isna(val):
        return 'Offline (Cabang / WA)'
    val_str = str(val).strip().upper()
    if 'PSB' in val_str or 'ONLINE' in val_str or 'WEB' in val_str:
        return 'Online (Web PSB)'
    return 'Offline (Cabang / WA)'

# Helper Function Deteksi Diskon Juara/PSJ dari Kolom Catatan
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
# HELPER GEMINI AI (REST API Native Python)
# ---------------------------------------------------------
def ask_gemini_ai(api_key, prompt_text):
    if not api_key:
        return "⚠️ **API Key tidak boleh kosong.**"
        
    clean_key = str(api_key).strip().strip("'").strip('"').strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={clean_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    
    try:
        data_json = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data_json, headers=headers)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
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
# HEADER UTAMA & AKSES ADMIN POP-UP
# ---------------------------------------------------------
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

files_trx = None
files_siswa = None
files_diskon = None

col_head1, col_head2 = st.columns([3.5, 1.2])

with col_head1:
    st.title("📊 Executive Dashboard & Analisis Multi-Tahun Ajaran")
    st.caption("Aplikasi Analisis Keuangan, Pendaftaran Siswa, Demografi, Diskon, & Status Bayar Domisili")

with col_head2:
    st.write("") 
    if not st.session_state.admin_logged_in:
        with st.popover("🔑 Login Admin / Upload", use_container_width=True):
            st.subheader("🔑 Akses Admin")
            input_user = st.text_input("Username", key="login_user")
            input_pass = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True):
                if input_user == "staf" and input_pass == "nfms2026":
                    st.session_state.admin_logged_in = True
                    st.success("Login Berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau Password Salah!")
    else:
        with st.popover("🔓 Admin Mode (Aktif)", use_container_width=True):
            st.success("🔓 Mode Admin Aktif")
            if st.button("Logout Admin", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.rerun()

            st.divider()
            st.subheader("📤 Upload File Excel Baru")
            files_trx = st.file_uploader("1. Transaksi (.xlsx)", type=["xlsx"], accept_multiple_files=True)
            files_siswa = st.file_uploader("2. Data Siswa (.xlsx)", type=["xlsx"], accept_multiple_files=True)
            files_diskon = st.file_uploader("3. Data Diskon (.xlsx)", type=["xlsx"], accept_multiple_files=True)

# Helper Function Pembersihan Data
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
    matched_files = [f for f in all_excel_files if any(kw in f.lower() for kw in filename_keywords)]
    
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

# ---------------------------------------------------------
# LOAD & COMBINE DATASETS
# ---------------------------------------------------------
df_trx_raw = load_combined_data(files_trx, ["trx", "laporan", "transaksi"])
df_siswa_raw = load_combined_data(files_siswa, ["siswa", "siswanf"])
df_diskon_raw = load_combined_data(files_diskon, ["diskon"])

# Olah Data Transaksi
if not df_trx_raw.empty:
    if 'Lb' in df_trx_raw.columns:
        df_trx_raw['lb_clean'] = df_trx_raw['Lb'].apply(format_lb)
    if 'Idtahun' in df_trx_raw.columns:
        df_trx_raw['ta_clean'] = df_trx_raw['Idtahun'].apply(clean_str)
    if 'Biaya F' in df_trx_raw.columns:
        df_trx_raw['Kategori_Siswa'] = df_trx_raw['Biaya F'].apply(get_kategori_siswa)
    if 'Jenjang' in df_trx_raw.columns:
        df_trx_raw['Jenjang'] = df_trx_raw['Jenjang'].apply(format_jenjang)

# Olah Data Siswa
if not df_siswa_raw.empty:
    if 'lb' in df_siswa_raw.columns:
        df_siswa_raw['lb_clean'] = df_siswa_raw['lb'].apply(format_lb)
    if 'TA' in df_siswa_raw.columns:
        df_siswa_raw['ta_clean'] = df_siswa_raw['TA'].apply(clean_str)
    if 'Biaya Formulir' in df_siswa_raw.columns:
        df_siswa_raw['Kategori_Siswa'] = df_siswa_raw['Biaya Formulir'].apply(get_kategori_siswa)
    if 'Jenjang' in df_siswa_raw.columns:
        df_siswa_raw['Jenjang'] = df_siswa_raw['Jenjang'].apply(format_jenjang)
        
    col_cara_daftar = None
    for c in df_siswa_raw.columns:
        c_clean = str(c).lower().replace(' ', '').replace('_', '')
        if 'caradaftar' in c_clean or 'caradaft' in c_clean:
            col_cara_daftar = c
            break
            
    if col_cara_daftar:
        df_siswa_raw['Jalur_Daftar'] = df_siswa_raw[col_cara_daftar].apply(get_jalur_pendaftaran_from_cara_daftar)
    else:
        alt_col = next((c for c in df_siswa_raw.columns if 'daftar' in str(c).lower() or 'cara' in str(c).lower()), None)
        if alt_col:
            df_siswa_raw['Jalur_Daftar'] = df_siswa_raw[alt_col].apply(get_jalur_pendaftaran_from_cara_daftar)
        else:
            df_siswa_raw['Jalur_Daftar'] = 'Offline (Cabang / WA)'

# EKSTRAKSI DATA DISKON
list_diskon_records = []

if not df_diskon_raw.empty:
    col_form_d = next((c for c in df_diskon_raw.columns if 'nomor' in str(c).lower() and 'form' in str(c).lower()), 'Nomor Formulir')
    col_kwt_d = next((c for c in df_diskon_raw.columns if 'kwi' in str(c).lower() or 'kwt' in str(c).lower()), 'Kwitansi')
    col_nama_d = next((c for c in df_diskon_raw.columns if 'nama' in str(c).lower() and 'diskon' in str(c).lower()), 'Nama Diskon')
    col_besar_d = next((c for c in df_diskon_raw.columns if 'besar' in str(c).lower() or 'nominal' in str(c).lower()), 'Besar Diskon')

    for _, row in df_diskon_raw.iterrows():
        raw_val = row.get(col_besar_d)
        try:
            val_diskon = float(pd.to_numeric(raw_val, errors='coerce'))
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

if not df_trx_raw.empty:
    col_cat_t = next((c for c in df_trx_raw.columns if 'catatan' in str(c).lower()), None)
    col_form_t = next((c for c in df_trx_raw.columns if 'nomor f' in str(c).lower() or 'form' in str(c).lower()), 'Nomor F')
    col_kwt_t = next((c for c in df_trx_raw.columns if 'nokwt' in str(c).lower() or 'kwt' in str(c).lower()), 'Nokwt')

    if col_cat_t:
        for _, row in df_trx_raw.iterrows():
            jenis_diskon_cat = extract_diskon_juara_from_catatan(row.get(col_cat_t))
            if jenis_diskon_cat:
                list_diskon_records.append({
                    'Nomor Formulir': clean_str(row.get(col_form_t)),
                    'Kwitansi': clean_str(row.get(col_kwt_t)),
                    'Nama Diskon': jenis_diskon_cat,
                    'Besar Diskon': 0.0,
                    'Sumber': 'Catatan Transaksi'
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

    if not df_trx_raw.empty:
        col_form_t = next((c for c in df_trx_raw.columns if 'nomor f' in str(c).lower() or 'form' in str(c).lower()), 'Nomor F')
        df_trx_meta = df_trx_raw.copy()
        df_trx_meta['f_clean'] = df_trx_meta[col_form_t].apply(clean_str) if col_form_t in df_trx_meta.columns else None

        meta_cols_t = ['ta_clean', 'Jenjang', 'lb_clean']
        meta_cols_t = [c for c in meta_cols_t if c in df_trx_meta.columns]

        if 'f_clean' in df_trx_meta.columns:
            map_trx_f = df_trx_meta.dropna(subset=['f_clean']).drop_duplicates(subset=['f_clean']).set_index('f_clean')[meta_cols_t]
            for col in meta_cols_t:
                if col in df_diskon_combined.columns:
                    df_diskon_combined[col] = df_diskon_combined[col].fillna(df_diskon_combined['Nomor Formulir'].map(map_trx_f[col]))
                else:
                    df_diskon_combined[col] = df_diskon_combined['Nomor Formulir'].map(map_trx_f[col])

df_diskon_raw = df_diskon_combined.copy()

# ---------------------------------------------------------
# MASTER FILTER (5 FILTER AKTIF)
# ---------------------------------------------------------
st.divider()

all_ta_set = set()
if 'ta_clean' in df_trx_raw.columns:
    all_ta_set.update(df_trx_raw['ta_clean'].dropna())
if 'ta_clean' in df_siswa_raw.columns:
    all_ta_set.update(df_siswa_raw['ta_clean'].dropna())
if 'ta_clean' in df_diskon_raw.columns:
    all_ta_set.update(df_diskon_raw['ta_clean'].dropna())
list_master_ta = ["Semua Tahun Ajaran"] + sorted(list(all_ta_set))

all_lb_set = set()
if 'lb_clean' in df_trx_raw.columns:
    all_lb_set.update(df_trx_raw['lb_clean'].dropna())
if 'lb_clean' in df_siswa_raw.columns:
    all_lb_set.update(df_siswa_raw['lb_clean'].dropna())
if 'lb_clean' in df_diskon_raw.columns:
    all_lb_set.update(df_diskon_raw['lb_clean'].dropna())
list_master_lb = ["Semua Cabang / Lokasi"] + sorted(list(all_lb_set))

list_master_jenjang = ["Semua Jenjang"] + JENJANG_ORDER

f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)

with f_col1:
    selected_ta = st.selectbox("📅 Tahun Ajaran (TA):", list_master_ta)

with f_col2:
    selected_lb = st.selectbox("🏢 Lokasi Belajar:", list_master_lb)

with f_col3:
    selected_jenjang = st.selectbox("🎓 Jenjang Kelas:", list_master_jenjang)

df_kec_source = df_siswa_raw.copy()
if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_kec_source.columns:
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
elif not df_kec_source.empty and 'Kel Tinggal' in df_kec_source.columns:
    list_kel += sorted([str(x) for x in df_kec_source['Kel Tinggal'].dropna().unique()])

with f_col5:
    selected_kel = st.selectbox("🏠 Kelurahan:", list_kel)

# ---------------------------------------------------------
# APLIKASI FILTER KE SEMUA DATAFRAME
# ---------------------------------------------------------
df_trx = df_trx_raw.copy()
if not df_trx.empty:
    if selected_ta != "Semua Tahun Ajaran" and 'ta_clean' in df_trx.columns:
        df_trx = df_trx[df_trx['ta_clean'] == selected_ta]
    if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_trx.columns:
        df_trx = df_trx[df_trx['lb_clean'] == selected_lb]
    if selected_jenjang != "Semua Jenjang" and 'Jenjang' in df_trx.columns:
        df_trx = df_trx[df_trx['Jenjang'] == selected_jenjang]

df_siswa = df_siswa_raw.copy()
if not df_siswa.empty:
    if selected_ta != "Semua Tahun Ajaran" and 'ta_clean' in df_siswa.columns:
        df_siswa = df_siswa[df_siswa['ta_clean'] == selected_ta]
    if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_siswa.columns:
        df_siswa = df_siswa[df_siswa['lb_clean'] == selected_lb]
    if selected_jenjang != "Semua Jenjang" and 'Jenjang' in df_siswa.columns:
        df_siswa = df_siswa[df_siswa['Jenjang'] == selected_jenjang]
    if selected_kec != "Semua Kecamatan" and 'Kec Tinggal' in df_siswa.columns:
        df_siswa = df_siswa[df_siswa['Kec Tinggal'] == selected_kec]
    if selected_kel != "Semua Kelurahan" and 'Kel Tinggal' in df_siswa.columns:
        df_siswa = df_siswa[df_siswa['Kel Tinggal'] == selected_kel]

df_diskon = df_diskon_raw.copy()
if not df_diskon.empty:
    if selected_ta != "Semua Tahun Ajaran" and 'ta_clean' in df_diskon.columns:
        df_diskon = df_diskon[df_diskon['ta_clean'] == selected_ta]
    if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_diskon.columns:
        df_diskon = df_diskon[df_diskon['lb_clean'] == selected_lb]
    if selected_jenjang != "Semua Jenjang" and 'Jenjang' in df_diskon.columns:
        df_diskon = df_diskon[df_diskon['Jenjang'] == selected_jenjang]
    if selected_kec != "Semua Kecamatan" and 'Kec Tinggal' in df_diskon.columns:
        df_diskon = df_diskon[df_diskon['Kec Tinggal'] == selected_kec]
    if selected_kel != "Semua Kelurahan" and 'Kel Tinggal' in df_diskon.columns:
        df_diskon = df_diskon[df_diskon['Kel Tinggal'] == selected_kel]

ta_info = f"TA {selected_ta}" if selected_ta != "Semua Tahun Ajaran" else "Semua TA"
lb_info = f"Lokasi: {selected_lb}" if selected_lb != "Semua Cabang / Lokasi" else "Semua Lokasi Belajar"
jj_info = f" | Jenjang: {selected_jenjang}" if selected_jenjang != "Semua Jenjang" else ""
dom_info = f" | {selected_kec}" if selected_kec != "Semua Kecamatan" else ""
if selected_kel != "Semua Kelurahan":
    dom_info += f" ({selected_kel})"

st.info(f"📌 **Filter Aktif:** Menampilkan data **{ta_info}** | **{lb_info}**{jj_info}{dom_info}")

# ---------------------------------------------------------
# TABS LAYOUT DASHBOARD
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
            fig_pie = style_chart(px.pie(
                df_pie_summary, 
                names='Type Bayar', 
                values='Jumlah_Siswa', 
                hole=0.4
            ))
            fig_pie.update_traces(
                textinfo='value+percent', 
                texttemplate='%{value} siswa<br>(%{percent})'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram:** Diagram donat di atas memperlihatkan persentase dan frekuensi penggunaan jenis metode pembayaran (Cash, Transfer, Debit, Virtual Account) yang digunakan oleh wali siswa.")

        st.divider()

        if 'Kategori_Siswa' in df_trx.columns:
            st.subheader("Distribusi Status Siswa (Siswa Baru / Lama / NFIC)")
            kat_trx_df = df_trx['Kategori_Siswa'].value_counts().reset_index()
            kat_trx_df.columns = ['Status Siswa', 'Jumlah Transaksi']
            fig_kat_trx = style_chart(px.bar(
                kat_trx_df, x='Status Siswa', y='Jumlah Transaksi', text='Jumlah Transaksi',
                color='Status Siswa'
            ))
            st.plotly_chart(fig_kat_trx, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram Batang:** Menampilkan total transaksi pembayaran formulir berdasarkan kelompok status siswa (Siswa Baru Rp300k, Siswa Lama Rp50k, atau NFIC Rp200k).")

    else:
        st.warning(f"Data Transaksi tidak ditemukan untuk filter terpilih.")

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
                fig_kat_siswa = style_chart(px.bar(
                    kat_siswa_df, x='Status Siswa', y='Jumlah', text='Jumlah',
                    color='Status Siswa'
                ))
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
                
                fig_jalur_pie = style_chart(px.pie(
                    df_jalur,
                    names='Jalur Pendaftaran',
                    values='Jumlah Siswa',
                    hole=0.4,
                    color='Jalur Pendaftaran',
                    color_discrete_map={
                        'Online (Web PSB)': '#00cc96',
                        'Offline (Cabang / WA)': '#636efa'
                    }
                ))
                
                fig_jalur_pie.update_traces(
                    textinfo='value+percent',
                    texttemplate='%{value} siswa<br>(%{percent})'
                )
                
                st.plotly_chart(fig_jalur_pie, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram:** Perbandingan efektivitas pendaftaran siswa melalui sistem Website PSB Online dibandingkan pendaftaran manual langsung di Cabang/WA.")
            else:
                st.warning("Kolom 'Cara Daftar' tidak ditemukan pada file Data Siswa.")

    else:
        st.warning(f"Data Siswa tidak ditemukan untuk filter terpilih.")

# --- TAB 3: SEKOLAH & DOMISILI SISWA ---
with tab3:
    if not df_siswa.empty:
        st.header("🏫 Analisis Asal Sekolah & Domisili Siswa")
        st.subheader("1. Top Asal Sekolah Pendaftar")
        c1, c2 = st.columns([2, 1])
        with c1:
            top_sekolah = df_siswa['Asal Sekolah'].value_counts().head(10).reset_index()
            top_sekolah.columns = ['Asal Sekolah', 'Jumlah Siswa']
            fig_sekolah = style_chart(px.bar(
                top_sekolah, y='Asal Sekolah', x='Jumlah Siswa', orientation='h', 
                text='Jumlah Siswa', color='Jumlah Siswa', color_continuous_scale='Viridis'
            ))
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

            fig_jenjang_kec = style_chart(px.bar(
                jenjang_kec,
                x='Kec Tinggal',
                y='Jumlah_Siswa',
                color='Jenjang',
                barmode='group',
                text='Label_Text',
                labels={'Kec Tinggal': 'Kecamatan Domisili', 'Jumlah_Siswa': 'Jumlah Siswa'}
            ))
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

            fig_jenjang_kel = style_chart(px.bar(
                jenjang_kel,
                x='Kel Tinggal',
                y='Jumlah_Siswa',
                color='Jenjang',
                barmode='group',
                text='Label_Text',
                labels={'Kel Tinggal': 'Kelurahan Domisili', 'Jumlah_Siswa': 'Jumlah Siswa'}
            ))
            fig_jenjang_kel.update_traces(textposition='outside')
            st.plotly_chart(fig_jenjang_kel, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram:** Pemetaan tingkat kelurahan secara mendalam untuk mengidentifikasi area pemukiman yang paling potensial untuk penetrasi pasar.")

    else:
        st.warning(f"Data Sekolah/Domisili tidak ditemukan.")

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
                
                fig_diskon_pie = style_chart(px.pie(
                    diskon_type, 
                    names='Nama Diskon', 
                    values='Jumlah Siswa', 
                    hole=0.4
                ))
                
                fig_diskon_pie.update_traces(
                    textinfo='value+percent',
                    texttemplate='%{value} siswa<br>(%{percent})'
                )
                
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
        st.warning(f"Data Diskon Khusus tidak ditemukan untuk filter aktif saat ini.")

# --- TAB 5: PERBANDINGAN MULTI-TA ---
with tab5:
    st.header("📈 Analisis & Komparasi Tren Multi-Tahun Ajaran (Multi-TA)")
    st.info("💡 **Tersinkronisasi:** Seluruh grafik di bawah ini membandingkan tren performa antar Tahun Ajaran berdasarkan Lokasi, Jenjang, dan Domisili terfilter.")

    df_s_comp = df_siswa_raw.copy()
    if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_s_comp.columns:
        df_s_comp = df_s_comp[df_s_comp['lb_clean'] == selected_lb]
    if selected_jenjang != "Semua Jenjang" and 'Jenjang' in df_s_comp.columns:
        df_s_comp = df_s_comp[df_s_comp['Jenjang'] == selected_jenjang]
    if selected_kec != "Semua Kecamatan" and 'Kec Tinggal' in df_s_comp.columns:
        df_s_comp = df_s_comp[df_s_comp['Kec Tinggal'] == selected_kec]
    if selected_kel != "Semua Kelurahan" and 'Kel Tinggal' in df_s_comp.columns:
        df_s_comp = df_s_comp[df_s_comp['Kel Tinggal'] == selected_kel]

    df_t_comp = df_trx_raw.copy()
    if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_t_comp.columns:
        df_t_comp = df_t_comp[df_t_comp['lb_clean'] == selected_lb]
    if selected_jenjang != "Semua Jenjang" and 'Jenjang' in df_t_comp.columns:
        df_t_comp = df_t_comp[df_t_comp['Jenjang'] == selected_jenjang]

    if not df_s_comp.empty and 'ta_clean' in df_s_comp.columns:
        
        def calculate_delta_df(df_grouped, col_cat, col_val='Jumlah'):
            df_pivot = df_grouped.pivot(index='ta_clean', columns=col_cat, values=col_val).fillna(0)
            df_diff = df_pivot.diff().fillna(0)
            df_pct = (df_pivot.pct_change() * 100).fillna(0).round(1)
            return df_pivot, df_diff, df_pct

        # 1. Jumlah Siswa Lama / Baru
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
            
            piv1, diff1, pct1 = calculate_delta_df(g1, 'Kategori_Siswa')
            st.caption("📈 **Tabel Rekapitulasi Perubahan YoY:**")
            st.dataframe(piv1.style.highlight_max(axis=0), use_container_width=True)

        st.divider()

        # 2. Komparasi Paket Bimbingan vs Cash In
        st.subheader("2. Komparasi Paket Bimbingan vs Realisasi Cash In per TA")
        g2 = df_s_comp.groupby('ta_clean').agg(
            Nilai_Paket=('Biaya Paket', 'sum'),
            Cash_In=('Total Bayar', 'sum')
        ).reset_index()
        
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

        # 3. Tren Pendapatan Harian
        st.subheader("3. Tren Pendapatan Harian Antar TA")
        if not df_t_comp.empty and 'Tanggal' in df_t_comp.columns:
            df_t_comp['Tanggal'] = pd.to_datetime(df_t_comp['Tanggal'])
            df_t_comp['Bulan_Tgl'] = df_t_comp['Tanggal'].dt.strftime('%m-%d')
            g3 = df_t_comp.groupby(['Bulan_Tgl', 'ta_clean'])['Jumlah'].sum().reset_index()

            fig3_line = style_chart(px.line(g3, x='Bulan_Tgl', y='Jumlah', color='ta_clean', markers=True, title="Grafik Tren Pendapatan Harian (Disetarakan Tanggal & Bulan)"))
            st.plotly_chart(fig3_line, use_container_width=True)
            st.caption("📝 **Penjelasan Grafik Garis Multi-Garis:** Menyejajarkan pola pemasukan harian harian antar TA pada kalender tanggal yang sama untuk menganalisis puncak periode penerimaan kas.")

        st.divider()

        # 4. Proporsi Metode Pembayaran
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

        st.divider()

        # 5. Distribusi Jenjang Kelas
        st.subheader("5. Distribusi Jenjang Kelas per TA")
        if 'Jenjang' in df_s_comp.columns:
            g5 = df_s_comp.groupby(['ta_clean', 'Jenjang']).size().reset_index(name='Jumlah')
            c1, c2 = st.columns(2)
            with c1:
                fig5_bar = style_chart(px.bar(g5, x='Jenjang', y='Jumlah', color='ta_clean', barmode='group', text_auto=True, title="Perbandingan Jenjang Kelas Antar TA"))
                st.plotly_chart(fig5_bar, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Batang:** Perbandingan volume siswa di setiap tingkatan kelas antar TA.")
            with c2:
                fig5_pie = style_chart(px.pie(g5, names='Jenjang', values='Jumlah', hole=0.4, title="Proporsi Akumulasi Jenjang Kelas"))
                fig5_pie.update_traces(textinfo='value+percent', texttemplate='%{value} siswa<br>(%{percent})')
                st.plotly_chart(fig5_pie, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Donat:** Distribusi pangsa siswa menurut tingkatan kelas bimbingan.")

        st.divider()

        # 6. Proporsi Pendaftaran Online vs Offline
        st.subheader("6. Proporsi Pendaftaran Online vs Offline per TA")
        if 'Jalur_Daftar' in df_s_comp.columns:
            g6 = df_s_comp.groupby(['ta_clean', 'Jalur_Daftar']).size().reset_index(name='Jumlah')
            c1, c2 = st.columns(2)
            with c1:
                fig6_bar = style_chart(px.bar(g6, x='ta_clean', y='Jumlah', color='Jalur_Daftar', barmode='group', text_auto=True, title="Diagram Batang Jalur Pendaftaran"))
                st.plotly_chart(fig6_bar, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Batang:** Pertumbuhan pendaftar jalur Online Web PSB dibanding pendaftaran Offline langsung.")
            with c2:
                fig6_pie = style_chart(px.pie(g6, names='Jalur_Daftar', values='Jumlah', hole=0.4, title="Proporsi Pendaftaran Online vs Offline"))
                fig6_pie.update_traces(textinfo='value+percent', texttemplate='%{value} siswa<br>(%{percent})')
                st.plotly_chart(fig6_pie, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Donat:** Perbandingan proporsi penetrasi jalur pendaftaran digital vs konvensional.")

        st.divider()

        # 7. Top Asal Sekolah Pendaftar
        st.subheader("7. Top Asal Sekolah Pendaftar per TA")
        if 'Asal Sekolah' in df_s_comp.columns:
            top_sch_list = df_s_comp['Asal Sekolah'].value_counts().head(10).index
            df_top_sch = df_s_comp[df_s_comp['Asal Sekolah'].isin(top_sch_list)]
            g7 = df_top_sch.groupby(['Asal Sekolah', 'ta_clean']).size().reset_index(name='Jumlah')

            fig7_bar = style_chart(px.bar(g7, x='Asal Sekolah', y='Jumlah', color='ta_clean', barmode='group', text_auto=True, title="10 Sekolah Penyumbang Siswa Terbanyak per TA"))
            st.plotly_chart(fig7_bar, use_container_width=True)
            st.caption("📝 **Penjelasan Diagram Batang:** Menampilkan tren pergerakan dinamika jumlah pendaftar dari 10 sekolah mitra utama antar TA.")

        st.divider()

        # 8. Detail Sebaran Sekolah & Lokasi Belajar
        st.subheader("8. Detail Sebaran Sekolah & Lokasi Belajar Antar TA")
        if 'Asal Sekolah' in df_s_comp.columns and 'lb_clean' in df_s_comp.columns:
            g8 = df_s_comp.groupby(['ta_clean', 'Asal Sekolah', 'lb_clean']).size().reset_index(name='Jumlah_Siswa')
            st.dataframe(g8.sort_values(by=['ta_clean', 'Jumlah_Siswa'], ascending=[True, False]), use_container_width=True)
            st.caption("📝 **Penjelasan Tabel Data:** Rincian kuantitatif distribusi domisili sekolah ke cabang lokasi belajar di setiap Tahun Ajaran.")

        st.divider()

        # 9. Presentase Status Bayar per Domisili
        st.subheader("9. Persentase Status Bayar per Domisili (Lunas vs Angsuran) Antar TA")
        if 'Tagihan' in df_s_comp.columns and 'Kec Tinggal' in df_s_comp.columns:
            df_s_comp['Status_Bayar'] = df_s_comp['Tagihan'].apply(lambda x: 'Lunas' if x >= 0 else 'Angsuran')
            dom_col = 'Kel Tinggal' if selected_kec != "Semua Kecamatan" else 'Kec Tinggal'
            g9 = df_s_comp.groupby(['ta_clean', dom_col, 'Status_Bayar']).size().reset_index(name='Jumlah')

            c1, c2 = st.columns(2)
            with c1:
                fig9_bar = style_chart(px.bar(g9, x=dom_col, y='Jumlah', color='Status_Bayar', facet_col='ta_clean', barmode='stack', text_auto=True, title="Status Bayar per Domisili per TA"))
                st.plotly_chart(fig9_bar, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Tumpuk:** Komparasi jumlah siswa yang telah Lunas vs Mengangsur pada masing-masing wilayah domisili dari TA ke TA.")
            with c2:
                fig9_pie = style_chart(px.pie(g9, names='Status_Bayar', values='Jumlah', hole=0.4, title="Proporsi Lunas vs Angsuran"))
                fig9_pie.update_traces(textinfo='value+percent', texttemplate='%{value} siswa<br>(%{percent})')
                st.plotly_chart(fig9_pie, use_container_width=True)
                st.caption("📝 **Penjelasan Diagram Donat:** Perbandingan akumulasi rasio kesehatan pelunasan biaya bimbingan.")

    else:
        st.warning("Data multi-tahun ajaran tidak cukup untuk ditampilkan.")

# --- TAB 6: STATUS BAYAR DOMISILI ---
with tab6:
    st.header("📊 Analisis Persentase Lunas & Angsuran Berdasarkan Domisili")
    st.info("💡 **Tersinkronisasi dengan Filter:** Data di bawah ini secara otomatis beradaptasi mengikuti filter Tahun Ajaran, Lokasi Belajar, Jenjang Kelas, Kecamatan, dan Kelurahan yang aktif di atas.")

    if not df_siswa.empty and 'Kec Tinggal' in df_siswa.columns:
        df_status = df_siswa.copy()
        
        df_status['Status_Bayar'] = df_status['Tagihan'].apply(lambda x: 'Lunas' if x >= 0 else 'Angsuran')
        
        if 'ta_clean' not in df_status.columns:
            df_status['ta_clean'] = df_status['TA'].apply(clean_str)
        if 'lb_clean' not in df_status.columns:
            df_status['lb_clean'] = df_status['lb'].apply(format_lb)

        col_st1, col_st2, col_st3, col_st4 = st.columns(4)
        total_s = len(df_status)
        total_lunas = len(df_status[df_status['Status_Bayar'] == 'Lunas'])
        total_angsuran = len(df_status[df_status['Status_Bayar'] == 'Angsuran'])
        
        col_st1.metric("Total Siswa Terfilter", f"{total_s} Siswa")
        col_st2.metric("Siswa Lunas", f"{total_lunas} Siswa ({round(total_lunas/total_s*100,1) if total_s>0 else 0}%)")
        col_st3.metric("Siswa Angsuran", f"{total_angsuran} Siswa ({round(total_angsuran/total_s*100,1) if total_s>0 else 0}%)")
        col_st4.metric("Jumlah Domisili", f"{df_status['Kel Tinggal'].nunique()} Kelurahan")

        st.divider()

        st.subheader("1. Grafik Presentase Status Bayar per Domisili")
        
        domisili_col = 'Kel Tinggal' if selected_kec != "Semua Kecamatan" else 'Kec Tinggal'
        domisili_label = 'Kelurahan' if selected_kec != "Semua Kecamatan" else 'Kecamatan'

        dom_summary = df_status.groupby(['lb_clean', domisili_col, 'Status_Bayar']).size().reset_index(name='Jumlah')
        
        fig_status_dom = style_chart(px.bar(
            dom_summary, 
            x=domisili_col, 
            y='Jumlah', 
            color='Status_Bayar', 
            barmode='stack',
            facet_col='lb_clean',
            text_auto=True,
            color_discrete_map={'Lunas': '#00cc96', '#ef553b': '#ef553b'},
            labels={domisili_col: f'{domisili_label} Domisili', 'lb_clean': 'Lokasi Belajar'}
        ))
        st.plotly_chart(fig_status_dom, use_container_width=True)
        st.caption("📝 **Penjelasan Diagram Batang Tumpuk:** Menampilkan proporsi jumlah siswa yang sudah Lunas (hijau) dan yang masih Mengangsur (merah) dipisahkan per wilayah domisili.")

        st.divider()

        st.subheader("2. Tabel Rincian Persentase per Kecamatan Domisili (Terfilter)")
        rekap_kec = df_status.groupby(['ta_clean', 'lb_clean', 'Kec Tinggal', 'Status_Bayar']).size().unstack(fill_value=0).reset_index()
        
        if 'Lunas' not in rekap_kec.columns:
            rekap_kec['Lunas'] = 0
        if 'Angsuran' not in rekap_kec.columns:
            rekap_kec['Angsuran'] = 0

        rekap_kec['Total Siswa'] = rekap_kec['Lunas'] + rekap_kec['Angsuran']
        rekap_kec['% Lunas'] = (rekap_kec['Lunas'] / rekap_kec['Total Siswa'] * 100).round(1).astype(str) + '%'
        rekap_kec['% Angsuran'] = (rekap_kec['Angsuran'] / rekap_kec['Total Siswa'] * 100).round(1).astype(str) + '%'

        rekap_kec = rekap_kec.rename(columns={
            'ta_clean': 'Tahun Ajaran (TA)',
            'lb_clean': 'Lokasi Belajar',
            'Kecamatan': 'Kecamatan Domisili',
            'Lunas': 'Jumlah Lunas',
            'Angsuran': 'Jumlah Angsuran'
        })
        
        st.dataframe(rekap_kec, use_container_width=True)
        st.caption("📝 **Penjelasan Tabel Rincian:** Tabel evaluasi keuangan per Kecamatan. Berguna bagi tim penagihan (*finance*) untuk memprioritaskan area pemukiman dengan persentase angsuran tinggi.")

        st.divider()

        st.subheader("3. Tabel Rincian Persentase per Kelurahan Domisili (Terfilter)")
        rekap_kel = df_status.groupby(['ta_clean', 'lb_clean', 'Kec Tinggal', 'Kel Tinggal', 'Status_Bayar']).size().unstack(fill_value=0).reset_index()
        
        if 'Lunas' not in rekap_kel.columns:
            rekap_kel['Lunas'] = 0
        if 'Angsuran' not in rekap_kel.columns:
            rekap_kel['Angsuran'] = 0

        rekap_kel['Total Siswa'] = rekap_kel['Lunas'] + rekap_kel['Angsuran']
        rekap_kel['% Lunas'] = (rekap_kel['Lunas'] / rekap_kel['Total Siswa'] * 100).round(1).astype(str) + '%'
        rekap_kel['% Angsuran'] = (rekap_kel['Angsuran'] / rekap_kel['Total Siswa'] * 100).round(1).astype(str) + '%'

        rekap_kel = rekap_kel.rename(columns={
            'ta_clean': 'Tahun Ajaran (TA)',
            'lb_clean': 'Lokasi Belajar',
            'Kecamatan': 'Kecamatan',
            'Kel Tinggal': 'Kelurahan Domisili',
            'Lunas': 'Jumlah Lunas',
            'Angsuran': 'Jumlah Angsuran'
        })
        
        st.dataframe(rekap_kel, use_container_width=True)
        st.caption("📝 **Penjelasan Tabel Rincian:** Rincian tingkat Kelurahan untuk penanganan lanjutan (*follow-up*) penagihan piutang sisa paket bimbingan.")

    else:
        st.warning("Data Siswa untuk analisis status bayar domisili tidak ditemukan untuk filter ini.")

# --- TAB 7: ANALISIS AI & EXECUTIVE SUMMARY ---
with tab7:
    st.header("🤖 Executive AI Analytics & Smart Insights Assistant")
    st.info("💡 **AI Engine Integration:** Modul ini menganalisis seluruh data pada dashboard untuk menghasilkan Laporan Eksekutif, Temuan Kunci, & Rekomendasi Strategis secara otomatis maupun melalui integrasi Google Gemini AI.")

    if not df_siswa.empty:
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

        st.subheader("✨ 2. Generative AI Executive Report (Google Gemini AI)")
        
        system_gemini_key = st.secrets.get("GEMINI_API_KEY", "")
        
        if system_gemini_key:
            user_gemini_key = system_gemini_key
            st.success("✅ **AI Key Terhubung dari Server System.**")
        else:
            with st.expander("🔑 Pengaturan API Key Google Gemini", expanded=True):
                st.write("Dapatkan API Key gratis Anda dari [Google AI Studio](https://aistudio.google.com/app/apikey).")
                user_gemini_key = st.text_input("Masukkan Gemini API Key Anda:", type="password", key="gemini_key_input")

        ctx_lines = [
            f"Filter Terpilih: {ta_info}, {lb_info}, {jj_info}, {dom_info}",
            f"Total Siswa: {tot_siswa} Siswa",
            f"Total Nilai Paket Bimbingan: Rp {tot_paket:,.0f}",
            f"Total Realisasi Pembayaran (Cash In): Rp {tot_bayar:,.0f}",
            f"Rasio Pelunasan: {pct_pelunasan:.1f}%",
            f"Sisa Tagihan Piutang: Rp {tot_tagihan:,.0f}"
        ]
        if 'Jalur_Daftar' in df_siswa.columns:
            jalur_str = ', '.join([f'{k}: {v}' for k,v in df_siswa['Jalur_Daftar'].value_counts().items()])
            ctx_lines.append(f"Metode Pendaftaran: {jalur_str}")
        if 'Asal Sekolah' in df_siswa.columns:
            top_sch_str = ', '.join([f'{k} ({v})' for k,v in df_siswa['Asal Sekolah'].value_counts().head(5).items()])
            ctx_lines.append(f"Top Asal Sekolah: {top_sch_str}")
        if 'Kec Tinggal' in df_siswa.columns:
            top_kec_str = ', '.join([f'{k} ({v})' for k,v in df_siswa['Kec Tinggal'].value_counts().head(5).items()])
            ctx_lines.append(f"Top Domisili Kecamatan: {top_kec_str}")

        data_context = "\n- ".join([""] + ctx_lines)

        if st.button("✨ Hasilkan Laporan & Rekomendasi Eksekutif dengan AI", type="primary", use_container_width=True):
            if not user_gemini_key:
                st.warning("⚠️ API Key belum dimasukkan. Silakan masukan API Key Anda di atas.")
            else:
                with st.spinner("🤖 Gemini AI sedang menganalisis data keuangan, demografi, & rasio pelunasan..."):
                    prompt_narrative = f"""Anda adalah seorang Management Consultant & Chief Data Officer senior untuk lembaga bimbingan belajar.
Berdasarkan data operasional & keuangan terbaru berikut:
{data_context}

Tuliskan laporan analisis eksekutif yang tajam, profesional, dan siap dipresentasikan kepada direksi:
1. Executive Summary & Evaluasi Kinerja
2. Analisis Risiko & Piutang Tagihan
3. Peluang Ekspansi & Marketing
4. 3 Langkah Strategis Prioritas (Actionable Steps)"""
                    
                    ai_response = ask_gemini_ai(user_gemini_key, prompt_narrative)
                    st.markdown("### 📝 Hasil Laporan Analisis Eksekutif AI:")
                    st.markdown(ai_response)

        st.divider()

        st.subheader("💬 3. Tanya AI Seputar Data Dashboard (Interactive Q&A)")
        
        user_question = st.text_input("Tanyakan sesuatu tentang data ini (Contoh: 'Apa saran untuk meningkatkan pelunasan tagihan?'):", key="ai_q_input")
        if st.button("Tanyakan ke AI", use_container_width=True):
            if not user_gemini_key:
                st.warning("⚠️ API Key belum dimasukkan.")
            elif user_question:
                with st.spinner("🤖 AI sedang memproses pertanyaan Anda..."):
                    prompt_q = f"""Anda adalah asisten AI Analis Data untuk Bimbingan Belajar.
Konteks data dashboard saat ini:
{data_context}

Pertanyaan Pengguna: '{user_question}'

Jawablah pertanyaan tersebut secara ringkas, lugas, ramah, dan berbasis data di atas."""
                    answer = ask_gemini_ai(user_gemini_key, prompt_q)
                    st.success(f"""**Jawaban AI:**\n\n{answer}""")

    else:
        st.warning("Data tidak tersedia untuk dilakukan analisis AI.")
