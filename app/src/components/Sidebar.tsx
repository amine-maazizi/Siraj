"use client";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useMemo, useState } from "react";
import { Scheherazade_New } from "next/font/google";

const arabicFont = Scheherazade_New({ subsets: ["latin"], weight: ["700"] });

const items = [
  { href: "/upload", label: "Upload" },
  { href: "/summary", label: "Summary / Brainrot" },
  { href: "/chat", label: "Q&A" },
  { href: "/quiz", label: "Quiz" },
  { href: "/review", label: "Review" },
  { href: "/recommendations", label: "Recommendations" },
  { href: "/dashboard", label: "Dashboard" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const activeIdx = useMemo(
    () => Math.max(0, items.findIndex((i) => i.href === pathname)),
    [pathname]
  );

  // which step we’re visually targeting (hover wins over active)
  const currentIdx = hoverIdx ?? activeIdx;
  const fillPct = ((currentIdx + 1) / items.length) * 100;

  return (
    <aside className="relative h-full p-4 border-r border-white/10 bg-midnight/60">
      {/* Header: logo LEFT, then the title */}
      <div className="flex items-center gap-3 mb-6 pl-2">
        <Image
          src="/logo.png"
          alt="Siraj Logo"
          width={44}
          height={44}
          className="opacity-90 shrink-0"
        />
        <div className={cn("text-4xl leading-none text-amberGlow", arabicFont.className)}>
          Siraj
        </div>
      </div>

      {/* Nav + timeline restricted to nav height (so it ends at Dashboard) */}
      <nav className="relative pl-8">
        {/* Vertical track only spans the nav */}
        <div className="absolute left-1 top-2 bottom-2 w-[4px] rounded-full bg-white/10" />
        {/* Filled progress up to current step */}
        <div
          className="absolute left-1 top-2 w-[4px] rounded-full bg-amberGlow transition-[height] duration-300"
          style={{ height: `${fillPct}%` }}
        />

        {items.map((i, idx) => (
          <div key={i.href} className="relative">
            {/* Downward arrow next to the hovered/active item (no drifting) */}
            {(hoverIdx === idx || (hoverIdx === null && activeIdx === idx)) && (
              <div className="absolute -left-5 top-1/2 -translate-y-1/2 z-10">
                <div className="w-0 h-0 border-l-[7px] border-l-transparent border-r-[7px] border-r-transparent border-b-[9px] border-b-amberGlow" />
              </div>
            )}

            <Link
              href={i.href}
              onMouseEnter={() => setHoverIdx(idx)}
              onMouseLeave={() => setHoverIdx(null)}
              className={cn(
                "block px-3 py-2 rounded-xl hover:bg-white/5 transition-colors",
                pathname === i.href && "bg-white/10"
              )}
            >
              {i.label}
            </Link>
          </div>
        ))}
      </nav>
    </aside>
  );
}
