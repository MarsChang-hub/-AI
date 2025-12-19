import streamlit as st
import google.generativeai as genai
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="保險業務超級軍師", page_icon="🛡️", layout="wide")

# --- 自定義 CSS ---
st.markdown("""
<style>
    .report-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        font-family: sans-serif;
        line-height: 1.6;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# --- 側邊欄：設定 ---
with st.sidebar:
    st.header("⚙️ 系統設定")
    api_key = st.text_input("請輸入 Google API Key", type="password")
    st.info("💡 這是「萬用相容模式」，使用最穩定的 Gemini Pro 模型。")

# --- 核心邏輯 ---
if api_key:
    genai.configure(api_key=api_key)
    
    # 【關鍵修改 1】改用最經典的 gemini-pro 模型 (絕對不會 404)
    # 注意：這裡我們先不放 system_instruction，改在下面用「手動拼接」的方式
    model = genai.GenerativeModel("gemini-pro")

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
        st.error("❌ 請先在左側欄位輸入 Google API Key")
    else:
        with st.spinner("🧠 總監正在分析中..."):
            today = datetime.date.today()
            age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
            
            # 【關鍵修改 2】把系統指令直接寫進 User Prompt 裡 (Old School 寫法，相容性 100%)
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
            3. 不要使用 Markdown 粗體符號，保持版面乾淨。
            
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
