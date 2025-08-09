"use client";
import { useForm } from "react-hook-form";

export function QuizForm({ quiz, onSubmit, submitting }: { quiz: any; onSubmit: (answers:{question_id:string; option_ids:string[]}[])=>void; submitting:boolean }){
  const { register, handleSubmit, watch } = useForm();
  const submit = (data:any)=>{
    const answers = quiz.questions.map((q:any)=> ({
      question_id: q.id,
      option_ids: Object.entries(data).filter(([k,v])=> k.startsWith(q.id+"_") && v===true).map(([k])=> k.split("_")[1])
    }));
    onSubmit(answers);
  };

  return (
    <form onSubmit={handleSubmit(submit)} className="grid gap-4">
      {quiz.questions.map((q:any, i:number)=> (
        <div key={q.id} className="p-4 rounded-xl bg-midnight/60 border border-white/10">
          <div className="font-medium mb-2">{i+1}. {q.stem}</div>
          <div className="grid gap-2">
            {q.options.map((op:any)=> (
              <label key={op.id} className="flex items-center gap-2">
                <input type="checkbox" {...register(`${q.id}_${op.id}`)} className="accent-amberGlow"/>
                <span>{op.text}</span>
              </label>
            ))}
          </div>
        </div>
      ))}
      <button disabled={submitting} className="s-btn-amber w-fit">{submitting?"Grading…":"Submit"}</button>
    </form>
  );
}
