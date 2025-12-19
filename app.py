import streamlit as st
import google.generativeai as genai
import datetime

# --- 設定頁面 ---
st.set_page_config(page_title="保險業務開發雙引擎", page_icon="🛡️")

# --- 側邊欄：設定 API Key ---
st.sidebar.header("⚙️ 設定")
api_key = st.sidebar.text_input("請輸入 Google API Key", type="password")

if api_key:
    # 設定模型
    genai.configure(api_key=api_key)
    
    # 這裡放入你之前在 System Instructions 寫好的超級指令
    sys_instruction = """
    你是一位擁有 20 年經驗的頂尖保險業務總監，精通「需求分析」、「風險管理」與「財務規劃」。
    你的目標是根據使用者提供的詳細客戶資料，產出高度客製化、有溫度的開發策略與建議。
    (請將你在 AI Studio 寫好的完整指令貼在這裡，取代這段文字)
    """
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=sys_instruction
    )
else:
    st.sidebar.warning("請先輸入 API Key 才能開始使用！")

# --- 主畫面 ---
st.title("🛡️ 保險業務超級軍師")
st.markdown("輸入客戶資料，AI 幫你生成 **風險分析** 與 **開發話術**。")

with st.form("client_form"):
    col1, col2 = st.columns(2)
    with col1:
        birthday = st.date_input("客戶生日", min_value=datetime.date(1950, 1, 1))
        gender = st.selectbox("性別", ["男", "女"])
        income = st.text_input("年收入 (例如：100萬)")
    with col2:
        job = st.text_input("職業 (例如：竹科工程師)")
        interests = st.text_input("興趣 (例如：露營、煮咖啡)")
        history = st.text_area("投保史 (例如：僅有健保、一張儲蓄險)")
    
    submitted = st.form_submit_button("🚀 開始分析與生成話術")

# --- 生成邏輯 ---
if submitted and api_key:
    with st.spinner("AI 正在思考策略中..."):
        # 計算年齡
        today = datetime.date.today()
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        
        # 組合 Prompt
        user_prompt = f"""
        【客戶資料】
        生日：{birthday} (約 {age} 歲)
        性別：{gender}
        職業：{job}
        興趣：{interests}
        年收入：{income}
        投保史：{history}
        """
        
        try:
            response = model.generate_content(user_prompt)
            st.success("分析完成！")
            st.markdown("---")
            st.markdown(response.text)
        except Exception as e:
            st.error(f"發生錯誤：{e}")
            
elif submitted and not api_key:
    st.error("請先在左側輸入 API Key！")
