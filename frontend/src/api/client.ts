// API client for Find Evil Agent backend

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:18000';

export interface AnalysisRequest {
  incident: string;
  goal: string;
  format?: 'html' | 'markdown';
}

export interface InvestigationRequest extends AnalysisRequest {
  max_iterations?: number;
}

export interface AnalysisResponse {
  success: boolean;
  report?: string;
  error?: string;
}

export const api = {
  // Single analysis
  analyze: async (data: AnalysisRequest): Promise<AnalysisResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  // Investigative mode
  investigate: async (data: InvestigationRequest): Promise<AnalysisResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  // Health check
  health: async (): Promise<{ status: string }> => {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  },
};
