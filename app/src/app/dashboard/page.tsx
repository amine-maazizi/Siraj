"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

export default function Dashboard(){
  const { data } = useQuery({ queryKey:["progress"], queryFn: async ()=> api.get("/progress") });
  const hist = data?.history || [];
  const completion = data?.totals?.avgScore || 0;
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="s-card p-4 h-64">
          <div className="text-sm mb-2">Scores Over Time</div>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={hist}>
              <XAxis dataKey="date" hide/>
              <YAxis domain={[0,100]} hide/>
              <Tooltip/>
              <Line type="monotone" dataKey="score" stroke="#FFB454" strokeWidth={2} dot={false}/>
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="s-card p-4 h-64 flex items-center justify-center">
          <div className="w-64 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={[{name:"complete", value: completion}, {name:"rest", value: 100-completion}]} dataKey="value" outerRadius={100}>
                  <Cell fill="#FFB454"/>
                  <Cell fill="#1A0E2E"/>
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}