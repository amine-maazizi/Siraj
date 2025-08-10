// app/src/app/upload/page.tsx
"use client";

import { useState, useRef, useMemo, useCallback } from "react";
import { savePdf } from "@/lib/pdfDb";
import { usePdfStore } from "@/lib/pdfStore";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const inputRef = useRef<HTMLInputElement | null>(null);

  const fileMeta = useMemo(() => {
    if (!file) return null;
    const kb = file.size / 1024;
    return {
      name: file.name,
      size: kb > 1024 ? `${(kb / 1024).toFixed(2)} MB` : `${Math.ceil(kb)} KB`,
    };
  }, [file]);

  const onFilePicked = useCallback((f: File | null) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setErr("Only PDF files are supported.");
      setFile(null);
      return;
    }
    setErr(null);
    setResult(null);
    setFile(f);
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setErr("Choose a PDF first.");
      return;
    }
    setLoading(true);
    setErr(null);
    setResult(null);

    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/proxy?path=/ingest", { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      const resp = await res.json();

      await savePdf(resp.doc_id, file);

      usePdfStore.getState().setDoc({
        docId: resp.doc_id,
        title: resp.title ?? file.name,
        url: URL.createObjectURL(file),
      });

      setResult(resp);
    } catch (e: any) {
      setErr(e?.message ?? "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full h-full p-6 lg:p-8">
      <h1 className="text-2xl font-semibold tracking-tight mb-1">Upload & Ingest</h1>
      <p className="text-sm opacity-80 mb-6">
        Add a PDF to your project. We’ll process, index, and store it for Q&A, summaries, and quizzes.
      </p>

      {/* Step indicators */}
      <ol className="flex items-center gap-4 text-sm mb-6">
        {["Select file", "Upload & ingest", "Saved & ready"].map((step, i) => (
          <li key={i} className="flex items-center gap-2">
            <span
              className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                (i === 0 && file) || (i === 1 && loading) || (i === 2 && result)
                  ? "bg-amber-400 text-black"
                  : "bg-white/10"
              }`}
            >
              {i + 1}
            </span>
            {step}
          </li>
        ))}
      </ol>

      {/* Dropzone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          onFilePicked(e.dataTransfer.files?.[0] ?? null);
        }}
        className={`p-6 border border-dashed rounded-xl transition-all ${
          dragOver ? "border-amber-400 bg-amber-400/10" : "border-white/20"
        }`}
      >
        <p className="font-medium">Drag & drop your PDF here</p>
        <p className="text-sm opacity-80">or</p>
        <div className="mt-3 flex items-center gap-3">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="rounded-xl bg-amber-400 px-4 py-2 text-black font-medium hover:brightness-95"
          >
            Choose file
          </button>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            onChange={(e) => onFilePicked(e.target.files?.[0] ?? null)}
            className="hidden"
          />
          {file && (
            <button
              type="button"
              onClick={() => {
                setFile(null);
                setResult(null);
                setErr(null);
              }}
              className="px-3 py-2 text-sm rounded-xl border border-white/20 hover:bg-white/5"
            >
              Clear
            </button>
          )}
        </div>

        {/* File chip */}
        {fileMeta && (
          <div className="mt-4 inline-flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm">
            <span className="font-medium">{fileMeta.name}</span>
            <span className="opacity-70">•</span>
            <span className="opacity-80">{fileMeta.size}</span>
          </div>
        )}
      </div>

      {/* Error */}
      {err && (
        <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm">
          {err}
        </div>
      )}

      {/* Submit */}
      <form onSubmit={onSubmit} className="mt-4 space-y-4">
        <button
          type="submit"
          disabled={!file || loading}
          className="inline-flex items-center gap-2 rounded-xl bg-amber-400 px-4 py-2 text-black font-semibold disabled:opacity-60 hover:brightness-95"
        >
          {loading ? "Processing…" : "Process PDF"}
        </button>
        {loading && (
          <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
            <div className="h-full w-2/3 animate-pulse bg-amber-400/70" />
          </div>
        )}
      </form>

      {/* Result */}
      {result && (
        <div className="mt-6 rounded-xl border border-white/10 p-4 bg-white/5">
          <p className="opacity-80 mb-2">Ingested:</p>
          <ul className="space-y-1 text-sm">
            <li><b>doc_id:</b> {result.doc_id}</li>
            <li><b>title:</b> {result.title}</li>
            <li><b>pages:</b> {result.pages}</li>
            <li><b>chunks:</b> {result.chunks}</li>
          </ul>
        </div>
      )}
    </div>
  );
}
