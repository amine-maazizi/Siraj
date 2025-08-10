// app/src/app/review/page.tsx
"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Types aligned with backend payload
type ReviewWrongItem = {
  question_id: string;
  stem: string;
  selected_texts: string[];
  correct_texts: string[];
  explanation: string;
  related_pages: number[];
};

type ReviewDoc = {
  doc_id: string;
  title: string;
  attempt_id: number;
  score: number;
  taken_at: string;
  wrong: ReviewWrongItem[];
};

type ReviewResponse = { reviews: ReviewDoc[] };

async function fetchReview(): Promise<ReviewResponse> {
  // Use the proxy wrapper (do NOT hardcode http://localhost:8000 here)
  return api.get<ReviewResponse>("/review");
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium">
      {children}
    </span>
  );
}

export default function ReviewPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["review"],
    queryFn: fetchReview,
    staleTime: 30_000,
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Review</h1>
        <button
          onClick={() => refetch()}
          className="rounded-xl bg-amber-400 px-3 py-1.5 text-sm font-medium text-black shadow hover:bg-amber-300"
        >
          Refresh
        </button>
      </div>

      {isLoading && <div className="s-card p-4 animate-pulse">Loading weak topics…</div>}
      {isError && <div className="s-card p-4 text-red-500">Could not load review. Try again.</div>}

      {!isLoading && !isError && (!data || data.reviews.length === 0) && (
        <div className="s-card p-4">
          Weak topics will appear here after you take a quiz. Once you submit,
          we’ll pull the latest attempt for each file and list explanations with PDF links.
        </div>
      )}

      {data?.reviews.map((doc) => (
        <div key={doc.doc_id} className="s-card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">{doc.title}</h2>
              <p className="text-xs text-muted-foreground">
                Latest attempt #{doc.attempt_id} • Score {Math.round(doc.score)}%
              </p>
            </div>
            <Badge>{doc.wrong.length} to review</Badge>
          </div>

          <div className="space-y-3">
            {doc.wrong.map((w) => (
              <div key={w.question_id} className="rounded-xl border p-3">
                <div className="mb-1 text-sm font-medium">
                  Q{w.question_id}: {w.stem}
                </div>

                <div className="grid gap-2 md:grid-cols-2">
                  <div className="rounded-lg bg-[#8B1E3F] text-white p-2 text-sm">
                    <div className="font-semibold">Your answer</div>
                    <ul className="list-disc pl-5">
                      {w.selected_texts.length > 0 ? (
                        w.selected_texts.map((t, i) => <li key={i}>{t}</li>)
                      ) : (
                        <li>(No selection)</li>
                      )}
                    </ul>
                  </div>
                  <div className="rounded-lg bg-[#2E7D32] text-white p-2 text-sm">
                    <div className="font-semibold">Correct answer</div>
                    <ul className="list-disc pl-5">
                      {w.correct_texts.map((t, i) => (
                        <li key={i}>{t}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="mt-2 text-sm leading-relaxed">
                  <span className="font-semibold">Why:</span> {w.explanation}
                </div>

                {w.related_pages.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {w.related_pages.map((p) => (
                      <a
                        key={p}
                        href={`/pdf/${doc.doc_id}#page=${p}`}
                        className="rounded-md border px-2 py-1 text-xs hover:bg-muted"
                      >
                        Open PDF p.{p}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
