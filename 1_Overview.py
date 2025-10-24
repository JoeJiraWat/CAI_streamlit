import streamlit as st
import os
import csv
import json
import google.generativeai as genai
from tavily import TavilyClient  # ⭐️ (1) เอา # ออก
import pandas as pd
import re
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# === 1. Setup (ฉบับแก้ไขที่ถูกต้อง) ===
st.title("🏠 Overview")
st.write("หน้าแรกสำหรับการวิเคราะห์เทรนด์เบเกอรี่ด้วย RAG System")

st.info("""
**📝 วิธีใช้งาน:**
1. เปลี่ยน `GOOGLE_API_KEY` และ `TAVILY_API_KEY` ในโค้ดเป็น API key จริงของคุณ
2. ไปที่ [Google AI Studio](https://makersuite.google.com/app/apikey) เพื่อสร้าง Google API Key
3. ไปที่ [Tavily](https://tavily.com/) เพื่อสร้าง Tavily API Key
4. กดปุ่ม "🚀 Run RAG Test" เพื่อทดสอบ
""")


# ใส่ API Keys ตรงๆ ที่นี่
GOOGLE_API_KEY = "AIzaSyAAv6i0xeWv_1J8hJ3UxeSU1bIqHE94qfA"  # เปลี่ยนเป็น API key จริงของคุณ
TAVILY_API_KEY = "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"  # เปลี่ยนเป็น API key จริงของคุณ
CSV_FILENAME = "Data/bakery_trends_dataset_updated.csv"

# ⭐️ (2) สร้างตัวแปร Client นอกฟังก์ชัน
tavily = None
genai_configured = False

# Configure Gemini
try:
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here":
        genai.configure(api_key=GOOGLE_API_KEY)
        genai_configured = True
        st.success("✅ Google API Key Configured")
    else:
        st.warning("⚠️ กรุณาเปลี่ยน GOOGLE_API_KEY เป็น API key จริงของคุณ")
except Exception as e:
    st.error(f"Error configuring Gemini: {e}")

# Configure Tavily
try:
    if TAVILY_API_KEY and TAVILY_API_KEY != "your_tavily_api_key_here":
        # ⭐️ (3) นี่คือส่วนสำคัญ: สร้าง Client จริงๆ
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        st.success("✅ Tavily Client Created")
    else:
        st.warning("⚠️ กรุณาเปลี่ยน TAVILY_API_KEY เป็น API key จริงของคุณ")
except Exception as e:
    st.error(f"Error configuring Tavily: {e}")

# === 2. (Pre-R) วิเคราะห์ CSV (เหมือนเดิม) ===
@st.cache_resource
def load_csv_insights():
    print(f"[{datetime.now()}] Running load_csv_insights...")
    try:
        stop_words = {'bakery', 'ขนม', 'เบเกอรี่', 'อร่อย', 'ขายส่ง', 'รับผลิต', '#bakery', '#ขนม', '#เบเกอรี่', '#อร่อย', 'N/A', 'ไม่มีชื่อเรื่อง', ''}
        title_list, keyword_list, hashtag_list = [], [], []

        with open(CSV_FILENAME, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # (... โค้ดส่วนนี้เหมือนเดิม ...)
            for row in reader:
                title = row.get('title')
                if title and title not in stop_words: title_list.append(title.strip())
                keywords = row.get('keywords')
                if keywords:
                    k_words = str(keywords).replace(",", " ").split();
                    keyword_list.extend([k.strip() for k in k_words if k not in stop_words])
                hashtags = row.get('hashtags')
                if hashtags:
                    h_words = str(hashtags).replace(",", " ").split();
                    hashtag_list.extend([h.strip() for h in h_words if h not in stop_words])
        
        csv_insights_list = list(set(title_list + keyword_list + hashtag_list))
        CSV_INSIGHTS_STR = ", ".join(csv_insights_list)
        print("วิเคราะห์ CSV สำเร็จ")
        st.success("✅ CSV Insights Loaded")
        return CSV_INSIGHTS_STR, True

    except FileNotFoundError:
        st.error(f"!!! ข้อผิดพลาด: ไม่พบไฟล์ {CSV_FILENAME}")
        return "", False
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอ่าน CSV: {e}")
        return "", False

# โหลด CSV
CSV_INSIGHTS, CSV_LOADED = load_csv_insights()

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

# แสดงข้อมูล CSV
if CSV_LOADED:
    st.info(f"📊 CSV Keywords: {len(CSV_INSIGHTS)} ตัวอักษร")
    with st.expander("ดู CSV Keywords"):
        st.text(CSV_INSIGHTS[:500] + "..." if len(CSV_INSIGHTS) > 500 else CSV_INSIGHTS)

# === แสดงสถานะ API Keys ===
st.subheader("🔑 API Keys Status")
col1, col2 = st.columns(2)

with col1:
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here":
        st.success("✅ Google API Key: Configured")
    else:
        st.error("❌ Google API Key: Not Set")

with col2:
    if TAVILY_API_KEY and TAVILY_API_KEY != "your_tavily_api_key_here":
        st.success("✅ Tavily API Key: Configured")
    else:
        st.error("❌ Tavily API Key: Not Set")


# === 3. (A) System Prompt ===
system_prompt_json = """
คุณคือเครื่องมือสกัดข้อมูลเทรนด์เบเกอรี่ในประเทศไทย

**คำสั่ง:**
1. วิเคราะห์ข้อมูลที่ให้มาและสกัดเทรนด์เบเกอรี่ยอดนิยม
2. ตอบกลับเป็น JSON array เท่านั้น
3. แต่ละรายการต้องมี: trend_name, mention_count, platform, description, source_url, category
4. source_url ต้องเป็น URL จริงจากข้อมูลที่ค้นพบ
5. category ต้องเป็นประเภทของขนม เช่น Bread, Cake, Cookie, Pastry, Donut, Muffin, Bagel, Croissant

**แพลตฟอร์มที่เน้นเป็นหลัก:**
- TikTok (🎵) - เทรนด์ไวรัล, อาหารยอดฮิต, วิธีทำขนม
- Instagram (📸) - ภาพสวย, อาหารสไตล์, รีวิวร้าน
- Facebook (👍) - กลุ่มชุมชน, รีวิว, แชร์ประสบการณ์
- Lemon8 (🍋) - ไลฟ์สไตล์, อาหารสุขภาพ, เทรนด์ใหม่

**รูปแบบ JSON ที่ต้องการ:**
[
  {
    "trend_name": "ชื่อเทรนด์",
    "mention_count": จำนวนการพูดถึง,
    "platform": "TikTok/Instagram/Facebook/Lemon8",
    "description": "คำอธิบาย",
    "source_url": "URL ของแหล่งข้อมูล",
    "category": "ประเภทขนม"
  }
]

**สำคัญ:** 
- เน้นข้อมูลจาก TikTok, Instagram, Facebook, Lemon8 เป็นหลัก
- ตอบกลับเป็น JSON array เท่านั้น ไม่ต้องมีข้อความอื่น
- หากมีข้อมูลจากแพลตฟอร์มอื่น ให้ระบุเป็น "Other"
"""

# === 4. (RAG) ฟังก์ชัน RAG หลัก (พร้อม Log Error) ===
# ⭐️ ไม่ต้อง Cache (ttl=0) เพื่อให้ทดสอบได้สดใหม่ทุกครั้ง
@st.cache_data(ttl=0)
def get_bakery_trends_test(query_topic: str, user_instruction: str, csv_keywords: str):
    
    print(f"[{datetime.now()}] Running RAG for: '{query_topic}'")

    if not tavily:
        st.error("Tavily client is NOT initialized. Check TAVILY_API_KEY.")
        return None 
    if not genai_configured:
        st.error("Gemini is NOT initialized. Check GOOGLE_API_KEY.")
        return None
    
    # --- (R) Retrieval (Multi-Query) ---
    # จำกัดความยาวของ query ให้ไม่เกิน 400 ตัวอักษร
    short_csv_keywords = csv_keywords[:200] if len(csv_keywords) > 200 else csv_keywords
    queries_to_search = [
        f"เทรนด์ {query_topic} TikTok Instagram Facebook Lemon8 ไทย", 
        f"{query_topic} ยอดนิยม TikTok Instagram Facebook Lemon8", 
        f"เทรนด์ {query_topic} social media ไทย",
        short_csv_keywords
    ]
    
    # ตรวจสอบความยาวของแต่ละ query
    for i, q in enumerate(queries_to_search):
        if len(q) > 400:
            queries_to_search[i] = q[:400]
            print(f"Query {i+1} ถูกตัดให้เหลือ 400 ตัวอักษร")
    all_context_str_list = []
    all_urls_found = set()
    
    for i, q in enumerate(queries_to_search):
        print(f"  -> Query {i+1}: '{q[:50]}...' (ความยาว: {len(q)} ตัวอักษร)")
        try:
            search_results = tavily.search(query=q, max_results=3, include_answer=False) 
            for doc in search_results['results']:
                if doc['url'] not in all_urls_found:
                    all_urls_found.add(doc['url'])
                    all_context_str_list.append(f"--- แหล่งที่มา: {doc['url']} ---\n{doc['content']}")
        except Exception as e:
            print(f"    -> TAVILY SEARCH ERROR: {e}")
            st.error(f"Tavily Search Error: {e}") 
            return None 
            
    if not all_context_str_list:
        retrieved_context = "การค้นหาล้มเหลว (ไม่พบข้อมูลใดๆ)"
    else:
        retrieved_context = "\n\n".join(all_context_str_list)
        
    print(f"ค้นพบข้อมูล {len(all_urls_found)} แหล่ง")
    if not all_urls_found:
        return [] 

    # --- (A) Augmentation ---
    # สร้างรายการ URL ที่ค้นพบ
    url_list = "\n".join([f"- {url}" for url in all_urls_found])
    
    final_prompt = f"""{system_prompt_json}

ข้อมูลที่ค้นพบ:
{retrieved_context}

URL ที่ค้นพบ:
{url_list}

คำถาม: {user_instruction}

ตอบกลับเป็น JSON array เท่านั้น โดยใช้ URL จากรายการด้านบน:"""
    
    # --- (G) Generation (Sync) ---
    print("กำลังส่ง Context + Prompt (Sync) ไปให้ Gemini วิเคราะห์...")
    raw_response_text = ""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(final_prompt)
        
        # ⭐️⭐️⭐️ [เพิ่มโค้ดแก้ไข] ⭐️⭐️⭐️
        # นี่คือ "ตัวดักจับ" ที่เราเพิ่มเข้ามา
        if response is None:
            st.error("Gemini Error: The model returned 'None'.")
            st.error("This is likely due to a SAFETY BLOCK on the retrieved web content.")
            return None # ออกจากฟังก์ชันทันที
            
        # ถ้า response ไม่ใช่ None, โค้ดด้านล่างจะทำงานปกติ
        raw_response_text = response.text 
        
        # --- (Python Brain) ---
        clean_json_str = raw_response_text.strip()
        
        # ลบคำว่า "json" และ "```" ออก
        clean_json_str = clean_json_str.replace("```json", "").replace("```", "").strip()
        
        # ตรวจสอบว่า JSON สมบูรณ์หรือไม่
        if not clean_json_str or clean_json_str == "":
            st.error("Gemini ตอบกลับมาว่างเปล่า")
            return []
            
        # พยายามแก้ไข JSON ที่ไม่สมบูรณ์
        if not clean_json_str.endswith('}'):
            # หา closing bracket ที่หายไป
            if clean_json_str.count('{') > clean_json_str.count('}'):
                missing_braces = clean_json_str.count('{') - clean_json_str.count('}')
                clean_json_str += '}' * missing_braces
                
        if '[' in clean_json_str and not clean_json_str.endswith(']'):
            # หา closing bracket ของ array
            if clean_json_str.count('[') > clean_json_str.count(']'):
                missing_brackets = clean_json_str.count('[') - clean_json_str.count(']')
                clean_json_str += ']' * missing_brackets
        
        try:
            new_results = json.loads(clean_json_str)
            
            # ตรวจสอบว่าเป็น list หรือไม่
            if isinstance(new_results, dict) and 'trends' in new_results:
                # ถ้าเป็น object ที่มี trends array
                trends = new_results['trends']
                if isinstance(trends, list):
                    # แปลงเป็นรูปแบบที่ต้องการ
                    formatted_results = []
                    for i, trend in enumerate(trends):
                        if isinstance(trend, str):
                            # หา URL ที่เหมาะสม (ใช้ URL แรกที่ค้นพบ)
                            source_url = list(all_urls_found)[0] if all_urls_found else "Unknown"
                            formatted_results.append({
                                'trend_name': trend,
                                'mention_count': 10 - i,  # ให้คะแนนตามลำดับ
                                'platform': 'Unknown',
                                'description': trend,
                                'source_url': source_url,
                                'category': 'Unknown'
                            })
                    new_results = formatted_results
                else:
                    st.error("รูปแบบข้อมูลไม่ถูกต้อง: trends ไม่ใช่ array")
                    return []
            elif not isinstance(new_results, list):
                st.error("รูปแบบข้อมูลไม่ถูกต้อง: ไม่ใช่ list หรือ object ที่มี trends")
                return []
                
            print(f"Gemini สกัดข้อมูลมาได้ {len(new_results)} รายการ")
            
            # ตรวจสอบว่าแต่ละรายการมี source_url และ category หรือไม่
            for i, item in enumerate(new_results):
                if 'source_url' not in item or not item['source_url']:
                    # ถ้าไม่มี source_url ให้ใช้ URL แรกที่ค้นพบ
                    if all_urls_found:
                        new_results[i]['source_url'] = list(all_urls_found)[0]
                    else:
                        new_results[i]['source_url'] = "Unknown"
                
                if 'category' not in item or not item['category']:
                    # ถ้าไม่มี category ให้ใช้ "Unknown"
                    new_results[i]['category'] = "Unknown"
            
            sorted_list = sorted(new_results, key=lambda x: x.get('mention_count', 0), reverse=True)
            return sorted_list
            
        except json.JSONDecodeError as json_err:
            st.error(f"JSON Parse Error: {json_err}")
            st.error("Raw Response:")
            st.text(clean_json_str)
            return []
        
    except Exception as e:
        # ถ้า Error เกิดจากสาเหตุอื่น (เช่น JSON ผิด)
        print(f"!!! ข้อผิดพลาด: Gemini/JSON Error: {e}")
        st.error(f"Gemini/JSON Error: {e}") 
        st.subheader("Raw AI Output (ที่ทำให้เกิด Error):")
        st.text(raw_response_text) # แสดงผลลัพธ์ดิบๆ ที่ AI ส่งมา
        return None
# === 5. ส่วน UI สำหรับทดสอบ ===
st.divider()

# เก็บข้อมูล previous trends ใน session state
if 'previous_trends' not in st.session_state:
    st.session_state['previous_trends'] = []

# จำค่าเดิมไว้
if 'saved_query' not in st.session_state:
    st.session_state['saved_query'] = "เบเกอรี่"
if 'saved_custom_prompt' not in st.session_state:
    st.session_state['saved_custom_prompt'] = "เทรนด์ 10 อันดับแรกในไทย"
if 'saved_use_custom_prompt' not in st.session_state:
    st.session_state['saved_use_custom_prompt'] = True

query = st.text_input("หัวข้อที่สนใจ (Topic)", value=st.session_state['saved_query'])

# เพิ่มช่องสำหรับ custom prompt
st.subheader("✏️ Custom Prompt")
custom_prompt = st.text_area(
    "คำสั่งพิเศษ (Custom Instruction)", 
    value=st.session_state['saved_custom_prompt'],
    help="คุณสามารถเขียนคำสั่งพิเศษได้ เช่น 'เทรนด์ 5 อันดับแรก', 'เทรนด์ที่กำลังมาแรง', 'เทรนด์สุขภาพ' เป็นต้น",
    height=100
)

# แสดงตัวอย่าง prompt
with st.expander("💡 ตัวอย่าง Prompt ที่แนะนำ"):
    st.markdown("""
    **ตัวอย่างคำสั่งที่สามารถใช้ได้:**
    
    - `เทรนด์ 5 อันดับแรกในไทย`
    - `เทรนด์ที่กำลังมาแรงที่สุด`
    - `เทรนด์สุขภาพและออร์แกนิก`
    - `เทรนด์ขนมหวานยอดนิยม`
    - `เทรนด์เบเกอรี่สำหรับเด็ก`
    - `เทรนด์ขนมปังโฮลวีท`
    - `เทรนด์เค้กวันเกิด`
    - `เทรนด์คุกกี้ช็อกโกแลต`
    - `เทรนด์โดนัทเกลือ`
    - `เทรนด์มัฟฟินผลไม้`
    
    **เคล็ดลับ:** ยิ่งคำสั่งชัดเจนเท่าไหร่ ผลลัพธ์จะตรงตามที่ต้องการมากขึ้น
    """)

# เพิ่มตัวเลือกสำหรับใช้ custom prompt หรือไม่
use_custom_prompt = st.checkbox("ใช้ Custom Prompt", value=st.session_state['saved_use_custom_prompt'], help="ถ้าไม่เลือกจะใช้คำสั่งเริ่มต้น")

if st.button("🚀 Run RAG Test", type="primary"):
    # เก็บค่าใหม่ใน session state
    st.session_state['saved_query'] = query
    st.session_state['saved_custom_prompt'] = custom_prompt
    st.session_state['saved_use_custom_prompt'] = use_custom_prompt
    
    if not CSV_LOADED or not tavily or not genai_configured:
        st.error("ไม่สามารถรันได้: กรุณาตรวจสอบข้อผิดพลาดด้านบน (API Keys หรือ CSV)")
    else:
        with st.spinner("Running RAG (Tavily Search + Gemini Generate)..."):
            # เลือกใช้ custom prompt หรือ default prompt
            if use_custom_prompt and custom_prompt.strip():
                user_instruction = f"เทรนด์ {query} {custom_prompt.strip()}"
            else:
                user_instruction = f"เทรนด์ {query} 10 อันดับแรกในไทย"
            
            results = get_bakery_trends_test(
                query_topic=query,
                user_instruction=user_instruction,
                csv_keywords=CSV_INSIGHTS
            )
        
        # แสดง prompt ที่ใช้จริง
        st.subheader("📝 Prompt ที่ใช้")
        st.info(f"**คำสั่งที่ส่งให้ AI:** {user_instruction}")
        
        st.subheader("📊 ผลลัพธ์การวิเคราะห์เทรนด์")
        
        if results is None:
            st.error("การทดสอบล้มเหลว (Test Failed). กรุณาดู Error ด้านบน")
        elif len(results) == 0:
            st.warning("การทดสอบสำเร็จ (Test Succeeded), แต่ Model คืนค่า 0 รายการ")
        else:
            st.success(f"การทดสอบสำเร็จ! Model คืนค่า {len(results)} รายการ")
            
            # คำนวณการเปลี่ยนแปลงอันดับ
            processed_results = calculate_rank_changes(results, st.session_state['previous_trends'])
            
            # เก็บข้อมูลปัจจุบันเป็น previous trends สำหรับครั้งต่อไป
            st.session_state['previous_trends'] = results
            
            # เก็บข้อมูลใน session state เพื่อให้หน้า Insight ใช้ได้
            st.session_state['current_trends'] = results
            
            # เก็บข้อมูลในประวัติ
            if 'run_history' not in st.session_state:
                st.session_state['run_history'] = []
            
            # เพิ่มข้อมูลการรันครั้งนี้ในประวัติ
            run_data = {
                'timestamp': datetime.now(),
                'query': query,
                'instruction': user_instruction,
                'results': results,
                'total_results': len(results)
            }
            st.session_state['run_history'].append(run_data)
            
            # === แสดงตาราง ===
            st.subheader("📋 ตารางเทรนด์ยอดฮิต")
            
            # สร้าง DataFrame
            df = pd.DataFrame(processed_results)
            
            # แสดงตารางแบบสวยงาม
            for i, row in df.iterrows():
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
            
            # === แสดงข้อมูลการพูดถึงในแต่ละวัน ===
            st.subheader("📅 การพูดถึงในแต่ละวัน")
            
            # สร้างข้อมูลการพูดถึงในแต่ละวัน
            daily_data = []
            for trend in results:
                trend_name = trend.get('trend_name', 'Unknown')
                daily_mentions = trend.get('daily_mentions', [])
                
                for day_data in daily_mentions:
                    daily_data.append({
                        'trend_name': trend_name,
                        'date': day_data['date'],
                        'date_display': day_data['date_display'],
                        'mentions': day_data['mentions'],
                        'platform': trend.get('platform', 'Unknown'),
                        'category': trend.get('category', 'Unknown')
                    })
            
            if daily_data:
                daily_df = pd.DataFrame(daily_data)
                
                # เลือกวันที่
                available_dates = sorted(daily_df['date'].unique(), reverse=True)
                selected_date = st.selectbox(
                    "เลือกวันที่ที่ต้องการดูเทรนด์:",
                    available_dates,
                    format_func=lambda x: f"{x} ({datetime.strptime(x, '%Y-%m-%d').strftime('%d/%m/%Y')})"
                )
                
                # แสดงเทรนด์ในวันที่เลือก
                trends_for_date = []
                for trend in results:
                    daily_mentions = trend.get('daily_mentions', [])
                    for day_data in daily_mentions:
                        if day_data['date'] == selected_date:
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
            
            # === แสดงกราฟวงกลม ===
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🥧 สัดส่วนแพลตฟอร์ม")
                
                # นับจำนวนแพลตฟอร์ม
                platform_counts = df['platform'].value_counts()
                
                if len(platform_counts) > 0:
                    # สร้างกราฟวงกลม
                    fig = go.Figure(data=[go.Pie(
                        labels=platform_counts.index,
                        values=platform_counts.values,
                        hole=0.4,  # ทำให้เป็น Donut
                        marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57']),
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
                category_counts = df['category'].value_counts()
                
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
            
            # === แสดงกราฟแท่ง ===
            st.subheader("📊 กราฟแท่ง - จำนวนการพูดถึง")
            
            # สร้างกราฟแท่ง
            fig_bar = px.bar(
                df.head(10),  # แสดงแค่ 10 อันดับแรก
                x='trend_name',
                y='mention_count',
                title="10 เทรนด์ยอดฮิต",
                labels={'trend_name': 'ชื่อเทรนด์', 'mention_count': 'จำนวนการพูดถึง'},
                color='mention_count',
                color_continuous_scale='Viridis'
            )
            
            fig_bar.update_layout(
                xaxis_tickangle=-45,
                height=500
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # === แสดงข้อมูลดิบ ===
            with st.expander("🔍 ดูข้อมูลดิบ (JSON)"):
                st.json(results)
            
            # === ปุ่มไปหน้า Insight ===
            st.success("✅ ข้อมูลถูกเก็บใน Session State แล้ว!")
            st.info("ตอนนี้คุณสามารถไปที่หน้า **📈 วิเคราะห์เทรนด์เชิงลึก (Insight)** เพื่อดูการวิเคราะห์เชิงลึกได้")
            
            if st.button("🚀 ไปหน้า Insight", type="primary"):
                st.switch_page("pages/2_Insight.py")
            
            st.divider()
            
            if st.button("🗑️ Reset All Data", type="secondary"):
                # รีเซ็ตข้อมูลทั้งหมด
                if 'current_trends' in st.session_state:
                    del st.session_state['current_trends']
                if 'previous_trends' in st.session_state:
                    del st.session_state['previous_trends']
                if 'run_history' in st.session_state:
                    del st.session_state['run_history']
                if 'saved_query' in st.session_state:
                    del st.session_state['saved_query']
                if 'saved_custom_prompt' in st.session_state:
                    del st.session_state['saved_custom_prompt']
                if 'saved_use_custom_prompt' in st.session_state:
                    del st.session_state['saved_use_custom_prompt']
                
                st.success("ข้อมูลทั้งหมดถูกรีเซ็ตเรียบร้อยแล้ว!")
                st.rerun()