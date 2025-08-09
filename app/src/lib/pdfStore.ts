// lib/pdfStore.ts
"use client";
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

type Doc = { docId: string; title: string; url?: string } | null;

type PdfState = {
  current: Doc;
  setDoc: (doc: NonNullable<Doc>) => void;
  clear: () => void;
};

export const usePdfStore = create<PdfState>()(
  persist(
    (set) => ({
      current: null,
      setDoc: (doc) => set({ current: doc }),
      clear: () => set({ current: null })
    }),
    {
      name: "siraj:pdf",
      storage: createJSONStorage(() => localStorage),
      // Persist only durable fields; drop transient blob URLs
      partialize: (s) =>
        s.current
          ? { current: { docId: s.current.docId, title: s.current.title } }
          : { current: null }
    }
  )
);
