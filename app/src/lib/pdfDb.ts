// lib/pdfDb.ts
import { set, get, del, keys } from "idb-keyval";

const KEY_PREFIX = "siraj:pdf:";
export async function savePdf(docId: string, file: Blob) {
  await set(KEY_PREFIX + docId, file);
}
export async function loadPdf(docId: string): Promise<Blob | undefined> {
  return get(KEY_PREFIX + docId);
}
export async function deletePdf(docId: string) {
  await del(KEY_PREFIX + docId);
}
export async function listDocIds(): Promise<string[]> {
  const all = await keys();
  return all
    .map((k: any) => (typeof k === "string" ? k : k?.toString?.()))
    .filter((k): k is string => !!k && k.startsWith(KEY_PREFIX))
    .map((k) => k.replace(KEY_PREFIX, ""));
}
