export interface SourceInfo {
  vendor: string;
  document: string;
  page?: string;
  chunk?: number;
}

export interface MessageItem {
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceInfo[];
  timestamp?: Date;
}

export interface QueryRequest {
  question: string;
  session_id?: string;
  top_k?: number;
  conversation_history?: MessageItem[];
}

export interface QueryResponse {
  answer: string;
  sources: SourceInfo[];
  session_id: string;
}

export interface ConfigGenRequest {
  request: string;
  vendor?: string;
  top_k?: number;
}

export interface ConfigGenResponse {
  config: string;
  sources: SourceInfo[];
}

export interface DocumentInfo {
  vendor: string;
  document: string;
  chunk_count: number;
  page_count: number;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total_chunks: number;
}

export interface AnalyticsResponse {
  total_queries: number;
  active_sessions: number;
  avg_response_time: number;
  popular_topics: { topic: string; count: number }[];
  recent_queries: { question: string; timestamp: number; response_time: number }[];
  total_documents: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  chromadb_count: number;
  model: string;
  embedding_model: string;
}

export interface ConfigResponse {
  model: string;
  embedding_model: string;
  has_api_key: boolean;
}
