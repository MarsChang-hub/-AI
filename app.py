import streamlit as st
import google.generativeai as genai
import datetime
import sqlite3
import json
import pandas as pd
import re
import time
import os

# --- 1. 頁面設定 (必須放在第一行) ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 2. 🛡️ 安全引入 pdfplumber (防止 Oh no 畫面) ---
pdf_tool_ready = False
try:
    import pdfplumber
    pdf_tool_ready = True
except ImportError:
    pdf_tool_ready = False

# --- 3. 🎨 風格設定 ( Mars 專屬視覺全回歸 ) ---
st.markdown("""
<style>
    :root {
        --bg-main: #001222;
        --glass-card: rgba(255, 255, 255, 0.05);
        --text-orange: #ff9933;
        --text-body: #e0e0e0;
    }
    .stApp { background-color: var(--bg-main); }
    p, li, span, div { color: var(--text-body); }
    .block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; max-width: 1200px; }
    
    /* 輸入框絕對顯色 */
    .stTextInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important; color: #000000 !important;
        border: 1px solid #ff9933 !important; border-radius: 6px;
    }
    .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label, .stRadio label {
        color: #ffffff !important; font-size: 14px !important; font-weight: 600;
    }
    
    /* 側邊欄 */
    section[data-testid="stSidebar"] { background-color: #001a33; border-right: 1px solid #ff9933; }
    
    /* 報告框 (白底深藍字回歸) */
    .report-box {
        background-color: #ffffff !important; padding: 40px; border-radius: 8px;
        border-top: 8px solid var(--text-orange); margin-top: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    .report-box p, .report-box span, .report-box li, .report-box div, 
    .report-box b, .report-box em, .report-box h4, .report-box h5, .report-box h6 {
        color: #003366 !important; /* 專業深藍文字 */
    }
    .report-box h1, .report-box h2 {
        color: #002244 !important; border-bottom: 2px solid #ff9933;
        padding-bottom: 10px; margin-top: 30px; font-weight: 800;
    }
    .report-box h3 { color: #cc4400 !important; font-weight: 700; margin-top: 20px;}
    .report-box strong { color: #002244 !important; background-color: #fff5e6 !important; padding: 0 4px; }

    /* 表格設計 */
    .report-box table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 15px; border-radius: 8px; overflow: hidden; }
    .report-box th { background-color: #003366 !important; color: #ffffff !important; padding: 15px; text-align: left; }
    .report-box th * { color: #ffffff !important; }
    .report-box td { padding: 12px 15px; border-bottom: 1px solid #eeeeee; color: #003366 !important; }
    .report-box tr:nth-child(even) { background-color: #f0f8ff; } 
    
    /* 教練陪練室獨立對話框 (深底亮字) */
    .streamlit-expanderHeader { background-color: rgba(255, 255, 255, 0.1) !important; color: #ff9933 !important; border-radius: 8px; }
    .streamlit-expanderContent { background-color: #0d1b2a !important; padding: 15px; border-radius: 0 0 8px 8px; }
    .streamlit-expanderContent * { color: #e6f7ff !important; }
    
    /* 浮水印回歸 */
    .mars-watermark {
        position: fixed; top: 15px; right: 25px; color: rgba(255, 153, 51, 0.9);
        font-size: 14px; font-weight: 700; z-index: 9999; pointer-events: none;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    }
    #MainMenu, footer {visibility: hidden;}
</style>
<div class="mars-watermark">Made by Mars Chang</div>
""", unsafe_allow_html=True)

# --- 4. 資料庫處理 ---
def init_db():
    conn = sqlite3.connect('insurance_crm.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, user_key TEXT, name TEXT, stage TEXT, data JSON, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

def save_client_to_db(user_key, name, stage, form_data):
    conn = sqlite3.connect('insurance_crm.db')
    c = conn.cursor()
    c.execute("SELECT id FROM clients WHERE user_key=? AND name=?", (user_key, name))
    result = c.fetchone()
    json_data = json.dumps(form_data, default=str)
    if result:
        c.execute("UPDATE clients SET stage=?, data=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (stage, json_data, result[0]))
    else:
        c.execute("INSERT INTO clients (user_key, name, stage, data) VALUES (?, ?, ?, ?)", (user_key, name, stage, json_data))
    conn.commit()
    conn.close()

def get_clients_by_key(user_key):
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

# --- 5. 初始化 Session State ---
if "current_client_data" not in st.session_state: st.session_state.current_client_data = {}
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "current_strategy" not in st.session_state: st.session_state.current_strategy = None
if "user_key" not in st.session_state: st.session_state.user_key = ""
if "kb_text" not in st.session_state: st.session_state.kb_text = ""
if "kb_count" not in st.session_state: st.session_state.kb_count = 0

# --- 6. 核心功能：讀取 PDF 知識庫 ---
def load_kb():
    full_text = ""
    count = 0
    debug_log = []
    if not pdf_tool_ready: return "", 0, ["❌ pdfplumber 未安裝"]
    
    files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    for f in files:
        try:
            with pdfplumber.open(f) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: full_text += text + "\n"
                count += 1
                debug_log.append(f"✅ 成功載入: {f}")
        except Exception as e:
            debug_log.append(f"❌ 讀取失敗 {f}: {e}")
    return full_text, count, debug_log

# 啟動時自動載入
if st.session_state.kb_count == 0:
    kb_t, kb_c, kb_d = load_kb()
    st.session_state.kb_text, st.session_state.kb_count = kb_t, kb_c
    st.session_state.kb_debug = kb_d

# --- 7. 工具函數 ---
def calculate_life_path_number(birth_text):
    digits = re.findall(r'\d', str(birth_text))
    if not digits: return 0
    total = sum(int(digit) for digit in "".join(digits))
    while total > 9: total = sum(int(digit) for digit in str(total))
    return total

def generate_with_retry(model, prompt):
    for _ in range(3):
        try: return model.generate_content(prompt)
        except Exception as e:
            if "429" in str(e): time.sleep(5)
            else: raise e

# --- 8. 側邊欄設計 (名單在上，設定在下) ---
with st.sidebar:
    st.markdown("### 🗂️ 客戶名單管理")
    ukey_input = st.text_input("🔑 專屬金鑰", value=st.session_state.user_key, type="password")
    if ukey_input:
        st.session_state.user_key = ukey_input
        if st.button("➕ 新增客戶"):
            st.session_state.current_client_data, st.session_state.current_strategy, st.session_state.chat_history = {}, None, []
            st.rerun()
        
        clients_df = get_clients_by_key(ukey_input)
        if not clients_df.empty:
            for s in ["S1", "S2", "S3", "S4", "S5", "S6"]:
                stage_df = clients_df[clients_df['stage'].str.startswith(s)]
                if not stage_df.empty:
                    with st.expander(f"📂 {s} ({len(stage_df)}人)"):
                        for _, row in stage_df.iterrows():
                            if st.button(f"👤 {row['name']}", key=f"btn_{row['id']}"):
                                st.session_state.current_client_data = json.loads(row['data'])
                                st.session_state.current_strategy = st.session_state.current_client_data.get('last_strategy')
                                st.session_state.chat_history = st.session_state.current_client_data.get('chat_history', [])
                                st.rerun()
    
    st.markdown("---")
    st.markdown("### 📚 知識庫狀態")
    if st.session_state.kb_count > 0:
        st.success(f"🟢 已掛載 {st.session_state.kb_count} 份手冊")
    else:
        st.info("ℹ️ 未偵測到 PDF 檔案")
    
    st.markdown("---")
    st.markdown("### ⚙️ 系統設定")
    api_key = st.text_input("Google API Key", type="password")
    model = None
    if api_key:
        genai.configure(api_key=api_key)
        try:
            m_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            m_list.sort(key=lambda x: "1.5-flash" not in x)
            sel_m = st.selectbox("🤖 AI 模型 (若額度不足請切換)", m_list)
            model = genai.GenerativeModel(sel_m)
            st.success("🟢 系統已連線")
            if "gemma" in sel_m.lower(): st.warning("⚠️ Gemma 額度低，已限制閱讀量。")
        except: st.error("API Key 驗證失敗")

# --- 9. 主畫面表單 ---
st.markdown("<h1 style='text-align: center;'>保險業務超級軍師</h1>", unsafe_allow_html=True)
data = st.session_state.current_client_data

with st.form("client_form"):
    c1, c2 = st.columns([1, 2])
    with c1: client_name = st.text_input("客戶姓名", value=data.get("name", ""))
    with c2: 
        s_opt = ["S1：取得名單", "S2：約訪", "S3：初步面談", "S4：發覺需求", "S5：說明建議書", "S6：成交"]
        idx = 0
        try: idx = [i for i, x in enumerate(s_opt) if x.startswith(data.get("stage", ""))][0]
        except: pass
        s_stage = st.selectbox("📍 銷售階段", s_opt, index=idx)
    
    c3, c4, c5 = st.columns(3)
    with c3: gender = st.radio("性別", ["男", "女"], index=0 if data.get("gender") == "男" else 1, horizontal=True)
    with c4: birthday = st.text_input("生日 (1990/01/01)", value=data.get("birthday", ""))
    with c5: income = st.text_input("年收 (萬)", value=data.get("income", ""))
    
    job = st.text_input("職業", value=data.get("job", ""))
    quotes = st.text_area("🗣️ 客戶語錄 / 痛點", value=data.get("quotes", ""), height=70)
    target = st.text_area("🎯 銷售目標商品", value=data.get("target_product", ""), height=70)
    
    st.markdown("<h3 style='color:#ff9933;'>🛡️ 保障額度健診</h3>", unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    with g1:
        c_daily = st.text_input("住院日額", value=data.get("cov_daily", ""))
        c_med = st.text_input("醫療實支", value=data.get("cov_med_reim", ""))
    with g2:
        c_cancer = st.text_input("癌症一次金", value=data.get("cov_cancer", ""))
        c_major = st.text_input("重大傷病", value=data.get("cov_major", ""))
    with g3:
        c_ltc = st.text_input("長照/失能", value=data.get("cov_ltc", ""))
        c_life = st.text_input("壽險額度", value=data.get("cov_life", ""))

    if st.form_submit_button("🚀 啟動教練分析"):
        if not api_key or not client_name:
            st.error("請輸入 API Key 與姓名")
        else:
            lpn = calculate_life_path_number(birthday)
            # 額度控管
            limit = 30000 if "flash" in model.model_name.lower() else 5000
            ctx = st.session_state.kb_text[:limit]
            
            prompt = f"""
            你是教練 Coach Mars Chang。
            【參考手冊】: {ctx}
            【客戶】: {client_name}, {lpn}號人, 職業{job}, 年收{income}萬
            【現有保障】: 日額{c_daily}, 實支{c_med}, 癌症{c_cancer}, 重大{c_major}, 長照{c_ltc}, 壽險{c_life}
            【目標與語錄】: {target} / {quotes}
            【任務】: 請依 Mars 標準做保障缺口表格與戰略建議，必須引用手冊中的凱基商品。
            """
            with st.spinner("教練 Mars 正在思考..."):
                res = generate_with_retry(model, prompt)
                st.session_state.current_strategy = res.text
                st.session_state.chat_history = []
                # 儲存
                new_data = {
                    "name": client_name, "stage": s_stage, "gender": gender, "birthday": birthday, "income": income, "job": job, "quotes": quotes, "target_product": target,
                    "cov_daily": c_daily, "cov_med_reim": c_med, "cov_cancer": c_cancer, "cov_major": c_major, "cov_ltc": c_ltc, "cov_life": c_life,
                    "last_strategy": res.text, "chat_history": []
                }
                save_client_to_db(ukey_input, client_name, s_stage, new_data)
                st.rerun()

# --- 10. 顯示分析結果與陪練室 ---
if st.session_state.current_strategy:
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("### 🤖 教練陪練室")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if p := st.chat_input("詢問教練關於此個案的問題..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        limit = 30000 if "flash" in model.model_name.lower() else 5000
        ctx = st.session_state.kb_text[:limit]
        chat_p = f"參考手冊：{ctx}\n個案分析：{st.session_state.current_strategy}\n問題：{p}"
        res = generate_with_retry(model, chat_p)
        st.session_state.chat_history.append({"role": "assistant", "content": res.text})
        st.rerun()
