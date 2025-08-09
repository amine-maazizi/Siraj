"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const items = [
  { href: "/upload", label: "Upload" },
  { href: "/summary", label: "Summary / Brainrot" },
  { href: "/chat", label: "Q&A" },
  { href: "/quiz", label: "Quiz" },
  { href: "/review", label: "Review" },
  { href: "/recommendations", label: "Recommendations" },
  { href: "/dashboard", label: "Dashboard" },
];

export function Sidebar(){
  const pathname = usePathname();
  return (
    <aside className="h-full p-4 border-r border-white/10 bg-midnight/60">
      <div className="text-amberGlow font-semibold text-lg mb-4">Siraj</div>
      <nav className="grid gap-1">
        {items.map(i=> (
          <Link key={i.href} href={i.href} className={cn("px-3 py-2 rounded-xl hover:bg-white/5", pathname===i.href && "bg-white/10")}>{i.label}</Link>
        ))}
      </nav>
    </aside>
  );
}