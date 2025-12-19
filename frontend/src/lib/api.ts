import type {
  ResearchConfig,
  ResearchSession,
  OverallMetrics,
  UserSettings,
  ComplianceReport
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'An error occurred' }));
      throw new Error(error.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Research Sessions
  async createSession(config: ResearchConfig): Promise<ResearchSession> {
    return this.request<ResearchSession>('/sessions', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getSession(sessionId: string): Promise<ResearchSession> {
    return this.request<ResearchSession>(`/sessions/${sessionId}`);
  }

  async listSessions(): Promise<ResearchSession[]> {
    return this.request<ResearchSession[]>('/sessions');
  }

  async startSession(sessionId: string): Promise<ResearchSession> {
    return this.request<ResearchSession>(`/sessions/${sessionId}/start`, {
      method: 'POST',
    });
  }

  async pauseSession(sessionId: string): Promise<ResearchSession> {
    return this.request<ResearchSession>(`/sessions/${sessionId}/pause`, {
      method: 'POST',
    });
  }

  async stopSession(sessionId: string): Promise<ResearchSession> {
    return this.request<ResearchSession>(`/sessions/${sessionId}/stop`, {
      method: 'POST',
    });
  }

  // Results
  async getResults(sessionId: string): Promise<unknown> {
    return this.request(`/sessions/${sessionId}/results`);
  }

  async downloadPaper(sessionId: string, format: 'pdf' | 'latex'): Promise<Blob> {
    const url = `${this.baseUrl}/sessions/${sessionId}/download?format=${format}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    return response.blob();
  }

  // Metrics
  async getMetrics(sessionId: string): Promise<OverallMetrics> {
    return this.request<OverallMetrics>(`/metrics/${sessionId}`);
  }

  // Ethics & Compliance
  async getComplianceReport(sessionId: string): Promise<ComplianceReport> {
    return this.request<ComplianceReport>(`/sessions/${sessionId}/compliance`);
  }

  async getAllComplianceReports(): Promise<ComplianceReport[]> {
    return this.request<ComplianceReport[]>('/compliance');
  }

  // Overall Metrics
  async getOverallMetrics(): Promise<OverallMetrics> {
    return this.request<OverallMetrics>('/metrics');
  }

  // User Settings
  async getSettings(): Promise<UserSettings> {
    return this.request<UserSettings>('/settings');
  }

  async updateSettings(settings: UserSettings): Promise<UserSettings> {
    return this.request<UserSettings>('/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);