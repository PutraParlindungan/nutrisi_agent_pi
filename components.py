import os
import time
import base64
import streamlit as st
from backend.tools import supabase
from backend.auth import update_user_avatar, update_user_name, update_user_password, cek_password_kuat

def get_avatar_src():
    avatar_path = st.session_state.get("avatar_path")
    if avatar_path:
        if avatar_path.startswith("http"):
            return avatar_path
        if os.path.exists(avatar_path):
            with open(avatar_path, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                ext = avatar_path.split('.')[-1].lower()
                mime = f"image/{ext}" if ext in ['png', 'jpeg', 'jpg'] else "image/png"
                return f"data:{mime};base64,{b64}"
    return f"https://api.dicebear.com/7.x/initials/svg?seed={st.session_state.get('username', 'user')}"

@st.dialog("Profil Akun")
def tampilkan_profil():
    col_a, col_b = st.columns([1.2, 2])
    with col_a:
        st.image(get_avatar_src(), width="stretch")
    with col_b:
        st.markdown(f"### {st.session_state.name}")
        st.markdown(f"**Username:** @{st.session_state.username}")
        st.markdown(f"**Role:** `{st.session_state.role.upper()}`")
        st.markdown(f"**Status:** 🟢 Aktif")

    with st.expander(":material/settings: Edit Profil"):
        if "menu_edit_aktif" not in st.session_state:
            st.session_state.menu_edit_aktif = None

        st.markdown("Pilih data yang ingin Anda perbarui:")
        col1, col2, col3 = st.columns(3)
        
        menu_sekarang = st.session_state.menu_edit_aktif
        
        with col1:
            type_n = "primary" if menu_sekarang == "nama" else "secondary"
            st.button(":material/badge: Nama", type=type_n, width="stretch", 
                      on_click=lambda: st.session_state.update(menu_edit_aktif=None if st.session_state.menu_edit_aktif == "nama" else "nama"))
        
        with col2:
            type_f = "primary" if menu_sekarang == "foto" else "secondary"
            st.button(":material/image: Foto", type=type_f, width="stretch", 
                      on_click=lambda: st.session_state.update(menu_edit_aktif=None if st.session_state.menu_edit_aktif == "foto" else "foto"))
        
        with col3:
            type_s = "primary" if menu_sekarang == "password" else "secondary"
            st.button(":material/lock: Password", type=type_s, width="stretch", 
                      on_click=lambda: st.session_state.update(menu_edit_aktif=None if st.session_state.menu_edit_aktif == "password" else "password"))

        # --- LOGIKA EDIT NAMA ---
        if st.session_state.menu_edit_aktif == "nama":
            st.divider()
            st.caption("Edit Nama Lengkap")
            
            # Gunakan session_state key agar bisa dikosongkan
            if "input_nama_baru" not in st.session_state:
                st.session_state.input_nama_baru = st.session_state.name
                
            new_name = st.text_input("Nama Baru", key="input_nama_baru")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Simpan", type="primary", width="stretch", key="save_n"):
                    if new_name.strip() and new_name != st.session_state.name:
                        if update_user_name(st.session_state.user_id, new_name):
                            st.session_state.name = new_name
                            # Tutup sub-menu setelah sukses (mengosongkan input secara alami)
                            st.session_state.menu_edit_aktif = None 
                            st.rerun() # Diperlukan khusus nama agar header profil langsung berubah
                    else:
                        st.warning("Nama tidak boleh kosong atau sama dengan yang lama.")
            with c2:
                st.button("Batal", width="stretch", key="cancel_n", on_click=lambda: st.session_state.update(menu_edit_aktif=None))

        # --- LOGIKA EDIT FOTO ---
        elif st.session_state.menu_edit_aktif == "foto":
            st.divider()
            st.caption("Ganti Foto Profil")
            uploaded_file = st.file_uploader("Pilih file gambar", type=["jpg", "png", "jpeg"], key="uploader_foto")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Simpan", type="primary", width="stretch", key="save_f"):
                    if uploaded_file:
                        if uploaded_file.size > 2 * 1024 * 1024: # Validasi ukuran maks 2MB
                            st.error("Ukuran foto maksimal 2MB!")
                        else:
                            try:
                                file_ext = uploaded_file.name.split('.')[-1].lower()
                                file_name = f"user_{st.session_state.user_id}.{file_ext}"
                                
                                # Proses Upload
                                res = supabase.storage.from_("avatars").upload(
                                    path=file_name, 
                                    file=uploaded_file.getvalue(), 
                                    file_options={"cache-control": "3600", "upsert": "true"}
                                )

                                st.info(f"Respon Supabase: {res}")
                                
                                file_path = supabase.storage.from_("avatars").get_public_url(file_name)
                                
                                if update_user_avatar(st.session_state.user_id, file_path):
                                    st.session_state.avatar_path = file_path
                                    st.session_state.menu_edit_aktif = None 
                                    st.success("✅ Foto berhasil diupload!")
                                    time.sleep(1.5)
                                    st.rerun()
                                    
                            except Exception as e:
                                # INI KUNCI DEBUGGING-NYA
                                st.error(f"❌ Supabase Error: {e}")
                    else:
                        st.warning("Silakan pilih foto terlebih dahulu.")
            with c2:
                st.button("Batal", width="stretch", key="cancel_f", on_click=lambda: st.session_state.update(menu_edit_aktif=None))

        # --- LOGIKA EDIT PASSWORD ---
        elif st.session_state.menu_edit_aktif == "password":
            st.divider()
            st.caption("Perbarui Kata Password")
            
            # Inisialisasi counter unik jika belum ada
            if "password_counter" not in st.session_state:
                st.session_state.password_counter = 0
            
            # Tempelkan counter ke dalam key agar menjadi dinamis (misal: "old_p_0", "old_p_1", dst)
            k = str(st.session_state.password_counter)
            old_p = st.text_input("Password Lama", type="password", key=f"old_p_{k}")
            new_p = st.text_input("Password Baru", type="password", key=f"new_p_{k}")
            conf_p = st.text_input("Konfirmasi Password", type="password", key=f"conf_p_{k}")
            
            c1, c2 = st.columns(2)
            with c1:
                # Tambahkan key acak di tombol juga agar tidak bentrok
                if st.button("Simpan", type="primary", width="stretch", key=f"btn_save_s_{k}"):
                    if not old_p or not new_p or not conf_p:
                        st.warning("Semua kolom password wajib diisi!")
                    elif new_p != conf_p:
                        st.error("Konfirmasi password tidak cocok!")
                    elif old_p == new_p:
                        st.warning("Password baru tidak boleh sama dengan password lama.")
                    else:
                        # EKSEKUSI VALIDASI KUAT DI SINI
                        is_strong, msg_strength = cek_password_kuat(new_p)
                        if not is_strong:
                            st.error(f"⚠️ {msg_strength}")
                        else:
                            res = update_user_password(st.session_state.user_id, old_p, new_p)
                            if res["success"]:
                                st.session_state.password_counter += 1
                                st.session_state.menu_edit_aktif = None 
                                st.success("✅ Password berhasil diubah!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error(res["message"])
            with c2:
                st.button("Batal", width="stretch", key=f"btn_cancel_s_{k}", on_click=lambda: st.session_state.update(menu_edit_aktif=None))
    
    # ==========================================
    # LOGIKA KONFIRMASI KELUAR AKUN
    # ==========================================
    if "konfirmasi_keluar" not in st.session_state:
        st.session_state.konfirmasi_keluar = False

    if not st.session_state.konfirmasi_keluar:
        st.button(":material/logout: Keluar Akun", type="primary", width="stretch", on_click=lambda: st.session_state.update(konfirmasi_keluar=True))
    else:
        st.warning("⚠️ Apakah Anda yakin ingin keluar?")
        col_ya, col_batal = st.columns(2)
        
        with col_ya:
            if st.button("Ya, Keluar", type="primary", width="stretch"):
                # 1. Bersihkan parameter URL
                st.query_params.clear()
                
                # 2. Hapus cookie dengan aman
                if "cookie_manager" in st.session_state:
                    try:
                        st.session_state.cookie_manager.remove('user_id')
                    except Exception:
                        pass
                
                # 3. Hapus semua data memori KECUALI cookie_manager (agar tidak error)
                for key in list(st.session_state.keys()):
                    if key != "cookie_manager":
                        del st.session_state[key]
                
                # 4. KUNCI UTAMA ANTI-ZOMBIE: 
                # Beri tahu app.py untuk mengabaikan cookie yang tertinggal di browser
                st.session_state.logged_in = False
                st.session_state.ignore_cookie = True 
                
                # 5. Rerun ke halaman login
                st.rerun()
                
        with col_batal:
            st.button("Batal", width="stretch", on_click=lambda: st.session_state.update(konfirmasi_keluar=False))
       
                    
  

def sidebar_profil():

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

    if st.button(":material/account_circle: Lihat Profil", width="stretch"):
        tampilkan_profil()