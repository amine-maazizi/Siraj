"use client";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { SentimentBadge } from "@/components/SentimentBadge";

type Message = { role:"user"|"assistant"; content:string; sentiment?:"positive"|"neutral"|"negative" };
type Doc = { doc_id: string; title?: string };
type ChatResp = { answer:string; citations:{page:number; snippet:string}[]; sentiment?: "positive"|"neutral"|"negative"; emoji?: string };

export default function ChatPage(){
  const [docId, setDocId] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");

  // Load docs for the drop-up
  const { data: docs = [] } = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.get<Doc[]>("/documents"),
  });

  // Default to first doc if none selected
  useEffect(() => {
    if (!docId && docs.length > 0) setDocId(docs[0].doc_id);
  }, [docs, docId]);

  const ask = useMutation({
    mutationFn: async () => api.post<ChatResp>("/chat", { doc_id: docId, messages }),
    onSuccess: (res)=>{
      setMessages(prev => {
        const updated = [...prev];
        const idx = updated.findIndex(m => m.role === "assistant" && m.content === "Thinking...");
        if (idx !== -1) {
          updated[idx] = { role: "assistant", content: res.answer };
        } else {
          updated.push({ role: "assistant", content: res.answer });
        }
        // Attach server sentiment to the last USER message (for the badge)
        if (res.sentiment) {
          for (let i = updated.length - 1; i >= 0; i--) {
            if (updated[i].role === "user") {
              updated[i] = { ...updated[i], sentiment: res.sentiment };
              break;
            }
          }
        }

        return updated;
      });
    }
  });

  const send = () => {
    if(!input || !docId) return;

    // provisional client guess; will be replaced by server sentiment on response
    const guess: "positive"|"neutral"|"negative" = input.includes("?") ? "neutral" : (input.length>120?"negative":"positive");

    setMessages(prev => [...prev, { role:"user", content: input, sentiment: guess }]);
    setInput("");

    setMessages(prev => [...prev, { role:"assistant", content: "Thinking..." }]);
    ask.mutate();
  };

  const lastSentiment = [...messages].reverse().find(m=>m.role==="user")?.sentiment || "neutral";
  const selected = docs.find(d=>d.doc_id===docId);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Q&A</h1>
          <SentimentBadge sentiment={lastSentiment}/>
        </div>

        {/* Dropdown document picker */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(o => !o)}
            className="px-3 py-2 rounded-xl border border-white/15 bg-midnight/60 hover:bg-midnight/80"
            title={selected?.title || docId || "Select document"}
          >
            {selected?.title || docId || "Select document"}
          </button>

          {menuOpen && (
            <div
              className="absolute top-full right-0 mt-2 w-72 max-h-64 overflow-auto
                        bg-midnight/95 border border-white/10 rounded-xl shadow-xl p-2 z-10"
            >
              {docs.map(d => (
                <button
                  key={d.doc_id}
                  onClick={() => { setDocId(d.doc_id); setMenuOpen(false); }}
                  className={`w-full text-left px-3 py-2 rounded-lg hover:bg-white/10 ${
                    d.doc_id === docId ? "bg-white/10" : ""
                  }`}
                >
                  <div className="text-sm font-medium">{d.title || d.doc_id}</div>
                  <div className="text-xs opacity-70">{d.doc_id}</div>
                </button>
              ))}
              {docs.length === 0 && (
                <div className="px-3 py-2 text-sm opacity-70">
                  No documents found. Ingest one first.
                </div>
              )}
            </div>
          )}
        </div>

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
        <input
          value={input}
          onChange={e=>setInput(e.target.value)}
          placeholder="Ask something…"
          className="flex-1 bg-transparent border rounded-xl px-3 py-2 border-white/15"
          onKeyDown={(e)=>{ if(e.key==="Enter") send(); }}
        />
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
