import streamlit as st
import pandas as pd
import plotly.express as px
import glob

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Executive Dashboard Multi-TA - Bimbingan Belajar",
    page_icon="📊",
    layout="wide"
)

# Custom Styling (Fix Teks Terang di Light & Dark Mode)
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #1f2937 !important;
        padding: 15px !important;
        border-radius: 10px !important;
        border: 1px solid #374151 !important;
    }
    div[data-testid="stMetricLabel"] > div {
        color: #9ca3af !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Executive Dashboard & Analisis Multi-Tahun Ajaran")
st.caption("Aplikasi Analisis Keuangan, Pendaftaran Siswa, Demografi, & Perbandingan 3 Tahun Ajaran (2425, 2526, 2627)")

# ---------------------------------------------------------
# AUTHENTICATION & LOGIN ADMIN (SIDEBAR)
# ---------------------------------------------------------
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

files_trx = None
files_siswa = None
files_diskon = None

st.sidebar.header("🔑 Akses Admin")

if not st.session_state.admin_logged_in:
    with st.sidebar.expander("🔒 Login Admin (Upload File)"):
        input_user = st.text_input("Username", key="login_user")
        input_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if input_user == "staf" and input_pass == "nfms2026":
                st.session_state.admin_logged_in = True
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Username atau Password Salah!")
else:
    st.sidebar.success("🔓 Mode Admin (Aktif)")
    if st.sidebar.button("Logout Admin"):
        st.session_state.admin_logged_in = False
        st.rerun()

    st.sidebar.subheader("📤 Upload File Excel Baru")
    files_trx = st.sidebar.file_uploader("1. Upload File Transaksi (.xlsx)", type=["xlsx"], accept_multiple_files=True)
    files_siswa = st.sidebar.file_uploader("2. Upload File Siswa (.xlsx)", type=["xlsx"], accept_multiple_files=True)
    files_diskon = st.sidebar.file_uploader("3. Upload File Data Diskon (.xlsx)", type=["xlsx"], accept_multiple_files=True)

# Helper Function Standarisasi String
def clean_str(val):
    if pd.isna(val):
        return None
    return str(int(val)) if isinstance(val, (int, float)) else str(val).strip()

# Helper Function Auto-Load Files dari GitHub Repository jika tidak ada upload manual
def load_combined_data(uploaded_files, filename_keywords):
    if uploaded_files:
        return pd.concat([pd.read_excel(f) for f in uploaded_files], ignore_index=True)
    
    # Auto-scan seluruh file .xlsx di folder GitHub yang sesuai kata kunci
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
# LOAD & COMBINE DATASETS AUTOMATICALLY
# ---------------------------------------------------------
df_trx_raw = load_combined_data(files_trx, ["trx", "laporan", "transaksi"])
df_siswa_raw = load_combined_data(files_siswa, ["siswa", "siswanf"])
df_diskon_raw = load_combined_data(files_diskon, ["diskon"])

# Standarisasi Status Pembayaran (Lunas vs Angsuran)
if not df_siswa_raw.empty and 'Tagihan' in df_siswa_raw.columns:
    df_siswa_raw['Status Pembayaran'] = df_siswa_raw['Tagihan'].apply(lambda x: 'Lunas' if x >= 0 else 'Angsuran')

# Standarisasi Kolom Lb dan TA untuk Filtering
if not df_trx_raw.empty:
    if 'Lb' in df_trx_raw.columns:
        df_trx_raw['lb_clean'] = df_trx_raw['Lb'].apply(clean_str)
    if 'Idtahun' in df_trx_raw.columns:
        df_trx_raw['ta_clean'] = df_trx_raw['Idtahun'].apply(clean_str)

if not df_siswa_raw.empty:
    if 'lb' in df_siswa_raw.columns:
        df_siswa_raw['lb_clean'] = df_siswa_raw['lb'].apply(clean_str)
    if 'TA' in df_siswa_raw.columns:
        df_siswa_raw['ta_clean'] = df_siswa_raw['TA'].apply(clean_str)

if not df_diskon_raw.empty:
    if 'Kode Lokasi' in df_diskon_raw.columns:
        df_diskon_raw['lb_clean'] = df_diskon_raw['Kode Lokasi'].apply(clean_str)

# ---------------------------------------------------------
# MASTER FILTERS SIDEBAR (UNTUK SEMUA STAF)
# ---------------------------------------------------------
st.sidebar.divider()
st.sidebar.header("📍 Master Filter Dashboard")

# 1. Master Filter Tahun Ajaran (TA)
all_ta_set = set()
if 'ta_clean' in df_trx_raw.columns:
    all_ta_set.update(df_trx_raw['ta_clean'].dropna())
if 'ta_clean' in df_siswa_raw.columns:
    all_ta_set.update(df_siswa_raw['ta_clean'].dropna())

list_master_ta = ["Semua Tahun Ajaran"] + sorted(list(all_ta_set))
selected_ta = st.sidebar.selectbox("📅 Pilih Tahun Ajaran (TA):", list_master_ta)

# 2. Master Filter Lokasi Cabang (Lb)
all_lb_set = set()
if 'lb_clean' in df_trx_raw.columns:
    all_lb_set.update(df_trx_raw['lb_clean'].dropna())
if 'lb_clean' in df_siswa_raw.columns:
    all_lb_set.update(df_siswa_raw['lb_clean'].dropna())
if 'lb_clean' in df_diskon_raw.columns:
    all_lb_set.update(df_diskon_raw['lb_clean'].dropna())

list_master_lb = ["Semua Cabang / Lokasi"] + sorted(list(all_lb_set))
selected_lb = st.sidebar.selectbox("🏢 Pilih Cabang / Lokasi (Lb):", list_master_lb)

# Apply Filter TA & Lb to Dataframes
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

df_diskon = df_diskon_raw.copy()
if not df_diskon.empty:
    if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_diskon.columns:
        df_diskon = df_diskon[df_diskon['lb_clean'] == selected_lb]

# Sub-Filters Spesifik Status Bayar, Domisili & Diskon
st.sidebar.divider()
st.sidebar.header("🔍 Filter Detail")

if not df_siswa.empty and 'Status Pembayaran' in df_siswa.columns:
    st.sidebar.subheader("Status Pembayaran")
    list_status_bayar = ["Semua Status", "Lunas", "Angsuran"]
    selected_status = st.sidebar.selectbox("Pilih Status Pembayaran:", list_status_bayar)
    if selected_status != "Semua Status":
        df_siswa = df_siswa[df_siswa['Status Pembayaran'] == selected_status]

if not df_siswa.empty and 'Kec Tinggal' in df_siswa.columns:
    st.sidebar.subheader("Domisili Siswa")
    list_kec = ["Semua Kecamatan"] + sorted([str(x) for x in df_siswa['Kec Tinggal'].dropna().unique()])
    selected_kec = st.sidebar.selectbox("Pilih Kecamatan:", list_kec)

    if selected_kec != "Semua Kecamatan":
        sub_kel = df_siswa[df_siswa['Kec Tinggal'] == selected_kec]['Kel Tinggal'].dropna().unique()
        list_kel = ["Semua Kelurahan"] + sorted([str(x) for x in sub_kel])
        df_siswa = df_siswa[df_siswa['Kec Tinggal'] == selected_kec]
    else:
        list_kel = ["Semua Kelurahan"] + sorted([str(x) for x in df_siswa['Kel Tinggal'].dropna().unique()])
    
    selected_kel = st.sidebar.selectbox("Pilih Kelurahan:", list_kel)
    if selected_kel != "Semua Kelurahan":
        df_siswa = df_siswa[df_siswa['Kel Tinggal'] == selected_kel]

if not df_diskon.empty and 'Nama Diskon' in df_diskon.columns:
    st.sidebar.subheader("Jenis Diskon")
    list_nama_diskon = ["Semua Jenis Diskon"] + sorted([str(x) for x in df_diskon['Nama Diskon'].dropna().unique()])
    selected_nama_diskon = st.sidebar.selectbox("Pilih Diskon:", list_nama_diskon)
    if selected_nama_diskon != "Semua Jenis Diskon":
        df_diskon = df_diskon[df_diskon['Nama Diskon'] == selected_nama_diskon]

# Banner Indikator Filter
ta_info = f"TA {selected_ta}" if selected_ta != "Semua Tahun Ajaran" else "Semua TA"
lb_info = f"Cabang {selected_lb}" if selected_lb != "Semua Cabang / Lokasi" else "Semua Cabang"
st.info(f"📌 **Filter Aktif:** Menampilkan data **{ta_info}** | **{lb_info}**")

# ---------------------------------------------------------
# TABS LAYOUT
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 Keuangan Transaksi", 
    "🎓 Pendaftaran Siswa", 
    "🏫 Sekolah & Domisili",
    "🏷️ Siswa Diskon Khusus",
    "📈 Perbandingan 3 TA"
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
            fig_line = px.line(daily_trx, x='Tanggal', y='Jumlah', markers=True, template="plotly_dark")
            st.plotly_chart(fig_line, use_container_width=True)

        with c2:
            st.subheader("Proporsi Metode Pembayaran")
            fig_pie = px.pie(df_trx, names='Type Bayar', values='Jumlah', hole=0.4, template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("Pendapatan per Kode Lokasi (Lb)")
        lb_summary = df_trx.groupby('Lb')['Jumlah'].sum().reset_index()
        lb_summary['Lb'] = lb_summary['Lb'].astype(str)
        fig_bar = px.bar(lb_summary, x='Lb', y='Jumlah', color='Jumlah', text_auto='.2s', template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)
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

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribusi Jenjang Kelas")
            jenjang_df = df_siswa['Jenjang'].value_counts().reset_index()
            jenjang_df.columns = ['Jenjang', 'Jumlah']
            fig_jenjang = px.bar(jenjang_df, x='Jenjang', y='Jumlah', color='Jumlah', template="plotly_dark")
            st.plotly_chart(fig_jenjang, use_container_width=True)

        with c2:
            st.subheader("Informasi NF Diperoleh Dari")
            info_df = df_siswa['Info NF dari'].value_counts().reset_index()
            info_df.columns = ['Media Info', 'Jumlah']
            fig_info = px.pie(info_df, names='Media Info', values='Jumlah', hole=0.3, template="plotly_dark")
            st.plotly_chart(fig_info, use_container_width=True)
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
            fig_sekolah = px.bar(
                top_sekolah, y='Asal Sekolah', x='Jumlah Siswa', orientation='h', 
                text='Jumlah Siswa', color='Jumlah Siswa', color_continuous_scale='Viridis', template="plotly_dark"
            )
            fig_sekolah.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_sekolah, use_container_width=True)

        with c2:
            st.write("📊 **Detail Sebaran Sekolah & Cabang**")
            sekolah_lb = df_siswa.groupby(['Asal Sekolah', 'lb']).size().reset_index(name='Jumlah Siswa')
            sekolah_lb = sekolah_lb.sort_values(by='Jumlah Siswa', ascending=False)
            st.dataframe(sekolah_lb, use_container_width=True, height=350)

        st.divider()

        st.subheader("2. Pemetaan Domisili Siswa (Kecamatan & Kelurahan)")
        col_kec, col_kel = st.columns(2)
        with col_kec:
            st.markdown("##### 📍 Sebaran Siswa per Kecamatan")
            kec_df = df_siswa['Kec Tinggal'].value_counts().reset_index()
            kec_df.columns = ['Kecamatan', 'Jumlah Siswa']
            fig_kec = px.pie(kec_df, names='Kecamatan', values='Jumlah Siswa', hole=0.4, template="plotly_dark")
            st.plotly_chart(fig_kec, use_container_width=True)

        with col_kel:
            st.markdown("##### 🏠 Top Kelurahan Tempat Tinggal Siswa")
            kel_df = df_siswa['Kel Tinggal'].value_counts().head(10).reset_index()
            kel_df.columns = ['Kelurahan', 'Jumlah Siswa']
            fig_kel = px.bar(kel_df, x='Kelurahan', y='Jumlah Siswa', text='Jumlah Siswa', color='Jumlah Siswa', template="plotly_dark")
            st.plotly_chart(fig_kel, use_container_width=True)

        st.divider()

        # ANALISIS PERSENTASE LUNAS VS ANGSURAN PER DOMISILI
        st.subheader("3. Persentase Status Pembayaran (Lunas vs Angsuran) Berdasarkan Domisili")
        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.markdown("##### 📊 Persentase Lunas vs Angsuran per Kecamatan")
            kec_summary = df_siswa.groupby('Kec Tinggal').agg(
                Total_Siswa=('No', 'count'),
                Lunas=('Status Pembayaran', lambda x: (x == 'Lunas').sum()),
                Angsuran=('Status Pembayaran', lambda x: (x == 'Angsuran').sum())
            ).reset_index()
            kec_summary['% Lunas'] = (kec_summary['Lunas'] / kec_summary['Total_Siswa'] * 100).round(1)
            kec_summary['% Angsuran'] = (kec_summary['Angsuran'] / kec_summary['Total_Siswa'] * 100).round(1)

            kec_melted = kec_summary.melt(
                id_vars=['Kec Tinggal', 'Total_Siswa'], 
                value_vars=['% Lunas', '% Angsuran'], 
                var_name='Status Pembayaran', 
                value_name='Persentase'
            )
            fig_kec_status = px.bar(
                kec_melted, x='Kec Tinggal', y='Persentase', color='Status Pembayaran', 
                text='Persentase', barmode='stack', template="plotly_dark",
                color_discrete_map={'% Lunas': '#00cc96', '% Angsuran': '#ef553b'},
                labels={'Kec Tinggal': 'Kecamatan', 'Persentase': 'Persentase (%)'}
            )
            fig_kec_status.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
            st.plotly_chart(fig_kec_status, use_container_width=True)

        with col_p2:
            st.markdown("##### 📋 Tabel Rincian Pembayaran per Kelurahan")
            kel_summary = df_siswa.groupby('Kel Tinggal').agg(
                Total_Siswa=('No', 'count'),
                Lunas=('Status Pembayaran', lambda x: (x == 'Lunas').sum()),
                Angsuran=('Status Pembayaran', lambda x: (x == 'Angsuran').sum())
            ).reset_index()
            kel_summary['% Lunas'] = (kel_summary['Lunas'] / kel_summary['Total_Siswa'] * 100).round(1)
            kel_summary['% Angsuran'] = (kel_summary['Angsuran'] / kel_summary['Total_Siswa'] * 100).round(1)
            kel_summary.columns = ['Kelurahan', 'Total Siswa', 'Jumlah Lunas', 'Jumlah Angsuran', '% Lunas', '% Angsuran']
            st.dataframe(kel_summary.sort_values(by='Total Siswa', ascending=False), use_container_width=True, height=380)

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
            fig_diskon_pie = px.pie(diskon_type, names='Nama Diskon', values='Jumlah Siswa', hole=0.4, template="plotly_dark")
            st.plotly_chart(fig_diskon_pie, use_container_width=True)

        with c2:
            diskon_lokasi = df_diskon.groupby('Kode Lokasi')['Besar Diskon'].sum().reset_index()
            diskon_lokasi['Kode Lokasi'] = diskon_lokasi['Kode Lokasi'].astype(str)
            fig_diskon_bar = px.bar(diskon_lokasi, x='Kode Lokasi', y='Besar Diskon', text_auto='.2s', color='Besar Diskon', template="plotly_dark")
            st.plotly_chart(fig_diskon_bar, use_container_width=True)
    else:
        st.warning(f"Data Diskon Khusus tidak ditemukan.")

# --- TAB 5: PERBANDINGAN SISWA & KEUTUHAN MULTI-TA (2425 vs 2526 vs 2627) ---
with tab5:
    st.header("📈 Perbandingan Data Siswa & Tren 3 Tahun Ajaran")
    st.info("💡 Menganalisis pertumbuhan pendaftaran siswa, finansial paket bimbingan, serta pergeseran jenjang antar TA.")

    if not df_siswa_raw.empty and 'ta_clean' in df_siswa_raw.columns:
        df_siswa_filtered = df_siswa_raw.copy()
        if selected_lb != "Semua Cabang / Lokasi":
            df_siswa_filtered = df_siswa_filtered[df_siswa_filtered['lb_clean'] == selected_lb]

        col_ta1, col_ta2 = st.columns(2)

        with col_ta1:
            st.subheader("1. Pertumbuhan Jumlah Siswa Terdaftar per TA")
            siswa_ta = df_siswa_filtered.groupby('ta_clean').size().reset_index(name='Jumlah Siswa')
            siswa_ta.columns = ['Tahun Ajaran', 'Jumlah Siswa']
            
            fig_siswa_ta = px.line(
                siswa_ta, x='Tahun Ajaran', y='Jumlah Siswa', markers=True, 
                text='Jumlah Siswa', template="plotly_dark", color_discrete_sequence=['#00cc96']
            )
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
            
            fig_fin_ta = px.bar(
                fin_ta_melted, x='ta_clean', y='Nominal', color='Kategori', barmode='group',
                text_auto='.3s', template="plotly_dark", labels={'ta_clean': 'Tahun Ajaran'}
            )
            st.plotly_chart(fig_fin_ta, use_container_width=True)

        st.divider()

        st.subheader("3. Perbandingan Sebaran Jenjang Kelas Antar TA")
        jenjang_ta = df_siswa_filtered.groupby(['ta_clean', 'Jenjang']).size().reset_index(name='Jumlah Siswa')
        fig_jenjang_ta = px.bar(
            jenjang_ta, x='ta_clean', y='Jumlah Siswa', color='Jenjang', barmode='group',
            template="plotly_dark", labels={'ta_clean': 'Tahun Ajaran'}
        )
        st.plotly_chart(fig_jenjang_ta, use_container_width=True)

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
        st.warning("Data Siswa Multi-TA belum tersedia.")
