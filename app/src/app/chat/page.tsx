"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { SentimentBadge } from "@/components/SentimentBadge";

export default function ChatPage(){
  const [docId, setDocId] = useState("");
  const [messages, setMessages] = useState<{role:"user"|"assistant"; content:string; sentiment?:"positive"|"neutral"|"negative"}[]>([]);
  const [input, setInput] = useState("");

  const ask = useMutation({
    mutationFn: async () => api.post<{answer:string; citations:{page:number; snippet:string}[]}>("/chat", { doc_id: docId, messages }),
    onSuccess: (res)=>{
      // Replace placeholder with real answer
      setMessages(prev => {
        const updated = [...prev];
        const placeholderIndex = updated.findIndex(m => m.role === "assistant" && m.content === "Thinking...");
        if (placeholderIndex !== -1) {
          updated[placeholderIndex] = { role: "assistant", content: res.answer };
        }
        return updated;
      });
    }
  });

  const send = () => {
    if(!input) return;
    const s: "positive"|"neutral"|"negative" = input.includes("?") ? "neutral" : (input.length>120?"negative":"positive");

    // Add user message
    setMessages(prev => [...prev, { role:"user", content: input, sentiment: s }]);
    setInput("");

    // Add placeholder assistant response right away
    setMessages(prev => [...prev, { role:"assistant", content: "Thinking..." }]);

    ask.mutate();
  };

  const lastSentiment = [...messages].reverse().find(m=>m.role==="user")?.sentiment || "neutral";

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">Q&A</h1>
        <SentimentBadge sentiment={lastSentiment}/>
      </div>

      <div className="s-card p-4 h-[60vh] overflow-auto space-y-3">
        {messages.map((m,i)=> (
          <div key={i} className={m.role==='user'?"text-right":"text-left"}>
            <div className={
              "inline-block max-w-[80%] px-4 py-2 rounded-2xl " + 
              (m.role==='user' ? "bg-amberGlow text-midnight" : "bg-midnight/70 border border-white/10")
            }>
              {m.content}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input value={docId} onChange={e=>setDocId(e.target.value)} placeholder="doc_id" className="bg-transparent border rounded-xl px-3 py-2 border-white/15 w-40"/>
        <input value={input} onChange={e=>setInput(e.target.value)} placeholder="Ask something…" className="flex-1 bg-transparent border rounded-xl px-3 py-2 border-white/15"/>
        <button onClick={send} className="s-btn-amber">Send</button>
      </div>

      {lastSentiment === "negative" && (
        <div className="flex gap-2">
          <button className="s-btn-amber">Need a simpler explanation?</button>
          <button className="s-btn-amber">More examples</button>
        </div>
      )}
    </div>
  );
}
