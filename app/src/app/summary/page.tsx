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
  const [video, setVideo] = useState<{ jobId?: string; mp4?: string; vtt?: string }>({});
  const [progress, setProgress] = useState<string>("");

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
      if (!docId) throw new Error("Pick a document first.");

      setVideo({});
      setProgress("Drafting script…");
      const s = await api.post<{ job_id: string; summary_text: string }>("/brainrot/summary", {
        doc_id: docId,
        style: "tldr",
        duration_sec: 30,
      });

      const jobId = s.job_id;
      if (!jobId) throw new Error("No job_id returned from /brainrot/summary");

      setProgress("Synthesizing voice…");
      await api.post("/brainrot/tts", {
        job_id: jobId,
        text: s.summary_text,
        voice: "en_female_1",
        speed: 1.0,
      });

      setProgress("Timing captions…");
      await api.post("/brainrot/captions", {
        job_id: jobId,
        text: s.summary_text,
        level: "line",
      });

      setProgress("Rendering video…");
      await api.post("/brainrot/render", {
        job_id: jobId,
        aspect: "9:16",
        include_waveform: false,
        theme: "siraj",
      });

      // Use pretty routes from your FastAPI:
      // GET /brainrot/{job_id} -> mp4
      // GET /brainrot/{job_id}.vtt -> captions
      setVideo({
        jobId,
        mp4: `/proxy?path=${encodeURIComponent(`/brainrot/${jobId}`)}`,
        vtt: `/proxy?path=${encodeURIComponent(`/brainrot/${jobId}.vtt`)}`,
      });
      setProgress("");
    },
    onError: (e: any) => {
      console.error("[SummaryPage] brainrot error:", e);
      setProgress("");
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
            title={docId ? "Generate a short memetic video" : "Select a document first"}
          >
            {brainrot.isPending ? (progress || "Rendering…") : "💀 Fried Attention Span"}
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

                <div className="grid gap-2">
                  {(s.bullets ?? []).map((b: string, j: number) => (
                    <div key={j} className="rounded-xl bg-black/20 px-3 py-2">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
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

      {/* === Video Panel === */}
      {video.mp4 && (
        <div className="s-card p-3">
          <VideoPlayer src={video.mp4} vttSrc={video.vtt} />
        </div>
      )}
    </div>
  );
}
