import streamlit as st
import google.generativeai as genai
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 🎨 專業深色配色 UI 設計 (CSS) ---
st.markdown("""
<style>
    /* 定義更深沉的專業配色 */
    :root {
        --primary-blue: #002244;  /* 極深午夜藍 (主色) */
        --primary-orange: #CC4400; /* 深磚橘色 (強調色) */
        --bg-color: #f0f2f6;       /* 背景色 */
    }

    /* 1. 全域背景設定 */
    .stApp {
        background-color: var(--bg-color);
    }
    
    /* 2. 調整頂部間距，避免跑版 */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 5rem;
    }

    /* 3. 輸入框優化：加深邊框顏色，讓它在手機上更明顯 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        border: 2px solid #b0b8c4 !important; /* 加粗邊框 */
        border-radius: 10px;
        padding: 12px;
        font-size: 16px;
        color: #000000 !important; /* 強制輸入文字為純黑 */
        box-shadow: none;
    }
    /* 聚焦時的效果 */
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within, .stDateInput input:focus, .stTextArea textarea:focus {
        border-color: var(--primary-orange) !important;
        box-shadow: 0 0 0 1px var(--primary-orange) !important;
    }

    /* 4. 按鈕優化：深藍底 + 深橘懸浮 */
    .stButton > button {
        width: 100%;
        background-color: var(--primary-blue) !important;
        color: white !important;
        border: none;
        padding: 16px 0;
        font-size: 18px;
        font-weight: 800; /* 特粗體 */
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: var(--primary-orange) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(204, 68, 0, 0.3);
    }

    /* 5. 報告輸出框：高對比配色 */
    .report-box {
        background-color: #ffffff !important;
        color: #000000 !important; /* 強制純黑字 */
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #d1d5db;
        border-left: 8px solid var(--primary-blue); /* 左側深藍條 */
        font-family: "Microsoft JhengHei", sans-serif;
        line-height: 1.8;
        font-size: 16px;
        white-space: pre-wrap;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    
    /* 6. 表單卡片容器 */
    .form-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-top: 5px solid var(--primary-blue); /* 頂部深藍條 */
        margin-bottom: 20px;
    }

    /* 7. 標題強制修正 (解決看不見的問題) */
    h1 {
        color: #002244 !important; /* 強制深藍色 */
        font-size: 2rem !important;
        font-weight: 900 !important;
        text-align: center;
        margin-bottom: 0.5rem;
        opacity: 1 !important; /* 確保不透明 */
    }
    
    h3 {
        color: #002244 !important;
        font-weight: 700 !important;
        font-size: 1.3rem !important;
        margin-top: 0 !important;
    }
    
    p {
        color: #333333 !important; /* 副標題深灰色 */
    }
    
    /* 隱藏預設元件 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 核心邏輯 ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    with st.sidebar:
        st.markdown(f"<h3 style='color: #002244;'>⚙️ 系統設定</h3>", unsafe_allow_html=True)
        api_key = st.text_input("請輸入 Google API Key", type="password")

# --- 連線模型 ---
model = None
if api_key:
    genai.configure(api_key=api_key)
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if available_models:
            selected_model_name = next((m for m in available_models if 'flash' in m), None)
            if not selected_model_name:
                selected_model_name = next((m for m in available_models if 'pro' in m), available_models[0])
            model = genai.GenerativeModel(selected_model_name)
    except Exception as e:
        st.error(f"連線失敗：{e}")

# --- 主畫面設計 ---

st.markdown("<h1>保險業務超級軍師</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px; margin-bottom: 25px; font-weight: 500;'>AI 賦能．精準開發．專業領航</p>", unsafe_allow_html=True)

# 表單卡片區域
with st.container():
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    
    with st.form("client_form"):
        st.markdown("<h3>📋 客戶基本輪廓</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            gender = st.selectbox("性別", ["男", "女"])
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
        # 移除 KGI 字樣，改用中性文字
        submitted = st.form_submit_button("🚀 啟動雙軌戰略分析")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 生成結果 ---
if submitted:
    if not api_key:
        st.error("⚠️ 請輸入 API Key")
    elif not model:
        st.error("⚠️ 系統連線異常")
    else:
        with st.spinner("🧠 總監正在分析客戶心理..."):
            today = datetime.date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            
            # Prompt 移除公司名稱，保持中性專業
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
                st.markdown(f"<h4 style='color: #CC4400; text-align: center; margin-top: 20px;'>✅ 分析完成！策略報告如下</h4>", unsafe_allow_html=True)
                st.markdown(f'<div class="report-box">{response.text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"發生錯誤：{e}")
