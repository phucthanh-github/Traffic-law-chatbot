"use client";
import { useState } from "react";

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // Gọi sang NestJS Backend (Port 4000)
      const res = await fetch("http://localhost:4000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input }),
      });
      const data = await res.json();

      const botMsg = { 
        role: "bot", 
        content: data.answer, 
        steps: data.steps // Lưu thêm các bước suy nghĩ
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-10 bg-gray-900 text-white">
      <h1 className="text-3xl font-bold mb-8 text-blue-400">Self-RAG AI Agent</h1>

      <div className="w-full max-w-3xl flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>

            {/* Bong bóng chat chính */}
            <div className={`p-4 rounded-xl max-w-[80%] ${msg.role === "user" ? "bg-blue-600" : "bg-gray-700"}`}>
              {msg.content}
            </div>

            {/* Hiển thị quy trình suy nghĩ (Thinking Process) */}
            {msg.steps && (
              <div className="mt-2 text-xs text-gray-400 ml-2 border-l-2 border-gray-600 pl-3">
                <p className="font-bold mb-1">Thinking Process:</p>
                {msg.steps.map((step: any, sIdx: number) => (
                  <div key={sIdx} className="mb-1">
                    <span className="text-yellow-500 uppercase">[{step.node}]</span>: {step.content}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="text-gray-400 animate-pulse">AI đang suy nghĩ...</div>}
      </div>

      <div className="w-full max-w-3xl flex gap-2">
        <input
          className="flex-1 p-3 rounded-lg bg-gray-800 border border-gray-600 focus:outline-none focus:border-blue-500"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Hỏi về bệnh tiểu đường..."
        />
        <button 
          onClick={sendMessage}
          className="bg-blue-600 px-6 py-3 rounded-lg hover:bg-blue-700 font-bold transition"
        >
          Gửi
        </button>
      </div>
    </main>
  );
}