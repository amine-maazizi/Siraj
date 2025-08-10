"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { QuizForm } from "@/components/QuizForm";

type Doc = { doc_id: string; title?: string };

type QuizOption = { id: string; text: string };
type QuizQuestion = { id: string; stem: string; options: QuizOption[]; multi?: boolean };
type Quiz = { quiz_id: string; doc_id: string; questions: QuizQuestion[] };

type GradeOptionResult = { id: string; text: string; selected: boolean; correct: boolean };
type GradePerQ = {
  id: string;
  correct_option_ids: string[];
  rationale: string;
  options: GradeOptionResult[];
};
type Grade = { score: number; per_question: GradePerQ[] };

type Attempt = { id: number; quiz_id: string; doc_id: string; score: number; created_at: string };

export default function QuizPage() {
  const qc = useQueryClient();
  const [docId, setDocId] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [result, setResult] = useState<Grade | null>(null);

  // documents for dropdown
  const { data: docs = [], isLoading: docsLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.get<Doc[]>("/documents"),
  });

  useEffect(() => {
    if (!docId && docs.length > 0) setDocId(docs[0].doc_id);
  }, [docs, docId]);

  // attempts history for the selected doc
  const { data: attempts = [] } = useQuery({
    queryKey: ["quiz_attempts", docId],
    queryFn: () => api.get<Attempt[]>(`/quiz/attempts${docId ? `?doc_id=${encodeURIComponent(docId)}` : ""}`),
    enabled: !!docId,
    staleTime: 10_000,
  });

  const selected = useMemo(() => docs.find((d) => d.doc_id === docId), [docs, docId]);

  // generate quiz
  const gen = useMutation({
    mutationFn: async () =>
      api.post<Quiz>("/quiz/generate", { doc_id: docId, n_questions: 10, type: "checkbox" }),
    onSuccess: (q) => {
      setQuiz(q);
      setResult(null);
    },
  });

  // grade quiz
  const grade = useMutation({
    mutationFn: async (answers: { question_id: string; option_ids: string[] }[]) =>
      api.post<Grade>("/quiz/grade", { quiz_id: quiz!.quiz_id, answers }),
    onSuccess: (res) => {
      setResult(res);
      // refresh attempts list so the new one shows up
      qc.invalidateQueries({ queryKey: ["quiz_attempts", docId] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Quiz</h1>
          <p className="text-sm opacity-70">Auto‑generated, graded, and saved locally.</p>
        </div>

        {/* Dropdown document picker */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="px-3 py-2 rounded-xl border border-white/15 bg-midnight/60 hover:bg-midnight/80"
            disabled={docsLoading || docs.length === 0}
          >
            {selected?.title || selected?.doc_id || (docsLoading ? "Loading…" : "Select document")}
          </button>
          {menuOpen && (
            <div
              className="absolute top-full right-0 mt-2 w-80 max-h-64 overflow-auto
                            bg-midnight/95 border border-white/10 rounded-xl shadow-xl p-2 z-10"
            >
              {docs.map((d) => (
                <button
                  key={d.doc_id}
                  onClick={() => {
                    setDocId(d.doc_id);
                    setMenuOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 rounded-lg hover:bg-white/10 ${
                    d.doc_id === docId ? "bg-white/10" : ""
                  }`}
                >
                  <div className="text-sm font-medium">{d.title || d.doc_id}</div>
                  <div className="text-xs opacity-70">{d.doc_id}</div>
                </button>
              ))}
              {docs.length === 0 && <div className="px-3 py-2 text-sm opacity-70">No documents found.</div>}
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => gen.mutate()}
          disabled={!docId || gen.isPending}
          className="s-btn-amber"
        >
          {gen.isPending ? "Generating…" : "Generate Quiz"}
        </button>

        {result && (
          <div className="text-sm opacity-80">
            Last score:&nbsp;
            <span className="font-semibold">{result.score}%</span>
          </div>
        )}
      </div>

      {/* Attempts history */}
      {attempts.length > 0 && (
        <div className="s-card p-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold">Recent Attempts</h2>
            <span className="text-xs opacity-60">{attempts.length} saved</span>
          </div>
          <div className="space-y-1">
            {attempts.map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between text-sm px-3 py-2 rounded-lg bg-white/5"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs opacity-60">#{a.id}</span>
                  <span className="opacity-80">{new Date(a.created_at).toLocaleString()}</span>
                </div>
                <div className="font-semibold">{a.score}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quiz + Results */}
      {quiz && (
        <div className="s-card p-4">
          <QuizForm
            quiz={quiz}
            onSubmit={(a) => grade.mutate(a)}
            submitting={grade.isPending}
            results={result || undefined}
          />
        </div>
      )}
    </div>
  );
}
