import { GoogleGenAI } from "@google/genai";
import { CustomerProfile } from "../types";

const apiKey = process.env.API_KEY;

// Initialize client
const ai = new GoogleGenAI({ apiKey: apiKey || '' });

export const generateInsuranceAnalysis = async (profile: CustomerProfile): Promise<string> => {
  if (!apiKey) throw new Error("API Key not found");

  const prompt = `
你是一位擁有 20 年經驗的頂尖保險業務總監，精通「需求分析」、「風險管理」與「財務規劃」。你的目標是根據以下詳細客戶資料，產出高度客製化、多角度的開發策略。

**客戶資料：**
- 生日：${profile.birthday}
- 性別：${profile.gender}
- 職業：${profile.occupation}
- 興趣：${profile.interests}
- 年收入：${profile.income}
- 投保史：${profile.history}
- **客戶曾說過的話 (關鍵線索)：** "${profile.quotes}"
- **業務員想主推的商品/方向：** "${profile.targetProduct}" (若此欄為空，請依專業自行判斷適合商品)

**你的思考邏輯與要求：**
1.  **多維度切入**：請勿過度依賴「生日」作為單一話題。請提供 **兩種截然不同的切入策略** (例如：策略 A 從「職業痛點」切入，策略 B 從「資產配置」或「家庭責任」切入)。
2.  **連結目標商品**：若使用者有輸入「主推商品」，請務必將該商品包裝在策略中；若無，請推薦最適合的缺口商品。
3.  **解讀潛台詞**：深入分析「客戶曾說過的話」，這通常是成交的關鍵鑰匙。

**輸出格式要求 (Clean Text)：**
請保持版面乾淨，避免複雜的 Markdown 符號 (如 **粗體**, ### 標題)。
請用簡單的符號 (如 「•」 或 「1.」) 分點。
段落間留空行以利閱讀。

**請依序輸出以下內容：**

【客戶畫像與潛在需求】
(簡短分析客戶心理狀態與風險缺口，並解讀他說那句話背後的含義。)

【攻防策略一：(請自行命名，例如：理性數據導向)】
• 切入點：(說明為什麼選這個角度)
• 推薦商品：(結合業務員想推的商品)
• 實際操作話術：(給出一段具體的開場白或LINE訊息，語氣自然)

【攻防策略二：(請自行命名，例如：感性責任導向)】
• 切入點：(提供另一個完全不同的角度，增加成交機率)
• 推薦商品：(可以是同商品的不同賣點，或是搭配其他商品)
• 實際操作話術：(給出另一種風格的溝通劇本)

【專家提醒】
(給業務員的一個成交小撇步或注意事項)
`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview',
      contents: prompt,
      config: {
        temperature: 0.75, // Slightly higher for creativity in generating two distinct paths
        thinkingConfig: { thinkingBudget: 2048 }
      }
    });
    
    return response.text || "無法產生分析結果。";
  } catch (error) {
    console.error("Text generation error:", error);
    throw error;
  }
};