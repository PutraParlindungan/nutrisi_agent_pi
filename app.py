import streamlit as st

st.set_page_config(page_title="NutriAgent - AI Nutritionist", page_icon="🥗", layout="wide")

# 1. Inisialisasi halaman dasar
daftar_halaman = [
    st.Page("pages/main.py", title="Dashboard", icon=":material/dashboard:")
]

# 2. Penambahan halaman berdasarkan status sesi
if st.session_state.get("logged_in"):
    daftar_halaman.append(
        st.Page("pages/chat.py", title="Agent Nutrisi", icon=":material/smart_toy:")
    )
    
if st.session_state.get("logged_in") and st.session_state.get("role") == "admin":
    daftar_halaman.append(
        st.Page("pages/3_admin.py", title="Super Admin", icon=":material/security:")
    )

pg = st.navigation(daftar_halaman)

# 3. Injeksi CSS Kustom (Tetap sama seperti aslinya)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

    p, h1, h2, h3, h4, h5, h6, li, label, input, textarea, [data-testid="stMarkdownContainer"] {
        font-family: 'Poppins', sans-serif !important;
    }

    span.material-icons, 
    span.material-symbols-rounded, 
    [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }

    .stAppDeployButton { display: none !important; }
    [data-testid="stHeaderActionElements"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent !important; }

    [data-testid="stChatMessage"] {
        border-radius: 15px !important;
        margin-bottom: 15px !important;
        padding: 12px 15px !important;
        width: fit-content !important;
        max-width: 80% !important;
    }

    [data-testid="stChatMessage"]:has(.user-msg) {
        background-color: #2d5a88 !important; 
        margin-left: auto !important;         
        flex-direction: row-reverse !important; 
        border: none !important;
    }
    [data-testid="stChatMessage"]:has(.user-msg) p { color: white !important; }

    [data-testid="stChatMessage"]:has(.ai-msg) {
        background-color: #262626 !important; 
        margin-right: auto !important;        
        border: 1px solid #444 !important;
    }
    [data-testid="stChatMessage"]:has(.ai-msg) p { color: #e0e0e0 !important; }

    [data-testid="stChatMessage"]:has(.ai-msg) [data-testid="stChatMessageAvatar"] {
        background-color: #1E1E1E !important; 
        border: 2px solid #1999dd !important;  
        color: #1999dd !important;             
        border-radius: 8px !important;         
    }
    
    [data-testid="stChatMessageAvatar"] svg {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

pg.run()