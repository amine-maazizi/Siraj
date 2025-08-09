const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, init);
  if(!res.ok) throw new Error(await res.text());
  return res.headers.get("content-type")?.includes("application/json") ? await res.json() : (await res.text() as any);
}

export const api = {
  get: <T=any>(path: string) => request<T>(path, { method: "GET" }),
  post: <T=any>(path: string, body?: any, isForm=false) => request<T>(path, { method: "POST", body: isForm? body: JSON.stringify(body), headers: isForm? undefined: { "Content-Type": "application/json" } })
};