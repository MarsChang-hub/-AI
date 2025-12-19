import streamlit as st
import google.generativeai as genai
import datetime

# --- 頁面設定 (設定標題與寬度) ---
st.set_page_config(page_title="KGI 保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 🎨 凱基人壽品牌配色 UI 設計 (CSS) ---
st.markdown("""
<style>
    /* 定義凱基人壽品牌色 */
    :root {
        --kgi-blue: #003366; /* 深藍色主色 */
        --kgi-orange: #FF6600; /* 亮橘色強調色 */
        --kgi-light-blue: #0099CC; /* 標誌中的亮藍色 */
        --bg-color: #f4f7f9; /* 淺藍灰色背景 */
    }

    /* 1. 整體背景微調 */
    .stApp {
        background-color: var(--bg-color);
        background-image: linear-gradient(to bottom right, #eef2f5, var(--bg-color)); /* 增加一點點質感漸層 */
    }
    
    /* 2. 移除頂部空白 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
    }

    /* 3. 輸入框優化：深藍色邊框，聚焦時變橘色 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input, .stTextArea textarea {
        background-color: #ffffff;
        border: 1px solid #ccd6e0; /* 淺藍灰色邊框 */
        border-radius: 8px; /* 稍微方一點，更穩重 */
        padding: 10px;
        font-size: 16px;
        box-shadow: 0 2px 4px rgba(0, 51, 102, 0.05); /* 深藍色微陰影 */
        color: var(--kgi-blue); /* 輸入文字顏色 */
    }
    /* 輸入框聚焦時的效果 */
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within, .stDateInput input:focus, .stTextArea textarea:focus {
        border-color: var(--kgi-orange); /* 聚焦變橘色 */
        box-shadow: 0 0 0 2px rgba(255, 102, 0, 0.2); /* 橘色光暈 */
    }

    /* 4. 按鈕大升級：深藍色底 + 橘色懸浮，品牌感強烈 */
    .stButton > button {
        width: 100%;
        background: var(--kgi-blue); /* 深藍色背景 */
        color: white;
        border: none;
        padding: 15px 0;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        box-shadow: 0 4px 10px rgba(0, 51, 102, 0.3); /* 深藍色陰影 */
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: var(--kgi-orange); /* 懸浮變橘色 */
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(255, 102, 0, 0.4); /* 橘色陰影 */
    }
    .stButton > button:active {
        background: #e65c00; /* 按下時更深的橘色 */
        box-shadow: 0 2px 5px rgba(255, 102, 0, 0.4);
        transform: translateY(0);
    }

    /* 5. 報告輸出框：白底黑字，左側深藍到橘色漸層條 */
    .report-box {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        /* 左側識別條改為品牌漸層色 */
        border-image: linear-gradient(to bottom, var(--kgi-blue), var(--kgi-orange)) 1 100%;
        border-left-width: 6px;
        border-left-style: solid;
        
        font-family: "Microsoft JhengHei", "PingFang TC", sans-serif;
        line-height: 1.8;
        font-size: 16px;
        white-space: pre-wrap;
        box-shadow: 0 8px 16px rgba(0, 51, 102, 0.1); /* 深藍色浮起陰影 */
        margin-top: 20px;
    }
    
    /* 6. 卡片容器樣式 */
    .form-card {
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 51, 102, 0.08); /* 深藍色陰影 */
        margin-bottom: 20px;
        border-top: 4px solid var(--kgi-blue); /* 卡片頂部加一條深藍色 */
    }

    /* 標題樣式 */
    h1 {
        color: var(--kgi-blue); /* 標題用深藍色 */
        font-family: "Microsoft JhengHei", sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: 1px;
    }
    
    /* 副標題樣式 */
    h3 {
        color: var(--kgi-blue) !important;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
    }
    
    /* 分隔線顏色 */
    hr {
        border-color: rgba(0, 51, 102, 0.1);
    }
    
    /* 隱藏 Streamlit 原生元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 核心邏輯與主畫面 (這部分不需要改，保持原樣) ---
# --- 自動取得 API Key ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    # 側邊欄也套用品牌色
    with st.sidebar:
        st.markdown(f"<h2 style='color: #003366;'>⚙️ 系統設定</h2>", unsafe_allow_html=True)
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

# 頂部標題區 (加入 KGI 風格)
col_logo, col_title = st.columns([1, 5])
# 這裡你可以選擇是否要加入 Logo 圖片，如果需要請告訴我，我教你怎麼放
# with col_logo:
#    st.image("你的logo網址.png", width=60) 

with col_title:
    st.markdown("<h1>KGI 保險業務超級軍師</h1>", unsafe_allow_html=True)

st.markdown("<p style='text-align: center; color: #666; font-size: 15px; margin-bottom: 25px;'>We Share We Link．AI 賦能，精準開發</p>", unsafe_allow_html=True)

# 使用容器將表單包起來
with st.container():
    st.markdown('<div class="form-card">', unsafe_allow_html=True) # 開始卡片
    
    with st.form("client_form"):
        st.markdown("### 📋 客戶基本輪廓")
        col1, col2 = st.columns([1, 1])
        with col1:
            gender = st.selectbox("性別", ["男", "女"])
        with col2:
            income = st.text_input("年收 (萬)", placeholder="例：100")
            
        birthday = st.date_input("客戶生日", min_value=datetime.date(1950, 1, 1), value=datetime.date(1990, 1, 1))
        
        st.markdown("### 💼 職業與興趣")
        job = st.text_input("職業 / 職位", placeholder="例：竹科工程師 / 主管")
        interests = st.text_input("興趣 / 休閒", placeholder="例：登山、美股、看韓劇")

        st.markdown("### 🛡️ 保障盤點")
        history = st.text_area("投保史 / 現有保障", placeholder="例：僅有公司團保...", height=100)
        
        st.markdown("---")
        st.subheader("🔍 深度分析線索")
        
        quotes = st.text_area("🗣️ 客戶語錄 (破冰關鍵)", placeholder="例：「我覺得保險都騙人的」...", height=100)
        target_product = st.text_area("🎯 你的銷售目標", placeholder="例：美元利變型保單...", height=80)

        st.markdown("<br>", unsafe_allow_html=True)
        # 按鈕文字也加入品牌精神
        submitted = st.form_submit_button("🚀 啟動 KGI 雙軌戰略分析")
    
    st.markdown('</div>', unsafe_allow_html=True) # 結束卡片

# --- 生成結果 ---
if submitted:
    if not api_key:
        st.error("⚠️ 請輸入 API Key")
    elif not model:
        st.error("⚠️ 系統連線異常")
    else:
        with st.spinner("🧠 KGI 總監正在分析客戶心理..."):
            today = datetime.date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            
            final_prompt = f"""
            你是一位擁有 20 年經驗的頂尖保險業務總監，任職於凱基人壽 (KGI LIFE)。
            
            【你的任務】
            根據以下客戶資料，產出符合凱基人壽專業形象的雙軌開發策略。
            
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
                # 成功訊息也用橘色強調
                st.markdown(f"<h4 style='color: #FF6600; text-align: center;'>✅ 分析完成！請查看下方 KGI 策略報告</h4>", unsafe_allow_html=True)
                st.markdown(f'<div class="report-box">{response.text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"發生錯誤：{e}")
