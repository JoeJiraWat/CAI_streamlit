import streamlit as st

# === ตั้งค่าหน้าจอ (ต้องเป็นคำสั่งแรก) ===
st.set_page_config(
    page_title="Bakery Trends Overview",
    page_icon="🥐",
    layout="wide"
)

import pandas as pd
import plotly.graph_objects as go
import json
from datetime import datetime

# Import ทุกอย่างจาก core service
from core_rag_service import (
    load_csv_insights, 
    get_bakery_trends, 
    get_ai_summary, 
    get_platform_icon,
    calculate_rank_changes
)

# === 1. โหลดข้อมูลพื้นฐาน (CSV) ===
# (จะทำงานแค่ครั้งแรก แล้วดึงจาก Cache)
CSV_INSIGHTS, CSV_LOADED = load_csv_insights()

# === 2. Initial Session State ===
# (สร้าง "หน่วยความจำ" ประจำ Session)
if 'run_history' not in st.session_state:
    st.session_state['run_history'] = [] # สำหรับหน้า History
if 'current_trends' not in st.session_state:
    st.session_state['current_trends'] = [] # ผลลัพธ์ล่าสุด
if 'previous_trends' not in st.session_state:
    st.session_state['previous_trends'] = [] # ผลลัพธ์ก่อนหน้า (สำหรับเทียบอันดับ)
if 'ai_summary' not in st.session_state:
    st.session_state['ai_summary'] = "" # บทวิเคราะห์ AI
if 'user_keywords' not in st.session_state:
    st.session_state['user_keywords'] = "" # จากหน้า Setting


st.title("🥐 ภาพรวมเทรนด์เบเกอรี่ (Bakery Trends Overview)")

# === 3. ส่วนควบคุม (Input) ===
with st.container(border=True):
    st.subheader("วิเคราะห์เทรนด์")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        query_topic = st.text_input(
            "หัวข้อที่สนใจ (Topic)", 
            "เบเกอรี่",
            help="เช่น เบเกอรี่, คุกกี้, ขนมปัง, เค้ก"
        )
    with col2:
        user_instruction = st.text_input(
            "คำสั่งพิเศษ (Instruction)", 
            f"เทรนด์ {query_topic} 10 อันดับแรกในไทย"
        )

    if st.button("🚀 วิเคราะห์เทรนด์ (Analyze Trends)", type="primary", use_container_width=True):
        if not CSV_LOADED:
            st.error("ไม่สามารถวิเคราะห์ได้: ไฟล์ CSV มีปัญหา กรุณาตรวจสอบ")
        else:
            with st.spinner(f"กำลังค้นหาเทรนด์ '{query_topic}' จากเว็บและวิเคราะห์โดย Gemini..."):
                
                # 1. ดึง Keyword จากหน้า Setting
                user_keywords = st.session_state.get('user_keywords', "")
                
                # 2. เรียก RAG
                new_results = get_bakery_trends(
                    query_topic=query_topic,
                    user_instruction=user_instruction,
                    csv_keywords=CSV_INSIGHTS,
                    user_keywords=user_keywords
                )
                
                # 3. อัปเดต Session State (สำคัญมาก)
                # (อันเก่าสุด -> อันก่อนหน้า)
                st.session_state['previous_trends'] = st.session_state['current_trends']
                # (อันใหม่ -> อันปัจจุบัน)
                st.session_state['current_trends'] = new_results
                
                # 4. เรียก AI Summary
                summary = get_ai_summary(json.dumps(new_results))
                st.session_state['ai_summary'] = summary
                
                # 5. บันทึกประวัติ (สำหรับหน้า History)
                st.session_state['run_history'].append({
                    "timestamp": datetime.now(),
                    "query": query_topic,
                    "instruction": user_instruction,
                    "results": new_results
                })
                
                st.success(f"วิเคราะห์ '{query_topic}' สำเร็จ! พบ {len(new_results)} รายการ")

# === 4. ส่วนแสดงผล (Display) ===
if not st.session_state['current_trends']:
    st.info("กรุณากด 'วิเคราะห์เทรนด์' เพื่อเริ่มใช้งาน")
    st.stop()

# --- กราฟวงกลม และ AI วิเคราะห์ ---
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("สัดส่วนแพลตฟอร์ม (Platform %)")
    
    # 1. เตรียมข้อมูลสำหรับกราฟ
    df = pd.DataFrame(st.session_state['current_trends'])
    if not df.empty and 'platform' in df.columns:
        platform_counts = df['platform'].value_counts()
        
        # สีตามที่กำหนด
        colors_map = {
            'Instagram': '#8fb6ff',
            'TikTok': '#b7ffd8',
            'Facebook': '#ffe08a',
            'Twitter': '#ffb385',
            'Other': '#d7d7d7'
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=platform_counts.index, 
            values=platform_counts.values,
            hole=.4, # ทำให้เป็น Donut
            marker=dict(colors=[colors_map.get(c, '#d7d7d7') for c in platform_counts.index]),
            pull=[0.05 if i == 0 else 0 for i in range(len(platform_counts))] # ดึงชิ้นใหญ่สุด
        )])
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            legend_title_text='Platforms'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("ไม่พบข้อมูลแพลตฟอร์ม")

with col2:
    st.subheader("🧠 AI วิเคราะห์เชิงลึก")
    with st.container(height=350, border=True):
        st.markdown(st.session_state.get('ai_summary', "รอการวิเคราะห์..."))


# --- ตารางเทรนด์ยอดฮิต 10 อันดับ ---
st.subheader("📊 10 เทรนด์ยอดฮิต (Top 10 Trends)")

# คำนวณอันดับ
processed_trends = calculate_rank_changes(
    st.session_state['current_trends'],
    st.session_state['previous_trends']
)

# 1. สร้าง Header
cols = st.columns([0.5, 1, 3, 1.5, 1, 1])
cols[0].markdown("**อันดับ**")
cols[1].markdown("**อันดับ (เดิม)**")
cols[2].markdown("**ชื่อสินค้า (Product)**")
cols[3].markdown("**Hashtag**")
cols[4].markdown("**พูดถึง (Mentions)**")
cols[5].markdown("**แหล่งที่มา (Source)**")
st.divider()

# 2. แสดงผล Top 10
for item in processed_trends[:10]:
    cols = st.columns([0.5, 1, 3, 1.5, 1, 1])
    
    # อันดับ
    cols[0].markdown(f"### {item.get('rank', 'N/A')}")
    
    # การเปลี่ยนแปลง (สี)
    color = item.get('rank_change_color', 'gray')
    change_str = item.get('rank_change_str', '➖')
    cols[1].markdown(f":{color}[**{change_str}**]")
    
    # ชื่อสินค้า
    cols[2].markdown(f"**{item.get('trend_name', 'N/A')}**\n\n*{item.get('description', '[ไม่ระบุ]')}*")
    
    # Hashtag
    cols[3].caption(f"{item.get('hashtag', '[ไม่พบข้อมูล]')}")
    
    # ยอดพูดถึง
    cols[4].metric("Mentions", item.get('mention_count', 0))

    # แหล่งที่มา
    platform = item.get('platform', 'Unknown')
    icon = get_platform_icon(platform)
    cols[5].markdown(f"{icon} {platform}")
    
    st.divider()