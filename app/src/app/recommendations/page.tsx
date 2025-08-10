// app/src/app/recommendations/page.tsx
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

type ReviewWrongItem = { stem: string };
type ReviewDoc = { wrong: ReviewWrongItem[]; title: string; doc_id: string; attempt_id: number };
type ReviewResponse = { reviews: ReviewDoc[] };

type SuggestReq = { gaps: string[]; time_per_day: number; horizon_weeks: number };
type Task = { text: string; reason?: string; effort_min?: number };
type Resource = { title: string; type?: string; provider?: string; price?: string; link?: string; embed_url?: string };
type SuggestResp = { tasks: Task[]; resources: Resource[] };

const uniq = (arr: string[]) => Array.from(new Set(arr.map((s) => s.trim()).filter(Boolean)));

export default function Recommendations() {
  const [selectedGaps, setSelectedGaps] = useState<string[]>([]);
  const [tpd, setTpd] = useState<number>(30);
  const [weeks, setWeeks] = useState<number>(4);

  // 1) Fetch weak topics
  const {
    data: review,
    isLoading: loadingReview,
    isError: reviewErr,
    refetch: refetchReview,
  } = useQuery({
    queryKey: ["review"],
    queryFn: async (): Promise<ReviewResponse> => api.get("/review"),
    staleTime: 30_000,
  });

  // 2) Derive candidate gaps
  const inferredGaps = useMemo(() => {
    const stems = review?.reviews.flatMap((r) => r.wrong?.map((w) => w.stem) ?? []) ?? [];
    const filtered = stems
      .map((s) => s.trim())
      .filter(Boolean)
      .filter((s) => s.length <= 100)
      .filter((s) => !/\b(PubMed|INRIA|Research Report|\d{4};|\[\d+\])\b/i.test(s));
    return uniq(filtered).slice(0, 12);
  }, [review]);

  useEffect(() => {
    if (inferredGaps.length && selectedGaps.length === 0) {
      setSelectedGaps(inferredGaps.slice(0, 3));
    }
  }, [inferredGaps, selectedGaps.length]);

  // 3) Call /suggest
  const suggest = useMutation({
    mutationFn: async (): Promise<SuggestResp> =>
      api.post("/suggest", {
        gaps: selectedGaps,
        time_per_day: tpd,
        horizon_weeks: weeks,
      } as SuggestReq),
  });

  const toggleGap = (g: string) => {
    setSelectedGaps((prev) => (prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g]));
  };

  return (
    // Keep page from creating a global bottom scrollbar
    <div className="space-y-6 overflow-x-hidden">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Suggestions</h1>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={5}
            max={60}
            value={tpd}
            onChange={(e) => setTpd(Math.max(5, Math.min(60, Number(e.target.value) || 30)))}
            className="w-20 rounded-md border px-2 py-1 text-sm"
            aria-label="Time per day (minutes)"
            title="Time per day (minutes)"
          />
          <input
            type="number"
            min={1}
            max={12}
            value={weeks}
            onChange={(e) => setWeeks(Math.max(1, Math.min(12, Number(e.target.value) || 4)))}
            className="w-20 rounded-md border px-2 py-1 text-sm"
            aria-label="Horizon (weeks)"
            title="Horizon (weeks)"
          />
          <button
            onClick={() => suggest.mutate()}
            disabled={selectedGaps.length === 0 || suggest.isPending}
            className={`rounded-xl px-3 py-1.5 text-sm font-medium shadow ${
              selectedGaps.length === 0 || suggest.isPending
                ? "bg-gray-300 text-gray-600 cursor-not-allowed"
                : "bg-amber-400 text-black hover:bg-amber-300"
            }`}
          >
            {suggest.isPending ? "Generating…" : "Generate"}
          </button>
        </div>
      </div>

      <div className="s-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Pick gaps to focus</h2>
          <div className="flex gap-2">
            <button className="rounded-md border px-2 py-1 text-xs hover:bg-muted" onClick={() => refetchReview()}>
              Refresh weak topics
            </button>
            <button className="rounded-md border px-2 py-1 text-xs hover:bg-muted" onClick={() => setSelectedGaps([])}>
              Clear
            </button>
          </div>
        </div>

        {loadingReview && <div className="animate-pulse text-sm text-muted-foreground">Loading weak topics…</div>}
        {reviewErr && <div className="text-sm text-red-500">Could not load weak topics from /review.</div>}

        <div className="flex flex-wrap gap-2">
          {inferredGaps.length === 0 && !loadingReview && (
            <span className="text-sm text-muted-foreground">
              No weak topics yet. Take a quiz, or type gaps manually below.
            </span>
          )}
          {inferredGaps.map((g) => (
            <button
              key={g}
              onClick={() => toggleGap(g)}
              className={`rounded-full border px-3 py-1 text-sm transition
                ${
                  selectedGaps.includes(g)
                    ? "bg-amber-400 border-amber-400 text-black"
                    : "border-amber-300 text-amber-800 hover:bg-amber-50 dark:text-amber-200 dark:hover:bg-amber-900/30"
                }`}
              title={g}
            >
              {selectedGaps.includes(g) ? "✓ " : ""}
              {g}
            </button>
          ))}
        </div>

        <ManualAdd onAdd={(g) => setSelectedGaps((prev) => uniq([...prev, g]))} />
      </div>

      {suggest.isError && (
        <div className="s-card p-4 text-red-600">{(suggest.error as any)?.message ?? "Failed to fetch suggestions."}</div>
      )}

      {suggest.data && (
        <>
          <div className="s-card p-4 space-y-2">
            <h2 className="font-semibold">To-dos</h2>
            <ul className="space-y-2">
              {suggest.data.tasks.map((t, i) => (
                <li key={i} className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    id={`task-${i}`}
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-amber-500 focus:ring-amber-400"
                  />
                  <label htmlFor={`task-${i}`} className="text-sm">
                    <span className="font-medium">{t.text}</span>
                    {t.reason || t.effort_min ? (
                      <span className="ml-1 text-muted-foreground">
                        — {[t.reason, t.effort_min ? `${t.effort_min} min` : ""].filter(Boolean).join(" • ")}
                      </span>
                    ) : null}
                  </label>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources — Amazon‑style button-driven carousel */}
          <div className="s-card p-4 space-y-2">
            <h2 className="font-semibold">Resources</h2>
            <ResourceCarousel items={suggest.data.resources} />
          </div>
        </>
      )}
    </div>
  );
}

function ManualAdd({ onAdd }: { onAdd: (g: string) => void }) {
  const [val, setVal] = useState("");
  return (
    <div className="flex gap-2">
      <input
        value={val}
        onChange={(e) => setVal(e.target.value)}
        placeholder="Add a custom gap (e.g., Newton’s 2nd Law)"
        className="flex-1 rounded-md border px-3 py-1.5 text-sm"
      />
      <button
        onClick={() => {
          const v = val.trim();
          if (v) {
            onAdd(v);
            setVal("");
          }
        }}
        className="rounded-md border px-3 py-1.5 text-sm hover:bg-muted"
      >
        Add
      </button>
    </div>
  );
}

function ResourceCarousel({ items }: { items: Resource[] }) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [atStart, setAtStart] = useState(true);
  const [atEnd, setAtEnd] = useState(false);

  const CARD_WIDTH = 256; // w-64 in px
  const GAP = 12;         // gap-3 in px
  const STEP = CARD_WIDTH + GAP;

  const updateArrows = () => {
    const el = trackRef.current;
    if (!el) return;
    const { scrollLeft, scrollWidth, clientWidth } = el;
    const max = Math.max(0, scrollWidth - clientWidth - 1);
    setAtStart(scrollLeft <= 0);
    setAtEnd(scrollLeft >= max);
  };

  const scrollByPx = (dx: number) => {
    trackRef.current?.scrollBy({ left: dx, behavior: "smooth" });
  };

  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;
    updateArrows();
    const onScroll = () => requestAnimationFrame(updateArrows);
    const ro = new ResizeObserver(updateArrows);
    el.addEventListener("scroll", onScroll, { passive: true });
    ro.observe(el);
    return () => {
      el.removeEventListener("scroll", onScroll);
      ro.disconnect();
    };
  }, []);

  return (
    <div className="relative">
      {/* cropped viewport */}
      <div
        className="overflow-hidden"
        style={{ maxWidth: `${(CARD_WIDTH + GAP) * 3 - GAP}px` }} // show 3 cards
      >
        <div
          ref={trackRef}
          className="flex gap-3 overflow-x-auto overflow-y-hidden scroll-smooth snap-x snap-mandatory pb-2 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          {items.map((r, i) => (
            <a
              key={i}
              href={r.link || "#"}
              target="_blank"
              rel="noopener noreferrer"
              className="snap-start shrink-0 w-64 rounded-xl border p-3 hover:bg-muted focus:outline-none focus:ring-2 focus:ring-amber-400"
            >
              <div className="font-medium line-clamp-2">{r.title}</div>
              <div className="mt-1 text-xs text-muted-foreground">
                {[r.type, r.provider, r.price].filter(Boolean).join(" • ")}
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* controls */}
      <button
        type="button"
        aria-label="Previous"
        onClick={() => scrollByPx(-STEP)}
        disabled={atStart}
        className="absolute -left-5 top-1/2 -translate-y-1/2 rounded-full border shadow p-2 bg-background/80 backdrop-blur hover:bg-muted disabled:opacity-40"
      >
        ‹
      </button>
      <button
        type="button"
        aria-label="Next"
        onClick={() => scrollByPx(STEP)}
        disabled={atEnd}
        className="absolute -right-5 top-1/2 -translate-y-1/2 rounded-full border shadow p-2 bg-background/80 backdrop-blur hover:bg-muted disabled:opacity-40"
      >
        ›
      </button>
    </div>
  );
}
