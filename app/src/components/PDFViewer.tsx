"use client";
import { useEffect, useRef } from "react";

export function PDFViewer({ url }: { url: string }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // Lazy import so SSR never touches pdfjs (prevents DOMMatrix errors)
      const pdfjs = await import("pdfjs-dist");
      await import("pdfjs-dist/build/pdf.worker.mjs");

      // @ts-ignore workerSrc typing is loose
      pdfjs.GlobalWorkerOptions.workerSrc = new URL(
        "pdfjs-dist/build/pdf.worker.mjs",
        import.meta.url
      ).toString();

      const pdf = await (pdfjs as any).getDocument(url).promise;
      const page = await pdf.getPage(1);
      const viewport = page.getViewport({ scale: 1.2 });

      const canvas = canvasRef.current!;
      const ctx = canvas.getContext("2d")!;
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      await page.render({ canvasContext: ctx, viewport }).promise;

      if (cancelled) ctx.clearRect(0, 0, canvas.width, canvas.height);
    })();
    return () => {
      cancelled = true;
    };
  }, [url]);

  return <canvas ref={canvasRef} className="rounded-xl overflow-hidden" />;
}
