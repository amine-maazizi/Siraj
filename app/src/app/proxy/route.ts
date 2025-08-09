// app/src/app/proxy/route.ts
import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  const url = new URL(req.url);
  const path = url.searchParams.get("path"); // e.g., "/ingest"
  if (!path) return new NextResponse("Missing ?path=", { status: 400 });

  const form = await req.formData();
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: form });

  const contentType = res.headers.get("content-type") || "text/plain";
  const buf = await res.arrayBuffer();
  return new NextResponse(buf, {
    status: res.status,
    headers: { "content-type": contentType },
  });
}
