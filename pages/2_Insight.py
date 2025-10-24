import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Bakery Trends Insight", page_icon="📈", layout="wide")
st.title("📈 วิเคราะห์เทรนด์เชิงลึก (Insight)")

# --- ตรวจสอบว่ามีข้อมูลหรือยัง ---
if 'current_trends' not in st.session_state or not st.session_state['current_trends']:
    st.warning("ไม่พบข้อมูลเทรนด์ กรุณากลับไปหน้า '1_Overview' และกดวิเคราะห์ก่อน")
    
    # แสดงวิธีแก้ไข
    st.info("""
    **วิธีแก้ไข:**
    
    **วิธีที่ 1: ใช้ Overview (แนะนำ)**
    1. ไปที่หน้า **Overview** (หน้าแรก)
    2. กดปุ่ม **"🚀 Run RAG Test"**
    3. รอให้ระบบวิเคราะห์เสร็จ
    4. กดปุ่ม **"🚀 ไปหน้า Insight"** ที่จะปรากฏขึ้น
    
    **วิธีที่ 2: ใช้หน้า Overview**
    1. ไปที่หน้า **1_Overview** (หน้าแรก)
    2. กดปุ่ม **"🚀 วิเคราะห์เทรนด์ (Analyze Trends)"**
    3. รอให้ระบบวิเคราะห์เสร็จ
    4. จากนั้นกลับมาหน้านี้
    """)
    
    # เพิ่มปุ่มไปหน้า Overview
    if st.button("🏠 ไปหน้า Overview", type="secondary"):
        st.switch_page("1_Overview.py")
    
    st.stop()

# --- โหลดข้อมูลจาก Session State ---
data = st.session_state['current_trends']
df = pd.DataFrame(data)

# === ฟังก์ชันสำหรับสร้างข้อมูลการพูดถึงในแต่ละวัน ===
def create_daily_mentions_chart(trends_data):
    """
    สร้างกราฟแสดงการพูดถึงในแต่ละวัน
    """
    all_daily_data = []
    
    for trend in trends_data:
        trend_name = trend.get('trend_name', 'Unknown')
        daily_mentions = trend.get('daily_mentions', [])
        
        for day_data in daily_mentions:
            all_daily_data.append({
                'trend_name': trend_name,
                'date': day_data['date'],
                'date_display': day_data['date_display'],
                'mentions': day_data['mentions'],
                'platform': trend.get('platform', 'Unknown'),
                'category': trend.get('category', 'Unknown')
            })
    
    return pd.DataFrame(all_daily_data)

def get_trends_by_date(trends_data, target_date):
    """
    ดึงเทรนด์ที่ถูกพูดถึงในวันที่กำหนด
    """
    trends_for_date = []
    
    for trend in trends_data:
        daily_mentions = trend.get('daily_mentions', [])
        for day_data in daily_mentions:
            if day_data['date'] == target_date:
                trends_for_date.append({
                    'trend_name': trend.get('trend_name', 'Unknown'),
                    'mentions': day_data['mentions'],
                    'platform': trend.get('platform', 'Unknown'),
                    'category': trend.get('category', 'Unknown'),
                    'description': trend.get('description', ''),
                    'source_url': trend.get('source_url', 'Unknown')
                })
    
    # เรียงตามจำนวนการพูดถึง
    trends_for_date.sort(key=lambda x: x['mentions'], reverse=True)
    return trends_for_date

# === ฟังก์ชันสำหรับคำนวณการเปลี่ยนแปลงอันดับ ===
def calculate_rank_changes(current_trends, previous_trends=None):
    """
    คำนวณการเปลี่ยนแปลงอันดับและคืนค่า List ใหม่พร้อมข้อมูล
    """
    if not previous_trends:
        previous_trends = []
    
    # สร้าง dict จาก previous_trends เพื่อค้นหาอันดับเดิม
    prev_ranks = {}
    for i, item in enumerate(previous_trends):
        trend_name = item.get('trend_name', '')
        if trend_name:
            prev_ranks[trend_name] = i + 1
    
    processed_list = []
    for i, item in enumerate(current_trends):
        trend_name = item.get('trend_name', '')
        current_rank = i + 1
        previous_rank = prev_ranks.get(trend_name, None)
        
        # คำนวณการเปลี่ยนแปลง
        if previous_rank is None:
            rank_change = "NEW"
            rank_change_val = 0
            rank_change_color = "blue"
        else:
            rank_change_val = previous_rank - current_rank
            if rank_change_val > 0:
                rank_change = f"↑ +{rank_change_val}"
                rank_change_color = "green"
            elif rank_change_val < 0:
                rank_change = f"↓ {rank_change_val}"
                rank_change_color = "red"
            else:
                rank_change = "➖ 0"
                rank_change_color = "gray"
        
        # เพิ่มข้อมูลใหม่
        new_item = item.copy()
        new_item.update({
            'rank': current_rank,
            'previous_rank': previous_rank,
            'rank_change': rank_change,
            'rank_change_val': rank_change_val,
            'rank_change_color': rank_change_color
        })
        processed_list.append(new_item)
    
    return processed_list

# คำนวณการเปลี่ยนแปลงอันดับ
previous_trends = st.session_state.get('previous_trends', [])
processed_results = calculate_rank_changes(data, previous_trends)
processed_df = pd.DataFrame(processed_results)

# --- สีหลัก ---
colors_map = {
    'TikTok': '#ff0050',      # สีแดง TikTok
    'Instagram': '#E4405F',    # สีชมพู Instagram
    'Facebook': '#1877F2',     # สีน้ำเงิน Facebook
    'Lemon8': '#FFD700',       # สีทอง Lemon8
    'Twitter': '#1DA1F2',      # สีฟ้า Twitter
    'YouTube': '#FF0000',      # สีแดง YouTube
    'Other': '#d7d7d7'         # สีเทา Other
}

# === 1. ตารางเทรนด์ยอดฮิต ===
st.subheader("📋 ตารางเทรนด์ยอดฮิต")

# แสดงตารางแบบสวยงาม
for i, row in processed_df.iterrows():
    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 2, 2, 2, 1])
        
        # อันดับ
        col1.metric("อันดับ", row['rank'])
        
        # การเปลี่ยนแปลง
        if row['rank_change'] == "NEW":
            col2.markdown(f"<span style='color: blue; font-weight: bold;'>🆕 NEW</span>", unsafe_allow_html=True)
        else:
            color = row['rank_change_color']
            col2.markdown(f"<span style='color: {color}; font-weight: bold;'>{row['rank_change']}</span>", unsafe_allow_html=True)
        
        # ชื่อเทรนด์
        col3.markdown(f"**{row['trend_name']}**")
        col3.caption(row['description'])
        
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
        
        col4.markdown(f"{category_emoji} **{category}**")
        
        # จำนวนการพูดถึง
        col5.metric("พูดถึง", row['mention_count'])
        
        # แพลตฟอร์ม
        col6.markdown(f"📱 {row['platform']}")
        
        # URL
        if row.get('source_url') and row['source_url'] != "Unknown":
            st.markdown(f"🔗 [ดูแหล่งข้อมูล]({row['source_url']})")
        
        st.divider()

# === 2. การพูดถึงในแต่ละวัน ===
st.subheader("📅 การพูดถึงในแต่ละวัน")

# สร้างข้อมูลการพูดถึงในแต่ละวัน
daily_df = create_daily_mentions_chart(data)

if not daily_df.empty:
    # เลือกวันที่
    available_dates = sorted(daily_df['date'].unique(), reverse=True)
    selected_date = st.selectbox(
        "เลือกวันที่ที่ต้องการดูเทรนด์:",
        available_dates,
        format_func=lambda x: f"{x} ({datetime.strptime(x, '%Y-%m-%d').strftime('%d/%m/%Y')})"
    )
    
    # แสดงเทรนด์ในวันที่เลือก
    trends_for_date = get_trends_by_date(data, selected_date)
    
    if trends_for_date:
        st.write(f"**เทรนด์ที่ถูกพูดถึงในวันที่ {datetime.strptime(selected_date, '%Y-%m-%d').strftime('%d/%m/%Y')}:**")
        
        # แสดงตารางเทรนด์ในวันนั้น
        for i, trend in enumerate(trends_for_date, 1):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 1])
                
                col1.metric("อันดับ", i)
                col2.markdown(f"**{trend['trend_name']}**")
                col2.caption(trend['description'])
                
                category_emoji = {
                    'Bread': '🍞', 'Cake': '🎂', 'Cookie': '🍪', 'Pastry': '🥐',
                    'Donut': '🍩', 'Muffin': '🧁', 'Bagel': '🥯', 'Croissant': '🥐',
                    'Unknown': '❓'
                }.get(trend['category'], '❓')
                
                col3.markdown(f"{category_emoji} **{trend['category']}**")
                col4.metric("พูดถึง", trend['mentions'])
                col5.markdown(f"📱 {trend['platform']}")
                
                if trend.get('source_url') and trend['source_url'] != "Unknown":
                    st.markdown(f"🔗 [ดูแหล่งข้อมูล]({trend['source_url']})")
                
                st.divider()
    else:
        st.info("ไม่พบเทรนด์ในวันที่เลือก")
    
    # กราฟแสดงการพูดถึงในแต่ละวัน
    st.subheader("📊 กราฟการพูดถึงในแต่ละวัน")
    
    # สร้างกราฟเส้นแสดงการพูดถึงของแต่ละเทรนด์
    fig_line = px.line(
        daily_df, 
        x='date_display', 
        y='mentions', 
        color='trend_name',
        title="การพูดถึงของแต่ละเทรนด์ในแต่ละวัน",
        labels={'date_display': 'วันที่', 'mentions': 'จำนวนการพูดถึง', 'trend_name': 'ชื่อเทรนด์'}
    )
    fig_line.update_layout(
        xaxis_title="วันที่",
        yaxis_title="จำนวนการพูดถึง",
        legend_title="ชื่อเทรนด์",
        height=500
    )
    st.plotly_chart(fig_line, use_container_width=True)
    
    # กราฟแท่งแสดงการพูดถึงรวมในแต่ละวัน
    daily_totals = daily_df.groupby('date_display')['mentions'].sum().reset_index()
    daily_totals = daily_totals.sort_values('date_display')
    
    fig_bar = px.bar(
        daily_totals,
        x='date_display',
        y='mentions',
        title="การพูดถึงรวมในแต่ละวัน",
        labels={'date_display': 'วันที่', 'mentions': 'จำนวนการพูดถึงรวม'},
        color='mentions',
        color_continuous_scale='Viridis'
    )
    fig_bar.update_layout(
        xaxis_title="วันที่",
        yaxis_title="จำนวนการพูดถึงรวม",
        height=400
    )
    st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("ไม่พบข้อมูลการพูดถึงในแต่ละวัน")

# === 3. กราฟรวม 10 อันดับแรก ===
st.subheader("📊 Top 10 Trends (All Categories)")
top_10_df = processed_df.head(10).sort_values(by="mention_count", ascending=False)

if not top_10_df.empty:
    # กราฟแท่ง
    fig_bar = px.bar(
        top_10_df, 
        x='trend_name', 
        y='mention_count', 
        color='platform',
        title="กราฟแท่ง 10 อันดับ (Mention Count)",
        color_discrete_map=colors_map,
        labels={'trend_name': 'ชื่อสินค้า', 'mention_count': 'จำนวนการพูดถึง'}
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # กราฟเส้น (แสดงการลดหลั่นของความนิยม)
    fig_line = px.line(
        top_10_df.sort_values(by="mention_count", ascending=False), 
        x='trend_name', 
        y='mention_count',
        markers=True,
        title="กราฟเส้น 10 อันดับ (Mention Count)",
        labels={'trend_name': 'ชื่อสินค้า', 'mention_count': 'จำนวนการพูดถึง'}
    )
    fig_line.update_traces(line_color='#007bff', line_width=3)
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("ไม่พบข้อมูล Top 10")

st.divider()

# === 2. กราฟวงกลม ===
st.subheader("🥧 กราฟวงกลม - สัดส่วนแพลตฟอร์มและประเภทขนม")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📱 สัดส่วนแพลตฟอร์ม")
    
    # นับจำนวนแพลตฟอร์ม
    platform_counts = processed_df['platform'].value_counts()
    
    if len(platform_counts) > 0:
        # สร้างกราฟวงกลม
        fig = go.Figure(data=[go.Pie(
            labels=platform_counts.index,
            values=platform_counts.values,
            hole=0.4,  # ทำให้เป็น Donut
                     marker=dict(colors=[colors_map.get(c, '#d7d7d7') for c in platform_counts.index]),
            pull=[0.05 if i == 0 else 0 for i in range(len(platform_counts))]  # ดึงชิ้นใหญ่สุด
        )])
        
        fig.update_layout(
            title="สัดส่วนแพลตฟอร์ม",
            margin=dict(t=50, b=0, l=0, r=0),
            legend_title_text='แพลตฟอร์ม',
            font=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลแพลตฟอร์ม")

with col2:
    st.subheader("🍰 สัดส่วนประเภทขนม")
    
    # นับจำนวนประเภทขนม
    category_counts = processed_df['category'].value_counts()
    
    if len(category_counts) > 0:
        # สร้างกราฟวงกลม
        fig = go.Figure(data=[go.Pie(
            labels=category_counts.index,
            values=category_counts.values,
            hole=0.4,  # ทำให้เป็น Donut
            marker=dict(colors=['#FF9F43', '#10AC84', '#EE5A24', '#0984E3', '#6C5CE7', '#A29BFE', '#FD79A8', '#FDCB6E']),
            pull=[0.05 if i == 0 else 0 for i in range(len(category_counts))]  # ดึงชิ้นใหญ่สุด
        )])
        
        fig.update_layout(
            title="สัดส่วนประเภทขนม",
            margin=dict(t=50, b=0, l=0, r=0),
            legend_title_text='ประเภทขนม',
            font=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลประเภทขนม")

st.divider()

# === 3. กราฟแยกตามหมวดหมู่ ===
st.subheader("เจาะลึกรายแพลตฟอร์ม (Platform Insight)")

# สร้าง Tabs สำหรับแต่ละ Platform
platforms = processed_df['platform'].unique()
if len(platforms) > 0:
    tabs = st.tabs([f"**{platform}**" for platform in platforms])
    
    for i, tab in enumerate(tabs):
        with tab:
            platform_name = platforms[i]
            platform_df = processed_df[processed_df['platform'] == platform_name].head(10) # เอา Top 10 ของแพลตฟอร์มนั้น
            
            if platform_df.empty:
                st.write(f"ไม่พบข้อมูลสำหรับแพลตฟอร์ม {platform_name}")
                continue
                
            st.markdown(f"#### 10 อันดับแรกในแพลตฟอร์ม '{platform_name}'")
            
            # สีสำหรับแพลตฟอร์มนี้
            platform_color = colors_map.get(platform_name, '#d7d7d7')
            
            # กราฟแท่ง (แพลตฟอร์ม)
            fig_bar_platform = px.bar(
                platform_df, 
                x='trend_name', 
                y='mention_count', 
                title=f"กราฟแท่ง '{platform_name}'",
                labels={'trend_name': 'ชื่อสินค้า', 'mention_count': 'จำนวนการพูดถึง'}
            )
            fig_bar_platform.update_traces(marker_color=platform_color)
            st.plotly_chart(fig_bar_platform, use_container_width=True)

            # กราฟเส้น (แพลตฟอร์ม)
            fig_line_platform = px.line(
                platform_df.sort_values(by="mention_count", ascending=False), 
                x='trend_name', 
                y='mention_count',
                markers=True,
                title=f"กราฟเส้น '{platform_name}'",
                labels={'trend_name': 'ชื่อสินค้า', 'mention_count': 'จำนวนการพูดถึง'}
            )
            fig_line_platform.update_traces(line_color=platform_color, line_width=3)
            st.plotly_chart(fig_line_platform, use_container_width=True)
else:
    st.info("ไม่พบข้อมูล Platform ที่จะแสดงผล")