# 🧪 RAG Model Test Guide

## วิธีใช้งานไฟล์ `test_rag_model.py`

### 1. เปิดไฟล์ `test_rag_model.py`
```bash
# เปิดไฟล์ใน editor ของคุณ
code test_rag_model.py
```

### 2. เปลี่ยน API Keys
หาบรรทัดที่ 31-32 และเปลี่ยนเป็น API key จริงของคุณ:

```python
# เปลี่ยนบรรทัดนี้:
GOOGLE_API_KEY = "your_google_api_key_here"  # เปลี่ยนเป็น API key จริง
TAVILY_API_KEY = "your_tavily_api_key_here"  # เปลี่ยนเป็น API key จริง
```

### 3. สร้าง API Keys

#### Google API Key:
1. ไปที่ https://makersuite.google.com/app/apikey
2. สร้าง API Key ใหม่
3. คัดลอก API Key มาใส่ในโค้ด

#### Tavily API Key (ถ้าต้องการ):
1. ไปที่ https://tavily.com/
2. สร้าง API Key
3. คัดลอก API Key มาใส่ในโค้ด

### 4. รันไฟล์ทดสอบ
```bash
streamlit run test_rag_model.py
```

### 5. ทดสอบระบบ
1. เปิดเว็บเบราว์เซอร์ไปที่ http://localhost:8501
2. ตรวจสอบสถานะ API Keys
3. กดปุ่ม "🚀 Run RAG Test"
4. ดูผลลัพธ์

## หมายเหตุ
- ไฟล์นี้ใช้สำหรับทดสอบ RAG system เท่านั้น
- ไม่ต้องใช้ไฟล์ `.streamlit/secrets.toml`
- API Keys ใส่ตรงๆ ในโค้ด
