import streamlit as st
import google.generativeai as genai
import datetime
import sqlite3
import json
import pandas as pd
import re
import time
import os

# --- 頁面設定 ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 🛡️ 安全引入套件 ---
try:
    import pdfplumber
    pdf_ready = True
except ImportError:
    pdf_ready = False

# --- 🎨 視覺風格 ---
st.markdown("""
<style>
    :root { --bg-main: #001222; --text-orange: #ff9933; }
    .stApp { background-color: var(--bg-main); }
    .report-box { background-color: #ffffff !important; padding: 30px; border-radius: 8px; border-top: 8px solid var(--text-orange); }
    .report-box * { color: #003366 !important; }
    .report-box h1, .report-box h2 { color: #002244 !important; border-bottom: 2px solid #ff9933; }
    .streamlit-expanderContent { background-color: #0d1b2a !important; }
    .streamlit-expanderContent * { color: #e6f7ff !important; }
    #MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 💾 資料庫功能 ---
def init_db():
    conn = sqlite3.connect('crm.db')
    conn.execute('CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT, name TEXT, stage TEXT, data JSON)')
    conn.close()
init_db()

# --- 📚 知識庫載入 ---
def load_manuals():
    text = ""
    count = 0
    if not pdf_ready: return "", 0
    files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    for f in files:
        try:
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    content = page.extract_text()
                    if content: text += content + "\n"
                count += 1
        except: continue
    return text, count

if "kb_text" not in st.session_state:
    st.session_state.kb_text, st.session_state.kb_count = load_manuals()

# --- 側邊欄 ---
with st.sidebar:
    st.markdown("### 🗂️ 客戶管理")
    ukey = st.text_input("金鑰", type="password")
    
    st.markdown("---")
    st.markdown("### 📚 知識庫狀態")
    if st.session_state.kb_count > 0:
        st.success(f"✅ 已掛載 {st.session_state.kb_count} 份手冊")
    else:
        st.info("ℹ️ 未偵測到 PDF 檔案")

    st.markdown("---")
    st.markdown("### ⚙️ 系統設定")
    akey = st.text_input("Gemini API Key", type="password")
    
    model = None
    if akey:
        genai.configure(api_key=akey)
        try:
            m_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            m_list.sort(key=lambda x: "1.5-flash" not in x) # 讓 Flash 排第一
            sel_m = st.selectbox("🤖 選擇模型", m_list)
            model = genai.GenerativeModel(sel_m)
            
            # 額度警告
            if "gemma" in sel_m.lower() or "pro" in sel_m.lower():
                st.warning("⚠️ 此模型額度較低，建議僅在對話時使用，不建議跑大型分析。")
        except: st.error("Key 無效")

# --- 主程式邏輯 (簡化) ---
st.title("🛡️ 保險業務超級軍師")
st.caption("顧問式銷售助理 v2.0")

# 表單部分省略 (保持您之前的設計)
# ...

def run_ai(prompt):
    if not model: return "請先設定 API Key"
    
    # 決定餵食量：Flash 餵 3 萬字，其他餵 5 千字
    limit = 30000 if "flash" in model.model_name else 5000
    context = st.session_state.kb_text[:limit]
    
    full_p = f"參考資料：\n{context}\n\n任務：你是教練 Mars，請參考資料回答問題：\n{prompt}"
    try:
        res = model.generate_content(full_p)
        return res.text
    except Exception as e:
        if "429" in str(e):
            return "❌ 額度爆了！請換一個模型試試，或者等一分鐘再問一次。"
        return f"錯誤：{str(e)}"

# 下方串接原本的 UI 顯示邏輯
