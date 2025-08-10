"use client";
import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { QuizForm } from "@/components/QuizForm";

type Doc = { doc_id: string; title?: string };
type Quiz = { quiz_id: string; questions: { id:string; stem:string; options:{id:string; text:string}[]; multi?:boolean }[] };
type Grade = { score:number; per_question: { id:string; correct_option_ids:string[]; rationale:string; options:{id:string; text:string; selected:boolean; correct:boolean}[] }[] };

export default function QuizPage(){
  const [docId, setDocId] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [quiz, setQuiz] = useState<Quiz|null>(null);
  const [result, setResult] = useState<Grade|null>(null);

  // docs for dropdown
  const { data: docs = [] } = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.get<Doc[]>("/documents"),
  });
  useEffect(() => {
    if (!docId && docs.length > 0) setDocId(docs[0].doc_id);
  }, [docs, docId]);

  const gen = useMutation({
    mutationFn: async () => api.post<Quiz>("/quiz/generate", { doc_id: docId, n_questions: 10, type: "checkbox"}),
    onSuccess: (q) => { setQuiz(q); setResult(null); },
  });

  const grade = useMutation({
    mutationFn: async (answers: {question_id:string; option_ids:string[]}[]) =>
      api.post<Grade>("/quiz/grade", { quiz_id: quiz!.quiz_id, answers }),
    onSuccess: setResult,
  });

  const selected = docs.find(d=>d.doc_id===docId);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Quiz</h1>

        {/* Dropdown document picker */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(o=>!o)}
            className="px-3 py-2 rounded-xl border border-white/15 bg-midnight/60 hover:bg-midnight/80"
          >
            {selected?.title || docId || "Select document"}
          </button>
          {menuOpen && (
            <div className="absolute top-full right-0 mt-2 w-72 max-h-64 overflow-auto
                            bg-midnight/95 border border-white/10 rounded-xl shadow-xl p-2 z-10">
              {docs.map(d=>(
                <button
                  key={d.doc_id}
                  onClick={()=>{ setDocId(d.doc_id); setMenuOpen(false); }}
                  className={`w-full text-left px-3 py-2 rounded-lg hover:bg-white/10 ${d.doc_id===docId ? "bg-white/10":""}`}
                >
                  <div className="text-sm font-medium">{d.title || d.doc_id}</div>
                  <div className="text-xs opacity-70">{d.doc_id}</div>
                </button>
              ))}
              {docs.length===0 && <div className="px-3 py-2 text-sm opacity-70">No documents found.</div>}
            </div>
          )}
        </div>
      </div>

      <div className="flex gap-2">
        <button onClick={()=>gen.mutate()} className="s-btn-amber">Generate 10‑Q Quiz</button>
      </div>

      {quiz && (
        <div className="s-card p-4">
          <QuizForm
            quiz={quiz}
            onSubmit={(a)=>grade.mutate(a)}
            submitting={grade.isPending}
            results={result}
          />
        </div>
      )}
    </div>
  );
}
