const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, init);
  if(!res.ok) throw new Error(await res.text());
  return res.headers.get("content-type")?.includes("application/json") ? await res.json() : (await res.text() as any);
}

// app/src/lib/api.ts
export const api = {
  get: async <T = any>(path: string): Promise<T> => {
    const r = await fetch(`/proxy?path=${encodeURIComponent(path)}`, { method: "GET" });
    if (!r.ok) throw new Error(`GET ${path} -> ${r.status}`);
    return r.json();
  },
  post: async <T = any>(path: string, body?: any): Promise<T> => {
    const r = await fetch(`/proxy?path=${encodeURIComponent(path)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body ?? {}),
    });
    if (!r.ok) throw new Error(`POST ${path} -> ${r.status}`);
    return r.json();
  },
};

