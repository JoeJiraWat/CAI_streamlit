import streamlit as st

st.set_page_config(page_title="Settings", page_icon="⚙️")
st.title("⚙️ ตั้งค่า (Settings)")

st.subheader("ป้อนข้อมูลเพื่อช่วย AI (User Input)")
st.markdown("""
ข้อมูลที่คุณป้อนในหน้านี้จะถูกบันทึกไว้ใน Session ปัจจุบัน
และจะถูกนำไปใช้เป็นส่วนหนึ่งของคำค้นหา (Query) 
ในหน้า **'1_Overview'** ครั้งถัดไป เพื่อช่วยให้ AI 
ค้นหาข้อมูลได้ตรงประเด็นมากยิ่งขึ้น
""")

# --- ใช้ `key=` เพื่อผูก Input กับ Session State โดยตรง ---
st.text_area(
    "Hashtag / Keywords ที่น่าสนใจ",
    key="user_keywords", # ⭐️ นี่คือชื่อตัวแปรใน st.session_state
    placeholder="เช่น #ครัวซองต์ร้านดัง, ขนมปังมันม่วง, เค้กวันเกิดมินิมอล"
)

# (ส่วนนี้ยังไม่ได้ต่อสาย แต่สร้างไว้ตามโจทย์)
st.text_input(
    "Link Your URL (ที่พบเจอเทรนด์)",
    key="user_urls", # ⭐️
    placeholder="https://www.tiktok.com/..."
)

if st.button("บันทึก (Save Settings)"):
    # (Streamlit จะบันทึกค่าจาก Input ที่มี key ให้อัตโนมัติ)
    st.success("บันทึกข้อมูลเรียบร้อย! (มีผลกับการวิเคราะห์ครั้งถัดไป)")

# แสดงค่าที่บันทึกไว้
st.subheader("ข้อมูลที่บันทึกไว้ใน Session นี้")
st.caption("Keywords:")
st.json(st.session_state.get('user_keywords', ""))
st.caption("URLs:")
st.json(st.session_state.get('user_urls', ""))