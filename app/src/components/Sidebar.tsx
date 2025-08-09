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
  { href: "/summary", label: "Summary" },
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

  // Hover takes precedence visually
  const currentIdx = hoverIdx ?? activeIdx;

  // Fill only up to the current item
  const fillPct =
    items.length > 1 ? (currentIdx / (items.length - 1)) * 100 : 0;

  return (
    <aside className="relative h-full p-4 border-r border-white/10 bg-midnight/60">
      {/* Header: logo LEFT, then the title */}
      <div className="flex items-center gap-3 mb-6 pl-2">
        <Image
          src="/logo.png"
          alt="Siraj Logo"
          width={48}
          height={48}
          className="opacity-90 shrink-0"
        />
        <div
          className={cn(
            "text-4xl leading-none text-amberGlow",
            arabicFont.className
          )}
        >
          Siraj
        </div>
      </div>

      {/* Nav + timeline restricted to just the nav block */}
      <nav className="relative pl-8">
        {/* Vertical track */}
        <div className="absolute left-1 top-2 bottom-2 w-[4px] rounded-full bg-white/12" />

        {/* Filled progress */}
        <div
          className="absolute left-1 top-2 w-[4px] rounded-full bg-amberGlow transition-[height] duration-300"
          style={{ height: `${fillPct}%` }}
        />

        {items.map((i, idx) => {
          const isActive = pathname === i.href;
          return (
            <Link
              key={i.href}
              href={i.href}
              onMouseEnter={() => setHoverIdx(idx)}
              onMouseLeave={() => setHoverIdx(null)}
              className={cn(
                "block px-3 py-2 rounded-xl hover:bg-white/5 transition-colors",
                isActive && "bg-white/10"
              )}
            >
              {i.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
