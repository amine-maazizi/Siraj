"use client";
import { motion } from "framer-motion";

export function SentimentBadge({ sentiment }:{ sentiment: "positive"|"neutral"|"negative" }){
  const map = {
    positive: { label: "😊", bg: "bg-green-500/20", dot: "bg-green-400" },
    neutral:  { label: "😐", bg: "bg-yellow-500/20", dot: "bg-yellow-400" },
    negative: { label: "😕", bg: "bg-red-500/20", dot: "bg-red-400" },
  } as const;
  const s = map[sentiment];
  return (
    <motion.div className={`flex items-center gap-2 px-3 py-1 rounded-xl ${s.bg}`}
      animate={{ scale: [1, 1.04, 1] }} transition={{ duration: 0.8 }}>
      <span className={`w-2 h-2 rounded-full ${s.dot}`}></span>
      <span>{s.label}</span>
    </motion.div>
  );
}