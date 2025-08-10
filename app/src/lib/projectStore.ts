// app/src/lib/projectStore.ts
"use client";
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { api } from "@/lib/api";

export type Project = {
  id: string;
  title: string;
  path?: string;           // manifest path (absolute on server)
  brainrot_enabled?: boolean;
};

type State = {
  current: Project | null;
  list: Project[];
  setCurrent: (p: Project | null) => void;
  refreshList: () => Promise<void>;
  save: (p: { id: string; title: string; brainrot_enabled?: boolean; description?: string }) => Promise<Project>;
  open: (manifestPath: string) => Promise<Project>;
};

export const useProjectStore = create<State>()(
  persist(
    (set, get) => ({
      current: null,
      list: [],
      setCurrent: (p) => set({ current: p }),
      refreshList: async () => {
        const res = await api.get<{projects: {id:string; title:string; path:string}[]}>("/projects");
        set({ list: res.projects.map(p => ({ id: p.id, title: p.title, path: p.path })) });
      },
      save: async (p) => {
        const res = await api.post<{ project: Project }>("/projects/save", p);
        set({ current: res.project });
        await get().refreshList();
        return res.project;
      },
      open: async (manifestPath) => {
        const res = await api.post<{ project: Project }>("/projects/open", { path: manifestPath });
        set({ current: res.project });
        await get().refreshList();
        return res.project;
      },
    }),
    {
      name: "siraj:project",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ current: s.current }), // keep it light
    }
  )
);
