"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function Recommendations() {
  const { data } = useQuery({
    queryKey: ["suggest"],
    queryFn: async () =>
      api.post("/suggest", {
        gaps: ["placeholder"],
        time_per_day: 30,
        horizon_weeks: 4,
      }),
  });

  const demoTasks = [
    "Review Newton's Laws",
    "Watch Thermodynamics intro",
    "Solve 5 kinematics problems",
    "Read chapter on fluid mechanics",
  ];

  const demoResources = [
    { title: "Halliday & Resnick – Physics", type: "book", price: "Free", link: "#" },
    { title: "Khan Academy: Newton's Laws", type: "video", price: "Free", link: "#" },
    { title: "Udemy: Thermodynamics Basics", type: "course", price: "$19", link: "#" },
  ];

  return (
    <div className="min-h-screen overflow-x-hidden space-y-6 p-4">
      <h1 className="text-2xl font-semibold">Recommendations</h1>

      {/* Horizontal scrollable tasks */}
      <section>
        <h2 className="text-lg font-medium mb-2">AI-Generated To-Do</h2>
        <div className="w-full max-w-full overflow-x-auto scroll-smooth pb-2">
          <div className="flex gap-4">
            {demoTasks.map((task, i) => (
              <div
                key={i}
                className="flex-none w-64 rounded-xl bg-white/5 p-4 border border-white/10"
              >
                <p className="text-sm">{task}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Horizontal scrollable resources */}
      <section>
        <h2 className="text-lg font-medium mb-2">Resources</h2>
        <div className="w-full max-w-full overflow-x-auto scroll-smooth pb-2">
          <div className="flex gap-4">
            {demoResources.map((r, i) => (
              <div
                key={i}
                className="flex-none w-72 rounded-xl bg-white/5 p-4 border border-white/10"
              >
                <div className="font-medium">{r.title}</div>
                <div className="text-xs opacity-70">{r.type}</div>
                <div className={`mt-2 text-sm ${r.price === "Free" ? "text-green-400" : ""}`}>
                  {r.price}
                </div>
                <a
                  href={r.link}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-block text-goldHi text-sm underline"
                >
                  Open resource
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
