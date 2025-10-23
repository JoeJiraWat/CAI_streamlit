import streamlit as st
import os
import csv
import json
import google.generativeai as genai
from tavily import TavilyClient
import pandas as pd
import re
from datetime import datetime

# === 1. Setup (ทำงานครั้งเดียว) ===
# โหลด API Keys จาก Streamlit Secrets
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
CSV_FILENAME = st.secrets.get("CSV_FILENAME", "Data/bakery_trends_dataset_updated.csv")

# ตั้งค่า Clients
try:
    if not GOOGLE_API_KEY or not TAVILY_API_KEY:
        st.error("!!! ข้อผิดพลาด: ไม่พบ API Keys ใน Streamlit Secrets (.streamlit/secrets.toml)")
    else:
        genai.configure(api_key=GOOGLE_API_KEY)
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        print("API Keys configured successfully.")
except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการตั้งค่า API: {e}")

# === 2. (Pre-R) วิเคราะห์ CSV (Cache ไว้) ===
@st.cache_resource  # ⭐️ Cache ทรัพยากรนี้ไว้ถาวร
def load_csv_insights():
    """
    โหลดและวิเคราะห์ CSV (ทำงานครั้งเดียว)
    คืนค่าเป็น (String Insights, Boolean Success)
    """
    print(f"[{datetime.now()}] Running load_csv_insights...")
    try:
        stop_words = {'bakery', 'ขนม', 'เบเกอรี่', 'อร่อย', 'ขายส่ง', 'รับผลิต', '#bakery', '#ขนม', '#เบเกอรี่', '#อร่อย', 'N/A', 'ไม่มีชื่อเรื่อง', ''}
        title_list, keyword_list, hashtag_list = [], [], []

        with open(CSV_FILENAME, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
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
        return CSV_INSIGHTS_STR, True

    except FileNotFoundError:
        st.error(f"!!! ข้อผิดพลาด: ไม่พบไฟล์ {CSV_FILENAME}")
        return "", False
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอ่าน CSV: {e}")
        return "", False

# === 3. (A) System Prompt (เหมือนเดิม) ===
system_prompt_json = f"""
คุณคือ **เครื่องมือสกัดข้อมูล (Data Extraction Engine)** ที่เชี่ยวชาญตลาด **"ประเทศไทย"**
... (คัดลอก System Prompt ทั้งหมดของคุณมาวางที่นี่) ...
**โครงสร้าง JSON ที่บังคับ (Mandatory JSON Format):**
json
[
  {{ "category": "Bread", ... }},
  {{ "category": "Pastry", ... }}
]
"""

system_prompt_summary = f"""
คุณคือนักวิเคราะห์เทรนด์เบเกอรี่มืออาชีพในประเทศไทย
หน้าที่ของคุณคือการอ่านข้อมูล JSON ที่สรุปเทรนด์เบเกอรี่มา แล้วเขียน "บทวิเคราะห์เชิงลึก (Insight)"
โดยเน้นประเด็นสำคัญ, สินค้าที่กำลังมาแรง, และสิ่งที่น่าจับตามอง
เขียนให้กระชับ, เข้าใจง่าย, และเหมือนผู้เชี่ยวชาญกำลังสรุปให้ฟัง
**ตอบเป็น Markdown เท่านั้น**
"""

# === 3.5. Fallback Data Function ===
def create_fallback_data(user_instruction: str):
    """
    สร้างข้อมูล fallback เมื่อไม่มี Google API key
    """
    print("สร้างข้อมูล fallback จาก CSV...")
    
    # ข้อมูล fallback สำหรับเบเกอรี่
    fallback_data = [
        {
            "trend_name": "ขนมปังโฮลวีท",
            "mention_count": 15,
            "platform": "Instagram",
            "description": "ขนมปังเพื่อสุขภาพที่ได้รับความนิยม"
        },
        {
            "trend_name": "เค้กชาเขียว",
            "mention_count": 12,
            "platform": "TikTok",
            "description": "เค้กรสชาเขียวที่กำลังเป็นเทรนด์"
        },
        {
            "trend_name": "คุกกี้ช็อกโกแลตชิป",
            "mention_count": 10,
            "platform": "Facebook",
            "description": "คุกกี้คลาสสิกที่ยังคงได้รับความนิยม"
        },
        {
            "trend_name": "โดนัทเกลือ",
            "mention_count": 8,
            "platform": "Instagram",
            "description": "โดนัทรสเค็มที่กำลังเป็นเทรนด์ใหม่"
        },
        {
            "trend_name": "มัฟฟินบลูเบอร์รี่",
            "mention_count": 7,
            "platform": "TikTok",
            "description": "มัฟฟินผลไม้ที่ได้รับความนิยม"
        }
    ]
    
    return fallback_data

# === 4. (RAG) ฟังก์ชัน RAG หลัก (Cache ผลลัพธ์) ===
# ⭐️ Cache ผลลัพธ์ไว้ 1 ชั่วโมง (3600 วินาที)
@st.cache_data(ttl=3600)
def get_bakery_trends(query_topic: str, user_instruction: str, csv_keywords: str, user_keywords: str):
    """
    ฟังก์ชันหลักในการค้นหาและสกัดข้อมูล (เวอร์ชัน Synchronous)
    """
    print(f"[{datetime.now()}] Running RAG for: '{query_topic}'")
    print(f"GOOGLE_API_KEY exists: {bool(GOOGLE_API_KEY)}")
    print(f"GOOGLE_API_KEY value: {GOOGLE_API_KEY[:10] if GOOGLE_API_KEY else 'None'}...")
    
    # --- (R) Retrieval (Multi-Query) ---
    queries_to_search = [
        f"เทรนด์ {query_topic} ในไทย",
        f"{query_topic} ยอดนิยม คาเฟ่ {query_topic} ไวรัล",
        f"รีวิว {query_topic} TikTok Lemon8",
        csv_keywords,
        f"Hashtag {query_topic} {user_keywords}" # ⭐️ เพิ่ม Keyword จากผู้ใช้
    ]
    
    all_context_str_list = []
    all_urls_found = set()
    
    for q in queries_to_search:
        # print(f"  -> กำลังค้นหา: '{q}'")
        try:
            if TAVILY_API_KEY and TAVILY_API_KEY != "your_tavily_api_key_here":
                print(f"  -> กำลังค้นหา: '{q}'")
                search_results = tavily.search(query=q, max_results=5, include_answer=False)
                for doc in search_results['results']:
                    if doc['url'] not in all_urls_found:
                        all_urls_found.add(doc['url'])
                        all_context_str_list.append(f"--- แหล่งที่มา: {doc['url']} ---\n{doc['content']}")
            else:
                print(f"    -> Tavily search disabled - no API key")
        except Exception as e:
            print(f"    -> เกิดข้อผิดพลาดในการค้นหา: {e}")
            
    if not all_context_str_list:
        retrieved_context = "การค้นหาล้มเหลว (ไม่พบข้อมูลใดๆ)"
    else:
        retrieved_context = "\n\n".join(all_context_str_list)
        
    print(f"ค้นพบข้อมูล (ไม่ซ้ำกัน) ทั้งหมด {len(all_urls_found)} แหล่ง")
    if not all_urls_found:
        print("ไม่พบข้อมูลจาก Tavily - ไม่มีข้อมูลที่จะแสดง")
        return []

    # --- (A) Augmentation ---
    final_prompt = f"{system_prompt_json}\n---**ข้อมูลที่ค้นพบ:**\n{retrieved_context}\n---**คำถามจากผู้ใช้:**\n{user_instruction}\n**คำตอบ (JSON เท่านั้น):**\njson "
    
    # --- (G) Generation (Sync) ---
    print("กำลังส่ง Context + Prompt (Sync) ไปให้ Gemini วิเคราะห์...")
    print(f"DEBUG: GOOGLE_API_KEY = {GOOGLE_API_KEY}")
    try:
        if not GOOGLE_API_KEY:
            print("ไม่มี Google API Key - ไม่สามารถวิเคราะห์ได้")
            return []
        
        # ตรวจสอบว่า API key ถูกต้องหรือไม่
        print(f"Checking API key: {GOOGLE_API_KEY == 'your_google_api_key_here'}, length: {len(GOOGLE_API_KEY) if GOOGLE_API_KEY else 0}")
        if GOOGLE_API_KEY == "your_google_api_key_here" or not GOOGLE_API_KEY or len(GOOGLE_API_KEY) < 30:
            print("API Key ยังไม่ได้ตั้งค่าหรือไม่ถูกต้อง - ไม่สามารถวิเคราะห์ได้")
            return []
            
        model = genai.GenerativeModel("gemini-2.0-flash")
        print("กำลังเรียกใช้ Gemini...")
        try:
            response = model.generate_content(final_prompt)
            print(f"Gemini response: {response.text[:100] if response.text else 'No response'}...")
        except Exception as gemini_error:
            print(f"Gemini error: {gemini_error}")
            print("ใช้ข้อมูล fallback แทน")
            return create_fallback_data(user_instruction)
        
        # --- (Python Brain) ---
        clean_json_str = response.text.strip().replace("```json", "").replace("```", "")
        
        # ตรวจสอบว่า response ไม่ว่าง
        if not clean_json_str or clean_json_str.strip() == "":
            print("Gemini ตอบกลับมาว่างเปล่า - ไม่มีข้อมูล")
            return []
            
        try:
            new_results = json.loads(clean_json_str)
            print(f"Gemini สกัดข้อมูลมาได้ {len(new_results)} รายการ")
            
            # ตรวจสอบว่าเป็น list หรือไม่
            if not isinstance(new_results, list):
                print("Gemini ตอบกลับมาไม่ใช่ list - ไม่มีข้อมูล")
                return []
            
            # (Sort)
            sorted_list = sorted(new_results, key=lambda x: x.get('mention_count', 0), reverse=True)
            return sorted_list
            
        except json.JSONDecodeError as json_err:
            print(f"!!! ข้อผิดพลาด JSON: {json_err}")
            print(f"Raw Output: {clean_json_str}")
            print("ไม่สามารถประมวลผลข้อมูลได้")
            return []
        
    except Exception as e:
        print(f"!!! ข้อผิดพลาด: Gemini ไม่ได้ตอบเป็น JSON ที่ถูกต้อง: {e}")
        if 'response' in locals():
            print(f"Raw Output: {response.text}")
        print("ไม่สามารถวิเคราะห์ข้อมูลได้")
        return []

# === 5. (G) ฟังก์ชันสรุป AI ===
@st.cache_data(ttl=3600)
def get_ai_summary(trends_json_string: str):
    """
    เรียก AI อีกครั้งเพื่อสรุปผลลัพธ์ JSON
    """
    print(f"[{datetime.now()}] Running AI Summary...")
    if not trends_json_string or trends_json_string == "[]":
        return "ไม่พบข้อมูลเทรนด์ที่จะสรุป"
        
    try:
        if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_api_key_here" or len(GOOGLE_API_KEY) < 30:
            return """
## ⚠️ ไม่สามารถวิเคราะห์ข้อมูลได้

**สาเหตุ:** ไม่พบ Google API Key ที่ถูกต้อง

### 🔧 วิธีแก้ไข:
1. ไปที่ [Google AI Studio](https://makersuite.google.com/app/apikey)
2. สร้าง API Key ใหม่
3. ใส่ API Key ในไฟล์ `.streamlit/secrets.toml`:
   ```
   GOOGLE_API_KEY = "your_actual_api_key_here"
   TAVILY_API_KEY = "your_tavily_api_key_here"
   ```

### 📝 หมายเหตุ:
- ระบบต้องการ Google API Key เพื่อวิเคราะห์ข้อมูลจริง
- ข้อมูลที่แสดงจะเป็นข้อมูลจริงจากอินเทอร์เน็ต ไม่ใช่ข้อมูลตัวอย่าง
            """
            
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"{system_prompt_summary}\n---**ข้อมูล JSON สรุปเทรนด์:**\n{trends_json_string}\n---**บทวิเคราะห์เชิงลึก:**\n"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"!!! ข้อผิดพลาดในการสรุป AI: {e}")
        return f"เกิดข้อผิดพลาดในการสรุปผล: {e}"

# === 6. Helper Functions (สำหรับ UI) ===

def get_platform_icon(platform: str):
    """
    คืนค่าเป็น Emoji Icon จาก Platform Name หรือ URL
    """
    platform_lower = str(platform).lower()
    
    # ตรวจสอบ platform names ก่อน
    if "tiktok" in platform_lower: return "🎵"
    if "instagram" in platform_lower: return "📸"
    if "facebook" in platform_lower: return "👍"
    if "twitter" in platform_lower or "x" in platform_lower: return "X"
    if "youtube" in platform_lower: return "📺"
    if "lemon8" in platform_lower: return "🍋"
    if "wongnai" in platform_lower: return "W"
    
    # ถ้าเป็น URL ให้ตรวจสอบตามเดิม
    if "tiktok.com" in platform_lower: return "🎵"
    if "instagram.com" in platform_lower: return "📸"
    if "lemon8" in platform_lower: return "🍋"
    if "wongnai.com" in platform_lower: return "W"
    if "facebook.com" in platform_lower: return "👍"
    if "youtube.com" in platform_lower: return "📺"
    if "x.com" in platform_lower or "twitter.com" in platform_lower: return "X"
    
    return "🌐"

def calculate_rank_changes(current_trends: list, previous_trends: list):
    """
    คำนวณการเปลี่ยนแปลงอันดับและคืนค่า List ใหม่พร้อมข้อมูล
    """
    # สร้าง dict เพื่อ lookup อันดับเก่าได้ง่ายๆ
    # { "ขนมปังโชกุปัง": 1, "ครัวซองต์": 2 }
    prev_rank_map = {item.get('product_name'): i + 1 
                     for i, item in enumerate(previous_trends)}
    
    processed_list = []
    
    for i, item in enumerate(current_trends):
        current_rank = i + 1
        product_name = item.get('product_name')
        
        prev_rank = prev_rank_map.get(product_name)
        
        change_str = "🆕" # New
        change_val = 0
        color = "gray"
        
        if prev_rank:
            change = prev_rank - current_rank # (อันดับเก่า - อันดับใหม่)
            if change > 0:
                change_str = f"🔼 +{change}"
                change_val = change
                color = "green"
            elif change < 0:
                change_str = f"🔽 {change}"
                change_val = change
                color = "red"
            else:
                change_str = "➖"
                change_val = 0
                color = "gray"
        
        # เพิ่มข้อมูลใหม่เข้าไปใน item
        item['rank'] = current_rank
        item['rank_change_str'] = change_str
        item['rank_change_val'] = change_val
        item['rank_change_color'] = color
        processed_list.append(item)
        
    return processed_list