const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

function buildUrl(pathParam: string) {
  const path = pathParam.startsWith("/") ? pathParam : `/${pathParam}`;
  return `${API_BASE}${path}`;
}

async function forward(req: Request) {
  const { searchParams } = new URL(req.url);
  const path = searchParams.get("path");
  if (!path) return new Response("Missing ?path", { status: 400 });

  const url = buildUrl(path);
  const isBodyless = req.method === "GET" || req.method === "HEAD";

  // Pass-through headers except host (Next will set it)
  const headers = new Headers(req.headers);
  headers.delete("host");

  const resp = await fetch(url, {
    method: req.method,
    headers,
    body: isBodyless ? undefined : await req.arrayBuffer(),
  });

  // Stream response + preserve headers/status
  return new Response(resp.body, { status: resp.status, headers: resp.headers });
}

// Next App Router settings
export const dynamic = "force-dynamic"; // avoid static optimization
export const revalidate = 0;

// Explicit handlers (avoid 404 on non-GET)
export async function GET(req: Request) { return forward(req); }
export async function POST(req: Request) { return forward(req); }
export async function PUT(req: Request) { return forward(req); }
export async function PATCH(req: Request) { return forward(req); }
export async function DELETE(req: Request) { return forward(req); }
export async function HEAD(req: Request) { return forward(req); }
export async function OPTIONS(req: Request) { return forward(req); }
