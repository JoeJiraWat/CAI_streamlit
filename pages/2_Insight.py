import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Bakery Trends Insight", page_icon="📈", layout="wide")
st.title("📈 วิเคราะห์เทรนด์เชิงลึก (Insight)")

# --- ตรวจสอบว่ามีข้อมูลหรือยัง ---
if 'current_trends' not in st.session_state or not st.session_state['current_trends']:
    st.warning("ไม่พบข้อมูลเทรนด์ กรุณากลับไปหน้า '1_Overview' และกดวิเคราะห์ก่อน")
    st.stop()

# --- โหลดข้อมูลจาก Session State ---
data = st.session_state['current_trends']
df = pd.DataFrame(data)

# --- สีหลัก ---
colors_map = {
    'Bread': '#8fb6ff',
    'Cake': '#b7ffd8',
    'Cookie': '#ffe08a',
    'Pastry': '#ffb385',
    'Other': '#d7d7d7'
}

# === 1. กราฟรวม 10 อันดับแรก ===
st.subheader("Top 10 Trends (All Categories)")
top_10_df = df.head(10).sort_values(by="mention_count", ascending=False)

if not top_10_df.empty:
    # กราฟแท่ง
    fig_bar = px.bar(
        top_10_df, 
        x='product_name', 
        y='mention_count', 
        color='category',
        title="กราฟแท่ง 10 อันดับ (Mention Count)",
        color_discrete_map=colors_map,
        labels={'product_name': 'ชื่อสินค้า', 'mention_count': 'จำนวนการพูดถึง'}
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # กราฟเส้น (แสดงการลดหลั่นของความนิยม)
    fig_line = px.line(
        top_10_df.sort_values(by="mention_count", ascending=False), 
        x='product_name', 
        y='mention_count',
        markers=True,
        title="กราฟเส้น 10 อันดับ (Mention Count)",
        labels={'product_name': 'ชื่อสินค้า', 'mention_count': 'จำนวนการพูดถึง'}
    )
    fig_line.update_traces(line_color='#007bff', line_width=3)
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("ไม่พบข้อมูล Top 10")

st.divider()

# === 2. กราฟแยกตามหมวดหมู่ ===
st.subheader("เจาะลึกรายหมวดหมู่ (Category Insight)")

# สร้าง Tabs สำหรับแต่ละ Category
categories = df['category'].unique()
if len(categories) > 0:
    tabs = st.tabs([f"**{cat}**" for cat in categories])
    
    for i, tab in enumerate(tabs):
        with tab:
            cat_name = categories[i]
            cat_df = df[df['category'] == cat_name].head(10) # เอา Top 10 ของหมวดนั้น
            
            if cat_df.empty:
                st.write(f"ไม่พบข้อมูลสำหรับหมวดหมู่ {cat_name}")
                continue
                
            st.markdown(f"#### 10 อันดับแรกในหมวด '{cat_name}'")
            
            # สีสำหรับหมวดหมู่นี้
            cat_color = colors_map.get(cat_name, '#d7d7d7')
            
            # กราฟแท่ง (หมวดหมู่)
            fig_bar_cat = px.bar(
                cat_df, 
                x='product_name', 
                y='mention_count', 
                title=f"กราฟแท่ง '{cat_name}'",
                labels={'product_name': 'ชื่อสินค้า', 'mention_count': 'จำนวนการพูดถึง'}
            )
            fig_bar_cat.update_traces(marker_color=cat_color)
            st.plotly_chart(fig_bar_cat, use_container_width=True)

            # กราฟเส้น (หมวดหมู่)
            fig_line_cat = px.line(
                cat_df, 
                x='product_name', 
                y='mention_count',
                markers=True,
                title=f"กราฟเส้น '{cat_name}'",
                labels={'product_name': 'ชื่อสินค้า', 'mention_count': 'จำนวนการพูดถึง'}
            )
            fig_line_cat.update_traces(line_color=cat_color, line_width=3)
            st.plotly_chart(fig_line_cat, use_container_width=True)
else:
    st.info("ไม่พบข้อมูล Category ที่จะแสดงผล")