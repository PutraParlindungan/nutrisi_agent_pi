import streamlit as st

@st.dialog("Pengaturan Akun")
def tampilkan_profil():
    col_a, col_b = st.columns([1, 2])
    with col_a:
        img_url = f"https://api.dicebear.com/7.x/initials/svg?seed={st.session_state.username}"
        st.image(img_url, width=80)
    with col_b:
        st.markdown(f"### {st.session_state.name}")
        st.markdown(f"**Username:** @{st.session_state.username}")
        st.markdown(f"**Role:** `{st.session_state.role.upper()}`")
        st.markdown(f"**Status:** 🟢 Aktif")
    
    st.divider()
    
    st.markdown("📸 **Ganti Foto Profil**")
    uploaded_file = st.file_uploader("Upload file", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        if st.button("Simpan Foto Baru", use_container_width=True):
            st.success("Foto berhasil disiapkan untuk diunggah!")
            
    st.divider()
    
    if st.button("🚪 Keluar Akun", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def sidebar_profil():
    st.divider()
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
            <img src="https://api.dicebear.com/7.x/initials/svg?seed={st.session_state.username}" width="50" style="border-radius: 12px;">
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