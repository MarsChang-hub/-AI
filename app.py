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

    /* 輸入框強制白底黑字 */
    .stTextInput input, .stDateInput input, .stTextArea textarea, 
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid var(--text-orange) !important;
        border-radius: 8px;
    }

    /* 強制下拉選單顯色 */
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

    /* 標籤顏色 */
    .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label, .stRadio label {
        color: var(--text-white) !important;
        font-size: 15px;
    }

    /* 按鈕 */
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

    /* 報告框 */
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
    
    /* 卡片容器 */
    .form-card {
        background-color: var(--card-blue);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #004080;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }

    /* 對話框樣式優化 */
    .stChatMessage {
        background-color: var(--card-blue);
        border: 1px solid #004080;
        border-radius: 10px;
    }
    
    /* 聊天輸入框優化 */
    .stChatInput textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* 標題設定 */
    h1, h2, h3 {
        color: var(--text-orange) !important;
    }
    p { color: #cccccc !important; }
    
    /* 隱藏預設元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 初始化 Session State (狀態記憶) ---
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

# --- 主畫面 ---
st.markdown("<h1>保險業務超級軍師</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 15px; margin-bottom: 25px;'>AI 賦能．精準開發．陪練對談</p>", unsafe_allow_html=True)

# --- 輸入表單 ---
with st.container():
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    
    with st.form("client_form"):
        st.markdown("<h3>📋 客戶基本輪廓</h3>", unsafe_allow_html=True)
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
        submitted = st.form_submit_button("🚀 啟動雙軌戰略分析")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 邏輯處理：生成策略 ---
if submitted:
    if not api_key:
        st.error("⚠️ 請輸入 API Key")
    elif not model:
        st.error("⚠️ 系統連線異常")
    else:
        with st.spinner("🧠 總監正在分析客戶心理..."):
            today = datetime.date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            
            final_prompt = f"""
            你是一位擁有 20 年經驗的頂尖保險業務總監。
            
            【你的任務】
            根據以下客戶資料，產出專業且具備溫度的雙軌開發策略。
            
            【資料如下】
            - 生日：{birthday} (約 {age} 歲)
            - 性別：{gender}
            - 職業：{job}
            - 興趣：{interests}
            - 年收入：{income} 萬
            - 投保史：{history}
            - 客戶說過的話："{quotes}"
            - 業務員想賣的商品：{target_product}
            
            【分析邏輯】
            1. 從「客戶說過的話」分析潛在擔憂。
            2. 提供兩個截然不同的切入方向。
            3. 保持版面乾淨，重點清晰，語氣專業且有溫度。
            
            【請依序輸出】
            1. [客戶畫像與心理分析]
            2. [建議方向一] (含切入點、險種、話術)
            3. [建議方向二] (含切入點、險種、話術)
            """
            
            try:
                response = model.generate_content(final_prompt)
                # 將結果存入 Session State，這樣才不會消失
                st.session_state.current_strategy = response.text
                # 清空舊的聊天紀錄，因為換新客戶了
                st.session_state.chat_history = []
                st.session_state.chat_history.append({"role": "assistant", "content": "策略已生成！對這份策略有任何疑問，或想練習話術，都可以直接在下方問我喔！"})
            except Exception as e:
                st.error(f"發生錯誤：{e}")

# --- 顯示策略與陪練室 ---
if st.session_state.current_strategy:
    st.markdown(f"<h4 style='color: #ff9933; text-align: center; margin-top: 20px;'>✅ 策略報告</h4>", unsafe_allow_html=True)
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<h3>🤖 總監陪練室 (針對上方策略提問)</h3>", unsafe_allow_html=True)

    # 顯示歷史對話
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 聊天輸入框
    if prompt := st.chat_input("輸入你想問的問題... (例如：這句話怎麼講更順？)"):
        # 1. 顯示使用者輸入
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. AI 回覆
        with st.chat_message("assistant"):
            with st.spinner("總監思考中..."):
                # 組合 Context：策略內容 + 使用者問題
                chat_prompt = f"""
                你現在是針對以下這份「保險策略報告」的陪練教練。
                
                【策略報告內容】：
                {st.session_state.current_strategy}
                
                【使用者(新人業務)的問題】：
                {prompt}
                
                【你的任務】：
                請針對上述策略報告的內容，回答新人的問題。
                如果是要求示範話術，請給出具體、口語化的例子。
                如果是看不懂策略，請用白話文解釋。
                """
                
                try:
                    response = model.generate_content(chat_prompt)
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"回覆失敗：{e}")
