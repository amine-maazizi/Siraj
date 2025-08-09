// components/PDFViewer.tsx
"use client";
import { useEffect, useRef } from "react";
import { usePdfStore } from "@/lib/pdfStore";
import { loadPdf } from "@/lib/pdfDb";

export function PDFViewer() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const current = usePdfStore((s) => s.current);

  useEffect(() => {
    let cancelled = false;
    let renderingTask: any | null = null;
    let objectUrl: string | null = null;

    if (!current?.docId) return;

    (async () => {
      // Try local-first
      const local = await loadPdf(current.docId);
      const url = local
        ? (objectUrl = URL.createObjectURL(local))
        : `/proxy?path=/files/${current.docId}`; // fallback to backend

      const pdfjsLib = await import("pdfjs-dist/build/pdf.mjs");
      (pdfjsLib as any).GlobalWorkerOptions.workerSrc = "/pdf.worker.mjs";
      const loadingTask = (pdfjsLib as any).getDocument(url);
      const pdf = await loadingTask.promise;
      const page = await pdf.getPage(1);
      const viewport = page.getViewport({ scale: 1.2 });

      const canvas = canvasRef.current!;
      const ctx = canvas.getContext("2d")!;
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      renderingTask = page.render({ canvasContext: ctx, viewport });
      await renderingTask.promise;

      if (cancelled) ctx.clearRect(0, 0, canvas.width, canvas.height);
    })().catch(console.error);

    return () => {
      cancelled = true;
      try { renderingTask?.cancel?.(); } catch {}
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [current?.docId]);

  return <canvas ref={canvasRef} className="rounded-xl overflow-hidden" />;
}
