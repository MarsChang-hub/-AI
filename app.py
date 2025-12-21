import streamlit as st
import google.generativeai as genai
import datetime
import sqlite3
import json
import pandas as pd
import re
import time
import os

# --- 1. 頁面設定 ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 2. 讀取套件檢查 ---
pdf_ready = False
try:
    import pdfplumber
    pdf_ready = True
except ImportError:
    pdf_ready = False

# --- 3. 🎨 介面風格 (Mars 風格全回歸) ---
st.markdown("""
<style>
    :root { --bg-main: #001222; --text-orange: #ff9933; }
    .stApp { background-color: var(--bg-main); }
    
    /* 報告框：白底深藍字 */
    .report-box { 
        background-color: #ffffff !important; 
        padding: 40px; 
        border-radius: 8px; 
        border-top: 8px solid var(--text-orange); 
        margin-top: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    .report-box p, .report-box li, .report-box div, .report-box span, .report-box b {
        color: #003366 !important; /* 深海藍 */
    }
    .report-box h1, .report-box h2 {
        color: #002244 !important; border-bottom: 2px solid #ff9933;
        padding-bottom: 10px; margin-top: 30px; font-weight: 800;
    }
    .report-box strong { 
        color: #002244 !important; background-color: #fff5e6 !important; padding: 0 4px; 
    }
    .report-box table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 15px; }
    .report-box th { background-color: #003366 !important; color: #ffffff !important; padding: 15px; }
    .report-box th * { color: #ffffff !important; }
    .report-box td { padding: 12px 15px; border-bottom: 1px solid #eeeeee; color: #003366 !important; }
    
    /* 陪練室：深底亮字 */
    .streamlit-expanderHeader { background-color: rgba(255, 255, 255, 0.1) !important; color: #ff9933 !important; }
    .streamlit-expanderContent { background-color: #0d1b2a !important; }
    .streamlit-expanderContent * { color: #e6f7ff !important; }
    
    /* 浮水印 */
    .mars-watermark {
        position: fixed; top: 15px; right: 25px; color: rgba(255, 153, 51, 0.9);
        font-size: 14px; font-weight: 700; z-index: 9999; pointer-events: none;
    }
    #MainMenu, footer {visibility: hidden;}
</style>
<div class="mars-watermark">Made by Mars Chang</div>
""", unsafe_allow_html=True)

# --- 4. 資料庫邏輯 ---
def init_db():
    conn = sqlite3.connect('insurance_crm.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT, name TEXT, stage TEXT, data JSON, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

def save_client(user_key, name, stage, data):
    conn = sqlite3.connect('insurance_crm.db')
    js = json.dumps(data, default=str)
    # 簡單的 Upsert 邏輯：先刪後加或更新
    c = conn.cursor()
    c.execute("SELECT id FROM clients WHERE user_key=? AND name=?", (user_key, name))
    exist = c.fetchone()
    if exist:
        c.execute("UPDATE clients SET stage=?, data=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (stage, js, exist[0]))
    else:
        c.execute("INSERT INTO clients (user_key, name, stage, data) VALUES (?, ?, ?, ?)", (user_key, name, stage, js))
    conn.commit()
    conn.close()

def get_clients(user_key):
    conn = sqlite3.connect('insurance_crm.db')
    df = pd.read_sql_query("SELECT * FROM clients WHERE user_key=? ORDER BY updated_at DESC", conn, params=(user_key,))
    conn.close()
    return df

def delete_client(user_key, name):
    conn = sqlite3.connect('insurance_crm.db')
    conn.execute("DELETE FROM clients WHERE user_key=? AND name=?", (user_key, name))
    conn.commit()
    conn.close()

init_db()

# --- 5. 狀態初始化 ---
if "current_client_data" not in st.session_state: st.session_state.current_client_data = {}
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "current_strategy" not in st.session_state: st.session_state.current_strategy = None
if "kb_text" not in st.session_state: st.session_state.kb_text = ""
if "kb_count" not in st.session_state: st.session_state.kb_count = 0

# --- 6. 讀取 PDF (自動抓取後台) ---
def load_manuals():
    if not pdf_ready: return "", 0
    text_out = ""
    count = 0
    try:
        files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
        for f in files:
            try:
                with pdfplumber.open(f) as pdf:
                    text_out += f"\n--- {f} ---\n"
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted: text_out += extracted + "\n"
                count += 1
            except: pass
    except: pass
    return text_out, count

# 啟動時載入一次
if st.session_state.kb_count == 0:
    st.session_state.kb_text, st.session_state.kb_count = load_manuals()

# --- 7. 側邊欄 ---
with st.sidebar:
    st.markdown("### 🗂️ 客戶名單")
    ukey = st.text_input("🔑 專屬金鑰", type="password")
    
    if ukey:
        if st.button("➕ 新增客戶"):
            st.session_state.current_client_data = {}
            st.session_state.current_strategy = None
            st.session_state.chat_history = []
            st.rerun()
            
        df = get_clients(ukey)
        if not df.empty:
            for s in ["S1", "S2", "S3", "S4", "S5", "S6"]:
                sub = df[df['stage'].str.startswith(s)]
                if not sub.empty:
                    with st.expander(f"📂 {s} ({len(sub)}人)"):
                        for _, r in sub.iterrows():
                            if st.button(f"👤 {r['name']}", key=f"b_{r['id']}"):
                                st.session_state.current_client_data = json.loads(r['data'])
                                st.session_state.current_strategy = st.session_state.current_client_data.get('last_strategy')
                                st.session_state.chat_history = st.session_state.current_client_data.get('chat_history', [])
                                st.rerun()

    st.markdown("---")
    st.markdown("### 📚 知識庫")
    if st.session_state.kb_count > 0:
        st.success(f"✅ 已掛載 {st.session_state.kb_count} 份手冊")
    else:
        st.info("ℹ️ 未偵測到 PDF")

    st.markdown("---")
    st.markdown("### ⚙️ 設定")
    apikey = st.text_input("API Key", type="password")
    
    model = None
    if apikey:
        genai.configure(api_key=apikey)
        try:
            # 強制 Flash 排第一，避免誤用 Gemma
            ms = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            ms.sort(key=lambda x: "1.5-flash" not in x) 
            sel = st.selectbox("🤖 模型選擇", ms, index=0)
            model = genai.GenerativeModel(sel)
            
            if "gemma" in sel.lower():
                st.warning("⚠️ Gemma 額度極小，容易報錯！強烈建議切回 1.5 Flash。")
            else:
                st.success("🟢 系統連線正常 (推薦使用 Flash)")
        except: st.error("Key 錯誤")

# --- 8. 主畫面 ---
st.title("🛡️ 保險業務超級軍師")
data = st.session_state.current_client_data

with st.form("main_form"):
    c1, c2 = st.columns([1, 2])
    with c1: name = st.text_input("客戶姓名", value=data.get("name", ""))
    with c2: 
        opts = ["S1：取得名單", "S2：約訪", "S3：初步面談", "S4：發覺需求", "S5：說明建議書", "S6：成交"]
        curr = data.get("stage", "")
        idx = next((i for i, x in enumerate(opts) if x.startswith(curr)), 0)
        stage = st.selectbox("銷售階段", opts, index=idx)
    
    c3, c4, c5 = st.columns(3)
    with c3: gender = st.radio("性別", ["男", "女"], index=0 if data.get("gender") == "男" else 1, horizontal=True)
    with c4: bday = st.text_input("生日", value=data.get("birthday", ""))
    with c5: inc = st.text_input("年收 (萬)", value=data.get("income", ""))
    
    job = st.text_input("職業", value=data.get("job", ""))
    quotes = st.text_area("客戶語錄", value=data.get("quotes", ""))
    target = st.text_area("目標商品", value=data.get("target_product", ""))
    
    st.markdown("### 保障盤點")
    g1, g2, g3 = st.columns(3)
    with g1: 
        v1 = st.text_input("日額", value=data.get("cov_daily", ""))
        v2 = st.text_input("實支", value=data.get("cov_med_reim", ""))
    with g2:
        v3 = st.text_input("癌症", value=data.get("cov_cancer", ""))
        v4 = st.text_input("重大", value=data.get("cov_major", ""))
    with g3:
        v5 = st.text_input("長照", value=data.get("cov_ltc", ""))
        v6 = st.text_input("壽險", value=data.get("cov_life", ""))

    if st.form_submit_button("🚀 分析"):
        if not model or not name:
            st.error("請輸入資料並連線")
        else:
            # 準備 Prompt，若非 Flash 模型則減少閱讀量以防爆掉
            is_flash = "flash" in model.model_name.lower() or "1.5" in model.model_name.lower()
            limit = 35000 if is_flash else 4000 
            
            kb_context = st.session_state.kb_text[:limit]
            
            prompt = f"""
            角色：你是教練 Mars Chang。
            參考資料：{kb_context}
            客戶：{name}, {gender}, {job}, 年收{inc}
            現況：{quotes}
            目標：{target}
            保障：日額{v1}, 實支{v2}, 癌{v3}, 重{v4}, 長{v5}, 壽{v6}
            任務：請進行缺口分析並推薦手冊中的具體商品。使用專業藍色調風格。
            """
            
            with st.spinner("教練思考中..."):
                try:
                    res = model.generate_content(prompt)
                    st.session_state.current_strategy = res.text
                    st.session_state.chat_history = []
                    
                    # Save
                    nd = {
                        "name": name, "stage": stage, "gender": gender, "birthday": bday, "income": inc, "job": job,
                        "quotes": quotes, "target_product": target, "cov_daily": v1, "cov_med_reim": v2, 
                        "cov_cancer": v3, "cov_major": v4, "cov_ltc": v5, "cov_life": v6,
                        "last_strategy": res.text, "chat_history": []
                    }
                    save_client(ukey, name, stage, nd)
                    st.rerun()
                except Exception as e:
                    st.error(f"錯誤：{e}")

# --- 9. 結果顯示 ---
if st.session_state.current_strategy:
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("### 🤖 陪練室")
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.write(m["content"])
        
    if q := st.chat_input("輸入問題..."):
        st.session_state.chat_history.append({"role": "user", "content": q})
        
        # 陪練室一樣要做額度保護
        is_flash = "flash" in model.model_name.lower() or "1.5" in model.model_name.lower()
        limit = 35000 if is_flash else 4000
        kb = st.session_state.kb_text[:limit]
        
        full_p = f"參考手冊：{kb}\n分析：{st.session_state.current_strategy}\n問題：{q}"
        
        try:
            r = model.generate_content(full_p)
            st.session_state.chat_history.append({"role": "assistant", "content": r.text})
            # 更新對話紀錄到 DB
            curr = st.session_state.current_client_data
            if curr:
                curr['chat_history'] = st.session_state.chat_history
                save_client(ukey, curr['name'], curr['stage'], curr)
            st.rerun()
        except Exception as e:
            st.error(f"回應失敗：{e}")
