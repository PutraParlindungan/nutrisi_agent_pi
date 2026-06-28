import re
import os
import datetime
import pytz
import streamlit as st
from hashids import Hashids
from components import sidebar_profil
from backend.agent import agent_executor, PERSONA_AI, trim_history
from langchain_core.messages import HumanMessage, AIMessage
from backend.session_manager import get_all_sessions, create_session, delete_session, save_message, get_session_messages, extract_and_save_nutrition, log_missing_food, rename_session

hasher = Hashids(salt=os.getenv("HASHIDS_SALT", "fallback_salt_aman"), min_length=8)

# ==========================================
# FUNGSI DIALOG (Pop-up Frontend UI)
# ==========================================
@st.dialog("✏️ Ganti Nama Riwayat")
def dialog_rename(session_id, current_name):
    new_name = st.text_input("Nama Baru", value=current_name)
    
    # Buat dua kolom untuk tombol
    col_simpan, col_batal = st.columns(2)
    
    with col_simpan:
        if st.button("Simpan", type="primary", width="stretch"):
            if new_name.strip() and new_name != current_name:
                rename_session(session_id, new_name)
                st.rerun()
            else:
                st.warning("Nama tidak berubah.")
                
    with col_batal:
        if st.button("Batal", width="stretch"):
            st.rerun()

@st.dialog("⚠️ Konfirmasi Hapus")
def dialog_delete(session_id):
    st.write("Apakah Anda yakin ingin menghapus percakapan ini?")
    col_y, col_n = st.columns(2)
    with col_y:
        if st.button("Hapus", type="primary", width="stretch"):
            delete_session(session_id)
            if st.session_state.get("current_session_id") == session_id:
                st.session_state.current_session_id = None
                st.session_state.messages = []
            st.rerun()
    with col_n:
        if st.button("Batal", width="stretch"):
            st.rerun()

# ==========================================
# LOGIKA HALAMAN UTAMA
# ==========================================
if not st.session_state.logged_in:
    st.warning("🔒 Akses ditolak. Silakan login di halaman utama.")
    st.stop()

# BACA URL TERLEBIH DAHULU
query_params = st.query_params
url_session_id = st.query_params.get("session")

if "current_session_id" not in st.session_state:
    if url_session_id:
        # Decode teks acak kembali menjadi angka array
        decoded = hasher.decode(url_session_id)
        if decoded: # Pastikan hasil decode tidak kosong
            st.session_state.current_session_id = decoded[0]
        else:
            st.session_state.current_session_id = None
    else:
        st.session_state.current_session_id = None

if "messages" not in st.session_state:
    if st.session_state.current_session_id:
        st.session_state.messages = get_session_messages(st.session_state.current_session_id, st.session_state.user_id)
    else:
        st.session_state.messages = []

# SIDEBAR
with st.sidebar:
    st.markdown('Sesi Obrolan')

    if st.button(":material/add: Percakapan Baru", width="stretch"):
        st.session_state.current_session_id = None
        st.session_state.messages = []
        st.query_params.clear()
        st.rerun()
   
    st.markdown("Riwayat Terdahulu")

    past_sessions = get_all_sessions(st.session_state.user_id)

    if not past_sessions:
        st.caption("Belum ada riwayat percakapan.")
    else:
        for session in past_sessions:
            col1, col2 = st.columns([5, 1], vertical_alignment="center")
            
            with col1:
            # Tombol Utama (Buka Riwayat)
                label = session["session_name"]
                is_active_session = st.session_state.get("current_session_id") == session["session_id"]
                if is_active_session:
                    # Tandai sesi yang sedang aktif dengan indikator warna
                    label = f"{label}"

                if st.button(label, key=f"btn_sess_{session['session_id']}", width="stretch", type="primary" if is_active_session else "secondary"):
                    st.session_state.current_session_id = session["session_id"]
                    # Simpan juga nama sesi agar header menampilkan dengan benar
                    st.session_state.current_session_name = session["session_name"]
                    st.session_state.messages = get_session_messages(session["session_id"], st.session_state.user_id)
                    
                    # UBAH BARIS INI: gunakan session["session_id"]
                    st.query_params["session"] = hasher.encode(session["session_id"]) 
                    
                    st.rerun()
            
            with col2:
                # Menu Titik Tiga (Popover)
                with st.popover("⋮", width="stretch"):
                    if st.button(":material/edit: Ganti Nama", key=f"btn_ren_{session['session_id']}", width="stretch"):
                        dialog_rename(session["session_id"], session["session_name"])
                        
                    if st.button(":material/delete: Hapus", key=f"btn_del_{session['session_id']}", width="stretch"):
                        dialog_delete(session["session_id"])

    st.divider()
    sidebar_profil()
    

# HEADER
# Tentukan nama sesi aktif agar tidak terjadi NameError saat ditampilkan di header.
nama_sesi_aktif = ""
if st.session_state.get("current_session_id"):
    # Jika nama sudah tersimpan di session_state gunakan itu
    nama_sesi_aktif = st.session_state.get("current_session_name", "")
    # Jika belum, coba ambil dari daftar sesi di DB
    if not nama_sesi_aktif:
        try:
            sessions_lookup = get_all_sessions(st.session_state.user_id)
            for s in sessions_lookup:
                if s.get("session_id") == st.session_state.current_session_id:
                    nama_sesi_aktif = s.get("session_name", "")
                    st.session_state.current_session_name = nama_sesi_aktif
                    break
        except Exception:
            nama_sesi_aktif = ""
else:
    nama_sesi_aktif = "Tidak ada"

st.title(":material/forum: Nutrisi Chat")
st.markdown(f"<span style='color: gray;'>Sesi Aktif: <b>{nama_sesi_aktif}</b></span>", unsafe_allow_html=True)
st.divider()

# AREA OBROLAN & INPUT
for msg in st.session_state.messages:
    if msg["role"] == "human":
        # Pakai ikon bawaan yang statis dan super ringan
        with st.chat_message("human", avatar=":material/sentiment_satisfied:"):
            st.markdown(f"<span class='user-msg'></span>\n{msg['content']}", unsafe_allow_html=True)
    else:
        # Pakai ikon bawaan yang statis dan super ringan
        with st.chat_message("assistant", avatar=":material/robot:"):
            st.markdown(f"<span class='ai-msg'></span>\n{msg['content']}", unsafe_allow_html=True)

if prompt := st.chat_input("Tuliskan makanan yang baru saja kamu konsumsi..."):
    
    # 1. UPDATE UI DULU: Masukkan pesan ke state dan langsung render ke layar
    st.session_state.messages.append({"role": "human", "content": prompt})
    
    with st.chat_message("human", avatar=":material/sentiment_satisfied:"):
        st.markdown(f"<span class='user-msg'></span>\n{prompt}", unsafe_allow_html=True)

    # 2. BUKA SPINNER AI: Pindahkan semua proses berat ke balik layar animasi ini
    with st.chat_message("assistant", avatar=":material/robot:"):
        with st.spinner("Menganalisis nutrisi..."):
            
            # --- PROSES DATABASE (Sesi & Simpan Pesan User) ---
            sesi_baru = False
            if st.session_state.current_session_id is None:
                sesi_baru = True
                bulan_indo = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
                tz_wib = pytz.timezone('Asia/Jakarta')
                sekarang = datetime.datetime.now(tz_wib)
                session_name = f"{sekarang.day} {bulan_indo[sekarang.month]} {sekarang.year}"
                
                new_id = create_session(st.session_state.user_id, session_name)
                if new_id:
                    st.session_state.current_session_id = new_id
                    st.session_state.current_session_name = session_name
                    st.query_params["session"] = hasher.encode(new_id) 

            # Simpan pesan user SEKARANG (saat roda loading berputar)
            save_message(st.session_state.current_session_id, "human", prompt)

            # --- PROSES ORKESTRASI LLM ---
            try:
                langchain_history = [PERSONA_AI]
                # Ambil history kecuali pesan terakhir
                for m in st.session_state.messages[:-1]: 
                    if m["role"] == "human":
                        langchain_history.append(HumanMessage(content=m["content"]))
                    elif m["role"] == "assistant":
                        langchain_history.append(AIMessage(content=m["content"]))
                
                # Injeksi Waktu Server
                tz_wib = pytz.timezone('Asia/Jakarta')
                jam_sekarang = datetime.datetime.now(tz_wib).strftime("%H:%M")
                prompt_with_metadata = f"{prompt}\n\n[INFO SISTEM: Waktu server saat ini adalah jam {jam_sekarang} WIB]"
                langchain_history.append(HumanMessage(content=prompt_with_metadata))

                langchain_history = trim_history(langchain_history, max_turns=10)
                respons = agent_executor.invoke({"messages": langchain_history})
                ai_reply = respons["messages"][-1].content
                
                # Render Jawaban AI
                st.markdown(f"<span class='ai-msg'></span>\n{ai_reply}", unsafe_allow_html=True)
                
            except Exception as e:
                st.error("⚠️ Maaf, layanan AI sedang sibuk atau batas token tercapai. Silakan coba lagi.")
                st.stop()

            # --- PROSES POST-LLM (Simpan Jawaban & Ekstrak Nutrisi) ---
            save_message(st.session_state.current_session_id, "assistant", ai_reply)
            st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            
            extract_and_save_nutrition(st.session_state.user_id, ai_reply)
            
            if "estimasi ai" in ai_reply.lower():
                makanan_gagal = re.findall(r"📋\s*\*\*(.*?)\*\*\s*\(Sumber:.*Estimasi AI.*\)", ai_reply, re.IGNORECASE)
                if makanan_gagal:
                    for makanan in makanan_gagal:
                        log_missing_food(st.session_state.user_id, makanan.strip())
                else:
                    log_missing_food(st.session_state.user_id, prompt)

    # Rerun hanya untuk memunculkan sesi di sidebar (jika sesi baru)
    if sesi_baru:
        st.rerun()