import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Executive Dashboard Multi-TA - Bimbingan Belajar",
    page_icon="📊",
    layout="wide"
)

# Custom Styling (Teks Kontras & Terang)
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
st.caption("Aplikasi Analisis Keuangan, Siswa, Demografi, & Perbandingan 3 Tahun Ajaran (2425, 2526, 2627)")

# Sidebar Upload File
st.sidebar.header("📁 Upload File Excel")
file_trx = st.sidebar.file_uploader("1. Upload File Transaksi (.xlsx)", type=["xlsx"])
file_siswa = st.sidebar.file_uploader("2. Upload File Siswa (.xlsx)", type=["xlsx"])
file_diskon = st.sidebar.file_uploader("3. Upload File Data Diskon (.xlsx)", type=["xlsx"])

# ---------------------------------------------------------
# LOAD & HELPER FUNCTIONS
# ---------------------------------------------------------
def clean_str(val):
    if pd.isna(val):
        return None
    return str(int(val)) if isinstance(val, (int, float)) else str(val).strip()

# 1. Data Transaksi
if file_trx is not None:
    df_trx_raw = pd.read_excel(file_trx)
else:
    try:
        df_trx_raw = pd.read_excel("20260805_data_trx_laporan.xlsx")
    except:
        df_trx_raw = pd.DataFrame()

# 2. Data Siswa
if file_siswa is not None:
    df_siswa_raw = pd.read_excel(file_siswa)
else:
    try:
        df_siswa_raw = pd.read_excel("20260805_data_siswanf.xlsx")
    except:
        df_siswa_raw = pd.DataFrame()

# 3. Data Diskon
if file_diskon is not None:
    df_diskon_raw = pd.read_excel(file_diskon)
else:
    try:
        df_diskon_raw = pd.read_excel("20260814_data_diskon.xlsx")
    except:
        df_diskon_raw = pd.DataFrame()

# Standarisasi kolom Lb dan TA untuk filtering
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
# MASTER FILTERS SIDEBAR (TA & LOKASI)
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


# Sub-Filters Spesifik Domisili & Diskon
st.sidebar.divider()
st.sidebar.header("🔍 Filter Detail")

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


# --- TAB 5: FITUR BARU - PERBANDINGAN 3 TAHUN AJARAN (2425, 2526, 2627) ---
with tab5:
    st.header("📈 Perbandingan Tren 3 Tahun Ajaran (2425 vs 2526 vs 2627)")
    st.info("💡 Tab ini menganalisis pertumbuhan bisnis dan siswa dari tahun ke tahun secara langsung.")

    col_ta1, col_ta2 = st.columns(2)

    # 1. Perbandingan Pendapatan Transaksi per TA
    with col_ta1:
        st.subheader("1. Total Pendapatan per Tahun Ajaran (TA)")
        if not df_trx_raw.empty and 'ta_clean' in df_trx_raw.columns:
            df_trx_filtered = df_trx_raw.copy()
            if selected_lb != "Semua Cabang / Lokasi":
                df_trx_filtered = df_trx_filtered[df_trx_filtered['lb_clean'] == selected_lb]

            rev_ta = df_trx_filtered.groupby('ta_clean')['Jumlah'].sum().reset_index()
            rev_ta.columns = ['Tahun Ajaran', 'Total Pendapatan']
            
            fig_rev_ta = px.bar(
                rev_ta, 
                x='Tahun Ajaran', 
                y='Total Pendapatan', 
                text_auto='.3s',
                color='Tahun Ajaran',
                color_discrete_sequence=px.colors.qualitative.Bold,
                template="plotly_dark"
            )
            st.plotly_chart(fig_rev_ta, use_container_width=True)
        else:
            st.warning("Data Transaksi Multi-TA belum tersedia.")

    # 2. Perbandingan Jumlah Siswa per TA
    with col_ta2:
        st.subheader("2. Pertumbuhan Jumlah Siswa per TA")
        if not df_siswa_raw.empty and 'ta_clean' in df_siswa_raw.columns:
            df_siswa_filtered = df_siswa_raw.copy()
            if selected_lb != "Semua Cabang / Lokasi":
                df_siswa_filtered = df_siswa_filtered[df_siswa_filtered['lb_clean'] == selected_lb]

            siswa_ta = df_siswa_filtered.groupby('ta_clean').size().reset_index(name='Jumlah Siswa')
            siswa_ta.columns = ['Tahun Ajaran', 'Jumlah Siswa']
            
            fig_siswa_ta = px.line(
                siswa_ta, 
                x='Tahun Ajaran', 
                y='Jumlah Siswa', 
                markers=True,
                text='Jumlah Siswa',
                template="plotly_dark"
            )
            fig_siswa_ta.update_traces(textposition="top center", line=dict(width=3))
            st.plotly_chart(fig_siswa_ta, use_container_width=True)
        else:
            st.warning("Data Siswa Multi-TA belum tersedia.")

    st.divider()

    # 3. Rincian Tabel Perbandingan Multi-TA
    st.subheader("3. Tabel Komparasi Kinerja Multi-Tahun Ajaran")
    if not df_siswa_raw.empty and 'ta_clean' in df_siswa_raw.columns:
        df_siswa_filtered = df_siswa_raw.copy()
        if selected_lb != "Semua Cabang / Lokasi":
            df_siswa_filtered = df_siswa_filtered[df_siswa_filtered['lb_clean'] == selected_lb]

        rekap_ta = df_siswa_filtered.groupby('ta_clean').agg(
            Total_Siswa=('No', 'count'),
            Total_Paket=('Biaya Paket', 'sum'),
            Total_Bayar=('Total Bayar', 'sum'),
            Total_Tagihan=('Tagihan', 'sum')
        ).reset_index()

        rekap_ta.columns = ['Tahun Ajaran (TA)', 'Jumlah Siswa', 'Total Nilai Paket', 'Total Cash In', 'Sisa Tagihan']
        st.dataframe(rekap_ta, use_container_width=True)
    else:
        st.warning("Data rincian Multi-TA belum tersedia.")
