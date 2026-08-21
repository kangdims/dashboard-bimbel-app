import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# KONFIGURASI HALAMAN
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Dashboard Sekolah",
    page_icon="🏫",
    layout="wide"
)

# ---------------------------------------------------------
# DATA MASTER FILTER
# ---------------------------------------------------------
TA_OPTIONS = ['2025/2026', '2024/2025', '2023/2024', '2022/2023']
LOKASI_OPTIONS = ['Semua Lokasi', 'Kampus Utama', 'Kampus Barat', 'Kampus Timur']
DISKON_OPTIONS = ['Semua Diskon', 'Prestasi Akademik', 'Yatim/Piatu', 'Saudara Kandung', 'Tahfizh']

DOMISILI_DATA = {
    'Semua Kecamatan': ['Semua Kelurahan'],
    'Kebayoran Baru': ['Semua Kelurahan', 'Gandaria Utara', 'Cipete Utara', 'Pulo', 'Kramat Pela'],
    'Cilandak': ['Semua Kelurahan', 'Cilandak Barat', 'Lebak Bulus', 'Pondok Labu'],
    'Tebet': ['Semua Kelurahan', 'Tebet Barat', 'Tebet Timur', 'Menteng Dalam'],
}

# ---------------------------------------------------------
# READ & SYNC URL QUERY PARAMETERS
# ---------------------------------------------------------
query_params = st.query_params

default_ta = query_params.get("ta", "2025/2026")
default_lokasi = query_params.get("lokasi", "Semua Lokasi")
default_kec = query_params.get("kecamatan", "Semua Kecamatan")
default_kel = query_params.get("kelurahan", "Semua Kelurahan")
default_diskon = query_params.get("diskon", "Semua Diskon")

# ---------------------------------------------------------
# SIDEBAR NAVIGATION (6 MENU)
# ---------------------------------------------------------
st.sidebar.title("🏫 Navigasi Dashboard")
menu = st.sidebar.radio(
    "Pilih Menu:",
    [
        "Keuangan Transaksi",
        "Pendaftaran Siswa",
        "Sekolah & Domisili",
        "Siswa Diskon Khusus",
        "Perbandingan 3 TA",
        "Status Bayar Domisili"
    ]
)

if st.sidebar.button("🔄 Reset Filter Global"):
    st.query_params.clear()
    st.rerun()

# ---------------------------------------------------------
# PANEL FILTER GLOBAL
# ---------------------------------------------------------
st.title("Sistem Informasi Executive Dashboard")
st.markdown("---")

st.subheader("⚙️ Filter Global Dashboard")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    ta_idx = TA_OPTIONS.index(default_ta) if default_ta in TA_OPTIONS else 0
    selected_ta = st.selectbox("Tahun Ajaran", TA_OPTIONS, index=ta_idx)

with col2:
    lokasi_idx = LOKASI_OPTIONS.index(default_lokasi) if default_lokasi in LOKASI_OPTIONS else 0
    selected_lokasi = st.selectbox("Lokasi Belajar", LOKASI_OPTIONS, index=lokasi_idx)

with col3:
    kec_keys = list(DOMISILI_DATA.keys())
    kec_idx = kec_keys.index(default_kec) if default_kec in kec_keys else 0
    selected_kec = st.selectbox("Kecamatan", kec_keys, index=kec_idx)

with col4:
    # Cascading Dropdown: Opsi Kelurahan menyesuaikan Kecamatan
    kel_options = DOMISILI_DATA.get(selected_kec, ['Semua Kelurahan'])
    kel_idx = kel_options.index(default_kel) if default_kel in kel_options else 0
    selected_kel = st.selectbox("Kelurahan", kel_options, index=kel_idx)

with col5:
    diskon_idx = DISKON_OPTIONS.index(default_diskon) if default_diskon in DISKON_OPTIONS else 0
    selected_diskon = st.selectbox("Jenis Diskon", DISKON_OPTIONS, index=diskon_idx)

# Simpan State Filter ke URL Query Parameter
st.query_params["ta"] = selected_ta
st.query_params["lokasi"] = selected_lokasi
st.query_params["kecamatan"] = selected_kec
st.query_params["kelurahan"] = selected_kel
st.query_params["diskon"] = selected_diskon

st.markdown("---")

# Banner Status Filter Aktif
st.info(
    f"📌 **Filter Aktif:** TA: `{selected_ta}` | Lokasi: `{selected_lokasi}` | "
    f"Kecamatan: `{selected_kec}` | Kelurahan: `{selected_kel}` | Diskon: `{selected_diskon}`"
)

# ---------------------------------------------------------
# RENDER SETIAP MENU
# ---------------------------------------------------------

# 1. MENU KEUANGAN TRANSAKSI
if menu == "Keuangan Transaksi":
    st.header("💵 Keuangan & Transaksi")
    st.caption("Ringkasan arus kas, pelunasan, dan tunggakan biaya siswa.")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Penerimaan", "Rp 1.450.000.000", "+8.2%")
    m2.metric("Sisa Piutang / Tunggakan", "Rp 185.000.000", "-3.1%")
    m3.metric("Capaian Pelunasan", "88.7%", "+2.4%")

    st.subheader("Rincian Transaksi Sesuai Filter")
    df_keuangan = pd.DataFrame({
        "ID Transaksi": ["TRX-001", "TRX-002", "TRX-003", "TRX-004"],
        "Nama Siswa": ["Ahmad Fauzi", "Siti Nurhaliza", "Budi Santoso", "Dewi Lestari"],
        "Lokasi": [selected_lokasi]*4,
        "Kecamatan": [selected_kec]*4,
        "Jenis Diskon": [selected_diskon]*4,
        "Nominal": ["Rp 2.500.000", "Rp 3.000.000", "Rp 1.800.000", "Rp 2.500.000"],
        "Status": ["Lunas", "Lunas", "Cicilan", "Lunas"]
    })
    st.dataframe(df_keuangan, use_container_width=True)

# 2. MENU PENDAFTARAN SISWA
elif menu == "Pendaftaran Siswa":
    st.header("📝 Pendaftaran Siswa Baru")
    st.caption("Statistik pendaftar, status lulus seleksi, dan registrasi ulang.")
    
    col_a, col_b = st.columns(2)
    col_a.metric(f"Total Pendaftar ({selected_ta})", "420 Siswa")
    col_b.metric("Siswa Terverifikasi", "385 Siswa")

    chart_data = pd.DataFrame({
        "Bulan": ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun"],
        "Pendaftar": [45, 60, 85, 110, 70, 50]
    })
    st.bar_chart(chart_data.set_index("Bulan"))

# 3. MENU SEKOLAH & DOMISILI
elif menu == "Sekolah & Domisili":
    st.header("🗺️ Sekolah Asal & Sebaran Domisili")
    st.caption("Pemetaan wilayah tinggal siswa dan asal sekolah pendaftar.")
    
    st.write(
        f"Demografi siswa dari **{selected_kec}** ({selected_kel}) "
        f"pada unit **{selected_lokasi}** dengan kriteria diskon **{selected_diskon}**."
    )
    
    df_domisili = pd.DataFrame({
        "Sekolah Asal": ["SMPN 1", "SMPN 5", "MTs Negeri 1", "SMP Swasta Merdeka"],
        "Kecamatan": [selected_kec]*4,
        "Kelurahan": [selected_kel]*4,
        "Jumlah Siswa": [42, 28, 19, 15]
    })
    st.table(df_domisili)

# 4. MENU SISWA DISKON KHUSUS
elif menu == "Siswa Diskon Khusus":
    st.header("🏷️ Penerima Diskon & Beasiswa")
    st.caption("Rincian penerima beasiswa berdasarkan skema khusus.")
    
    df_diskon = pd.DataFrame({
        "Kategori Diskon": [selected_diskon],
        "Lokasi Belajar": [selected_lokasi],
        "Kecamatan": [selected_kec],
        "Kelurahan": [selected_kel],
        "Jumlah Penerima": ["64 Siswa"],
        "Total Potongan": ["Rp 128.000.000"]
    })
    st.dataframe(df_diskon, use_container_width=True)

# 5. MENU PERBANDINGAN 3 TA
elif menu == "Perbandingan 3 TA":
    st.header("📊 Perbandingan Multi-Tahun Ajaran")
    
    try:
        base_year = int(selected_ta.split('/')[0])
    except ValueError:
        base_year = 2025
        
    ta_current = f"{base_year}/{base_year + 1}"
    ta_prev1 = f"{base_year - 1}/{base_year}"
    ta_prev2 = f"{base_year - 2}/{base_year - 1}"
    
    st.caption(f"Analisis tren 3 tahun berturut-turut dengan patokan Anchor Year {ta_current}.")
    
    c1, c2, c3 = st.columns(3)
    c1.metric(f"TA {ta_current} (Aktif)", "420 Siswa", "+8.5%")
    c2.metric(f"TA {ta_prev1}", "387 Siswa", "+4.2%")
    c3.metric(f"TA {ta_prev2}", "371 Siswa", "0.0%")
    
    df_compare = pd.DataFrame({
        "Metrik Aggregat": ["Total Pendaftar", "Siswa Lunas", "Penerima Diskon"],
        ta_prev2: [371, 310, 45],
        ta_prev1: [387, 340, 52],
        ta_current: [420, 385, 64]
    })
    st.dataframe(df_compare, use_container_width=True)

# 6. MENU STATUS BAYAR DOMISILI
elif menu == "Status Bayar Domisili":
    st.header("💳 Status Pembayaran per Domisili")
    st.caption("Matriks pelunasan SPP/Pangkal berbasis wilayah domisili.")
    
    st.subheader(f"Tingkat Pelunasan Wilayah: {selected_kec} ({selected_kel})")
    st.progress(0.912)
    st.write("Persentase Pelunasan: **91.2%** (Lunas: 351 siswa, Menunggak: 34 siswa)")
    
    df_bayar_domisili = pd.DataFrame({
        "Kelurahan": [selected_kel],
        "Siswa Lunas": [351],
        "Siswa Menunggak": [34],
        "Total Nominal Tunggakan": ["Rp 42.500.000"]
    })
    st.table(df_bayar_domisili)
