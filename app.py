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
    
    /* Expander 樣式優化 */
    .streamlit-expanderHeader {
        background-color: var(--card-blue) !important;
        color: var(--text-white) !important;
        border: 1px solid var(--text-orange) !important;
        border-radius: 8px;
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

# --- 初始化 Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_strategy" not in st.session_state:
    st.session_state.current_strategy = None

# --- 工具函數：計算生命靈數 ---
def calculate_life_path_number(birth_date):
    # 格式化為 YYYYMMDD 字串
    date_str = birth_date.strftime("%Y%m%d")
    # 將所有數字相加
    total = sum(int(digit) for digit in date_str)
    
    # 遞迴相加直到剩下一位數 (1-9)
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

# --- 主畫面標題 ---
st.markdown("<h1>保險業務超級軍師</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 15px; margin-bottom: 15px;'>AI 賦能．S線戰略．靈數解碼</p>", unsafe_allow_html=True)

# --- S線銷售戰略指南 (收合選單) ---
with st.expander("📖 點擊查看：S線銷售循環詳解 (S1~S6)"):
    st.markdown("""
    <div class="s-line-card">
        <div class="s-line-title">S1：取得名單 (Lead Generation)</div>
        <div class="s-line-content">
        • 核心目標：區分「嫌疑」與「潛在」名單。<br>
        • 執行重點：初步篩選 (Qualification)。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S2：約訪 (Appointment Setting)</div>
        <div class="s-line-content">
        • 核心目標：賣「見面的價值」，不賣產品。<br>
        • 執行重點：引起好奇，降低防備。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S3：初步面談 (Initial Interview)</div>
        <div class="s-line-content">
        • 核心目標：破冰，建立信任，SPIN-Situation。<br>
        • 執行重點：蒐集背景，觀察 DISC/靈數特質。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S4：發覺需求 (Needs Discovery)</div>
        <div class="s-line-content">
        • 核心目標：隱性需求轉顯性 (SPIN-P/I/N)。<br>
        • 執行重點：擴大痛點，讓客戶覺得不解決不行。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S5：說明建議書 (Proposal)</div>
        <div class="s-line-content">
        • 核心目標：FAB 法則，證明方案解決 S4 痛點。<br>
        • 執行重點：針對痛點客製化，不堆疊功能。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S6：成交 (Closing)</div>
        <div class="s-line-content">
        • 核心目標：簽署合約，鋪墊轉介紹。<br>
        • 執行重點：促成行動，處理最後反對問題。
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 輸入表單 ---
with st.container():
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    
    with st.form("client_form"):
        st.markdown("<h3>📍 目前銷售階段 (S線)</h3>", unsafe_allow_html=True)
        s_stage = st.selectbox(
            "請選擇目前進度", 
            ["S1：取得名單/陌生開發", "S2：電話約訪/邀約", "S3：初步面談/建立關係", "S4：發覺需求/挖掘痛點", "S5：說明建議書/解決方案", "S6：成交締結/處理反對問題"]
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
        history = st.text_area("投保史 / 現有保障", placeholder="例：僅有公司團保...", height=100)
        
        st.markdown("---")
        st.markdown("<h3>🔍 深度分析線索</h3>", unsafe_allow_html=True)
        quotes = st.text_area("🗣️ 客戶語錄 (破冰關鍵)", placeholder="例：「我覺得保險都騙人的」...", height=100)
        target_product = st.text_area("🎯 你的銷售目標", placeholder="例：美元利變型保單...", height=80)

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 啟動 S 線 + 靈數分析")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 邏輯處理：生成策略 ---
if submitted:
    if not api_key:
        st.error("⚠️ 請輸入 API Key")
    elif not model:
        st.error("⚠️ 系統連線異常")
    else:
        # 計算生命靈數
        life_path_num = calculate_life_path_number(birthday)
        
        with st.spinner(f"🧠 正在運算：生命靈數 {life_path_num} 號人 + S線戰略..."):
            today = datetime.date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            
            final_prompt = f"""
            你是一位擁有 20 年經驗的頂尖保險業務總監，精通「S線銷售循環」與「生命靈數性格分析」。
            
            【目前的戰略位置】
            👉 **{s_stage}**
            
            【客戶關鍵密碼】
            👉 **生命靈數：{life_path_num} 號人**
            
            【資料如下】
            - 生日：{birthday} (約 {age} 歲)
            - 性別：{gender}
            - 職業：{job}
            - 興趣：{interests}
            - 年收入：{income} 萬
            - 投保史：{history}
            - 客戶說過的話："{quotes}"
            - 業務員想賣的商品：{target_product}
            
            【分析邏輯 - 請結合靈數與S線】
            1. **生命靈數分析**：請先分析 {life_path_num} 號人的核心性格、決策模式（是衝動型、分析型、還是感受型？）。
            2. **戰略融合**：針對 {life_path_num} 號人的性格，在 {s_stage} 階段，我們該用什麼語氣？該強調什麼重點？（例如：對4號人講S5建議書，要強調數據和條款安全感；對3號人要強調願景和圖像）。
            
            【請依序輸出】
            1. [客戶畫像：生命靈數 {life_path_num} 號人深度解析] (性格關鍵字、決策地雷、溝通偏好)
            2. [本階段 ({s_stage}) 戰略目標]
            3. [建議方向一] (針對此靈數的專屬切入點、話術)
            4. [建議方向二] (針對此靈數的專屬切入點、話術)
            """
            
            try:
                response = model.generate_content(final_prompt)
                st.session_state.current_strategy = response.text
                st.session_state.chat_history = []
                st.session_state.chat_history.append({"role": "assistant", "content": f"分析完成！這是一位 **{life_path_num} 號人**，針對他在 **{s_stage}** 的策略已生成。歡迎提問陪練！"})
            except Exception as e:
                st.error(f"發生錯誤：{e}")

# --- 顯示策略與陪練室 ---
if st.session_state.current_strategy:
    st.markdown(f"<h4 style='color: #ff9933; text-align: center; margin-top: 20px;'>✅ S 線 + 靈數戰略報告</h4>", unsafe_allow_html=True)
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<h3>🤖 總監陪練室 (針對上方策略提問)</h3>", unsafe_allow_html=True)

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("輸入你想問的問題... (例如：怎麼跟 4 號人談這張單？)"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("總監思考中..."):
                chat_prompt = f"""
                你現在是針對以下這份「保險策略報告」的陪練教練。
                目前階段：{st.session_state.current_strategy}裡的戰略階段。
                
                【策略報告內容】：
                {st.session_state.current_strategy}
                
                【使用者問題】：
                {prompt}
                
                【任務】：
                請針對客戶的「生命靈數性格」與「目前S線階段」回答。
                如果是要求示範話術，請給出符合該靈數聽得進去的口語化例子。
                """
                
                try:
                    response = model.generate_content(chat_prompt)
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"回覆失敗：{e}")
