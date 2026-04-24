// API client for Find Evil Agent backend

// Use environment variable or default to localhost
// In production, set VITE_API_BASE_URL to your backend URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:18000';

export interface AnalysisRequest {
  incident: string;
  goal: string;
  format?: 'html' | 'markdown';
}

export interface InvestigationRequest extends AnalysisRequest {
  max_iterations?: number;
}

export interface Lead {
  type: string;
  description: string;
  priority: string;
  confidence?: number;
  rationale?: string;
}

export interface AnalysisResponse {
  success: boolean;
  session_id?: string;
  report?: string;
  error?: string;
  summary?: string;
  findings?: any[];
  iocs?: any[];
}

export interface InvestigationResponse extends AnalysisResponse {
  iterations?: any[];
  investigation_chain?: Lead[];
  all_findings?: any[];
  all_iocs?: any;
  total_duration?: number;
  stopping_reason?: string;
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
  investigate: async (data: InvestigationRequest): Promise<InvestigationResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  // Resume investigation after HITL approval
  resume: async (sessionId: string, approved: boolean): Promise<InvestigationResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/investigate/${sessionId}/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved }),
    });
    return response.json();
  },

  // Health check
  health: async (): Promise<{ status: string }> => {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  },
};
