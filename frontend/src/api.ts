// Typed client for the Evidence-RAG backend.

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface Citation {
  id: string;
  source: string;
  chunk_index: number;
  text: string;
  score: number | null;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  used_context: boolean;
  latency_ms: number;
}

export interface Chunk {
  id: string;
  text: string;
  source: string;
  chunk_index: number;
  score: number | null;
}

export interface RetrieveResponse {
  question: string;
  chunks: Chunk[];
  latency_ms: number;
}

export interface Stats {
  collection: string;
  chunks: number;
  embedding_model: string;
  llm_provider: string;
}

export interface HistoryItem {
  id: number;
  question: string;
  answer: string;
  citations: Citation[];
  used_context: boolean;
  latency_ms: number | null;
  created_at: string;
}

export interface IngestResponse {
  documents: number;
  chunks: number;
  collection: string;
}

export interface DocumentInfo {
  source: string;
  chunks: number;
}

export interface DocumentsResponse {
  documents: DocumentInfo[];
  total_documents: number;
  total_chunks: number;
}

export interface DocumentChunksResponse {
  source: string;
  chunks: Chunk[];
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function askQuestion(question: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return handle<QueryResponse>(res);
}

export async function retrieveChunks(question: string): Promise<RetrieveResponse> {
  const res = await fetch(`${API_BASE}/retrieve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return handle<RetrieveResponse>(res);
}

export async function getStats(): Promise<Stats> {
  return handle<Stats>(await fetch(`${API_BASE}/stats`));
}

export async function getDocuments(): Promise<DocumentsResponse> {
  return handle<DocumentsResponse>(await fetch(`${API_BASE}/documents`));
}

export async function getDocumentChunks(
  source: string,
): Promise<DocumentChunksResponse> {
  return handle<DocumentChunksResponse>(
    await fetch(`${API_BASE}/documents/${encodeURIComponent(source)}`),
  );
}

export async function getHistory(limit = 50): Promise<HistoryItem[]> {
  return handle<HistoryItem[]>(await fetch(`${API_BASE}/history?limit=${limit}`));
}

export async function clearHistory(): Promise<{ deleted: number }> {
  return handle<{ deleted: number }>(
    await fetch(`${API_BASE}/history`, { method: "DELETE" }),
  );
}

export async function uploadFiles(files: FileList): Promise<IngestResponse> {
  const form = new FormData();
  Array.from(files).forEach((f) => form.append("files", f));
  const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
  return handle<IngestResponse>(res);
}
