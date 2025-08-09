"use client";
import { useState } from "react";

export function Topbar(){
  const [project, setProject] = useState("Untitled Project");
  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-white/10 bg-midnight/60">
      <input value={project} onChange={e=>setProject(e.target.value)} className="bg-transparent text-lg font-medium outline-none"/>
      <button className="s-btn-amber">Save</button>
    </header>
  );
}