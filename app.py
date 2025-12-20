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

    /* --- S線指南卡片樣式 (已更名) --- */
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
st.markdown("<p style='text-align: center; font-size: 15px; margin-bottom: 15px;'>AI 賦能．精準開發．陪練對談</p>", unsafe_allow_html=True)

# --- NEW: S線銷售戰略指南 (收合選單) ---
with st.expander("📖 點擊查看：S線銷售循環詳解 (S1~S6)"):
    st.markdown("""
    <div class="s-line-card">
        <div class="s-line-title">S1：取得名單 (Lead Generation)</div>
        <div class="s-line-content">
        • <b>核心目標</b>：建立潛在客戶資料庫，區分「嫌疑」與「潛在」名單。<br>
        • <b>執行重點</b>：不只蒐集名字，要初步篩選 (Qualification)。<br>
        • <b>關鍵數據</b>：名單來源、客戶輪廓、冷熱度標籤。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S2：約訪、取得約會 (Appointment Setting)</div>
        <div class="s-line-content">
        • <b>核心目標</b>：不在電話中賣產品，只賣「見面的價值」。<br>
        • <b>執行重點</b>：引起好奇心，降低防備心。<br>
        • <b>關鍵數據</b>：聯繫次數、拒絕理由、約訪結果。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S3：初步面談 (Initial Interview)</div>
        <div class="s-line-content">
        • <b>核心目標</b>：破冰，建立專業形象，蒐集「現狀背景」。<br>
        • <b>SPIN應用</b>：Situation (情境性問題)。<br>
        • <b>關鍵數據</b>：現狀盤點、人格特質 (DISC)、關鍵決策者。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S4：發覺需求 (Needs Discovery) ★最關鍵</div>
        <div class="s-line-content">
        • <b>核心目標</b>：將「隱性需求」轉化為「顯性需求」。<br>
        • <b>SPIN應用</b>：Problem (難點)、Implication (隱喻)、Need-payoff (解決)。<br>
        • <b>關鍵數據</b>：核心痛點、預算範圍、急迫性、競爭對手。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S5：說明建議書 (Proposal Presentation)</div>
        <div class="s-line-content">
        • <b>核心目標</b>：運用 FAB 法則，證明方案能解決 S4 的痛點。<br>
        • <b>執行重點</b>：不堆疊功能，只講「針對痛點」的方案。<br>
        • <b>關鍵數據</b>：提案內容、反對問題 (Objections)、成交機率。
        </div>
    </div>
    <div class="s-line-card">
        <div class="s-line-title">S6：成交 (Closing)</div>
        <div class="s-line-content">
        • <b>核心目標</b>：簽署合約，鋪墊未來的「轉介紹」。<br>
        • <b>執行重點</b>：促成行動，確認細節。<br>
        • <b>關鍵數據</b>：成交金額、循環天數、(失敗需做屍檢分析)。
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 輸入表單 ---
with st.container():
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    
    with st.form("client_form"):
        # 加入階段選擇 (S線)
        st.markdown("<h3>📍 目前銷售階段 (S線位置)</h3>", unsafe_allow_html=True)
        s_stage = st.selectbox(
            "請選擇目前進度 (AI 將根據此階段給予精準建議)", 
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
        submitted = st.form_submit_button("🚀 啟動 S 線戰略分析")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 邏輯處理：生成策略 ---
if submitted:
    if not api_key:
        st.error("⚠️ 請輸入 API Key")
    elif not model:
        st.error("⚠️ 系統連線異常")
    else:
        with st.spinner(f"🧠 總監正在針對【{s_stage}】進行戰略佈局..."):
            today = datetime.date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            
            # 將 S 線邏輯寫入 Prompt
            final_prompt = f"""
            你是一位擁有 20 年經驗的頂尖保險業務總監，精通「S線銷售循環 (S1~S6)」。
            
            【目前的戰略位置】
            👉 **{s_stage}**
            (請根據此階段的核心目標，給予最精準的指導，不要講下一階段的事，專注突破當下瓶頸)
            
            【S線階段定義參考】
            S1: 建立名單，區分嫌疑/潛在。
            S2: 賣見面價值，不賣產品，降低防備。
            S3: 破冰，建立信任，蒐集背景 (SPIN-Situation)。
            S4: 挖掘隱性需求轉顯性 (SPIN-Problem/Implication/Need-payoff)。
            S5: 提出 FAB 解決方案，針對痛點。
            S6: 締結，處理反對問題，鋪墊轉介紹。

            【客戶資料】
            - 生日：{birthday} (約 {age} 歲)
            - 性別：{gender}
            - 職業：{job}
            - 興趣：{interests}
            - 年收入：{income} 萬
            - 投保史：{history}
            - 客戶說過的話："{quotes}"
            - 業務員想賣的商品：{target_product}
            
            【請依序輸出】
            1. [客戶畫像與心理分析] (請特別分析他在 {s_stage} 階段的心理防線)
            2. [本階段戰略目標] (簡單說明在 {s_stage} 我們要達成什麼)
            3. [建議方向一] (含切入點、話術、下一步行動)
            4. [建議方向二] (含切入點、話術、下一步行動)
            """
            
            try:
                response = model.generate_content(final_prompt)
                st.session_state.current_strategy = response.text
                st.session_state.chat_history = []
                st.session_state.chat_history.append({"role": "assistant", "content": f"針對【{s_stage}】的策略已生成！如果遇到卡關，請在下面隨時問我！"})
            except Exception as e:
                st.error(f"發生錯誤：{e}")

# --- 顯示策略與陪練室 ---
if st.session_state.current_strategy:
    st.markdown(f"<h4 style='color: #ff9933; text-align: center; margin-top: 20px;'>✅ S 線戰略報告</h4>", unsafe_allow_html=True)
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<h3>🤖 總監陪練室 (針對上方策略提問)</h3>", unsafe_allow_html=True)

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("輸入你想問的問題... (例如：S2電話被掛怎麼辦？)"):
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
                請針對目前 S 線階段 ({s_stage}) 回答。
                如果是要求示範話術，請給出具體、口語化的例子。
                """
                
                try:
                    response = model.generate_content(chat_prompt)
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"回覆失敗：{e}")
