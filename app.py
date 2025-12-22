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

# --- 2. 安全引入套件 ---
pdf_tool_ready = False
try:
    import pdfplumber
    pdf_tool_ready = True
except ImportError:
    pdf_tool_ready = False

# --- 3. 🎨 風格設定 ---
st.markdown("""
<style>
    :root { --bg-main: #001222; --text-orange: #ff9933; --text-body: #e0e0e0; }
    .stApp { background-color: var(--bg-main); }
    
    .stTextInput input, .stDateInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important; color: #000000 !important;
        border: 1px solid #ff9933 !important; border-radius: 6px;
    }
    .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label, .stRadio label {
        color: #ffffff !important; font-weight: 600;
    }
    
    section[data-testid="stSidebar"] { background-color: #001a33; border-right: 1px solid #ff9933; }
    
    /* 報告框：更溫暖的配色 */
    .report-box {
        background-color: #ffffff !important; padding: 40px; border-radius: 8px;
        border-top: 8px solid var(--text-orange); margin-top: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        font-family: "Microsoft JhengHei", "Segoe UI", sans-serif;
    }
    .report-box p, .report-box li, .report-box div, .report-box span { 
        color: #2c3e50 !important; /* 深灰藍，比較有質感 */
        line-height: 1.6;
    }
    .report-box h1, .report-box h2 { color: #d35400 !important; border-bottom: 2px solid #ff9933; margin-top: 30px; }
    .report-box h3 { color: #e67e22 !important; font-weight: 700; margin-top: 25px;}
    .report-box strong { color: #c0392b !important; background-color: #fadbd8 !important; padding: 0 4px; }
    
    .report-box table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 15px; }
    .report-box th { background-color: #34495e !important; color: #ffffff !important; padding: 15px; }
    .report-box th * { color: #ffffff !important; }
    .report-box td { padding: 12px 15px; border-bottom: 1px solid #eeeeee; color: #2c3e50 !important; }
    .report-box tr:nth-child(even) { background-color: #f2f3f4; } 

    .mars-watermark {
        position: fixed; top: 15px; right: 25px; color: rgba(255, 153, 51, 0.9);
        font-size: 14px; font-weight: 700; z-index: 9999; pointer-events: none;
    }
    #MainMenu, footer {visibility: hidden;}
</style>
<div class="mars-watermark">Made by Mars Chang</div>
""", unsafe_allow_html=True)

# --- 4. 資料庫功能 ---
def init_db():
    conn = sqlite3.connect('insurance_crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_key TEXT, name TEXT, stage TEXT, data JSON,
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

# --- 5. 初始化 Session ---
if "current_client_data" not in st.session_state: st.session_state.current_client_data = {}
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "current_strategy" not in st.session_state: st.session_state.current_strategy = None
if "user_key" not in st.session_state: st.session_state.user_key = ""
if "kb_text" not in st.session_state: st.session_state.kb_text = ""
if "kb_count" not in st.session_state: st.session_state.kb_count = 0
if "kb_debug" not in st.session_state: st.session_state.kb_debug = []

# --- 6. 核心：知識庫讀取 (支援 xlsx/xlsm/txt/pdf) ---
def load_kb():
    full_text = ""
    count = 0
    debug_log = []
    
    all_files = os.listdir('.')
    debug_log.append(f"📂 目錄檔案: {all_files}")

    # 1. 讀取 Excel (xlsm/xlsx)
    excel_files = [f for f in all_files if f.lower().endswith(('.xlsx', '.xlsm'))]
    for f in excel_files:
        try:
            df = pd.read_excel(f, engine='openpyxl')
            csv_text = df.to_csv(index=False)
            full_text += f"\n=== 資料庫 ({f}) ===\n{csv_text}\n"
            count += 1
            debug_log.append(f"✅ Excel 載入: {f}")
        except Exception as e:
            debug_log.append(f"❌ Excel 失敗 {f}: {e}")

    # 2. 讀取 TXT (UTF-8)
    txt_files = [f for f in all_files if f.lower().endswith('.txt')]
    for f in txt_files:
        if "requirements" in f: continue
        try:
            with open(f, "r", encoding="utf-8") as file:
                full_text += f"\n=== 手冊資料 ({f}) ===\n{file.read()}\n"
                count += 1
                debug_log.append(f"✅ TXT 載入: {f}")
        except Exception as e:
            debug_log.append(f"❌ TXT 失敗 {f}: {e}")

    # 3. 讀取 PDF
    if pdf_tool_ready:
        pdf_files = [f for f in all_files if f.lower().endswith('.pdf')]
        for f in pdf_files:
            try:
                with pdfplumber.open(f) as pdf:
                    text = ""
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted: text += extracted + "\n"
                    full_text += f"\n=== PDF資料 ({f}) ===\n{text}\n"
                    count += 1
                    debug_log.append(f"✅ PDF 載入: {f}")
            except Exception as e:
                debug_log.append(f"❌ PDF 失敗 {f}: {e}")
    
    return full_text, count, debug_log

if st.session_state.kb_count == 0:
    t, c, d = load_kb()
    st.session_state.kb_text, st.session_state.kb_count, st.session_state.kb_debug = t, c, d

# --- 7. 工具函數 ---
def calculate_life_path_number(birth_text):
    digits = re.findall(r'\d', str(birth_text))
    if not digits: return 0
    total = sum(int(digit) for digit in "".join(digits))
    while total > 9: total = sum(int(digit) for digit in str(total))
    return total

def generate_with_retry(model, prompt):
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    for _ in range(3):
        try:
            res = model.generate_content(prompt, safety_settings=safety_settings)
            if res.text: return res
        except Exception as e:
            if "429" in str(e): time.sleep(5)
            else: raise e
    raise Exception("API 回應失敗")

# --- 8. 側邊欄 ---
with st.sidebar:
    st.markdown("### 🗂️ 客戶名單管理")
    ukey_input = st.text_input("🔑 請輸入您的專屬金鑰", value=st.session_state.user_key, type="password")
    
    if ukey_input:
        st.session_state.user_key = ukey_input
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

        clients_df = get_clients_by_key(ukey_input)
        if not clients_df.empty:
            for s in ["S1", "S2", "S3", "S4", "S5", "S6"]:
                stage_clients = clients_df[clients_df['stage'].str.startswith(s)]
                if not stage_clients.empty:
                    with st.expander(f"📂 {s} ({len(stage_clients)}人)"):
                        for _, row in stage_clients.iterrows():
                            if st.button(f"👤 {row['name']}", key=f"btn_{row['id']}"):
                                st.session_state.current_client_data = json.loads(row['data'])
                                st.session_state.current_strategy = st.session_state.current_client_data.get('last_strategy')
                                st.session_state.chat_history = st.session_state.current_client_data.get('chat_history', [])
                                st.rerun()
    else:
        st.warning("請輸入金鑰以存取名單")

    st.markdown("---")
    
    # 知識庫診斷
    st.markdown("### 📚 知識庫")
    if st.session_state.kb_count > 0:
        st.success(f"✅ 已掛載 {st.session_state.kb_count} 份文件")
    else:
        st.info("ℹ️ 未偵測到文件")
    
    with st.expander("🔍 檔案狀態"):
        for m in st.session_state.kb_debug: st.write(m)
        if st.button("🔄 重新掃描"):
            st.session_state.kb_count = 0
            st.rerun()

    st.markdown("---")
    
    # 模型設定
    api_key = ""
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.caption("🔑 API Key 已自動掛載")
    else:
        api_key = st.text_input("請輸入 Google API Key", type="password")

    model = None
    if api_key:
        genai.configure(api_key=api_key)
        try:
            all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_keywords = ['flash', 'gemma']
            filtered_models = [m for m in all_models if any(k in m.lower() for k in target_keywords)]
            filtered_models.sort(key=lambda x: "flash" not in x.lower())
            if not filtered_models: filtered_models = all_models

            st.markdown("### 🤖 模型選擇")
            selected_model_name = st.selectbox("請選擇 AI 大腦", filtered_models, index=0)
            model = genai.GenerativeModel(selected_model_name)
            st.success(f"🟢 已連線")
        except Exception as e:
            st.error(f"連線失敗: {e}")

# --- 9. 主畫面 ---
col_t1, col_t2, col_t3 = st.columns([1, 6, 1])
with col_t2:
    st.markdown("<h1 style='text-align: center;'>保險業務超級軍師</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #bbb;'>CRM 雲端版．顧問式銷售．精準健診</p>", unsafe_allow_html=True)

data = st.session_state.current_client_data
with st.form("client_form"):
    c1, c2 = st.columns([1, 2])
    with c1: client_name = st.text_input("客戶姓名", value=data.get("name", ""))
    with c2: 
        s_opt = ["S1：取得名單 (定聯/分類)", "S2：約訪 (賣見面價值)", "S3：初步面談 (4切點/Rapport)", "S4：發覺需求 (擴大痛點)", "S5：說明建議書 (保險生活化)", "S6：成交 (促成/轉介紹)"]
        idx = 0
        try: idx = [i for i, x in enumerate(s_opt) if x.startswith(data.get("stage", ""))][0]
        except: pass
        s_stage = st.selectbox("📍 銷售階段 (S線)", s_opt, index=idx)

    c3, c4, c5 = st.columns(3)
    with c3: gender = st.radio("性別", ["男", "女"], index=0 if data.get("gender") == "男" else 1, horizontal=True)
    with c4: birthday = st.text_input("生日 (西元年/月/日)", value=data.get("birthday", ""))
    with c5: income = st.text_input("年收 (萬)", value=data.get("income", ""))

    c6, c7 = st.columns(2)
    with c6: job = st.text_input("職業 / 職位", value=data.get("job", ""))
    with c7: interests = st.text_input("興趣 / 休閒", value=data.get("interests", ""))

    st.markdown("<h3 style='margin-top:15px; color:#ff9933;'>🛡️ 保障盤點與分析</h3>", unsafe_allow_html=True)
    with st.expander("➕ 詳細保障額度 (點擊展開填寫)", expanded=True):
        g1, g2, g3 = st.columns(3)
        with g1:
            cov_daily = st.text_input("住院日額", value=data.get("cov_daily", ""))
            cov_med_reim = st.text_input("醫療實支 (萬)", value=data.get("cov_med_reim", ""))
            cov_surg = st.text_input("定額手術", value=data.get("cov_surg", ""))
            cov_acc_reim = st.text_input("意外實支 (萬)", value=data.get("cov_acc_reim", ""))
        with g2:
            cov_cancer = st.text_input("癌症一次金 (萬)", value=data.get("cov_cancer", ""))
            cov_major = st.text_input("重大傷病 (萬)", value=data.get("cov_major", ""))
            cov_radio = st.text_input("放療/次", value=data.get("cov_radio", ""))
            cov_chemo = st.text_input("化療/次", value=data.get("cov_chemo", ""))
        with g3:
            cov_ltc = st.text_input("長照月給付", value=data.get("cov_ltc", ""))
            cov_dis = st.text_input("失能月給付", value=data.get("cov_dis", ""))
            cov_life = st.text_input("壽險 (萬)", value=data.get("cov_life", ""))
            
    history_note = st.text_area("投保史備註 / 其他狀況", value=data.get("history_note", ""), height=68)
    
    c8, c9 = st.columns(2)
    with c8: quotes = st.text_area("🗣️ 客戶語錄 (痛點)", value=data.get("quotes", ""), height=68)
    with c9: target_product = st.text_area("🎯 銷售目標 (AI 將優先建議此項目)", value=data.get("target_product", ""), height=68)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1, 1, 2])
    with b1: save_btn = st.form_submit_button("💾 僅儲存資料")
    with b3: analyze_btn = st.form_submit_button("🚀 儲存並啟動教練分析")

# --- 處理按鈕邏輯 ---
if save_btn or analyze_btn:
    if not st.session_state.user_key: st.error("⚠️ 請先在側邊欄輸入「專屬金鑰」！")
    elif not client_name: st.error("⚠️ 客戶姓名為必填！")
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
        
        if save_btn:
            st.success(f"✅ {client_name} 的資料已儲存！")
        
        if analyze_btn:
            if not model: st.error("⚠️ 請確認 API Key 連線")
            else:
                life_path_num = calculate_life_path_number(birthday)
                is_flash = "flash" in model.model_name.lower() or "1.5" in model.model_name.lower()
                limit = 35000 if is_flash else 5000
                kb_context = st.session_state.kb_text[:limit]
                
                detailed_coverage = f"""
                【保障盤點】日額:{cov_daily}, 實支:{cov_med_reim}, 手術:{cov_surg}, 意外:{cov_acc_reim}, 癌:{cov_cancer}, 重大:{cov_major}, 長照:{cov_ltc}, 壽險:{cov_life}。備註:{history_note}
                """
                
                # ★★★ 核心Prompt：20年資深顧問、SPIN、NLP、禁談保費、禁談來源 ★★★
                prompt = f"""
                【角色設定】
                你是一位擁有20年經驗的頂尖保險顧問，深諳人性，擅長運用 NLP (神經語言學) 與客戶建立深層連結。
                你的風格：感性優先、理性為輔。你不是在賣商品，而是在協助客戶解決家庭的擔憂。
                你精通 SPIN 銷售法，擅長用情境問句引發客戶對風險的覺察。

                【絕對規則 (Constraints)】
                1. **嚴禁提及保費/價格**：即便資料庫有數據，也絕對不要在報告中顯示任何費用數字。
                2. **隱藏資料來源**：請將知識內化，直接給出專業建議，絕對不要說「根據 Excel」或「依據手冊」。
                3. **銷售目標優先**：請全力聚焦於推廣「{target_product}」。
                4. **其他建議後置**：若有其他缺口(如壽險)，請放在最後稍微帶過即可。

                【客戶資料】
                {client_name}, {life_path_num} 號人, {job}, 年收{income}萬
                語錄："{quotes}"
                現有保障：{detailed_coverage}
                
                【參考資料 (僅供內部邏輯參考)】:
                {kb_context}

                【輸出架構 (請用溫暖、專業、像在對話的語氣)】
                1. **[💖 暖心開場]** (運用 NLP 技巧，呼應客戶語錄，先處理心情，再處理事情。展現同理心。)
                
                2. **[❓ SPIN 情境探索]** (針對 {target_product} 設計 3-4 個情境式問句。例如：「如果發生...對家庭會有什麼影響？」引發痛點。)
                
                3. **[🛡️ 顧問式解決方案]** (提出概念性的解法，說明 {target_product} 如何解決上述痛點。強調價值，不談價格。)
                
                4. **[📊 專屬規劃建議]** (在此處才引用商品名稱與理賠優勢。請列出中文商品名與英文代號。若 Excel 有理賠數據，請在此展示"給付內容"，但絕不能提保費。)
                
                5. **[💡 其他溫馨提醒]** (補充建議其他缺口，點到為止)
                """
                
                with st.spinner("資深顧問 Mars 正在構思 SPIN 策略..."):
                    try:
                        res = generate_with_retry(model, prompt)
                        st.session_state.current_strategy = res.text
                        st.session_state.chat_history = []
                        form_data['last_strategy'] = res.text
                        save_client_to_db(st.session_state.user_key, client_name, s_stage, form_data)
                        st.rerun()
                    except Exception as e:
                        st.error(f"分析失敗: {e}")

# --- 10. 顯示分析結果 ---
if st.session_state.current_strategy:
    st.markdown("---")
    st.markdown(f"<h3 style='text-align: center; border:none;'>✅ 教練戰略報告 ({st.session_state.current_client_data.get('name', '客戶')})</h3>", unsafe_allow_html=True)
    
    with st.expander("📝 複製完整報告"):
        st.code(st.session_state.current_strategy, language="markdown")
    
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("<h3 style='border:none; margin-top:30px;'>🤖 教練陪練室</h3>", unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        role = msg['role']
        content = msg['content']
        if role == 'user':
            st.info(f"🙋‍♂️ 你的提問：{content}")
        else:
            with st.expander(f"💬 教練回覆", expanded=True):
                st.write(content)

    if prompt := st.chat_input("輸入問題..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        if not model: st.error("請確認連線")
        else:
            with st.spinner("教練思考中..."):
                is_flash = "flash" in model.model_name.lower() or "1.5" in model.model_name.lower()
                limit = 35000 if is_flash else 5000
                kb_context = st.session_state.kb_text[:limit]
                
                chat_prompt = f"""
                你是 Coach Mars Chang，一位 20 年資深保險顧問。
                你的風格：SPIN 提問、NLP 感性溝通、絕對不提保費、不透露資料來源。
                參考資料：{kb_context}
                報告：{st.session_state.current_strategy}
                問題：{prompt}
                任務：請延續上述風格進行指導。
                """
                try:
                    res = generate_with_retry(model, chat_prompt)
                    st.session_state.chat_history.append({"role": "assistant", "content": res.text})
                    
                    curr = st.session_state.current_client_data
                    if curr:
                        curr['chat_history'] = st.session_state.chat_history
                        save_client_to_db(st.session_state.user_key, curr['name'], curr['stage'], curr)
                    st.rerun()
                except Exception as e:
                    st.error(f"回覆失敗: {e}")
