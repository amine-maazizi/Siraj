// app/src/components/Topbar.tsx
"use client";
import { useEffect, useMemo, useState } from "react";
import { useProjectStore } from "@/lib/projectStore";
import clsx from "clsx";

export function Topbar() {
  const { current, list, setCurrent, refreshList, save, open } = useProjectStore();
  const [title, setTitle] = useState(current?.title ?? "Untitled Project");
  const [id, setId] = useState(current?.id ?? "untitled");
  const [menuOpen, setMenuOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadingList, setLoadingList] = useState(false);

  useEffect(() => {
    setTitle(current?.title ?? "Untitled Project");
    setId(current?.id ?? "untitled");
  }, [current]);

  useEffect(() => {
    (async () => {
      setLoadingList(true);
      await refreshList().catch(() => {});
      setLoadingList(false);
    })();
  }, [refreshList]);

  const canSave = title.trim().length > 0 && id.trim().length > 0;

  const doSave = async () => {
    if (!canSave || saving) return;
    setSaving(true);
    try {
      const proj = await save({ id: id.trim(), title: title.trim() });
      setCurrent(proj);
    } finally {
      setSaving(false);
    }
  };

  const doOpen = async (manifestPath: string) => {
    setMenuOpen(false);
    await open(manifestPath);
  };

  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-white/10 bg-midnight/60">
      <div className="flex items-center gap-3">
        {/* Project title + id (slug) */}
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          className="bg-transparent text-lg font-medium outline-none"
          placeholder="Project title"
        />
        <span className="text-white/40">/</span>
        <input
          value={id}
          onChange={e => setId(e.target.value.replace(/\s+/g, "-").toLowerCase())}
          className="bg-transparent text-sm outline-none text-white/70"
          placeholder="project-id"
        />
      </div>

      <div className="flex items-center gap-2 relative">
        {/* Load/Switch */}
        <button
          onClick={() => setMenuOpen(v => !v)}
          className="s-btn-neutral"
          aria-haspopup="menu"
          aria-expanded={menuOpen}
        >
          {current ? `Open (${current.title})` : "Open"}
        </button>

        {menuOpen && (
          <div className="absolute right-0 top-10 w-80 max-h-96 overflow-auto rounded-2xl border border-white/10 bg-black/70 backdrop-blur p-2 z-10">
            <div className="px-2 pb-2 text-xs text-white/60">Projects</div>
            {loadingList && <div className="px-3 py-2 text-sm text-white/60">Loading…</div>}
            {!loadingList && list.length === 0 && (
              <div className="px-3 py-2 text-sm text-white/60">No projects yet.</div>
            )}
            {!loadingList && list.map(p => (
              <button
                key={p.path}
                onClick={() => doOpen(p.path!)}
                className={clsx(
                  "w-full text-left px-3 py-2 rounded-xl hover:bg-white/5",
                  current?.id === p.id && "bg-white/5"
                )}
              >
                <div className="text-sm">{p.title}</div>
                <div className="text-xs text-white/40">{p.id}</div>
              </button>
            ))}
          </div>
        )}

        {/* Save */}
        <button
          onClick={doSave}
          className={clsx("s-btn-amber", !canSave && "opacity-50 pointer-events-none")}
          disabled={!canSave || saving}
        >
          {saving ? "Saving…" : "Save"}
        </button>
      </div>
    </header>
  );
}
