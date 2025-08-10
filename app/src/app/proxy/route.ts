// app/src/app/proxy/route.ts
import { NextRequest } from "next/server";
import { Agent } from "undici";

export const runtime = "nodejs";           // ensure Node runtime (not Edge)
export const dynamic = "force-dynamic";    // no caching of responses

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

// Undici agent with LONG/disabled timeouts for heavy jobs (TTS/render)
const dispatcher = new Agent({
  connect: { timeout: 60_000 }, // 60s to connect
  headersTimeout: 0,            // disable header timeout
  bodyTimeout: 0,               // disable body timeout (allow minutes)
  keepAliveTimeout: 60_000,
  keepAliveMaxTimeout: 60_000,
});

function buildUrl(pathParam: string) {
  const path = pathParam.startsWith("/") ? pathParam : `/${pathParam}`;
  return `${API_BASE}${path}`;
}

function sanitizeHeaders(h: Headers) {
  const headers = new Headers(h);
  // strip hop-by-hop/problematic headers
  ["host", "content-length", "accept-encoding", "connection"].forEach((k) => headers.delete(k));
  return headers;
}

async function forward(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const path = searchParams.get("path");
  if (!path) return new Response("Missing ?path", { status: 400 });

  const url = buildUrl(path);
  const isBodyless = req.method === "GET" || req.method === "HEAD";

  const controller = new AbortController();
  const kill = setTimeout(() => controller.abort(), 10 * 60 * 1000); // hard cap: 10 min

  try {
    const resp = await fetch(url, {
      method: req.method,
      headers: sanitizeHeaders(req.headers),
      body: isBodyless ? undefined : await req.arrayBuffer(),
      cache: "no-store",
      // @ts-expect-error: undici option
      dispatcher,
      signal: controller.signal,
      // If you ever pass a stream body, uncomment:
      // // @ts-expect-error
      // duplex: "half",
    });

    // Avoid double compression issues
    const outHeaders = new Headers(resp.headers);
    outHeaders.delete("content-encoding");

    return new Response(resp.body, {
      status: resp.status,
      headers: outHeaders,
    });
  } catch (err: any) {
    console.error("[proxy] error", url, err);
    return new Response(`Proxy error (${err?.code ?? "UNKNOWN"}): ${err?.message ?? "fetch failed"}`, {
      status: 502,
    });
  } finally {
    clearTimeout(kill);
  }
}

export async function GET(req: NextRequest) { return forward(req); }
export async function POST(req: NextRequest) { return forward(req); }
export async function PUT(req: NextRequest) { return forward(req); }
export async function PATCH(req: NextRequest) { return forward(req); }
export async function DELETE(req: NextRequest) { return forward(req); }
export async function OPTIONS(req: NextRequest) { return forward(req); }
