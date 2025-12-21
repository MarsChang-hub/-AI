import streamlit as st
import google.generativeai as genai
import datetime
import sqlite3
import json
import pandas as pd
import re
import time

# --- 頁面設定 ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 🎨 風格設定 (深藍專業版 + 高質感報告 + 陪練室優化) ---
st.markdown("""
<style>
    :root {
        --bg-main: #001222;
        --glass-card: rgba(255, 255, 255, 0.05);
        --text-orange: #ff9933;
        --text-body: #e0e0e0;
        --btn-gradient: linear-gradient(135deg, #ff8533 0%, #cc4400 100%);
    }
    .stApp { background-color: var(--bg-main); }
    p, li, span, div { color: var(--text-body); }
    .block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; max-width: 1200px; }
    
    /* 輸入框絕對顯色 */
    .stTextInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #ff9933 !important;
        border-radius: 6px;
    }
    .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label, .stRadio label {
        color: #ffffff !important; font-size: 14px !important; font-weight: 600;
    }
    
    /* 下拉選單修復 */
    div[data-baseweb="popover"], div[data-baseweb="menu"] { background-color: #ffffff !important; }
    div[data-baseweb="menu"] div { color: #000000 !important; }
    li[aria-selected="true"], li[data-baseweb="option"]:hover { background-color: #ffe6cc !important; }
    li[aria-selected="true"] div, li[data-baseweb="option"]:hover div { color: #ff6600 !important; font-weight: bold; }

    /* 側邊欄 */
    section[data-testid="stSidebar"] {
        background-color: #001a33;
        border-right: 1px solid #ff9933;
    }
    
    /* 按鈕優化 */
    div.row-widget.stButton > button {
        background: transparent;
        border: 1px solid rgba(255,255,255,0.2);
        color: #ddd !important;
        text-align: left;
    }
    div.row-widget.stButton > button:hover {
        border-color: #ff9933;
        color: #ff9933 !important;
    }
    .delete-btn button {
        background-color: #ff4d4d !important;
        color: white !important;
        border: none;
    }

    /* 報告框優化 */
    .report-box {
        background-color: #ffffff !important;
        color: #333333 !important;
        padding: 40px;
        border-radius: 8px;
        border-top: 8px solid var(--text-orange);
        margin-top: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
    }
    .report-box h1, .report-box h2 {
        color: #001a33 !important;
        border-bottom: 2px solid #ff9933;
        padding-bottom: 10px;
        margin-top: 30px;
        font-weight: 800;
    }
    .report-box h3 { color: #cc4400 !important; font-weight: 700; margin-top: 20px;}
    .report-box p, .report-box li { color: #333333 !important; line-height: 1.8; font-size: 16px; }
    .report-box strong { color: #001a33 !important; background-color: #fff5e6; padding: 0 4px; }

    /* 表格設計 */
    .report-box table {
        width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 15px;
        border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .report-box th {
        background-color: #001a33 !important; color: #ffffff !important; padding: 15px; text-align: left;
    }
    .report-box td {
        padding: 12px 15px; border-bottom: 1px solid #eeeeee; color: #333333 !important;
    }
    .report-box tr:nth-child(even) { background-color: #f8f9fa; }
    .report-box tr:hover { background-color: #fff5e6; transition: background-color 0.2s; }
    
    /* 教練陪練室獨立對話框 */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: #ff9933 !important;
        border: 1px solid rgba(255, 153, 51, 0.3) !important;
        border-radius: 8px;
        font-weight: bold;
        margin-top: 10px;
    }
    .streamlit-expanderContent {
        border: 1px solid rgba(255, 153, 51, 0.2);
        border-top: none;
        border-radius: 0 0 8px 8px;
        background-color: rgba(0, 0, 0, 0.2);
        padding: 15px;
    }
    
    .mars-watermark {
        position: fixed; top: 15px; right: 25px;
        color: rgba(255, 153, 51, 0.9);
        font-size: 14px; font-weight: 700;
        z-index: 9999; pointer-events: none;
        font-family: 'Montserrat', sans-serif;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="mars-watermark">Made by Mars Chang</div>', unsafe_allow_html=True)

# --- 資料庫處理 ---
def init_db():
    conn = sqlite3.connect('insurance_crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_key TEXT,
                  name TEXT,
                  stage TEXT,
                  data JSON,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
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
    try:
        df = pd.read_sql_query("SELECT * FROM clients WHERE user_key=? ORDER BY updated_at DESC", conn, params=(user_key,))
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def delete_client(user_key, name):
    conn = sqlite3.connect('insurance_crm.db')
    c = conn.cursor()
    c.execute("DELETE FROM clients WHERE user_key=? AND name=?", (user_key, name))
    conn.commit()
    conn.close()

init_db()

# --- 初始化 Session State ---
if "current_client_data" not in st.session_state:
    st.session_state.current_client_data = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_strategy" not in st.session_state:
    st.session_state.current_strategy = None
if "user_key" not in st.session_state:
    st.session_state.user_key = ""

# --- 工具函數 ---
def calculate_life_path_number(birth_text):
    digits = re.findall(r'\d', str(birth_text))
    if not digits: return 0
    date_str = "".join(digits)
    total = sum(int(digit) for digit in date_str)
    while total > 9:
        total = sum(int(digit) for digit in str(total))
    return total

# --- ★★★ API 自動重試函數 ★★★ ---
def generate_content_with_retry(model_instance, prompt):
    max_retries = 3
    base_delay = 5 
    
    for attempt in range(max_retries):
        try:
            return model_instance.generate_content(prompt)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Quota" in error_str:
                if attempt == max_retries - 1:
                    raise e
                wait_time = base_delay * (attempt + 1) + 5
                placeholder = st.empty()
                for t in range(wait_time, 0, -1):
                    placeholder.warning(f"⚠️ API 額度冷卻中 (429)... 系統將在 {t} 秒後自動重試 (嘗試 {attempt+1}/{max_retries})")
                    time.sleep(1)
                placeholder.empty()
            else:
                raise e 

# --- ★★★ 核心：自動偵測正確的 Flash 模型 (第一次修正時的參數邏輯) ★★★ ---
def get_auto_detected_model(api_key):
    genai.configure(api_key=api_key)
    try:
        # 1. 取得所有可用模型清單
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 2. 優先尋找 1.5 Flash (最穩定且額度高)
        # 這是您第一次修正成功時的邏輯：去清單裡找名字有 'flash' 的
        selected_model_name = next((m for m in available_models if '1.5' in m and 'flash' in m), None)
        
        if not selected_model_name:
             # 如果沒有 1.5 flash，找任何 flash
            selected_model_name = next((m for m in available_models if 'flash' in m), None)
            
        if not selected_model_name:
            # 真的都沒有，找 Pro (排除 2.5)
            selected_model_name = next((m for m in available_models if 'pro' in m), None)
            
        # 如果還是空的，就強制用字串 (極少發生，除非 API Key 權限全無)
        if not selected_model_name:
            selected_model_name = 'gemini-1.5-flash'
            
        return genai.GenerativeModel(selected_model_name)
    except:
        # 最後防線，直接回傳預設物件，避免 crash
        return genai.GenerativeModel('gemini-1.5-flash')

# --- 側邊欄 ---
with st.sidebar:
    st.markdown("### 🗂️ 客戶名單管理")
    user_key_input = st.text_input("🔑 請輸入您的專屬金鑰", value=st.session_state.user_key, placeholder="例如：您的手機號碼", type="password")
    
    if user_key_input:
        st.session_state.user_key = user_key_input
        st.success(f"已載入名單")
        
        col_new, col_del = st.columns([1, 1])
        with col_new:
            if st.button("➕ 新增客戶"):
                st.session_state.current_client_data = {} 
                st.session_state.current_strategy = None
                st.session_state.chat_history = []
                st.rerun()
        
        if st.session_state.current_client_data.get("name"):
            with col_del:
                if st.button("🗑️ 刪除個案"):
                    client_to_delete = st.session_state.current_client_data["name"]
                    delete_client(st.session_state.user_key, client_to_delete)
                    st.session_state.current_client_data = {} 
                    st.session_state.current_strategy = None
                    st.session_state.chat_history = []
                    st.warning(f"已刪除 {client_to_delete}")
                    st.rerun()

        clients_df = get_clients_by_key(user_key_input)
        
        if not clients_df.empty:
            st.markdown("---")
            stages = ["S1", "S2", "S3", "S4", "S5", "S6"]
            for stage_prefix in stages:
                stage_clients = clients_df[clients_df['stage'].str.startswith(stage_prefix)]
                if not stage_clients.empty:
                    with st.expander(f"📂 {stage_prefix} ({len(stage_clients)}人)", expanded=False):
                        for index, row in stage_clients.iterrows():
                            if st.button(f"👤 {row['name']}", key=f"btn_{row['id']}"):
                                loaded_data = json.loads(row['data'])
                                st.session_state.current_client_data = loaded_data
                                st.session_state.current_strategy = loaded_data.get('last_strategy')
                                st.session_state.chat_history = loaded_data.get('chat_history', [])
                                st.rerun()
    else:
        st.warning("請輸入金鑰以存取您的名單")

# --- 主畫面 ---
col_t1, col_t2, col_t3 = st.columns([1, 6, 1])
with col_t2:
    st.markdown("<h1 style='text-align: center;'>保險業務超級軍師</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #bbb; margin-bottom: 10px;'>CRM 雲端版．顧問式銷售．精準健診</p>", unsafe_allow_html=True)

# --- API Key 設定 ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.text_input("請輸入 Google API Key", type="password")

model = None
if api_key:
    # ★★★ 使用回歸第一次成功的動態偵測函數 ★★★
    model = get_auto_detected_model(api_key)

# --- 表單 ---
data = st.session_state.current_client_data
st.markdown('<div class="form-card" style="background:rgba(255,255,255,0.05); padding:20px; border-radius:12px;">', unsafe_allow_html=True)
with st.form("client_form"):
    c1, c2 = st.columns([1, 2])
    with c1:
        client_name = st.text_input("客戶姓名", value=data.get("name", ""))
    with c2:
        s_options = ["S1：取得名單 (定聯/分類)", "S2：約訪 (賣見面價值)", "S3：初步面談 (4切點/Rapport)", "S4：發覺需求 (擴大痛點)", "S5：說明建議書 (保險生活化)", "S6：成交 (促成/轉介紹)"]
        default_index = 0
        if "stage" in data:
            try: default_index = s_options.index(data["stage"])
            except: pass
        s_stage = st.selectbox("📍 銷售階段 (S線)", s_options, index=default_index)

    c3, c4, c5 = st.columns(3)
    with c3:
        gender_idx = 0 if data.get("gender") == "男" else 1
        gender = st.radio("性別", ["男", "女"], index=gender_idx, horizontal=True)
    with c4:
        birthday = st.text_input("生日 (西元年/月/日)", value=data.get("birthday", ""), placeholder="例：1990/01/01")
    with c5:
        income = st.text_input("年收 (萬)", value=data.get("income", ""))

    c6, c7 = st.columns(2)
    with c6:
        job = st.text_input("職業 / 職位", value=data.get("job", ""))
    with c7:
        interests = st.text_input("興趣 / 休閒", value=data.get("interests", ""))

    st.markdown("<h3 style='margin-top:15px; color:#ff9933;'>🛡️ 保障盤點與分析</h3>", unsafe_allow_html=True)
    with st.expander("➕ 詳細保障額度 (點擊展開填寫)", expanded=True):
        g1, g2, g3 = st.columns(3)
        with g1:
            cov_daily = st.text_input("住院日額", value=data.get("cov_daily", ""), placeholder="標準:4000")
            cov_med_reim = st.text_input("醫療實支 (萬)", value=data.get("cov_med_reim", ""), placeholder="標準:20")
            cov_surg = st.text_input("定額手術", value=data.get("cov_surg", ""), placeholder="標準:1000")
            cov_acc_reim = st.text_input("意外實支 (萬)", value=data.get("cov_acc_reim", ""), placeholder="標準:10")
        with g2:
            cov_cancer = st.text_input("癌症一次金 (萬)", value=data.get("cov_cancer", ""), placeholder="標準:50")
            cov_major = st.text_input("重大傷病 (萬)", value=data.get("cov_major", ""), placeholder="標準:30")
            cov_radio = st.text_input("放療/次", value=data.get("cov_radio", ""), placeholder="標準:3000")
            cov_chemo = st.text_input("化療/次", value=data.get("cov_chemo", ""), placeholder="標準:3000")
        with g3:
            cov_ltc = st.text_input("長照月給付", value=data.get("cov_ltc", ""), placeholder="標準:3萬")
            cov_dis = st.text_input("失能月給付", value=data.get("cov_dis", ""), placeholder="標準:3萬")
            cov_life = st.text_input("壽險 (萬)", value=data.get("cov_life", ""), placeholder="標準:5倍年薪")
            
    history_note = st.text_area("投保史備註 / 其他狀況", value=data.get("history_note", ""), height=68)
    
    c8, c9 = st.columns(2)
    with c8:
        quotes = st.text_area("🗣️ 客戶語錄 (痛點:愛的人、愛自己、想做的事、不安全感)", value=data.get("quotes", ""), height=68)
    with c9:
        target_product = st.text_area("🎯 銷售目標", value=data.get("target_product", ""), height=68)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 2])
    with b1:
        save_btn = st.form_submit_button("💾 僅儲存資料")
    with b3:
        analyze_btn = st.form_submit_button("🚀 儲存並啟動教練分析")

st.markdown('</div>', unsafe_allow_html=True)

# --- 處理儲存與分析邏輯 ---
if save_btn or analyze_btn:
    if not st.session_state.user_key:
        st.error("⚠️ 請先在側邊欄輸入「專屬金鑰」才能儲存資料！")
    elif not client_name:
        st.error("⚠️ 客戶姓名為必填！")
    else:
        form_data = {
            "name": client_name, "stage": s_stage, "gender": gender, 
            "birthday": str(birthday), "income": income, "job": job, "interests": interests,
            "cov_daily": cov_daily, "cov_med_reim": cov_med_reim, "cov_surg": cov_surg,
            "cov_acc_reim": cov_acc_reim, "cov_cancer": cov_cancer, "cov_major": cov_major,
            "cov_radio": cov_radio, "cov_chemo": cov_chemo, "cov_ltc": cov_ltc, 
            "cov_dis": cov_dis, "cov_life": cov_life, "history_note": history_note,
            "quotes": quotes, "target_product": target_product,
            "last_strategy": st.session_state.current_strategy,
            "chat_history": st.session_state.chat_history
        }
        
        save_client_to_db(st.session_state.user_key, client_name, s_stage, form_data)
        st.success(f"✅ {client_name} 的資料已更新！")
        
        if analyze_btn:
            if not model:
                st.error("⚠️ 系統連線異常，請檢查 API Key")
            else:
                life_path_num = calculate_life_path_number(birthday)
                
                age = "未知"
                try:
                    for fmt in ["%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d", "%Y%m%d"]:
                        try:
                            bday_obj = datetime.datetime.strptime(birthday, fmt).date()
                            today = datetime.date.today()
                            age = today.year - bday_obj.year - ((today.month, today.day) < (bday_obj.month, bday_obj.day))
                            break
                        except: continue
                except: pass

                coverage_inputs = [cov_daily, cov_med_reim, cov_surg, cov_acc_reim, cov_cancer, cov_major, cov_radio, cov_chemo, cov_ltc, cov_dis, cov_life]
                has_coverage_data = any(x.strip() for x in coverage_inputs)
                has_medical_intent = "醫療" in target_product
                show_gap_analysis = has_coverage_data or has_medical_intent

                detailed_coverage = f"""
                【詳細保障額度盤點】
                - 住院日額：{cov_daily if cov_daily else '0'} (標準: 4000)
                - 醫療實支：{cov_med_reim if cov_med_reim else '0'} 萬 (標準: 20萬)
                - 定額手術：{cov_surg if cov_surg else '0'} (標準: 1000)
                - 意外實支：{cov_acc_reim if cov_acc_reim else '0'} 萬 (標準: 10萬)
                - 癌症一次金：{cov_cancer if cov_cancer else '0'} 萬 (標準: 50萬)
                - 重大傷病：{cov_major if cov_major else '0'} 萬 (標準: 30萬)
                - 放療/次：{cov_radio if cov_radio else '0'} (標準: 3000)
                - 化療/次：{cov_chemo if cov_chemo else '0'} (標準: 3000)
                - 長照月給付：{cov_ltc if cov_ltc else '0'} (標準: 3萬)
                - 失能月給付：{cov_dis if cov_dis else '0'} (標準: 3萬)
                - 壽險：{cov_life if cov_life else '0'} 萬 (標準: 5倍年薪)
                【備註】{history_note}
                """

                output_requirements = """
                1. **[客戶畫像與心理分析]**：({life_path_num}號人性格+風險)
                """
                if show_gap_analysis:
                    output_requirements += """
                2. **[保障額度健康度檢核表]**
                (請製作一個 Markdown 表格，欄位如下：)
                | 檢核項目 | 目前額度 | Mars標準 | 狀態 | 
                | :--- | :--- | :--- | :---: |
                (狀態欄請使用 ✅ / ⚠️ / 🆘 代表：及格 / 略低 / 嚴重不足)
                    """
                output_requirements += f"""
                3. **[戰略目標 ({s_stage})]**
                4. **[建議方向一]**
                5. **[建議方向二]**
                """
                if show_gap_analysis:
                    output_requirements += """
                6. **[⚠️ 缺口風險與嚴重性分析]** (集中說明未達標項目的後果)
                    """

                final_prompt = f"""
                你是「教練 Coach Mars Chang」。嚴格遵守「顧問式銷售」與「Mars Chang 保障標準」。
                請使用豐富的 Markdown 語法讓報告美觀易讀（使用粗體、條列、表格）。
                
                【戰略位置】{s_stage}
                【客戶】{client_name}, {life_path_num} 號人, {age}歲, {job}, 年收{income}萬
                【語錄】"{quotes}"
                【目標】{target_product}
                {detailed_coverage}
                
                【Mars Chang 標準】
                1.住院日額:4000。2.醫療實支:20萬。3.定額手術:1000。
                4.意外實支:10萬。5.癌/重:50/30萬。6.放化療:3000。
                7.長照失能:3萬。8.壽險:5倍年薪。

                【輸出要求】
                {output_requirements}
                """
                
                with st.spinner("教練 Mars 正在分析..."):
                    try:
                        # 使用自動重試函數
                        response = generate_content_with_retry(model, final_prompt)
                        st.session_state.current_strategy = response.text
                        st.session_state.chat_history = []
                        form_data['last_strategy'] = response.text
                        save_client_to_db(st.session_state.user_key, client_name, s_stage, form_data)
                        st.rerun()
                    except Exception as e:
                        st.error(f"分析失敗 (已達最大重試次數): {e}")

# --- 顯示結果 ---
if st.session_state.current_strategy:
    st.markdown("---")
    st.markdown(f"<h3 style='text-align: center; border:none;'>✅ 教練戰略報告 ({st.session_state.current_client_data.get('name', '客戶')})</h3>", unsafe_allow_html=True)
    
    with st.expander("📝 複製完整報告"):
        st.code(st.session_state.current_strategy, language="markdown")
    
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("<h3 style='border:none; margin-top:30px;'>🤖 教練陪練室</h3>", unsafe_allow_html=True)

    messages = st.session_state.chat_history
    user_indices = [i for i, m in enumerate(messages) if m['role'] == 'user']

    if not user_indices:
        st.info("尚未開始對話，請在下方輸入問題...")
    else:
        for idx, i in enumerate(user_indices):
            question = messages[i]['content']
            answer = None
            if i + 1 < len(messages) and messages[i+1]['role'] == 'assistant':
                answer = messages[i+1]['content']
            
            is_expanded = (idx == len(user_indices) - 1)
            expander_title = f"💬 第 {idx+1} 回合：{question[:30]}..." if len(question) > 30 else f"💬 第 {idx+1} 回合：{question}"
            
            with st.expander(expander_title, expanded=is_expanded):
                st.markdown(f"**🙋‍♂️ 你的提問**：\n{question}")
                st.markdown("---")
                if answer:
                    st.markdown(f"**🤖 教練回覆**：\n{answer}")
                    st.code(answer, language="markdown")
                else:
                    st.warning("教練正在思考中...")

    if prompt := st.chat_input("輸入問題..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        if not model:
            st.error("請先輸入 API Key")
        else:
            with st.spinner("教練思考中..."):
                chat_prompt = f"""
                你是 Coach Mars Chang。
                報告：{st.session_state.current_strategy}
                問題：{prompt}
                任務：人性化指導。
                """
                try:
                    # 使用自動重試函數
                    response = generate_content_with_retry(model, chat_prompt)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                    
                    current_data = st.session_state.current_client_data
                    if current_data:
                        current_data['chat_history'] = st.session_state.chat_history
                        save_client_to_db(st.session_state.user_key, current_data['name'], current_data['stage'], current_data)
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"回覆失敗 (已達最大重試次數): {e}")
