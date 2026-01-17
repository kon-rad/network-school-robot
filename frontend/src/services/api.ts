import type { RobotStatus, ActionResponse, LogsResponse } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Request failed');
  }
  return response.json();
}

export const robotApi = {
  getStatus: async (): Promise<RobotStatus> => {
    const response = await fetch(`${API_BASE}/api/robot/status`);
    return handleResponse<RobotStatus>(response);
  },

  connect: async (connectionMode: string = 'auto'): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ connection_mode: connectionMode }),
    });
    return handleResponse<ActionResponse>(response);
  },

  disconnect: async (): Promise<ActionResponse> => {
    const response = await fetch(`${API_BASE}/api/robot/disconnect`, {
      method: 'POST',
    });
    return handleResponse<ActionResponse>(response);
  },

  getLogs: async (page: number = 1, limit: number = 50): Promise<LogsResponse> => {
    const response = await fetch(`${API_BASE}/api/logs?page=${page}&limit=${limit}`);
    return handleResponse<LogsResponse>(response);
  },

  clearLogs: async (): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE}/api/logs`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

export const getWebSocketUrl = (): string => {
  const wsBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
  return `${wsBase}/api/logs/stream`;
};
