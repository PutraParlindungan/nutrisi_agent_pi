import streamlit as st
import uuid
import time
from components import sidebar_profil # <-- Import komponen

if "logged_in" not in st.session_state or not st.session_state.logged_in:
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

    past_sessions = [
        {"session_id": "123", "session_name": "Makan Siang Nasi Padang"},
        {"session_id": "124", "session_name": "Kalori Kopi Kenangan"}
    ]

    for session in past_sessions:
        if st.button(session["session_name"], key=session["session_id"], use_container_width=True):
            st.session_state.current_session_id = session["session_id"]
            st.session_state.messages = [{"role": "ai", "content": "Memuat riwayat obrolan..."}]
            st.rerun()

    sidebar_profil() # <-- Cukup dipanggil 1 baris ini saja!

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
        st.session_state.current_session_id = str(uuid.uuid4())

    st.session_state.messages.append({"role": "human", "content": prompt})
    
    with st.chat_message("human", avatar="🧑‍💻"):
        st.markdown(f"<span class='user-msg'></span>\n{prompt}", unsafe_allow_html=True)

    with st.chat_message("assistant", avatar=":material/smart_toy:"):
        with st.spinner("Menganalisis nutrisi..."):
            try:
                time.sleep(1.5)
                ai_reply = "Ini simulasi balasan AI. (Hapus baris ini dan buka komentar LangGraph)."
                st.markdown(f"<span class='ai-msg'></span>\n{ai_reply}", unsafe_allow_html=True)
            except Exception as e:
                ai_reply = f"Error sistem: {str(e)}"
                st.error(ai_reply)

    st.session_state.messages.append({"role": "assistant", "content": ai_reply})