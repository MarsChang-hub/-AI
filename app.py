import streamlit as st
import google.generativeai as genai
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 🎨 深藍橘色高對比 UI (CSS) ---
st.markdown("""
<style>
    /* 定義配色變數 */
    :root {
        --bg-deep-blue: #001a33;
        --card-blue: #002b4d;
        --text-orange: #ff9933;
        --btn-orange: #ff6600;
        --text-white: #ffffff;
    }

    /* 全域背景 */
    .stApp {
        background-color: var(--bg-deep-blue);
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
    }
    
    /* --- Mars Chang 商標浮水印 --- */
    .mars-watermark {
        position: fixed;
        top: 15px;
        right: 25px;
        color: var(--text-orange);
        font-size: 14px;
        font-weight: 600;
        z-index: 9999;
        font-family: 'Montserrat', sans-serif;
        letter-spacing: 1px;
        opacity: 0.8;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        pointer-events: none;
    }
    @media (max-width: 600px) {
        .mars-watermark {
            font-size: 12px;
            top: 10px;
            right: 15px;
        }
    }

    /* --- 輸入框與選單修復 --- */
    .stTextInput input, .stDateInput input, .stTextArea textarea, 
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid var(--text-orange) !important;
        border-radius: 8px;
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"] {
        background-color: #ffffff !important;
    }
    div[data-baseweb="menu"] li span {
        color: #000000 !important;
    }
    div[data-baseweb="menu"] li:hover, div[data-baseweb="menu"] li[aria-selected="true"] {
        background-color: var(--text-orange) !important;
        color: #ffffff !important;
    }
    .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label, .stRadio label {
        color: var(--text-white) !important;
        font-size: 15px;
    }

    /* --- S線指南卡片樣式 --- */
    .s-line-card {
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 4px solid var(--text-orange);
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 0 10px 10px 0;
    }
    .s-line-title {
        color: var(--text-orange);
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 5px;
    }
    .s-line-content {
        color: #cccccc;
        font-size: 14px;
        line-height: 1.5;
    }
    .s-line-highlight {
        color: #fff;
        font-weight: bold;
    }
    
    /* Expander 樣式優化 */
    .streamlit-expanderHeader {
        background-color: var(--card-blue) !important;
        color: var(--text-white) !important;
        border: 1px solid var(--text-orange) !important;
        border-radius: 8px;
        font-weight: bold;
    }
    .streamlit-expanderContent {
        background-color: rgba(255,255,255,0.02) !important;
        border-radius: 0 0 8px 8px;
        border: 1px solid var(--text-orange);
        border-top: none;
    }

    /* --- 按鈕與報告框 --- */
    .stButton > button {
        width: 100%;
        background: linear-gradient(to bottom, #ff8533, var(--btn-orange));
        color: white !important;
        border: none;
        padding: 16px 0;
        font-size: 18px;
        font-weight: 800;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(255, 102, 0, 0.3);
        margin-top: 10px;
    }
    .report-box {
        background-color: var(--card-blue) !important;
        color: #ffffff !important;
        padding: 25px;
        border-radius: 12px;
        border: 2px solid var(--text-orange);
        font-family: "Microsoft JhengHei", sans-serif;
        line-height: 1.8;
        font-size: 16px;
        white-space: pre-wrap;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        margin-top: 20px;
        margin-bottom: 30px;
    }
    .form-card {
        background-color: var(--card-blue);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #004080;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }

    /* --- 對話視窗 --- */
    .stChatMessage p, .stChatMessage div {
        color: #ffffff !important;
    }
    .stChatMessage {
        background-color: var(--card-blue) !important;
        border: 1px solid #4d4d4d !important;
        border-radius: 10px;
    }
    div[data-testid="stChatMessage"]:nth-child(odd) {
         background-color: rgba(255, 255, 255, 0.05) !important;
    }
    .stChatInput textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid var(--text-orange) !important;
    }

    /* 標題設定 */
    h1, h2, h3, h4 {
        color: var(--text-orange) !important;
    }
    p { color: #cccccc !important; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 插入 Mars Chang 商標 ---
st.markdown('<div class="mars-watermark">Made by Mars Chang</div>', unsafe_allow_html=True)

# --- 初始化 Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_strategy" not in st.session_state:
    st.session_state.current_strategy = None

# --- 工具函數 ---
def calculate_life_path_number(birth_date):
    date_str = birth_date.strftime("%Y%m%d")
    total = sum(int(digit) for digit in date_str)
    while total > 9:
        total = sum(int(digit) for digit in str(total))
    return total

# --- API Key 設定 ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    with st.sidebar:
        st.markdown(f"<h3 style='color: #ff9933;'>⚙️ 系統設定</h3>", unsafe_allow_html=True)
        api_key = st.text_input("請輸入 Google API Key", type="password")

# --- 連線模型 ---
model = None
if api_key:
    genai.configure(api_key=api_key)
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if available_models:
            selected = next((m for m in available_models if 'flash' in m), None)
            if not selected: selected = next((m for m in available_models if 'pro' in m), available_models[0])
            model = genai.GenerativeModel(selected)
    except Exception as e:
        st.error(f"連線失敗：{e}")

# --- 主畫面 ---
st.markdown("<h1>保險業務超級軍師</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 15px; margin-bottom: 15px;'>AI 賦能．顧問式銷售．精準健診</p>", unsafe_allow_html=True)

# --- S線銷售戰略指南 (更新版) ---
with st.expander("📖 點擊查看：S線顧問式銷售詳解 (核心心法)"):
    st.markdown("""
    <div class="s-line-card">
        <div class="s-line-title">S1：取得名單 (Lead Generation)</div>
        <div class="s-line-content">
        • <span class="s-line-highlight">核心策略</span>：定聯 (Regular Contact)。名單不是名字，是連結。<br>
        • <span class="s-line-highlight">分類</span>：強連結、弱連結、無連結。<br>
        • <span class="s-line-highlight">目標</span>：300顆種子計畫，把弱連結養成都強連結。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S2：約訪 (Appointment Setting)</div>
        <div class="s-line-content">
        • <span class="s-line-highlight">核心目標</span>：只賣「見面」，不賣「保險」。<br>
        • <span class="s-line-highlight">話術重點</span>：「學到很棒的觀念想請你聽聽看，給我回饋」。<br>
        • <span class="s-line-highlight">反對處理</span>：沒空? -> 我配合你；電話講? -> 見面才能看肢體回饋。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S3：初步面談 (Initial Interview)</div>
        <div class="s-line-content">
        • <span class="s-line-highlight">核心原則</span>：建立信任 (Rapport)，跟追/第三人/觀察。<br>
        • <span class="s-line-highlight">4大與入點</span>：愛的人、愛自己、想做的事、不安全感。<br>
        • <span class="s-line-highlight">過橋</span>：簡單問幾個問題(收入/支出/資產)進入S4。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S4：發覺需求 (Needs Discovery) ★關鍵</div>
        <div class="s-line-content">
        • <span class="s-line-highlight">執行步驟</span>：Find (找痛點) -> Confirm (正面讚美/描述心聲) -> Expand (人生軸線/往遠處看)。<br>
        • <span class="s-line-highlight">目標</span>：讓隱性需求變顯性痛點，不解決會很痛苦。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S5：說明建議書 (Proposal)</div>
        <div class="s-line-content">
        • <span class="s-line-highlight">核心概念</span>：保險生活化。不講條款，講故事。<br>
        • <span class="s-line-highlight">比喻</span>：醫療=進廠度假；長照=專業瑪麗亞；壽險=現金企業。<br>
        • <span class="s-line-highlight">價值</span>：保住未來的賺錢能力。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S6：成交 (Closing)</div>
        <div class="s-line-content">
        • <span class="s-line-highlight">促成</span>：給予選擇題 (A/B方案)。<br>
        • <span class="s-line-highlight">轉介</span>：成交後請求轉介紹，重新進入 S1 循環。
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 輸入表單 ---
with st.container():
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    
    with st.form("client_form"):
        col_name, col_stage = st.columns([1, 2])
        with col_name:
            client_name = st.text_input("客戶姓名", placeholder="例：王小明")
        with col_stage:
            s_stage = st.selectbox(
                "📍 目前銷售階段 (S線)", 
                ["S1：取得名單 (定聯/分類)", "S2：約訪 (賣見面價值)", "S3：初步面談 (4切點/Rapport)", "S4：發覺需求 (擴大痛點)", "S5：說明建議書 (保險生活化)", "S6：成交 (促成/轉介紹)"]
            )

        st.markdown("<br><h3>📋 客戶基本輪廓</h3>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            gender = st.radio("性別", ["男", "女"], horizontal=True)
        with col2:
            income = st.text_input("年收 (萬)", placeholder="例：100")
            
        birthday = st.date_input("客戶生日", min_value=datetime.date(1950, 1, 1), value=datetime.date(1990, 1, 1))
        
        st.markdown("<br><h3>💼 職業與興趣</h3>", unsafe_allow_html=True)
        job = st.text_input("職業 / 職位", placeholder="例：竹科工程師 / 主管")
        interests = st.text_input("興趣 / 休閒", placeholder="例：登山、美股、看韓劇")

        st.markdown("<br><h3>🛡️ 保障盤點</h3>", unsafe_allow_html=True)
        history_note = st.text_area("投保史備註 (文字描述)", placeholder="例：僅有公司團保，客戶覺得保費太貴...", height=80)
        
        # 詳細保障額度
        with st.expander("➕ 點擊展開：詳細保障額度填寫 (選填)"):
            st.markdown("<p style='color:white; font-size:14px;'>※ 請輸入數字 (單位已標註)</p>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                cov_daily = st.text_input("住院日額", placeholder="標準：4000")
                cov_med_reim = st.text_input("醫療實支實付 (萬)", placeholder="標準：20萬")
                cov_surg = st.text_input("定額手術 (單位)", placeholder="標準：1000")
                cov_acc_reim = st.text_input("意外實支實付 (萬)", placeholder="標準：10萬")
            with c2:
                cov_cancer = st.text_input("癌症一次金 (萬)", placeholder="標準：50萬")
                cov_major = st.text_input("重大傷病 (萬)", placeholder="標準：30萬")
                cov_radio = st.text_input("放療/次", placeholder="標準：6000")
                cov_chemo = st.text_input("化療/次", placeholder="標準：6000")
            with c3:
                cov_ltc = st.text_input("長期照護月給付", placeholder="標準：3萬")
                cov_dis = st.text_input("失能月給付", placeholder="標準：3萬")
                cov_life = st.text_input("壽險 (萬)", placeholder="標準：5倍年薪")

        st.markdown("---")
        st.markdown("<h3>🔍 深度分析線索</h3>", unsafe_allow_html=True)
        quotes = st.text_area("🗣️ 客戶語錄 (破冰關鍵)", placeholder="例：「我覺得保險都騙人的」...", height=100)
        target_product = st.text_area("🎯 你的銷售目標", placeholder="例：美元利變型保單...", height=80)

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 啟動完整戰略分析")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 邏輯處理：生成策略 ---
if submitted:
    if not api_key:
        st.error("⚠️ 請輸入 API Key")
    elif not model:
        st.error("⚠️ 系統連線異常")
    else:
        life_path_num = calculate_life_path_number(birthday)
        display_name = client_name if client_name else "客戶"
        
        # 計算壽險標準
        try:
            income_val = float(income) if income else 0
            life_ins_standard = int(income_val * 5)
        except:
            life_ins_standard = "無法計算"

        with st.spinner(f"🧠 教練正在為【{display_name}】進行診斷..."):
            today = datetime.date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            
            # 組合詳細保障資料
            detailed_coverage = f"""
            【詳細保障額度盤點】
            - 住院日額：{cov_daily if cov_daily else '0'} (標準: 4000)
            - 醫療實支實付：{cov_med_reim if cov_med_reim else '0'} 萬 (標準: 20萬)
            - 定額手術：{cov_surg if cov_surg else '0'} (標準: 1000)
            - 意外實支實付：{cov_acc_reim if cov_acc_reim else '0'} 萬 (標準: 10萬)
            - 癌症一次金：{cov_cancer if cov_cancer else '0'} 萬 (標準: 50萬)
            - 重大傷病一次金：{cov_major if cov_major else '0'} 萬 (標準: 30萬)
            - 放療/次：{cov_radio if cov_radio else '0'} (標準: 6000)
            - 化療/次：{cov_chemo if cov_chemo else '0'} (標準: 6000)
            - 長期照護月給付：{cov_ltc if cov_ltc else '0'} (標準: 3萬)
            - 失能月給付：{cov_dis if cov_dis else '0'} (標準: 3萬)
            - 壽險：{cov_life if cov_life else '0'} 萬 (標準: 5年年薪，約 {life_ins_standard} 萬)
            
            【其他備註】
            {history_note}
            """
            
            # 顧問式銷售核心邏輯 Prompt
            final_prompt = f"""
            你現在是「教練 (Coach) Mars Chang」，一位擁有 20 年保險業經驗、精通「顧問式銷售 (Consultative Sales)」的頂尖專家。
            請以「教練」自稱，語氣要人性化、有溫度、有經驗，像一位前輩在指導後輩。
            
            【目前的戰略位置】
            👉 **{s_stage}**
            
            【S線顧問式銷售核心邏輯 (必須嚴格遵守)】
            S1 (名單): 強調「定聯」與「連結強度」。名單不是名字，是連結。目的是為了以後可以懶惰。
            S2 (約訪): 只賣「見面」不賣保險。話術：「學到一個觀念想請你聽聽看，給我回饋」。拒絕處理：配合客戶時間、見面才能觀察肢體。
            S3 (面談): 建立 Rapport，運用「4切點」(愛的人/愛自己/想做的事/不安全感)。
            S4 (需求): 核心三步驟：Find(找痛點) -> Confirm(正面讚美/描述心聲) -> Expand(人生軸線/往遠處看)。讓隱性需求變顯性。
            S5 (建議書): 保險生活化。不講條款，講故事。比喻：醫療=進廠度假、長照=專業瑪麗亞、壽險=現金企業。
            S6 (成交): 給予選擇題 (A/B方案)，成交後轉介紹 (回到S1)。

            【客戶關鍵密碼】
            👉 **姓名：{display_name}**
            👉 **生命靈數：{life_path_num} 號人**
            
            【客戶資料】
            - 生日：{birthday} (約 {age} 歲)
            - 性別：{gender}
            - 職業：{job}
            - 興趣：{interests}
            - 年收入：{income} 萬
            - 客戶說過的話："{quotes}"
            - 業務員想賣的商品：{target_product}
            
            {detailed_coverage}
            
            【保障缺口審查標準 (Mars Chang 教練標準)】
            1. 住院日額：標準 4000 (單人房費)。
            2. 醫療實支：標準 20萬 (達文西/海扶刀/標靶)。
            3. 定額手術：標準 1000。
            4. 意外實支：標準 10萬 (鈦合金/PRP)。
            5. 癌症/重大傷病：標準 50萬/30萬 (緊急預備金)。
            6. 放療/化療：標準 6000/次 (薪資損失/營養費)。
            7. 長照/失能：標準 3萬 (外籍看護)。
            8. 壽險：標準 5倍年薪 (留愛不留債)。
            
            【輸出要求】
            1. **[客戶畫像與心理分析]**：結合 {life_path_num} 號人性格與職業風險。
            2. **[保障缺口診斷書]**：嚴格比對 Mars Chang 標準，列出具體缺口與後果。
            3. **[本階段 ({s_stage}) 戰略目標]**：引用上述 S 線核心邏輯 (例如 S2 就是賣見面)。
            4. **[建議方向一]**：提供切入點與具體話術 (若是 S2 請用「求回饋」話術；S5 請用「生活化比喻」)。
            5. **[建議方向二]**：提供另一種切入路徑。
            """
            
            try:
                response = model.generate_content(final_prompt)
                st.session_state.current_strategy = response.text
                st.session_state.chat_history = []
                st.session_state.chat_history.append({"role": "assistant", "content": f"我是教練 Mars。已針對 **{display_name}** ({life_path_num} 號人) 完成顧問式銷售分析。請看上方報告！"})
            except Exception as e:
                st.error(f"發生錯誤：{e}")

# --- 顯示策略與陪練室 ---
if st.session_state.current_strategy:
    st.markdown(f"<h4 style='color: #ff9933; text-align: center; margin-top: 20px;'>✅ 教練戰略報告</h4>", unsafe_allow_html=True)
    
    with st.expander("📝 點擊這裡：複製完整報告 (純文字版)"):
        st.code(st.session_state.current_strategy, language="markdown")
    
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<h3>🤖 教練陪練室 (針對上方策略提問)</h3>", unsafe_allow_html=True)

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("輸入你想問的問題... (例如：S2如果他說沒空怎麼回？)"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("教練思考中..."):
                chat_prompt = f"""
                你現在是「教練 (Coach) Mars Chang」。請依照以下「保險策略報告」內容指導新人。
                嚴格遵守「顧問式銷售 S 線」邏輯。
                
                【策略報告內容】：
                {st.session_state.current_strategy}
                
                【新人問題】：
                {prompt}
                
                【教練任務】：
                請以過來人的經驗（人性化、經驗法則）回答。
                若是 S2 問題，強調「配合客戶時間」；若是 S5 問題，強調「比喻故事」。
                """
                
                try:
                    response = model.generate_content(chat_prompt)
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                    
                    with st.expander("📝 複製這個回覆"):
                        st.code(response.text, language="markdown")
                        
                except Exception as e:
                    st.error(f"回覆失敗：{e}")
