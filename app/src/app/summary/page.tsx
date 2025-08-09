"use client";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useState } from "react";
import { VideoPlayer } from "@/components/VideoPlayer";

export default function SummaryPage(){
  const [docId, setDocId] = useState("");
  const [summary, setSummary] = useState<any>(null);
  const [video, setVideo] = useState<{mp4?:string; vtt?:string}>({});

  const summarize = useMutation({
    mutationFn: async () => api.post("/summarize", { doc_id: docId }),
    onSuccess: setSummary
  });

  const brainrot = useMutation({
    mutationFn: async () => {
      const s = await api.post<{job_id:string; summary_text:string}>("/brainrot/summary", { doc_id: docId, style: "tldr", duration_sec: 30 });
      const t = await api.post<{audio_path:string; duration_ms:number}>("/brainrot/tts", { job_id: s.job_id, text: s.summary_text });
      const c = await api.post<{vtt_path:string}>("/brainrot/captions", { job_id: s.job_id, audio_path: t.audio_path, text: s.summary_text });
      const r = await api.post<{video_path:string}>("/brainrot/render", { job_id: s.job_id, audio_path: t.audio_path, vtt_path: c.vtt_path, aspect: "9:16", theme: "siraj", include_waveform: true });
      setVideo({ mp4: `/api/proxy?path=${encodeURIComponent(r.video_path)}`, vtt: `/api/proxy?path=${encodeURIComponent(c.vtt_path)}`});
    }
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Summary & Brainrot</h1>
      <div className="s-card p-4 grid gap-3">
        <input value={docId} onChange={e=>setDocId(e.target.value)} placeholder="Enter doc_id" className="bg-transparent border rounded-xl px-3 py-2 border-white/15"/>
        <div className="flex gap-2">
          <button onClick={()=>summarize.mutate()} className="s-btn-amber">Generate Text Summary</button>
          <button onClick={()=>brainrot.mutate()} className="s-btn-amber">Create Brainrot Video</button>
        </div>
      </div>
      {summary && (
        <div className="s-card p-4">
          <h2 className="text-xl mb-2">Summary</h2>
          <div className="grid gap-3">
            {summary.summary_sections?.map((s:any,i:number)=> (
              <div key={i}>
                <div className="font-medium text-goldHi">{s.title}</div>
                <ul className="list-disc list-inside text-sandLight/90">
                  {s.bullets?.map((b:string, j:number)=> <li key={j}>{b}</li>)}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
      {video.mp4 && (
        <div className="s-card p-3">
          <VideoPlayer src={video.mp4} vttSrc={video.vtt}/>
        </div>
      )}
    </div>
  );
}