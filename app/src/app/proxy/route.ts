// app/src/app/proxy/route.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

function buildUrl(pathParam: string, reqUrl: string) {
  const base = pathParam.startsWith("/") ? pathParam : `/${pathParam}`;
  const out = new URL(`${API_BASE}${base}`);

  // forward all query params except "path"
  const inUrl = new URL(reqUrl);
  inUrl.searchParams.forEach((value, key) => {
    if (key !== "path") out.searchParams.append(key, value);
  });

  return out.toString();
}

async function forward(req: Request) {
  const { searchParams } = new URL(req.url);
  const path = searchParams.get("path");
  if (!path) return new Response("Missing ?path", { status: 400 });

  const url = buildUrl(path, req.url);
  const isBodyless = req.method === "GET" || req.method === "HEAD";

  // Clone headers and strip host & length (Node/fetch will set the right ones)
  const headers = new Headers(req.headers);
  headers.delete("host");
  headers.delete("content-length");

  // Stream body instead of buffering (fixes large/multipart uploads)
  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
    // @ts-expect-error: Node fetch quirk when streaming request bodies
    duplex: isBodyless ? undefined : "half",
    body: isBodyless ? undefined : req.body,
  };

  const resp = await fetch(url, init);

  // Scrub hop-by-hop headers on the way back
  const outHeaders = new Headers(resp.headers);
  outHeaders.delete("content-length");
  outHeaders.delete("transfer-encoding");
  outHeaders.delete("connection");

  return new Response(resp.body, {
    status: resp.status,
    statusText: resp.statusText,
    headers: outHeaders,
  });
}

// Support all common verbs so we never get 405 from Next
export {
  forward as GET,
  forward as POST,
  forward as PUT,
  forward as PATCH,
  forward as DELETE,
  forward as OPTIONS,
};
