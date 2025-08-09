"use client";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { QuizForm } from "@/components/QuizForm";


export default function QuizPage(){
  const [docId, setDocId] = useState("");
  const [quiz, setQuiz] = useState<any>(null);
  const [result, setResult] = useState<any>(null);

  const gen = useMutation({
    mutationFn: async () => api.post("/quiz/generate", { doc_id: docId, n_questions: 6, type: "checkbox"}),
    onSuccess: setQuiz
  });

  const grade = useMutation({
    mutationFn: async (answers: {question_id:string; option_ids:string[]}[]) => api.post("/quiz/grade", { quiz_id: quiz.quiz_id, answers }),
    onSuccess: setResult
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Quiz</h1>
      <div className="flex gap-2">
        <input value={docId} onChange={e=>setDocId(e.target.value)} placeholder="doc_id" className="bg-transparent border rounded-xl px-3 py-2 border-white/15 w-40"/>
        <button onClick={()=>gen.mutate()} className="s-btn-amber">Generate Quiz</button>
      </div>
      {quiz && (
        <div className="s-card p-4">
          <QuizForm quiz={quiz} onSubmit={(a)=>grade.mutate(a)} submitting={grade.isPending}/>
        </div>
      )}
      {result && (
        <div className="s-card p-4">
          <div className="text-xl">Score: <span className="text-goldHi font-semibold">{result.score}%</span></div>
          <div className="mt-3 grid gap-2">
            {result.per_question?.map((q:any)=> (
              <div key={q.id} className="p-3 rounded-xl bg-midnight/60">
                <div className="font-medium">Q{q.id}</div>
                <div className="text-sandLight/80 text-sm">{q.rationale}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
