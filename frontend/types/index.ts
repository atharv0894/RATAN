// ============================================================
// RATAN Frontend Type Definitions
// ============================================================

// -- Auth --
export interface User {
  id: string;
  org_id: string;
  plant_id: string | null;
  department_id: string | null;
  role: string;
  email: string;
  full_name: string;
  status?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  org_name: string;
  admin_email: string;
  admin_password: string;
  admin_name: string;
}

// -- Generic API --
export interface APIResponse<T = unknown> {
  success: boolean;
  data: T;
  meta: PaginatedMeta | null;
  message?: string;
}

export interface PaginatedMeta {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

// -- Documents --
export interface Document {
  id: string;
  filename: string;
  status: "READY" | "PROCESSING" | "FAILED" | "QUEUED" | "DELETED";
  chunks: number;
  version_number: number;
  is_latest: boolean;
  title?: string;
  description?: string;
  category?: string;
  equipment?: string;
  language?: string;
  author?: string;
}

export interface DocumentMetadataUpdate {
  title?: string;
  description?: string;
  category?: string;
  equipment?: string;
  language?: string;
  author?: string;
}

// -- Chat --
export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatRequest {
  question: string;
  document_id?: string;
  chat_history?: ChatMessage[];
}

export interface Citation {
  document_name: string;
  version: number;
  page: string;
  section: string;
  chunk_id: string;
}

export interface RAGResponse {
  answer: string;
  citations: Citation[];
  confidence_score: number;
  follow_up_questions: string[];
  intent: string;
  provider: string;
  session_id?: string;
}

// -- Dashboard --
export interface DashboardOverview {
  total_documents: number;
  active_users: number;
  total_chats: number;
  total_storage_mb: number;
}

export interface DocumentAnalytics {
  total: number;
  by_category: { category: string; count: number }[];
  by_department: { department: string; count: number }[];
  by_status: { status: string; count: number }[];
  latest_uploads: { title: string; created_at: number }[];
}

export interface AIAnalytics {
  total_chats: number;
  total_messages: number;
  avg_confidence: number;
  total_tokens: number;
}

export interface StorageAnalytics {
  total_storage_bytes: number;
  total_versions: number;
  total_chunks: number;
  total_vectors: number;
}

export interface SystemHealth {
  status: string;
  cpu_percent: number;
  memory_percent: number;
  uptime_seconds: number;
  db_size_mb: number;
  qdrant_status: string;
  b2_status: string;
}

export interface ActivityItem {
  action: string;
  resource: string;
  status: string;
  endpoint: string;
  execution_time_ms: number;
  created_at: number;
  user_name: string | null;
}

export interface AlertItem {
  severity: "High" | "Critical" | "Medium" | "Low";
  message: string;
}

// -- Processing Jobs --
export interface ProcessingJob {
  id: string;
  target_type: string;
  target_id: string;
  status: "QUEUED" | "PROCESSING" | "EMBEDDING" | "INDEXING" | "COMPLETED" | "FAILED" | "CANCELLED";
  started_at: number | null;
  finished_at: number | null;
  retry_count: number;
  error_message: string | null;
  created_at: number;
  updated_at: number;
}

export interface ProcessingAnalytics {
  queued: number;
  processing: number;
  completed: number;
  failed: number;
  recent_failures: { target_id: string; error_message: string; updated_at: number }[];
}

// -- Admin --
export interface Organization {
  id: string;
  name: string;
  status: string;
  created_at: number;
  updated_at: number;
}

export interface Plant {
  id: string;
  org_id: string;
  name: string;
  location: string;
  status: string;
}

export interface Department {
  id: string;
  plant_id: string;
  name: string;
  status: string;
}

export interface Role {
  id: string;
  name: string;
  permissions: string;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  endpoint: string;
  action: string;
  resource: string;
  status: string;
  ip_address: string;
  execution_time_ms: number;
  created_at: number;
  updated_at: number;
}

// -- Stats --
export interface Stats {
  total_documents: number;
  total_chunks: number;
  total_queries: number;
  storage_mb: number;
}

// -- Entities --
export interface Entity {
  id: string;
  name: string;
  type: string;
  source_document: string;
}
