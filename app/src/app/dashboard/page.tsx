"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ProgressResponse } from "@/types/api"; // or "@/shared/schemas" if you re-export

import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area,
  PieChart, Pie, Cell
} from "recharts";
import clsx from "clsx";

const AMBER = "#FFB454";
const BG_DARK = "#1A0E2E";

function StatCard({ label, value, suffix, sub }: { label: string; value: string | number; suffix?: string; sub?: string }) {
  return (
    <div className="rounded-2xl bg-[#2E1A47] border border-[#1A0E2E] p-4">
      <div className="text-xs text-gray-300">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-white">
        {value}{suffix}
      </div>
      {sub ? <div className="text-xs text-gray-400 mt-1">{sub}</div> : null}
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <div className="text-sm text-gray-200 mb-2">{children}</div>;
}

export default function ProgressPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["progress"],
    queryFn: async () => api.get<ProgressResponse>("/progress"),
  });

  const hist = data?.history ?? [];
  const totals = data?.totals ?? { docs: 0, quizzes: 0, avgScore: 0, streak: 0, trendDelta: 0 };
  const completion = totals?.avgScore ?? 0;

  const donutData = useMemo(
    () => [{ name: "complete", value: completion }, { name: "rest", value: Math.max(0, 100 - completion) }],
    [completion]
  );

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-6 w-48 bg-[#2E1A47] rounded" />
        <div className="grid lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="h-20 bg-[#2E1A47] rounded-2xl" />)}
        </div>
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="h-72 bg-[#2E1A47] rounded-2xl" />
          <div className="h-72 bg-[#2E1A47] rounded-2xl" />
        </div>
        <div className="h-40 bg-[#2E1A47] rounded-2xl" />
      </div>
    );
  }

  if (isError) {
    return <div className="text-red-400">Failed to load progress.</div>;
  }

  const trendSub =
    totals.trendDelta === 0
      ? "flat vs recent baseline"
      : totals.trendDelta > 0
      ? `up +${totals.trendDelta}`
      : `down ${totals.trendDelta}`;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-white">Progress</h1>

      {/* Totals */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Documents" value={totals.docs} />
        <StatCard label="Quizzes" value={totals.quizzes} />
        <StatCard label="Avg. Score" value={Math.round(totals.avgScore)} suffix="%" sub={trendSub} />
        <StatCard label="Streak" value={totals.streak} suffix=" 🔥" />
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-[#2E1A47] border border-[#1A0E2E] p-4 h-80">
          <SectionTitle>Scores Over Time</SectionTitle>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={hist} margin={{ left: -20, right: 0, top: 10, bottom: 0 }}>
              <defs>
                <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={AMBER} stopOpacity={0.35}/>
                  <stop offset="100%" stopColor={AMBER} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fill: "#F6E7CB", fontSize: 12 }} tickMargin={8}/>
              <YAxis domain={[0, 100]} tick={{ fill: "#F6E7CB", fontSize: 12 }}/>
              <Tooltip
                contentStyle={{ background: BG_DARK, border: "1px solid #2E1A47", borderRadius: 12, color: "#fff" }}
                labelStyle={{ color: "#F6E7CB" }}
              />
              <Area type="monotone" dataKey="score" stroke={AMBER} fill="url(#g1)" strokeWidth={2}/>
              <Line type="monotone" dataKey="score" stroke={AMBER} strokeWidth={2} dot={false}/>
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-2xl bg-[#2E1A47] border border-[#1A0E2E] p-4 h-80 flex items-center justify-center">
          <div className="w-64 h-64">
            <SectionTitle>Average Completion</SectionTitle>
            <ResponsiveContainer width="100%" height="85%">
              <PieChart>
                <Pie data={donutData} dataKey="value" outerRadius={100} innerRadius={60}>
                  <Cell fill={AMBER}/>
                  <Cell fill={BG_DARK}/>
                </Pie>
                {/* Optional: Tooltip could show exact % */}
              </PieChart>
            </ResponsiveContainer>
            <div className="text-center text-white -mt-8 text-xl font-semibold">{Math.round(completion)}%</div>
          </div>
        </div>
      </div>

      {/* History Table */}
      <div className="rounded-2xl bg-[#2E1A47] border border-[#1A0E2E] p-4">
        <SectionTitle>Recent Attempts</SectionTitle>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-gray-300">
                <th className="py-2 pr-4">Date</th>
                <th className="py-2 pr-4">Document</th>
                <th className="py-2 pr-4">Score</th>
              </tr>
            </thead>
            <tbody>
              {hist.slice(-12).map((h, i) => (
                <tr key={i} className={clsx("border-t border-[#1A0E2E]")}>
                  <td className="py-2 pr-4 text-white">{h.date}</td>
                  <td className="py-2 pr-4 text-gray-200">{h.doc ?? "—"}</td>
                  <td className="py-2 pr-4">
                    <span className={clsx(
                      "px-2 py-1 rounded-md text-white",
                      (h.score ?? 0) >= 70 ? "bg-green-700/50" : "bg-red-700/50"
                    )}>
                      {Math.round(h.score ?? 0)}%
                    </span>
                  </td>
                </tr>
              ))}
              {hist.length === 0 && (
                <tr>
                  <td className="py-4 text-gray-400" colSpan={3}>No attempts yet. Take a quiz to see your trend.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Gaps + Review */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-[#2E1A47] border border-[#1A0E2E] p-4">
          <SectionTitle>Weak Topics</SectionTitle>
          <ul className="space-y-2">
            {(data?.gaps ?? []).slice(0, 8).map((g, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-[#FFC94A] mt-0.5">📌</span>
                <div>
                  <div className="text-white">{g.topic}</div>
                  {g.note ? <div className="text-xs text-gray-300">{g.note}</div> : null}
                </div>
              </li>
            ))}
            {(data?.gaps ?? []).length === 0 && <li className="text-gray-400">No recurring gaps detected yet.</li>}
          </ul>
        </div>
        <div className="rounded-2xl bg-[#2E1A47] border border-[#1A0E2E] p-4">
          <SectionTitle>AI Review</SectionTitle>
          <p className="prose prose-invert text-[15px] leading-relaxed max-w-none">
            {data?.review ?? "Once you take a few quizzes, I’ll summarize your trend here."}
          </p>
        </div>
      </div>
    </div>
  );
}
