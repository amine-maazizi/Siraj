"use client";
import { useEffect, useRef } from "react";
import * as pdfjsLib from "pdfjs-dist";
import "pdfjs-dist/build/pdf.worker.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc = "pdfjs-dist/build/pdf.worker.mjs" as any;

export function PDFViewer({ url }: { url: string }){
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(()=>{
    let cancelled = false;
    (async()=>{
      const pdf = await (pdfjsLib as any).getDocument(url).promise;
      const page = await pdf.getPage(1);
      const viewport = page.getViewport({ scale: 1.2 });
      const canvas = canvasRef.current!;
      const ctx = canvas.getContext("2d")!;
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      await page.render({ canvasContext: ctx, viewport }).promise;
      if(cancelled){ ctx.clearRect(0,0,canvas.width,canvas.height); }
    })();
    return ()=>{ cancelled = true; };
  },[url]);

  return <canvas ref={canvasRef} className="rounded-xl overflow-hidden"/>;
}
