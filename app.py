import streamlit as st
import google.generativeai as genai
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 自定義 CSS (白底黑字版) ---
st.markdown("""
<style>
    .report-box {
        background-color: #ffffff !important;
        color: #000000 !important;
        padding: 25px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        border-left: 8px solid #4CAF50;
        font-family: "Microsoft JhengHei", sans-serif;
        line-height: 1.8;
        font-size: 16px;
        white-space: pre-wrap;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stTextInput input, .stTextArea textarea {
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# --- 核心邏輯：自動取得 API Key ---
# 1. 優先從保險箱 (Secrets) 拿鑰匙
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    # 既然有鑰匙了，就不用顯示輸入框，直接顯示歡迎訊息
    with st.sidebar:
        st.success("✅ 已自動登入團隊帳號")
else:
    # 2. 如果沒鑰匙，才顯示輸入框
    api_key = st.sidebar.text_input("請輸入 Google API Key", type="password")

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
        else:
            st.error("❌ 錯誤：API Key 無效或無權限。")
    except Exception as e:
        st.error(f"連線失敗：{e}")

# --- 主畫面 ---
st.title("🛡️ 保險業務超級軍師")
st.markdown("### 輸入客戶資料，AI 幫你擬定雙軌戰略")

with st.form("client_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        birthday = st.date_input("客戶生日", min_value=datetime.date(1950, 1, 1), value=datetime.date(1990, 1, 1))
    with col2:
        gender = st.selectbox("性別", ["男", "女"])
    with col3:
        income = st.text_input("年收入 (萬)", placeholder="例：100")

    col4, col5 = st.columns(2)
    with col4:
        job = st.text_input("職業 / 職位", placeholder="例：竹科工程師 / 主管")
    with col5:
        interests = st.text_input("興趣 / 休閒", placeholder="例：登山、美股、看韓劇")

    history = st.text_area("投保史 / 現有保障", placeholder="例：僅有公司團保...")
    
    st.markdown("---")
    st.subheader("🔍 深度分析關鍵")
    
    col_q, col_p = st.columns(2)
    with col_q:
        quotes = st.text_area("🗣️ 客戶語錄", placeholder="例：「我覺得保險都騙人的」...")
    with col_p:
        target_product = st.text_area("🎯 你的銷售目標", placeholder="例：美元利變型保單...")

    submitted = st.form_submit_button("🚀 啟動分析", use_container_width=True)

# --- 生成結果 ---
if submitted:
    if not api_key:
        st.error("❌ 請輸入 API Key 才能使用")
    elif not model:
        st.error("❌ 系統連線異常")
    else:
        with st.spinner("🧠 總監正在分析中..."):
            today = datetime.date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            
            final_prompt = f"""
            你是一位擁有 20 年經驗的頂尖保險業務總監。
            
            【你的任務】
            根據以下客戶資料，產出雙軌開發策略。
            
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
            3. 不要使用 Markdown 粗體符號 (**)，請使用乾淨的純文字排版。
            
            【請依序輸出】
            1. [客戶畫像與心理分析]
            2. [建議方向一] (含切入點、險種、話術)
            3. [建議方向二] (含切入點、險種、話術)
            """
            
            try:
                response = model.generate_content(final_prompt)
                st.success("✅ 分析完成！")
                st.markdown(f'<div class="report-box">{response.text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"發生錯誤：{e}")
