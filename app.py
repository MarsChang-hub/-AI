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
    
    /* --- NEW: Mars 商標浮水印樣式 --- */
    .mars-watermark {
        position: fixed; /* 固定定位，釘在螢幕上 */
        top: 15px;       /* 距離頂部 */
        right: 25px;     /* 距離右側 */
        color: var(--text-orange); /* 使用主題橘色 */
        font-size: 14px;
        font-weight: 600;
        z-index: 9999;   /* 保證在最上層 */
        font-family: 'Montserrat', sans-serif; /* 選個有質感的英文字體 */
        letter-spacing: 1px; /* 增加字距，提升高級感 */
        opacity: 0.8;    /* 稍微透明，不要太搶戲 */
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5); /* 加一點陰影增加立體感 */
        pointer-events: none; /* 讓滑鼠可以穿透它點擊下方的東西 */
    }
    /* 手機版微調 */
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

# --- 插入 Mars 商標 (在 CSS 之後立即執行) ---
st.markdown('<div class="mars-watermark">Made by Mars</div>', unsafe_allow_html=True)


# --- 初始化 Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_strategy" not in st.session_state:
    st.session_state.current_strategy = None

# --- 工具函數：計算生命靈數 ---
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

# --- 主畫面標題 ---
st.markdown("<h1>保險業務超級軍師</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 15px; margin-bottom: 15px;'>AI 賦能．S線戰略．結構化健診</p>", unsafe_allow_html=True)

# --- S線銷售戰略指南 (收合選單) ---
with st.expander("📖 點擊查看：S線銷售循環詳解 (S1~S6)"):
    st.markdown("""
    <div class="s-line-card"><div class="s-line-title">S1：取得名單</div><div class="s-line-content">建立潛在客戶資料庫，初步篩選。</div></div>
    <div class="s-line-card"><div class="s-line-title">S2：約訪</div><div class="s-line-content">賣見面價值，不賣產品，引起好奇。</div></div>
    <div class="s-line-card"><div class="s-line-title">S3：初步面談</div><div class="s-line-content">破冰，建立信任，SPIN-Situation。</div></div>
    <div class="s-line-card"><div class="s-line-title">S4：發覺需求</div><div class="s-line-content">挖掘痛點，隱性需求轉顯性 (SPIN-P/I/N)。</div></div>
    <div class="s-line-card"><div class="s-line-title">S5：說明建議書</div><div class="s-line-content">FAB 法則，證明方案解決 S4 痛點。</div></div>
    <div class="s-line-card"><div class="s-line-title">S6：成交</div><div class="s-line-content">簽約締結，處理反對問題，鋪墊轉介紹。</div></div>
    """, unsafe_allow_html=True)

# --- 輸入表單 ---
with st.container():
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    
    with st.form("client_form"):
        # 客戶姓名與階段
        col_name, col_stage = st.columns([1, 2])
        with col_name:
            client_name = st.text_input("客戶姓名", placeholder="例：王小明")
        with col_stage:
            s_stage = st.selectbox(
                "📍 目前銷售階段 (S線)", 
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
        # 保留原本的文字備註區
        history_note = st.text_area("投保史備註 (文字描述)", placeholder="例：僅有公司團保，客戶覺得保費太貴...", height=80)
        
        # 詳細保障額度
        with st.expander("➕ 點擊展開：詳細保障額度填寫 (選填)"):
            st.markdown("<p style='color:white; font-size:14px;'>※ 請輸入數字或單位 (例: 2000, 50萬)</p>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                cov_daily = st.text_input("住院日額", placeholder="例：2000")
                cov_med_reim = st.text_input("醫療實支實付", placeholder="例：15萬")
                cov_surg = st.text_input("定額手術", placeholder="例：5萬")
                cov_acc_reim = st.text_input("意外實支實付", placeholder="例：3萬")
            with c2:
                cov_cancer = st.text_input("癌症一次金", placeholder="例：100萬")
                cov_major = st.text_input("重大傷病", placeholder="例：100萬")
                cov_radio = st.text_input("放療/次", placeholder="例：5000")
                cov_chemo = st.text_input("化療/次", placeholder="例：5000")
            with c3:
                cov_ltc = st.text_input("長期照護月給付", placeholder="例：3萬")
                cov_dis = st.text_input("失能月給付", placeholder="例：3萬")
                cov_life = st.text_input("壽險", placeholder="例：500萬")

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
        
        with st.spinner(f"🧠 正在為【{display_name}】運算戰略..."):
            today = datetime.date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            
            # 組合詳細保障資料
            detailed_coverage = f"""
            【詳細保障額度盤點】
            - 住院日額：{cov_daily if cov_daily else '未填寫'}
            - 醫療實支實付：{cov_med_reim if cov_med_reim else '未填寫'}
            - 定額手術：{cov_surg if cov_surg else '未填寫'}
            - 意外實支實付：{cov_acc_reim if cov_acc_reim else '未填寫'}
            - 癌症一次金：{cov_cancer if cov_cancer else '未填寫'}
            - 重大傷病一次金：{cov_major if cov_major else '未填寫'}
            - 放療/次：{cov_radio if cov_radio else '未填寫'}
            - 化療/次：{cov_chemo if cov_chemo else '未填寫'}
            - 長期照護月給付：{cov_ltc if cov_ltc else '未填寫'}
            - 失能月給付：{cov_dis if cov_dis else '未填寫'}
            - 壽險：{cov_life if cov_life else '未填寫'}
            
            【其他備註】
            {history_note}
            """
            
            final_prompt = f"""
            你是一位擁有 20 年經驗的頂尖保險業務總監，精通「S線銷售循環」與「保單健診分析」。
            
            【目前的戰略位置】
            👉 **{s_stage}**
            
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
            
            【分析邏輯】
            1. **保單健診 (Gap Analysis)**：請根據客戶的「詳細保障額度」與「年收入/職業風險」進行比對。具體指出哪裡不足。
            2. **生命靈數結合**：針對 {life_path_num} 號人，我們該如何「包裝」這個保障缺口？
            3. **S線戰略**：在 {s_stage} 階段，如何利用這些缺口數據來推進銷售？
            4. **話術要求**：請在話術中直接稱呼客戶為「{display_name}」或「{display_name}先生/小姐」。
            
            【請依序輸出】
            1. [客戶畫像與心理分析] ({display_name}, {life_path_num} 號人)
            2. [保障缺口診斷書]
            3. [本階段 ({s_stage}) 戰略目標]
            4. [建議方向一] (含切入點、話術)
            5. [建議方向二] (含切入點、話術)
            """
            
            try:
                response = model.generate_content(final_prompt)
                st.session_state.current_strategy = response.text
                st.session_state.chat_history = []
                st.session_state.chat_history.append({"role": "assistant", "content": f"分析完成！已針對 **{display_name}** ({life_path_num} 號人) 生成戰略。歡迎提問陪練！"})
            except Exception as e:
                st.error(f"發生錯誤：{e}")

# --- 顯示策略與陪練室 ---
if st.session_state.current_strategy:
    st.markdown(f"<h4 style='color: #ff9933; text-align: center; margin-top: 20px;'>✅ 戰略與健診報告</h4>", unsafe_allow_html=True)
    
    # 一鍵複製區塊
    with st.expander("📝 點擊這裡：複製完整報告 (純文字版)"):
        st.code(st.session_state.current_strategy, language="markdown")
    
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<h3>🤖 總監陪練室 (針對上方策略提問)</h3>", unsafe_allow_html=True)

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("輸入你想問的問題..."):
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
                請針對客戶的保障缺口、生命靈數性格、S線階段回答。
                如果是回答話術，請記得使用客戶姓名。
                """
                
                try:
                    response = model.generate_content(chat_prompt)
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                    
                    # 聊天回覆複製按鈕
                    with st.expander("📝 複製這個回覆"):
                        st.code(response.text, language="markdown")
                        
                except Exception as e:
                    st.error(f"回覆失敗：{e}")
