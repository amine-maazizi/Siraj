"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function Recommendations(){
  const { data } = useQuery({
    queryKey: ["suggest"],
    queryFn: async ()=> api.post("/suggest", { gaps: ["placeholder"], time_per_day: 30, horizon_weeks: 4 })
  });
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Recommendations</h1>
      <div className="grid sm:grid-cols-2 gap-4">
        {data?.resources?.map((r:any,i:number)=> (
          <div key={i} className="s-card p-4">
            <div className="font-medium text-goldHi">{r.title}</div>
            <div className="text-sm text-sandLight/80">{r.type}</div>
          </div>
        ))}
      </div>
    </div>
  );
}