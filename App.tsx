import React, { useState } from 'react';
import { 
  CustomerProfile, 
  Gender, 
  AnalysisResult
} from './types';
import { generateInsuranceAnalysis } from './services/geminiService';

const App: React.FC = () => {
  // --- State ---
  const [profile, setProfile] = useState<CustomerProfile>({
    birthday: '',
    gender: Gender.MALE,
    occupation: '',
    interests: '',
    income: '',
    history: '',
    quotes: '',
    targetProduct: '' // Initialize new field
  });

  const [analysis, setAnalysis] = useState<AnalysisResult>({
    text: '',
    isLoading: false
  });

  // --- Handlers ---
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setProfile(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Reset output states
    setAnalysis({ text: '', isLoading: true, error: undefined });

    // Trigger Text Analysis
    generateInsuranceAnalysis(profile)
      .then(text => {
        setAnalysis({ text, isLoading: false });
      })
      .catch(err => {
        setAnalysis({ text: '', isLoading: false, error: "分析生成失敗，請稍後再試。" });
      });
  };

  // --- Helpers ---
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-emerald-600">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
            </svg>
            <h1 className="text-xl font-bold tracking-tight text-slate-800">InsureAI <span className="text-emerald-600 font-light">Advisor</span></h1>
          </div>
          <div className="text-sm text-slate-500 hidden sm:block">
            智慧保險開發助手 · Powered by Gemini
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* LEFT COLUMN: Input Form */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
                客戶資料建檔
              </h2>
              
              <form onSubmit={handleSubmit} className="space-y-5">
                
                {/* Birthday & Gender Row */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">生日</label>
                    <input 
                      type="date" 
                      name="birthday"
                      max={today}
                      required
                      value={profile.birthday}
                      onChange={handleInputChange}
                      className="w-full rounded-md border-slate-200 bg-slate-50 p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">性別</label>
                    <select 
                      name="gender"
                      value={profile.gender}
                      onChange={handleInputChange}
                      className="w-full rounded-md border-slate-200 bg-slate-50 p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                    >
                      <option value={Gender.MALE}>{Gender.MALE}</option>
                      <option value={Gender.FEMALE}>{Gender.FEMALE}</option>
                      <option value={Gender.OTHER}>{Gender.OTHER}</option>
                    </select>
                  </div>
                </div>

                {/* Occupation & Income */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">職業</label>
                    <input 
                      type="text" 
                      name="occupation"
                      placeholder="例：竹科工程師"
                      required
                      value={profile.occupation}
                      onChange={handleInputChange}
                      className="w-full rounded-md border-slate-200 bg-slate-50 p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-500 mb-1">年收入</label>
                    <input 
                      type="text" 
                      name="income"
                      placeholder="例：300萬"
                      required
                      value={profile.income}
                      onChange={handleInputChange}
                      className="w-full rounded-md border-slate-200 bg-slate-50 p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                    />
                  </div>
                </div>

                {/* Interests */}
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">興趣與愛好</label>
                  <input 
                    type="text" 
                    name="interests"
                    placeholder="例如：登山、美股、攝影"
                    required
                    value={profile.interests}
                    onChange={handleInputChange}
                    className="w-full rounded-md border-slate-200 bg-slate-50 p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>

                {/* History */}
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">既有投保史</label>
                  <textarea 
                    name="history"
                    rows={2}
                    placeholder="例如：僅有團保、一張20年前儲蓄險..."
                    required
                    value={profile.history}
                    onChange={handleInputChange}
                    className="w-full rounded-md border-slate-200 bg-slate-50 p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>

                {/* Target Product - NEW FIELD */}
                 <div>
                  <label className="block text-xs font-medium text-emerald-700 font-bold mb-1 flex items-center justify-between">
                    <span>想銷售的商品 / 策略重點</span>
                    <span className="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">選填</span>
                  </label>
                  <input 
                    type="text" 
                    name="targetProduct"
                    placeholder="例如：美元利變型、長照險、投資型保單..."
                    value={profile.targetProduct}
                    onChange={handleInputChange}
                    className="w-full rounded-md border-emerald-200 bg-emerald-50/30 p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none placeholder:text-slate-400"
                  />
                </div>

                {/* Quotes */}
                <div>
                  <label className="block text-xs font-medium text-emerald-700 font-bold mb-1 flex items-center justify-between">
                    <span>他/她說 (關鍵線索)</span>
                    <span className="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">銷售關鍵</span>
                  </label>
                  <textarea 
                    name="quotes"
                    rows={3}
                    placeholder="請輸入客戶說過的一句話，例如：「我最近覺得身體容易累...」或「保險都是騙人的。」"
                    required
                    value={profile.quotes}
                    onChange={handleInputChange}
                    className="w-full rounded-md border-emerald-200 bg-emerald-50/30 p-2.5 text-sm focus:ring-2 focus:ring-emerald-500 outline-none placeholder:text-slate-400"
                  />
                </div>

                <button 
                  type="submit"
                  disabled={analysis.isLoading}
                  className="w-full mt-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 px-4 rounded-lg shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
                >
                  {analysis.isLoading ? (
                    <>
                      <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      AI 深度分析中...
                    </>
                  ) : (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                      </svg>
                      生成雙軌策略
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* RIGHT COLUMN: Results */}
          <div className="lg:col-span-7 space-y-6">
            
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden min-h-[500px] flex flex-col">
              <div className="bg-slate-50 border-b border-slate-200 px-6 py-4 flex justify-between items-center">
                <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-emerald-600">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                  策略分析與銷售劇本
                </h3>
              </div>
              <div className="p-8 flex-1 bg-white">
                {analysis.isLoading ? (
                  <div className="animate-pulse space-y-6">
                    <div className="h-5 bg-slate-100 rounded w-1/3"></div>
                    <div className="space-y-3">
                      <div className="h-4 bg-slate-100 rounded w-full"></div>
                      <div className="h-4 bg-slate-100 rounded w-5/6"></div>
                      <div className="h-4 bg-slate-100 rounded w-4/6"></div>
                    </div>
                    <div className="h-5 bg-slate-100 rounded w-1/4 pt-4"></div>
                     <div className="space-y-3">
                      <div className="h-4 bg-slate-100 rounded w-full"></div>
                      <div className="h-4 bg-slate-100 rounded w-full"></div>
                    </div>
                  </div>
                ) : analysis.error ? (
                  <div className="text-red-500 bg-red-50 p-6 rounded-lg text-center">
                    {analysis.error}
                  </div>
                ) : analysis.text ? (
                  <div className="prose prose-slate max-w-none">
                    {/* We use whitespace-pre-wrap but with a cleaner font and line-height. 
                        The backend prompt is now optimized to remove excessive markdown symbols. */}
                    <div className="whitespace-pre-wrap font-sans text-[15px] leading-relaxed text-slate-700 tracking-wide">
                      {analysis.text}
                    </div>
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400 min-h-[400px]">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" className="w-16 h-16 mb-4 opacity-30">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
                    </svg>
                    <p className="font-medium">等待輸入資料...</p>
                    <p className="text-sm mt-2 opacity-70">輸入左側客戶資料與對話，獲取專業銷售建議</p>
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
};

export default App;