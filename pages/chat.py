import time
import datetime
import streamlit as st
from components import sidebar_profil, init_session 
from backend.auth import get_user_by_id
from backend.agent import agent_executor, PERSONA_AI
from streamlit_cookies_controller import CookieController
from langchain_core.messages import HumanMessage, AIMessage
from backend.session_manager import get_all_sessions, create_session, delete_session, save_message, get_session_messages, extract_and_save_nutrition, log_missing_food, rename_session

# ==========================================
# 1. CEK AUTO-LOGIN VIA COOKIE
# ==========================================
init_session()

# ==========================================
# 2. FUNGSI DIALOG (Pop-up Frontend UI)
# ==========================================
@st.dialog("✏️ Ganti Nama Riwayat")
def dialog_rename(session_id, current_name):
    new_name = st.text_input("Nama Baru", value=current_name)
    if st.button("Simpan", type="primary", use_container_width=True):
        rename_session(session_id, new_name)
        st.rerun()

@st.dialog("⚠️ Konfirmasi Hapus")
def dialog_delete(session_id):
    st.write("Apakah Anda yakin ingin menghapus percakapan ini?")
    col_y, col_n = st.columns(2)
    with col_y:
        if st.button("Ya, Hapus", type="primary", use_container_width=True):
            delete_session(session_id)
            if st.session_state.get("current_session_id") == session_id:
                st.session_state.current_session_id = None
                st.session_state.messages = []
            st.rerun()
    with col_n:
        if st.button("Batal", use_container_width=True):
            st.rerun()

# ==========================================
# 3. LOGIKA HALAMAN UTAMA
# ==========================================
if not st.session_state.logged_in:
    st.warning("🔒 Akses ditolak. Silakan login di halaman utama.")
    st.stop()

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# SIDEBAR
with st.sidebar:
    st.header("🗂️ Sesi Obrolan")

    if st.button("➕ Percakapan Baru", use_container_width=True):
        st.session_state.current_session_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("Riwayat Terdahulu")

    past_sessions = get_all_sessions(st.session_state.user_id)

    if not past_sessions:
        st.caption("Belum ada riwayat percakapan.")
    else:
        for session in past_sessions:
            col1, col2 = st.columns([5, 1], vertical_alignment="center")
            
            with col1:
                # Tombol Utama (Buka Riwayat)
                if st.button(session["session_name"], key=f"btn_sess_{session['session_id']}", use_container_width=True):
                    st.session_state.current_session_id = session["session_id"]
                    st.session_state.messages = get_session_messages(session["session_id"])
                    st.rerun()
            
            with col2:
                # Menu Titik Tiga (Popover)
                with st.popover("⋮", use_container_width=True):
                    if st.button("✏️ Ganti Nama", key=f"btn_ren_{session['session_id']}", use_container_width=True):
                        dialog_rename(session["session_id"], session["session_name"])
                        
                    if st.button("🗑️ Hapus", key=f"btn_del_{session['session_id']}", use_container_width=True):
                        dialog_delete(session["session_id"])

    sidebar_profil()

# HEADER
st.title("🤖 Agent Nutrisi")
st.caption("Sesi Aktif: Ruang Obrolan")
st.divider()

# AREA OBROLAN & INPUT
for msg in st.session_state.messages:
    if msg["role"] == "human":
        with st.chat_message("human", avatar="🧑‍💻"):
            st.markdown(f"<span class='user-msg'></span>\n{msg['content']}", unsafe_allow_html=True)
    else:
        with st.chat_message("assistant", avatar=":material/smart_toy:"):
            st.markdown(f"<span class='ai-msg'></span>\n{msg['content']}", unsafe_allow_html=True)

if prompt := st.chat_input("Tuliskan makanan yang baru saja kamu konsumsi..."):
    if st.session_state.current_session_id is None:
        
        # 2. Ubah penamaan session_name menggunakan penanggalan
        bulan_indo = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        sekarang = datetime.datetime.now()
        session_name = f"{sekarang.day} {bulan_indo[sekarang.month]} {sekarang.year}"
        
        new_id = create_session(st.session_state.user_id, session_name)
        if new_id:
            st.session_state.current_session_id = new_id
        else:
            st.error("Gagal membuat sesi di database!")
            st.stop()

    save_message(st.session_state.current_session_id, "human", prompt)
    st.session_state.messages.append({"role": "human", "content": prompt})
    
    with st.chat_message("human", avatar="🧑‍💻"):
        st.markdown(f"<span class='user-msg'></span>\n{prompt}", unsafe_allow_html=True)

    with st.chat_message("assistant", avatar=":material/smart_toy:"):
        with st.spinner("Menganalisis nutrisi..."):
            try:
                langchain_history = [PERSONA_AI]
                for m in st.session_state.messages[:-1]: 
                    if m["role"] == "human":
                        langchain_history.append(HumanMessage(content=m["content"]))
                    elif m["role"] == "assistant":
                        langchain_history.append(AIMessage(content=m["content"]))
                
                langchain_history.append(HumanMessage(content=prompt))

                respons = agent_executor.invoke({"messages": langchain_history})
                ai_reply = respons["messages"][-1].content
                st.markdown(f"<span class='ai-msg'></span>\n{ai_reply}", unsafe_allow_html=True)
                
            except Exception as e:
                ai_reply = f"Error sistem: {str(e)}"
                st.error(ai_reply)

    save_message(st.session_state.current_session_id, "assistant", ai_reply)
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
    
    extract_and_save_nutrition(st.session_state.user_id, ai_reply)
    if "[Estimasi AI]" in ai_reply:
        log_missing_food(st.session_state.user_id, prompt)
    
    st.rerun()