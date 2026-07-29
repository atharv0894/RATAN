import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { TokenResponse } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://ratan-uwno.onrender.com";

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

// ─── Token Helpers ────────────────────────────────────────────────────────────
export const getAccessToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("ratan_access_token");
};

export const getRefreshToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("ratan_refresh_token");
};

export const setTokens = (access: string, refresh: string): void => {
  localStorage.setItem("ratan_access_token", access);
  localStorage.setItem("ratan_refresh_token", refresh);
};

export const clearTokens = (): void => {
  localStorage.removeItem("ratan_access_token");
  localStorage.removeItem("ratan_refresh_token");
};

// ─── Request Interceptor: Attach Bearer Token ─────────────────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Response Interceptor: Token Refresh Logic ───────────────────────────────
let isRefreshing = false;
let failedQueue: { resolve: (v: unknown) => void; reject: (e: unknown) => void }[] = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refresh = getRefreshToken();
      if (!refresh) {
        clearTokens();
        if (typeof window !== "undefined") window.location.href = "/";
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (originalRequest.headers) originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post<{ success: boolean; data: TokenResponse }>(
          `${BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refresh }
        );
        const { access_token, refresh_token } = data.data;
        setTokens(access_token, refresh_token);
        processQueue(null, access_token);
        if (originalRequest.headers) originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        clearTokens();
        if (typeof window !== "undefined") window.location.href = "/";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ─── API Service Modules ──────────────────────────────────────────────────────

// Auth
export const authApi = {
  // Personal
  register_personal: (data: any) => api.post("/personal/auth/register", data),
  login_personal: (username: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);
    return api.post("/personal/auth/login", form, { headers: { "Content-Type": "application/x-www-form-urlencoded" }});
  },
  verify_email: (token: string) => api.post("/personal/auth/verify-email", { token }),
  resend_verification: (email: string) => api.post("/personal/auth/resend-verification", { email }),
  google_oauth_start: () => api.get("/personal/auth/google"),

  // Enterprise
  register_enterprise: (data: any) => api.post("/enterprise/auth/register", data),
  login_enterprise: (username: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);
    return api.post("/enterprise/auth/login", form, { headers: { "Content-Type": "application/x-www-form-urlencoded" }});
  },

  // Super Admin
  login_super_admin: (username: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);
    return api.post("/super-admin/auth/login", form, { headers: { "Content-Type": "application/x-www-form-urlencoded" }});
  },

  // Shared Auth
  refresh: (refresh_token: string) => api.post("/auth/refresh", { refresh_token }),
  logout: (refresh_token: string) => api.post("/auth/logout", { refresh_token }),
  get_me: () => api.get("/auth/me"),
  changePassword: (old_password: string, new_password: string) =>
    api.patch("/auth/change-password", { old_password, new_password }),
  forgotPassword: (email: string) => api.post("/auth/forgot-password", { email }),
};

// Personal Files
export const personalFilesApi = {
  list: () => api.get("/personal/files"),
  upload: (file: File, session_id?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (session_id) {
      form.append("session_id", session_id);
    }
    return api.post("/personal/files", form, { headers: { "Content-Type": "multipart/form-data" } });
  },
  delete: (id: string) => api.delete(`/personal/files/${id}`),
};

// Documents
export const documentsApi = {
  list: (page = 1, limit = 50) => api.get(`/documents?page=${page}&limit=${limit}`),
  get: (id: string) => api.get(`/documents/${id}`),
  upload: (file: File, metadata?: Record<string, string>) => {
    const form = new FormData();
    form.append("file", file);
    if (metadata) form.append("metadata", JSON.stringify(metadata));
    return api.post("/documents/upload", form, { headers: { "Content-Type": "multipart/form-data" } });
  },
  delete: (id: string) => api.delete(`/documents/${id}`),
  restore: (id: string) => api.post(`/documents/${id}/restore`),
  updateMetadata: (id: string, payload: Record<string, string>) => api.patch(`/documents/${id}`, payload),
  getChunk: (chunk_id: string) => api.get(`/documents/chunks/${chunk_id}`),
};

// Chat
export const chatApi = {
  createSession: (title: string, llm_model: string = "gpt-4o") => api.post("/chat", { title, llm_model }),
  search: (question: string) => api.post("/chat/search", { question }),
  send: (question: string, chat_history?: { role: string; content: string }[], document_id?: string, session_id?: string) =>
    api.post("/chat/message", { question, chat_history, document_id, session_id }),
  sendStream: async function* (question: string, chat_history?: { role: string; content: string }[], document_id?: string, session_id?: string) {
    const token = getAccessToken();
    const response = await fetch(`${BASE_URL}/api/v1/chat/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ question, chat_history, document_id, session_id }),
    });

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.error?.message || `HTTP error! status: ${response.status}`);
    }

    if (!response.body) throw new Error("No response body stream");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || "";
      
      for (const part of parts) {
        if (part.startsWith('data: ')) {
          try {
            const data = JSON.parse(part.slice(6));
            yield data;
          } catch (e) {
            // Ignore partial parse
          }
        }
      }
    }
  },
  listSessions: () => api.get("/chat/sessions"),
  getSession: (id: string) => api.get(`/chat/sessions/${id}`),
  deleteSession: (id: string) => api.delete(`/chat/sessions/${id}`),
  renameSession: (id: string, title: string) => api.patch(`/chat/sessions/${id}/rename`, { title }),
  pinSession: (id: string) => api.patch(`/chat/sessions/${id}/pin`),
};

// Personal Chat
export const personalChatApi = {
  createSession: (title: string, llm_model: string = "gpt-4o") => api.post("/personal/chat", { title, llm_model }),
  send: (question: string, chat_history?: { role: string; content: string }[], document_id?: string, session_id?: string) =>
    api.post("/personal/chat/message", { question, chat_history, document_id, session_id }),
  sendStream: async function* (question: string, chat_history?: { role: string; content: string }[], document_id?: string, session_id?: string) {
    const token = getAccessToken();
    const response = await fetch(`${BASE_URL}/api/v1/personal/chat/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ question, chat_history, document_id, session_id }),
    });

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.error?.message || `HTTP error! status: ${response.status}`);
    }

    if (!response.body) throw new Error("No response body stream");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || "";
      
      for (const part of parts) {
        if (part.startsWith('data: ')) {
          try {
            const data = JSON.parse(part.slice(6));
            yield data;
          } catch (e) {
            // Ignore partial parse
          }
        }
      }
    }
  },
  listSessions: () => api.get("/personal/chat"),
  getSession: (id: string) => api.get(`/personal/chat/${id}`),
  deleteSession: (id: string) => api.delete(`/personal/chat/${id}`),
  pinSession: (id: string) => api.patch(`/personal/chat/${id}/pin`),
  renameSession: (id: string, title: string) => api.patch(`/personal/chat/${id}/rename`, { title }),
};

// Dashboard
export const dashboardApi = {
  overview: () => api.get("/dashboard"),
  documents: () => api.get("/dashboard/documents"),
  processing: () => api.get("/dashboard/processing"),
  search: () => api.get("/dashboard/search"),
  ai: () => api.get("/dashboard/ai"),
  users: () => api.get("/dashboard/users"),
  storage: () => api.get("/dashboard/storage"),
  system: () => api.get("/dashboard/system"),
  updateSystemSetting: (id: string, setting_value: string) => api.put(`/dashboard/system/${id}`, { setting_value }),
  flushSystemCache: () => api.post("/dashboard/system/cache/flush"),
  activity: (limit = 20) => api.get(`/dashboard/activity?limit=${limit}`),
  alerts: () => api.get("/dashboard/alerts"),
};

// Jobs
export const jobsApi = {
  list: (page = 1, limit = 20, status?: string) =>
    api.get(`/processing-jobs?page=${page}&limit=${limit}${status ? `&status=${status}` : ""}`),
};

// Admin
export const adminApi = {
  // Organizations
  listOrgs: (skip = 0, limit = 50) => api.get(`/admin/organizations?skip=${skip}&limit=${limit}`),
  createOrg: (name: string) => api.post("/admin/organizations", { name }),
  updateOrg: (id: string, name: string) => api.patch(`/admin/organizations/${id}`, { name }),
  deleteOrg: (id: string) => api.delete(`/admin/organizations/${id}`),
  // Users
  listUsers: (skip = 0, limit = 50) => api.get(`/admin/users?skip=${skip}&limit=${limit}`),
  updateUser: (id: string, payload: Record<string, string>) => api.patch(`/admin/users/${id}`, payload),
  deleteUser: (id: string) => api.delete(`/admin/users/${id}`),
  // Roles
  listRoles: () => api.get("/admin/roles"),
  createRole: (name: string, permissions: string[]) => api.post("/admin/roles", { name, permissions }),
  updateRole: (id: string, payload: Record<string, unknown>) => api.patch(`/admin/roles/${id}`, payload),
  deleteRole: (id: string) => api.delete(`/admin/roles/${id}`),
  // Settings
  getSettings: () => api.get("/admin/settings"),
  updateSettings: (settings: Record<string, unknown>) => api.patch("/admin/settings", settings),
  // Audit
  listAuditLogs: (skip = 0, limit = 50) => api.get(`/admin/audit?skip=${skip}&limit=${limit}`),
  // Maintenance
  runMaintenance: (task_type: string) => api.post(`/admin/maintenance/${task_type}`),
  // System
  systemHealth: () => api.get("/admin/system/health"),
  systemStats: () => api.get("/admin/system/statistics"),
  // Telemetry
  telemetrySystem: () => api.get("/admin/telemetry/system"),
  telemetryTenants: () => api.get("/admin/telemetry/tenants"),
  toggleTenantStatus: (org_id: string) => api.post(`/admin/telemetry/tenants/${org_id}/toggle-status`),
};

// Organizations
export const orgsApi = {
  list: () => api.get("/organizations"),
};

// Plants
export const plantsApi = {
  list: (org_id: string) => api.get(`/plants?org_id=${org_id}`),
  create: (org_id: string, name: string, location?: string) =>
    api.post("/plants", { org_id, name, location }),
  update: (id: string, payload: Record<string, string>) => api.patch(`/plants/${id}`, payload),
  delete: (id: string) => api.delete(`/plants/${id}`),
};

// Departments
export const departmentsApi = {
  list: (plant_id: string) => api.get(`/departments?plant_id=${plant_id}`),
  create: (plant_id: string, name: string) => api.post("/departments", { plant_id, name }),
  update: (id: string, name: string) => api.patch(`/departments/${id}`, { name }),
  delete: (id: string) => api.delete(`/departments/${id}`),
};

// Users
export const usersApi = {
  list: (skip = 0, limit = 50) => api.get(`/users?skip=${skip}&limit=${limit}`),
  create: (payload: Record<string, unknown>) => api.post("/users", payload),
  update: (id: string, payload: Record<string, unknown>) => api.patch(`/users/${id}`, payload),
  delete: (id: string) => api.delete(`/users/${id}`),
};

// Stats
export const statsApi = {
  get: () => api.get("/stats"),
};

// Entities
export const entitiesApi = {
  list: (document_id?: string) => api.get(`/entities${document_id ? `?document_id=${document_id}` : ""}`),
  graph: () => api.get("/entities/graph/data"),
  getDetails: (entity_value: string) => api.get(`/entities/details/${encodeURIComponent(entity_value)}`),
};

// Health
export const healthApi = {
  check: () => api.get("/health"),
};
