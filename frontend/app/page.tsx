"use client";
import { useState, useRef, useEffect } from "react";

const QUICK_PROMPTS = [
  { text: "Mức phạt vượt đèn đỏ đối với xe máy?", icon: "🏍️" },
  { text: "Bằng lái xe hạng B2 được lái những loại xe nào?", icon: "🚗" },
  { text: "Các hành vi bị nghiêm cấm trong hoạt động đường bộ?", icon: "🚫" },
  { text: "Quy định về hành lang an toàn đường bộ như thế nào?", icon: "🛣️" },
];

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Tự động cuộn xuống khi có tin nhắn mới
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (textToSend?: string) => {
    const text = textToSend !== undefined ? textToSend : input;
    if (!text.trim()) return;

    // Lấy lịch sử trò chuyện từ mảng messages hiện tại trước khi thêm câu hỏi mới
    const chatHistory = messages
      .filter((msg) => msg.content.trim() !== "")
      .map((msg) => ({
        role: msg.role === "user" ? "user" : "assistant",
        content: msg.content
      }));

    const userMsg = { role: "user", content: text };
    const botMsgPlaceholder = { 
      role: "bot", 
      content: ""
    };
    
    // Thêm đồng thời user message và bot message placeholder vào danh sách
    setMessages((prev) => [...prev, userMsg, botMsgPlaceholder]);
    
    if (textToSend === undefined) {
      setInput("");
    }
    setLoading(true);

    try {
      // Gọi sang NestJS Backend (Port 4000)
      const res = await fetch("http://localhost:4000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, chatHistory }),
      });

      if (!res.body) {
        throw new Error("Không nhận được luồng dữ liệu (ReadableStream) từ server.");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Phân tích cú pháp các dòng SSE
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || ""; // Giữ lại phần chưa hoàn chỉnh cuối cùng

        for (const part of parts) {
          if (part.startsWith("data: ")) {
            const dataStr = part.substring(6).trim();
            if (!dataStr) continue;

            try {
              const data = JSON.parse(dataStr);
              if (data.type === "token") {
                setMessages((prev) => {
                  const updated = [...prev];
                  const idx = updated.length - 1;
                  if (idx >= 0 && updated[idx].role === "bot") {
                    const currentBotMsg = { ...updated[idx] };
                    currentBotMsg.content += data.content;
                    updated[idx] = currentBotMsg;
                  }
                  return updated;
                });
              } else if (data.type === "error") {
                setMessages((prev) => {
                  const updated = [...prev];
                  const idx = updated.length - 1;
                  if (idx >= 0 && updated[idx].role === "bot") {
                    const currentBotMsg = { ...updated[idx] };
                    currentBotMsg.content = `Lỗi: ${data.content}`;
                    updated[idx] = currentBotMsg;
                  }
                  return updated;
                });
              }
            } catch (err) {
              console.error("Lỗi parse JSON chunk:", err, dataStr);
            }
          }
        }
      }
    } catch (e: any) {
      console.error(e);
      setMessages((prev) => {
        const updated = [...prev];
        const idx = updated.length - 1;
        if (idx >= 0 && updated[idx].role === "bot") {
          const currentBotMsg = { ...updated[idx] };
          currentBotMsg.content = `Lỗi kết nối tới Server AI: ${e.message || e}`;
          updated[idx] = currentBotMsg;
        }
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };



  return (
    <main className="relative flex min-h-screen flex-col items-center justify-between p-4 md:p-10 bg-[#0b0f19] text-gray-100 overflow-hidden font-sans">
      {/* Glow Effects in Background */}
      <div className="absolute top-10 left-10 w-72 h-72 rounded-full bg-blue-600/15 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-96 h-96 rounded-full bg-indigo-600/15 blur-[150px] pointer-events-none" />
      
      {/* Header Container */}
      <div className="w-full max-w-4xl flex flex-col items-center text-center z-10 mt-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-4">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
          </span>
          Self-Reflective RAG Agent
        </div>
        <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent mb-2 drop-shadow-sm">
          Trợ Lý Luật Giao Thông Việt Nam
        </h1>
        <p className="text-gray-400 text-sm md:text-base max-w-2xl">
          Giải đáp trực tuyến các thắc mắc về Luật Giao thông đường bộ số 35/2024/QH15. Hệ thống AI tự động kiểm chứng và trích dẫn điều khoản chính xác.
        </p>
      </div>

      {/* Main Chat Container */}
      <div className="w-full max-w-4xl flex-1 flex flex-col mt-8 z-10 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-md shadow-2xl overflow-hidden min-h-[500px]">
        {/* Messages list */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 max-h-[55vh]">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-gray-500 py-16 px-4">
              <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center border border-white/10 text-3xl mb-4 animate-bounce">
                🛡️
              </div>
              <p className="text-lg font-medium text-gray-300">Chào mừng bạn đến với Trợ lý Luật Giao thông!</p>
              <p className="text-sm text-gray-400 max-w-md mt-1">
                Hãy đặt câu hỏi trực tiếp hoặc lựa chọn một trong những câu hỏi gợi ý nhanh dưới đây để bắt đầu.
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                
                {/* Bubble Wrapper */}
                <div className={`group relative max-w-[85%] rounded-2xl p-4 shadow-md ${
                  msg.role === "user" 
                    ? "bg-indigo-600/80 border border-indigo-500/20 text-white rounded-tr-none" 
                    : "bg-gray-800/80 border border-gray-700/50 text-gray-100 rounded-tl-none"
                }`}>
                  <span className="absolute -top-5 text-[9px] text-gray-500 font-semibold tracking-wider uppercase">
                    {msg.role === "user" ? "BẠN" : "AI AGENT"}
                  </span>
                  
                  <div className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </div>
                </div>


              </div>
            ))
          )}
          {loading && (
            <div className="flex flex-col items-start space-y-2 animate-pulse">
              <div className="max-w-[85%] rounded-2xl rounded-tl-none p-4 bg-white/5 border border-white/10 text-gray-400 text-sm flex items-center gap-3">
                <span className="flex h-3 w-3 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                </span>
                Hệ thống đang suy nghĩ và tra cứu điều luật...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Quick Prompts Panel */}
        {messages.length === 0 && (
          <div className="px-4 md:px-6 py-4 bg-black/20 border-t border-white/5">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Câu hỏi gợi ý nhanh:</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {QUICK_PROMPTS.map((prompt, pIdx) => (
                <button
                  key={pIdx}
                  onClick={() => sendMessage(prompt.text)}
                  className="flex items-center gap-2 p-3 text-left rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/10 text-xs md:text-sm text-gray-300 hover:text-white transition shadow-sm hover:shadow-md cursor-pointer"
                >
                  <span className="text-base flex-shrink-0">{prompt.icon}</span>
                  <span className="truncate">{prompt.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Bar */}
        <div className="p-4 md:p-6 bg-black/40 border-t border-white/10 flex gap-2 items-center">
          <input
            className="flex-1 p-3.5 rounded-xl bg-[#131926] border border-white/10 focus:border-blue-500/80 focus:ring-1 focus:ring-blue-500/80 focus:outline-none text-sm md:text-base text-gray-100 placeholder-gray-500 transition-all shadow-inner"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Hỏi về Luật Giao thông đường bộ..."
            disabled={loading}
          />
          <button 
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className={`p-3.5 px-6 rounded-xl font-bold text-sm md:text-base transition-all duration-200 flex items-center justify-center gap-2 ${
              loading || !input.trim()
                ? "bg-gray-800 text-gray-500 cursor-not-allowed border border-white/5"
                : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-indigo-600/20 hover:scale-[1.02] cursor-pointer"
            }`}
          >
            <span>Gửi</span>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4.5 h-4.5">
              <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.896 28.896 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Footer Info */}
      <div className="w-full max-w-4xl text-center z-10 mt-6 text-[10px] md:text-xs text-gray-600">
        Dự án xây dựng bằng Next.js, Nest.js & LangGraph Self-RAG. Dữ liệu trích xuất trực tiếp từ file tài liệu của bạn.
      </div>
    </main>
  );
}