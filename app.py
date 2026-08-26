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

# Helper Function Plotly Transparent
def style_chart(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# Helper Function Pendaftaran Online vs Offline (Sesuai Logika Kolom Crt_By)
def get_jalur_pendaftaran(crt_by):
    if pd.isna(crt_by):
        return 'Offline (Cabang / WA)'
    
    # Konversi ke string, hapus spasi di awal/akhir, dan ubah ke huruf kapital
    crt_str = str(crt_by).strip().upper()
    
    # Cek apakah kata 'PSB' ada di dalam isi kolom
    if 'PSB' in crt_str:
        return 'Online (Web PSB)'
    
    return 'Offline (Cabang / WA)'

# ---------------------------------------------------------
# HELPER GEMINI AI (REST API Native Python)
# ---------------------------------------------------------
def ask_gemini_ai(api_key, prompt_text):
    if not api_key:
        return "⚠️ **API Key tidak boleh kosong.**"
        
    clean_key = str(api_key).strip().strip("'").strip('"').strip()
    
    # URL Endpoint Gemini 1.5 Flash Resmi & Stabil
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={clean_key}"
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
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
# HEADER UTAMA & AKSES ADMIN POP-UP (POJOK KANAN ATAS)
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
                if input_user == "staf612120" and input_pass == "nfms2026%":
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

if not df_trx_raw.empty:
    if 'Lb' in df_trx_raw.columns:
        df_trx_raw['lb_clean'] = df_trx_raw['Lb'].apply(format_lb)
    if 'Idtahun' in df_trx_raw.columns:
        df_trx_raw['ta_clean'] = df_trx_raw['Idtahun'].apply(clean_str)
    if 'Biaya F' in df_trx_raw.columns:
        df_trx_raw['Kategori_Siswa'] = df_trx_raw['Biaya F'].apply(get_kategori_siswa)

if not df_siswa_raw.empty:
    if 'lb' in df_siswa_raw.columns:
        df_siswa_raw['lb_clean'] = df_siswa_raw['lb'].apply(format_lb)
    if 'TA' in df_siswa_raw.columns:
        df_siswa_raw['ta_clean'] = df_siswa_raw['TA'].apply(clean_str)
    if 'Biaya Formulir' in df_siswa_raw.columns:
        df_siswa_raw['Kategori_Siswa'] = df_siswa_raw['Biaya Formulir'].apply(get_kategori_siswa)
    if 'Jenjang' in df_siswa_raw.columns:
        df_siswa_raw['Jenjang'] = df_siswa_raw['Jenjang'].apply(format_jenjang)
        
    # --- LOGIKA PENETAPAN KOLOM CRT BY (LEBIH FLEKSIBEL) ---
    # Mencari nama kolom yang mengandung kata 'crt' tanpa mempedulikan spasi/underscore/huruf besar-kecil
    crt_col_found = None
    for col in df_siswa_raw.columns:
        if 'crt' in str(col).lower():
            crt_col_found = col
            break
            
    if crt_col_found:
        df_siswa_raw['Jalur_Daftar'] = df_siswa_raw[crt_col_found].apply(get_jalur_pendaftaran)
    else:
        df_siswa_raw['Jalur_Daftar'] = 'Offline (Cabang / WA)'

if not df_diskon_raw.empty:
    if 'Kode Lokasi' in df_diskon_raw.columns:
        df_diskon_raw['lb_clean'] = df_diskon_raw['Kode Lokasi'].apply(format_lb)

# ---------------------------------------------------------
# MASTER FILTER
# ---------------------------------------------------------
st.divider()

all_ta_set = set()
if 'ta_clean' in df_trx_raw.columns:
    all_ta_set.update(df_trx_raw['ta_clean'].dropna())
if 'ta_clean' in df_siswa_raw.columns:
    all_ta_set.update(df_siswa_raw['ta_clean'].dropna())
list_master_ta = ["Semua Tahun Ajaran"] + sorted(list(all_ta_set))

all_lb_set = set()
if 'lb_clean' in df_trx_raw.columns:
    all_lb_set.update(df_trx_raw['lb_clean'].dropna())
if 'lb_clean' in df_siswa_raw.columns:
    all_lb_set.update(df_siswa_raw['lb_clean'].dropna())
if 'lb_clean' in df_diskon_raw.columns:
    all_lb_set.update(df_diskon_raw['lb_clean'].dropna())
list_master_lb = ["Semua Cabang / Lokasi"] + sorted(list(all_lb_set))

f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)

with f_col1:
    selected_ta = st.selectbox("📅 Tahun Ajaran (TA):", list_master_ta)

with f_col2:
    selected_lb = st.selectbox("🏢 Lokasi Belajar:", list_master_lb)

df_kec_source = df_siswa_raw.copy()
if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_kec_source.columns:
    df_kec_source = df_kec_source[df_kec_source['lb_clean'] == selected_lb]

list_kec = ["Semua Kecamatan"]
if not df_kec_source.empty and 'Kec Tinggal' in df_kec_source.columns:
    list_kec += sorted([str(x) for x in df_kec_source['Kec Tinggal'].dropna().unique()])

with f_col3:
    selected_kec = st.selectbox("📍 Kecamatan:", list_kec)

list_kel = ["Semua Kelurahan"]
if selected_kec != "Semua Kecamatan" and not df_kec_source.empty:
    sub_kel = df_kec_source[df_kec_source['Kec Tinggal'] == selected_kec]['Kel Tinggal'].dropna().unique()
    list_kel += sorted([str(x) for x in sub_kel])
elif not df_kec_source.empty and 'Kel Tinggal' in df_kec_source.columns:
    list_kel += sorted([str(x) for x in df_kec_source['Kel Tinggal'].dropna().unique()])

with f_col4:
    selected_kel = st.selectbox("🏠 Kelurahan:", list_kel)

list_nama_diskon = ["Semua Jenis Diskon"]
df_diskon_source = df_diskon_raw.copy()
if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_diskon_source.columns:
    df_diskon_source = df_diskon_source[df_diskon_source['lb_clean'] == selected_lb]

if not df_diskon_source.empty and 'Nama Diskon' in df_diskon_source.columns:
    list_nama_diskon += sorted([str(x) for x in df_diskon_source['Nama Diskon'].dropna().unique()])

with f_col5:
    selected_nama_diskon = st.selectbox("🏷️ Jenis Diskon:", list_nama_diskon)

# ---------------------------------------------------------
# APLIKASI FILTER KE DATAFRAME
# ---------------------------------------------------------
df_trx = df_trx_raw.copy()
if not df_trx.empty:
    if selected_ta != "Semua Tahun Ajaran" and 'ta_clean' in df_trx.columns:
        df_trx = df_trx[df_trx['ta_clean'] == selected_ta]
    if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_trx.columns:
        df_trx = df_trx[df_trx['lb_clean'] == selected_lb]

df_siswa = df_siswa_raw.copy()
if not df_siswa.empty:
    if selected_ta != "Semua Tahun Ajaran" and 'ta_clean' in df_siswa.columns:
        df_siswa = df_siswa[df_siswa['ta_clean'] == selected_ta]
    if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_siswa.columns:
        df_siswa = df_siswa[df_siswa['lb_clean'] == selected_lb]
    if selected_kec != "Semua Kecamatan" and 'Kec Tinggal' in df_siswa.columns:
        df_siswa = df_siswa[df_siswa['Kec Tinggal'] == selected_kec]
    if selected_kel != "Semua Kelurahan" and 'Kel Tinggal' in df_siswa.columns:
        df_siswa = df_siswa[df_siswa['Kel Tinggal'] == selected_kel]

df_diskon = df_diskon_raw.copy()
if not df_diskon.empty:
    if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_diskon.columns:
        df_diskon = df_diskon[df_diskon['lb_clean'] == selected_lb]
    if selected_nama_diskon != "Semua Jenis Diskon" and 'Nama Diskon' in df_diskon.columns:
        df_diskon = df_diskon[df_diskon['Nama Diskon'] == selected_nama_diskon]

ta_info = f"TA {selected_ta}" if selected_ta != "Semua Tahun Ajaran" else "Semua TA"
lb_info = f"Lokasi: {selected_lb}" if selected_lb != "Semua Cabang / Lokasi" else "Semua Lokasi Belajar"
dom_info = f" | {selected_kec}" if selected_kec != "Semua Kecamatan" else ""
if selected_kel != "Semua Kelurahan":
    dom_info += f" ({selected_kel})"
diskon_info = f" | {selected_nama_diskon}" if selected_nama_diskon != "Semua Jenis Diskon" else ""

st.info(f"📌 **Filter Aktif:** Menampilkan data **{ta_info}** | **{lb_info}**{dom_info}{diskon_info}")

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

        with c2:
            st.subheader("Distribusi Jenjang Kelas")
            jenjang_df = df_siswa['Jenjang'].value_counts().reset_index()
            jenjang_df.columns = ['Jenjang', 'Jumlah']
            fig_jenjang = style_chart(px.bar(jenjang_df, x='Jenjang', y='Jumlah', color='Jumlah'))
            st.plotly_chart(fig_jenjang, use_container_width=True)

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
            else:
                st.warning("Kolom 'Crt_By' tidak ditemukan pada data siswa.")

    else:
        st.warning(f"Data Siswa tidak ditemukan untuk filter terpilih.")

# Tambahkan di Tab 2 sementara untuk cek isi kolom aslinya
with tab2:
    if 'Jalur_Daftar' in df_siswa.columns:
        # Menampilkan 10 nilai unik dari kolom Crt_By
        st.write("🔍 **Debug Nilai Kolom Crt_By:**", df_siswa_raw[crt_col_found].unique() if crt_col_found else "Kolom Crt tidak ditemukan")

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

        with c2:
            st.write("📊 **Detail Sebaran Sekolah & Lokasi Belajar**")
            sekolah_lb = df_siswa.groupby(['Asal Sekolah', 'lb_clean']).size().reset_index(name='Jumlah Siswa')
            sekolah_lb.columns = ['Asal Sekolah', 'Lokasi Belajar', 'Jumlah Siswa']
            sekolah_lb = sekolah_lb.sort_values(by='Jumlah Siswa', ascending=False)
            st.dataframe(sekolah_lb, use_container_width=True, height=350)

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

    else:
        st.warning(f"Data Sekolah/Domisili tidak ditemukan.")

# --- TAB 4: DISKON KHUSUS ---
with tab4:
    if not df_diskon.empty:
        st.header("🏷️ Analisis Siswa Pendaftar Diskon Khusus")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Penerima Diskon", f"{len(df_diskon)} Siswa")
        col2.metric("Total Nominal Diskon", f"Rp {df_diskon['Besar Diskon'].sum():,.0f}".replace(',', '.'))
        col3.metric("Rata-rata Diskon", f"Rp {df_diskon['Besar Diskon'].mean():,.0f}".replace(',', '.'))
        col4.metric("Jenis Diskon", f"{df_diskon['Nama Diskon'].nunique()} Kategori")

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            diskon_type = df_diskon['Nama Diskon'].value_counts().reset_index()
            diskon_type.columns = ['Nama Diskon', 'Jumlah Siswa']
            fig_diskon_pie = style_chart(px.pie(diskon_type, names='Nama Diskon', values='Jumlah Siswa', hole=0.4))
            st.plotly_chart(fig_diskon_pie, use_container_width=True)

        with c2:
            diskon_lokasi = df_diskon.groupby('lb_clean')['Besar Diskon'].sum().reset_index()
            diskon_lokasi.columns = ['Lokasi Belajar', 'Besar Diskon']
            fig_diskon_bar = style_chart(px.bar(diskon_lokasi, x='Lokasi Belajar', y='Besar Diskon', text_auto='.2s', color='Besar Diskon'))
            st.plotly_chart(fig_diskon_bar, use_container_width=True)
    else:
        st.warning(f"Data Diskon Khusus tidak ditemukan.")

# --- TAB 5: PERBANDINGAN MULTI-TA ---
with tab5:
    st.header("📈 Perbandingan Data Siswa & Tren 3 Tahun Ajaran")
    st.info("💡 Menganalisis pertumbuhan pendaftaran siswa, finansial paket bimbingan, serta pergeseran jenjang & status siswa antar TA.")

    if not df_siswa_raw.empty and 'ta_clean' in df_siswa_raw.columns:
        df_siswa_filtered = df_siswa_raw.copy()
        
        if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_siswa_filtered.columns:
            df_siswa_filtered = df_siswa_filtered[df_siswa_filtered['lb_clean'] == selected_lb]
            
        if selected_kec != "Semua Kecamatan" and 'Kec Tinggal' in df_siswa_filtered.columns:
            df_siswa_filtered = df_siswa_filtered[df_siswa_filtered['Kec Tinggal'] == selected_kec]
            
        if selected_kel != "Semua Kelurahan" and 'Kel Tinggal' in df_siswa_filtered.columns:
            df_siswa_filtered = df_siswa_filtered[df_siswa_filtered['Kel Tinggal'] == selected_kel]

        if not df_siswa_filtered.empty:
            col_ta1, col_ta2 = st.columns(2)

            with col_ta1:
                st.subheader("1. Pertumbuhan Jumlah Siswa Terdaftar per TA")
                siswa_ta = df_siswa_filtered.groupby('ta_clean').size().reset_index(name='Jumlah Siswa')
                siswa_ta.columns = ['Tahun Ajaran', 'Jumlah Siswa']
                
                fig_siswa_ta = style_chart(px.line(
                    siswa_ta, x='Tahun Ajaran', y='Jumlah Siswa', markers=True, 
                    text='Jumlah Siswa', color_discrete_sequence=['#00cc96']
                ))
                fig_siswa_ta.update_traces(textposition="top center", line=dict(width=3))
                st.plotly_chart(fig_siswa_ta, use_container_width=True)

            with col_ta2:
                st.subheader("2. Komparasi Paket Bimbingan vs Cash In per TA")
                fin_ta = df_siswa_filtered.groupby('ta_clean').agg(
                    Nilai_Paket=('Biaya Paket', 'sum'),
                    Cash_In=('Total Bayar', 'sum')
                ).reset_index()
                fin_ta_melted = fin_ta.melt(id_vars='ta_clean', value_vars=['Nilai_Paket', 'Cash_In'], 
                                            var_name='Kategori', value_name='Nominal')
                fin_ta_melted['Kategori'] = fin_ta_melted['Kategori'].replace({'Nilai_Paket': 'Nilai Paket Bimbingan', 'Cash_In': 'Total Cash In'})
                
                fig_fin_ta = style_chart(px.bar(
                    fin_ta_melted, x='ta_clean', y='Nominal', color='Kategori', barmode='group',
                    text_auto='.3s', labels={'ta_clean': 'Tahun Ajaran'}
                ))
                st.plotly_chart(fig_fin_ta, use_container_width=True)

            st.divider()

            if 'Kategori_Siswa' in df_siswa_filtered.columns:
                st.subheader("3. Perbandingan Status Siswa (Lama / Baru / NFIC) Antar TA")
                kat_ta = df_siswa_filtered.groupby(['ta_clean', 'Kategori_Siswa']).size().reset_index(name='Jumlah Siswa')
                fig_kat_ta = style_chart(px.bar(
                    kat_ta, x='ta_clean', y='Jumlah Siswa', color='Kategori_Siswa', barmode='group',
                    text_auto=True, labels={'ta_clean': 'Tahun Ajaran', 'Kategori_Siswa': 'Status Siswa'}
                ))
                st.plotly_chart(fig_kat_ta, use_container_width=True)

            st.divider()

            st.subheader("4. Rekapitulasi Data Siswa Multi-Tahun Ajaran")
            rekap_ta = df_siswa_filtered.groupby('ta_clean').agg(
                Total_Siswa=('No', 'count'),
                Total_Paket=('Biaya Paket', 'sum'),
                Total_Bayar=('Total Bayar', 'sum'),
                Total_Tagihan=('Tagihan', 'sum'),
                Rata_Paket=('Biaya Paket', 'mean')
            ).reset_index()

            rekap_ta.columns = ['Tahun Ajaran (TA)', 'Jumlah Siswa', 'Total Nilai Paket', 'Total Cash In', 'Sisa Tagihan', 'Rata-rata Nilai Paket/Siswa']
            st.dataframe(rekap_ta, use_container_width=True)
        else:
            st.warning("Data Siswa Multi-TA tidak ditemukan untuk kombinasi Lokasi & Domisili terpilih.")

    else:
        st.warning("Data Siswa Multi-TA belum tersedia.")

# --- TAB 6: STATUS BAYAR DOMISILI ---
with tab6:
    st.header("📊 Analisis Persentase Lunas & Angsuran Berdasarkan Domisili")
    st.info("💡 **Tersinkronisasi dengan Filter:** Data di bawah ini secara otomatis beradaptasi mengikuti filter Tahun Ajaran, Lokasi Belajar, Kecamatan, dan Kelurahan yang aktif di atas.")

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
            color_discrete_map={'Lunas': '#00cc96', 'Angsuran': '#ef553b'},
            labels={domisili_col: f'{domisili_label} Domisili', 'lb_clean': 'Lokasi Belajar'}
        ))
        st.plotly_chart(fig_status_dom, use_container_width=True)

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

    else:
        st.warning("Data Siswa untuk analisis status bayar domisili tidak ditemukan untuk filter ini.")

# --- TAB 7: ANALISIS AI & EXECUTIVE SUMMARY ---
with tab7:
    st.header("🤖 Executive AI Analytics & Smart Insights Assistant")
    st.info("💡 **AI Engine Integration:** Modul ini menganalisis seluruh data pada dashboard untuk menghasilkan Laporan Eksekutif, Temuan Kunci, & Rekomendasi Strategis secara otomatis maupun melalui integrasi Google Gemini AI.")

    if not df_siswa.empty:
        # 1. OTOMATISASI HIGHLIGHT DATA
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

        # 2. INTEGRASI GEMINI AI API
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
            f"Filter Terpilih: {ta_info}, {lb_info}, {dom_info}",
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

        # 3. CHATBOT TANYA-JAWAB AI INTERAKTIF
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
