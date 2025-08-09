"use client";

import { useState } from "react";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setResult(null);
    if (!file) {
      setErr("Choose a PDF first.");
      return;
    }
    const form = new FormData();
    form.append("file", file);

    setLoading(true);
    try {
      // proxies to FastAPI: POST /ingest
      const res = await fetch("/proxy?path=/ingest", { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      setResult(json);
    } catch (e: any) {
      setErr(e.message ?? "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">Upload & Ingest</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-sm file:mr-4 file:py-2 file:px-4
                     file:rounded-full file:border-0 file:text-sm file:font-semibold
                     file:bg-amber-200 hover:file:bg-amber-300"
        />
        <button
          type="submit"
          disabled={loading || !file}
          className="px-4 py-2 rounded-xl bg-amber-400 text-black disabled:opacity-50"
        >
          {loading ? "Processing..." : "Process PDF"}
        </button>
      </form>

      {err && <p className="text-red-400 mt-4">{err}</p>}
      {result && (
        <div className="mt-6 rounded-xl border border-white/10 p-4">
          <p className="opacity-80">Ingested:</p>
          <ul className="mt-2 space-y-1">
            <li><b>doc_id</b>: {result.doc_id}</li>
            <li><b>title</b>: {result.title}</li>
            <li><b>pages</b>: {result.pages}</li>
            <li><b>chunks</b>: {result.chunks}</li>
          </ul>
        </div>
      )}
    </div>
  );
}
