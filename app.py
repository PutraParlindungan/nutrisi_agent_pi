import streamlit as st
import time
from streamlit_cookies_controller import CookieController
from backend.auth import get_user_by_id

sidebar_state = "collapsed" if not st.session_state.get("cookie_checked", False) else "auto"

st.set_page_config(
    page_title="NutriAgent", 
    page_icon="assets/favicon.png", 
    layout="wide",
    initial_sidebar_state=sidebar_state 
)

# ==========================================
# 1. INISIALISASI COOKIE GLOBAL 
# ==========================================
cookie_manager = CookieController()
st.session_state.cookie_manager = cookie_manager

# ==========================================
# 2. MANAJEMEN SESI
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = "user"
if "reg_form_key" not in st.session_state:
    st.session_state.reg_form_key = 0
if "cookie_checked" not in st.session_state:
    st.session_state.cookie_checked = False

# OBJEK HALAMAN 
hal_login = st.Page("views/login.py", title="Masuk / Daftar", icon=":material/login:")
hal_admin = st.Page("views/admin.py", title="Dasbor Super Admin", icon=":material/security:")
hal_beranda = st.Page("views/home.py", title="Dashboard", icon=":material/dashboard:")
hal_chat = st.Page("views/chat.py", title="Nutrisi Chat", icon=":material/forum:")

# === BLOK PEMERIKSAAN COOKIE ===
if not st.session_state.logged_in and not st.session_state.get("ignore_cookie", False):
    try:
        saved_user_id = cookie_manager.get('user_id')
    except TypeError:
        saved_user_id = None
    
    # Skenario 1: Cookie belum masuk dari browser (Putaran 1)
    if saved_user_id is None and not st.session_state.cookie_checked:
        # GHOST NAVIGATION: Panggil router sementara secara TERSEMBUNYI
        # agar URL aman tapi menu tidak bocor di layar.
        pg = st.navigation([hal_login, hal_admin, hal_beranda, hal_chat], position="hidden")
        
        with st.spinner("Memuat sesi Anda..."):
            time.sleep(0.5)
        st.session_state.cookie_checked = True
        st.rerun() # Rerun ke putaran 2
        
    # Skenario 2: Cookie berhasil ditangkap (Putaran 2)
    elif saved_user_id:
        try:
            user_data = get_user_by_id(int(saved_user_id))
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user_id = user_data["user_id"]
                st.session_state.name = user_data["name"]
                st.session_state.username = user_data["username"]
                st.session_state.role = user_data["role"]
                st.session_state.avatar_path = user_data["avatar_path"]
                # PENTING: Jangan ada st.rerun() di sini agar kode langsung mengalir ke bawah
        except Exception as e:
            print(f"Error membaca cookie: {e}")


# ==========================================
# 3. NAVIGASI ASLI (Setelah Status Sesi Jelas)
# ==========================================
if not st.session_state.logged_in:
    daftar_halaman = [hal_login]
else:
    if st.session_state.role == "admin":
        daftar_halaman = [hal_admin]
    else:
        daftar_halaman = [hal_beranda, hal_chat]

pg = st.navigation(daftar_halaman)

# Logika lompatan untuk login baru
if st.session_state.get("just_logged_in"):
    st.session_state.just_logged_in = False
    if st.session_state.role == "admin":
        st.switch_page(hal_admin)

# ==========================================
# 4. INJEKSI CSS KUSTOM
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    p, h1, h2, h3, h4, h5, h6, li, label, input, textarea, [data-testid="stMarkdownContainer"] {
        font-family: 'Poppins', sans-serif !important;
    }
    span.material-icons, span.material-symbols-rounded, [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }
    .stAppDeployButton { display: none !important; }
    [data-testid="stHeaderActionElements"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    
    [data-testid="stChatMessage"] {
        border-radius: 15px !important; margin-bottom: 15px !important; padding: 12px 15px !important; width: fit-content !important; max-width: 80% !important;
    }
    [data-testid="stChatMessage"]:has(.user-msg) {
        background-color: #2d5a88 !important; margin-left: auto !important; flex-direction: row-reverse !important; border: none !important;
    }
    [data-testid="stChatMessage"]:has(.user-msg) p { color: white !important; }
    [data-testid="stChatMessage"]:has(.ai-msg) {
        background-color: #262626 !important; margin-right: auto !important; border: 1px solid #444 !important;
    }
    [data-testid="stChatMessage"]:has(.ai-msg) p { color: #e0e0e0 !important; }
    [data-testid="stChatMessage"]:has(.ai-msg) [data-testid="stChatMessageAvatar"] {
        background-color: #1E1E1E !important; border: 2px solid #1999dd !important; color: #1999dd !important; border-radius: 8px !important;         
    }
    
    /* --- TAMBAHAN UNTUK KOTAK INPUT & PERINGATAN AI --- */
    div[data-testid="stChatInput"] {
        padding-bottom: 18px !important;
        margin-bottom: -25px !important;
        padding-bottom: 0px !important; 
    }
    div[data-testid="stChatInput"]::after {
        content: "Agent Nutrisi dapat membuat kesalahan.";
        position: absolute;
        bottom: -25px; 
        left: 0;
        right: 0;
        text-align: center;
        font-size: 13px; 
        color: gray;
    }
    /* Persempit jarak atas/bawah pada divider */
    hr, .stDivider, [data-testid="stDivider"] {
        margin-top: 6px !important;
        margin-bottom: 6px !important;
        padding: 0 !important;
    }
    [data-testid="stMetric"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    [data-testid="stMetricLabel"] {
        justify-content: center !important;
        width: 100% !important;
    }
    [data-testid="stMetricLabel"] p, 
    [data-testid="stMetricLabel"] span, 
    [data-testid="stMetricLabel"] label,
    [data-testid="stMetricLabel"] div {
        font-size: 24px !important; 
        font-weight: 700 !important;
    }
    [data-testid="stMetricValue"] {
        justify-content: center !important;
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

pg.run()