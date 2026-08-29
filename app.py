import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import json
import urllib.request
import urllib.error
from datetime import datetime
import io

# ---------------------------------------------------------
# KONFIGURASI HALAMAN WEB & THEME
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive Dashboard Multi-TA - Bimbingan Belajar Nurul Fikri",
    page_icon="📊",
    layout="wide"
)

# Custom Styling Adaptive Theme & Branded PDF Download Button
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
    
    /* Styling Custom Download Button - Nurul Fikri Theme */
    div.stDownloadButton > button {
        background: linear-gradient(135deg, #00529C 0%, #002B5B 100%) !important;
        color: #FFFFFF !important;
        border: 2px solid #FFCC00 !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 12px rgba(0, 82, 156, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    div.stDownloadButton > button:hover {
        background: linear-gradient(135deg, #FFCC00 0%, #FFA500 100%) !important;
        color: #002B5B !important;
        border-color: #00529C !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(255, 204, 0, 0.4) !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HELPER GENERATOR PDF (FPDF / REPORTLAB FALLBACK)
# ---------------------------------------------------------
def create_pdf_report(report_text, filename_title):
    """Fungsi pembentuk dokumen PDF laporan eksekutif dengan header resmi Nurul Fikri"""
    try:
        from fpdf import FPDF
        
        class NF_PDF_Engine(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 12)
                self.set_text_color(0, 82, 156) # NF Blue
                self.cell(0, 6, 'BIMBINGAN DAN KONSULTASI BELAJAR NURUL FIKRI', 0, 1, 'C')
                self.set_font('Arial', 'I', 8)
                self.set_text_color(100, 100, 100)
                self.cell(0, 4, 'Wilayah Megapolitan Selatan - Laporan Analytics Eksekutif AI', 0, 1, 'C')
                self.line(10, 20, 200, 20)
                self.ln(6)

            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, f'BKB Nurul Fikri | Halaman {self.page_no()}', 0, 0, 'C')

        pdf = NF_PDF_Engine()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=9)
        
        lines = report_text.split('\n')
        for line in lines:
            clean_line = line.encode('latin-1', 'replace').decode('latin-1')
            if clean_line.startswith('### '):
                pdf.ln(2)
                pdf.set_font("Arial", 'B', 10)
                pdf.set_text_color(0, 82, 156)
                pdf.multi_cell(0, 5, clean_line.replace('### ', ''))
                pdf.set_font("Arial", size=9)
                pdf.set_text_color(30, 30, 30)
            elif clean_line.startswith('**') and clean_line.endswith('**'):
                pdf.set_font("Arial", 'B', 9)
                pdf.multi_cell(0, 5, clean_line.replace('**', ''))
                pdf.set_font("Arial", size=9)
            else:
                txt = clean_line.replace('**', '')
                pdf.multi_cell(0, 5, txt)

        return bytes(pdf.output())
    except Exception as e:
        # Fallback generator sederhana jika library fpdf tidak tersedia
        output_buffer = io.BytesIO()
        output_buffer.write(report_text.encode('utf-8'))
        return output_buffer.getvalue()

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

def clean_str(val):
    if pd.isna(val):
        return None
    return str(int(val)) if isinstance(val, (int, float)) else str(val).strip()

def format_lb(val):
    clean_val = clean_str(val)
    return LOCATION_MAP.get(clean_val, clean_val) if clean_val else None

def format_jenjang(val):
    if pd.isna(val):
        return None
    return JENJANG_MAP.get(str(val).strip().upper(), str(val).strip())

def get_kategori_siswa(biaya):
    try:
        biaya = float(biaya)
    except:
        return 'Lainnya'
    if biaya == 50000: return 'Siswa Lama (Rp50k)'
    elif biaya == 300000: return 'Siswa Baru (Rp300k)'
    elif biaya == 200000: return 'Siswa NFIC (Rp200k)'
    elif biaya == 0: return 'Lainnya / Gratis (Rp0)'
    else: return f'Lainnya (Rp{int(biaya):,})'

@st.cache_data(ttl=600)
def load_combined_data(uploaded_files, filename_keywords):
    if uploaded_files:
        return pd.concat([pd.read_excel(f) for f in uploaded_files], ignore_index=True)
    all_excel_files = glob.glob("*.xlsx")
    matched_files = [f for f in all_excel_files if any(kw in f.lower() for kw in filename_keywords)]
    if matched_files:
        dfs = [pd.read_excel(mf) for mf in matched_files if pd.read_excel(mf) is not None]
        if dfs: return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

# LOAD & COMBINE DATASETS
df_trx_raw = load_combined_data(files_trx, ["trx", "laporan", "transaksi"])
df_siswa_raw = load_combined_data(files_siswa, ["siswa", "siswanf"])
df_diskon_raw = load_combined_data(files_diskon, ["diskon"])

if not df_trx_raw.empty:
    if 'Lb' in df_trx_raw.columns: df_trx_raw['lb_clean'] = df_trx_raw['Lb'].apply(format_lb)
    if 'Idtahun' in df_trx_raw.columns: df_trx_raw['ta_clean'] = df_trx_raw['Idtahun'].apply(clean_str)
    if 'Biaya F' in df_trx_raw.columns: df_trx_raw['Kategori_Siswa'] = df_trx_raw['Biaya F'].apply(get_kategori_siswa)
    if 'Jenjang' in df_trx_raw.columns: df_trx_raw['Jenjang'] = df_trx_raw['Jenjang'].apply(format_jenjang)

if not df_siswa_raw.empty:
    if 'lb' in df_siswa_raw.columns: df_siswa_raw['lb_clean'] = df_siswa_raw['lb'].apply(format_lb)
    if 'TA' in df_siswa_raw.columns: df_siswa_raw['ta_clean'] = df_siswa_raw['TA'].apply(clean_str)
    if 'Biaya Formulir' in df_siswa_raw.columns: df_siswa_raw['Kategori_Siswa'] = df_siswa_raw['Biaya Formulir'].apply(get_kategori_siswa)
    if 'Jenjang' in df_siswa_raw.columns: df_siswa_raw['Jenjang'] = df_siswa_raw['Jenjang'].apply(format_jenjang)
    
    col_cara_daftar = next((c for c in df_siswa_raw.columns if 'caradaftar' in str(c).lower().replace(' ','')), None)
    df_siswa_raw['Jalur_Daftar'] = df_siswa_raw[col_cara_daftar].apply(get_jalur_pendaftaran_from_cara_daftar) if col_cara_daftar else 'Offline (Cabang / WA)'

# EKSTRAKSI DATA DISKON
list_diskon_records = []
if not df_diskon_raw.empty:
    for _, row in df_diskon_raw.iterrows():
        raw_val = pd.to_numeric(row.get('Besar Diskon'), errors='coerce')
        val_diskon = 0.0 if pd.isna(raw_val) else float(raw_val)
        raw_nama = str(row.get('Nama Diskon')).strip() if pd.notna(row.get('Nama Diskon')) else 'Diskon Khusus'
        list_diskon_records.append({
            'Nomor Formulir': clean_str(row.get('Nomor Formulir')),
            'Kwitansi': clean_str(row.get('Kwitansi')),
            'Nama Diskon': extract_diskon_juara_from_catatan(raw_nama) or raw_nama,
            'Besar Diskon': val_diskon,
            'Sumber': 'File Diskon'
        })

df_diskon_combined = pd.DataFrame(list_diskon_records)
df_diskon_raw = df_diskon_combined.copy() if not df_diskon_combined.empty else pd.DataFrame()

# ---------------------------------------------------------
# MASTER FILTER
# ---------------------------------------------------------
st.divider()

all_ta_set = set(df_siswa_raw['ta_clean'].dropna()) if 'ta_clean' in df_siswa_raw.columns else set()
list_master_ta = ["Semua Tahun Ajaran"] + sorted(list(all_ta_set))

all_lb_set = set(df_siswa_raw['lb_clean'].dropna()) if 'lb_clean' in df_siswa_raw.columns else set()
list_master_lb = ["Semua Cabang / Lokasi"] + sorted(list(all_lb_set))

list_master_jenjang = ["Semua Jenjang"] + JENJANG_ORDER

f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns(5)
with f_col1: selected_ta = st.selectbox("📅 Tahun Ajaran (TA):", list_master_ta)
with f_col2: selected_lb = st.selectbox("🏢 Lokasi Belajar:", list_master_lb)
with f_col3: selected_jenjang = st.selectbox("🎓 Jenjang Kelas:", list_master_jenjang)

df_kec_source = df_siswa_raw.copy()
if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_kec_source.columns:
    df_kec_source = df_kec_source[df_kec_source['lb_clean'] == selected_lb]

list_kec = ["Semua Kecamatan"] + (sorted([str(x) for x in df_kec_source['Kec Tinggal'].dropna().unique()]) if 'Kec Tinggal' in df_kec_source.columns else [])
with f_col4: selected_kec = st.selectbox("📍 Kecamatan:", list_kec)

list_kel = ["Semua Kelurahan"]
if selected_kec != "Semua Kecamatan" and not df_kec_source.empty:
    sub_kel = df_kec_source[df_kec_source['Kec Tinggal'] == selected_kec]['Kel Tinggal'].dropna().unique()
    list_kel += sorted([str(x) for x in sub_kel])
with f_col5: selected_kel = st.selectbox("🏠 Kelurahan:", list_kel)

# FILTER DATAFRAME
df_trx = df_trx_raw.copy()
df_siswa = df_siswa_raw.copy()
df_diskon = df_diskon_raw.copy()

if not df_siswa.empty:
    if selected_ta != "Semua Tahun Ajaran" and 'ta_clean' in df_siswa.columns: df_siswa = df_siswa[df_siswa['ta_clean'] == selected_ta]
    if selected_lb != "Semua Cabang / Lokasi" and 'lb_clean' in df_siswa.columns: df_siswa = df_siswa[df_siswa['lb_clean'] == selected_lb]
    if selected_jenjang != "Semua Jenjang" and 'Jenjang' in df_siswa.columns: df_siswa = df_siswa[df_siswa['Jenjang'] == selected_jenjang]
    if selected_kec != "Semua Kecamatan" and 'Kec Tinggal' in df_siswa.columns: df_siswa = df_siswa[df_siswa['Kec Tinggal'] == selected_kec]
    if selected_kel != "Semua Kelurahan" and 'Kel Tinggal' in df_siswa.columns: df_siswa = df_siswa[df_siswa['Kel Tinggal'] == selected_kel]

ta_info = f"TA {selected_ta}" if selected_ta != "Semua Tahun Ajaran" else "Semua TA"
lb_info = f"Lokasi: {selected_lb}" if selected_lb != "Semua Cabang / Lokasi" else "Semua Lokasi Belajar"
jj_info = f" | Jenjang: {selected_jenjang}" if selected_jenjang != "Semua Jenjang" else ""
dom_info = f" | {selected_kec}" if selected_kec != "Semua Kecamatan" else ""

st.info(f"📌 **Filter Aktif:** Menampilkan data **{ta_info}** | **{lb_info}**{jj_info}{dom_info}")

# TABS LAYOUT
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💰 Keuangan Transaksi", "🎓 Pendaftaran Siswa", "🏫 Sekolah & Domisili",
    "🏷️ Siswa Diskon Khusus", "📈 Perbandingan 3 TA", "📊 Status Bayar Domisili",
    "🤖 Analisis AI & Executive Summary"
])

with tab1:
    if not df_trx.empty:
        st.write("### Summary Transaksi")
        c1, c2 = st.columns(2)
        with c1:
            df_trx['Tanggal'] = pd.to_datetime(df_trx['Tanggal'])
            daily_trx = df_trx.groupby('Tanggal')['Jumlah'].sum().reset_index()
            st.plotly_chart(style_chart(px.line(daily_trx, x='Tanggal', y='Jumlah', markers=True)), use_container_width=True)
            st.caption("📝 **Penjelasan Grafik:** Grafik garis fluktuasi nominal pendapatan harian.")
        with c2:
            df_pie_summary = df_trx.groupby('Type Bayar').size().reset_index(name='Jumlah_Siswa')
            st.plotly_chart(style_chart(px.pie(df_pie_summary, names='Type Bayar', values='Jumlah_Siswa', hole=0.4)), use_container_width=True)
            st.caption("📝 **Penjelasan Diagram:** Diagram donat persentase metode pembayaran.")
    else: st.warning("Data Transaksi tidak ditemukan.")

with tab2:
    if not df_siswa.empty:
        st.write("### Summary Data Siswa")
        c1, c2 = st.columns(2)
        with c1:
            kat_siswa_df = df_siswa['Kategori_Siswa'].value_counts().reset_index()
            st.plotly_chart(style_chart(px.bar(kat_siswa_df, x='index', y='Kategori_Siswa', color='index')), use_container_width=True)
            st.caption("📝 **Penjelasan Diagram:** Komposisi pendaftar Baru vs Lama.")
        with c2:
            df_jalur = df_siswa['Jalur_Daftar'].value_counts().reset_index()
            st.plotly_chart(style_chart(px.pie(df_jalur, names='index', values='Jalur_Daftar', hole=0.4)), use_container_width=True)
            st.caption("📝 **Penjelasan Diagram:** Pendaftaran Online vs Offline.")
    else: st.warning("Data Siswa tidak ditemukan.")

with tab3:
    if not df_siswa.empty:
        st.write("### Top Asal Sekolah & Domisili")
        top_sekolah = df_siswa['Asal Sekolah'].value_counts().head(10).reset_index()
        st.plotly_chart(style_chart(px.bar(top_sekolah, y='index', x='Asal Sekolah', orientation='h')), use_container_width=True)
        st.caption("📝 **Penjelasan Bagan:** 10 Sekolah penyumbang pendaftar terbanyak.")
    else: st.warning("Data Sekolah/Domisili tidak ditemukan.")

with tab4:
    if not df_diskon.empty:
        st.write("### Summary Diskon Khusus & PSJ")
        diskon_type = df_diskon['Nama Diskon'].value_counts().reset_index()
        st.plotly_chart(style_chart(px.pie(diskon_type, names='index', values='Nama Diskon', hole=0.4)), use_container_width=True)
        st.caption("📝 **Penjelasan Diagram:** Proporsi jenis promo/diskon terpakai.")
    else: st.warning("Data Diskon tidak ditemukan.")

with tab5:
    st.write("### Perbandingan Multi-Tahun Ajaran")
    st.caption("Membandingkan tren kinerja antar TA secara dinamis.")

with tab6:
    st.write("### Status Bayar per Domisili")
    st.caption("Rincian Lunas vs Angsuran per wilayah.")

# --- TAB 7: ANALISIS AI & EXECUTIVE SUMMARY (DENGAN STRATEGI PROMO & PDF) ---
with tab7:
    st.header("🤖 Executive AI Analytics & Smart Insights Assistant")
    st.info("💡 **Memorandum Eksekutif AI:** Menggabungkan analisis kuantitatif dengan masukan strategi operasional cabang (Promo TryOut/MBTI, KDL/KDN Gratis, & Fitur Unggulan Flyer NF)[cite: 1, 3].")

    if not df_siswa.empty:
        sender_cabang = f"Tim Cabang {selected_lb}" if selected_lb != "Semua Cabang / Lokasi" else "Tim Gabungan Cabang (Wilayah Megapolitan Selatan)"
        current_date_str = datetime.now().strftime("%d %B %Y")

        tot_siswa = len(df_siswa)
        tot_paket = df_siswa['Biaya Paket'].sum() if 'Biaya Paket' in df_siswa.columns else 0
        tot_bayar = df_siswa['Total Bayar'].sum() if 'Total Bayar' in df_siswa.columns else 0
        tot_tagihan = abs(df_siswa['Tagihan'].sum()) if 'Tagihan' in df_siswa.columns else 0
        pct_pelunasan = (tot_bayar / tot_paket * 100) if tot_paket > 0 else 0

        st.subheader("📌 1. Operational & Marketing Inputs (Terintegrasi ke AI)")
        
        # Display operational strategy cards
        op_col1, op_col2, op_col3 = st.columns(3)
        with op_col1:
            st.markdown("🎯 **Entry Point Promo Sekolah:**")
            st.caption("Tim Cabang aktif terlibat agenda promo sekolah membawa Try Out (TO) atau Asesmen Akademik/MBTI sebagai pembuka jalan[cite: 1].")
        with op_col2:
            st.markdown("🚀 **Perekrutan Massal (START NF):**")
            st.caption("Pelaksanaan Tes Kemampuan Dasar Literasi (KDL) & Numerasi (KDN) GRATIS untuk memperluas corong perekrutan.")
        with op_col3:
            st.markdown("💎 **Value Proposition Flyer:**")
            st.caption("100% Pengajar PTN, Full Tatap Muka, Zuper Book & Digital, 24/7 SIP-NF & NF Juara, Chat Konsul, ANDARA & MBPJ[cite: 3].")

        st.divider()

        st.subheader("✨ 2. Generative AI Executive Memorandum (Google Gemini AI)")
        
        system_gemini_key = st.secrets.get("GEMINI_API_KEY", "")
        if system_gemini_key:
            user_gemini_key = system_gemini_key
            st.success("✅ **AI Key Terhubung dari Server System.**")
        else:
            with st.expander("🔑 Pengaturan API Key Google Gemini", expanded=True):
                user_gemini_key = st.text_input("Masukkan Gemini API Key Anda:", type="password", key="gemini_key_input")

        # Context Payload for Gemini
        ctx_lines = [
            f"Filter Terpilih: {ta_info}, {lb_info}, {jj_info}, {dom_info}",
            f"Total Siswa Terdaftar: {tot_siswa} Siswa",
            f"Total Target Paket Bimbingan: Rp {tot_paket:,.0f}",
            f"Total Realisasi Pembayaran (Cash In): Rp {tot_bayar:,.0f}",
            f"Rasio Pelunasan: {pct_pelunasan:.1f}%",
            f"Total Sisa Tagihan Piutang: Rp {tot_tagihan:,.0f}",
            "Strategi Promo Cabang: Kunjungan sekolah dengan TO/Asesmen MBTI sebagai entry point[cite: 1].",
            "Program Funneling: Tes Kemampuan Dasar Literasi (KDL) & Numerasi (KDN) / START NF GRATIS.",
            "Fasilitas & Fitur Flyer: 100% Pengajar PTN, Full Tatap Muka, Modul Zuper Book & Digital, SIP-NF & NF Juara, Konsultasi Chat Gratis, ANDARA & MBPJ[cite: 3]."
        ]
        data_context = "\n- ".join([""] + ctx_lines)

        if st.button("✨ Hasilkan Laporan & Rekomendasi Eksekutif dengan AI", type="primary", use_container_width=True):
            if not user_gemini_key:
                st.warning("⚠️ API Key belum dimasukkan.")
            else:
                with st.spinner("🤖 Gemini AI sedang menyusun Laporan Memorandum Eksekutif 4-Pillar..."):
                    prompt_narrative = f"""Anda adalah Management Consultant & Chief Data Officer Senior untuk BKB Nurul Fikri.
Berdasarkan data operasional, keuangan, dan strategi marketing lapangan berikut:
{data_context}

Formatlah jawaban Anda persis dalam struktur **MEMORANDUM EKSEKUTIF** profesional berikut:

**MEMORANDUM EKSEKUTIF**

**Kepada:** Manajer Wilayah Megapolitan Selatan
**Dari:** {sender_cabang}
**Tanggal:** {current_date_str}
**Subjek:** Laporan Analisis Kinerja Operasional & Keuangan: {lb_info}

---

### 1. ANALISIS DESKRIPTIF (What Happened)
(Jabarkan kondisi faktual pencapaian siswa, pendapatan cash in, omset paket, rasio pelunasan, serta partisipasi siswa dalam event Tes KDL/KDN gratis & TryOut sekolah[cite: 1]).

### 2. ANALISIS DIAGNOSTIK (Why It Happened)
(Analisis akar masalah & pemicu internal/eksternal. Mengapa rasio pelunasan mencapai angka tersebut? Seberapa efektif eksekusi tim cabang pada agenda promo sekolah dengan TO/MBTI serta konversi fitur unggulan flyer NF[cite: 1, 3]?).

### 3. ANALISIS PREDIKTIF (What Will Happen)
(Proyeksi tren ke depan. Bagaimana risiko keterlambatan pelunasan piutang? Bagaimana potensi akuisisi peserta Tes KDL/KDN gratis untuk dikonversi menjadi siswa berbayar di periode berikutnya?).

### 4. ANALISIS PRESKRIPTIF (What Should We Do)
(Rekomendasikan 4 langkah strategis taktis & konkret bagi Tim Cabang & Manajemen Wilayah. Kaitkan dengan penguatan tim promo sekolah, optimalisasi pendaftaran online, serta tindak lanjut penagihan piutang)."""
                    
                    ai_response = ask_gemini_ai(user_gemini_key, prompt_narrative)
                    st.session_state['latest_ai_report'] = ai_response

        # JIKA LAPORAN SUDAH DI-GENERATE, TAMPILKAN DAN SEDIAKAN TOMBOL DOWNLOAD PDF
        if 'latest_ai_report' in st.session_state and st.session_state['latest_ai_report']:
            st.markdown("### 📝 Hasil Laporan Analisis Eksekutif AI:")
            report_text = st.session_state['latest_ai_report']
            st.markdown(report_text)

            st.divider()

            # ELEMEN UNDUH LAPORAN BERGAYA EXCLUSIVE NURUL FIKRI
            pdf_bytes = create_pdf_report(report_text, f"Laporan_Eksekutif_NF_{selected_lb}")
            
            st.download_button(
                label="📥 UNDUH LAPORAN EKSEKUTIF (PDF) - BKB NURUL FIKRI",
                data=pdf_bytes,
                file_name=f"Memorandum_Eksekutif_NF_{selected_lb.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.divider()

        st.subheader("💬 3. Tanya AI Seputar Data Dashboard (Interactive Q&A)")
        user_question = st.text_input("Tanyakan sesuatu tentang data ini (Contoh: 'Bagaimana menaikkan konversi dari Tes KDL/KDN gratis ke pendaftar?'):", key="ai_q_input")
        if st.button("Tanyakan ke AI", use_container_width=True):
            if not user_gemini_key:
                st.warning("⚠️ API Key belum dimasukkan.")
            elif user_question:
                with st.spinner("🤖 AI sedang memproses pertanyaan Anda..."):
                    prompt_q = f"""Anda adalah asisten AI Analis Data BKB Nurul Fikri.
Konteks data dashboard:
{data_context}

Pertanyaan: '{user_question}'

Jawablah secara ringkas, lugas, ramah, dan berbasis data di atas."""
                    answer = ask_gemini_ai(user_gemini_key, prompt_q)
                    st.success(f"""**Jawaban AI:**\n\n{answer}""")

    else:
        st.warning("Data tidak tersedia untuk dilakukan analisis AI.")
