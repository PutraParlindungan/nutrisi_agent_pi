import streamlit as st
import os
import time
import base64
from streamlit_cookies_controller import CookieController
from backend.auth import update_user_avatar, update_user_name, get_user_by_id


def get_avatar_src():
    avatar_path = st.session_state.get("avatar_path")
    if avatar_path and os.path.exists(avatar_path):
        with open(avatar_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            ext = avatar_path.split('.')[-1].lower()
            mime = f"image/{ext}" if ext in ['png', 'jpeg', 'jpg'] else "image/png"
            return f"data:{mime};base64,{b64}"
    return f"https://api.dicebear.com/7.x/initials/svg?seed={st.session_state.get('username', 'user')}"

@st.dialog("Pengaturan Akun")
def tampilkan_profil():
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.image(get_avatar_src(), width=80)
    with col_b:
        st.markdown(f"### {st.session_state.name}")
        st.markdown(f"**Username:** @{st.session_state.username}")
        st.markdown(f"**Role:** `{st.session_state.role.upper()}`")
        st.markdown(f"**Status:** 🟢 Aktif")
    
    st.divider()
    
    # === JADIKAN SATU DALAM EXPANDER (TOMBOL LIPAT) ===
    with st.expander("✏️ Edit Profil"):
        
        # 1. Bagian Ganti Nama
        st.markdown("**Ganti Nama Tampilan**")
        new_name = st.text_input("Nama Baru", value=st.session_state.name, label_visibility="collapsed")
        
        if st.button("Simpan Nama Baru", use_container_width=True):
            if new_name.strip() and new_name != st.session_state.name:
                if update_user_name(st.session_state.user_id, new_name):
                    st.session_state.name = new_name
                    st.success("Nama berhasil diperbarui!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Gagal menyimpan ke database.")
            elif new_name == st.session_state.name:
                st.warning("Nama belum diubah.")
                
        st.divider()
        
        # 2. Bagian Ganti Foto
        st.markdown("**Ganti Foto Profil**")
        uploaded_file = st.file_uploader("Upload file", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
        
        if uploaded_file is not None:
            if st.button("Simpan Foto Baru", use_container_width=True):
                UPLOAD_DIR = "assets/avatars"
                if not os.path.exists(UPLOAD_DIR):
                    os.makedirs(UPLOAD_DIR)
                
                file_extension = uploaded_file.name.split(".")[-1]
                file_name = f"user_{st.session_state.user_id}.{file_extension}"
                file_path = os.path.join(UPLOAD_DIR, file_name)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if update_user_avatar(st.session_state.user_id, file_path):
                    st.session_state.avatar_path = file_path
                    st.success("Foto berhasil diperbarui!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Gagal menyimpan ke database.")
                    
    # =================================================
    
    st.divider()
    
    # Tombol Keluar Akun tetap di luar agar mudah dijangkau
    if st.button("🚪 Keluar Akun", type="primary", use_container_width=True):
        # 1. Hapus cookie dari peramban
        cookie = CookieController()
        cookie.remove('user_id')
        
        # 2. Bersihkan memori Streamlit
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        time.sleep(1)
        st.rerun()

def sidebar_profil():
    # Hapus CSS panjang, biarkan kosong agar Streamlit mengurus UI-nya
    st.divider()
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
            <img src="{get_avatar_src()}" width="50" height="50" style="border-radius: 12px; object-fit: cover;">
            <div style="line-height: 1.2;">
                <b style="font-size: 16px; margin: 0; padding: 0;">{st.session_state.name}</b><br>
                <span style="color: gray; font-size: 14px; margin: 0; padding: 0;">@{st.session_state.username}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("👁️ Lihat Profil", use_container_width=True):
        tampilkan_profil()

def init_session():
    if "run_count" not in st.session_state:
        st.session_state.run_count = 0
    st.session_state.run_count += 1

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.name = ""
        st.session_state.role = "user"
        st.session_state.username = ""
        st.session_state.avatar_path = ""

    if "reg_form_key" not in st.session_state:
        st.session_state.reg_form_key = 0

    cookie = CookieController()

    if st.session_state.run_count == 1:
        st.info("🔄 Mensinkronisasi sesi Anda...")
        st.progress(50)
        st.stop()

    if st.session_state.run_count > 1:
        saved_user_id = cookie.get('user_id')
        if saved_user_id and not st.session_state.logged_in:
            user_data = get_user_by_id(saved_user_id)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user_id = user_data["user_id"]
                st.session_state.name = user_data["name"]
                st.session_state.username = user_data["username"]
                st.session_state.role = user_data["role"]
                st.session_state.avatar_path = user_data["avatar_path"]
    
    return cookie