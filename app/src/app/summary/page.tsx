// app/src/app/summary/page.tsx
"use client";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useMemo, useState } from "react";
import { VideoPlayer } from "@/components/VideoPlayer";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

export default function SummaryPage() {
  const [docId, setDocId] = useState("");
  const [summary, setSummary] = useState<any>(null);
  const [video, setVideo] = useState<{ mp4?: string; vtt?: string }>({});

  const { data: rawDocs = [], isLoading: docsLoading, isError: docsErr, error: docsError } = useQuery({
    queryKey: ["docs"],
    queryFn: async () => {
      const raw = await api.get("/documents");
      if (Array.isArray(raw)) return raw;
      if (Array.isArray(raw?.docs)) return raw.docs;
      if (Array.isArray(raw?.items)) return raw.items;
      return [];
    },
  });

  const docs = useMemo(() => rawDocs ?? [], [rawDocs]);

  const summarize = useMutation({
    mutationFn: async () => api.post("/summarize", { doc_id: docId }).then((r: any) => r.data ?? r),
    onSuccess: setSummary,
    onError: (err: any) => {
      console.error("Summarize failed", err);
      alert(`Summarize failed: ${err?.message ?? "Unknown error"}`);
    },
  });

  const brainrot = useMutation({
    mutationFn: async () => {
      const s = await api.post<{ job_id: string; summary_text: string }>("/brainrot/summary", {
        doc_id: docId,
        style: "tldr",
        duration_sec: 30,
      });
      const t = await api.post<{ audio_path: string; duration_ms: number }>("/brainrot/tts", {
        job_id: s.job_id,
        text: s.summary_text,
      });
      const c = await api.post<{ vtt_path: string }>("/brainrot/captions", {
        job_id: s.job_id,
        audio_path: t.audio_path,
        text: s.summary_text,
      });
      const r = await api.post<{ video_path: string }>("/brainrot/render", {
        job_id: s.job_id,
        audio_path: t.audio_path,
        vtt_path: c.vtt_path,
        aspect: "9:16",
        theme: "siraj",
        include_waveform: true,
      });
      setVideo({
        mp4: `/proxy?path=${encodeURIComponent(r.video_path)}`,
        vtt: `/proxy?path=${encodeURIComponent(c.vtt_path)}`,
      });
    },
    onError: (e: any) => {
      console.error("[SummaryPage] brainrot error:", e);
      alert(`Brainrot failed: ${e?.message ?? "unknown error"}`);
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Summary & Brainrot</h1>

      <div className="s-card p-4 grid gap-3">
        {docsLoading ? (
          <div>Loading docs…</div>
        ) : docsErr ? (
          <div className="text-red-400">Docs error: {String(docsError)}</div>
        ) : (
          <select
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            className="bg-transparent border rounded-xl px-3 py-2 border-white/15"
          >
            <option value="">Select a document</option>
            {Array.isArray(docs) &&
              docs.map((d: any, i: number) => (
                <option key={i} value={d.doc_id}>
                  {d.title || d.doc_id}
                </option>
              ))}
          </select>
        )}

        <div className="flex gap-2">
          <button
            disabled={!docId || summarize.isPending}
            onClick={() => summarize.mutate()}
            className="s-btn-amber"
          >
            {summarize.isPending ? "Summarizing…" : "Generate Summary"}
          </button>
          <button
            disabled={!docId || brainrot.isPending}
            onClick={() => brainrot.mutate()}
            className="s-btn-amber"
          >
            {brainrot.isPending ? "Rendering…" : "💀 Fried Attention Span"}
          </button>
        </div>
      </div>

      {/* === Summary Board (Markdown + KaTeX) === */}
      {summary?.summary_sections?.length ? (
        <div className="s-card p-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl">Summary</h2>
            <button
              className="text-xs px-2 py-1 rounded-lg border border-white/10 hover:bg-white/5"
              onClick={() => {
                const text = summary.summary_sections
                  .map((s: any) => `## ${s.title}\n${(s.bullets || []).map((b: string) => `- ${b}`).join("\n")}`)
                  .join("\n\n");
                navigator.clipboard.writeText(text).catch(() => {});
              }}
            >
              Copy as Markdown
            </button>
          </div>

          <div className="grid gap-4">
            {summary.summary_sections.map((s: any, i: number) => (
              <div key={i} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="font-medium text-goldHi mb-2">{s.title}</div>

                {/* Each bullet rendered as Markdown+Math */}
                <div className="grid gap-2">
                  {(s.bullets ?? []).map((b: string, j: number) => (
                    <div key={j} className="rounded-xl bg-black/20 px-3 py-2">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                        // Optional: tweak elements for Siraj style
                        components={{
                          p: (props) => <p className="text-sandLight/90 leading-relaxed" {...props} />,
                          li: (props) => <li className="ml-4 list-disc" {...props} />,
                          code: (props) => (
                            <code className="px-1 py-0.5 rounded bg-black/40 text-sandLight/95" {...props} />
                          ),
                        }}
                      >
                        {b}
                      </ReactMarkdown>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : summary ? (
        <div className="s-card p-4">
          <h2 className="text-xl mb-2">Summary (raw)</h2>
          <pre className="text-xs opacity-80 overflow-auto max-h-64">
{JSON.stringify(summary, null, 2)}
          </pre>
          <div className="text-amber-300 text-sm">No summary_sections found in response.</div>
        </div>
      ) : null}

      {video.mp4 && (
        <div className="s-card p-3">
          <VideoPlayer src={video.mp4} vttSrc={video.vtt} />
        </div>
      )}
    </div>
  );
}
