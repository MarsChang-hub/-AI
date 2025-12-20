import streamlit as st
import google.generativeai as genai
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 🎨 設計大師級 UI (CSS) ---
st.markdown("""
<style>
    /* --- 1. 配色系統 (Color System) --- */
    :root {
        --bg-main: #001222;        /* 更深邃的午夜藍背景 */
        --glass-card: rgba(255, 255, 255, 0.03); /* 玻璃擬態背景 */
        --border-color: rgba(255, 153, 51, 0.3); /* 橘色微光邊框 */
        --text-orange: #ff9933;
        --btn-gradient: linear-gradient(135deg, #ff8533 0%, #cc4400 100%);
        --text-white: #f0f2f5;
        --input-bg: #ffffff;
    }

    /* --- 2. 全域重置與背景 --- */
    .stApp {
        background-color: var(--bg-main);
        background-image: radial-gradient(circle at 50% 0%, #002a4d 0%, var(--bg-main) 70%); /* 頂部聚光燈效果 */
    }
    
    /* 移除 Streamlit 預設討厭的頂部空白 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px; /* 限制最大寬度，讓大螢幕看起來不散漫 */
    }

    /* --- 3. 緊湊排版核心 (Compact Layout Core) --- */
    
    /* 縮小所有元件之間的垂直間距 */
    div[data-testid="stVerticalBlock"] {
        gap: 0.6rem !important; /* 從預設的 1rem 改為 0.6rem */
    }
    
    /* 縮小每個元件容器的邊距 */
    .stElementContainer {
        margin-bottom: 0.3rem !important;
    }

    /* --- 4. 玻璃擬態卡片 (Glassmorphism Cards) --- */
    .form-card {
        background: var(--glass-card);
        backdrop-filter: blur(10px); /* 毛玻璃效果 */
        border: 1px solid var(--border-color);
        padding: 20px 25px; /* 稍微縮減 Padding */
        border-radius: 16px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 15px;
    }
    
    .s-line-card {
        background: rgba(0, 0, 0, 0.2);
        border-left: 3px solid var(--text-orange);
        padding: 10px 15px; /* 緊湊化 */
        margin-bottom: 8px;
        border-radius: 4px;
    }

    /* --- 5. 輸入元件美化 (Input Styling) --- */
    /* 保持白底黑字以確保可讀性，但修飾細節 */
    .stTextInput input, .stDateInput input, .stTextArea textarea, 
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: var(--input-bg) !important;
        color: #000000 !important;
        border: 1px solid #ddd !important; /* 邊框細一點 */
        border-radius: 6px; /* 圓角小一點，比較專業 */
        padding: 8px 10px !important; /* 內距縮小 */
        font-size: 15px;
        min-height: 40px; /* 統一高度 */
    }
    
    /* 聚焦時的橘色光暈 */
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within {
        border-color: var(--text-orange) !important;
        box-shadow: 0 0 0 2px rgba(255, 153, 51, 0.2) !important;
    }

    /* Label 標籤美化 */
    .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label, .stRadio label {
        color: #b0c4de !important; /* 淺藍灰色，比純白更有質感 */
        font-size: 13px !important; /* 字體縮小，更精緻 */
        font-weight: 500;
        margin-bottom: 2px !important;
    }

    /* 下拉選單修復 */
    div[data-baseweb="popover"], div[data-baseweb="menu"] { background-color: #fff !important; }
    div[data-baseweb="menu"] li span { color: #000 !important; }
    div[data-baseweb="menu"] li:hover { background-color: #fff5e6 !important; }

    /* --- 6. 按鈕大師級設計 --- */
    .stButton > button {
        width: 100%;
        background: var(--btn-gradient);
        color: white !important;
        border: none;
        padding: 12px 0; /* 高度縮小一點 */
        font-size: 16px;
        font-weight: 600;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(255, 102, 0, 0.2);
        transition: all 0.3s ease;
        letter-spacing: 1px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 102, 0, 0.4);
    }

    /* --- 7. 報告與對話框 --- */
    .report-box {
        background-color: #fff !important; /* 報告區改為白底，模仿紙張質感，閱讀體驗最好 */
        color: #1a1a1a !important;
        padding: 30px;
        border-radius: 8px;
        border-top: 5px solid var(--text-orange);
        font-family: "Microsoft JhengHei", sans-serif;
        line-height: 1.7;
        font-size: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin-top: 10px;
        margin-bottom: 20px;
    }
    
    /* 對話框 */
    .stChatMessage {
        background-color: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    .stChatMessage p { color: #fff !important; }

    /* --- 8. 文字排版 --- */
    h1 {
        color: var(--text-orange) !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 5px !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    h3 {
        color: var(--text-white) !important;
        font-size: 16px !important;
        border-left: 3px solid var(--text-orange);
        padding-left: 10px;
        margin-top: 10px !important;
        margin-bottom: 10px !important;
    }
    p, li { color: #ccc; font-size: 14px; }
    
    /* Mars Watermark */
    .mars-watermark {
        position: fixed;
        top: 20px;
        right: 30px;
        color: rgba(255, 153, 51, 0.7);
        font-size: 12px;
        font-weight: 600;
        font-family: 'Helvetica Neue', sans-serif;
        letter-spacing: 2px;
        z-index: 9999;
        pointer-events: none;
        text-transform: uppercase;
        border: 1px solid rgba(255, 153, 51, 0.3);
        padding: 5px 10px;
        border-radius: 20px;
    }

    /* Hide standard Streamlit clutter */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Expander 調整 */
    .streamlit-expanderHeader {
        background-color: rgba(255,255,255,0.05) !important;
        color: #fff !important;
        font-size: 14px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 6px;
    }
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

# --- API Key ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    with st.sidebar:
        st.markdown(f"<h3 style='color: #ff9933; border:none;'>⚙️ 系統設定</h3>", unsafe_allow_html=True)
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

# --- 主畫面標題區 (置中且緊湊) ---
col_t1, col_t2, col_t3 = st.columns([1, 6, 1])
with col_t2:
    st.markdown("<h1 style='text-align: center;'>保險業務超級軍師</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 13px; color: #8899a6; margin-bottom: 10px;'>AI 賦能．顧問式銷售．精準健診</p>", unsafe_allow_html=True)

# --- S線銷售戰略指南 (使用 Expander 收合) ---
with st.expander("📖 S線顧問式銷售詳解 (核心心法)"):
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("""
        <div class="s-line-card"><b>S1 名單</b>：定聯、分類 (強/弱/無)、300顆種子。</div>
        <div class="s-line-card"><b>S2 約訪</b>：賣見面不賣產品。配合時間、求回饋。</div>
        <div class="s-line-card"><b>S3 面談</b>：Rapport、4切點、過橋。</div>
        """, unsafe_allow_html=True)
    with col_s2:
        st.markdown("""
        <div class="s-line-card"><b>S4 需求</b>：Find -> Confirm -> Expand (痛點擴大)。</div>
        <div class="s-line-card"><b>S5 建議</b>：保險生活化。比喻 (度假/瑪麗亞/現金企業)。</div>
        <div class="s-line-card"><b>S6 成交</b>：選擇題促成、轉介紹 (回S1)。</div>
        """, unsafe_allow_html=True)

# --- 輸入表單 (使用玻璃擬態卡片包裹) ---
st.markdown('<div class="form-card">', unsafe_allow_html=True)
with st.form("client_form"):
    # 第一排：姓名 + 階段 (最重要資訊)
    c1, c2 = st.columns([1, 2])
    with c1:
        client_name = st.text_input("客戶姓名", placeholder="王小明")
    with c2:
        s_stage = st.selectbox("📍 銷售階段 (S線)", 
            ["S1：取得名單 (定聯/分類)", "S2：約訪 (賣見面價值)", "S3：初步面談 (4切點/Rapport)", "S4：發覺需求 (擴大痛點)", "S5：說明建議書 (保險生活化)", "S6：成交 (促成/轉介紹)"])

    # 第二排：個資 (3欄更緊湊)
    c3, c4, c5 = st.columns(3)
    with c3:
        gender = st.radio("性別", ["男", "女"], horizontal=True)
    with c4:
        birthday = st.date_input("生日", min_value=datetime.date(1950, 1, 1), value=datetime.date(1990, 1, 1))
    with c5:
        income = st.text_input("年收 (萬)", placeholder="100")

    # 第三排：職業與興趣
    c6, c7 = st.columns(2)
    with c6:
        job = st.text_input("職業 / 職位", placeholder="例：竹科工程師")
    with c7:
        interests = st.text_input("興趣 / 休閒", placeholder="例：登山、美股")

    st.markdown("<h3>🛡️ 保障盤點與分析</h3>", unsafe_allow_html=True)
    
    # 保障細項 (使用 Expander 保持介面乾淨)
    with st.expander("➕ 詳細保障額度 (點擊展開填寫)", expanded=True):
        st.markdown("<p style='font-size:12px; color:#aaa; margin-bottom:10px;'>※ 請輸入數字 (單位已預設)</p>", unsafe_allow_html=True)
        g1, g2, g3 = st.columns(3)
        with g1:
            cov_daily = st.text_input("住院日額", placeholder="標準:4000")
            cov_med_reim = st.text_input("醫療實支 (萬)", placeholder="標準:20")
            cov_surg = st.text_input("定額手術", placeholder="標準:1000")
            cov_acc_reim = st.text_input("意外實支 (萬)", placeholder="標準:10")
        with g2:
            cov_cancer = st.text_input("癌症一次金 (萬)", placeholder="標準:50")
            cov_major = st.text_input("重大傷病 (萬)", placeholder="標準:30")
            cov_radio = st.text_input("放療/次", placeholder="標準:6000")
            cov_chemo = st.text_input("化療/次", placeholder="標準:6000")
        with g3:
            cov_ltc = st.text_input("長照月給付", placeholder="標準:3萬")
            cov_dis = st.text_input("失能月給付", placeholder="標準:3萬")
            cov_life = st.text_input("壽險 (萬)", placeholder="標準:5倍年薪")
            
    history_note = st.text_area("投保史備註 / 其他狀況", placeholder="例：僅有團保，覺得保費貴...", height=68)
    
    # 第四排：語錄與目標
    c8, c9 = st.columns(2)
    with c8:
        quotes = st.text_area("🗣️ 客戶語錄", placeholder="破冰關鍵句...", height=68)
    with c9:
        target_product = st.text_area("🎯 銷售目標", placeholder="想賣什麼商品...", height=68)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    submitted = st.form_submit_button("🚀 啟動教練分析")

st.markdown('</div>', unsafe_allow_html=True)

# --- 邏輯處理 ---
if submitted:
    if not api_key:
        st.error("⚠️ 請輸入 API Key")
    elif not model:
        st.error("⚠️ 系統連線異常")
    else:
        life_path_num = calculate_life_path_number(birthday)
        display_name = client_name if client_name else "客戶"
        
        try:
            income_val = float(income) if income else 0
            life_ins_standard = int(income_val * 5)
        except:
            life_ins_standard = "無法計算"

        with st.spinner(f"🧠 教練 Mars 正在為【{display_name}】進行診斷..."):
            today = datetime.date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            
            detailed_coverage = f"""
            【詳細保障額度盤點】
            - 住院日額：{cov_daily if cov_daily else '0'} (標準: 4000)
            - 醫療實支：{cov_med_reim if cov_med_reim else '0'} 萬 (標準: 20萬)
            - 定額手術：{cov_surg if cov_surg else '0'} (標準: 1000)
            - 意外實支：{cov_acc_reim if cov_acc_reim else '0'} 萬 (標準: 10萬)
            - 癌症一次金：{cov_cancer if cov_cancer else '0'} 萬 (標準: 50萬)
            - 重大傷病：{cov_major if cov_major else '0'} 萬 (標準: 30萬)
            - 放療/次：{cov_radio if cov_radio else '0'} (標準: 6000)
            - 化療/次：{cov_chemo if cov_chemo else '0'} (標準: 6000)
            - 長照月給付：{cov_ltc if cov_ltc else '0'} (標準: 3萬)
            - 失能月給付：{cov_dis if cov_dis else '0'} (標準: 3萬)
            - 壽險：{cov_life if cov_life else '0'} 萬 (標準: 5年年薪)
            【備註】{history_note}
            """
            
            final_prompt = f"""
            你現在是「教練 (Coach) Mars Chang」。請嚴格遵守「顧問式銷售」邏輯與「Mars Chang 保障標準」。
            
            【戰略位置】{s_stage}
            【客戶】{display_name}, {life_path_num} 號人, {age}歲, {job}, 年收{income}萬
            【語錄】"{quotes}"
            【目標】{target_product}
            {detailed_coverage}
            
            【S線顧問式銷售核心】
            S1:定聯/連結強度。S2:賣見面/求回饋。S3:4切點/Rapport。
            S4:Find/Confirm/Expand(痛點擴大)。S5:保險生活化(比喻)。S6:選擇題/轉介紹。

            【Mars Chang 缺口審查標準 (低於標準請警示)】
            1.住院日額:4000(單人房)。2.醫療實支:20萬(達文西)。3.定額手術:1000。
            4.意外實支:10萬(鈦合金)。5.癌/重:50/30萬(預備金)。6.放化療:6000/次。
            7.長照失能:3萬(外勞)。8.壽險:5倍年薪。

            【輸出】
            1. [客戶畫像] ({life_path_num}號人性格+風險)
            2. [保障缺口診斷] (嚴格比對標準)
            3. [本階段戰略] (引用S線心法)
            4. [建議方向一] (話術+切入)
            5. [建議方向二] (話術+切入)
            """
            
            try:
                response = model.generate_content(final_prompt)
                st.session_state.current_strategy = response.text
                st.session_state.chat_history = []
                st.session_state.chat_history.append({"role": "assistant", "content": f"我是教練 Mars。已針對 **{display_name}** 完成分析。報告如下："})
            except Exception as e:
                st.error(f"發生錯誤：{e}")

# --- 結果顯示 ---
if st.session_state.current_strategy:
    st.markdown("---")
    st.markdown(f"<h3 style='text-align: center; border:none;'>✅ 教練戰略報告</h3>", unsafe_allow_html=True)
    
    with st.expander("📝 複製完整報告 (純文字版)"):
        st.code(st.session_state.current_strategy, language="markdown")
    
    # 報告區塊改用白底黑字，確保閱讀體驗
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("<h3 style='border:none; margin-top:30px;'>🤖 教練陪練室</h3>", unsafe_allow_html=True)

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("輸入問題... (例如：這個缺口怎麼講更順？)"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("教練思考中..."):
                chat_prompt = f"""
                你是 Coach Mars Chang。依據報告回答新人問題。
                報告：{st.session_state.current_strategy}
                問題：{prompt}
                任務：人性化指導，若問S5請用比喻，若問缺口請強調 Mars 標準。
                """
                try:
                    response = model.generate_content(chat_prompt)
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                    with st.expander("📝 複製回覆"):
                        st.code(response.text, language="markdown")
                except Exception as e:
                    st.error(f"回覆失敗：{e}")
