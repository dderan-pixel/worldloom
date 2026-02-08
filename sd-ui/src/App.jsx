import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

const tabs = ["Chat", "Simulate", "AI Score", "Portfolio", "News"];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("Chat");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { role: "user", text: input };
    setMessages([...messages, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post("http://34.32.76.50:8000/chat", {
        message: input,
      });
      const botMsg = { role: "assistant", text: res.data.response };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const errorMsg = {
        role: "assistant",
        text: "❌ Network Error: " + err.message,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-white font-sans">
      <header className="flex justify-between items-center px-8 py-4 bg-[#1e293b] shadow">
        <h1 className="text-2xl font-bold">Worldloom GPT</h1>
        <div className="space-x-4">
          <button className="hover:underline text-sm">Login</button>
          <button className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded">Subscribe</button>
        </div>
      </header>

      <nav className="flex justify-center space-x-4 bg-[#111827] border-b border-gray-700 py-3 sticky top-0 z-10">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={`px-4 py-2 text-sm rounded-md ${
              activeTab === tab ? "bg-blue-600 text-white" : "hover:bg-gray-700"
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {activeTab === "Chat" && (
          <>
            <div className="bg-[#1e293b] rounded-lg p-6 h-[400px] overflow-y-auto shadow-inner space-y-4">
              {messages.map((msg, i) => (
                <div key={i} className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}>
                  <div className={`max-w-[75%] px-4 py-2 rounded-lg text-sm ${
                    msg.role === "user"
                      ? "bg-blue-500 text-white"
                      : "bg-gray-700 text-gray-100"
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="text-sm text-gray-400 italic">Assistant is typing...</div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="flex mt-6 gap-4">
              <textarea
                className="flex-1 bg-gray-800 border border-gray-600 rounded-lg p-3 resize-none h-24"
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
              />
              <button
                onClick={sendMessage}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg"
                disabled={loading}
              >
                Send
              </button>
            </div>
          </>
        )}

        {activeTab !== "Chat" && (
          <div className="mt-10 text-center text-gray-400 text-sm italic">
            🚧 {activeTab} is under construction.
          </div>
        )}
      </main>
    </div>
  );
}
