import streamlit as st
import google.generativeai as genai
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 🎨 深藍專業版 UI (CSS) ---
st.markdown("""
<style>
    /* --- 1. 配色系統 (回歸深藍) --- */
    :root {
        --bg-main: #001222;        /* 極深午夜藍 */
        --glass-card: rgba(255, 255, 255, 0.05); /* 玻璃質感卡片 */
        --text-orange: #ff9933;    /* 橘色高亮 */
        --text-body: #e0e0e0;      /* 亮銀色文字 */
        --btn-gradient: linear-gradient(135deg, #ff8533 0%, #cc4400 100%);
    }

    /* --- 2. 全域設定 --- */
    .stApp {
        background-color: var(--bg-main);
    }
    
    /* 讓深色背景上的文字變亮 */
    p, li, span, div {
        color: var(--text-body);
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px;
    }

    /* --- 3. 輸入元件絕對顯色 (白底黑字) --- */
    /* 這是解決「看不到字」的最關鍵設定 */
    .stTextInput input, .stDateInput input, .stTextArea textarea, 
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important; /* 絕對白底 */
        color: #000000 !important;            /* 絕對黑字 */
        border: 1px solid #ff9933 !important; /* 橘色邊框 */
        border-radius: 6px;
    }

    /* 標籤文字 (Label) */
    .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label, .stRadio label {
        color: #ffffff !important;
        font-size: 14px !important;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* --- 4. 下拉選單強制修復 (防止變黑) --- */
    div[data-baseweb="popover"], div[data-baseweb="menu"] {
        background-color: #ffffff !important;
    }
    div[data-baseweb="popover"] div, div[data-baseweb="menu"] div,
    div[data-baseweb="popover"] span, div[data-baseweb="menu"] span,
    div[data-baseweb="popover"] li, div[data-baseweb="menu"] li {
        color: #000000 !important; /* 選項文字強制黑 */
    }
    div[data-baseweb="menu"] li:hover, div[data-baseweb="menu"] li[aria-selected="true"] {
        background-color: #ffcc99 !important; /* 選中時變淺橘 */
    }

    /* --- 5. 報告框 (白紙黑字，最易讀) --- */
    .report-box {
        background-color: #ffffff !important;
        color: #000000 !important;
        padding: 30px;
        border-radius: 8px;
        border-top: 6px solid var(--text-orange);
        font-family: "Microsoft JhengHei", "Segoe UI", sans-serif;
        line-height: 1.8;
        font-size: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin-top: 15px;
    }
    /* 強制報告框內文字為黑色 */
    .report-box p, .report-box li, .report-box strong, .report-box span, .report-box table {
        color: #000000 !important; 
    }

    /* --- 6. 對話視窗 --- */
    .stChatMessage {
        background-color: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }
    .stChatMessage p, .stChatMessage div { 
        color: #ffffff !important;
    }

    /* --- 7. 其他元件 --- */
    .form-card {
        background: var(--glass-card);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    
    .s-line-card {
        background: rgba(0,0,0,0.3);
        border-left: 3px solid var(--text-orange);
        padding: 10px;
        margin-bottom: 5px;
    }
    .s-line-highlight { color: #fff !important; font-weight: bold; }

    .stButton > button {
        background: var(--btn-gradient);
        color: white !important;
        border: none;
        font-weight: bold;
        letter-spacing: 1px;
        padding: 12px 0;
        border-radius: 8px;
    }
    
    h1, h2, h3 { color: var(--text-orange) !important; }

    /* Mars Watermark */
    .mars-watermark {
        position: fixed; top: 15px; right: 25px;
        color: rgba(255, 153, 51, 0.9);
        font-size: 14px; font-weight: 700;
        z-index: 9999; pointer-events: none;
        font-family: 'Montserrat', sans-serif;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    }

    #MainMenu, footer, header {visibility: hidden;}
    
    /* Expander 優化 */
    .streamlit-expanderHeader {
        color: #ffffff !important;
        font-weight: bold;
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
        st.markdown(f"<h3 style='border:none;'>⚙️ 系統設定</h3>", unsafe_allow_html=True)
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
col_t1, col_t2, col_t3 = st.columns([1, 6, 1])
with col_t2:
    st.markdown("<h1 style='text-align: center;'>保險業務超級軍師</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #bbb; margin-bottom: 10px;'>AI 賦能．顧問式銷售．精準健診</p>", unsafe_allow_html=True)

# --- S線指南 ---
with st.expander("📖 S線顧問式銷售詳解 (核心心法)"):
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("""
        <div class="s-line-card"><b>S1 名單</b>：定聯、分類 (強/弱/無)。</div>
        <div class="s-line-card"><b>S2 約訪</b>：賣見面不賣產品。</div>
        <div class="s-line-card"><b>S3 面談</b>：Rapport、4切點、過橋。</div>
        """, unsafe_allow_html=True)
    with col_s2:
        st.markdown("""
        <div class="s-line-card"><b>S4 需求</b>：Find -> Confirm -> Expand。</div>
        <div class="s-line-card"><b>S5 建議</b>：保險生活化 (比喻)。</div>
        <div class="s-line-card"><b>S6 成交</b>：選擇題促成、轉介紹。</div>
        """, unsafe_allow_html=True)

# --- 輸入表單 ---
st.markdown('<div class="form-card">', unsafe_allow_html=True)
with st.form("client_form"):
    c1, c2 = st.columns([1, 2])
    with c1:
        client_name = st.text_input("客戶姓名", placeholder="王小明")
    with c2:
        s_stage = st.selectbox("📍 銷售階段 (S線)", 
            ["S1：取得名單 (定聯/分類)", "S2：約訪 (賣見面價值)", "S3：初步面談 (4切點/Rapport)", "S4：發覺需求 (擴大痛點)", "S5：說明建議書 (保險生活化)", "S6：成交 (促成/轉介紹)"])

    c3, c4, c5 = st.columns(3)
    with c3:
        gender = st.radio("性別", ["男", "女"], horizontal=True)
    with c4:
        birthday = st.date_input("生日", min_value=datetime.date(1950, 1, 1), value=datetime.date(1990, 1, 1))
    with c5:
        income = st.text_input("年收 (萬)", placeholder="100")

    c6, c7 = st.columns(2)
    with c6:
        job = st.text_input("職業 / 職位", placeholder="例：竹科工程師")
    with c7:
        interests = st.text_input("興趣 / 休閒", placeholder="例：登山、美股")

    st.markdown("<h3 style='margin-top:15px;'>🛡️ 保障盤點與分析</h3>", unsafe_allow_html=True)
    
    with st.expander("➕ 詳細保障額度 (點擊展開填寫)", expanded=True):
        st.markdown("<p style='font-size:13px; color:#ffcc80;'>※ 請輸入數字 (單位已預設)</p>", unsafe_allow_html=True)
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
            
            # --- 智慧判斷邏輯 ---
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
            - 放療/次：{cov_radio if cov_radio else '0'} (標準: 6000)
            - 化療/次：{cov_chemo if cov_chemo else '0'} (標準: 6000)
            - 長照月給付：{cov_ltc if cov_ltc else '0'} (標準: 3萬)
            - 失能月給付：{cov_dis if cov_dis else '0'} (標準: 3萬)
            - 壽險：{cov_life if cov_life else '0'} 萬 (標準: 5年年薪)
            【備註】{history_note}
            """
            
            output_requirements = """
            1. **[客戶畫像與心理分析]**：({life_path_num}號人性格+風險)
            """
            
            if show_gap_analysis:
                output_requirements += """
            2. **[保障額度健康度檢核表]**
            (請製作一個表格，列出：項目 | 目前額度 | Mars標準 | 狀態(✅/❌))
                """
            
            output_requirements += f"""
            3. **[戰略目標 ({s_stage})]**
            (引用S線心法，例如S2就是賣見面)
            4. **[建議方向一]** (話術+切入)
            5. **[建議方向二]** (話術+切入)
            """
            
            if show_gap_analysis:
                output_requirements += """
            6. **[⚠️ 缺口風險與嚴重性分析]**
            (請將所有未達標的項目，在此處集中說明原因與後果。例如：為什麼醫療實支少於20萬很危險？因為達文西手術...等。請用強烈、專業的口吻說明，作為報告的壓軸警示。)
                """

            final_prompt = f"""
            你現在是「教練 (Coach) Mars Chang」。請嚴格遵守「顧問式銷售」邏輯。
            
            【戰略位置】{s_stage}
            【客戶】{display_name}, {life_path_num} 號人, {age}歲, {job}, 年收{income}萬
            【語錄】"{quotes}"
            【目標】{target_product}
            {detailed_coverage}
            
            【Mars Chang 缺口審查標準】
            1.住院日額:4000(單人房)。2.醫療實支:20萬(達文西)。3.定額手術:1000。
            4.意外實支:10萬(鈦合金)。5.癌/重:50/30萬(預備金)。6.放化療:6000/次。
            7.長照失能:3萬(外勞)。8.壽險:5倍年薪。

            【輸出要求 - 請依序輸出】
            {output_requirements}
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
    
    st.markdown(f'<div class="report-box">{st.session_state.current_strategy}</div>', unsafe_allow_html=True)
    
    st.markdown("<h3 style='border:none; margin-top:30px;'>🤖 教練陪練室</h3>", unsafe_allow_html=True)

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("輸入問題..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("教練思考中..."):
                chat_prompt = f"""
                你是 Coach Mars Chang。
                報告：{st.session_state.current_strategy}
                問題：{prompt}
                任務：人性化指導，若問缺口請強調 Mars 標準。
                """
                try:
                    response = model.generate_content(chat_prompt)
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                    with st.expander("📝 複製回覆"):
                        st.code(response.text, language="markdown")
                except Exception as e:
                    st.error(f"回覆失敗：{e}")
