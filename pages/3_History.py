import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Trends History", page_icon="📜", layout="wide")
st.title("📜 ประวัติการวิเคราะห์ (Analysis History)")

# --- ตรวจสอบว่ามีข้อมูลหรือยัง ---
if 'run_history' not in st.session_state or not st.session_state['run_history']:
    st.info("ยังไม่มีประวัติการวิเคราะห์ กรุณากลับไปหน้า '1_Overview' และกดวิเคราะห์ก่อน")
    st.stop()

# --- โหลดข้อมูลจาก Session State ---
# (เรียงจากใหม่สุดไปเก่าสุด)
history_runs = sorted(st.session_state['run_history'], key=lambda x: x['timestamp'], reverse=True)

# --- 1. สร้าง Filter ---
st.subheader("ตัวกรองประวัติ (View Filter)")

col1, col2 = st.columns(2)
with col1:
    view_mode = st.radio(
        "กรองตามเวลา:",
        ('All', 'Day', 'Month', 'Year'), 
        horizontal=True,
        label_visibility="collapsed"
    )
with col2:
    selected_date = st.date_input("เลือกวันที่", datetime.now())

# --- 2. กรองข้อมูล ---
filtered_runs = []
if view_mode == 'All':
    filtered_runs = history_runs
else:
    for run in history_runs:
        ts = run['timestamp']
        if view_mode == 'Day':
            if ts.date() == selected_date:
                filtered_runs.append(run)
        elif view_mode == 'Month':
            if ts.month == selected_date.month and ts.year == selected_date.year:
                filtered_runs.append(run)
        elif view_mode == 'Year':
            if ts.year == selected_date.year:
                filtered_runs.append(run)

st.divider()

# --- 3. แสดงผลประวัติ ---
if not filtered_runs:
    st.warning(f"ไม่พบประวัติการวิเคราะห์สำหรับเงื่อนไข: {view_mode} ({selected_date})")
    st.stop()

st.subheader(f"พบ {len(filtered_runs)} รายการ")

for i, run in enumerate(filtered_runs):
    timestamp_str = run['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    query = run['query']
    
    with st.expander(f"**Run #{len(history_runs) - i}** | {timestamp_str} | Query: **'{query}'**"):
        
        st.markdown(f"**Query:** `{query}`")
        st.markdown(f"**Instruction:** `{run['instruction']}`")
        
        results = run['results']
        if results:
            df = pd.DataFrame(results)
            # แสดง Top 10 ของการรันครั้งนั้น
            st.dataframe(df.head(10), use_container_width=True)
        else:
            st.write("ไม่พบผลลัพธ์ในการรันครั้งนี้")