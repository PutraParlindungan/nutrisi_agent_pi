import streamlit as st
from components import sidebar_profil

# Pastikan sidebar profil tetap tampil
with st.sidebar:
    sidebar_profil()

# --- HEADER / HERO SECTION ---
col_logo, col_judul = st.columns([1, 10], vertical_alignment="center")

with col_logo:
    # Menggunakan path logo kustom kita
    st.image("assets/favicon.png", width="stretch") 

with col_judul:
    st.title("NutriAgent: Asisten Nutrisi Pintar")

st.markdown(f"### Halo, **{st.session_state.name}**! 👋")
st.markdown("""
NutriAgent hadir untuk membantu Anda memahami apa yang Anda konsumsi setiap hari. 
Dengan teknologi AI terkini, kami mengubah cerita makan Anda menjadi data gizi yang akurat untuk mendukung gaya hidup sehat.
""")

st.divider()

# --- SECTION 1: EDUKASI NUTRISI & POLA MAKAN ---
st.markdown("#### 🥗 Mengapa Memantau Nutrisi Itu Penting?")
col_edu1, col_edu2 = st.columns(2)

with col_edu1:
    with st.container(border=True):
        st.markdown("**⚖️ Kontrol Berat Badan**")
        st.markdown("Pencatatan kalori membantu Anda mencapai target berat badan, baik itu surplus (bulking), defisit (cutting), atau maintenance.")

with col_edu2:
    with st.container(border=True):
        st.markdown("**💪 Perbaikan Sel & Otot**")
        st.markdown("Memastikan asupan Protein yang cukup sangat vital untuk pemulihan tubuh dan menjaga massa otot tetap optimal.")

st.divider()

# --- SECTION 2: PANDUAN PENGGUNAAN (USER GUIDE) ---
st.markdown("#### 🚀 Panduan Penggunaan Sistem")
tab1, tab2, tab3 = st.tabs(["📝 Cara Input", "📊 Membaca Analisis", "🔒 Keamanan Data"])

with tab1:
    st.markdown("""
    Cukup buka menu **Nutrisi Chat** dan ceritakan apa yang Anda makan.
    - *Tips:* Masukkan detail porsi (misal: '2 potong', '1 piring besar') agar AI lebih akurat.
    - *Contoh:* "Tadi pagi saya sarapan bubur ayam tanpa kacang dan 1 sate usus."
    """)

with tab2:
    st.markdown("""
    Setiap laporan akan diproses menjadi 4 pilar gizi utama:
    - **Energi (Kalori)**: Bahan bakar harian Anda.
    - **Protein**: Untuk pembentukan jaringan tubuh.
    - **Karbohidrat**: Sumber energi utama otak dan otot.
    - **Lemak**: Mendukung hormon dan fungsi sel.
    """)

with tab3:
    st.markdown("""
    - Data Anda tersimpan secara terenkripsi dan aman di database PostgreSQL.
    - Riwayat konsumsi tidak akan terhapus meskipun Anda membersihkan sesi percakapan.
    """)

st.divider()

# --- SECTION 3: DETAIL TEKNIS (DISEMBUNYIKAN / COLLAPSIBLE) ---
with st.expander("🛠️ Spesifikasi & Arsitektur Teknis (Klik untuk Detail)"):
    st.markdown("##### Infrastruktur Sistem")
    st.markdown("""
    <table style="width:100%; border: 1px solid #444; border-collapse: collapse; font-family: 'Poppins', sans-serif;">
      <tr style="background-color: #262626; color: #1999dd;">
        <th style="padding: 12px; border: 1px solid #444; text-align: left;">Komponen Utama</th>
        <th style="padding: 12px; border: 1px solid #444; text-align: left;">Teknologi</th>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #444;"><b>AI Engine</b></td>
        <td style="padding: 10px; border: 1px solid #444;">LangGraph (Multi-Actor Orchestration)</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #444;"><b>Model (LLM)</b></td>
        <td style="padding: 10px; border: 1px solid #444;">Llama-3.3-70b-Versatile (via Groq)</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #444;"><b>Cloud Database</b></td>
        <td style="padding: 10px; border: 1px solid #444;">PostgreSQL Supabase</td>
      </tr>
    </table>
    <br>
    """, unsafe_allow_html=True)
    
    st.markdown("##### Mekanisme Pencarian Berjenjang")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**Layer 1: Local DB**\nValidasi data via database TKPI Indonesia.")
    with c2:
        st.info("**Layer 2: Global API**\nPencarian real-time via FatSecret API.")
    with c3:
        st.info("**Layer 3: AI Inference**\nEstimasi saintifik berbasis internal knowledge LLM.")

# --- FOOTER ---
st.success("🎯 **Sudah siap?** Pilih menu **Nutrisi Chat** di sebelah kiri untuk mulai mencatat!")