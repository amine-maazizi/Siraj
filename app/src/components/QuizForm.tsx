"use client";
import { useMemo, useState } from "react";

type Option = { id: string; text: string };
type Question = { id: string; stem: string; options: Option[]; multi?: boolean };

type Quiz = { quiz_id: string; questions: Question[] };

type PerOptionResult = { id: string; text: string; selected: boolean; correct: boolean };
type PerQuestionResult = { id: string; correct_option_ids: string[]; rationale: string; options: PerOptionResult[] };

export function QuizForm({
  quiz,
  onSubmit,
  submitting,
  results,
}: {
  quiz: Quiz;
  onSubmit: (answers: {question_id:string; option_ids:string[]}[]) => void;
  submitting?: boolean;
  results?: { score: number; per_question: PerQuestionResult[] } | null;
}) {
  const [state, setState] = useState<Record<string, Set<string>>>({});

  const toggle = (qid: string, oid: string) => {
    setState(prev => {
      const s = new Set(prev[qid] || []);
      if (s.has(oid)) s.delete(oid); else s.add(oid);
      return { ...prev, [qid]: s };
    });
  };

  const submit = () => {
    const answers = quiz.questions.map(q => ({
      question_id: q.id,
      option_ids: Array.from(state[q.id] || []),
    }));
    onSubmit(answers);
  };

  const resByQ = useMemo(() => {
    const map = new Map<string, PerQuestionResult>();
    results?.per_question?.forEach(r => map.set(r.id, r));
    return map;
  }, [results]);

  return (
    <div className="space-y-6">
      {quiz.questions.map((q, qi) => {
        const correction = resByQ.get(q.id);
        return (
          <div key={q.id} className="rounded-xl p-4 bg-midnight/60 border border-white/10">
            <div className="font-semibold mb-2">Q{qi+1}. {q.stem}</div>
            <div className="grid gap-2">
              {q.options.map(o => {
                const selected = (state[q.id]?.has(o.id)) ?? false;
                // correction view
                const corOpt = correction?.options.find(x => x.id === o.id);
                const showCorrection = !!correction;
                const isCorrect = corOpt?.correct ?? false;
                const wasSelected = corOpt?.selected ?? selected;

                return (
                  <label key={o.id} className={
                    "flex items-start gap-3 rounded-lg px-3 py-2 border " +
                    (showCorrection
                      ? (isCorrect
                          ? "border-green-500/40 bg-green-500/10"
                          : (wasSelected ? "border-red-500/40 bg-red-500/10" : "border-white/10 bg-white/5"))
                      : "border-white/10 hover:bg-white/5")
                  }>
                    {!showCorrection ? (
                      <input
                        type="checkbox"
                        className="mt-1"
                        checked={selected}
                        onChange={() => toggle(q.id, o.id)}
                      />
                    ) : (
                      <span className="mt-0.5 text-lg">
                        {wasSelected
                          ? (isCorrect ? "✓" : "✗")
                          : (isCorrect ? "✓" : "•")}
                      </span>
                    )}
                    <span className="leading-snug">{o.id}. {o.text}</span>
                  </label>
                );
              })}
            </div>

            {correction && (
              <div className="mt-3 text-sm text-sandLight/80">
                <div className="opacity-80">Correct answer(s): {correction.correct_option_ids.join(", ")}</div>
                <div className="mt-1">{correction.rationale}</div>
              </div>
            )}
          </div>
        );
      })}

      {!results && (
        <div className="flex justify-end">
          <button onClick={submit} disabled={submitting} className="s-btn-amber">
            {submitting ? "Grading…" : "Submit"}
          </button>
        </div>
      )}

      {results && (
        <div className="text-right text-lg">
          Score: <span className="text-goldHi font-semibold">{results.score}%</span>
        </div>
      )}
    </div>
  );
}
