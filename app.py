import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Executive Dashboard - Bimbingan Belajar",
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

st.title("📊 Executive Dashboard & Analisis Demografi Siswa")
st.caption("Aplikasi Analisis Keuangan, Pendaftaran, Asal Sekolah, Domisili, & Diskon Khusus")

# Sidebar Upload File
st.sidebar.header("📁 Upload File Excel")
file_trx = st.sidebar.file_uploader("1. Upload File Transaksi (.xlsx)", type=["xlsx"])
file_siswa = st.sidebar.file_uploader("2. Upload File Siswa (.xlsx)", type=["xlsx"])
file_diskon = st.sidebar.file_uploader("3. Upload File Data Diskon (.xlsx)", type=["xlsx"])

# ---------------------------------------------------------
# LOAD DATASETS
# ---------------------------------------------------------
def clean_lb(val):
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

# Standarisasi kolom Lb untuk filtering
if not df_trx_raw.empty and 'Lb' in df_trx_raw.columns:
    df_trx_raw['lb_clean'] = df_trx_raw['Lb'].apply(clean_lb)
else:
    df_trx_raw['lb_clean'] = None

if not df_siswa_raw.empty and 'lb' in df_siswa_raw.columns:
    df_siswa_raw['lb_clean'] = df_siswa_raw['lb'].apply(clean_lb)
else:
    df_siswa_raw['lb_clean'] = None

if not df_diskon_raw.empty and 'Kode Lokasi' in df_diskon_raw.columns:
    df_diskon_raw['lb_clean'] = df_diskon_raw['Kode Lokasi'].apply(clean_lb)
else:
    df_diskon_raw['lb_clean'] = None

# ---------------------------------------------------------
# GLOBAL SIDEBAR FILTERS (MASTER FILTER CABANG)
# ---------------------------------------------------------
st.sidebar.divider()
st.sidebar.header("📍 Master Filter Lokasi Cabang")

all_lb_set = set(df_trx_raw['lb_clean'].dropna()) | set(df_siswa_raw['lb_clean'].dropna()) | set(df_diskon_raw['lb_clean'].dropna())
list_master_lb = ["Semua Cabang / Lokasi"] + sorted(list(all_lb_set))

selected_lb = st.sidebar.selectbox("Pilih Cabang / Lokasi (Lb):", list_master_lb)

# Apply Master Location Filter to All Dataframes
df_trx = df_trx_raw.copy()
if not df_trx.empty and selected_lb != "Semua Cabang / Lokasi":
    df_trx = df_trx[df_trx['lb_clean'] == selected_lb]

df_siswa = df_siswa_raw.copy()
if not df_siswa.empty and selected_lb != "Semua Cabang / Lokasi":
    df_siswa = df_siswa[df_siswa['lb_clean'] == selected_lb]

df_diskon = df_diskon_raw.copy()
if not df_diskon.empty and selected_lb != "Semua Cabang / Lokasi":
    df_diskon = df_diskon[df_diskon['lb_clean'] == selected_lb]

# Sub-Filters Spesifik di Sidebar
st.sidebar.divider()
st.sidebar.header("🔍 Filter Tambahan")

if not df_siswa.empty:
    st.sidebar.subheader("Filter Domisili Siswa")
    list_kec = ["Semua Kecamatan"] + sorted([str(x) for x in df_siswa['Kec Tinggal'].dropna().unique()])
    selected_kec = st.sidebar.selectbox("Pilih Kecamatan Tinggal:", list_kec)

    if selected_kec != "Semua Kecamatan":
        sub_kel = df_siswa[df_siswa['Kec Tinggal'] == selected_kec]['Kel Tinggal'].dropna().unique()
        list_kel = ["Semua Kelurahan"] + sorted([str(x) for x in sub_kel])
    else:
        list_kel = ["Semua Kelurahan"] + sorted([str(x) for x in df_siswa['Kel Tinggal'].dropna().unique()])
    selected_kel = st.sidebar.selectbox("Pilih Kelurahan Tinggal:", list_kel)

    if selected_kec != "Semua Kecamatan":
        df_siswa = df_siswa[df_siswa['Kec Tinggal'] == selected_kec]
    if selected_kel != "Semua Kelurahan":
        df_siswa = df_siswa[df_siswa['Kel Tinggal'] == selected_kel]

if not df_diskon.empty:
    st.sidebar.subheader("Filter Jenis Diskon")
    list_nama_diskon = ["Semua Jenis Diskon"] + sorted([str(x) for x in df_diskon['Nama Diskon'].dropna().unique()])
    selected_nama_diskon = st.sidebar.selectbox("Pilih Kategori Diskon:", list_nama_diskon)

    if selected_nama_diskon != "Semua Jenis Diskon":
        df_diskon = df_diskon[df_diskon['Nama Diskon'] == selected_nama_diskon]

# Banner Status Filter
if selected_lb != "Semua Cabang / Lokasi":
    st.info(f"📌 **Status Filter Aktif:** Menampilkan laporan khusus **Cabang / Lokasi: {selected_lb}**")
else:
    st.info("📌 **Status Filter Aktif:** Menampilkan akumulasi laporan **Semua Cabang / Lokasi**")

# ---------------------------------------------------------
# TABS LAYOUT
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "💰 Laporan Keuangan Transaksi", 
    "🎓 Pendaftaran Siswa Baru", 
    "🏫 Sekolah & Domisili Siswa",
    "🏷️ Siswa Diskon Khusus"
])

# --- TAB 1: LAPORAN TRANSAKSI ---
with tab1:
    if not df_trx.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Transaksi", f"{len(df_trx):,} Transaksi")
        col2.metric("Total Pendapatan", f"Rp {df_trx['Jumlah'].sum():,.0f}".replace(',', '.'))
        col3.metric("Rata-rata Transaksi", f"Rp {df_trx['Jumlah'].mean():,.0f}".replace(',', '.'))
        col4.metric("Cabang Dilihat", selected_lb if selected_lb != "Semua Cabang / Lokasi" else f"{df_trx['Lb'].nunique()} Lokasi")

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

        st.subheader("Detail Transaksi per Kode Lokasi (Lb)")
        lb_summary = df_trx.groupby('Lb')['Jumlah'].sum().reset_index()
        lb_summary['Lb'] = lb_summary['Lb'].astype(str)
        fig_bar = px.bar(lb_summary, x='Lb', y='Jumlah', color='Jumlah', text_auto='.2s', template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning(f"Tidak ada data Transaksi untuk Cabang {selected_lb}.")


# --- TAB 2: OVERVIEW DATA SISWA ---
with tab2:
    if not df_siswa.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Siswa (Terfilter)", f"{len(df_siswa)} Siswa")
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
        st.warning(f"Tidak ada data Siswa untuk Cabang {selected_lb} dengan filter yang dipilih.")


# --- TAB 3: ANALISIS SEKOLAH & DOMISILI SISWA ---
with tab3:
    if not df_siswa.empty:
        st.header("🏫 Analisis Asal Sekolah & Domisili Siswa")
        
        st.subheader("1. Top Asal Sekolah Pendaftar")
        c1, c2 = st.columns([2, 1])
        
        with c1:
            top_sekolah = df_siswa['Asal Sekolah'].value_counts().head(10).reset_index()
            top_sekolah.columns = ['Asal Sekolah', 'Jumlah Siswa']
            fig_sekolah = px.bar(
                top_sekolah, 
                y='Asal Sekolah', 
                x='Jumlah Siswa', 
                orientation='h', 
                text='Jumlah Siswa',
                color='Jumlah Siswa',
                color_continuous_scale='Viridis',
                template="plotly_dark"
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
            fig_kel = px.bar(
                kel_df, 
                x='Kelurahan', 
                y='Jumlah Siswa', 
                text='Jumlah Siswa',
                color='Jumlah Siswa',
                template="plotly_dark"
            )
            st.plotly_chart(fig_kel, use_container_width=True)

        st.divider()

        st.subheader("3. Data Detail Siswa (Sesuai Filter Cabang)")
        kolom_pilihan = [
            'Nama Siswa', 'Jenjang', 'lb', 'Asal Sekolah', 
            'Prov Tinggal', 'Kab/Kota Tinggal', 'Kec Tinggal', 'Kel Tinggal', 
            'Total Bayar', 'Tagihan'
        ]
        kolom_ada = [col for col in kolom_pilihan if col in df_siswa.columns]
        st.dataframe(df_siswa[kolom_ada], use_container_width=True)

    else:
        st.warning(f"Tidak ada data Sekolah/Domisili Siswa untuk Cabang {selected_lb}.")


# --- TAB 4: ANALISIS DATA DISKON KHUSUS ---
with tab4:
    if not df_diskon.empty:
        st.header("🏷️ Analisis Siswa Pendaftar Diskon Khusus")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Penerima Diskon", f"{len(df_diskon)} Siswa")
        col2.metric("Total Nominal Diskon", f"Rp {df_diskon['Besar Diskon'].sum():,.0f}".replace(',', '.'))
        col3.metric("Rata-rata Diskon", f"Rp {df_diskon['Besar Diskon'].mean():,.0f}".replace(',', '.'))
        col4.metric("Jenis Diskon Digunakan", f"{df_diskon['Nama Diskon'].nunique()} Kategori")

        st.divider()

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("1. Proporsi Kategori Diskon")
            diskon_type = df_diskon['Nama Diskon'].value_counts().reset_index()
            diskon_type.columns = ['Nama Diskon', 'Jumlah Siswa']
            fig_diskon_pie = px.pie(
                diskon_type, 
                names='Nama Diskon', 
                values='Jumlah Siswa', 
                hole=0.4,
                template="plotly_dark"
            )
            st.plotly_chart(fig_diskon_pie, use_container_width=True)

        with c2:
            st.subheader("2. Total Nominal Diskon per Kode Lokasi Cabang")
            diskon_lokasi = df_diskon.groupby('Kode Lokasi')['Besar Diskon'].sum().reset_index()
            diskon_lokasi['Kode Lokasi'] = diskon_lokasi['Kode Lokasi'].astype(str)
            fig_diskon_bar = px.bar(
                diskon_lokasi, 
                x='Kode Lokasi', 
                y='Besar Diskon', 
                text_auto='.2s',
                color='Besar Diskon',
                template="plotly_dark"
            )
            st.plotly_chart(fig_diskon_bar, use_container_width=True)

        st.divider()

        st.subheader("3. Data Detail Siswa Penerima Diskon Khusus")
        kolom_diskon_show = ['No NF', 'Nama Siswa', 'Kode Lokasi', 'Nomor Formulir', 'Kwitansi', 'Nama Diskon', 'Besar Diskon']
        kolom_diskon_ada = [c for c in kolom_diskon_show if c in df_diskon.columns]
        
        st.dataframe(df_diskon[kolom_diskon_ada], use_container_width=True)
    else:
        st.warning(f"Tidak ada data Siswa Diskon Khusus untuk Cabang {selected_lb}.")