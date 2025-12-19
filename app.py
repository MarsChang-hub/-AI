import streamlit as st
import google.generativeai as genai
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 🎨 深藍 + 橘色 高對比 UI (CSS) ---
st.markdown("""
<style>
    /* 定義配色變數 */
    :root {
        --bg-deep-blue: #001a33;   /* 極深藍背景 */
        --card-blue: #002b4d;      /* 卡片深藍色 */
        --text-orange: #ff9933;    /* 亮橘色文字/邊框 */
        --btn-orange: #ff6600;     /* 按鈕深橘色 */
        --text-white: #ffffff;     /* 一般文字白 */
    }

    /* 1. 網頁全域背景：深藍色 */
    .stApp {
        background-color: var(--bg-deep-blue);
    }
    
    /* 2. 調整頂部間距 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
    }

    /* 3. 【關鍵修復】輸入框優化：強制白底黑字 */
    /* 為了解決手機下拉選單看不到字的問題，輸入框必須是亮色底 */
    .stTextInput input, 
    .stSelectbox div[data-baseweb="select"] > div, 
    .stDateInput input, 
    .stTextArea textarea {
        background-color: #ffffff !important; /* 強制白底 */
        color: #000000 !important;            /* 強制黑字 */
        border: 2px solid var(--text-orange) !important; /* 橘色邊框 */
        border-radius: 8px;
        padding: 10px;
        font-size: 16px;
    }
    
    /* 輸入框內的標籤 (Label) 顏色：改成白色或淺橘，才看得到 */
    .stTextInput label, .stSelectbox label, .stDateInput label, .stTextArea label {
        color: var(--text-white) !important;
        font-size: 15px;
    }
    
    /* 下拉選單的箭頭顏色 */
    .stSelectbox svg {
        fill: #000000 !important;
    }

    /* 4. 按鈕優化：橘色背景 + 白字 */
    .stButton > button {
        width: 100%;
        background: linear-gradient(to bottom, #ff8533, var(--btn-orange)); /* 橘色漸層 */
        color: white !important;
        border: none;
        padding: 16px 0;
        font-size: 18px;
        font-weight: 800;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(255, 102, 0, 0.3); /* 橘色發光陰影 */
        margin-top: 10px;
    }
    .stButton > button:hover {
        background: #ff471a !important; /* 滑鼠移過去變紅橘色 */
        transform: translateY(-2px);
    }

    /* 5. 報告輸出框：深藍底 + 白字 + 橘色邊框 */
    .report-box {
        background-color: var(--card-blue) !important;
        color: #ffffff !important; /* 白字，在深藍底上最清楚 */
        padding: 25px;
        border-radius: 12px;
        border: 2px solid var(--text-orange); /* 橘色邊框 */
        font-family: "Microsoft JhengHei", sans-serif;
        line-height: 1.8;
        font-size: 16px;
        white-space: pre-wrap;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        margin-top: 20px;
    }
    
    /* 6. 表單卡片容器：稍微亮一點的深藍色 */
    .form-card {
        background-color: var(--card-blue);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #004080;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }

    /* 7. 標題與文字顏色設定 */
    h1 {
        color: var(--text-orange) !important; /* 標題橘色 */
        font-weight: 900 !important;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    h3 {
        color: var(--text-orange) !important; /* 副標題橘色 */
        font-weight: 700 !important;
        margin-top: 0 !important;
    }
    p {
        color: #cccccc !important; /* 說明文字淺灰 */
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
        st.markdown(f"<h3 style='color: #ff9933;'>⚙️ 系統設定</h3>", unsafe_allow_html=True)
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
st.markdown("<p style='text-align: center; font-size: 15px; margin-bottom: 25px;'>AI 賦能．精準開發．專業領航</p>", unsafe_allow_html=True)

# 表單卡片區域
with st.container():
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    
    with st.form("client_form"):
        st.markdown("<h3>📋 客戶基本輪廓</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            # 這裡的 Selectbox 會變成白底黑字，解決看不到的問題
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
                st.markdown(f"<h4 style='color: #ff9933; text-align: center; margin-top: 20px;'>✅ 分析完成！策略報告如下</h4>", unsafe_allow_html=True)
                st.markdown(f'<div class="report-box">{response.text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"發生錯誤：{e}")
