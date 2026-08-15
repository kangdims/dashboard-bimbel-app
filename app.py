# Sidebar Upload File (Bisa pilih/upload banyak file sekaligus)
st.sidebar.header("📁 Upload File Excel")
files_trx = st.sidebar.file_uploader("1. Upload File Transaksi (.xlsx)", type=["xlsx"], accept_multiple_files=True)
files_siswa = st.sidebar.file_uploader("2. Upload File Siswa (.xlsx)", type=["xlsx"], accept_multiple_files=True)
files_diskon = st.sidebar.file_uploader("3. Upload File Data Diskon (.xlsx)", type=["xlsx"], accept_multiple_files=True)

# ---------------------------------------------------------
# LOAD & COMBINE DATASETS AUTOMATICALLY
# ---------------------------------------------------------
# 1. Gabungkan Data Transaksi
if files_trx:
    df_trx_raw = pd.concat([pd.read_excel(f) for f in files_trx], ignore_index=True)
else:
    try:
        df_trx_raw = pd.read_excel("20260805_data_trx_laporan.xlsx")
    except:
        df_trx_raw = pd.DataFrame()

# 2. Gabungkan Data Siswa
if files_siswa:
    df_siswa_raw = pd.concat([pd.read_excel(f) for f in files_siswa], ignore_index=True)
else:
    try:
        df_siswa_raw = pd.read_excel("20260805_data_siswanf.xlsx")
    except:
        df_siswa_raw = pd.DataFrame()

# 3. Gabungkan Data Diskon
if files_diskon:
    df_diskon_raw = pd.concat([pd.read_excel(f) for f in files_diskon], ignore_index=True)
else:
    try:
        df_diskon_raw = pd.read_excel("20260814_data_diskon.xlsx")
    except:
        df_diskon_raw = pd.DataFrame()
