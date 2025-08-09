import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const path = req.nextUrl.searchParams.get("path");
  if(!path) return NextResponse.json({ error: "Missing path" }, { status: 400 });
  const url = `http://localhost:8000/static?path=${encodeURIComponent(path)}`;
  const res = await fetch(url);
  const buf = await res.arrayBuffer();
  return new NextResponse(buf, { headers: { "Content-Type": res.headers.get("Content-Type") || "application/octet-stream" }});
}