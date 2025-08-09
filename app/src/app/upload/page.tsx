"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PDFViewer } from "@/components/PDFViewer";
import { cn } from "@/lib/utils";

export default function UploadPage(){
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const { mutate, isPending, data } = useMutation({
    mutationFn: async () => {
      if(!file) throw new Error("No file selected");
      const form = new FormData();
      form.append("file", file);
      return api.post<{doc_id:string; title:string; pages:number; chunks:number}>("/ingest", form, true);
    }
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Upload Resources</h1>
      <div className="s-card p-4 grid gap-4">
        <input
          type="file"
          accept="application/pdf"
          onChange={(e)=>{
            const f = e.target.files?.[0] || null;
            setFile(f);
            setPreviewUrl(f ? URL.createObjectURL(f) : null);
          }}
          className="file:mr-4 file:py-2 file:px-4 file:rounded-2xl file:border-0 file:bg-amberGlow file:text-midnight hover:file:opacity-90"
        />
        <button disabled={!file || isPending} onClick={()=>mutate()} className={cn("s-btn-amber w-fit", isPending && "opacity-70")}>Process Resources</button>
        {data && (
          <div className="text-sm text-sandLight/80">Ingested: {data.chunks} chunks • Pages: {data.pages}</div>
        )}
      </div>
      {previewUrl && (
        <div className="s-card p-4">
          <PDFViewer url={previewUrl}/>
        </div>
      )}
    </div>
  );
}
