import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import calendar

st.set_page_config(page_title="Trends History", page_icon="📜", layout="wide")
st.title("📜 ประวัติการวิเคราะห์ (Analysis History)")

# --- ตรวจสอบว่ามีข้อมูลหรือยัง ---
if 'run_history' not in st.session_state or not st.session_state['run_history']:
    st.warning("ยังไม่มีประวัติการวิเคราะห์ กรุณากลับไปหน้า '1_Overview' และกดวิเคราะห์ก่อน")
    
    # แสดงวิธีแก้ไข
    st.info("""
    **วิธีแก้ไข:**
    
    **วิธีที่ 1: ใช้ Overview (แนะนำ)**
    1. ไปที่หน้า **Overview** (หน้าแรก)
    2. กดปุ่ม **"🚀 Run RAG Test"**
    3. รอให้ระบบวิเคราะห์เสร็จ
    4. ข้อมูลจะถูกเก็บในประวัติอัตโนมัติ
    
    **วิธีที่ 2: ใช้หน้า Overview**
    1. ไปที่หน้า **1_Overview** (หน้าแรก)
    2. กดปุ่ม **"🚀 วิเคราะห์เทรนด์ (Analyze Trends)"**
    3. รอให้ระบบวิเคราะห์เสร็จ
    4. ข้อมูลจะถูกเก็บในประวัติอัตโนมัติ
    """)
    
    # เพิ่มปุ่มไปหน้า Overview
    if st.button("🏠 ไปหน้า Overview", type="secondary"):
        st.switch_page("1_Overview.py")
    
    st.stop()

# --- โหลดข้อมูลจาก Session State ---
# (เรียงจากใหม่สุดไปเก่าสุด)
history_runs = sorted(st.session_state['run_history'], key=lambda x: x['timestamp'], reverse=True)

# --- 1. Calendar View ---
st.subheader("📅 Calendar View")

# สร้าง calendar view
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    view_mode = st.radio(
        "กรองตามเวลา:",
        ('All', 'Day', 'Month', 'Year'), 
        horizontal=True
    )

with col2:
    if view_mode == 'Day':
        selected_date = st.date_input("เลือกวันที่", datetime.now())
    elif view_mode == 'Month':
        selected_date = st.date_input("เลือกเดือน", datetime.now())
    elif view_mode == 'Year':
        selected_date = st.date_input("เลือกปี", datetime.now())
    else:
        selected_date = datetime.now()

with col3:
    # แสดงสถิติ
    total_runs = len(history_runs)
    st.metric("Total Runs", total_runs)
    
    if total_runs > 0:
        latest_run = history_runs[0]
        st.metric("Latest Run", latest_run['timestamp'].strftime('%Y-%m-%d'))

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

# --- 2. กราฟย้อนหลัง 10 Products ---
if len(history_runs) > 0:
    st.subheader("📊 กราฟย้อนหลัง 10 Products")
    
    # รวบรวมข้อมูลจากทุกการรัน
    all_products = {}
    for run in history_runs:
        if run['results']:
            for product in run['results']:
                product_name = product.get('trend_name', 'Unknown')
                if product_name not in all_products:
                    all_products[product_name] = {
                        'name': product_name,
                        'mentions': [],
                        'dates': [],
                        'platforms': [],
                        'categories': []
                    }
                
                all_products[product_name]['mentions'].append(product.get('mention_count', 0))
                all_products[product_name]['dates'].append(run['timestamp'])
                all_products[product_name]['platforms'].append(product.get('platform', 'Unknown'))
                all_products[product_name]['categories'].append(product.get('category', 'Unknown'))
    
    # คำนวณค่าเฉลี่ยและเลือก 10 products ที่มี mention มากที่สุด
    product_stats = []
    for product_name, data in all_products.items():
        avg_mentions = sum(data['mentions']) / len(data['mentions']) if data['mentions'] else 0
        total_mentions = sum(data['mentions'])
        product_stats.append({
            'name': product_name,
            'avg_mentions': avg_mentions,
            'total_mentions': total_mentions,
            'appearances': len(data['mentions']),
            'latest_date': max(data['dates']),
            'platforms': list(set(data['platforms'])),
            'categories': list(set(data['categories']))
        })
    
    # เรียงตาม total_mentions และเลือก 10 อันดับแรก
    top_10_products = sorted(product_stats, key=lambda x: x['total_mentions'], reverse=True)[:10]
    
    if top_10_products:
        # สร้างกราฟแท่ง
        fig = px.bar(
            pd.DataFrame(top_10_products),
            x='name',
            y='total_mentions',
            title="Top 10 Products by Total Mentions",
            labels={'name': 'Product Name', 'total_mentions': 'Total Mentions'},
            color='total_mentions',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # แสดงตารางสรุป
        st.subheader("📋 สรุป Top 10 Products")
        summary_df = pd.DataFrame(top_10_products)
        summary_df = summary_df[['name', 'total_mentions', 'avg_mentions', 'appearances', 'latest_date']]
        summary_df.columns = ['Product Name', 'Total Mentions', 'Avg Mentions', 'Appearances', 'Latest Date']
        st.dataframe(summary_df, use_container_width=True)
    
    st.divider()

# --- 3. แสดงผลประวัติ ---
if not filtered_runs:
    st.warning(f"ไม่พบประวัติการวิเคราะห์สำหรับเงื่อนไข: {view_mode} ({selected_date})")
    st.stop()

st.subheader(f"📜 พบ {len(filtered_runs)} รายการ")

for i, run in enumerate(filtered_runs):
    timestamp_str = run['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    query = run['query']
    
    with st.expander(f"**Run #{len(history_runs) - i}** | {timestamp_str} | Query: **'{query}'**"):
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Query", query)
        
        with col2:
            st.metric("Results", run['total_results'])
        
        with col3:
            st.metric("Date", run['timestamp'].strftime('%Y-%m-%d'))
        
        st.markdown(f"**Instruction:** `{run['instruction']}`")
        
        results = run['results']
        if results:
            df = pd.DataFrame(results)
            
            # แสดงตารางแบบสวยงาม
            for j, row in df.head(10).iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                    
                    # ชื่อเทรนด์
                    col1.markdown(f"**{row['trend_name']}**")
                    col1.caption(row.get('description', ''))
                    
                    # ประเภทขนม
                    category = row.get('category', 'Unknown')
                    category_emoji = {
                        'Bread': '🍞',
                        'Cake': '🎂',
                        'Cookie': '🍪',
                        'Pastry': '🥐',
                        'Donut': '🍩',
                        'Muffin': '🧁',
                        'Bagel': '🥯',
                        'Croissant': '🥐',
                        'Unknown': '❓'
                    }.get(category, '❓')
                    
                    col2.markdown(f"{category_emoji} {category}")
                    
                    # จำนวนการพูดถึง
                    col3.metric("Mentions", row.get('mention_count', 0))
                    
                    # แพลตฟอร์ม
                    col4.markdown(f"📱 {row.get('platform', 'Unknown')}")
                    
                    # URL
                    if row.get('source_url') and row['source_url'] != "Unknown":
                        col5.markdown(f"🔗 [Link]({row['source_url']})")
                    
                    st.divider()
        else:
            st.write("ไม่พบผลลัพธ์ในการรันครั้งนี้")